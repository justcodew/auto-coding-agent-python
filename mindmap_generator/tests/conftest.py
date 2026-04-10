"""测试公共 fixture"""
import pytest
import fitz


@pytest.fixture
def simple_pdf(tmp_path):
    """创建带标题层级的测试 PDF"""
    path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()

    # 模拟多级标题
    page.insert_text((72, 80), "Machine Learning Guide", fontsize=28, fontname="helv")
    page.insert_text((72, 120), "Chapter 1: Overview", fontsize=22, fontname="helv")
    page.insert_text((72, 155), "1.1 What is ML", fontsize=16, fontname="helv")
    page.insert_text((72, 180), "Machine learning is a branch of AI.", fontsize=11, fontname="helv")
    page.insert_text((72, 200), "It focuses on learning from data.", fontsize=11, fontname="helv")
    page.insert_text((72, 240), "1.2 Types of Learning", fontsize=16, fontname="helv")
    page.insert_text((72, 265), "Supervised and unsupervised methods.", fontsize=11, fontname="helv")

    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def flat_pdf(tmp_path):
    """创建无标题层级的纯文本 PDF"""
    path = tmp_path / "flat.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 80), "This is plain text.", fontsize=11, fontname="helv")
    page.insert_text((72, 100), "All same size no headings.", fontsize=11, fontname="helv")
    page.insert_text((72, 120), "Just body content.", fontsize=11, fontname="helv")
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def empty_pdf(tmp_path):
    """创建空 PDF（无文本）"""
    path = tmp_path / "empty.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(path))
    doc.close()
    return str(path)
