# swat_skill 设计文档

## 1. 项目概述

### 1.1 背景

swat_skill 是一个 PostgreSQL 数据库智能诊断 CLI Agent，设计参考了 Claude Code 的交互方式。目标是让 DBA 和开发人员能够通过最简洁的交互方式，实现最优的数据库管理和诊断。

### 1.2 设计目标

- **简洁交互**：三种输入类型自动识别，无需切换模式
- **智能诊断**：LLM 多轮推理，自动采集证据，定位根因
- **丰富技能**：覆盖 PostgreSQL 主要诊断场景
- **美观输出**：表格、健康报告等格式化展示
- **易于扩展**：模块化设计，便于添加新技能

### 1.3 目标用户

- PostgreSQL DBA
- 后端开发人员
- 数据库运维人员
- 数据分析师

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          swat_skill Architecture                         │
│                                                                         │
│  ┌─────────────────┐                                                   │
│  │    CLI Layer    │                                                   │
│  │  (cli.py)       │                                                   │
│  │                 │                                                   │
│  │ - Prompt Loop   │                                                   │
│  │ - History       │                                                   │
│  │ - Completion    │                                                   │
│  └────────┬────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                   │
│  │  Dispatcher     │                                                   │
│  │  (router.py)    │                                                   │
│  │                 │                                                   │
│  │ - Input Parse   │                                                   │
│  │ - Type Detect   │                                                   │
│  │ - Route Handler │                                                   │
│  └────────┬────────┘                                                   │
│           │                                                             │
│     ┌─────┴─────┬───────────┐                                          │
│     ▼           ▼           ▼                                          │
│  ┌─────┐    ┌─────┐    ┌─────┐                                         │
│  │Skill│    │ SQL │    │ LLM │                                         │
│  │Exec │    │Exec │    │Agent│                                         │
│  └─────┘    └─────┘    └─────┘                                         │
│     │           │           │                                          │
│     └─────┬─────┴─────┬─────┘                                          │
│           │           │                                                │
│           ▼           ▼                                                │
│  ┌─────────────────┐  ┌─────────────────┐                              │
│  │ Database Layer  │  │  LLM Tools      │                              │
│  │ (connection.py) │  │  (tools.py)     │                              │
│  │                 │  │                 │                              │
│  │ - Connection    │  │ - Function      │                              │
│  │ - Query Exec    │  │   Calling       │                              │
│  │ - Pool Mgmt     │  │ - Evidence      │                              │
│  └────────┬────────┘  │   Collection    │                              │
│           │           └────────┬────────┘                              │
│           │                    │                                        │
│           └──────┬─────────────┘                                        │
│                  ▼                                                      │
│  ┌─────────────────────────────────────────┐                           │
│  │            PostgreSQL                   │                           │
│  │                                         │                           │
│  │  pg_stat_activity                       │                           │
│  │  pg_locks                               │                           │
│  │  pg_stat_database                       │                           │
│  │  pg_stat_statements                     │                           │
│  │  ...                                    │                           │
│  └─────────────────────────────────────────┘                           │
│                                                                         │
│  ┌─────────────────┐                                                   │
│  │   Formatter     │                                                   │
│  │  (formatter.py) │                                                   │
│  │                 │                                                   │
│  │ - Table Render  │                                                   │
│  │ - Health Report │                                                   │
│  │ - Color/Style   │                                                   │
│  └─────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| CLI Layer | 用户交互、命令历史、自动补全 | `cli.py` |
| Dispatcher | 输入分类、路由分发 | `dispatcher/router.py` |
| Skills | 内置诊断技能执行 | `skills/*.py` |
| Database Layer | PostgreSQL 连接和查询执行 | `database/connection.py`, `database/queries.py` |
| LLM Agent | 多轮推理、证据采集 | `llm/agent.py`, `llm/tools.py` |
| Formatter | 输出格式化、表格渲染 | `utils/formatter.py` |
| Config | 配置加载和保存 | `config.py` |

## 3. 核心设计

### 3.1 输入分发器

Dispatcher 是核心路由模块，负责识别用户输入类型并分发到对应处理器：

```python
def dispatch(input: str) -> Tuple[SkillResult, Optional[Skill]]:
    input = input.strip()
    
    if not input:
        return EmptyResult(), None
    
    # 1. 技能命令：以 / 开头
    if input.startswith('/'):
        return handle_skill(input)
    
    # 2. SQL 语句：以 SQL 关键字开头
    if is_sql_statement(input):
        return execute_sql(input)
    
    # 3. 自然语言：其他情况路由到 LLM
    return handle_natural_language(input)
```

**设计考量**：
- 简单规则，无需复杂 NLP
- 支持技能别名（如 `/active` → `/activesessions`）
- 技能参数解析（如 `/slowsql 500`）

### 3.2 技能系统

技能采用注册模式，所有技能在导入时自动注册：

```python
@register_skill
class HealthSkill(Skill):
    name = "health"
    description = "全维度健康体检"
    
    def execute(self, conn, args, formatter) -> SkillResult:
        # 执行健康检查 SQL，收集指标
        # 返回 SkillResult
```

**技能基类设计**：

```python
class Skill(ABC):
    name: str           # 技能名称
    description: str    # 技能描述  
    aliases: List[str]  # 技能别名
    
    @abstractmethod
    def execute(self, conn, args, formatter) -> SkillResult:
        pass
```

**QuerySkill 简化类**：

对于只需执行预定义 SQL 的技能，提供简化基类：

```python
class QuerySkill(Skill):
    query_name: str  # SQL 模板名称
    
    def execute(self, conn, args, formatter):
        sql = get_query(self.query_name)
        result = conn.execute(sql)
        return SkillResult(success=result.success, data=result.rows)
```

### 3.3 PostgreSQL 连接管理

使用 psycopg 3.x 作为 PostgreSQL 驱动：

```python
class ConnectionManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection: Optional[psycopg.Connection] = None
    
    def connect(self) -> None:
        conn_info = self.config.get_connection_info()
        self._connection = psycopg.connect(**conn_info, row_factory=dict_row)
    
    def execute(self, sql: str, params=None) -> QueryResult:
        # 执行 SQL，返回字典列表格式的结果
```

**设计考量**：
- 使用 dict_row factory，返回字典而非元组
- 自动重连机制
- 查询执行时间统计

### 3.4 LLM Agent

LLM Agent 使用 Anthropic Claude API 的 Function Calling 功能：

```python
class LLMAgent:
    def diagnose(self, question: str) -> str:
        messages = [{"role": "user", "content": question}]
        
        for turn in range(self.max_turns):
            response = self.client.messages.create(
                model=self.model,
                tools=self.tools,
                messages=messages,
            )
            
            if response.stop_reason == "end_turn":
                return extract_text(response)
            
            # 处理 tool_use，执行工具，返回结果
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    # 添加 tool_result 到消息
```

**防幻觉机制**：
- System Prompt 约束：结论必须基于工具查询结果
- 只读查询安全检查
- 危险操作需要确认

**工具定义**：

```python
TOOLS = [
    {
        "name": "query_health",
        "description": "获取数据库健康状态",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "execute_sql",
        "description": "执行自定义 SQL 查询",
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string"}}
        }
    },
    # ...
]
```

### 3.5 输出格式化

使用 Rich 库渲染表格和报告：

```python
class Formatter:
    def format_table(self, data: List[Dict], columns: List[str]) -> Table:
        table = Table(box=box.ROUNDED)
        for col in columns:
            table.add_column(col)
        for row in data:
            table.add_row(*[str(row.get(col)) for col in columns])
        return table
    
    def format_health_report(self, items: List[HealthItem]) -> Panel:
        # 使用 ✓/⚠/✗ 符号
        # 分组展示各维度指标
```

## 4. PostgreSQL 诊断 SQL

### 4.1 数据源

主要使用 PostgreSQL 系统视图和函数：

| 数据源 | 用途 |
|--------|------|
| `pg_stat_activity` | 会话、连接、等待事件 |
| `pg_locks` | 锁信息 |
| `pg_stat_database` | 数据库级统计 |
| `pg_stat_user_tables` | 表级统计 |
| `pg_stat_statements` | SQL 执行统计（需扩展） |
| `pg_stat_wal` | WAL 统计 |
| `pg_stat_replication` | 复制状态 |
| `pg_settings` | 参数配置 |

### 4.2 查询模板

查询模板集中在 `queries.py`：

```python
QUERIES = {
    "sessions_all": """
        SELECT pid, usename, state, query, query_start
        FROM pg_stat_activity
        WHERE datname = current_database()
        ORDER BY query_start DESC
    """,
    
    "locks_blocked": """
        SELECT blocked.pid, blocking.pid, ...
        FROM pg_stat_activity blocked
        JOIN pg_locks blocked_locks ON ...
        WHERE blocked_locks.granted = false
    """,
    # ...
}
```

## 5. 配置设计

### 5.1 配置结构

```yaml
database:
  host: localhost
  port: 5432
  database: postgres
  user: postgres
  password: ""
  ssl_mode: prefer

llm:
  provider: anthropic
  model: claude-sonnet-4-6
  api_key: ""  # 推荐使用环境变量
  max_tokens: 4096
  max_turns: 20

display:
  theme: dark
  table_style: rounded
```

### 5.2 配置优先级

1. 命令行参数（最高优先级）
2. 环境变量（`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`）
3. 配置文件（`~/.swat_skill/config.yaml`）
4. 默认值（最低优先级）

## 6. 安全设计

### 6.1 只读查询保护

LLM Agent 的 `execute_sql` 工具只允许 SELECT 查询：

```python
if not sql.strip().upper().startswith("SELECT"):
    return {"error": "Only SELECT queries are allowed"}
```

### 6.2 危险操作确认

`/kill` 等危险操作需要用户确认（当前版本为简化版，后续添加确认机制）。

### 6.3 连接信息安全

- 密码不直接写入配置文件（推荐使用环境变量）
- SSL 连接支持

## 7. 扩展设计

### 7.1 新技能添加

创建新技能文件并注册：

```python
# swat_skill/skills/new_skill.py
@register_skill
class NewSkill(Skill):
    name = "newskill"
    description = "新技能描述"
    
    def execute(self, conn, args, formatter):
        # 实现技能逻辑
        return SkillResult(...)
```

然后在 `registry.py` 中导入：

```python
from .new_skill import NewSkill
```

### 7.2 新 LLM Provider

在 `llm/agent.py` 中添加 Provider 支持：

```python
if config.llm.provider == "openai":
    # 使用 OpenAI API
elif config.llm.provider == "anthropic":
    # 使用 Anthropic API
```

### 7.3 新数据库支持

架构设计预留了多数据库支持空间：

- Database Layer 可抽象为接口
- Queries 模板按数据库类型分离
- Skills 按数据库兼容性标记

## 8. 性能考量

### 8.1 查询性能

- 使用预定义查询模板，避免动态拼接
- 查询添加 LIMIT 限制
- 执行时间统计和报告

### 8.2 LLM Token 控制

- System Prompt 精简
- 证据数据压缩（只返回关键信息）
- 最大轮次限制（20 轮）

## 9. 后续规划

### v1.6.0 (已完成)

- dbtop 显示重构（参考 pg_top）
- Rich Layout 分区域显示
- Table 直接渲染（不转为字符串）

### v1.7.0

- Sentinel 实时监控
- Rule 规则引擎（确定性诊断）
- Scheduler 定时巡检

### v1.8.0

- MySQL 支持
- Oracle 支持（可选）
- 报告导出

## 10. 参考资料

- [PostgreSQL System Views](https://www.postgresql.org/docs/current/monitoring-stats.html)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/)
- [Rich](https://rich.readthedocs.io/)