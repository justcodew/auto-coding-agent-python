"""测试 PDF 提取模块"""
import pytest
from mindmap_generator.pdf_parser.extractor import extract_spans


class TestExtractSpans:
    def test_extracts_spans_with_font_info(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        assert len(spans) > 0

        # 检查包含不同字体大小
        sizes = set(s.font_size for s in spans)
        assert len(sizes) >= 3  # 28, 22, 16, 11

        # 检查最大的字体是标题
        title_span = max(spans, key=lambda s: s.font_size)
        assert "Machine Learning" in title_span.text

    def test_empty_pdf_returns_empty(self, empty_pdf):
        spans = extract_spans(empty_pdf)
        assert spans == []

    def test_spans_have_correct_fields(self, simple_pdf):
        spans = extract_spans(simple_pdf)
        for span in spans:
            assert span.text != ""
            assert span.font_size > 0
            assert span.page_number >= 0
            assert span.origin_x >= 0
            assert span.origin_y >= 0

    def test_invalid_pdf_raises(self, tmp_path):
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_text("not a pdf")
        with pytest.raises(ValueError, match="无法打开"):
            extract_spans(str(fake_pdf))

    def test_nonexistent_file_raises(self):
        with pytest.raises(ValueError):
            extract_spans("/nonexistent/file.pdf")
