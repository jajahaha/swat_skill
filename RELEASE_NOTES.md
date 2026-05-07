# Release Notes

## v1.2.0 (2026-05-07)

🔧 **Web Interface Bug 修复与体验优化**

swat_skill v1.2.0 修复了 Web Interface 的若干问题，提升了用户体验。

### 🐛 修复内容

#### WebSocket 连接稳定性
- **连接断开问题**：修复输错命令导致 WebSocket 连接断开的问题
- **异常处理优化**：区分连接错误和执行错误，执行错误不再断开连接
- **JSON 解析错误**：无效消息格式只报错，不影响连接

#### 输出格式优化
- **换行显示**：修复文本输出中 `\n` 换行符不显示的问题（添加 `white-space: pre-wrap`）
- **结果分隔**：各输出块之间添加分隔线，提升可读性
- **表格样式**：优化表格和健康报告的显示布局

### ✨ 新功能

#### Tab 键命令补全
- **自动补全**：Web Terminal 支持 Tab 键自动补全命令
- **多匹配提示**：多个匹配时显示所有候选项
- **公共前缀补全**：部分匹配时补全到公共前缀

### 📝 文档更新

- 版本号统一更新为 1.2.0
- RELEASE_NOTES.md 添加版本历史

---

## v1.1.0 (2026-05-07)

🌐 **Web Interface 新功能**

swat_skill v1.1.0 添加了网页端入口，可以在浏览器中使用 swat_skill。

### 🚀 新功能

#### Web Terminal
- **网页终端**：在浏览器中使用 swat_skill，支持所有 CLI 功能
- **WebSocket 实时交互**：命令实时执行，结果实时显示
- **终端风格 UI**：深色主题，类似命令行界面
- **会话管理**：支持多个独立会话，自动清理过期会话

#### 使用方式
```bash
# 启动 Web 服务器
swat_skill web --port 8080

# 或使用 CLI
swat_skill web
```

打开浏览器访问 http://localhost:8080 即可使用。

#### REST API
提供 REST API 供外部程序调用：
- `/api/connect` - 创建会话
- `/api/command/{session_id}` - 执行命令
- `/api/session/{session_id}` - 删除会话
- `/api/status` - 获取服务器状态

### 📦 新增依赖
- fastapi>=0.100.0
- uvicorn>=0.23.0
- websockets>=11.0
- jinja2>=3.1.0

安装方式：
```bash
pip install swat_skill[web]
```

---

## v1.0.1 (2026-05-06)

🔧 **Bug 修复与样式更新**

swat_skill v1.0.1 是一个维护版本，修复了若干问题并更新了项目样式。

### 🐛 修复内容

- **Banner 更新**：启动 Banner 更新为正确的 SWAT SKILL ASCII 艺术字（使用 bulbhead 字体，字母内部白色填充）
- **文档清理**：移除 DESIGN.md 中不必要的 OpenDB 引用，仅在 README.md 致谢部分保留
- **导入修复**：修复多个技能文件中缺少 `Formatter` 导入的问题

### 📝 文档更新

- README.md Banner 更新
- RELEASE_NOTES.md 添加版本历史记录
- 项目版本号统一为 1.0.1

### 🔧 技术改进

- 使用 raw string 处理 Banner 中的转义字符
- 统一 pyproject.toml 和 __init__.py 中的版本号

---

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
| v1.2.0 | 2026-05-07 | Web Interface Bug 修复与体验优化 |
| v1.1.0 | 2026-05-07 | Web Interface 新功能 |
| v1.0.1 | 2026-05-06 | Bug 修复与样式更新 |
| v1.0.0 | 2026-05-06 | 首个正式版本 |