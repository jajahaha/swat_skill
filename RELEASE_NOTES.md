# Release Notes

## v1.0.0 (2026-05-06)

🎉 **首个正式版本发布！**

swat_skill v1.0.0 是一个功能完整的 PostgreSQL 数据库智能诊断 CLI Agent。

### 🚀 新功能

#### 三种交互方式
- **简化命令**：36+ 内置诊断技能，`/command` 一键执行
- **原生 SQL**：直接执行 PostgreSQL SQL 语句
- **自然语言**：LLM Agent 多轮推理智能诊断

#### 诊断技能（36 个）
- **监控诊断**：`/health`, `/dbtop`, `/sessions`, `/activesessions`, `/waits`, `/locks`, `/blocked`, `/blocktree`, `/longtx`, `/idletx`
- **空间分析**：`/space`, `/tablesizes`, `/indexsizes`, `/bloat`, `/unusedindexes`
- **PostgreSQL 特有**：`/vacuum`, `/wal`, `/replication`, `/slots`, `/xid`, `/buffers`
- **SQL 分析**：`/slowsql`, `/topsql`, `/topsqlcalls`, `/explain`, `/sql`
- **管理操作**：`/kill`, `/params`, `/memory`, `/users`, `/tableinfo`, `/tableindexes`
- **AI 诊断**：`/llm`, `/model`
- **系统命令**：`/help`, `/exit`

#### LLM 智能诊断
- Claude API 集成，支持多轮 Function Calling
- 自动采集数据库证据，逐步收敛根因
- 防幻觉机制：结论基于工具查询结果
- 支持 Anthropic Claude 和 OpenAI 模型

#### 美观输出
- Rich 库渲染表格和健康报告
- ✓/⚠/✗ 状态符号直观展示
- 自适应终端宽度

#### 配置管理
- YAML 配置文件（`~/.swat_skill/config.yaml`）
- 交互式配置向导（`swat_skill setup`）
- 命令行参数覆盖

### 📦 技术栈

| 模块 | 技术 |
|------|------|
| PostgreSQL 驱动 | psycopg[binary] 3.x |
| CLI 框架 | prompt_toolkit |
| 输出渲染 | rich |
| 配置管理 | PyYAML |
| LLM 集成 | anthropic SDK |

### 🔧 安装

```bash
pip install swat_skill
```

或从源码安装：

```bash
git clone https://github.com/jajahaha/swat_skill.git
cd swat_skill
pip install -e .
```

### 📋 已知限制

1. `/slowsql` 和 `/topsql` 需要 `pg_stat_statements` 扩展
2. LLM 诊断需要配置 API Key
3. 暂不支持 Sentinel 实时监控（计划后续版本）
4. 暂不支持 Rule 规则引擎（计划后续版本）

### 🔮 后续计划

**v1.1.0**
- Sentinel 实时异常监控
- `/rule` 确定性规则引擎
- `/scheduler` 定时巡检

**v1.2.0**
- MySQL 支持
- Oracle 支持（可选）
- Web UI 界面

### 🙏 贡献者

- Initial development by swat_skill team

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| v1.0.0 | 2026-05-06 | 首个正式版本 |