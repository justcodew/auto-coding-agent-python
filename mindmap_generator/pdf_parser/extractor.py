"""PDF 文本提取 - 使用 PyMuPDF 提取带字体信息的文本 span"""

import logging
from typing import List
import fitz

from ..models import TextSpan

logger = logging.getLogger(__name__)


def extract_spans(pdf_path: str) -> List[TextSpan]:
    """
    从 PDF 文件提取所有文本 span。

    每个 span 包含文本内容、字体名称、字体大小、页码和位置信息。

    Args:
        pdf_path: PDF 文件路径

    Returns:
        TextSpan 列表，按页码和位置排序
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise ValueError(f"无法打开 PDF 文件: {pdf_path} - {e}")

    spans: List[TextSpan] = []

    for page_num, page in enumerate(doc):
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # 只处理文本块
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    font_size = span.get("size", 0)
                    if font_size <= 0:
                        continue

                    origin = span.get("origin", [0, 0])

                    spans.append(TextSpan(
                        text=text,
                        font_name=span.get("font", "unknown"),
                        font_size=font_size,
                        page_number=page_num,
                        origin_x=origin[0],
                        origin_y=origin[1],
                    ))

    doc.close()

    if not spans:
        logger.warning("PDF 中未提取到任何文本（可能是扫描版 PDF）")

    return spans
