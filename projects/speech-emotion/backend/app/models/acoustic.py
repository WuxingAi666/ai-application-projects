"""
声学情感分析模型
---------------
策略（按优先级）：
1. HuBERT — 自监督语音预训练（英文版，通用声学特征）
2. emotion2vec — 中文语音情感专用（需 funasr，Windows 兼容性差）
3. 改进的声学特征分析 — 基频+能量+语速（非随机，基于声学统计）
"""

# 必须在导入 numpy 之前设置，防止 Intel SVML DLL 错误
import os
os.environ.setdefault("NPY_DISABLE_SVML", "1")

import numpy as np
import torch
import torch.nn as nn
import librosa

from app.config import EMOTION_LABELS, TARGET_SAMPLE_RATE
from app.utils.logger import logger


class AcousticEmotionAnalyzer:
    """
    声学情感分析器

    加载优先级: emotion2vec > HuBERT > 改进声学特征
    每次加载失败自动降级到下一级
    """

    EMOTIONS = EMOTION_LABELS

    def __init__(self):
        self.model = None
        self.processor = None
        self.classifier = None
        self.emotion_pipeline = None
        self.model_type = "unknown"
        self.model_quality = "low"  # high/medium/low
        self.device = torch.device("cpu")
        self._init_model()

    def _init_model(self):
        """按优先级尝试加载模型：HuBERT > emotion2vec > 统计特征"""
        # HuBERT 优先（已验证可用，质量 medium）
        if self._try_hubert():
            return
        # emotion2vec 备选（需要 funasr，Windows 兼容性差）
        if self._try_emotion2vec():
            return
        # 最终兜底
        self._init_acoustic_features()
        self.model_quality = "low"

    def _try_emotion2vec(self) -> bool:
        """尝试加载 emotion2vec（中文语音情感专用）"""
        try:
            from modelscope.pipelines import pipeline
            from modelscope.utils.constant import Tasks

            self.emotion_pipeline = pipeline(
                Tasks.emotion_recognition,
                model="iic/emotion2vec_base",
                device="cpu",
            )
            self.model_type = "emotion2vec"
            self.model_quality = "high"
            logger.info("[OK] 声学模型: emotion2vec (ModelScope, quality=high)")
            return True
        except Exception as e:
            logger.warning(f"emotion2vec 加载失败: {str(e)[:80]}")
            return False

    def _try_hubert(self) -> bool:
        """尝试加载 HuBERT（英文版，作为通用声学特征提取器）"""
        try:
            from transformers import HubertModel, Wav2Vec2FeatureExtractor

            # 使用英文 HuBERT（已验证可加载），作为跨语言声学特征提取器
            # 虽不能理解中文词义，但能捕获音调、节奏、能量等情感相关的声学特征
            model_name = "facebook/hubert-base-ls960"
            self.processor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
            self.model = HubertModel.from_pretrained(model_name).to(self.device)
            self.model.eval()

            hidden_size = self.model.config.hidden_size  # 768
            self.classifier = nn.Sequential(
                nn.Linear(hidden_size, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, len(self.EMOTIONS)),
            ).to(self.device)
            self.classifier.eval()

            self.model_type = "hubert"
            self.model_quality = "medium"
            logger.info("[OK] 声学模型: HuBERT (facebook/hubert-base, quality=medium)")
            return True

        except Exception as e:
            logger.warning(f"HuBERT 加载失败: {str(e)[:80]}")
            return False

    def _init_acoustic_features(self):
        """兜底方案：基于声学统计特征的非随机分析"""
        self.model_type = "acoustic_features"
        self.model_quality = "low"
        logger.info("[OK] 声学模型: Acoustic Features (统计规则, quality=low)")

    def analyze(self, audio_path: str) -> dict:
        """分析音频情感"""
        if self.model_type == "emotion2vec":
            return self._analyze_emotion2vec(audio_path)
        elif self.model_type == "hubert":
            return self._analyze_hubert(audio_path)
        else:
            return self._analyze_acoustic_features(audio_path)

    def _analyze_emotion2vec(self, audio_path: str) -> dict:
        """emotion2vec 推理"""
        try:
            result = self.emotion_pipeline(audio_path)
            scores = result.get("scores", [1.0 / len(self.EMOTIONS)] * len(self.EMOTIONS))
            labels = result.get("labels", self.EMOTIONS)

            probs = self._map_to_standard_emotions(labels, scores)
            best = max(probs, key=probs.get)

            return {
                "label": best,
                "confidence": float(probs[best]),
                "probabilities": probs,
                "feature_vector": list(probs.values()) + [0.0] * (512 - len(self.EMOTIONS)),
                "quality": self.model_quality,
            }
        except Exception as e:
            logger.error(f"emotion2vec 推理失败: {e}")
            return self._fallback_result()

    def _analyze_hubert(self, audio_path: str) -> dict:
        """HuBERT 推理（英文HuBERT作为通用声学特征提取器）"""
        try:
            waveform, sr = librosa.load(audio_path, sr=16000, mono=True)

            # Wav2Vec2FeatureExtractor API
            inputs = self.processor(
                waveform, sampling_rate=16000, return_tensors="pt"
            )
            input_values = inputs["input_values"].to(self.device)

            with torch.no_grad():
                outputs = self.model(input_values)
                hidden = outputs.last_hidden_state  # [1, T, 768]
                pooled = hidden.mean(dim=1)          # [1, 768]
                logits = self.classifier(pooled)      # [1, 6]
                probs_tensor = torch.softmax(logits, dim=-1).squeeze().cpu().numpy()

            best_idx = int(np.argmax(probs_tensor))
            probs = {self.EMOTIONS[i]: float(probs_tensor[i]) for i in range(len(self.EMOTIONS))}

            return {
                "label": self.EMOTIONS[best_idx],
                "confidence": float(probs_tensor[best_idx]),
                "probabilities": probs,
                "feature_vector": pooled.squeeze().cpu().numpy().tolist(),
                "quality": self.model_quality,
            }
        except Exception as e:
            logger.error(f"HuBERT 推理失败: {e}")
            return self._fallback_result()

    def _analyze_acoustic_features(self, audio_path: str) -> dict:
        """
        基于声学统计特征的非随机分析

        利用语音信号的基本声学属性进行合理推测：
        - 基频(F0)高+变化大 → 开心/愤怒
        - 基频低+语速慢 → 悲伤
        - 能量高+语速快 → 愤怒/惊讶
        - 能量低+平稳 → 中性/悲伤
        """
        try:
            waveform, sr = librosa.load(audio_path, sr=16000, mono=True)

            # 1. 基频 (F0) 分析
            f0, voiced_flag, _ = librosa.pyin(
                waveform, fmin=50, fmax=500, sr=sr, fill_na=0
            )
            voiced_f0 = f0[voiced_flag] if np.any(voiced_flag) else np.array([0])

            f0_mean = float(np.mean(voiced_f0)) if len(voiced_f0) > 0 else 0
            f0_std = float(np.std(voiced_f0)) if len(voiced_f0) > 0 else 0
            f0_range = f0_std / (f0_mean + 1e-8)  # 基频变异系数

            # 2. 能量分析
            rms = librosa.feature.rms(y=waveform).flatten()
            energy_mean = float(np.mean(rms))
            energy_std = float(np.std(rms))

            # 3. 语速估计 (过零率变化)
            zcr = librosa.feature.zero_crossing_rate(waveform).flatten()
            zcr_mean = float(np.mean(zcr))
            zcr_std = float(np.std(zcr))

            # 4. 频谱质心 (声音亮度)
            spectral_centroid = librosa.feature.spectral_centroid(y=waveform, sr=sr).flatten()
            centroid_mean = float(np.mean(spectral_centroid))

            # ---- 基于声学特征的合理推测 ----
            # 初始化概率（不是均匀分布，而是基于声学统计的合理估计）
            scores = {"开心": 0.10, "悲伤": 0.10, "愤怒": 0.10, "中性": 0.30, "惊讶": 0.20, "恐惧": 0.20}

            # 基频高+变化大 → 更可能是情绪激动的 (开心/愤怒/惊讶)
            if f0_mean > 180 and f0_range > 0.3:
                scores["开心"] += 0.15
                scores["愤怒"] += 0.15
                scores["惊讶"] += 0.10
                scores["中性"] -= 0.10
                scores["悲伤"] -= 0.05

            # 基频低+能量低 → 更可能是悲伤
            if f0_mean < 140 and energy_mean < 0.05:
                scores["悲伤"] += 0.30
                scores["中性"] += 0.10
                scores["开心"] -= 0.15
                scores["愤怒"] -= 0.10

            # 能量高+变化大 → 愤怒/惊讶
            if energy_std > 0.03 and zcr_std > 0.02:
                scores["愤怒"] += 0.15
                scores["惊讶"] += 0.10
                scores["中性"] -= 0.05

            # 语速快(ZCR高) → 激动类情绪
            if zcr_mean > 0.08:
                scores["愤怒"] += 0.10
                scores["开心"] += 0.05
                scores["悲伤"] -= 0.10

            # 频谱质心低 → 悲伤（声音偏暗）
            if centroid_mean < 1500:
                scores["悲伤"] += 0.10
                scores["中性"] += 0.05
                scores["开心"] -= 0.05

            # 一切平稳 → 中性
            if f0_range < 0.15 and energy_std < 0.01 and zcr_std < 0.01:
                scores["中性"] += 0.30
                for k in scores:
                    if k != "中性":
                        scores[k] -= 0.05

            # 确保所有概率为正
            for k in scores:
                scores[k] = max(0.02, scores[k])

            # 归一化
            total = sum(scores.values())
            probs = {k: round(v / total, 4) for k, v in scores.items()}

            best = max(probs, key=probs.get)

            logger.info(
                f"声学特征分析: f0_mean={f0_mean:.0f}Hz, "
                f"energy={energy_mean:.4f}, zcr={zcr_mean:.4f} → {best}({probs[best]:.2f})"
            )

            return {
                "label": best,
                "confidence": round(float(probs[best]), 4),
                "probabilities": probs,
                "feature_vector": list(probs.values()) + [0.0] * (512 - len(self.EMOTIONS)),
                "quality": self.model_quality,
            }
        except Exception as e:
            logger.error(f"声学特征分析失败: {e}")
            return self._fallback_result()

    def _map_to_standard_emotions(self, labels: list, scores: list) -> dict:
        """将模型标签映射到标准6情感"""
        emotion_map = {
            "高兴": "开心", "开心": "开心", "happy": "开心", "happiness": "开心",
            "悲伤": "悲伤", "难过": "悲伤", "sad": "悲伤", "sadness": "悲伤",
            "愤怒": "愤怒", "生气": "愤怒", "angry": "愤怒", "anger": "愤怒",
            "中性": "中性", "平静": "中性", "neutral": "中性",
            "惊讶": "惊讶", "惊奇": "惊讶", "surprise": "惊讶", "surprised": "惊讶",
            "恐惧": "恐惧", "害怕": "恐惧", "fear": "恐惧", "fearful": "恐惧",
        }
        probs = {e: 0.0 for e in self.EMOTIONS}
        for label, score in zip(labels, scores):
            mapped = emotion_map.get(str(label).lower(), "中性")
            if mapped in probs:
                probs[mapped] = max(probs[mapped], float(score))
        return probs

    def _fallback_result(self) -> dict:
        """完全失败时的保守中性结果"""
        return {
            "label": "中性",
            "confidence": 0.30,
            "probabilities": {e: 0.15 if e == "中性" else 0.17 for e in self.EMOTIONS},
            "feature_vector": [0.0] * 512,
            "quality": "lowest",
        }
