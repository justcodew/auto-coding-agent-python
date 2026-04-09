from pathlib import Path
import config
from core.state_manager import StateManager
from core.file_utils import read_file, load_meta


class SentryCheck:
    """哨兵检查器"""

    @staticmethod
    def check_before_planner() -> tuple[bool, str]:
        """Planner 前置检查"""
        task = StateManager.get_current_task()
        if not task:
            return False, "没有当前任务，请先创建 tasks/current.json"
        if not task.get("description"):
            return False, "任务描述为空"
        return True, "OK"

    @staticmethod
    def check_before_coder() -> tuple[bool, str]:
        """Coder 前置检查"""
        plan_file = config.WORKSPACE_DIR / "plans" / "plan_v1.md"

        if not plan_file.exists():
            return False, "计划文件不存在，回退到 planning 阶段"

        plan_content = read_file(plan_file)
        if not plan_content.strip():
            return False, "计划文件为空，回退到 planning 阶段"

        state = StateManager.load()
        if state["retry_count"] >= state["max_retries"]:
            return False, f"重试次数已达上限 ({state['max_retries']})，请人工介入"

        if state.get("total_cycles", 0) >= config.TOTAL_CYCLE_LIMIT:
            return False, f"总编码周期已达上限 ({config.TOTAL_CYCLE_LIMIT})，请人工介入"

        return True, "OK"

    @staticmethod
    def check_before_debugger() -> tuple[bool, str]:
        """Debugger 前置检查"""
        code_dir = config.WORKSPACE_DIR / "code"
        code_files = list(code_dir.rglob("*.py"))

        if not code_files:
            return False, "code 目录下没有 Python 文件"

        # 检查 Coder 是否输出了错误标记
        for py_file in code_files:
            content = read_file(py_file)
            if "抱歉，我无法" in content or "I cannot" in content:
                return False, "Coder 输出包含拒绝标记，需重新生成"

        return True, "OK"

    @staticmethod
    def check_before_reviewer() -> tuple[bool, str]:
        """Reviewer 前置检查"""
        test_result_meta = load_meta(config.WORKSPACE_DIR / "reports" / "test_result")

        if not test_result_meta:
            return False, "缺少 Debugger 测试结果"

        if test_result_meta.get("verdict") != "passed":
            return False, "Debugger 测试未通过，不能进入评审阶段"

        return True, "OK"

    @staticmethod
    def detect_loop() -> tuple[bool, str]:
        """死循环检测"""
        state = StateManager.load()

        # 检查连续相同错误
        consecutive = state.get("loop_detection", {}).get("consecutive_same_error", 0)
        if consecutive >= config.LOOP_DETECTION_THRESHOLD:
            return True, f"连续 {consecutive} 次相同错误，建议暂停"

        return False, "OK"
