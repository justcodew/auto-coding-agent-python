"""命令行入口"""

import argparse
import sys
from pathlib import Path

from .pdf_parser.extractor import extract_spans
from .pdf_parser.structure import group_into_lines, detect_heading_levels, build_document_tree
from .mindmap.builder import build_mindmap
from .mindmap.xmind_writer import write_xmind
from .mindmap.freemind_writer import write_freemind
from .mindmap.markdown_writer import write_markdown


def main():
    parser = argparse.ArgumentParser(
        prog="mindmap_generator",
        description="将 PDF 文档转换为脑图（XMind/FreeMind/Markdown）"
    )
    parser.add_argument("input", help="输入 PDF 文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（默认根据格式自动生成）")
    parser.add_argument(
        "-f", "--format",
        choices=["xmind", "freemind", "markdown"],
        default="xmind",
        help="输出格式（默认: xmind）"
    )
    parser.add_argument(
        "--max-depth", type=int, default=4,
        help="最大标题深度（默认: 4）"
    )
    parser.add_argument(
        "--y-tolerance", type=float, default=3.0,
        help="行合并的 y 坐标容差（默认: 3.0 磅）"
    )

    args = parser.parse_args()

    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not input_path.suffix.lower() == ".pdf":
        print(f"警告: 文件可能不是 PDF: {input_path.suffix}", file=sys.stderr)

    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        suffix_map = {"xmind": ".xmind", "freemind": ".mm", "markdown": ".md"}
        output_path = str(input_path.with_suffix(suffix_map[args.format]))

    print(f"📄 输入: {input_path}")
    print(f"📝 输出: {output_path} ({args.format})")

    # Step 1: 提取文本 span
    print("  [1/4] 提取 PDF 文本...")
    spans = extract_spans(str(input_path))
    if not spans:
        print("错误: 未能从 PDF 提取到任何文本", file=sys.stderr)
        sys.exit(1)
    print(f"        提取到 {len(spans)} 个文本片段")

    # Step 2: 分析文档结构
    print("  [2/4] 分析文档结构...")
    lines = group_into_lines(spans, y_tolerance=args.y_tolerance)
    level_map = detect_heading_levels(lines)

    heading_count = sum(1 for l in level_map.values() if l.value > 0)
    print(f"        识别到 {len(lines)} 行文本，{heading_count} 级标题")

    # Step 3: 构建脑图
    print("  [3/4] 构建脑图...")
    root_title = input_path.stem
    doc_root = build_document_tree(lines, level_map, root_title=root_title)
    mm_root = build_mindmap(doc_root, max_depth=args.max_depth)
    print(f"        根节点: {mm_root.text}，{len(mm_root.children)} 个分支")

    # Step 4: 输出文件
    print("  [4/4] 生成输出文件...")
    if args.format == "xmind":
        write_xmind(mm_root, output_path)
    elif args.format == "freemind":
        write_freemind(mm_root, output_path)
    elif args.format == "markdown":
        write_markdown(mm_root, output_path)

    print(f"✅ 完成! 脑图已保存至: {output_path}")
