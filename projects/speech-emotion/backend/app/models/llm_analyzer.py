"""
LLM 语义情感分析模块
--------------------
使用 DeepSeek API 进行深度语义情感分析
理解反讽、隐喻、潜台词等复杂表达
无 API Key 时自动回退到本地规则分析
"""

import json
import re
import os

from app.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL, EMOTION_LABELS,
)
from app.utils.logger import logger


class LLMEmotionAnalyzer:
    """
    大语言模型语义情感分析器

    核心能力：
    1. 识别文本中的情感倾向（6分类）
    2. 理解反讽、隐喻等复杂表达
    3. 提供可解释的判断理由
    4. 提取关键情感词汇
    """

    EMOTIONS = EMOTION_LABELS

    SYSTEM_PROMPT = """你是一个专业的语音情感分析专家。你的任务是分析从语音转录的文本中所包含的情感。

# 情感类别（必须从以下6类中选择一个）：
1. 开心 - 表达喜悦、满足、积极的情绪
2. 悲伤 - 表达难过、失望、沮丧的情绪
3. 愤怒 - 表达生气、不满、愤慨的情绪
4. 中性 - 无明显情感倾向，陈述事实
5. 惊讶 - 表达意外、震惊、诧异的情绪
6. 恐惧 - 表达害怕、担忧、焦虑的情绪

# 分析要求：
1. 仔细分析文本的措辞、语气、语境
2. 注意反讽（字面积极但实际消极）、隐喻、夸张等修辞
3. 如果有多种情感混合，选择最主导的一种
4. 给出每个情感类别的概率分布（总和必须为1.0）
5. 提供详细的推理过程，解释为什么做出这个判断
6. 提取文本中的关键情感词汇或短语

# 输出格式（严格JSON）：
{
  "primary_emotion": "悲伤",
  "confidence": 0.91,
  "probabilities": {
    "开心": 0.02,
    "悲伤": 0.91,
    "愤怒": 0.04,
    "中性": 0.02,
    "惊讶": 0.01,
    "恐惧": 0.00
  },
  "reasoning": "详细的分析推理过程，解释判断依据",
  "key_phrases": ["关键情感词1", "关键情感词2"]
}"""

    def __init__(self):
        self.client = None
        self.has_api = False
        self._init_client()

    def _init_client(self):
        """初始化 DeepSeek API 客户端"""
        api_key = DEEPSEEK_API_KEY

        # 尝试从环境变量获取
        if not api_key:
            api_key = os.getenv("DEEPSEEK_API_KEY", "")

        # 尝试从 .env 文件读取
        if not api_key:
            api_key = self._load_from_env_file()

        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=DEEPSEEK_BASE_URL,
                )
                self.has_api = True
                logger.info("✅ LLM分析器: DeepSeek API (云端)")
            except Exception as e:
                logger.warning(f"DeepSeek 客户端初始化失败: {e}")
                self.has_api = False
        else:
            logger.warning("⚠️ 未设置 DEEPSEEK_API_KEY，将使用本地规则分析器（效果受限）")
            logger.warning("   请设置环境变量: export DEEPSEEK_API_KEY=your_key")
            self.has_api = False

    def _load_from_env_file(self) -> str:
        """从 .env 文件加载 API Key"""
        env_files = [
            os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
            ".env",
        ]
        for env_file in env_files:
            if os.path.exists(env_file):
                try:
                    with open(env_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("DEEPSEEK_API_KEY="):
                                return line.split("=", 1)[1].strip().strip('"').strip("'")
                except Exception:
                    pass
        return ""

    async def analyze(self, text: str) -> dict:
        """
        分析文本的情感

        参数:
            text: 转录后的中文文本

        返回:
            dict: {
                "label": 情感标签,
                "confidence": 置信度,
                "probabilities": 各情感概率,
                "reasoning": 推理过程,
                "key_phrases": 关键情感词,
                "model": 使用的模型,
                "feature_vector": 768维语义特征(用概率分布构建)
            }
        """
        if not text or not text.strip():
            return self._empty_result()

        # 优先使用 DeepSeek API
        if self.has_api:
            result = await self._analyze_with_deepseek(text)
            if result is not None:
                return result

        # 回退到本地规则分析
        logger.info("使用本地规则分析器")
        return self._analyze_with_rules(text)

    async def _analyze_with_deepseek(self, text: str) -> dict | None:
        """使用 DeepSeek API 分析"""
        try:
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"请分析以下从语音转录的文本所表达的情感：\n\n{text}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # 低温度确保稳定输出
                max_tokens=1000,
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # 规范化输出
            primary = result.get("primary_emotion", "中性")
            if primary not in self.EMOTIONS:
                primary = "中性"

            probs = result.get("probabilities", {})
            # 确保所有情感都有概率值
            normalized_probs = {}
            for e in self.EMOTIONS:
                normalized_probs[e] = float(probs.get(e, 0.0))

            # 归一化
            total = sum(normalized_probs.values())
            if total > 0:
                normalized_probs = {k: v / total for k, v in normalized_probs.items()}

            # 构建特征向量（用概率分布）
            feature_vec = [normalized_probs.get(e, 0.0) for e in self.EMOTIONS]

            logger.info(f"LLM 分析完成: {primary} (置信度={result.get('confidence', 0)})")

            return {
                "label": primary,
                "confidence": float(result.get("confidence", normalized_probs.get(primary, 0.5))),
                "probabilities": normalized_probs,
                "reasoning": result.get("reasoning", ""),
                "key_phrases": result.get("key_phrases", []),
                "model": DEEPSEEK_MODEL,
                "feature_vector": feature_vec + [0.0] * (768 - len(feature_vec)),
            }

        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return None

    def _analyze_with_rules(self, text: str) -> dict:
        """本地规则分析器（无API时的兜底方案）"""
        # 情感词典
        emotion_keywords = {
            "开心": ["哈哈", "开心", "太棒", "高兴", "喜欢", "真好", "不错", "爱", "美", "赞",
                     "快乐", "幸福", "棒", "好开心", "太好了", "nice", "good", "嘻嘻", "嘿嘿"],
            "悲伤": ["难过", "伤心", "哭", "痛苦", "绝望", "失望", "遗憾", "孤独", "想哭",
                     "不好", "糟糕", "太差", "惨", "崩溃", "难受", "心碎", "唉", "哎"],
            "愤怒": ["气死", "讨厌", "烦", "滚", "恶心", "混蛋", "垃圾", "凭什么", "不公平",
                     "怒", "恨", "操", "靠", "妈的", "可恶", "过分", "气人", "坏"],
            "惊讶": ["天哪", "什么", "居然", "竟然", "不会吧", "真的假的", "不可思议",
                     "哇", "天啊", "我的天", "oh", "wow", "震惊", "吓一跳"],
            "恐惧": ["害怕", "担心", "恐惧", "恐怖", "不敢", "紧张", "焦虑", "吓人",
                     "怕", "慌", "担忧", "危险", "惊悚"],
        }

        # 统计各类别关键词命中
        scores = {e: 0.0 for e in self.EMOTIONS}
        matched_phrases = []

        for emotion, keywords in emotion_keywords.items():
            for kw in keywords:
                if kw in text:
                    scores[emotion] += 1.0
                    matched_phrases.append(kw)

        # 去重
        matched_phrases = list(set(matched_phrases))

        # 分析否定词（可能反转情感）
        negation_words = ["不", "没", "并非", "不是"]
        for nw in negation_words:
            if any(nw + kw in text for kw in emotion_keywords.get("开心", [])):
                scores["开心"] = max(0, scores["开心"] - 1)
                scores["悲伤"] += 0.5

        # 分析程度副词
        intensifiers = ["非常", "很", "特别", "极其", "太", "超级", "真的"]
        if any(i in text for i in intensifiers):
            for e in scores:
                if scores[e] > 0:
                    scores[e] *= 1.5

        # 如果没有命中任何关键词，判断为中性
        total_score = sum(scores.values())
        if total_score == 0:
            scores["中性"] = 1.0
            reasoning = "文本中未检测到明显的情感关键词，判断为中性表达。"
        else:
            # 归一化
            for e in scores:
                scores[e] = scores[e] / total_score

            best_emotion = max(scores, key=scores.get)
            phrases_str = "、".join(matched_phrases[:5]) if matched_phrases else "无"
            reasoning = f"基于规则分析：检测到情感关键词 [{phrases_str}]，综合判断为{best_emotion}。"

        best_emotion = max(scores, key=scores.get)
        feature_vec = [scores.get(e, 0.0) for e in self.EMOTIONS]

        return {
            "label": best_emotion,
            "confidence": float(scores[best_emotion]),
            "probabilities": {e: float(scores[e]) for e in self.EMOTIONS},
            "reasoning": reasoning,
            "key_phrases": matched_phrases[:10],
            "model": "rule-based (离线本地)",
            "feature_vector": feature_vec + [0.0] * (768 - len(feature_vec)),
        }

    def _empty_result(self) -> dict:
        """空文本的默认结果"""
        return {
            "label": "中性",
            "confidence": 0.5,
            "probabilities": {"开心": 0.1, "悲伤": 0.1, "愤怒": 0.1, "中性": 0.5, "惊讶": 0.1, "恐惧": 0.1},
            "reasoning": "未检测到有效文本内容。",
            "key_phrases": [],
            "model": "none",
            "feature_vector": [0.0] * 768,
        }
