"""
FastAPI 应用入口
---------------
中文语音情感识别系统后端服务
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import API_HOST, API_PORT, CORS_ORIGINS, STATIC_DIR
from app.api.routes import router as api_router
from app.db.database import init_db
from app.services.pipeline import pipeline
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时：初始化数据库、加载模型
    - 关闭时：清理资源
    """
    logger.info("=" * 60)
    logger.info("[SER] 中文语音情感识别系统 - 后端服务启动中...")
    logger.info("=" * 60)

    # 初始化数据库表
    try:
        init_db()
        logger.info("[OK] 数据库初始化完成")
    except Exception as e:
        logger.error(f"[FAIL] 数据库初始化失败: {e}")

    # 加载 AI 模型（启动时不下载，首次使用时延迟加载）
    try:
        await pipeline.initialize()
    except Exception as e:
        logger.error(f"[FAIL] 模型加载失败: {e}")
        logger.warning("[WARN] 服务将以降级模式运行，部分功能可能不可用")

    logger.info(f"[API] http://{API_HOST}:{API_PORT}")
    logger.info(f"[DOC] http://{API_HOST}:{API_PORT}/docs")
    logger.info("=" * 60)

    yield  # 服务运行期间

    # 关闭时的清理工作
    logger.info("[STOP] 服务正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title="中文语音情感识别系统",
    description="""
    ## 🎙️ 基于大语言模型的中文语音情感识别系统

    ### 核心功能
    - 🎵 **声学分析**: 基于 HuBERT/emotion2vec 的语音情感特征提取
    - 📝 **语音转写**: 基于 Whisper 的高精度中文语音识别
    - 🤖 **LLM语义分析**: 基于 DeepSeek 大语言模型的深度语义情感理解
    - 🔗 **多模态融合**: Cross-Attention 跨模态特征融合

    ### 支持的情感类别
    开心 | 悲伤 | 愤怒 | 中性 | 惊讶 | 恐惧

    ### 支持的音频格式
    WAV | MP3 | WEBM | M4A | FLAC | OGG | AAC
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 注册路由
app.include_router(api_router)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常捕获"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "detail": str(exc) if app.debug else None,
        },
    )


# 根路径
@app.get("/")
async def root():
    """服务根路径"""
    return {
        "name": "中文语音情感识别系统",
        "version": "1.0.0",
        "status": "running" if pipeline.is_ready else "initializing",
        "docs": "/docs",
        "models": pipeline.models_status,
    }
