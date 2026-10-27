"""
语音识别模块 (ASR)
------------------
使用 faster-whisper 将语音转为文字
CPU 优化：使用 CTranslate2 加速推理
"""

from app.config import WHISPER_MODEL_SIZE
from app.utils.logger import logger


class WhisperASR:
    """
    语音识别引擎

    使用 faster-whisper (CTranslate2 加速的 Whisper)
    CPU 推理速度比原版快 3-4 倍
    """

    def __init__(self):
        self.model = None
        self.model_size = WHISPER_MODEL_SIZE
        self._init_model()

    def _init_model(self):
        """加载 Whisper 模型"""
        try:
            from faster_whisper import WhisperModel

            # 使用 int8 量化加速 CPU 推理
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",  # CPU 推理用 int8 量化
                num_workers=2,
            )
            logger.info(f"✅ ASR模型: faster-whisper-{self.model_size}")
        except Exception as e:
            logger.warning(f"faster-whisper 加载失败: {e}, 尝试 openai-whisper")
            self._init_openai_whisper()

    def _init_openai_whisper(self):
        """回退到 openai-whisper"""
        try:
            import whisper
            self.model = whisper.load_model(self.model_size)
            self._use_openai = True
            logger.info(f"✅ ASR模型: openai-whisper-{self.model_size}")
        except Exception as e:
            logger.error(f"Whisper 加载失败: {e}")
            self.model = None

    def transcribe(self, audio_path: str) -> str:
        """
        语音转文字

        参数:
            audio_path: 音频文件路径

        返回:
            str: 转录文本，若失败返回空字符串
        """
        if self.model is None:
            logger.error("ASR 模型未加载")
            return ""

        try:
            if hasattr(self, "_use_openai") and self._use_openai:
                return self._transcribe_openai(audio_path)
            else:
                return self._transcribe_faster(audio_path)
        except Exception as e:
            logger.error(f"语音转录失败: {e}")
            return ""

    def _transcribe_faster(self, audio_path: str) -> str:
        """使用 faster-whisper 转录"""
        segments, info = self.model.transcribe(
            audio_path,
            language="zh",
            beam_size=5,
            vad_filter=True,  # 过滤静音
        )

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        transcript = " ".join(text_parts)
        logger.info(f"ASR 转录完成 ({info.language}, {info.duration:.1f}s): {transcript[:50]}...")
        return transcript

    def _transcribe_openai(self, audio_path: str) -> str:
        """使用 openai-whisper 转录"""
        result = self.model.transcribe(
            audio_path,
            language="zh",
            task="transcribe",
        )
        transcript = result.get("text", "").strip()
        logger.info(f"ASR 转录完成: {transcript[:50]}...")
        return transcript
