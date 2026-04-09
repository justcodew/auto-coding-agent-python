"""测试 main.py - CLI 和流程控制"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.state_manager import StateManager
import config


@pytest.fixture(autouse=True)
def setup_workspace(tmp_path, monkeypatch):
    """每个测试前设置临时工作区"""
    monkeypatch.setattr(config, "WORKSPACE_DIR", tmp_path)
    monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

    for subdir in ["tasks", "plans", "code", "reports"]:
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)


class TestInitWorkspace:
    """测试工作区初始化"""

    def test_init_creates_state_and_task(self, tmp_path, monkeypatch):
        """初始化应创建状态文件和任务文件"""
        monkeypatch.setattr(config, "WORKSPACE_DIR", tmp_path)
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        from main import init_workspace
        init_workspace("实现一个 LRU 缓存")

        # 验证状态
        state = StateManager.load()
        assert state["current_phase"] == "planning"
        assert state["original_requirement"] == "实现一个 LRU 缓存"
        assert state["retry_count"] == 0

        # 验证任务
        task = StateManager.get_current_task()
        assert task is not None
        assert task["description"] == "实现一个 LRU 缓存"


class TestRunSingleCycle:
    """测试单周期执行"""

    def test_cycle_completed_state(self, tmp_path):
        """已完成状态应返回 False"""
        StateManager.save({"current_phase": "completed", "version": 1})

        from main import run_single_cycle
        assert run_single_cycle() is False

    def test_cycle_unknown_phase(self, tmp_path):
        """未知阶段应返回 False"""
        StateManager.save({"current_phase": "unknown_phase", "version": 1})

        from main import run_single_cycle
        assert run_single_cycle() is False

    def test_cycle_planning_phase(self, tmp_path):
        """planning 阶段执行 Planner"""
        StateManager.save(StateManager.DEFAULT_STATE.copy())
        StateManager.save_current_task({"id": "1", "description": "任务"})

        with patch("skills.planner.llm_client") as mock_llm:
            mock_llm.chat.return_value = "计划内容"
            from main import run_single_cycle
            result = run_single_cycle()

        assert result is True
        state = StateManager.load()
        assert state["current_phase"] == "coding"

    def test_cycle_sentry_fail(self, tmp_path):
        """哨兵检查失败时不执行"""
        StateManager.save(StateManager.DEFAULT_STATE.copy())
        # 没有任务文件 → planner 前置检查失败

        from main import run_single_cycle
        result = run_single_cycle()
        assert result is False

    def test_loop_detected_stops_cycle(self, tmp_path):
        """检测到死循环应停止"""
        StateManager.save({
            "current_phase": "planning",
            "version": 1,
            "loop_detection": {
                "consecutive_same_error": config.LOOP_DETECTION_THRESHOLD,
                "action_on_threshold": "pause"
            }
        })

        from main import run_single_cycle
        result = run_single_cycle()
        assert result is False
