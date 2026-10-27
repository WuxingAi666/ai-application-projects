"""
SQLAlchemy ORM 模型
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Text, DateTime, JSON

from app.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class AnalysisRecord(Base):
    """分析记录表"""
    __tablename__ = "analysis_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audio_filename = Column(String(255), nullable=False, comment="原始音频文件名")
    audio_path = Column(String(500), nullable=False, comment="音频文件存储路径")
    duration = Column(Float, nullable=False, comment="音频时长(秒)")

    # 转录文本
    transcript = Column(Text, nullable=True, comment="Whisper转录文本")

    # 声学通道结果
    acoustic_label = Column(String(20), nullable=True, comment="声学情感标签")
    acoustic_probs = Column(JSON, nullable=True, comment="声学情感概率分布")

    # LLM语义通道结果
    semantic_label = Column(String(20), nullable=True, comment="语义情感标签")
    semantic_probs = Column(JSON, nullable=True, comment="语义情感概率分布")
    semantic_reasoning = Column(Text, nullable=True, comment="LLM推理过程")
    semantic_model = Column(String(50), nullable=True, comment="使用的LLM模型")

    # 融合结果
    fused_label = Column(String(20), nullable=False, comment="融合后情感标签")
    fused_probs = Column(JSON, nullable=False, comment="融合后概率分布")
    fusion_method = Column(String(30), default="late_fusion", comment="融合方法")
    fusion_weight = Column(JSON, nullable=True, comment="融合权重")

    # 元数据
    processing_time = Column(Float, nullable=False, comment="处理耗时(秒)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    def to_dict(self) -> dict:
        """转为字典"""
        return {
            "id": self.id,
            "audio_filename": self.audio_filename,
            "duration": self.duration,
            "transcript": self.transcript or "",
            "acoustic_emotion": {
                "label": self.acoustic_label,
                "confidence": max(self.acoustic_probs.values()) if self.acoustic_probs else 0,
                "probabilities": self.acoustic_probs or {},
            } if self.acoustic_label else None,
            "semantic_emotion": {
                "label": self.semantic_label,
                "confidence": max(self.semantic_probs.values()) if self.semantic_probs else 0,
                "probabilities": self.semantic_probs or {},
                "reasoning": self.semantic_reasoning or "",
                "model": self.semantic_model or "",
                "key_phrases": [],
            } if self.semantic_label else None,
            "fused_emotion": {
                "label": self.fused_label,
                "confidence": max(self.fused_probs.values()) if self.fused_probs else 0,
                "probabilities": self.fused_probs or {},
                "fusion_method": self.fusion_method or "late_fusion",
                "fusion_weight": self.fusion_weight or {},
            },
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
