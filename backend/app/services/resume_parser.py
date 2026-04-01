"""
Echo Mock System - 简历文件解析服务
====================================
支持从 PDF 和 DOCX 文件中提取纯文本内容。
仅在内存中处理，不持久化原始文件。
"""

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def parse_resume(file_bytes: bytes, filename: str) -> Optional[str]:
    """
    根据文件扩展名解析简历内容为纯文本。

    Args:
        file_bytes: 文件的二进制内容
        filename: 原始文件名（用于判断格式）

    Returns:
        解析后的纯文本字符串，失败返回 None
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        if ext == "pdf":
            return _parse_pdf(file_bytes)
        elif ext in ("docx", "doc"):
            return _parse_docx(file_bytes)
        else:
            logger.warning(f"不支持的简历格式: .{ext}")
            return None
    except Exception as e:
        logger.error(f"简历解析失败 ({filename}): {e}")
        return None


def _parse_pdf(file_bytes: bytes) -> str:
    """使用 pdfplumber 从 PDF 中提取文本。"""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())

    return "\n\n".join(text_parts)


def _parse_docx(file_bytes: bytes) -> str:
    """使用 python-docx 从 DOCX 中提取文本。"""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    text_parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text.strip())

    return "\n".join(text_parts)
