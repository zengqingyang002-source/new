"""
文件解析模块 —— 解析上传的文件内容

这个模块负责把用户上传的简历/文档文件"读懂"，
支持 4 种常见格式：
- .txt：纯文本文件（直接读取）
- .docx：Word 文档（用 XML 解析）
- .xlsx：Excel 表格（用 openpyxl 解析）
- .pdf：PDF 文件（用 pdfplumber 解析）

所有格式解析完后都返回纯文本字符串，
方便后续的评估模块（evaluator.py）进行分析。
"""

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from fastapi import UploadFile

# XML 命名空间 —— docx 文件里的 XML 需要这个才能找到正确的内容
DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


async def parse_upload(file: UploadFile) -> tuple[str, str]:
    """
    解析上传的文件，提取文本内容

    参数：
      file: FastAPI 的上传文件对象

    返回：
      (文本内容, 文件类型) 的元组
      比如 ("张三  23岁  本科学历...", "docx")
    """
    # 获取文件后缀名（.txt, .docx 等）
    suffix = Path(file.filename or "upload.txt").suffix.lower()

    # 读取文件的所有字节内容
    payload = await file.read()

    # 根据文件类型选择不同的解析方式
    if suffix == ".txt":
        return payload.decode("utf-8", errors="ignore"), "txt"
    if suffix == ".docx":
        return parse_docx_bytes(payload), "docx"
    if suffix == ".xlsx":
        return parse_xlsx_bytes(payload), "xlsx"
    if suffix == ".pdf":
        return parse_pdf_bytes(payload), "pdf"

    # 不认识的文件类型，当纯文本处理
    return payload.decode("utf-8", errors="ignore"), suffix.replace(".", "") or "file"


def parse_docx_bytes(payload: bytes) -> str:
    """
    解析 docx 文件（Word 文档）

    docx 本质上是一个"压缩包"，里面包含 XML 格式的文档内容。
    这里用 Python 的 zipfile 解压，然后用 ElementTree 解析 XML，
    提取出所有的文本段落（<w:t> 标签中的内容）。
    """
    import io

    # docx 就是 zip 压缩包，解压后读取 word/document.xml
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        xml = archive.read("word/document.xml")

    root = ET.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", DOCX_NS):
        # 提取段落中的所有文本节点
        text = "".join(
            node.text or "" for node in paragraph.findall(".//w:t", DOCX_NS)
        ).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def parse_xlsx_bytes(payload: bytes) -> str:
    """
    解析 xlsx 文件（Excel 表格）

    用 openpyxl 库读取 Excel 文件，遍历所有工作表，
    把每个单元格的内容用竖线（|）连接起来。
    """
    import io

    import openpyxl

    workbook = openpyxl.load_workbook(io.BytesIO(payload), data_only=True, read_only=True)
    lines: list[str] = []
    for sheet in workbook.worksheets:
        lines.append(f"工作表：{sheet.title}")
        for row in sheet.iter_rows(values_only=True):
            values = [str(value or "").strip() for value in row]
            if any(values):
                lines.append(" | ".join(values))
    return "\n".join(lines)


def parse_pdf_bytes(payload: bytes) -> str:
    """
    解析 PDF 文件

    用 pdfplumber 库读取 PDF，逐页提取文字。
    pdfplumber 比 PyPDF2 更能保留文字的排版和顺序。
    """
    import io

    import pdfplumber

    chunks: list[str] = []
    with pdfplumber.open(io.BytesIO(payload)) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunk for chunk in chunks if chunk.strip())
