"""
API 请求/响应数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class EmotionResult(BaseModel):
    """单通道情感分析结果"""
    label: str = Field(..., description="情感标签")
    confidence: float = Field(..., description="置信度")
    probabilities: Dict[str, float] = Field(..., description="各类别概率")


class SemanticEmotionResult(EmotionResult):
    """LLM语义通道结果（额外包含推理过程）"""
    reasoning: str = Field("", description="LLM推理过程")
    key_phrases: List[str] = Field(default_factory=list, description="关键情感词汇")
    model: str = Field("deepseek-v3", description="使用的LLM模型")


class FusedEmotionResult(EmotionResult):
    """融合后的情感结果"""
    fusion_method: str = Field("late_fusion", description="融合方法")
    fusion_weight: Dict[str, float] = Field(default_factory=dict, description="各通道权重")


class WaveformData(BaseModel):
    """波形数据"""
    samples: List[float] = Field(default_factory=list, description="归一化采样点")
    time_axis: List[float] = Field(default_factory=list, description="时间轴")


class AnalysisResponse(BaseModel):
    """POST /api/analyze 完整响应"""
    task_id: str = Field(..., description="任务ID")
    duration: float = Field(..., description="音频时长(秒)")
    sample_rate: int = Field(16000, description="采样率")
    transcript: str = Field("", description="Whisper转录文本")
    acoustic_emotion: Optional[EmotionResult] = Field(None, description="声学通道结果")
    semantic_emotion: Optional[SemanticEmotionResult] = Field(None, description="LLM语义通道结果")
    fused_emotion: FusedEmotionResult = Field(..., description="融合后最终结果")
    waveform: Optional[WaveformData] = Field(None, description="波形数据")
    spectrogram_url: Optional[str] = Field(None, description="频谱图URL")
    processing_time: float = Field(..., description="处理耗时(秒)")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HistoryItem(BaseModel):
    """历史记录列表项"""
    id: str
    audio_filename: str
    transcript_preview: str = ""
    emotion_label: str
    confidence: float
    duration: float
    created_at: datetime


class HistoryListResponse(BaseModel):
    """历史记录列表"""
    total: int
    items: List[HistoryItem]


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    version: str = "1.0.0"
    models_loaded: Dict[str, bool] = Field(default_factory=dict)
