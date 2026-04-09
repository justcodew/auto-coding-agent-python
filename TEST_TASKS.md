# Auto Coding Agent - 测试任务集（实战版）

> 从基础验证到复杂项目的分层测试任务，真正检验多智能体协作系统的能力边界

## 目录

1. [任务分层设计](#任务分层设计)
2. [L1：基础验证层](#l1基础验证层)
3. [L2：单模块复杂度层](#l2单模块复杂度层)
4. [L3：多模块协作层](#l3多模块协作层)
5. [L4：系统集成层](#l4系统集成层)
6. [L5：完整产品层](#l5完整产品层)
7. [评估标准](#评估标准)

---

## 任务分层设计

| 层级 | 名称 | 验证目标 | 任务数量 | 单任务预计轮次 |
|:---|:---|:---|:---|:---|
| L1 | 基础验证层 | 验证四角色基本协作 | 2 | 1 |
| L2 | 单模块复杂度层 | 验证复杂算法/业务逻辑 | 3 | 2-3 |
| L3 | 多模块协作层 | 验证模块间依赖和接口设计 | 3 | 3-5 |
| L4 | 系统集成层 | 验证外部依赖处理和完整流程 | 2 | 5-8 |
| L5 | 完整产品层 | 验证端到端产品交付能力 | 1 | 8+ |

---

## L1：基础验证层

快速验证系统基本可用，任务简单直接。

### Task 1.1：斐波那契数列

**描述**：

创建一个 Python 函数 `fibonacci(n)`，返回斐波那契数列的第 n 项。要求：处理 n < 0 的情况（抛出 ValueError）。

**预期轮次**：1

### Task 1.2：判断素数

**描述**：

创建一个 Python 函数 `is_prime(n)`，判断是否为素数。要求：使用 sqrt 优化，处理边界条件。

**预期轮次**：1

---

## L2：单模块复杂度层

验证系统处理复杂算法和业务逻辑的能力。

### Task 2.1：LRU 缓存实现

**描述**：

实现一个 LRU (Least Recently Used) 缓存类 `LRUCache`。

**要求**：

- 构造函数 `__init__(self, capacity: int)` 初始化缓存容量
- `get(key: str) -> Any`：获取 key 对应的值，不存在返回 None，同时将 key 标记为最近使用
- `put(key: str, value: Any) -> None`：插入或更新键值对，如果缓存已满，淘汰最久未使用的键
- 时间复杂度要求：get 和 put 都是 O(1)
- 使用 `collections.OrderedDict` 或自己实现双向链表+哈希表
- 包含完整的类型注解和文档字符串

**预期产出**：
- 单个 Python 文件 `lru_cache.py`
- 完整的类实现
- 包含测试示例的 `if __name__ == "__main__"`

**验证要点**：
- [ ] 是否正确实现 LRU 淘汰策略
- [ ] 时间复杂度是否满足 O(1)
- [ ] 边界条件：容量为0、重复插入、获取不存在的key
- [ ] 代码可读性和注释

**预期轮次**：2-3

---

### Task 2.2：表达式求值器

**描述**：

实现一个数学表达式求值器 `ExpressionEvaluator`。

**要求**：

- 支持四则运算：`+`、`-`、`*`、`/`
- 支持括号 `()`
- 支持空格分隔（自动忽略）
- 正确处理运算符优先级
- 处理除零错误（返回 None 或抛出异常，需文档说明）
- 处理无效表达式（返回 None 或抛出异常）

**示例**：

```
"2 + 3 * 4"   -> 14
"(2 + 3) * 4" -> 20
"10 / 0"      -> None
"2 + + 3"     -> None
```

**实现方式**：可以使用栈（调度场算法）或递归下降。

**预期产出**：
- 单个 Python 文件 `expr_eval.py`
- 完整的类或函数实现
- 健壮的错误处理

**验证要点**：
- [ ] 运算符优先级是否正确
- [ ] 括号是否正确处理
- [ ] 错误输入是否正确拒绝
- [ ] 算法选择是否合理（有文档说明）

**预期轮次**：2-4

---

### Task 2.3：文本差异对比器

**描述**：

实现一个文本差异对比工具 `TextDiff`。

**要求**：

- 提供函数 `diff(text1: str, text2: str) -> List[DiffOp]`
- `DiffOp` 是一个数据类，包含操作类型（`"equal"`, `"insert"`, `"delete"`, `"replace"`）和内容
- 实现基于 Myers 差分算法或简单的 LCS 算法
- 提供函数 `format_diff(diff: List[DiffOp]) -> str`，输出人类可读的差异报告
- 支持按行对比和按字符对比两种模式（通过参数控制）

**示例输出格式**：

```
  "hello world"  -> 不变
+ "hello python" -> 新增
~ "old text" -> "new text" -> 替换
```

**预期产出**：
- `text_diff.py`：核心算法
- `diff_formatter.py`：格式化输出
- 数据类定义

**验证要点**：
- [ ] 算法是否正确（对比标准库 difflib）
- [ ] 模块划分是否合理
- [ ] 格式化输出是否清晰
- [ ] 边界条件：空字符串、完全相同、完全不同

**预期轮次**：3-5

---

## L3：多模块协作层

验证系统处理多模块、多文件项目的能力。

### Task 3.1：简易任务队列系统

**描述**：

实现一个基于 Redis 或内存的异步任务队列系统。

**项目结构**：

```
task_queue/
├── __init__.py
├── broker.py        # 消息代理，负责任务的入队和出队
├── worker.py        # 工作进程，消费并执行任务
├── task.py          # 任务定义（数据类）
├── exceptions.py    # 自定义异常
└── example.py       # 使用示例
```

**功能要求**：

- 支持任务优先级（整数，越小优先级越高）
- 支持任务延迟执行（delay 参数，单位秒）
- 支持任务重试（max_retries 参数）
- 支持任务超时（timeout 参数）
- 工作进程支持并发处理多个任务（使用线程池）
- 提供装饰器 `@task` 用于注册任务函数

**使用示例**：

```python
from task_queue import TaskQueue, task

@task(max_retries=3, timeout=10)
def send_email(to: str, subject: str, body: str):
    # 发送邮件的逻辑
    pass

queue = TaskQueue(redis_url="redis://localhost")
queue.enqueue(send_email, to="user@example.com", subject="Hello", body="...")
queue.enqueue(send_email, to="admin@example.com", subject="Alert", body="...", priority=1, delay=30)

worker = Worker(queue)
worker.start()
```

如果不想依赖 Redis，可以实现内存版本（使用 `queue.PriorityQueue`）。

**预期产出**：
- 完整的包结构
- 5+ 个 Python 文件
- 可运行的示例
- 清晰的模块接口

**验证要点**：
- [ ] 模块间依赖是否清晰
- [ ] 接口设计是否合理
- [ ] 优先级队列是否正确实现
- [ ] 并发处理是否正确（线程安全）
- [ ] 错误处理是否完善
- [ ] 是否处理了 Redis 不可用的情况

**预期轮次**：4-6

---

### Task 3.2：Markdown 静态站点生成器

**描述**：

实现一个 Markdown 静态站点生成器，将 Markdown 文件转换为 HTML 网站。

**项目结构**：

```
ssg/
├── __init__.py
├── parser.py        # Markdown 解析（可使用 mistune 或 markdown 库）
├── renderer.py      # HTML 渲染（使用 Jinja2 模板）
├── scanner.py       # 文件扫描，发现所有 .md 文件
├── server.py        # 开发服务器（可选）
├── cli.py           # 命令行入口
├── templates/       # Jinja2 模板目录
│   ├── base.html
│   ├── post.html
│   └── index.html
└── example_site/    # 示例站点内容
```

**功能要求**：

- 扫描指定目录下的所有 `.md` 文件
- 支持 Front Matter（YAML 头部元数据：title, date, tags）
- 生成文章页面（post.html）
- 生成首页（index.html），按日期倒序列出所有文章
- 支持标签页面（按 tags 分类）
- 支持代码高亮（使用 Pygments）

**命令行接口**：

```bash
ssg build --source ./content --output ./public
ssg serve --port 8080
```

**技术要求**：

- 使用 `mistune` 或 `markdown` 库解析 Markdown
- 使用 `Jinja2` 渲染模板
- 使用 `PyYAML` 解析 Front Matter
- 可选：使用 `watchdog` 监听文件变化，自动重新构建

**预期产出**：
- 完整的包结构
- CLI 入口
- 模板文件
- 依赖清单（requirements.txt 或 pyproject.toml）

**验证要点**：
- [ ] Markdown 解析是否正确
- [ ] Front Matter 是否正确提取
- [ ] 模板渲染是否正确
- [ ] 文件路径处理是否正确（跨平台）
- [ ] 命令行参数解析是否正确
- [ ] 依赖是否正确声明

**预期轮次**：5-7

---

### Task 3.3：简易 ORM 框架

**描述**：

实现一个简易的 ORM（对象关系映射）框架，支持 SQLite。

**项目结构**：

```
mini_orm/
├── __init__.py
├── fields.py        # 字段类型定义（IntegerField, StringField, FloatField, BooleanField）
├── model.py         # Model 基类，元类实现
├── query.py         # QuerySet 查询集，支持链式调用
├── manager.py       # Manager 管理器
├── migrations.py    # 简单的迁移支持（可选）
└── connection.py    # 数据库连接管理
```

**功能要求**：

支持模型定义：

```python
class User(Model):
    name = StringField(max_length=100)
    age = IntegerField(default=0)
    email = StringField(unique=True)

    class Meta:
        table_name = "users"
```

支持 CRUD 操作：

```python
User.create(name="Alice", age=25)
User.get(id=1)
User.filter(age__gt=18).order_by("-age").limit(10)
user.update(age=26)
user.delete()
```

- 支持的查询操作符：`__eq`, `__gt`, `__gte`, `__lt`, `__lte`, `__contains`, `__startswith`
- 自动创建表结构（根据模型定义生成 CREATE TABLE）
- 支持基本的关系：ForeignKey（一对一、一对多）

**技术要求**：

- 使用 `sqlite3` 标准库
- 使用元类收集字段定义
- 参数化查询防止 SQL 注入
- 连接池管理

**预期产出**：
- 完整的包结构
- 核心 ORM 功能
- 使用示例

**验证要点**：
- [ ] 元类是否正确收集字段
- [ ] SQL 生成是否正确
- [ ] 参数化查询是否防止注入
- [ ] 查询链式调用是否流畅
- [ ] 关系映射是否正确

**预期轮次**：5-8

---

## L4：系统集成层

验证系统处理外部服务、复杂依赖和完整业务流程的能力。

### Task 4.1：文件解析与脑图生成系统

**描述**：

开发一个文件解析系统，接受用户的 PDF 文件输入，输出文件的脑图，用 XMind 格式输出。

**项目结构**：

```
mindmap_generator/
├── __init__.py
├── pdf_parser/
│   ├── __init__.py
│   ├── extractor.py     # PDF 文本提取
│   ├── structure.py     # 文档结构分析（标题层级）
│   └── keywords.py      # 关键词提取（可选）
├── mindmap/
│   ├── __init__.py
│   ├── builder.py       # 脑图节点构建
│   ├── xmind_writer.py  # XMind 格式输出
│   └── freemind_writer.py  # 可选：FreeMind 格式
├── ai_analyzer/
│   ├── __init__.py
│   └── summarizer.py    # 使用 LLM 总结段落（可选）
├── cli.py               # 命令行入口
├── web_api.py           # Web API（FastAPI）
├── templates/
│   └── upload.html      # 文件上传页面
└── requirements.txt
```

**技术栈**：

- PDF 解析：PyMuPDF (fitz) 或 pdfplumber
- 文档结构分析：基于字体大小、位置推断标题层级
- XMind 生成：xmindparser 库或手动生成 .xmind 文件（本质是 ZIP 包）
- Web 框架：FastAPI
- 可选：使用 LLM API 进行智能摘要

**功能要求**：

第一阶段 - 核心功能：

- 从 PDF 提取纯文本
- 分析文档结构：
  - 根据字体大小和样式识别标题层级（H1, H2, H3...）
  - 将正文内容归属到最近的标题下
- 生成脑图节点树
- 输出为 XMind 格式文件

第二阶段 - 增强功能：

- 对每个段落使用 LLM 生成一句话摘要作为节点内容
- 提取关键词作为子节点
- 支持多种输出格式（XMind, FreeMind, Markdown 大纲）

第三阶段 - 产品化：

- Web 界面：上传 PDF，下载脑图
- 异步处理：大文件后台处理，返回任务 ID 轮询
- 历史记录：保存已处理的文件

**XMind 文件格式说明**：

- .xmind 文件本质是一个 ZIP 压缩包
- 包含 `content.xml`（脑图结构）、`styles.xml`（样式）、`manifest.xml`
- 可以使用 xmindparser 库简化操作，或手动构建 XML

**API 设计**：

```python
# Web API
POST /upload          # 上传 PDF，返回 task_id
GET  /status/{id}     # 查询处理状态
GET  /download/{id}   # 下载生成的 XMind 文件

# CLI
python -m mindmap_generator input.pdf -o output.xmind
python -m mindmap_generator input.pdf --format freemind --use-llm
```

**测试用例**：

- 标准学术论文（有明确章节标题）
- 技术文档（多级标题）
- 无结构纯文本（需要 AI 分析）
- 扫描版 PDF（需要 OCR，作为可选功能）

**预期产出**：
- 完整的项目结构（10+ 文件）
- 可运行的 CLI 工具
- 可运行的 Web 服务
- 依赖清单
- 使用文档

**验证要点**：
- [ ] PDF 文本提取是否准确
- [ ] 标题层级识别是否合理
- [ ] 脑图结构是否正确
- [ ] XMind 文件是否可正常打开
- [ ] Web 上传流程是否完整
- [ ] 错误处理：损坏的 PDF、空文件、大文件
- [ ] 异步处理是否正确

**预期轮次**：8-12

**分步执行建议**：

这个任务较大，建议分阶段验证：

| 阶段 | 子任务 | 验证点 |
|:---|:---|:---|
| 4.1.1 | PDF 文本提取模块 | 使用 PyMuPDF 提取文本 |
| 4.1.2 | 文档结构分析模块 | 基于字体大小识别标题 |
| 4.1.3 | 脑图构建模块 | 生成节点树结构 |
| 4.1.4 | XMind 输出模块 | 生成可打开的 .xmind |
| 4.1.5 | CLI 整合 | 命令行完整流程 |
| 4.1.6 | Web API | FastAPI 上传下载 |
| 4.1.7 | 异步处理 | 后台任务队列 |
| 4.1.8 | LLM 摘要（可选） | 集成 AI 生成摘要 |

---

### Task 4.2：API 网关与限流器

**描述**：

实现一个轻量级 API 网关，包含限流、认证、路由转发功能。

**项目结构**：

```
api_gateway/
├── __init__.py
├── gateway.py        # 主网关服务
├── router.py         # 路由配置和转发
├── limiter.py        # 限流器实现
├── auth.py           # 认证模块（JWT）
├── config.py         # 配置管理
├── middleware.py     # 中间件
├── models.py         # 数据模型
└── example_config.yaml
```

**功能要求**：

- 反向代理：将请求转发到配置的后端服务

- 限流策略：
  - 固定窗口计数器
  - 滑动窗口（更精确）
  - 令牌桶算法
- 支持多种限流维度：按 IP、按用户、按 API 路径

- JWT 认证：验证 token，提取用户信息
- 配置热加载：修改配置文件无需重启

- 提供管理 API：

```
GET  /admin/stats        # 流量统计
POST /admin/ban/{ip}     # 封禁 IP
GET  /admin/health       # 健康检查
```

**预期产出**：
- 完整的项目结构
- 可运行的网关服务
- 配置文件示例
- 限流算法实现

**验证要点**：
- [ ] 反向代理是否正确转发请求
- [ ] 限流算法是否正确实现
- [ ] JWT 认证是否安全
- [ ] 配置热加载是否生效
- [ ] 管理 API 是否可用
- [ ] 并发场景下的线程安全

**预期轮次**：6-10

---

## L5：完整产品层

> 待补充：L5 层级任务设计为端到端完整产品交付，验证系统在真实产品级需求下的综合表现。

---

## 评估标准

> 待补充：跨层级通用评估维度（代码质量、架构合理性、测试覆盖、文档完善度等）。
