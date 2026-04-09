# Auto Coding Agent (Python 实现)

> 一个基于文件交互模式的多智能体协作编程系统 —— 让 AI 像软件开发团队一样工作

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 项目简介

本项目是对 [SamuelQZQ/auto-coding-agent-demo](https://github.com/SamuelQZQ/auto-coding-agent-demo) 的 Python 重构与设计升级。核心理念不变：**AI 已经能够编写绝大部分代码，程序员的核心价值正从亲手写代码转向如何高效地指挥、控制和审核 AI**。

与原项目相比，本实现的创新点在于：

- **多智能体协作架构**：将开发流程拆分为 Planner、Coder、Debugger、Reviewer 四个专职 Agent，各司其职
- **文件交互模式**：Agent 之间通过约定的文件（JSON、Markdown）进行通信，松耦合、易调试、可追溯
- **内置防御机制**：包含哨兵检查、死循环检测、决策日志等机制，防止 Token 浪费和方向偏离
- **纯 Python 实现**：无需 TypeScript/Node.js 环境，只需 Python 3.9+ 和 LLM API

## 系统架构

### 四角色协作模型

```
用户需求输入
       ↓
┌─────────────────┐
│ Planner 规划者   │
│ 分析需求拆解任务  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Coder 编码者     │←─────┐
│ 根据计划生成代码  │      │
└────────┬────────┘      │
         ↓               │
┌─────────────────┐      │
│ Debugger 调试者  │      │
│ 审查代码找错误    │      │
└────────┬────────┘      │
         ↓               │
     ┌───┴───┐           │
     ↓       ↓           │
  测试通过  测试失败──────┘
     ↓
┌─────────────────┐
│ Reviewer 评审者  │
│ 最终代码审查     │
└────────┬────────┘
         ↓
     ┌───┴───┐
     ↓       ↓
  批准合并  需要修改 → 返回 Coder
     ↓
   完成
```

### 文件交互设计

所有 Agent 通过 `.agent_workspace/` 目录下的文件进行通信：

```
.agent_workspace/
├── state.json                 # 全局状态机
├── tasks/
│   └── current.json           # 当前任务
├── plans/
│   ├── plan_v1.md             # 开发计划
│   └── plan_v1.meta.json      # 计划元数据
├── code/
│   ├── main.py                # 生成的代码
│   └── coder_v1.meta.json     # 编码元数据
└── reports/
    ├── test_result.md          # 测试报告
    ├── test_result.meta.json   # 测试元数据
    ├── review.md               # 评审报告
    └── review.meta.json        # 评审元数据
```

## 防御机制设计

| 风险类型 | 防御机制 | 实现方式 |
|:---|:---|:---|
| 目标漂移 | 需求锚点 | state.json 锁定原始需求 |
| 死循环 | 错误指纹检测 | 连续相同错误触发警告 |
| 上下文断裂 | 决策日志 | 每个 Agent 输出 meta.json |
| Token 浪费 | 哨兵检查 | 调用 LLM 前检查输入完整性 |

## 快速开始

### 环境要求

- Python 3.9+
- LLM API Key（支持 OpenAI 兼容接口）

### 安装

```bash
git clone https://github.com/yourusername/auto-coding-agent-python.git
cd auto-coding-agent-python
pip install -r requirements.txt
```

### 配置

创建 `.env` 文件：

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

### 使用

```bash
# 初始化任务
python main.py --init "创建一个 Python 函数，计算斐波那契数列的第 n 项"

# 运行自动化流程（单步）
python main.py --run --cycles 1

# 连续运行
python main.py --run --cycles 10 --delay 3

# 查看状态
python main.py --status

# 重置工作区
python main.py --reset
```

## 项目结构

```
auto-coding-agent-python/
├── .agent_workspace/          # Agent 工作区（运行时创建）
├── core/                      # 核心模块
│   ├── llm_client.py          # LLM 调用封装
│   ├── state_manager.py       # 状态管理
│   ├── file_utils.py          # 文件解析工具
│   └── sentry_checks.py       # 哨兵检查器
├── skills/                    # Agent Skill 实现
│   ├── planner.py
│   ├── coder.py
│   ├── debugger.py
│   └── reviewer.py
├── main.py                    # 主控脚本
├── config.py                  # 配置文件
└── requirements.txt           # 依赖清单
```

## 配置参数

| 参数 | 位置 | 默认值 | 说明 |
|:---|:---|:---|:---|
| MAX_RETRIES | config.py | 3 | 最大重试次数 |
| LOOP_DETECTION_THRESHOLD | config.py | 2 | 死循环检测阈值 |
| LLM_MODEL | .env | gpt-4 | 使用的模型 |
| --cycles | 命令行 | 10 | 最大运行周期数 |
| --delay | 命令行 | 2 | 周期间隔秒数 |

## Agent 角色说明

| 角色 | 输入 | 输出 | 职责 |
|:---|:---|:---|:---|
| Planner | tasks/current.json | plans/plan_v1.md | 分析需求，拆解任务 |
| Coder | plans/plan_v1.md | code/*.py | 根据计划生成代码 |
| Debugger | code/*.py | reports/test_result.md | 审查代码，发现错误 |
| Reviewer | code/* + 原始需求 | reports/review.md | 最终评审，对照需求 |

## 与 TypeScript 原版的对比

| 维度 | TypeScript 原版 | Python 重构版 |
|:---|:---|:---|
| 架构模式 | 单一 Agent 循环 | 多智能体协作 |
| 通信方式 | Claude Code 内部状态 | 文件系统，完全透明 |
| 防御机制 | 依赖 Claude | 哨兵检查 + 死循环检测 |
| 运行环境 | Node.js + Claude Code | Python + 任意 LLM |

## 许可证

MIT License

## 致谢

- 原项目 [SamuelQZQ/auto-coding-agent-demo](https://github.com/SamuelQZQ/auto-coding-agent-demo)
- 多智能体架构参考 Microsoft Agent Framework

> **免责声明**：本项目所有代码和提示词均由 AI 辅助生成。运行前请自行审查，建议在隔离环境中运行。
