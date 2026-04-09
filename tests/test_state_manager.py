"""测试 core/state_manager.py"""
import json
import pytest
from pathlib import Path
from core.state_manager import StateManager
import config


class TestStateManagerLoad:
    """测试状态加载"""

    def test_load_creates_default_if_missing(self, tmp_path, monkeypatch):
        """文件不存在时创建默认状态"""
        monkeypatch.setattr(config, "WORKSPACE_DIR", tmp_path)
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        state = StateManager.load()
        assert state["current_phase"] == "planning"
        assert state["retry_count"] == 0
        assert state["total_cycles"] == 0
        assert state["version"] == 1
        assert (tmp_path / "state.json").exists()

    def test_load_existing_state(self, tmp_path, monkeypatch):
        """加载已有状态文件"""
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        saved = {"current_phase": "coding", "retry_count": 2, "version": 1}
        with open(tmp_path / "state.json", "w") as f:
            json.dump(saved, f)

        state = StateManager.load()
        assert state["current_phase"] == "coding"
        assert state["retry_count"] == 2

    def test_load_backward_compat(self, tmp_path, monkeypatch):
        """旧状态文件缺少新字段时自动补全"""
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        # 模拟旧版本状态（缺少 total_cycles, review_reject_count 等新字段）
        old_state = {"current_phase": "debugging", "retry_count": 1, "version": 1}
        with open(tmp_path / "state.json", "w") as f:
            json.dump(old_state, f)

        state = StateManager.load()
        assert state["current_phase"] == "debugging"
        assert state["total_cycles"] == 0  # 补全默认值
        assert state["review_reject_count"] == 0
        assert "loop_detection" in state


class TestStateManagerSave:
    """测试状态保存"""

    def test_save_and_reload(self, tmp_path, monkeypatch):
        """保存后重新加载应一致"""
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        state = StateManager.DEFAULT_STATE.copy()
        state["current_phase"] = "reviewing"
        StateManager.save(state)

        loaded = StateManager.load()
        assert loaded["current_phase"] == "reviewing"

    def test_save_preserves_chinese(self, tmp_path, monkeypatch):
        """中文内容保存正确"""
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        StateManager.save({"original_requirement": "实现一个 LRU 缓存"})
        loaded = StateManager.load()
        assert "LRU" in loaded["original_requirement"]


class TestStateManagerUpdate:
    """测试部分更新"""

    def test_update_partial_fields(self, tmp_path, monkeypatch):
        """只更新部分字段"""
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        StateManager.save(StateManager.DEFAULT_STATE.copy())
        StateManager.update(current_phase="coding", retry_count=1)

        state = StateManager.load()
        assert state["current_phase"] == "coding"
        assert state["retry_count"] == 1
        assert state["total_cycles"] == 0  # 未修改的字段保持不变


class TestDecisionTrail:
    """测试决策日志"""

    def test_append_trail(self, tmp_path, monkeypatch):
        """追加决策日志"""
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        StateManager.save(StateManager.DEFAULT_STATE.copy())
        StateManager.append_decision_trail({"agent": "Planner", "action": "plan_created"})
        StateManager.append_decision_trail({"agent": "Coder", "action": "code_generated"})

        state = StateManager.load()
        assert len(state["decision_trail"]) == 2
        assert state["decision_trail"][0]["agent"] == "Planner"
        assert state["decision_trail"][1]["agent"] == "Coder"
        # 时间戳自动添加
        assert "timestamp" in state["decision_trail"][0]


class TestTaskManagement:
    """测试任务管理"""

    def test_save_and_get_task(self, tmp_path, monkeypatch):
        """保存和获取当前任务"""
        monkeypatch.setattr(config, "WORKSPACE_DIR", tmp_path)
        monkeypatch.setattr(StateManager, "STATE_FILE", tmp_path / "state.json")

        task = {"id": "task_001", "description": "实现斐波那契", "status": "pending"}
        StateManager.save_current_task(task)

        loaded = StateManager.get_current_task()
        assert loaded is not None
        assert loaded["id"] == "task_001"

    def test_get_task_when_missing(self, tmp_path, monkeypatch):
        """没有任务文件时返回 None"""
        monkeypatch.setattr(config, "WORKSPACE_DIR", tmp_path)
        assert StateManager.get_current_task() is None
