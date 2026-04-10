"""Markdown 格式输出 - 生成 .md 大纲文件"""

from ..models import MindMapNode


def write_markdown(root: MindMapNode, output_path: str):
    """
    将脑图节点树写入 Markdown 大纲文件。

    Args:
        root: 脑图根节点
        output_path: 输出文件路径
    """
    lines = _render(root, depth=0)
    content = "\n".join(lines) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def _render(node: MindMapNode, depth: int) -> list:
    """递归渲染为 Markdown 行"""
    lines = []

    # 标题层级 (depth 0 = #, depth 1 = ##, ...)
    heading_level = min(depth + 1, 6)
    prefix = "#" * heading_level
    lines.append(f"{prefix} {node.text}")

    # 备注作为缩进正文
    if node.notes:
        for note_line in node.notes.split("\n"):
            lines.append(f"  {note_line}")

    lines.append("")  # 空行分隔

    # 子节点
    for child in node.children:
        lines.extend(_render(child, depth + 1))

    return lines
