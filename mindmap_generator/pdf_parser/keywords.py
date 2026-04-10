"""关键词提取 - 简易 TF-IDF 实现（无外部依赖）"""

import re
import math
from collections import Counter
from typing import List

# 英文停用词表
STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "of", "in", "to",
    "for", "with", "on", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "and", "but",
    "or", "not", "no", "nor", "so", "yet", "both", "either", "neither",
    "each", "every", "all", "any", "few", "more", "most", "other", "some",
    "such", "than", "too", "very", "just", "because", "if", "when", "where",
    "how", "what", "which", "who", "whom", "this", "that", "these", "those",
    "it", "its", "he", "she", "they", "them", "we", "you", "i", "me",
    "my", "his", "her", "our", "your", "their",
})


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    从文本中提取关键词（简易 TF-IDF）。

    将文本按段落拆分，每个段落视为一个"文档"来计算 IDF。

    Args:
        text: 输入文本
        top_n: 返回前 N 个关键词

    Returns:
        关键词列表，按重要性降序
    """
    # 分词：提取 3 个字符以上的英文单词
    tokens = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    tokens = [t for t in tokens if t not in STOP_WORDS]

    if not tokens:
        return []

    # TF: 全文档词频
    tf = Counter(tokens)

    # IDF: 按段落计算
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) < 2:
        paragraphs = [text]  # 只有一个段落时，IDF 全部为 1

    total_paragraphs = len(paragraphs)
    doc_freq = Counter()
    for para in paragraphs:
        para_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', para.lower()))
        para_tokens = {t for t in para_tokens if t not in STOP_WORDS}
        for t in para_tokens:
            doc_freq[t] += 1

    # TF-IDF 得分
    scores = {}
    for word, freq in tf.items():
        idf = math.log(total_paragraphs / (1 + doc_freq.get(word, 0)))
        scores[word] = freq * idf

    # 按得分降序，取 top_n
    sorted_words = sorted(scores, key=scores.get, reverse=True)
    return sorted_words[:top_n]
