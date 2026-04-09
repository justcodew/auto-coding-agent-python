import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
WORKSPACE_DIR = PROJECT_ROOT / ".agent_workspace"

# LLM 配置 - 支持 OpenAI 兼容的 API
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4")

# Agent 配置
MAX_RETRIES = 3
LOOP_DETECTION_THRESHOLD = 2  # 连续相同错误触发暂停的次数
TOTAL_CYCLE_LIMIT = 10  # 总编码周期上限（防止 Reviewer 驳回导致的无限循环）


def init_workspace_dirs():
    """初始化工作区目录结构"""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    for subdir in ["tasks", "plans", "code", "reports"]:
        (WORKSPACE_DIR / subdir).mkdir(exist_ok=True)


# 自动初始化（保持向后兼容）
init_workspace_dirs()
