"""
音频预处理工具
-------------
负责音频格式转换、重采样、特征提取等
"""

import subprocess
import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from app.config import TARGET_SAMPLE_RATE, AUDIO_CHANNELS, MAX_AUDIO_DURATION, STATIC_DIR
from app.utils.logger import logger


class AudioUtils:
    """音频处理工具类"""

    @staticmethod
    def preprocess(audio_path: str) -> str:
        """
        音频预处理流水线：
        1. 格式转换（webm/mp3/m4a → wav）
        2. 重采样到 16kHz
        3. 转为单声道
        4. 截断过长音频
        """
        # 先用 FFmpeg 统一转为标准 WAV
        converted = AudioUtils._convert_to_wav(audio_path)

        # 用 librosa 加载并处理
        waveform, sr = librosa.load(
            converted,
            sr=TARGET_SAMPLE_RATE,
            mono=True,
            duration=MAX_AUDIO_DURATION,
        )

        # 保存处理后的文件
        output_path = str(Path(audio_path).with_suffix(".processed.wav"))
        sf.write(output_path, waveform, TARGET_SAMPLE_RATE)

        logger.info(f"音频预处理完成: {output_path}, 时长={len(waveform)/TARGET_SAMPLE_RATE:.2f}s")
        return output_path

    @staticmethod
    def _convert_to_wav(audio_path: str) -> str:
        """使用 FFmpeg 将任意格式转为标准 WAV"""
        output_path = str(Path(audio_path).with_suffix(".converted.wav"))

        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-ar", str(TARGET_SAMPLE_RATE),
            "-ac", str(AUDIO_CHANNELS),
            "-sample_fmt", "s16",
            output_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=30)
        except subprocess.TimeoutExpired:
            logger.warning("FFmpeg 转换超时，尝试直接加载原始文件")
            return audio_path
        except subprocess.CalledProcessError as e:
            logger.warning(f"FFmpeg 转换失败: {e.stderr.decode()}, 尝试直接加载")
            return audio_path

        return output_path

    @staticmethod
    def get_waveform_data(audio_path: str, max_points: int = 2000) -> dict:
        """
        提取波形数据（用于前端渲染）
        返回归一化的采样点和时间轴
        """
        waveform, sr = librosa.load(audio_path, sr=TARGET_SAMPLE_RATE, mono=True)

        # 降采样到 max_points 个点
        if len(waveform) > max_points:
            indices = np.linspace(0, len(waveform) - 1, max_points, dtype=int)
            waveform = waveform[indices]

        # 归一化
        peak = np.max(np.abs(waveform))
        if peak > 0:
            waveform = waveform / peak

        time_axis = np.linspace(0, len(waveform) / sr, len(waveform))

        return {
            "samples": waveform.tolist(),
            "time_axis": time_axis.tolist(),
        }

    @staticmethod
    def generate_spectrogram(audio_path: str) -> str:
        """
        生成梅尔频谱图并保存为图片
        返回图片 URL 路径
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        waveform, sr = librosa.load(audio_path, sr=TARGET_SAMPLE_RATE, mono=True)

        # 生成梅尔频谱
        mel_spec = librosa.feature.melspectrogram(
            y=waveform, sr=sr,
            n_mels=128, fmax=8000,
            hop_length=256, n_fft=1024,
        )
        log_mel = librosa.power_to_db(mel_spec, ref=np.max)

        # 绘图
        fig, ax = plt.subplots(figsize=(8, 3))
        img = librosa.display.specshow(
            log_mel, sr=sr, hop_length=256,
            x_axis="time", y_axis="mel",
            fmax=8000, ax=ax, cmap="magma",
        )
        ax.set_title("Mel Spectrogram", fontsize=10)
        fig.colorbar(img, ax=ax, format="%+2.0f dB")

        # 保存
        spec_filename = f"spec_{Path(audio_path).stem}.png"
        spec_path = STATIC_DIR / spec_filename
        plt.savefig(spec_path, dpi=100, bbox_inches="tight")
        plt.close(fig)

        return f"/static/{spec_filename}"

    @staticmethod
    def get_duration(audio_path: str) -> float:
        """获取音频时长"""
        return librosa.get_duration(path=audio_path)


audio_utils = AudioUtils()
