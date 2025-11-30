"""
消息分析器 - 增強多輪對話：意圖識別、話題檢測、情感分析
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from pyrogram.types import Message

logger = logging.getLogger(__name__)


@dataclass
class MessageIntent:
    """消息意圖"""
    intent_type: str  # greeting, question, request, redpacket, etc.
    confidence: float  # 0.0-1.0
    keywords: List[str] = None


@dataclass
class TopicInfo:
    """話題信息"""
    topic: str
    confidence: float
    keywords: List[str] = None


@dataclass
class SentimentInfo:
    """情感信息"""
    sentiment: str  # positive, negative, neutral
    score: float  # -1.0 to 1.0


class MessageAnalyzer:
    """消息分析器 - 用於多輪對話增強"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 意圖關鍵詞映射
        self.intent_keywords = {
            "greeting": {
                "zh": ["你好", "您好", "哈嘍", "hi", "hello", "早上好", "晚上好", "中午好", "嗨"],
                "en": ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]
            },
            "question": {
                "zh": ["什麼", "為什麼", "怎麼", "如何", "哪個", "哪裡", "誰", "？", "?"],
                "en": ["what", "why", "how", "which", "where", "who", "when", "?"]
            },
            "request": {
                "zh": ["請", "幫", "麻煩", "能否", "可以", "想要", "需要"],
                "en": ["please", "help", "can you", "could you", "would you", "need", "want"]
            },
            "redpacket": {
                "zh": ["紅包", "紅包遊戲", "搶紅包"],
                "en": ["red packet", "redpacket", "gift"]
            },
            "thanks": {
                "zh": ["謝謝", "感謝", "多謝", "謝了"],
                "en": ["thanks", "thank you", "thx", "appreciate"]
            },
            "goodbye": {
                "zh": ["再見", "拜拜", "bye", "走了"],
                "en": ["bye", "goodbye", "see you", "farewell"]
            }
        }
        
        # 話題關鍵詞（示例）
        self.topic_keywords = {
            "work": ["工作", "上班", "job", "work", "職業", "career"],
            "game": ["遊戲", "game", "玩", "play", "娛樂"],
            "weather": ["天氣", "weather", "下雨", "rain", "晴天", "sunny"],
            "food": ["吃", "food", "美食", "餐廳", "restaurant", "飯"],
            "sports": ["運動", "sports", "球", "ball", "跑步", "run"],
            "technology": ["技術", "tech", "電腦", "computer", "手機", "phone"]
        }
        
        self.logger.info("MessageAnalyzer 初始化完成")
    
    def detect_intent(self, message: Message, language: str = "zh") -> Optional[MessageIntent]:
        """
        檢測消息意圖
        
        Args:
            message: Telegram 消息對象
            language: 語言代碼（zh/en）
        
        Returns:
            MessageIntent 或 None
        """
        if not message.text:
            return None
        
        text = message.text.lower()
        language = language.lower()[:2]  # 只取前兩個字符
        
        # 遍歷所有意圖類型
        for intent_type, keywords_dict in self.intent_keywords.items():
            keywords = keywords_dict.get(language, keywords_dict.get("en", []))
            matched_keywords = [kw for kw in keywords if kw.lower() in text]
            
            if matched_keywords:
                # 計算置信度（基於匹配的關鍵詞數量）
                confidence = min(len(matched_keywords) / max(len(keywords), 1), 1.0)
                return MessageIntent(
                    intent_type=intent_type,
                    confidence=confidence,
                    keywords=matched_keywords
                )
        
        return None
    
    def detect_topic(self, message: Message, language: str = "zh") -> Optional[TopicInfo]:
        """
        檢測消息話題
        
        Args:
            message: Telegram 消息對象
            language: 語言代碼
        
        Returns:
            TopicInfo 或 None
        """
        if not message.text:
            return None
        
        text = message.text.lower()
        language = language.lower()[:2]
        
        # 遍歷所有話題
        best_topic = None
        best_confidence = 0.0
        matched_keywords = []
        
        for topic, keywords in self.topic_keywords.items():
            # 檢查關鍵詞匹配（支持多語言）
            topic_keywords = [kw for kw in keywords]
            matched = [kw for kw in topic_keywords if kw.lower() in text]
            
            if matched:
                confidence = len(matched) / max(len(topic_keywords), 1)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_topic = topic
                    matched_keywords = matched
        
        if best_topic:
            return TopicInfo(
                topic=best_topic,
                confidence=best_confidence,
                keywords=matched_keywords
            )
        
        return None
    
    def analyze_sentiment(self, message: Message) -> SentimentInfo:
        """
        分析消息情感（簡單實現，基於關鍵詞）
        
        Args:
            message: Telegram 消息對象
        
        Returns:
            SentimentInfo
        """
        if not message.text:
            return SentimentInfo(sentiment="neutral", score=0.0)
        
        text = message.text.lower()
        
        # 積極情感關鍵詞
        positive_keywords = [
            "好", "棒", "開心", "高興", "喜歡", "愛", "感謝", "謝謝",
            "good", "great", "nice", "love", "happy", "thanks"
        ]
        
        # 消極情感關鍵詞
        negative_keywords = [
            "差", "壞", "討厭", "煩", "生氣", "不喜歡", "討厭",
            "bad", "hate", "angry", "annoyed", "dislike"
        ]
        
        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)
        
        if positive_count > negative_count:
            score = min(positive_count / 5.0, 1.0)  # 正規化到 0-1
            return SentimentInfo(sentiment="positive", score=score)
        elif negative_count > positive_count:
            score = -min(negative_count / 5.0, 1.0)  # 正規化到 -1-0
            return SentimentInfo(sentiment="negative", score=score)
        else:
            return SentimentInfo(sentiment="neutral", score=0.0)
    
    def extract_entities(self, message: Message) -> Dict[str, List[str]]:
        """
        提取實體（簡單實現，可擴展）
        
        Returns:
            實體字典，例如: {"person": ["張三"], "location": ["北京"]}
        """
        if not message.text:
            return {}
        
        entities = {
            "mentions": [],  # @提及
            "hashtags": [],  # #標籤
            "urls": []       # URL
        }
        
        text = message.text
        
        # 提取 @提及
        mentions = re.findall(r'@(\w+)', text)
        if mentions:
            entities["mentions"] = mentions
        
        # 提取 #標籤
        hashtags = re.findall(r'#(\w+)', text)
        if hashtags:
            entities["hashtags"] = hashtags
        
        # 提取 URL
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        if urls:
            entities["urls"] = urls
        
        return entities
    
    def analyze_message(self, message: Message, language: str = "zh") -> Dict[str, any]:
        """
        綜合分析消息（意圖、話題、情感、實體）
        
        Returns:
            分析結果字典
        """
        intent = self.detect_intent(message, language)
        topic = self.detect_topic(message, language)
        sentiment = self.analyze_sentiment(message)
        entities = self.extract_entities(message)
        
        return {
            "intent": {
                "type": intent.intent_type if intent else None,
                "confidence": intent.confidence if intent else 0.0,
                "keywords": intent.keywords if intent else []
            },
            "topic": {
                "topic": topic.topic if topic else None,
                "confidence": topic.confidence if topic else 0.0,
                "keywords": topic.keywords if topic else []
            },
            "sentiment": {
                "sentiment": sentiment.sentiment,
                "score": sentiment.score
            },
            "entities": entities
        }
