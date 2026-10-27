"""
主处理流水线
-----------
编排所有模型：音频预处理 → 并行分析（声学/ASR/LLM）→ 多模态融合 → 结果组装
模型采用延迟加载策略：启动时不加载，首次使用时才加载，超时自动降级
"""

import time
import uuid
import asyncio
from pathlib import Path

from app.config import UPLOAD_DIR, STATIC_DIR
from app.utils.logger import logger
from app.services.audio_utils import audio_utils
from app.models.fusion import MultiModalFusion


class EmotionAnalysisPipeline:
    """
    情感分析主流水线

    模型加载策略：
    - 启动时：仅初始化 LLM 和 Fusion（秒级）
    - 首次分析：按需加载声学模型和 ASR（带超时保护）
    - 加载失败：自动降级到本地规则方案，不影响基本使用
    """

    def __init__(self):
        self.acoustic_analyzer = None
        self.asr_engine = None
        self.llm_analyzer = None
        self.fusion_engine = None
        self._models_ready = False
        self._models_loading = False
        self._load_lock = asyncio.Lock()

    async def initialize(self):
        """快速初始化：仅加载轻量模块，重模型延迟到首次使用"""
        logger.info("=" * 50)
        logger.info("[SER] 情感分析流水线初始化中...")
        logger.info("[SER] (声学模型和ASR将在首次分析时按需加载)")
        logger.info("=" * 50)

        # LLM 分析器（纯 API 调用，秒级初始化）
        from app.models.llm_analyzer import LLMEmotionAnalyzer
        self.llm_analyzer = LLMEmotionAnalyzer()
        if self.llm_analyzer.has_api:
            logger.info("  [OK] LLM分析器 (DeepSeek API)")
        else:
            logger.info("  [OK] LLM分析器 (本地规则模式)")

        # 融合引擎（纯计算模块，毫秒级初始化）
        self.fusion_engine = MultiModalFusion()
        logger.info("  [OK] 融合引擎 (Cross-Attention)")

        self._models_ready = True
        logger.info("=" * 50)
        logger.info("[OK] 服务就绪！（声学模型和ASR将在首次分析时加载）")
        logger.info("=" * 50)

    async def _ensure_heavy_models(self):
        """按需加载重型模型（带超时保护，并行加载）"""
        if self.acoustic_analyzer is not None and self.asr_engine is not None:
            return  # 已加载

        # 防止并发重复加载
        async with self._load_lock:
            if self.acoustic_analyzer is not None and self.asr_engine is not None:
                return  # 双重检查

            logger.info("[LOAD] 正在加载声学模型和ASR引擎（首次使用）...")

            async def _load_with_timeout(name, loader, timeout=25):
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(loader), timeout=timeout
                    )
                    logger.info(f"  [OK] {name} 就绪")
                    return result
                except asyncio.TimeoutError:
                    logger.warning(f"  [WARN]{name} 加载超时({timeout}s)，使用降级方案")
                    return None
                except Exception as e:
                    logger.warning(f"  [WARN]{name} 加载失败: {str(e)[:100]}，使用降级方案")
                    return None

            from app.models.acoustic import AcousticEmotionAnalyzer
            from app.models.asr import WhisperASR

            self.acoustic_analyzer, self.asr_engine = await asyncio.gather(
                _load_with_timeout("声学模型", AcousticEmotionAnalyzer, 180),
                _load_with_timeout("ASR引擎", WhisperASR, 60),
            )

            if self.acoustic_analyzer:
                logger.info(f"  声学模型类型: {self.acoustic_analyzer.model_type}")
            if not self.asr_engine:
                logger.warning("  语音转录功能暂不可用，将仅使用LLM进行语义分析")

    @property
    def is_ready(self) -> bool:
        return self._models_ready

    @property
    def models_status(self) -> dict:
        return {
            "acoustic": self.acoustic_analyzer is not None,
            "asr": self.asr_engine is not None,
            "llm": self.llm_analyzer is not None,
            "fusion": self.fusion_engine is not None,
            "pipeline_ready": self._models_ready,
        }

    @staticmethod
    def _fallback_acoustic() -> dict:
        """声学模型完全不可用时的降级结果"""
        return {
            "label": "中性",
            "confidence": 0.25,
            "probabilities": {"开心": 0.15, "悲伤": 0.17, "愤怒": 0.15, "中性": 0.23, "惊讶": 0.15, "恐惧": 0.15},
            "feature_vector": [0.0] * 512,
            "quality": "lowest",
        }

    async def process(
        self,
        audio_path: str,
        original_filename: str,
        fusion_method: str = "late_fusion",
    ) -> dict:
        """处理音频文件，执行完整情感分析流水线"""
        if not self._models_ready:
            raise RuntimeError("流水线尚未初始化完成，请先调用 initialize()")

        task_id = str(uuid.uuid4())
        start_time = time.time()
        logger.info(f"[IN] [{task_id}] 开始处理: {original_filename}")

        # 按需加载重型模型
        await self._ensure_heavy_models()

        # ==================== 阶段1：音频预处理 ====================
        wav_path = await asyncio.to_thread(audio_utils.preprocess, audio_path)
        duration = await asyncio.to_thread(audio_utils.get_duration, wav_path)
        logger.info(f"  [DUR] 音频时长: {duration:.2f}s")

        # ==================== 阶段2：并行分析 ====================
        # 声学分析
        if self.acoustic_analyzer:
            acoustic_result = await asyncio.to_thread(
                self.acoustic_analyzer.analyze, wav_path
            )
        else:
            acoustic_result = self._fallback_acoustic()

        # ASR 转录
        if self.asr_engine:
            transcript = await asyncio.to_thread(
                self.asr_engine.transcribe, wav_path
            )
        else:
            transcript = ""

        logger.info(f"  [ACOUSTIC] 声学: {acoustic_result['label']} ({acoustic_result['confidence']:.2f})")
        logger.info(f"  [TEXT] 转录: {transcript[:80]}{'...' if len(transcript) > 80 else ''}")

        # LLM 语义分析
        semantic_result = await self.llm_analyzer.analyze(transcript)
        logger.info(f"  [LLM] LLM: {semantic_result['label']} ({semantic_result['confidence']:.2f})")

        # ==================== 阶段3：可视化数据 ====================
        waveform_data, spectrogram_url = await asyncio.gather(
            asyncio.to_thread(audio_utils.get_waveform_data, wav_path),
            asyncio.to_thread(audio_utils.generate_spectrogram, wav_path),
        )

        # ==================== 阶段4：多模态融合 ====================
        fused_result = self.fusion_engine.fuse(acoustic_result, semantic_result, method=fusion_method)
        logger.info(f"  [FUSION] 融合: {fused_result['label']} ({fused_result['confidence']:.2f})")

        # ==================== 阶段5：持久化 ====================
        from datetime import datetime
        import shutil

        date_prefix = datetime.utcnow().strftime("%Y%m%d")
        persistent_dir = UPLOAD_DIR / date_prefix
        persistent_dir.mkdir(parents=True, exist_ok=True)
        persistent_path = persistent_dir / f"{task_id}_{original_filename}"
        shutil.copy2(wav_path, str(persistent_path))

        # ==================== 阶段6：组装结果 ====================
        processing_time = round(time.time() - start_time, 3)

        result = {
            "task_id": task_id,
            "duration": round(duration, 2),
            "sample_rate": 16000,
            "transcript": transcript,
            "acoustic_emotion": {
                "label": acoustic_result["label"],
                "confidence": round(acoustic_result["confidence"], 4),
                "probabilities": {k: round(v, 4) for k, v in acoustic_result["probabilities"].items()},
            },
            "semantic_emotion": {
                "label": semantic_result["label"],
                "confidence": round(semantic_result["confidence"], 4),
                "probabilities": {k: round(v, 4) for k, v in semantic_result["probabilities"].items()},
                "reasoning": semantic_result.get("reasoning", ""),
                "key_phrases": semantic_result.get("key_phrases", []),
                "model": semantic_result.get("model", "unknown"),
            },
            "fused_emotion": fused_result,
            "waveform": waveform_data,
            "spectrogram_url": spectrogram_url,
            "processing_time": processing_time,
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"[OK] [{task_id}] 完成: {processing_time}s | {acoustic_result['label']}→{semantic_result['label']}→{fused_result['label']}")

        return {
            "task_id": task_id,
            "persistent_path": str(persistent_path),
            "result": result,
        }


# 全局单例
pipeline = EmotionAnalysisPipeline()
