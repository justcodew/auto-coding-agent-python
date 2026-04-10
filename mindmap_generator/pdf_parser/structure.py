"""文档结构分析 - 根据字体大小识别标题层级，构建文档树"""

from typing import List, Dict
from collections import Counter

from ..models import TextSpan, TextLine, DocumentNode, HeadingLevel


def group_into_lines(spans: List[TextSpan], y_tolerance: float = 3.0) -> List[TextLine]:
    """
    将相邻的 span 按 y 坐标合并为逻辑行。

    同一页上 y 坐标差小于 tolerance 的 span 视为同一行。

    Args:
        spans: TextSpan 列表
        y_tolerance: y 坐标容差（磅），默认 3.0

    Returns:
        TextLine 列表
    """
    if not spans:
        return []

    # 按页码和位置排序
    sorted_spans = sorted(spans, key=lambda s: (s.page_number, s.origin_y, s.origin_x))

    lines: List[TextLine] = []
    current_spans: List[TextSpan] = [sorted_spans[0]]

    for span in sorted_spans[1:]:
        prev = current_spans[-1]

        # 同一页且 y 坐标接近 → 同一行
        if span.page_number == prev.page_number and abs(span.origin_y - prev.origin_y) < y_tolerance:
            current_spans.append(span)
        else:
            lines.append(_build_line(current_spans))
            current_spans = [span]

    # 别忘了最后一行
    if current_spans:
        lines.append(_build_line(current_spans))

    return lines


def detect_heading_levels(lines: List[TextLine]) -> Dict[float, HeadingLevel]:
    """
    根据字体大小频率分析标题层级。

    最频繁出现的字体大小 = 正文，其余从大到小映射为 H1/H2/H3。

    Args:
        lines: TextLine 列表

    Returns:
        {字体大小: HeadingLevel} 映射
    """
    if not lines:
        return {}

    # 统计每个字体大小出现的行数（按行数而非 span 数）
    size_counter = Counter(line.dominant_size for line in lines)

    # 最频繁的字体大小 = 正文
    body_size = size_counter.most_common(1)[0][0]

    # 收集非正文的字体大小，从大到小排序
    non_body_sizes = sorted(
        [s for s in size_counter if s != body_size],
        reverse=True
    )

    level_map: Dict[float, HeadingLevel] = {body_size: HeadingLevel.BODY}

    # 最多支持 3 级标题
    level_values = [HeadingLevel.H1, HeadingLevel.H2, HeadingLevel.H3]
    for i, size in enumerate(non_body_sizes[:3]):
        level_map[size] = level_values[i]

    return level_map


def build_document_tree(
    lines: List[TextLine],
    level_map: Dict[float, HeadingLevel],
    root_title: str = "Document"
) -> DocumentNode:
    """
    用栈式算法构建文档结构树。

    Args:
        lines: TextLine 列表
        level_map: 字体大小到标题层级的映射
        root_title: 根节点标题（通常为文件名）

    Returns:
        文档结构树的根节点
    """
    root = DocumentNode(title=root_title, level=HeadingLevel.H1)
    stack: List[DocumentNode] = [root]

    for line in lines:
        level = level_map.get(line.dominant_size, HeadingLevel.BODY)

        if level == HeadingLevel.BODY:
            # 正文追加到当前最近的标题节点
            stack[-1].content_lines.append(line.text)
        else:
            # 标题：弹栈到正确的父级深度
            while len(stack) > level.value:
                stack.pop()

            node = DocumentNode(
                title=line.text,
                level=level,
                page_number=line.page_number
            )
            stack[-1].children.append(node)
            stack.append(node)

    return root


def _build_line(spans: List[TextSpan]) -> TextLine:
    """从 span 列表构建 TextLine"""
    # dominant_size: 按字符数加权，取覆盖最多字符的字体大小
    size_chars: Counter = Counter()
    for s in spans:
        size_chars[s.font_size] += len(s.text)
    dominant_size = size_chars.most_common(1)[0][0]

    avg_y = sum(s.origin_y for s in spans) / len(spans)
    text = " ".join(s.text for s in spans)

    return TextLine(
        spans=spans,
        text=text,
        dominant_size=dominant_size,
        page_number=spans[0].page_number,
        avg_y=avg_y,
    )
