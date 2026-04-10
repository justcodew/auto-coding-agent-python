"""测试关键词提取"""
from mindmap_generator.pdf_parser.keywords import extract_keywords


class TestKeywordExtraction:
    def test_extracts_meaningful_words(self):
        text = """
        Machine learning is a branch of artificial intelligence.
        Machine learning algorithms learn from data.
        Deep learning is a subset of machine learning.
        Neural networks power deep learning systems.
        """
        keywords = extract_keywords(text, top_n=5)
        assert len(keywords) > 0
        # "learn" or "learning" or "machine" should be top keywords
        # (stemming not applied, but "learn" and "machine" are frequent)
        assert "machine" in keywords or "learn" in keywords or "learning" in keywords

    def test_ignores_stop_words(self):
        text = "The quick brown fox jumps over the lazy dog."
        keywords = extract_keywords(text, top_n=3)
        # "the", "over" should not appear
        assert "the" not in keywords
        assert "over" not in keywords

    def test_empty_text(self):
        assert extract_keywords("", top_n=5) == []

    def test_short_words_filtered(self):
        text = "I am a big fan of programming languages"
        keywords = extract_keywords(text, top_n=5)
        for kw in keywords:
            assert len(kw) >= 3
