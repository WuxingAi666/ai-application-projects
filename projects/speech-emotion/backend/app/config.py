"""
应用配置管理
-----------
集中管理所有配置：模型路径、API密钥、服务参数等
"""

import os
from pathlib import Path

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

# 修复 numpy 2.x 在 Windows 上的 LLVM/SVML 兼容性问题
os.environ.setdefault("NPY_DISABLE_SVML", "1")

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "samples"
STATIC_DIR = DATA_DIR / "static"

# 模型目录
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

# 确保目录存在
for d in [UPLOAD_DIR, SAMPLE_DIR, STATIC_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============ DeepSeek API 配置 ============
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

# ============ 模型配置 ============
# 声学情感模型（使用 emotion2vec 或 HuBERT）
ACOUSTIC_MODEL_NAME = "emotion2vec"  # 可选: "hubert", "mfcc_cnn"
# Whisper 模型大小 (tiny/base/small/medium/large)
WHISPER_MODEL_SIZE = "base"

# HuggingFace 镜像（国内加速）+ 超时保护
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "15")   # 15秒下载超时
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "5")         # 5秒连接超时
os.environ.setdefault("REQUESTS_CA_BUNDLE", os.environ.get("REQUESTS_CA_BUNDLE", ""))

# ============ 音频配置 ============
TARGET_SAMPLE_RATE = 16000  # 目标采样率
MAX_AUDIO_DURATION = 30     # 最大音频时长（秒）
AUDIO_CHANNELS = 1          # 单声道

# ============ 情感类别 ============
EMOTION_LABELS = ["开心", "悲伤", "愤怒", "中性", "惊讶", "恐惧"]
EMOTION_LABELS_EN = ["happy", "sad", "angry", "neutral", "surprise", "fear"]

# ============ 服务配置 ============
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

# ============ 数据库配置 ============
# Windows 路径需要转为正斜杠格式，确保 URL 解析正确
_DB_PATH = (DATA_DIR / "analysis_history.db").as_posix()
DATABASE_URL = f"sqlite+aiosqlite:///{_DB_PATH}"
DATABASE_URL_SYNC = f"sqlite:///{_DB_PATH}"
