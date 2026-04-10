"""FreeMind 格式输出 - 生成 .mm XML 文件"""

import uuid
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

from ..models import MindMapNode


def write_freemind(root: MindMapNode, output_path: str):
    """
    将脑图节点树写入 FreeMind (.mm) 文件。

    Args:
        root: 脑图根节点
        output_path: 输出文件路径
    """
    map_elem = Element("map")
    map_elem.set("version", "1.0.1")

    root_node = _build_node(root)
    map_elem.append(root_node)

    xml_str = _prettify(map_elem)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_str)


def _build_node(node: MindMapNode) -> Element:
    """递归构建 node 元素"""
    elem = Element("node")
    elem.set("ID", node.node_id or uuid.uuid4().hex)

    # FreeMind 用 TEXT 属性
    display_text = node.text
    if node.notes:
        display_text += "\n" + node.notes
    elem.set("TEXT", display_text)

    # 第一层子节点标记位置
    for i, child in enumerate(node.children):
        child_elem = _build_node(child)
        child_elem.set("POSITION", "right")
        elem.append(child_elem)

    return elem


def _prettify(elem: Element) -> str:
    raw = tostring(elem, encoding="unicode")
    try:
        dom = parseString(raw)
        return dom.toprettyxml(indent="  ", encoding=None)
    except Exception:
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + raw
