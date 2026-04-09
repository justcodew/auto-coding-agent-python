"""测试 core/file_utils.py"""
import json
import pytest
from pathlib import Path
from core.file_utils import (
    parse_meta_from_response,
    parse_code_files,
    save_file,
    read_file,
    save_meta,
    load_meta,
)


class TestParseMetaFromResponse:
    """测试元数据解析"""

    def test_normal_meta(self):
        """正常 META 块解析"""
        response = """这是一些正文内容

[META_START]
{"agent": "Planner", "key_interpretation": "测试"}
[META_END]

更多内容"""
        content, meta = parse_meta_from_response(response)
        assert "这是一些正文内容" in content
        assert "更多内容" in content
        assert meta is not None
        assert meta["agent"] == "Planner"

    def test_meta_with_trailing_comma(self):
        """带尾随逗号的 JSON 自动修复"""
        response = """正文
[META_START]
{"agent": "Coder", "items": [1, 2, 3,],}
[META_END]"""
        content, meta = parse_meta_from_response(response)
        assert meta is not None
        assert meta["agent"] == "Coder"
        assert meta["items"] == [1, 2, 3]

    def test_meta_with_invalid_json(self):
        """完全无效的 JSON 应返回 None"""
        response = """正文
[META_START]
{broken json [[[}}
[META_END]"""
        content, meta = parse_meta_from_response(response)
        assert meta is None

    def test_no_meta_block(self):
        """没有 META 块时返回原始内容和 None"""
        response = "纯文本内容，没有任何元数据"
        content, meta = parse_meta_from_response(response)
        assert content == response
        assert meta is None

    def test_meta_multiline_json(self):
        """多行 JSON 解析"""
        response = """正文
[META_START]
{
  "agent": "Debugger",
  "verdict": "passed",
  "details": {
    "checks": 5,
    "errors": 0
  }
}
[META_END]"""
        content, meta = parse_meta_from_response(response)
        assert meta is not None
        assert meta["verdict"] == "passed"
        assert meta["details"]["checks"] == 5

    def test_meta_empty_block(self):
        """空 META 块"""
        response = """正文
[META_START]
[META_END]"""
        content, meta = parse_meta_from_response(response)
        assert meta is None

    def test_meta_chinese_content(self):
        """含中文的 JSON"""
        response = """正文
[META_START]
{"agent": "Reviewer", "summary": "代码质量良好，符合需求"}
[META_END]"""
        content, meta = parse_meta_from_response(response)
        assert meta is not None
        assert "良好" in meta["summary"]


class TestParseCodeFiles:
    """测试代码文件解析 - 4级降级策略"""

    def test_strategy1_original_format(self):
        """策略1: 原始格式 --- 文件路径: path --- content --- 文件结束 ---"""
        response = """一些说明文字

--- 文件路径: main.py ---
def hello():
    print("hello")
--- 文件结束 ---

--- 文件路径: utils.py ---
def add(a, b):
    return a + b
--- 文件结束 ---"""
        files = parse_code_files(response)
        assert len(files) == 2
        assert "main.py" in files
        assert "utils.py" in files
        assert "def hello" in files["main.py"]

    def test_strategy1_flexible_spacing(self):
        """策略1: 宽松空格匹配"""
        response = """---  文件路径:  test.py  ---
x = 1
---文件结束---"""
        files = parse_code_files(response)
        assert len(files) == 1
        assert "test.py" in files

    def test_strategy2_code_block_with_comment(self):
        """策略2: 代码块 + 文件路径注释"""
        response = """说明文字

```python
# 文件路径: main.py
def hello():
    print("hello")
```

```python
# file: utils.py
def add(a, b):
    return a + b
```"""
        files = parse_code_files(response)
        assert len(files) == 2
        assert "main.py" in files
        assert "utils.py" in files

    def test_strategy2_path_variant(self):
        """策略2: path: 前缀"""
        response = """```python
# path: helper.py
def help():
    pass
```"""
        files = parse_code_files(response)
        assert len(files) == 1
        assert "helper.py" in files

    def test_strategy3_title_plus_code_block(self):
        """策略3: 文件名标题 + 代码块"""
        response = """说明文字

**main.py**

```python
def hello():
    print("hello")
```

`utils.py`

```python
def add(a, b):
    return a + b
```"""
        files = parse_code_files(response)
        assert len(files) == 2
        assert "main.py" in files
        assert "utils.py" in files

    def test_strategy4_single_python_block(self):
        """策略4: 单个 python 代码块 → main.py"""
        response = """说明文字

```python
def hello():
    print("hello")
```"""
        files = parse_code_files(response)
        assert len(files) == 1
        assert "main.py" in files

    def test_strategy4_multiple_python_blocks(self):
        """策略4: 多个 python 代码块 → module_N.py"""
        response = """说明文字

```python
def hello():
    print("hello")
```

```python
def world():
    print("world")
```"""
        files = parse_code_files(response)
        assert len(files) == 2
        assert "module_1.py" in files
        assert "module_2.py" in files

    def test_no_code_blocks(self):
        """没有任何代码块"""
        response = "纯文本，没有代码"
        files = parse_code_files(response)
        assert len(files) == 0

    def test_strategy3_yaml_file(self):
        """策略3: 支持 yaml/yml 文件"""
        response = """**config.yaml**

```yaml
key: value
```"""
        files = parse_code_files(response)
        assert len(files) == 1
        assert "config.yaml" in files


class TestFileIO:
    """测试文件读写"""

    def test_save_and_read(self, tmp_path):
        """基本保存和读取"""
        fpath = tmp_path / "test.txt"
        save_file(fpath, "hello world")
        assert read_file(fpath) == "hello world"

    def test_save_creates_parent_dirs(self, tmp_path):
        """自动创建父目录"""
        fpath = tmp_path / "a" / "b" / "c" / "test.txt"
        save_file(fpath, "deep nested")
        assert read_file(fpath) == "deep nested"

    def test_read_nonexistent(self, tmp_path):
        """读取不存在的文件返回空字符串"""
        assert read_file(tmp_path / "nope.txt") == ""

    def test_save_overwrites(self, tmp_path):
        """覆盖写入"""
        fpath = tmp_path / "test.txt"
        save_file(fpath, "first")
        save_file(fpath, "second")
        assert read_file(fpath) == "second"

    def test_chinese_content(self, tmp_path):
        """中文内容读写"""
        fpath = tmp_path / "cn.txt"
        save_file(fpath, "你好世界")
        assert read_file(fpath) == "你好世界"


class TestMetaIO:
    """测试元数据文件读写"""

    def test_save_and_load_meta(self, tmp_path):
        """基本元数据读写"""
        base = tmp_path / "report.md"
        meta = {"agent": "Debugger", "verdict": "passed"}
        save_meta(meta, base)

        loaded = load_meta(base)
        assert loaded is not None
        assert loaded["agent"] == "Debugger"
        assert loaded["verdict"] == "passed"

        # 检查文件路径
        meta_path = tmp_path / "report.meta.json"
        assert meta_path.exists()

    def test_load_nonexistent_meta(self, tmp_path):
        """加载不存在的元数据返回 None"""
        base = tmp_path / "nonexist.md"
        assert load_meta(base) is None

    def test_meta_filename_convention(self, tmp_path):
        """元数据文件命名约定: basefile.ext → basefile.meta.json"""
        base = tmp_path / "test_result.md"
        save_meta({"test": True}, base)
        meta_path = tmp_path / "test_result.meta.json"
        assert meta_path.exists()
