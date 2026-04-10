import config
import hashlib
from core.llm_client import llm_client
from core.state_manager import StateManager
from core.file_utils import (
    parse_meta_from_response, save_file, save_meta,
    read_file, load_meta
)
from core.logger import get_logger

logger = get_logger(__name__)


def generate_error_signature(error_description: str) -> str:
    """根据错误描述生成确定性指纹（比 LLM 自述更可靠）"""
    if not error_description:
        return "N/A"
    return hashlib.md5(error_description[:100].encode()).hexdigest()[:16]


def run_debugger():
    """执行 Debugger Skill"""
    logger.info("[Debugger] 开始审查代码...")

    state = StateManager.load()

    # 读取输入
    plan_content = read_file(config.WORKSPACE_DIR / "plans" / "plan_v1.md")
    coder_meta = load_meta(config.WORKSPACE_DIR / "code" / f"coder_v{state.get('retry_count', 0) + 1}.md")

    # 读取所有代码文件（递归搜索子目录）
    all_code = ""
    code_dir = config.WORKSPACE_DIR / "code"
    for py_file in code_dir.rglob("*.py"):
        rel_path = py_file.relative_to(code_dir)
        all_code += f"\n--- 文件: {rel_path} ---\n{read_file(py_file)}\n"

    # 构建 Prompt
    prompt = f"""[角色]
你是一位严谨的软件测试工程师 (Debugger)。你的任务是对给定的代码进行审查，找出任何可能导致程序失败、行为异常或不符合计划的问题。

[审查依据]
1. **开发计划**：
{plan_content}

2. **代码文件**：
{all_code}

3. **Coder 的说明**：
{coder_meta if coder_meta else '无'}

[输出要求]
请基于以上信息，对代码进行审查，并按以下格式输出。

第一部分：测试报告 (保存为 reports/test_result.md)
请用 Markdown 撰写一份测试报告，内容需包括：
1. **测试结论**：明确给出 "通过" 或 "失败"。
2. **问题列表** (如果失败)：详细列出发现的问题，包含错误位置和现象。
3. **改进建议** (如果失败)：向 Coder 提出具体的修复建议。

第二部分：测试元数据
[META_START]
{{
  "agent": "Debugger",
  "verdict": "passed 或 failed",
  "error_signature": "如果失败，生成一个能代表此错误的简短描述，例如 'NameError_main_py_line_12'。如果通过，填 'N/A'。",
  "failure_category": "如果失败，将错误归类为 '语法错误', '逻辑错误', '需求不符', 或 '性能问题'。",
  "failure_analysis": "详细分析失败原因",
  "suggestion_for_coder": "给 Coder 的具体修复建议",
  "next_action_suggestion": "给系统的建议，如 'continue' 或 'retry'"
}}
[META_END]"""

    # 调用 LLM
    response = llm_client.chat(prompt)

    # 解析响应
    main_content, meta = parse_meta_from_response(response)

    # 保存文件
    report_path = config.WORKSPACE_DIR / "reports" / "test_result.md"
    save_file(report_path, main_content)
    if meta:
        save_meta(meta, report_path)

    # 确定判定结果
    if meta:
        verdict = meta.get("verdict", "failed")
    else:
        # meta 解析失败时，尝试从文本推断
        verdict = "passed" if "通过" in main_content and "失败" not in main_content else "failed"
        logger.warning("[Debugger] 元数据解析失败，从文本推断判定结果")

    # 使用程序化指纹（确定性，不受 LLM 输出格式影响）
    error_signature = generate_error_signature(main_content[:200]) if verdict == "failed" else ""

    if verdict == "passed":
        StateManager.update(
            current_phase="reviewing",
            last_error_signature=None
        )
        logger.info("[Debugger] 代码验证通过！")
    else:
        # 检查是否陷入循环
        last_error = state.get("last_error_signature")
        loop_detection = state.get("loop_detection", {})
        consecutive = loop_detection.get("consecutive_same_error", 0)

        if last_error and last_error == error_signature:
            consecutive += 1
        else:
            consecutive = 1

        new_retry_count = state.get("retry_count", 0) + 1

        # 合并更新 loop_detection，保留已有字段
        loop_detection["consecutive_same_error"] = consecutive

        StateManager.update(
            current_phase="coding",
            retry_count=new_retry_count,
            last_error_signature=error_signature,
            loop_detection=loop_detection
        )

        if consecutive >= config.LOOP_DETECTION_THRESHOLD:
            logger.warning("[Debugger] 连续 %d 次相同错误，可能陷入死循环！", consecutive)
        else:
            logger.warning("[Debugger] 发现问题，将重新编码 (第 %d 次重试)", new_retry_count)

    StateManager.append_decision_trail({
        "agent": "Debugger",
        "verdict": verdict,
        "error_signature": error_signature
    })

    return main_content
