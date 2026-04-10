"""数据模型定义 - 管道各阶段的数据结构"""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class HeadingLevel(Enum):
    """标题层级"""
    BODY = 0
    H1 = 1
    H2 = 2
    H3 = 3


@dataclass
class TextSpan:
    """从 PDF 提取的原始文本片段"""
    text: str
    font_name: str
    font_size: float
    page_number: int
    origin_x: float
    origin_y: float


@dataclass
class TextLine:
    """由相邻 span 合并的逻辑行"""
    spans: List[TextSpan]
    text: str
    dominant_size: float
    page_number: int
    avg_y: float


@dataclass
class DocumentNode:
    """文档结构树节点"""
    title: str
    level: HeadingLevel
    children: List['DocumentNode'] = field(default_factory=list)
    content_lines: List[str] = field(default_factory=list)
    page_number: int = 0


@dataclass
class MindMapNode:
    """脑图节点，可序列化为任意输出格式"""
    text: str
    children: List['MindMapNode'] = field(default_factory=list)
    notes: str = ""
    node_id: str = ""
