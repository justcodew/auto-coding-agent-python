import json
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import config


class StateManager:
    STATE_FILE = config.WORKSPACE_DIR / "state.json"

    DEFAULT_STATE = {
        "current_phase": "planning",
        "current_task_id": None,
        "original_requirement": "",
        "retry_count": 0,
        "max_retries": config.MAX_RETRIES,
        "total_cycles": 0,
        "review_reject_count": 0,
        "last_error_signature": None,
        "loop_detection": {
            "consecutive_same_error": 0,
            "action_on_threshold": "pause_and_request_human_guidance"
        },
        "decision_trail": [],
        "version": 1
    }

    @classmethod
    def load(cls) -> dict:
        """加载状态，如果文件不存在则创建默认状态"""
        if not cls.STATE_FILE.exists():
            cls.save(cls.DEFAULT_STATE)
            return cls.DEFAULT_STATE.copy()

        with open(cls.STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

        # 补充新字段（向后兼容旧状态文件）
        for key, value in cls.DEFAULT_STATE.items():
            state.setdefault(key, value if not isinstance(value, dict) else value.copy())

        return state

    @classmethod
    def save(cls, state: dict):
        """保存状态"""
        with open(cls.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    @classmethod
    def update(cls, **kwargs):
        """更新状态的部分字段"""
        state = cls.load()
        state.update(kwargs)
        cls.save(state)

    @classmethod
    def append_decision_trail(cls, entry: dict):
        """追加决策日志"""
        state = cls.load()
        entry["timestamp"] = datetime.now().isoformat()
        state.setdefault("decision_trail", []).append(entry)
        cls.save(state)

    @classmethod
    def get_current_task(cls) -> Optional[dict]:
        """获取当前任务"""
        task_file = config.WORKSPACE_DIR / "tasks" / "current.json"
        if task_file.exists():
            with open(task_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    @classmethod
    def save_current_task(cls, task: dict):
        """保存当前任务"""
        task_file = config.WORKSPACE_DIR / "tasks" / "current.json"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
