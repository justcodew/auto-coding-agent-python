"""测试 skills/ - 各 Skill 的输入组装和状态转换"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.state_manager import StateManager
from core.file_utils import save_file, save_meta
import config


@pytest.fixture(autouse=True)
def setup_workspace(tmp_path, monkeypatch):
    """每个测试前设置临时工作区"""
    monkeypatch.setattr(config, "WORKSPACE_DIR", tmp_path)
    monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

    for subdir in ["tasks", "plans", "code", "reports"]:
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)

    StateManager.save(StateManager.DEFAULT_STATE.copy())


class TestPlannerSkill:
    """测试 Planner Skill"""

    def test_planner_saves_plan_and_transitions(self, tmp_path):
        """Planner 应保存计划文件并转换到 coding 阶段"""
        # 设置任务
        StateManager.save_current_task({"id": "1", "description": "写一个函数"})

        mock_response = """# 开发计划

## 任务理解
实现一个函数

[META_START]
{"agent": "Planner", "key_interpretation": "理解了", "assumptions": [], "potential_risks": [], "next_step_hint": "注意边界"}
[META_END]"""

        with patch("skills.planner.llm_client") as mock_llm:
            mock_llm.chat.return_value = mock_response
            from skills.planner import run_planner
            run_planner()

        # 验证计划文件
        assert (tmp_path / "plans" / "plan_v1.md").exists()
        assert (tmp_path / "plans" / "plan_v1.meta.json").exists()

        # 验证状态转换
        state = StateManager.load()
        assert state["current_phase"] == "coding"
        assert state["retry_count"] == 0  # Planner 重置 retry_count

    def test_planner_without_meta(self, tmp_path):
        """Planner 没有输出 meta 时不崩溃"""
        StateManager.save_current_task({"id": "1", "description": "写函数"})

        with patch("skills.planner.llm_client") as mock_llm:
            mock_llm.chat.return_value = "简单的计划文本，没有 meta"
            from skills.planner import run_planner
            run_planner()

        state = StateManager.load()
        assert state["current_phase"] == "coding"


class TestCoderSkill:
    """测试 Coder Skill"""

    def test_coder_saves_code_and_transitions(self, tmp_path):
        """Coder 应保存代码并转换到 debugging 阶段"""
        # 准备前置状态
        StateManager.update(current_phase="coding")
        save_file(tmp_path / "plans" / "plan_v1.md", "计划内容")

        mock_response = """--- 文件路径: main.py ---
def hello():
    print("hello")
--- 文件结束 ---

[META_START]
{"agent": "Coder", "changes_summary": "创建了 main.py", "addressed_feedback": "N/A"}
[META_END]"""

        with patch("skills.coder.llm_client") as mock_llm:
            mock_llm.chat.return_value = mock_response
            from skills.coder import run_coder
            run_coder()

        # 验证代码文件
        assert (tmp_path / "main.py").exists()

        # 验证状态转换
        state = StateManager.load()
        assert state["current_phase"] == "debugging"
        assert state["total_cycles"] == 1

    def test_coder_increments_total_cycles(self, tmp_path):
        """Coder 应递增 total_cycles"""
        StateManager.update(current_phase="coding", total_cycles=3)
        save_file(tmp_path / "plans" / "plan_v1.md", "计划")

        with patch("skills.coder.llm_client") as mock_llm:
            mock_llm.chat.return_value = "--- 文件路径: a.py ---\nx=1\n--- 文件结束 ---"
            from skills.coder import run_coder
            run_coder()

        state = StateManager.load()
        assert state["total_cycles"] == 4


class TestDebuggerSkill:
    """测试 Debugger Skill"""

    def test_debugger_passed_transitions_to_reviewing(self, tmp_path):
        """Debugger 通过时转换到 reviewing"""
        StateManager.update(current_phase="debugging")
        save_file(tmp_path / "plans" / "plan_v1.md", "计划")
        save_file(tmp_path / "code" / "main.py", "print('hello')")

        mock_response = """# 测试报告

## 测试结论：通过

[META_START]
{"agent": "Debugger", "verdict": "passed"}
[META_END]"""

        with patch("skills.debugger.llm_client") as mock_llm:
            mock_llm.chat.return_value = mock_response
            from skills.debugger import run_debugger
            run_debugger()

        state = StateManager.load()
        assert state["current_phase"] == "reviewing"
        assert state["last_error_signature"] is None

    def test_debugger_failed_transitions_to_coding(self, tmp_path):
        """Debugger 失败时转换到 coding 并递增 retry_count"""
        StateManager.update(current_phase="debugging", retry_count=0)
        save_file(tmp_path / "plans" / "plan_v1.md", "计划")
        save_file(tmp_path / "code" / "main.py", "bad code")

        mock_response = """# 测试报告

## 测试结论：失败

[META_START]
{"agent": "Debugger", "verdict": "failed", "error_signature": "SyntaxError", "failure_category": "语法错误"}
[META_END]"""

        with patch("skills.debugger.llm_client") as mock_llm:
            mock_llm.chat.return_value = mock_response
            from skills.debugger import run_debugger
            run_debugger()

        state = StateManager.load()
        assert state["current_phase"] == "coding"
        assert state["retry_count"] == 1

    def test_debugger_error_signature_generation(self, tmp_path):
        """错误签名应基于 MD5 生成"""
        from skills.debugger import generate_error_signature

        sig1 = generate_error_signature("TypeError on line 15")
        sig2 = generate_error_signature("TypeError on line 15")
        sig3 = generate_error_signature("SyntaxError on line 20")

        assert sig1 == sig2  # 相同输入产生相同签名
        assert sig1 != sig3  # 不同输入产生不同签名
        assert len(sig1) == 16

    def test_debugger_empty_error_returns_na(self):
        """空错误描述返回 N/A"""
        from skills.debugger import generate_error_signature
        assert generate_error_signature("") == "N/A"


class TestReviewerSkill:
    """测试 Reviewer Skill"""

    def test_reviewer_approved_transitions_to_completed(self, tmp_path):
        """Reviewer 批准时转换到 completed"""
        StateManager.update(current_phase="reviewing")
        StateManager.save_current_task({"id": "1", "description": "任务"})
        save_file(tmp_path / "plans" / "plan_v1.md", "计划")
        save_file(tmp_path / "code" / "main.py", "code")
        save_meta({"verdict": "passed"}, tmp_path / "reports" / "test_result")

        mock_response = """# 评审报告

## 最终结论：批准合并

[META_START]
{"agent": "Reviewer", "final_decision": "approved", "requirement_compliance": "fully"}
[META_END]"""

        with patch("skills.reviewer.llm_client") as mock_llm:
            mock_llm.chat.return_value = mock_response
            from skills.reviewer import run_reviewer
            run_reviewer()

        state = StateManager.load()
        assert state["current_phase"] == "completed"

    def test_reviewer_rejected_back_to_coding(self, tmp_path):
        """Reviewer 驳回时回到 coding"""
        StateManager.update(current_phase="reviewing", retry_count=1)
        StateManager.save_current_task({"id": "1", "description": "任务"})
        save_file(tmp_path / "plans" / "plan_v1.md", "计划")
        save_file(tmp_path / "code" / "main.py", "code")
        save_meta({"verdict": "passed"}, tmp_path / "reports" / "test_result")

        mock_response = """# 评审报告

## 最终结论：需要修改

[META_START]
{"agent": "Reviewer", "final_decision": "changes_requested", "requirement_compliance": "partially"}
[META_END]"""

        with patch("skills.reviewer.llm_client") as mock_llm:
            mock_llm.chat.return_value = mock_response
            from skills.reviewer import run_reviewer
            run_reviewer()

        state = StateManager.load()
        assert state["current_phase"] == "coding"
        assert state["review_reject_count"] == 1
        # 不重置 retry_count
        assert state["retry_count"] == 1

    def test_reviewer_increments_reject_count(self, tmp_path):
        """多次驳回应累积 reject_count"""
        StateManager.update(
            current_phase="reviewing",
            retry_count=2,
            review_reject_count=1
        )
        StateManager.save_current_task({"id": "1", "description": "任务"})
        save_file(tmp_path / "plans" / "plan_v1.md", "计划")
        save_file(tmp_path / "code" / "main.py", "code")
        save_meta({"verdict": "passed"}, tmp_path / "reports" / "test_result")

        mock_response = """# 评审报告

[META_START]
{"agent": "Reviewer", "final_decision": "changes_requested"}
[META_END]"""

        with patch("skills.reviewer.llm_client") as mock_llm:
            mock_llm.chat.return_value = mock_response
            from skills.reviewer import run_reviewer
            run_reviewer()

        state = StateManager.load()
        assert state["review_reject_count"] == 2
