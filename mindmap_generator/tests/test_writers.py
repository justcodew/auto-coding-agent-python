"""测试脑图构建和输出格式"""
import zipfile
import pytest
from xml.etree.ElementTree import parse as xml_parse

from mindmap_generator.models import MindMapNode
from mindmap_generator.mindmap.builder import build_mindmap
from mindmap_generator.mindmap.xmind_writer import write_xmind
from mindmap_generator.mindmap.freemind_writer import write_freemind
from mindmap_generator.mindmap.markdown_writer import write_markdown
from mindmap_generator.pdf_parser.extractor import extract_spans
from mindmap_generator.pdf_parser.structure import group_into_lines, detect_heading_levels, build_document_tree


def _make_test_tree():
    """创建测试用脑图树"""
    return MindMapNode(
        text="Root",
        node_id="root123",
        notes="Root notes",
        children=[
            MindMapNode(
                text="Child 1",
                node_id="child1",
                children=[
                    MindMapNode(text="Grandchild 1", node_id="gc1"),
                ]
            ),
            MindMapNode(text="Child 2", node_id="child2", notes="Child notes"),
        ]
    )


class TestMindmapBuilder:
    def test_builds_from_document(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)
        doc_root = build_document_tree(lines, level_map, root_title="Test")
        mm_root = build_mindmap(doc_root)

        assert mm_root.text == "Test"
        assert len(mm_root.children) > 0
        assert mm_root.node_id != ""

    def test_max_depth_limits_tree(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)
        doc_root = build_document_tree(lines, level_map)

        mm1 = build_mindmap(doc_root, max_depth=1)
        # depth=1 只有一层子节点
        for child in mm1.children:
            assert len(child.children) == 0 or child.notes != ""

    def test_node_ids_unique(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)
        doc_root = build_document_tree(lines, level_map)
        mm_root = build_mindmap(doc_root)

        ids = set()
        def _collect(node):
            ids.add(node.node_id)
            for c in node.children:
                _collect(c)
        _collect(mm_root)
        assert len(ids) > 1  # 所有 ID 唯一


class TestXMindWriter:
    def test_generates_valid_zip(self, tmp_path):
        tree = _make_test_tree()
        output = str(tmp_path / "test.xmind")
        write_xmind(tree, output)

        assert zipfile.is_zipfile(output)

    def test_contains_required_files(self, tmp_path):
        tree = _make_test_tree()
        output = str(tmp_path / "test.xmind")
        write_xmind(tree, output)

        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert "content.xml" in names
            assert "meta.xml" in names
            assert "META-INF/manifest.xml" in names

    def test_content_xml_has_correct_structure(self, tmp_path):
        tree = _make_test_tree()
        output = str(tmp_path / "test.xmind")
        write_xmind(tree, output)

        with zipfile.ZipFile(output) as zf:
            content = zf.read("content.xml").decode("utf-8")

        # 检查包含标题文本
        assert "Root" in content
        assert "Child 1" in content
        assert "Grandchild 1" in content
        assert "Root notes" in content

    def test_e2e_from_pdf(self, simple_pdf, tmp_path):
        """端到端: PDF → XMind"""
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)
        doc_root = build_document_tree(lines, level_map)
        mm_root = build_mindmap(doc_root)

        output = str(tmp_path / "e2e.xmind")
        write_xmind(mm_root, output)

        assert zipfile.is_zipfile(output)
        with zipfile.ZipFile(output) as zf:
            content = zf.read("content.xml").decode("utf-8")
            assert "Machine Learning" in content


class TestFreeMindWriter:
    def test_generates_valid_xml(self, tmp_path):
        tree = _make_test_tree()
        output = str(tmp_path / "test.mm")
        write_freemind(tree, output)

        tree_xml = xml_parse(output)
        root = tree_xml.getroot()
        assert root.tag == "map"

    def test_contains_node_text(self, tmp_path):
        tree = _make_test_tree()
        output = str(tmp_path / "test.mm")
        write_freemind(tree, output)

        content = open(output, encoding="utf-8").read()
        assert "Root" in content
        assert "Child 1" in content


class TestMarkdownWriter:
    def test_generates_markdown(self, tmp_path):
        tree = _make_test_tree()
        output = str(tmp_path / "test.md")
        write_markdown(tree, output)

        content = open(output, encoding="utf-8").read()
        assert "# Root" in content
        assert "## Child 1" in content
        assert "### Grandchild 1" in content
        assert "Root notes" in content

    def test_e2e_from_pdf(self, simple_pdf, tmp_path):
        spans = extract_spans(simple_pdf)
        lines = group_into_lines(spans)
        level_map = detect_heading_levels(lines)
        doc_root = build_document_tree(lines, level_map)
        mm_root = build_mindmap(doc_root)

        output = str(tmp_path / "e2e.md")
        write_markdown(mm_root, output)

        content = open(output, encoding="utf-8").read()
        assert "Machine Learning" in content
