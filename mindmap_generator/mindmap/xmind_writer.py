"""XMind 格式输出 - 生成 .xmind 文件（ZIP 包含 XML）"""

import time
import uuid
import zipfile
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from pathlib import Path

from ..models import MindMapNode

# XMind XML 命名空间
NS_CONTENT = "urn:xmind:xmap:xmlns:content:2.0"
NS_FO = "http://www.w3.org/1999/XSL/Format"
NS_SVG = "http://www.w3.org/2000/svg"
NS_XHTML = "http://www.w3.org/1999/xhtml"
NS_XLINK = "http://www.w3.org/1999/xlink"
NS_META = "urn:xmind:xmap:xmlns:meta:2.0"
NS_MANIFEST = "urn:xmind:xmap:xmlns:manifest:2.0"


def write_xmind(root: MindMapNode, output_path: str, sheet_title: str = "Sheet 1"):
    """
    将脑图节点树写入 .xmind 文件。

    XMind 8 格式是一个 ZIP 包，包含：
    - content.xml: 脑图结构
    - meta.xml: 元数据
    - META-INF/manifest.xml: 清单

    Args:
        root: 脑图根节点
        output_path: 输出文件路径
        sheet_title: 工作表标题
    """
    timestamp = str(int(time.time() * 1000))

    content_xml = _build_content_xml(root, sheet_title, timestamp)
    meta_xml = _build_meta_xml(timestamp)
    manifest_xml = _build_manifest_xml()

    # 写入 ZIP
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("content.xml", content_xml)
        zf.writestr("meta.xml", meta_xml)
        zf.writestr("META-INF/manifest.xml", manifest_xml)


def _build_content_xml(root: MindMapNode, sheet_title: str, timestamp: str) -> str:
    """构建 content.xml"""
    xmap = Element(f"{{{NS_CONTENT}}}xmap-content")
    xmap.set("version", "2.0")

    sheet = SubElement(xmap, f"{{{NS_CONTENT}}}sheet")
    sheet.set("id", uuid.uuid4().hex)
    sheet.set("timestamp", timestamp)

    # 根 topic
    topic = _build_topic(root)
    sheet.append(topic)

    # sheet title
    title_elem = SubElement(sheet, f"{{{NS_CONTENT}}}title")
    title_elem.text = sheet_title

    return _prettify(xmap)


def _build_topic(node: MindMapNode) -> Element:
    """递归构建 topic 元素"""
    topic = Element(f"{{{NS_CONTENT}}}topic")
    topic.set("id", node.node_id or uuid.uuid4().hex)
    topic.set("timestamp", str(int(time.time() * 1000)))

    # 标题
    title = SubElement(topic, f"{{{NS_CONTENT}}}title")
    title.text = node.text

    # 备注
    if node.notes:
        notes = SubElement(topic, f"{{{NS_CONTENT}}}notes")
        plain = SubElement(notes, f"{{{NS_CONTENT}}}plain")
        plain.text = node.notes

    # 子节点
    if node.children:
        children = SubElement(topic, f"{{{NS_CONTENT}}}children")
        topics = SubElement(children, f"{{{NS_CONTENT}}}topics")
        topics.set("type", "attached")
        for child in node.children:
            topics.append(_build_topic(child))

    return topic


def _build_meta_xml(timestamp: str) -> str:
    """构建 meta.xml"""
    meta = Element(f"{{{NS_META}}}meta")
    meta.set("version", "2.0")

    author = SubElement(meta, f"{{{NS_META}}}Author")
    author.text = "mindmap_generator"

    create_at = SubElement(meta, f"{{{NS_META}}}CreateAt")
    create_at.text = timestamp

    version = SubElement(meta, f"{{{NS_META}}}Version")
    version.text = "2.0"

    return _prettify(meta)


def _build_manifest_xml() -> str:
    """构建 manifest.xml"""
    manifest = Element(f"{{{NS_MANIFEST}}}manifest")

    entries = [
        ("content.xml", "text/xml"),
        ("meta.xml", "text/xml"),
        ("META-INF/", ""),
        ("", ""),
    ]
    for path, media_type in entries:
        entry = SubElement(manifest, f"{{{NS_MANIFEST}}}file-entry")
        entry.set("full-path", path)
        entry.set("media-type", media_type)

    return _prettify(manifest)


def _prettify(elem: Element) -> str:
    """格式化 XML 输出"""
    raw = tostring(elem, encoding="unicode", xml_declaration=False)
    try:
        dom = parseString(raw)
        return dom.toprettyxml(indent="  ", encoding=None)
    except Exception:
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + raw
