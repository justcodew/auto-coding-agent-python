auto-coding-agent-python/
├── .agent_workspace/              # Agent 工作区
│   ├── state.json                 # 全局状态机
│   ├── tasks/
│   │   ├── backlog.json           # 待办任务列表
│   │   └── current.json           # 当前执行的任务
│   ├── plans/                     # Planner 产出
│   ├── code/                      # Coder 产出
│   └── reports/                   # Debugger/Reviewer 产出
├── skills/
│   ├── __init__.py
│   ├── planner.py
│   ├── coder.py
│   ├── debugger.py
│   └── reviewer.py
├── core/
│   ├── __init__.py
│   ├── state_manager.py
│   ├── sentry_checks.py
│   ├── llm_client.py
│   └── file_utils.py
├── main.py                        # 主控脚本
├── config.py                      # 配置文件
└── requirements.txt