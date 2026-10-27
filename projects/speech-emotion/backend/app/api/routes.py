"""
API 路由定义
-----------
所有 REST API 端点
"""

import os
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    AnalysisResponse, HistoryItem, HistoryListResponse,
    ErrorResponse, HealthResponse,
)
from app.db.database import get_db, AsyncSessionLocal
from app.db.models import AnalysisRecord
from app.services.pipeline import pipeline
from app.config import UPLOAD_DIR, STATIC_DIR
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["情感分析"])


# ==================== 健康检查 ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """系统健康检查 + 模型状态"""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        models_loaded=pipeline.models_status,
    )


# ==================== 核心接口：音频分析 ====================

@router.post("/analyze", response_model=dict)
async def analyze_audio(
    audio: UploadFile = File(..., description="音频文件 (WAV/MP3/WEBM/M4A)"),
    fusion_method: str = Query("late_fusion", description="融合方法"),
):
    """
    🎙️ 上传音频文件并执行情感分析

    - **audio**: 音频文件，支持 WAV/MP3/WEBM/M4A 格式
    - **fusion_method**: 融合方法 (cross_attention / late_fusion / early_fusion)

    返回完整的三通道分析结果 + 可视化数据
    """
    # 校验文件
    if not audio.filename:
        raise HTTPException(status_code=400, detail="未提供音频文件")

    allowed_ext = {".wav", ".mp3", ".webm", ".m4a", ".flac", ".ogg", ".aac"}
    ext = Path(audio.filename).suffix.lower()
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式: {ext}，支持: {', '.join(allowed_ext)}",
        )

    # 校验融合方法
    allowed_methods = {"late_fusion", "late_fusion", "early_fusion"}
    if fusion_method not in allowed_methods:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的融合方法: {fusion_method}，支持: {', '.join(allowed_methods)}",
        )

    # 保存上传文件到临时目录
    temp_dir = UPLOAD_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{uuid.uuid4()}{ext}"

    try:
        content = await audio.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="上传的音频文件为空")

        if len(content) > 50 * 1024 * 1024:  # 50MB 限制
            raise HTTPException(status_code=400, detail="音频文件过大（最大50MB）")

        temp_path.write_bytes(content)
        logger.info(f"收到音频: {audio.filename} ({len(content)/1024:.1f}KB)")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件保存失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 执行分析流水线
    try:
        pipe_result = await pipeline.process(
            str(temp_path),
            audio.filename,
            fusion_method,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"分析流水线失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
    finally:
        # 清理临时文件
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass

    # 持久化到数据库
    try:
        async with AsyncSessionLocal() as session:
            record = AnalysisRecord(
                id=pipe_result["task_id"],
                audio_filename=audio.filename,
                audio_path=pipe_result["persistent_path"],
                duration=pipe_result["result"]["duration"],
                transcript=pipe_result["result"]["transcript"],
                acoustic_label=pipe_result["result"]["acoustic_emotion"]["label"],
                acoustic_probs=pipe_result["result"]["acoustic_emotion"]["probabilities"],
                semantic_label=pipe_result["result"]["semantic_emotion"]["label"],
                semantic_probs=pipe_result["result"]["semantic_emotion"]["probabilities"],
                semantic_reasoning=pipe_result["result"]["semantic_emotion"].get("reasoning", ""),
                semantic_model=pipe_result["result"]["semantic_emotion"].get("model", ""),
                fused_label=pipe_result["result"]["fused_emotion"]["label"],
                fused_probs=pipe_result["result"]["fused_emotion"]["probabilities"],
                fusion_method=fusion_method,
                fusion_weight=pipe_result["result"]["fused_emotion"].get("fusion_weight", {}),
                processing_time=pipe_result["result"]["processing_time"],
                created_at=datetime.utcnow(),
            )
            session.add(record)
            await session.commit()
            logger.info(f"结果已保存到数据库: {pipe_result['task_id']}")
    except Exception as e:
        logger.error(f"数据库保存失败: {e}（分析结果仍会返回）")

    return {
        "code": 200,
        "message": "分析完成",
        "data": pipe_result["result"],
    }


# ==================== 语音播报 ====================

@router.post("/voice/{task_id}")
async def get_voice_feedback(task_id: str):
    """
    获取 AI 生成的语音播报文本

    根据情感分析结果，用 LLM 生成个性化的反馈文本
    前端使用浏览器 Web Speech API 播报
    """
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(AnalysisRecord).where(AnalysisRecord.id == task_id)
            record = (await session.execute(stmt)).scalar_one_or_none()

            if record is None:
                raise HTTPException(status_code=404, detail="记录不存在")

            result = record.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # 生成反馈文本
    from app.services.voice_assistant import voice_assistant

    try:
        text = await voice_assistant.generate_feedback_text(result)

        return {
            "code": 200,
            "data": {
                "text": text,
            },
        }

    except Exception as e:
        logger.error(f"语音文本生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# ==================== 历史记录 ====================

@router.get("/history", response_model=dict)
async def get_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取历史分析记录列表"""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, func, desc

            # 查询总数
            count_stmt = select(func.count(AnalysisRecord.id))
            total = (await session.execute(count_stmt)).scalar()

            # 分页查询
            stmt = (
                select(AnalysisRecord)
                .order_by(desc(AnalysisRecord.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            records = (await session.execute(stmt)).scalars().all()

            items = []
            for r in records:
                transcript = r.transcript or ""
                items.append({
                    "id": r.id,
                    "audio_filename": r.audio_filename,
                    "transcript_preview": transcript[:50] + ("..." if len(transcript) > 50 else ""),
                    "emotion_label": r.fused_label,
                    "confidence": max(r.fused_probs.values()) if r.fused_probs else 0,
                    "duration": r.duration,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                })

            return {
                "code": 200,
                "data": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "items": items,
                },
            }
    except Exception as e:
        logger.error(f"查询历史记录失败: {e}")
        return {"code": 200, "data": {"total": 0, "page": page, "items": []}}


@router.get("/history/{record_id}")
async def get_history_detail(record_id: str):
    """获取单条分析记录详情"""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(AnalysisRecord).where(AnalysisRecord.id == record_id)
            record = (await session.execute(stmt)).scalar_one_or_none()

            if record is None:
                raise HTTPException(status_code=404, detail="记录不存在")

            return {"code": 200, "data": record.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询记录详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{record_id}")
async def delete_history(record_id: str):
    """删除一条分析记录"""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(AnalysisRecord).where(AnalysisRecord.id == record_id)
            record = (await session.execute(stmt)).scalar_one_or_none()

            if record is None:
                raise HTTPException(status_code=404, detail="记录不存在")

            # 删除音频文件
            if record.audio_path and os.path.exists(record.audio_path):
                try:
                    os.remove(record.audio_path)
                except Exception:
                    pass

            await session.delete(record)
            await session.commit()

            return {"code": 200, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 静态文件 ====================

@router.get("/static/{filename}")
async def serve_static(filename: str):
    """提供频谱图等静态文件"""
    file_path = STATIC_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(file_path))
