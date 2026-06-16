import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "knowledge"
SEED_DIR = ROOT / "data" / "seed"

SOURCE_BASE = (
    Path.home()
    / "Desktop"
    / "\u9879\u76ee\u8bfe\u8bfe\u4ef6"
    / "\u8bfe\u4ef6"
    / "\u7b2c\u4e8c\u5468"
    / "Dify"
    / "\u6559\u80b2\u670d\u52a1"
)

DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", DOCX_NS):
        text = "".join(
            node.text or "" for node in paragraph.findall(".//w:t", DOCX_NS)
        ).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def read_xlsx(path: Path) -> list[dict[str, str]]:
    try:
        import openpyxl
    except Exception as exc:  # pragma: no cover - depends on local env
        raise RuntimeError("openpyxl is required to extract xlsx files") from exc

    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    rows: list[dict[str, str]] = []
    for sheet in workbook.worksheets:
        values = list(sheet.iter_rows(values_only=True))
        if not values:
            continue
        headers = [str(value or "").strip() for value in values[0]]
        for raw in values[1:]:
            record = {
                headers[index] or f"col_{index + 1}": str(value or "").strip()
                for index, value in enumerate(raw)
                if index < len(headers)
            }
            if any(record.values()):
                record["_sheet"] = sheet.title
                rows.append(record)
    return rows


def read_pdf(path: Path) -> str:
    try:
        import pdfplumber
    except Exception as exc:  # pragma: no cover - depends on local env
        raise RuntimeError("pdfplumber is required to extract pdf files") from exc

    chunks: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunk for chunk in chunks if chunk.strip())


def write_text(name: str, title: str, body: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SEED_DIR.mkdir(parents=True, exist_ok=True)

    if not SOURCE_BASE.exists():
        raise SystemExit(f"Source directory not found: {SOURCE_BASE}")

    documents = [
        ("company_info.md", "企业信息", SOURCE_BASE / "公司信息" / "企业信息.docx"),
        ("new_employee_guide.md", "公司新人指南", SOURCE_BASE / "公司信息" / "公司新人指南.docx"),
        (
            "germany_program.md",
            "中德精英人才共建计划",
            SOURCE_BASE / "公司业务" / "中德精英人才共建计划.docx",
        ),
        (
            "singapore_program.md",
            "新加坡国际本硕升学计划",
            SOURCE_BASE / "公司业务" / "新加坡国际本硕升学计划.docx",
        ),
        (
            "germany_policy.md",
            "德国留学政策指南",
            SOURCE_BASE / "留学政策" / "德国留学政策指南.docx",
        ),
        (
            "singapore_policy.md",
            "新加坡留学政策指南",
            SOURCE_BASE / "留学政策" / "新加坡留学政策指南.docx",
        ),
        (
            "lead_profile_rules.md",
            "用户画像研判规则",
            SOURCE_BASE / "用户研判规则" / "用户画像研判规则.docx",
        ),
    ]

    for filename, title, path in documents:
        write_text(filename, title, read_docx(path))
        print(f"extracted {path.name} -> {filename}")

    faq_txt = SOURCE_BASE / "公司信息" / "问答对文本版.txt"
    write_text("faq_text.md", "常见问答文本版", faq_txt.read_text(encoding="utf-8"))

    faq_rows = read_xlsx(SOURCE_BASE / "公司信息" / "常见问答对.xlsx")
    (SEED_DIR / "faq.json").write_text(
        json.dumps(faq_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    requirements = read_xlsx(SOURCE_BASE / "客户需求表.xlsx")
    (SEED_DIR / "customer_requirements.json").write_text(
        json.dumps(requirements, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    resume_dir = SOURCE_BASE / "测试简历"
    resumes: list[dict[str, str]] = []
    for resume in sorted(resume_dir.glob("*.pdf")):
        try:
            text = read_pdf(resume)
        except Exception as exc:
            text = f"PDF extraction failed: {exc}"
        resumes.append({"filename": resume.name, "text": text[:8000]})
    (SEED_DIR / "sample_resumes.json").write_text(
        json.dumps(resumes, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"knowledge files written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
