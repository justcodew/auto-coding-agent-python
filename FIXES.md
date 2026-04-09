# Auto Coding Agent - 问题追踪与修复记录

> 代码审查发现的 14 个问题，按严重程度分类，含修复方案与状态

## 严重问题

### Issue #1: Reviewer 驳回绕过重试上限，可无限循环

- **严重程度**: 严重
- **位置**: `skills/reviewer.py:80`
- **现象**: Reviewer 驳回时 `retry_count=0` 被重置，系统可在 Coder → Debugger → Reviewer → Coder 之间无限循环，MAX_RETRIES 形同虚设
- **修复**:
  - 不再重置 `retry_count`，改为递增 `review_reject_count`
  - 在 `state_manager.py` 中新增 `total_cycles` 计数器
  - 在 `config.py` 中新增 `TOTAL_CYCLE_LIMIT = 10` 硬上限
  - 在 `sentry_checks.py` 的 `check_before_coder` 中检查 `total_cycles` 上限
- **状态**: ✅ 已修复

### Issue #2: Reviewer 的反馈没有传递给 Coder

- **严重程度**: 严重
- **位置**: `skills/coder.py:19-29`
- **现象**: Coder 的 prompt 只读取 Debugger 的反馈，Review 报告完全没喂给 Coder，Reviewer 驳回后等于白审
- **修复**: 在 `coder.py` 中新增读取 `reports/review.md` 和 `review.meta.json` 的逻辑，将 Reviewer 反馈作为独立的上下文段落传入 prompt
- **状态**: ✅ 已修复

### Issue #3: LLM 调用无错误处理

- **严重程度**: 严重
- **位置**: `core/llm_client.py:12-24`
- **现象**: `chat()` 裸调 API，网络超时、限流、Key 错误直接崩溃
- **修复**:
  - 添加指数退避重试（默认 3 次）
  - 延迟初始化 OpenAI 客户端（避免空 Key 时静默创建）
  - 添加 API Key 为空的明确报错
- **状态**: ✅ 已修复

### Issue #4: 代码文件解析极度脆弱

- **严重程度**: 严重
- **位置**: `core/file_utils.py:24-36`
- **现象**: `parse_code_files` 只支持一种严格格式 `--- 文件路径: X ---`，LLM 稍有偏差就解析不到任何文件
- **修复**: 实现 4 级降级策略：
  1. 原始格式（宽松匹配，允许空格变化）
  2. Markdown 代码块 + 文件路径注释
  3. 文件名标题 + Markdown 代码块
  4. 提取所有 ` ```python ` 代码块（最后手段）
- **状态**: ✅ 已修复

### Issue #5: loop_detection 状态被部分覆盖

- **严重程度**: 严重
- **位置**: `skills/debugger.py:104-109`
- **现象**: 更新 `loop_detection` 时只写了 `{"consecutive_same_error": n}`，丢失原有的 `action_on_threshold` 等字段
- **修复**: 先读取现有 `loop_detection` 字典，再合并更新，保留已有字段
- **状态**: ✅ 已修复

---

## 设计缺陷

### Issue #6: generate_error_signature 定义但从未使用

- **严重程度**: 中等
- **位置**: `skills/debugger.py:10-15`
- **现象**: 函数写好了但 error_signature 完全交给 LLM 生成，格式不可控，死循环检测可靠性存疑
- **修复**: 使用程序化 `generate_error_signature()` 生成确定性指纹，基于测试报告内容而非 LLM 自述
- **状态**: ✅ 已修复

### Issue #7: 文件路径全部硬编码为 plan_v1.md

- **严重程度**: 中等
- **位置**: 所有 skill 文件
- **现象**: 不支持多版本计划，重新规划时旧计划被覆盖
- **修复**: 当前版本标记为已知限制。未来可引入 `plan_version` 字段，在 state.json 中追踪计划版本号
- **状态**: ⏳ 记录为未来改进

### Issue #8: code_dir.glob("*.py") 只搜一层

- **严重程度**: 中等
- **位置**: `skills/debugger.py:30`, `skills/coder.py:34`, `skills/reviewer.py:21`, `core/sentry_checks.py:41`
- **现象**: 生成的代码如果创建了子目录结构，`*.py` glob 找不到嵌套文件
- **修复**: 全部改为 `rglob("*.py")`，并使用 `relative_to()` 显示相对路径
- **状态**: ✅ 已修复

### Issue #9: meta 解析失败默认 verdict 为 failed

- **严重程度**: 中等
- **位置**: `skills/debugger.py:82-83`, `skills/reviewer.py:74`
- **现象**: 当 `[META_START]` 解析失败时默认 `failed` / `changes_requested`，可能触发不必要的重试
- **修复**:
  - 在 `file_utils.py` 中添加 JSON 修复逻辑（处理尾随逗号等常见问题）
  - 在 `debugger.py` 和 `reviewer.py` 中，meta 解析失败时从文本内容推断判定结果并输出警告
- **状态**: ✅ 已修复

---

## 工程问题

### Issue #10: config.py 导入时有副作用

- **严重程度**: 低
- **位置**: `config.py:21-25`
- **现象**: import config 就创建目录结构，影响测试
- **修复**: 将目录创建包装为 `init_workspace_dirs()` 函数，保留模块级自动调用以兼容现有代码
- **状态**: ✅ 已修复

### Issue #11: --reset 无确认直接删除

- **严重程度**: 低
- **位置**: `main.py:189-193`
- **现象**: `shutil.rmtree` 直接删除整个工作区，误操作风险高
- **修复**: 添加 `input()` 确认提示，非 `y` 则取消
- **状态**: ✅ 已修复

### Issue #12: 缺少 .gitignore

- **严重程度**: 低
- **位置**: 项目根目录
- **现象**: `.env`（含 API Key）和 `.agent_workspace/` 可能被误提交
- **修复**: 创建 `.gitignore`，排除 `.env`、`.agent_workspace/`、`__pycache__/` 等
- **状态**: ✅ 已修复

### Issue #13: 无 Token 用量追踪

- **严重程度**: 低
- **位置**: `core/llm_client.py`
- **现象**: 无 API 调用次数和 Token 消耗记录
- **修复**: 在 LLMClient 中添加 `usage_stats` 属性，追踪调用次数和 Token 用量，运行结束时打印统计
- **状态**: ✅ 已修复

### Issue #14: LLMClient 模块级实例化

- **严重程度**: 低
- **位置**: `core/llm_client.py:27`
- **现象**: API Key 为空时客户端静默创建成功，直到调用时才报错，难以排查
- **修复**: 改为延迟初始化，在首次调用 `chat()` 时才创建 OpenAI 客户端，并在此时检查 API Key
- **状态**: ✅ 已修复

---

## 未修复项（未来改进）

| 编号 | 问题 | 原因 |
|:---|:---|:---|
| #7 | plan_v1.md 硬编码 | 需要设计计划版本管理机制，影响面大，建议单独迭代 |
| - | 无并行 Agent 执行 | 当前架构为单任务线性执行，并行需要重构为事件驱动 |
| - | 无真实代码运行测试 | Debugger 仅做静态分析，需要 Docker 沙箱支持 |

## 修改文件清单

| 文件 | 修改内容 |
|:---|:---|
| `FIXES.md` | 新增 - 本文件 |
| `.gitignore` | 新增 |
| `core/llm_client.py` | 延迟初始化、重试机制、Token 追踪 |
| `core/file_utils.py` | 多策略代码解析、JSON 修复 |
| `config.py` | 新增 TOTAL_CYCLE_LIMIT、init_workspace_dirs() |
| `core/state_manager.py` | 新增 total_cycles、review_reject_count、向后兼容 |
| `core/sentry_checks.py` | 新增 total_cycles 检查、rglob |
| `skills/debugger.py` | loop_detection 合并修复、程序化指纹、rglob、文本推断 |
| `skills/coder.py` | Reviewer 反馈传递、rglob、total_cycles 递增 |
| `skills/reviewer.py` | 不重置 retry_count、review_reject_count、rglob |
| `main.py` | 重置确认、用量统计、状态展示增强 |
