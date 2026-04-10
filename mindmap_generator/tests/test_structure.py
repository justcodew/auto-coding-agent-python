"""测试文档结构分析"""
import pytest
from mindmap_generator.models import TextSpan, HeadingLevel
from mindmap_generator.pdf_parser.structure import (
    group_into_lines,
    detect_heading_levels,
    build_document_tree,
)
from mindmap_generator.pdf_parser.extractor import extract_spans


class TestGroupIntoLines:
    def test_merges_spans_with_similar_y(self):
        spans = [
            TextSpan("Hello", "helv", 11, 0, 72, 100),
            TextSpan("World", "helv", 11, 0, 150, 101),  # y 差 1，应合并
        ]
        lines = group_into_lines(spans)
        assert len(lines) == 1
        assert "Hello" in lines[0].text
        assert "World" in lines[0].text

    def test_separates_spans_with_different_y(self):
        spans = [
            TextSpan("Line1", "helv", 11, 0, 72, 100),
            TextSpan("Line2", "helv", 11, 0, 72, 200),  # y 差 100
        ]
        lines = group_into_lines(spans)
        assert len(lines) == 2

    def test_empty_input(self):
        assert group_into_lines([]) == []

    def test_from_real_pdf(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        assert len(lines) >= 5  # 至少 5 行
        # 每行有文本
        for line in lines:
            assert line.text.strip() != ""


class TestDetectHeadingLevels:
    def test_identifies_heading_sizes(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)

        # 应该有 H1, H2, H3 和 BODY
        levels = set(level_map.values())
        assert HeadingLevel.H1 in levels
        assert HeadingLevel.H2 in levels
        assert HeadingLevel.BODY in levels

    def test_flat_pdf_all_body(self, flat_pdf):
        spans = extract_spans(flat_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)

        # 所有行都是 BODY
        for level in level_map.values():
            assert level == HeadingLevel.BODY

    def test_empty_lines(self):
        assert detect_heading_levels([]) == {}


class TestBuildDocumentTree:
    def test_builds_hierarchy(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)
        root = build_document_tree(lines, level_map, root_title="TestDoc")

        assert root.title == "TestDoc"
        assert len(root.children) > 0

        # H1 子节点存在
        h1_children = [c for c in root.children if c.level == HeadingLevel.H1]
        assert len(h1_children) >= 1

    def test_flat_pdf_single_node(self, flat_pdf):
        spans = extract_spans(flat_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)
        root = build_document_tree(lines, level_map, root_title="FlatDoc")

        assert root.title == "FlatDoc"
        # 无标题层级，所有内容在 root 的 content_lines
        assert len(root.content_lines) >= 3

    def test_body_text_assigned_to_parent(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)
        root = build_document_tree(lines, level_map)

        # 找到有正文内容的节点
        has_content = False
        def _check(node):
            nonlocal has_content
            if node.content_lines:
                has_content = True
            for c in node.children:
                _check(c)
        _check(root)
        assert has_content
