# swat_skill v1.2.0 - PostgreSQL Database CLI Agent

<p align="center">
  <pre align="center">
 ___  _    _    __   ____    ___  _  _  ____  __    __
/ __)( \/\/ )  /__\ (_  _)  / __)( )/ )(_  _)(  )  (  )
\__ \ )    (  /(__)\  )(    \__ \ )  (  _)(_  )(__  )(__
(___/(__/\__)(__)(__)(__)   (___/(_)\_)(____)(____)(____)
  </pre>
  <strong>PostgreSQL Database CLI Agent</strong><br>
  <em>三种交互方式，智能数据库诊断</em>
</p>

<p align="center">
  <a href="https://github.com/jajahaha/swat_skill/releases"><img alt="Release" src="https://img.shields.io/github/v/release/jajahaha/swat_skill?style=flat-square&color=blue"></a>
  <a href="https://github.com/jajahaha/swat_skill/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square"></a>
  <img alt="Platform" src="https://img.shields.io/badge/platform-linux%20%7C%20macOS-lightgrey?style=flat-square">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white">
</p>


---

## 🎯 项目简介

swat_skill 是一个专为 PostgreSQL 设计的数据库智能诊断 CLI Agent。它借鉴 Claude Code 的交互设计理念，提供三种无缝整合的交互方式，让 DBA 和开发人员能够高效地管理和诊断数据库。

### 三种交互方式

| 模式 | 示例 | 执行效果 |
|------|------|---------|
| **/ 命令** | `/health` | 执行内置诊断技能 |
| **原生 SQL** | `SELECT * FROM pg_stat_activity` | 直接在数据库执行 |
| **自然语言** | `数据库为什么慢？` | 路由到 LLM Agent 智能诊断 |

## ✨ 核心特性

- 🔍 **36+ 诊断技能**：覆盖会话、锁、空间、Vacuum、WAL、复制、性能等
- 🤖 **LLM 智能诊断**：多轮推理，自动采集证据，定位根因
- 📊 **美观输出**：使用 Rich 库渲染表格和健康报告
- ⚙️ **灵活配置**：YAML 配置文件，支持命令行覆盖
- 🔒 **安全执行**：只读查询安全检查，危险操作需确认

## 📦 安装

```bash
# 从 PyPI 安装（即将发布）
pip install swat_skill

# 安装 Web Interface 支持
pip install swat_skill[web]

# 从源码安装
git clone https://github.com/jajahaha/swat_skill.git
cd swat_skill
pip install -e .
pip install -e ".[web]"  # Web Interface 支持
```

## 🚀 快速开始

### 1. 配置数据库连接

```bash
swat_skill setup
```

交互式向导将引导您配置数据库和 LLM。

### 2. 启动 CLI

```bash
swat_skill

# 或使用命令行参数
swat_skill --host localhost --port 5432 --database mydb --user postgres
```

### 3. 启动 Web Interface

```bash
# 启动 Web 服务器
swat_skill web --port 8080

# 然后在浏览器打开 http://localhost:8080
```

### 4. 开始诊断

```
swat_skill> /health
swat_skill> SELECT * FROM pg_stat_activity WHERE state='active';
swat_skill> 数据库连接数为什么这么高？
```

## 📚 技能列表

### 监控与诊断

| 技能 | 说明 |
|------|------|
| `/health` | 全维度健康体检（10+ 项指标） |
| `/dbtop` | 实时性能面板（类似 Linux top） |
| `/sessions` | 全部会话列表 |
| `/activesessions` | 活跃会话分析 |
| `/waits` | 等待事件统计 |
| `/locks` | 锁信息概览 |
| `/blocked` | 被阻塞的锁 |
| `/blocktree` | 锁阻塞链树状结构 |
| `/longtx` | 长事务检测（>60秒） |
| `/idletx` | idle in transaction 检测 |

### 空间分析

| 技能 | 说明 |
|------|------|
| `/space` | 数据库空间使用 |
| `/tablesizes` | 大表空间占用 TOP 20 |
| `/indexsizes` | 索引空间占用 TOP 20 |
| `/bloat` | 表/索引膨胀检测 |
| `/unusedindexes` | 未使用的索引 |

### PostgreSQL 特有

| 技能 | 说明 |
|------|------|
| `/vacuum` | Vacuum 状态和 Autovacuum |
| `/wal` | WAL 日志状态 |
| `/replication` | 主从复制状态 |
| `/slots` | 复制槽状态 |
| `/xid` | XID wraparound 监控 |
| `/buffers` | Shared Buffer 命中率 |

### SQL 分析

| 技能 | 说明 |
|------|------|
| `/slowsql [ms]` | 慢 SQL 分析（需 pg_stat_statements） |
| `/topsql` | Top SQL（按总耗时） |
| `/topsqlcalls` | Top SQL（按调用次数） |
| `/explain` | SQL 执行计划分析 |
| `/sql` | 执行自定义 SQL |

### 管理操作

| 技能 | 说明 |
|------|------|
| `/kill <pid>` | 终止会话 |
| `/params [pattern]` | 搜索数据库参数 |
| `/memory` | 内存相关参数 |
| `/users` | 用户信息 |
| `/tableinfo [table]` | 表结构信息 |
| `/tableindexes` | 表索引信息 |

### AI 诊断

| 技能 | 说明 |
|------|------|
| `/llm` | 启动 LLM 多轮诊断 |
| `/model [model]` | 切换/显示 LLM 模型 |

### 系统命令

| 技能 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/exit` | 退出程序 |

## ⚙️ 配置

配置文件位置：`~/.swat_skill/config.yaml`

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
  max_tokens: 4096
  max_turns: 20

display:
  theme: dark
  table_style: rounded
```

### LLM 配置

设置 API Key（推荐使用环境变量）：

```bash
export ANTHROPIC_API_KEY=your-api-key
```

## 🌐 Web Interface

swat_skill v1.2.0 提供了网页端入口，支持在浏览器中使用所有 CLI 功能。

### 启动 Web 服务器

```bash
swat_skill web --port 8080
```

访问 http://localhost:8080 即可使用。

### Web 功能

| 功能 | 说明 |
|------|------|
| 终端风格 UI | 深色主题，类似命令行界面 |
| WebSocket | 实时命令执行和结果显示 |
| 会话管理 | 支持多个独立会话 |
| REST API | `/api/connect`, `/api/command`, `/api/status` |

### REST API 示例

```bash
# 创建会话
curl -X POST http://localhost:8080/api/connect

# 执行命令
curl -X POST "http://localhost:8080/api/command/{session_id}?command=/health"
```

## 🏗️ 架构设计

```
用户输入
    │
    ▼
┌─────────────┐
│  Dispatcher │ ← 智能输入分类
└──────┬──────┘
       │
   ┌───┼───┐
   ▼   ▼   ▼
/命令 SQL 自然语言
   │   │   │
   ▼   ▼   ▼
Skills DB  LLM Agent
   │   │   │
   └───┴───┘
       │
       ▼
Formatter → 输出
```

详细设计文档见 [DESIGN.md](./DESIGN.md)。

## 🛠️ 开发

### 项目结构

```
swat_skill/
├── swat_skill/
│   ├── cli.py              # CLI 入口
│   ├── config.py           # 配置管理
│   ├── database/
│   │   ├── connection.py   # PostgreSQL 连接
│   │   └── queries.py      # 诊断 SQL 模板
│   ├── dispatcher/
│   │   └── router.py       # 输入分发器
│   ├── skills/             # 36 个诊断技能
│   ├── llm/
│   │   ├── agent.py        # LLM Agent
│   │   └── tools.py        # Function Calling 工具
│   └── utils/
│       └── formatter.py    # 输出格式化
├── pyproject.toml
├── requirements.txt
└── README.md
```

### 运行测试

```bash
python -m pytest tests/
```

## 📝 更新日志

见 [RELEASE_NOTES.md](./RELEASE_NOTES.md)。

## 📄 许可证

Apache License 2.0

## 🙏 致谢

本项目设计参考了 [OpenDB](https://github.com/sqlrush/opendb) 的交互理念和功能设计。