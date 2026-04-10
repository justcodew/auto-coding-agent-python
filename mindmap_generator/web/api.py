"""FastAPI Web 接口 - PDF 上传、脑图生成和下载"""

import uuid
import os
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, UploadFile, File, HTTPRequest
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..pdf_parser.extractor import extract_spans
from ..pdf_parser.structure import group_into_lines, detect_heading_levels, build_document_tree
from ..mindmap.builder import build_mindmap
from ..mindmap.xmind_writer import write_xmind
from ..mindmap.freemind_writer import write_freemind
from ..mindmap.markdown_writer import write_markdown

app = FastAPI(title="Mind Map Generator", version="1.0.0")

# 任务存储（demo 级别，内存中）
tasks: Dict[str, dict] = {}

# 临时目录
UPLOAD_DIR = Path("/tmp/mindmap_uploads")
OUTPUT_DIR = Path("/tmp/mindmap_outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 模板目录
TEMPLATES_DIR = Path(__file__).parent / "templates"


@app.get("/", response_class=HTMLResponse)
async def index():
    """上传页面"""
    html_path = TEMPLATES_DIR / "upload.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), format: str = "xmind"):
    """
    上传 PDF 文件，生成脑图。

    Args:
        file: 上传的 PDF 文件
        format: 输出格式 (xmind/freemind/markdown)

    Returns:
        task_id 用于后续查询状态和下载
    """
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "只支持 PDF 文件"}

    task_id = uuid.uuid4().hex[:12]

    # 保存上传文件
    input_path = UPLOAD_DIR / f"{task_id}.pdf"
    content = await file.read()
    input_path.write_bytes(content)

    # 初始化任务状态
    tasks[task_id] = {
        "status": "processing",
        "filename": file.filename,
        "format": format,
        "output_path": None,
        "error": None,
    }

    # 同步处理（demo 级别）
    try:
        _process_pdf(task_id, str(input_path), file.filename, format)
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        return {"task_id": task_id, "status": "failed", "error": str(e)}

    return {"task_id": task_id, "status": "completed"}


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """查询处理状态"""
    if task_id not in tasks:
        return {"error": "任务不存在"}
    return tasks[task_id]


@app.get("/download/{task_id}")
async def download(task_id: str):
    """下载生成的脑图文件"""
    if task_id not in tasks:
        return {"error": "任务不存在"}

    task = tasks[task_id]
    if task["status"] != "completed":
        return {"error": f"任务状态: {task['status']}"}

    output_path = task.get("output_path")
    if not output_path or not Path(output_path).exists():
        return {"error": "输出文件不存在"}

    return FileResponse(
        output_path,
        filename=Path(output_path).name,
        media_type="application/octet-stream",
    )


def _process_pdf(task_id: str, pdf_path: str, filename: str, fmt: str):
    """处理 PDF 生成脑图"""
    spans = extract_spans(pdf_path)
    lines = group_into_lines(spans)
    level_map = detect_heading_levels(lines)

    root_title = Path(filename).stem
    doc_root = build_document_tree(lines, level_map, root_title=root_title)
    mm_root = build_mindmap(doc_root)

    suffix_map = {"xmind": ".xmind", "freemind": ".mm", "markdown": ".md"}
    output_path = str(OUTPUT_DIR / f"{task_id}{suffix_map.get(fmt, '.xmind')}")

    if fmt == "xmind":
        write_xmind(mm_root, output_path)
    elif fmt == "freemind":
        write_freemind(mm_root, output_path)
    elif fmt == "markdown":
        write_markdown(mm_root, output_path)

    tasks[task_id]["status"] = "completed"
    tasks[task_id]["output_path"] = output_path
