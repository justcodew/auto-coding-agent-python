"""测试 core/sentry_checks.py"""
import json
import pytest
from pathlib import Path
from core.sentry_checks import SentryCheck
from core.state_manager import StateManager
import config


@pytest.fixture(autouse=True)
def setup_workspace(tmp_path, monkeypatch):
    """每个测试前设置临时工作区"""
    monkeypatch.setattr(config, "WORKSPACE_DIR", tmp_path)
    monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

    # 创建必要目录
    for subdir in ["tasks", "plans", "code", "reports"]:
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)

    # 初始化默认状态
    StateManager.save(StateManager.DEFAULT_STATE.copy())


class TestCheckBeforePlanner:
    """Planner 前置检查"""

    def test_ok_with_valid_task(self, tmp_path):
        """有效任务时通过"""
        StateManager.save_current_task({"id": "1", "description": "写一个函数"})
        ok, msg = SentryCheck.check_before_planner()
        assert ok is True
        assert msg == "OK"

    def test_fail_no_task(self):
        """没有任务文件时失败"""
        ok, msg = SentryCheck.check_before_planner()
        assert ok is False
        assert "没有当前任务" in msg

    def test_fail_empty_description(self, tmp_path):
        """任务描述为空时失败"""
        StateManager.save_current_task({"id": "1", "description": ""})
        ok, msg = SentryCheck.check_before_planner()
        assert ok is False
        assert "描述为空" in msg

    def test_fail_missing_description_key(self, tmp_path):
        """任务缺少 description 字段时失败"""
        StateManager.save_current_task({"id": "1"})
        ok, msg = SentryCheck.check_before_planner()
        assert ok is False


class TestCheckBeforeCoder:
    """Coder 前置检查"""

    def test_ok_all_conditions_met(self, tmp_path):
        """所有条件满足时通过"""
        # 创建计划文件
        (tmp_path / "plans" / "plan_v1.md").write_text("开发计划内容")
        StateManager.update(retry_count=0, total_cycles=0)

        ok, msg = SentryCheck.check_before_coder()
        assert ok is True

    def test_fail_no_plan(self):
        """没有计划文件时失败"""
        ok, msg = SentryCheck.check_before_coder()
        assert ok is False
        assert "回退到 planning" in msg

    def test_fail_empty_plan(self, tmp_path):
        """计划文件为空时失败"""
        (tmp_path / "plans" / "plan_v1.md").write_text("  \n  ")
        ok, msg = SentryCheck.check_before_coder()
        assert ok is False
        assert "回退到 planning" in msg

    def test_fail_max_retries_reached(self, tmp_path):
        """重试次数达上限时失败"""
        (tmp_path / "plans" / "plan_v1.md").write_text("计划")
        StateManager.update(retry_count=config.MAX_RETRIES)

        ok, msg = SentryCheck.check_before_coder()
        assert ok is False
        assert "重试次数已达上限" in msg

    def test_fail_total_cycle_limit(self, tmp_path):
        """总编码周期达上限时失败"""
        (tmp_path / "plans" / "plan_v1.md").write_text("计划")
        StateManager.update(total_cycles=config.TOTAL_CYCLE_LIMIT)

        ok, msg = SentryCheck.check_before_coder()
        assert ok is False
        assert "总编码周期已达上限" in msg

    def test_ok_at_max_retries_minus_one(self, tmp_path):
        """retry_count = max_retries - 1 时仍可通过"""
        (tmp_path / "plans" / "plan_v1.md").write_text("计划")
        StateManager.update(retry_count=config.MAX_RETRIES - 1)

        ok, msg = SentryCheck.check_before_coder()
        assert ok is True


class TestCheckBeforeDebugger:
    """Debugger 前置检查"""

    def test_ok_with_code_files(self, tmp_path):
        """有 Python 文件时通过"""
        (tmp_path / "code" / "main.py").write_text("print('hello')")
        ok, msg = SentryCheck.check_before_debugger()
        assert ok is True

    def test_fail_no_code_files(self):
        """没有 Python 文件时失败"""
        ok, msg = SentryCheck.check_before_debugger()
        assert ok is False
        assert "没有 Python 文件" in msg

    def test_ok_recursive_search(self, tmp_path):
        """递归搜索子目录中的 Python 文件"""
        sub_dir = tmp_path / "code" / "subdir"
        sub_dir.mkdir(parents=True)
        (sub_dir / "module.py").write_text("x = 1")
        ok, msg = SentryCheck.check_before_debugger()
        assert ok is True

    def test_fail_refusal_marker_chinese(self, tmp_path):
        """代码包含中文拒绝标记时失败"""
        (tmp_path / "code" / "main.py").write_text("抱歉，我无法完成此任务")
        ok, msg = SentryCheck.check_before_debugger()
        assert ok is False
        assert "拒绝标记" in msg

    def test_fail_refusal_marker_english(self, tmp_path):
        """代码包含英文拒绝标记时失败"""
        (tmp_path / "code" / "main.py").write_text("I cannot generate this code")
        ok, msg = SentryCheck.check_before_debugger()
        assert ok is False
        assert "拒绝标记" in msg


class TestCheckBeforeReviewer:
    """Reviewer 前置检查"""

    def test_ok_with_passed_debug(self, tmp_path):
        """Debugger 通过时可以进入评审"""
        from core.file_utils import save_meta
        save_meta({"verdict": "passed"}, tmp_path / "reports" / "test_result")

        ok, msg = SentryCheck.check_before_reviewer()
        assert ok is True

    def test_fail_no_test_result(self):
        """没有测试结果时失败"""
        ok, msg = SentryCheck.check_before_reviewer()
        assert ok is False
        assert "缺少" in msg

    def test_fail_debug_not_passed(self, tmp_path):
        """Debugger 未通过时不能进入评审"""
        from core.file_utils import save_meta
        save_meta({"verdict": "failed"}, tmp_path / "reports" / "test_result")

        ok, msg = SentryCheck.check_before_reviewer()
        assert ok is False
        assert "未通过" in msg


class TestDetectLoop:
    """死循环检测"""

    def test_no_loop(self):
        """正常状态不检测到循环"""
        detected, msg = SentryCheck.detect_loop()
        assert detected is False

    def test_loop_detected(self, tmp_path):
        """连续相同错误达到阈值时检测到循环"""
        StateManager.update(loop_detection={
            "consecutive_same_error": config.LOOP_DETECTION_THRESHOLD,
            "action_on_threshold": "pause_and_request_human_guidance"
        })
        detected, msg = SentryCheck.detect_loop()
        assert detected is True
        assert "连续" in msg

    def test_below_threshold(self, tmp_path):
        """低于阈值时不检测到循环"""
        StateManager.update(loop_detection={
            "consecutive_same_error": config.LOOP_DETECTION_THRESHOLD - 1,
            "action_on_threshold": "pause_and_request_human_guidance"
        })
        detected, msg = SentryCheck.detect_loop()
        assert detected is False
