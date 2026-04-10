import config
from core.llm_client import llm_client
from core.state_manager import StateManager
from core.file_utils import (
    parse_meta_from_response, save_file, save_meta,
    read_file, load_meta
)
from core.logger import get_logger

logger = get_logger(__name__)


def run_reviewer():
    """执行 Reviewer Skill"""
    logger.info("[Reviewer] 开始最终评审...")

    # 读取输入
    task = StateManager.get_current_task()
    plan_content = read_file(config.WORKSPACE_DIR / "plans" / "plan_v1.md")
    test_meta = load_meta(config.WORKSPACE_DIR / "reports" / "test_result")

    # 读取所有代码文件（递归搜索子目录）
    all_code = ""
    code_dir = config.WORKSPACE_DIR / "code"
    for py_file in code_dir.rglob("*.py"):
        rel_path = py_file.relative_to(code_dir)
        all_code += f"\n--- 文件: {rel_path} ---\n{read_file(py_file)}\n"

    # 构建 Prompt
    prompt = f"""[角色]
你是一位首席软件架构师 (Reviewer)。你的职责是进行最终的代码审查，确保交付物完美符合原始需求，且具备高质量和可维护性。

[评审基准]
1. **原始需求 (最高准则)**：
{task.get('description', '') if task else '无'}

2. **开发计划**：
{plan_content}

3. **待评审的代码**：
{all_code}

4. **测试结果**：
{test_meta if test_meta else '无'}

[输出要求]
请对照原始需求和开发计划，从架构、规范、可读性、安全性等角度进行综合评审。

第一部分：评审报告 (保存为 reports/review.md)
用 Markdown 撰写评审报告，必须包含：
1. **最终结论**：明确给出 "批准合并" 或 "需要修改"。
2. **需求符合度**：评估代码是否完全满足了原始需求。
3. **代码质量评价**：指出优点和存在的具体问题 (如果有)。

第二部分：评审元数据
[META_START]
{{
  "agent": "Reviewer",
  "final_decision": "approved 或 changes_requested",
  "requirement_compliance": "fully 或 partially 或 not_met",
  "critical_issues_count": 0,
  "summary_for_human": "给人类项目管理者的最终总结，1-2句话。"
}}
[META_END]"""

    # 调用 LLM
    response = llm_client.chat(prompt)

    # 解析响应
    main_content, meta = parse_meta_from_response(response)

    # 保存文件
    review_path = config.WORKSPACE_DIR / "reports" / "review.md"
    save_file(review_path, main_content)
    if meta:
        save_meta(meta, review_path)

    # 确定判定结果
    if meta:
        decision = meta.get("final_decision", "changes_requested")
    else:
        # meta 解析失败时，尝试从文本推断
        decision = "approved" if "批准" in main_content and "修改" not in main_content else "changes_requested"
        logger.warning("[Reviewer] 元数据解析失败，从文本推断判定结果")

    state = StateManager.load()

    if decision == "approved":
        StateManager.update(current_phase="completed")
        logger.info("[Reviewer] 评审通过！代码可以合并。")
    else:
        # 不再重置 retry_count，改为递增 review_reject_count
        review_reject_count = state.get("review_reject_count", 0) + 1
        StateManager.update(
            current_phase="coding",
            review_reject_count=review_reject_count
        )
        logger.warning("[Reviewer] 需要修改 (第 %d 次驳回)，将重新进入编码阶段。", review_reject_count)

    StateManager.append_decision_trail({
        "agent": "Reviewer",
        "final_decision": decision,
        "summary": meta.get("summary_for_human", "") if meta else ""
    })

    return main_content
