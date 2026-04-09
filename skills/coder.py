import config
from core.llm_client import llm_client
from core.state_manager import StateManager
from core.file_utils import (
    parse_meta_from_response, parse_code_files,
    save_file, save_meta, read_file, load_meta
)


def run_coder():
    """执行 Coder Skill"""
    print("\n💻 [Coder] 开始生成代码...")

    state = StateManager.load()

    # 读取输入
    plan_content = read_file(config.WORKSPACE_DIR / "plans" / "plan_v1.md")
    plan_meta = load_meta(config.WORKSPACE_DIR / "plans" / "plan_v1.md")
    test_meta = load_meta(config.WORKSPACE_DIR / "reports" / "test_result")

    # 获取 Debugger 反馈（如果存在）
    debugger_feedback = ""
    if test_meta and test_meta.get("verdict") == "failed":
        test_report = read_file(config.WORKSPACE_DIR / "reports" / "test_result.md")
        debugger_feedback = f"""
Debugger 测试失败报告：
{test_report}

错误指纹：{test_meta.get('error_signature', 'N/A')}
失败分析：{test_meta.get('failure_analysis', 'N/A')}
修复建议：{test_meta.get('suggestion_for_coder', 'N/A')}
"""

    # 获取 Reviewer 反馈（如果存在）
    reviewer_feedback = ""
    review_meta = load_meta(config.WORKSPACE_DIR / "reports" / "review")
    if review_meta and review_meta.get("final_decision") == "changes_requested":
        review_report = read_file(config.WORKSPACE_DIR / "reports" / "review.md")
        reviewer_feedback = f"""
Reviewer 评审驳回报告：
{review_report}

需求符合度：{review_meta.get('requirement_compliance', 'N/A')}
"""

    # 获取已有代码（递归搜索子目录）
    existing_code = ""
    code_dir = config.WORKSPACE_DIR / "code"
    for py_file in code_dir.rglob("*.py"):
        rel_path = py_file.relative_to(code_dir)
        existing_code += f"\n--- 现有文件: {rel_path} ---\n{read_file(py_file)}\n"

    # 构建反馈指令
    feedback_sections = []
    if debugger_feedback:
        feedback_sections.append(("Debugger 的反馈", debugger_feedback, "*你必须根据以上反馈修正代码，并确保不再出现相同错误。*"))
    if reviewer_feedback:
        feedback_sections.append(("Reviewer 的反馈", reviewer_feedback, "*你必须根据以上评审意见修改代码，确保满足原始需求。*"))

    if feedback_sections:
        parts = [f"{i}. **{label}**：\n{content}" for i, (label, content, _) in enumerate(feedback_sections, 1)]
        feedback_text = "\n".join(parts)
        feedback_instruction = feedback_sections[-1][2]  # 最后一条指令
    else:
        feedback_text = "无反馈，这是首次生成"
        feedback_instruction = ""

    # 构建 Prompt
    prompt = f"""[角色]
你是一位资深 Python 工程师 (Coder)。你的职责是严格遵循开发计划，生成高质量、可立即运行的代码。

[上下文与约束]
1. **开发计划**：
--- 计划内容 ---
{plan_content}
--- 计划内容结束 ---

2. **Planner 的提示**：
{plan_meta.get('next_step_hint', '无特殊提示') if plan_meta else '无特殊提示'}

3. **现有代码** (如果是修改任务)：
{existing_code if existing_code else '无现有代码，这是全新开发'}

4. **反馈信息**：
{feedback_text}
{feedback_instruction}

[输出要求]
请生成完整的代码文件，并严格按以下格式提供元数据。

第一部分：代码文件
请输出所有需要创建或修改的文件的完整内容。对于每个文件，使用以下格式：
--- 文件路径: {{filepath}} ---
{{file_content}}
--- 文件结束 ---

第二部分：编码元数据
[META_START]
{{
  "agent": "Coder",
  "changes_summary": "简述你对代码所做的主要更改。",
  "addressed_feedback": "说明你如何响应了反馈 (如果没有，填 'N/A')。",
  "key_implementation_notes": [
    "记录关键实现细节，例如为什么选择某个特定算法或库。"
  ],
  "known_limitations": [
    "明确指出此版本代码的已知限制或未处理的边界情况。"
  ]
}}
[META_END]"""

    # 调用 LLM
    response = llm_client.chat(prompt)

    # 解析响应
    main_content, meta = parse_meta_from_response(response)
    files = parse_code_files(main_content)

    # 保存代码文件
    version = state.get("retry_count", 0) + 1
    for filepath, content in files.items():
        full_path = config.WORKSPACE_DIR / filepath
        save_file(full_path, content)
        print(f"   📄 已保存: {filepath}")

    if not files:
        # 如果没有解析出文件，保存原始响应
        raw_path = config.WORKSPACE_DIR / "code" / f"raw_response_v{version}.txt"
        save_file(raw_path, main_content)
        print(f"   ⚠️ 未解析到文件格式，原始响应已保存至 {raw_path}")

    # 保存元数据
    coder_meta_path = config.WORKSPACE_DIR / "code" / f"coder_v{version}.md"
    save_meta(meta or {}, coder_meta_path)

    # 更新状态：递增 total_cycles
    total_cycles = state.get("total_cycles", 0) + 1
    StateManager.update(current_phase="debugging", total_cycles=total_cycles)
    StateManager.append_decision_trail({
        "agent": "Coder",
        "version": version,
        "total_cycles": total_cycles,
        "changes_summary": meta.get("changes_summary", "") if meta else "",
        "addressed_feedback": meta.get("addressed_feedback", "") if meta else ""
    })

    print(f"✅ [Coder] 代码生成完成 (版本 {version}, 总周期 {total_cycles})")
    return main_content
