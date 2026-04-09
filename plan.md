# 测试计划 - auto-coding-agent-python

## 目标
对项目所有模块进行单元测试，发现并修复代码问题，输出测试报告。

## 测试范围

### 1. core/file_utils.py（最高优先级）
- `parse_meta_from_response()`: META标签解析、JSON修复、降级处理
- `parse_code_files()`: 4级降级策略，每种格式都要覆盖
- `save_file()` / `read_file()`: 文件I/O，自动创建目录
- `save_meta()` / `load_meta()`: 元数据文件读写

### 2. core/state_manager.py
- `load()` / `save()` / `update()`: 状态CRUD
- `append_decision_trail()`: 日志追加
- `get_current_task()` / `save_current_task()`: 任务管理
- 向后兼容：旧状态文件缺少新字段时的补全

### 3. core/sentry_checks.py
- `check_before_planner()`: 任务文件存在性和描述检查
- `check_before_coder()`: 计划文件、重试上限、周期上限检查
- `check_before_debugger()`: 代码文件存在性、拒绝标记检查
- `check_before_reviewer()`: 测试结果元数据检查
- `detect_loop()`: 连续相同错误检测

### 4. core/llm_client.py（Mock OpenAI）
- 延迟初始化、API Key检查
- 重试逻辑（指数退避）
- usage_stats统计

### 5. skills/planner.py, coder.py, debugger.py, reviewer.py（Mock LLM）
- 各Skill的输入组装、输出解析、状态转换是否正确

### 6. main.py（Mock LLM + StateManager）
- CLI参数解析
- 单周期执行流程
- 连续运行流程

## 测试方法
- 使用 `pytest` 框架
- Mock LLM 调用（不需要真实API Key）
- 临时目录隔离工作区
- 每个测试用例前后清理状态

## 发现问题后的流程
1. 记录到 plan.md 的"问题清单"
2. 修复代码
3. 重新运行测试验证
4. 最终输出 TEST_REPORT.md
