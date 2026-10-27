"""
智能语音播报助手
---------------
基于 DeepSeek 生成情感分析总结 + edge-tts 语音合成
提供自然、温暖、有建设性的语音反馈
"""

import asyncio
import tempfile
import os
from pathlib import Path
from app.utils.logger import logger
from app.config import EMOTION_LABELS, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

# 情感对应的建议和反馈模板
EMOTION_ADVICE = {
    "开心": {
        "acknowledge": "听起来你现在心情很不错！",
        "advice": "保持这份好心情，可以记录下今天让你开心的事情，或者和朋友分享一下这份快乐。",
    },
    "悲伤": {
        "acknowledge": "我能感受到你现在有些难过。",
        "advice": "每个人都会有情绪低落的时候，这很正常。试着深呼吸几次，或者找个信任的人聊一聊，不要把情绪憋在心里。如果持续感到低落，也可以听听喜欢的音乐、出去走走。",
    },
    "愤怒": {
        "acknowledge": "听起来你现在有些生气。",
        "advice": "愤怒是正常的情绪反应。建议你先深呼吸几次，从一数到十，让自己冷静下来。待情绪平复后，再理性地分析问题，寻找解决方案会更有效。",
    },
    "中性": {
        "acknowledge": "你现在的情绪比较平稳。",
        "advice": "保持平稳的心态很好，这是高效工作和学习的最佳状态。可以继续专注于手头的事情。",
    },
    "惊讶": {
        "acknowledge": "听起来你遇到了让你意外的事情。",
        "advice": "生活中总会有惊喜和意外。不妨停下来好好感受这一刻，无论是好是坏，都是独特的经历。",
    },
    "恐惧": {
        "acknowledge": "我能感受到你现在有些担忧和不安。",
        "advice": "恐惧是人类的自我保护机制。试着分析一下让你害怕的具体是什么，把它写下来，往往会发现事情没有想象中那么可怕。需要的时候可以向身边的人寻求支持。",
    },
}


# 语音文件缓存 {task_id: audio_path}
_voice_cache: dict = {}


class VoiceAssistant:
    """
    智能语音播报助手

    工作流程：
    1. 接收情感分析结果
    2. 用 LLM 生成自然、个性化的反馈文本
    3. 用 edge-tts 合成语音
    4. 返回音频文件路径和文本
    """

    def __init__(self):
        self.tts_available = False
        self._check_tts()

    def _check_tts(self):
        """检查 TTS 是否可用"""
        try:
            import edge_tts  # noqa: F401
            self.tts_available = True
            logger.info("[OK] 语音播报: edge-tts (Microsoft Neural TTS)")
        except ImportError:
            logger.warning("[WARN] edge-tts 未安装，语音播报功能不可用")
            self.tts_available = False

    async def generate_feedback_text(self, result: dict) -> str:
        """
        生成情感分析反馈文本

        先用 LLM 生成，如果失败则用预置模板
        """
        # 提取关键信息
        fused = result.get("fused_emotion", {})
        acoustic = result.get("acoustic_emotion", {})
        semantic = result.get("semantic_emotion", {})
        transcript = result.get("transcript", "")
        primary_emotion = fused.get("label", "中性")
        confidence = fused.get("confidence", 0)

        # 尝试用 LLM 生成个性化反馈
        llm_text = await self._llm_generate_feedback(
            primary_emotion, confidence, transcript,
            acoustic.get("label", ""), semantic.get("label", ""),
        )

        if llm_text:
            return llm_text

        # 回退到模板
        return self._template_feedback(primary_emotion, confidence, transcript)

    async def _llm_generate_feedback(
        self, emotion: str, confidence: float, transcript: str,
        acoustic_label: str, semantic_label: str,
    ) -> str | None:
        """用 LLM 生成个性化反馈"""
        try:
            from openai import AsyncOpenAI

            if not DEEPSEEK_API_KEY:
                return None

            client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

            prompt = f"""你是一个温暖、专业的语音情感助手。请根据以下情感分析结果，生成一段30-50字的语音播报反馈。

分析结果：
- 主要情绪：{emotion}（置信度 {confidence:.0%}）
- 声学分析判断：{acoustic_label}
- 语义分析判断：{semantic_label}
- 用户说的话："{transcript}"（可能为空）

要求：
1. 语气温暖、自然、口语化，像朋友在对话
2. 先简要反馈检测到的情绪
3. 给出一句简短实用的建议
4. 总长度控制在30-50字，适合语音播报
5. 不要使用任何markdown或特殊符号
6. 直接给出播报文本，不要添加任何前缀"""

            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
            )
            text = response.choices[0].message.content.strip()
            if text and len(text) > 5:
                logger.info(f"LLM 生成反馈: {text[:50]}...")
                return text
            return None

        except Exception as e:
            logger.warning(f"LLM 生成反馈失败: {e}")
            return None

    def _template_feedback(self, emotion: str, confidence: float, transcript: str) -> str:
        """使用预置模板生成反馈"""
        cfg = EMOTION_ADVICE.get(emotion, EMOTION_ADVICE["中性"])
        parts = [cfg["acknowledge"]]

        if confidence < 0.5:
            parts.append("不过置信度较低，仅供参考。")
            parts.append(cfg["advice"])
        elif confidence < 0.75:
            parts.append(cfg["advice"])
        else:
            parts.append(cfg["advice"])

        return "".join(parts)

    async def synthesize_speech(self, text: str) -> str | None:
        """
        将文本合成为语音

        返回: 音频文件路径（MP3），失败返回 None
        """
        if not self.tts_available:
            return None

        try:
            import edge_tts

            # 使用微软晓晓语音 - 中文女声，自然温暖
            voice = "zh-CN-XiaoxiaoNeural"

            # 创建临时文件
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp_path = tmp.name
            tmp.close()

            # 合成语音
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(tmp_path)

            logger.info(f"语音合成完成: {len(text)}字 → {tmp_path}")
            return tmp_path

        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            return None

    async def generate_and_save(self, task_id: str, result: dict) -> dict:
        """生成反馈文本+语音，并缓存音频路径"""
        text = await self.generate_feedback_text(result)
        audio_path = await self.synthesize_speech(text)
        if audio_path:
            _voice_cache[task_id] = audio_path
            # 清理超过10条的旧缓存
            if len(_voice_cache) > 10:
                oldest = next(iter(_voice_cache))
                try:
                    os.remove(_voice_cache.pop(oldest))
                except Exception:
                    pass
        return {
            "text": text,
            "audio_path": audio_path,
            "tts_available": self.tts_available,
        }

    @staticmethod
    def get_cached_audio(task_id: str) -> str | None:
        """获取缓存的语音文件路径"""
        return _voice_cache.get(task_id)


# 全局单例
voice_assistant = VoiceAssistant()
