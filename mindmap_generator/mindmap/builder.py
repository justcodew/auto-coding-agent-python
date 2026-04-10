"""脑图构建 - 将文档结构树转换为脑图节点树"""

import uuid
from typing import Optional

from ..models import DocumentNode, MindMapNode, HeadingLevel


def build_mindmap(root: DocumentNode, max_depth: int = 3) -> MindMapNode:
    """
    将 DocumentNode 树转换为 MindMapNode 树。

    Args:
        root: 文档结构树根节点
        max_depth: 最大深度限制（防止脑图过于复杂）

    Returns:
        脑图节点树根节点
    """
    mm_root = _convert_node(root, depth=0, max_depth=max_depth)
    return mm_root


def _convert_node(node: DocumentNode, depth: int, max_depth: int) -> MindMapNode:
    """递归转换单个节点"""
    mm_node = MindMapNode(
        text=node.title,
        node_id=uuid.uuid4().hex,
    )

    # 正文内容作为 notes
    if node.content_lines:
        mm_node.notes = "\n".join(node.content_lines)

    # 递归处理子节点（受深度限制）
    if depth < max_depth:
        for child in node.children:
            mm_node.children.append(_convert_node(child, depth + 1, max_depth))
    else:
        # 超出深度的子节点内容合并到 notes
        overflow_texts = _collect_all_text(node)
        if overflow_texts:
            if mm_node.notes:
                mm_node.notes += "\n"
            mm_node.notes += "\n".join(overflow_texts)

    return mm_node


def _collect_all_text(node: DocumentNode) -> list:
    """递归收集节点及所有子节点的文本"""
    texts = []
    for child in node.children:
        texts.append(child.title)
        if child.content_lines:
            texts.extend(child.content_lines)
        texts.extend(_collect_all_text(child))
    return texts
