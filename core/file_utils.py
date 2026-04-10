import re
import json
from pathlib import Path
from typing import Tuple, Optional

from .logger import get_logger

logger = get_logger(__name__)


def parse_meta_from_response(response: str) -> Tuple[str, Optional[dict]]:
    """
    从响应中分离主体内容和元数据。
    返回: (主体内容, 元数据字典或None)
    """
    meta_pattern = r"\[META_START\](.*?)\[META_END\]"
    match = re.search(meta_pattern, response, re.DOTALL)

    if match:
        meta_str = match.group(1).strip()
        main_content = re.sub(meta_pattern, "", response, flags=re.DOTALL).strip()
        try:
            meta = json.loads(meta_str)
            return main_content, meta
        except json.JSONDecodeError:
            # 尝试修复常见的 JSON 格式问题（如尾随逗号）
            meta_str_fixed = re.sub(r',\s*([}\]])', r'\1', meta_str)
            try:
                meta = json.loads(meta_str_fixed)
                return main_content, meta
            except json.JSONDecodeError:
                logger.warning("元数据 JSON 解析失败")
                return response, None
    return response, None


def parse_code_files(response: str) -> dict:
    """
    从 Coder 响应中解析出文件路径和内容。
    支持多种格式，按优先级降级尝试。
    返回: {文件路径: 文件内容}
    """
    files = {}

    # 策略 1: 原始格式 --- 文件路径: path --- content --- 文件结束 ---
    # 宽松匹配，允许空格变化
    pattern1 = r"---\s*文件路径:\s*(.*?)\s*---\n(.*?)\n---\s*文件结束\s*---"
    matches = re.findall(pattern1, response, re.DOTALL)
    if matches:
        for path, content in matches:
            files[path.strip()] = content.strip()
        return files

    # 策略 2: Markdown 代码块 + 文件路径注释 (# file: path / # 文件路径: path)
    pattern2 = r"```(?:python|py)?\s*\n#\s*(?:文件路径|file|path):\s*(.+?)\n(.*?)```"
    matches = re.findall(pattern2, response, re.DOTALL)
    if matches:
        for path, content in matches:
            files[path.strip()] = content.strip()
        return files

    # 策略 3: 文件名标题 + Markdown 代码块 (如 **main.py** 后跟 ```python)
    pattern3 = r"(?:\*\*|`)([\w./\\]+\.(?:py|json|yaml|yml|toml|cfg|txt))(?:\*\*|`)\s*\n```(?:\w+)?\s*\n(.*?)```"
    matches = re.findall(pattern3, response, re.DOTALL)
    if matches:
        for path, content in matches:
            files[path.strip()] = content.strip()
        return files

    # 策略 4: 直接提取 ```python 代码块（最后手段，使用序号命名）
    pattern4 = r"```(?:python|py)\s*\n(.*?)```"
    matches = re.findall(pattern4, response, re.DOTALL)
    if len(matches) == 1:
        files["main.py"] = matches[0].strip()
        return files
    elif len(matches) > 1:
        for i, content in enumerate(matches):
            files[f"module_{i+1}.py"] = content.strip()
        return files

    return files


def save_file(path: Path, content: str):
    """保存文件，自动创建父目录"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def read_file(path: Path) -> str:
    """读取文件内容"""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def save_meta(meta: dict, output_path: Path):
    """保存元数据文件"""
    meta_path = output_path.with_suffix(".meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def load_meta(base_path: Path) -> Optional[dict]:
    """加载元数据文件"""
    meta_path = base_path.with_suffix(".meta.json")
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
