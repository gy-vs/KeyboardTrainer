"""
内容生成器模块

生成测试和训练文本内容。

Requirements: 1.1, 4.1, 4.2, 4.3
"""

import random
from collections import Counter
from typing import Dict, List, Optional


# 内置常用英文单词库
DEFAULT_WORD_DATABASE = [
    # 常用短词
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    # 常用中等长度词
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    # 包含各种字母的词
    "quick", "brown", "fox", "jumps", "lazy", "dog", "pack", "box", "five",
    "dozen", "liquor", "jugs", "sphinx", "quartz", "waltz", "nymph", "vex",
    "keyboard", "typing", "practice", "exercise", "training", "improve", "skill",
    "finger", "position", "accuracy", "speed", "test", "result", "progress",
    # 更多常用词
    "able", "about", "above", "accept", "across", "act", "actually", "add", "admit",
    "afraid", "after", "again", "against", "age", "ago", "agree", "air", "allow",
    "almost", "alone", "along", "already", "always", "among", "amount", "animal",
    "another", "answer", "appear", "area", "argue", "arm", "around", "arrive", "art",
    "ask", "assume", "attack", "attention", "available", "avoid", "away", "baby",
    "bad", "bag", "ball", "bank", "bar", "base", "beat", "beautiful", "become",
    "bed", "before", "begin", "behavior", "behind", "believe", "benefit", "best",
    "better", "between", "beyond", "big", "bill", "billion", "bit", "black", "blood",
    "blue", "board", "body", "book", "born", "both", "box", "boy", "break", "bring",
    "brother", "budget", "build", "building", "business", "buy", "call", "camera",
    "campaign", "cancer", "candidate", "capital", "car", "card", "care", "career",
    "carry", "case", "catch", "cause", "cell", "center", "central", "century",
    "certain", "certainly", "chair", "challenge", "chance", "change", "character",
    "charge", "check", "child", "choice", "choose", "church", "citizen", "city",
    "civil", "claim", "class", "clear", "clearly", "close", "coach", "cold",
    "collection", "college", "color", "common", "community", "company", "compare",
    "computer", "concern", "condition", "conference", "consider", "consumer",
    "contain", "continue", "control", "cost", "country", "couple", "course", "court",
    "cover", "create", "crime", "cultural", "culture", "cup", "current", "customer",
]


class ContentGenerator:
    """内容生成器，生成测试和训练文本"""
    
    WEAK_KEY_FREQUENCY_MULTIPLIER = 3  # 薄弱按键频率倍数
    
    def __init__(self, word_database: Optional[List[str]] = None):
        """
        初始化内容生成器
        
        Args:
            word_database: 单词库，如果为 None 则使用默认单词库
        """
        self.word_database = word_database or DEFAULT_WORD_DATABASE
    
    def generate_basic_test_content(self, length: int = 200) -> str:
        """
        生成基础测试内容
        
        Args:
            length: 目标字符数
            
        Returns:
            随机生成的测试文本
        """
        words = []
        current_length = 0
        
        while current_length < length:
            word = random.choice(self.word_database)
            words.append(word)
            current_length += len(word) + 1  # +1 for space
        
        return " ".join(words)
    
    def generate_training_content(self, weak_keys: List[str], length: int = 200) -> str:
        """
        生成针对薄弱按键的训练内容
        
        确保薄弱按键出现频率至少是普通按键的 3 倍
        
        Args:
            weak_keys: 薄弱按键列表
            length: 目标字符数
            
        Returns:
            包含高频薄弱按键的训练文本
        """
        if not weak_keys:
            return self.generate_basic_test_content(length)
        
        # 筛选包含薄弱按键的单词
        weak_key_words = self.filter_words_by_keys(weak_keys)
        
        if not weak_key_words:
            # 如果没有找到包含薄弱按键的单词，使用基础内容
            return self.generate_basic_test_content(length)
        
        # 生成内容，确保薄弱按键高频出现
        words = []
        current_length = 0
        weak_key_set = set(k.lower() for k in weak_keys)
        
        while current_length < length:
            # 以较高概率选择包含薄弱按键的单词
            if random.random() < 0.7 and weak_key_words:
                word = random.choice(weak_key_words)
            else:
                word = random.choice(self.word_database)
            
            words.append(word)
            current_length += len(word) + 1
        
        content = " ".join(words)
        
        # 验证薄弱按键频率
        freq = self.calculate_key_frequency(content)
        total_chars = len(content.replace(" ", ""))
        
        # 如果频率不够，增加更多包含薄弱按键的单词
        if total_chars > 0:
            avg_freq = total_chars / 26  # 假设 26 个字母均匀分布
            for key in weak_keys:
                key_lower = key.lower()
                if freq.get(key_lower, 0) < avg_freq * self.WEAK_KEY_FREQUENCY_MULTIPLIER:
                    # 添加更多包含该按键的单词
                    key_specific_words = [w for w in weak_key_words if key_lower in w.lower()]
                    if key_specific_words:
                        extra_words = random.choices(key_specific_words, k=5)
                        words.extend(extra_words)
        
        return " ".join(words)
    
    def filter_words_by_keys(self, keys: List[str]) -> List[str]:
        """
        筛选包含指定按键的单词
        
        Args:
            keys: 按键列表
            
        Returns:
            包含任意指定按键的单词列表
        """
        key_set = set(k.lower() for k in keys)
        return [
            word for word in self.word_database
            if any(k in word.lower() for k in key_set)
        ]
    
    def calculate_key_frequency(self, text: str) -> Dict[str, int]:
        """
        计算文本中各按键的出现频率
        
        Args:
            text: 文本内容
            
        Returns:
            按键到出现次数的映射
        """
        # 只统计字母字符
        letters = [c.lower() for c in text if c.isalpha()]
        return dict(Counter(letters))
