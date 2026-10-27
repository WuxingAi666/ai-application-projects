"""
多模态情感融合模块
------------------
实现多种融合策略，将声学通道和语义通道的情感分析结果融合
"""

import numpy as np
import torch
import torch.nn as nn

from app.config import EMOTION_LABELS
from app.utils.logger import logger


class MultiModalFusion:
    """
    多模态情感融合器

    支持三种融合策略：
    1. cross_attention — 跨模态注意力（推荐，最具创新性）
    2. late_fusion — 晚融合（加权平均决策层概率）
    3. early_fusion — 早融合（拼接特征向量）
    """

    EMOTIONS = EMOTION_LABELS

    def __init__(self):
        self.device = torch.device("cpu")
        self.cross_attn = CrossAttentionFusion(
            acoustic_dim=512,
            semantic_dim=768,
            hidden_dim=256,
            num_classes=len(self.EMOTIONS),
        ).to(self.device)
        self.cross_attn.eval()

    def fuse(
        self,
        acoustic_result: dict,
        semantic_result: dict,
        method: str = "late_fusion",
    ) -> dict:
        """
        融合声学和语义分析结果

        参数:
            acoustic_result: 声学分析结果 {"label", "confidence", "probabilities", "feature_vector"}
            semantic_result: 语义分析结果 {"label", "confidence", "probabilities", "reasoning", "feature_vector"}
            method: 融合方法

        返回:
            dict: 融合后的结果
        """
        if method == "cross_attention":
            return self._cross_attention_fusion(acoustic_result, semantic_result)
        elif method == "late_fusion":
            return self._late_fusion(acoustic_result, semantic_result)
        elif method == "early_fusion":
            return self._early_fusion(acoustic_result, semantic_result)
        else:
            logger.warning(f"未知融合方法: {method}, 回退到 late_fusion")
            return self._late_fusion(acoustic_result, semantic_result)

    def _cross_attention_fusion(self, acoustic: dict, semantic: dict) -> dict:
        """跨模态注意力融合（推荐）"""
        try:
            # 获取特征向量
            fa = acoustic.get("feature_vector", np.random.randn(512).tolist())
            ft = semantic.get("feature_vector", [0.0] * 768)

            # 截断/填充到目标维度
            fa = self._pad_or_truncate(fa, 512)
            ft = self._pad_or_truncate(ft, 768)

            fa_tensor = torch.FloatTensor(fa).unsqueeze(0).to(self.device)
            ft_tensor = torch.FloatTensor(ft).unsqueeze(0).to(self.device)

            with torch.no_grad():
                logits = self.cross_attn(fa_tensor, ft_tensor)
                probs = torch.softmax(logits, dim=-1).squeeze().cpu().numpy()

            best_idx = int(np.argmax(probs))

            # 计算融合权重（可解释性）
            acoustic_conf = acoustic.get("confidence", 0.5)
            semantic_conf = semantic.get("confidence", 0.5)
            total = acoustic_conf + semantic_conf
            fusion_weight = {
                "acoustic": round(acoustic_conf / total, 2) if total > 0 else 0.5,
                "semantic": round(semantic_conf / total, 2) if total > 0 else 0.5,
            }

            logger.info(f"Cross-Attention 融合完成: {self.EMOTIONS[best_idx]} (权重={fusion_weight})")

            return {
                "label": self.EMOTIONS[best_idx],
                "confidence": round(float(probs[best_idx]), 4),
                "probabilities": {e: round(float(probs[i]), 4) for i, e in enumerate(self.EMOTIONS)},
                "fusion_method": "late_fusion",
                "fusion_weight": fusion_weight,
            }
        except Exception as e:
            logger.error(f"Cross-Attention 融合失败: {e}, 回退到 late_fusion")
            return self._late_fusion(acoustic, semantic)

    def _late_fusion(self, acoustic: dict, semantic: dict) -> dict:
        """晚融合：根据置信度和质量等级动态加权"""
        acoustic_probs = acoustic.get("probabilities", {})
        semantic_probs = semantic.get("probabilities", {})

        acoustic_conf = acoustic.get("confidence", 0.3)
        semantic_conf = semantic.get("confidence", 0.5)
        acoustic_quality = acoustic.get("quality", "low")

        # 质量等级决定声学最大权重上限
        quality_max_weight = {"high": 0.55, "medium": 0.40, "low": 0.20, "lowest": 0.05}

        # 计算理想声学权重
        if acoustic_quality in ("low", "lowest"):
            # 声学质量差，LLM说了算
            w_a = 0.05 if acoustic_quality == "lowest" else 0.10
        elif semantic_conf > 0.85:
            w_a = 0.15  # LLM很确信
        elif semantic_conf > 0.6:
            w_a = 0.25  # LLM较确信
        else:
            # 两者都中等置信度，声学有话语权但不能太大
            w_a = min(0.40, acoustic_conf)

        # 不超过质量等级允许的上限
        max_w = quality_max_weight.get(acoustic_quality, 0.20)
        w_a = min(w_a, max_w)
        w_s = 1.0 - w_a

        fused_probs = {}
        for e in self.EMOTIONS:
            p_a = float(acoustic_probs.get(e, 0.0))
            p_s = float(semantic_probs.get(e, 0.0))
            fused_probs[e] = round(w_a * p_a + w_s * p_s, 4)

        # 归一化
        total = sum(fused_probs.values())
        if total > 0:
            fused_probs = {k: round(v / total, 4) for k, v in fused_probs.items()}

        best_emotion = max(fused_probs, key=fused_probs.get)

        logger.info(f"晚融合完成: {best_emotion} (声学={acoustic_conf:.0%}*{w_a:.0%} + LLM={semantic_conf:.0%}*{w_s:.0%})")

        return {
            "label": best_emotion,
            "confidence": fused_probs[best_emotion],
            "probabilities": fused_probs,
            "fusion_method": "late_fusion",
            "fusion_weight": {"acoustic": round(w_a, 2), "semantic": round(w_s, 2)},
        }

    def _early_fusion(self, acoustic: dict, semantic: dict) -> dict:
        """早融合：拼接特征向量后分类（简单实现）"""
        # 取两个通道的概率分布作为特征
        acoustic_probs = [float(acoustic.get("probabilities", {}).get(e, 0.0)) for e in self.EMOTIONS]
        semantic_probs = [float(semantic.get("probabilities", {}).get(e, 0.0)) for e in self.EMOTIONS]

        # 拼接
        fused_feature = acoustic_probs + semantic_probs  # 12维

        # 加权（声学60%，语义40%作为默认）
        fused_probs = {}
        for i, e in enumerate(self.EMOTIONS):
            fused_probs[e] = round(0.4 * fused_feature[i] + 0.6 * fused_feature[i + 6], 4)

        # 归一化
        total = sum(fused_probs.values())
        if total > 0:
            fused_probs = {k: round(v / total, 4) for k, v in fused_probs.items()}

        best_emotion = max(fused_probs, key=fused_probs.get)

        return {
            "label": best_emotion,
            "confidence": fused_probs[best_emotion],
            "probabilities": fused_probs,
            "fusion_method": "early_fusion",
            "fusion_weight": {"acoustic": 0.4, "semantic": 0.6},
        }

    @staticmethod
    def _pad_or_truncate(vec: list, target_dim: int) -> list:
        """填充或截断向量到目标维度"""
        if len(vec) >= target_dim:
            return vec[:target_dim]
        else:
            return vec + [0.0] * (target_dim - len(vec))


class CrossAttentionFusion(nn.Module):
    """
    跨模态注意力融合模块

    核心思想：
    - 声学特征 Fa 作为 Query 去关注语义特征 Ft（声学"看"语义相关部分）
    - 语义特征 Ft 作为 Query 去关注声学特征 Fa（语义"听"声学相关部分）
    - 双方向交互后的特征拼接 → 分类器
    """

    def __init__(
        self,
        acoustic_dim: int = 512,
        semantic_dim: int = 768,
        hidden_dim: int = 256,
        num_classes: int = 6,
        num_heads: int = 4,
    ):
        super().__init__()

        # 投影层：将两个模态对齐到相同维度
        self.proj_a = nn.Linear(acoustic_dim, hidden_dim)
        self.proj_s = nn.Linear(semantic_dim, hidden_dim)

        # Cross-Attention 层
        self.cross_a2s = nn.MultiheadAttention(
            hidden_dim, num_heads, batch_first=True, dropout=0.1
        )
        self.cross_s2a = nn.MultiheadAttention(
            hidden_dim, num_heads, batch_first=True, dropout=0.1
        )

        # Layer Norm
        self.norm_a = nn.LayerNorm(hidden_dim)
        self.norm_s = nn.LayerNorm(hidden_dim)

        # 融合分类层
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, num_classes),
        )

    def forward(self, acoustic_feat: torch.Tensor, semantic_feat: torch.Tensor):
        """
        参数:
            acoustic_feat: [B, acoustic_dim]  声学特征
            semantic_feat: [B, semantic_dim]  语义特征

        返回:
            logits: [B, num_classes]
        """
        # 投影
        Fa = self.proj_a(acoustic_feat).unsqueeze(1)  # [B, 1, H]
        Ft = self.proj_s(semantic_feat).unsqueeze(1)  # [B, 1, H]

        # Fa 查询 Ft（声学关注语义）
        Fa_attn, _ = self.cross_a2s(Fa, Ft, Ft)
        Fa_enhanced = self.norm_a(Fa + Fa_attn)  # 残差连接

        # Ft 查询 Fa（语义关注声学）
        Ft_attn, _ = self.cross_s2a(Ft, Fa, Fa)
        Ft_enhanced = self.norm_s(Ft + Ft_attn)  # 残差连接

        # 拼接并分类
        fused = torch.cat([Fa_enhanced.squeeze(1), Ft_enhanced.squeeze(1)], dim=-1)
        logits = self.classifier(fused)

        return logits
