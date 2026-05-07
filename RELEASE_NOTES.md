# Release Notes

## v1.6.0 (2026-05-07)

📊 **dbtop 显示重构（参考 pg_top）**

swat_skill v1.6.0 重构了 `/dbtop` 命令的显示效果，使其更像 pg_top 的经典 top 风格。

### 📊 dbtop 显示改进

#### CLI 模式 - Layout 布局
使用 Rich Layout 分区域显示，类似 pg_top：

```
┌──────────────────────────────────────────────────────────────────────┐
│ SWAT SKILL dbtop - PostgreSQL Monitor          15:45:17             │
├──────────────────────────────────────────────────────────────────────┤
│ Active: 3   Total: 12/100   Cache: 98.5%   Commit: 1234   Rollback: 0│
├──────────────────────────────────────────────────────────────────────┤
│  PID   USER        STATE        DURATION   WAIT          QUERY       │
│ 23887  lcj         active       0.12s      -             SELECT *... │
│ 23888  lcj         idle         2.34s      ClientRead    INSERT...   │
├──────────────────────────────────────────────────────────────────────┤
│ Wait Events: ClientRead(2), DataFileRead(1)                         │
└──────────────────────────────────────────────────────────────────────┘
```

#### 显示区域
- **Header**：标题和时间戳
- **Stats**：活跃会话、连接数、缓存命中率、事务统计
- **Table**：会话列表表格（PID、用户、状态、执行时间、等待事件、查询）
- **Footer**：等待事件汇总

#### 表格改进
- 新增 **Wait 列**：显示等待事件类型和名称
- 状态颜色编码：active（绿色）、idle（灰色）、idle_tx（黄色）
- 执行时间颜色：>60s（红色）、>10s（黄色）
- 表格自适应宽度

#### 关键修复
- **问题修复**：之前使用 `"\n".join(str(table))` 导致 Rich Table 被转为字符串
- **新方案**：使用 `Layout["table"].update(table)` 直接渲染 Table 对象

### 📝 文档更新

- 版本号统一更新为 1.6.0

---

## v1.5.0 (2026-05-07)

📊 **dbtop 命令优化**

swat_skill v1.5.0 改进了 `/dbtop` 命令，使其更像 Linux top 命令，支持实时刷新显示。

### 📊 dbtop 改进

#### CLI 模式
- **实时刷新显示**：类似 Linux top 命令，每次迭代清屏重绘
- **Rich 格式化**：使用 Rich Panel 和 Table 渲染，美观直观
- **Ctrl+C 中断**：支持按键中断停止监控
- **参数支持**：`/dbtop [interval] [iterations]` 自定义刷新间隔和次数

#### Web 模式
- **格式化显示**：返回结构化的 JSON 数据，前端美观渲染
- **摘要卡片**：显示活跃会话、连接数、缓存命中率、事务统计
- **会话表格**：展示活跃会话详情（PID、用户、状态、执行时间）
- **等待事件表格**：展示当前等待事件

### 🎨 Web UI 新增
- dbtop 专用样式：摘要区、会话表、等待事件表
- 样式统一：与健康报告卡片风格一致

### 📝 文档更新

- 版本号统一更新为 1.5.0

---

## v1.4.0 (2026-05-07)

🧪 **测试框架与 CI/CD**

swat_skill v1.4.0 添加了完整的测试框架和 GitHub Actions CI 配置，确保代码质量。

### 🧪 测试框架

#### 测试用例
- **Config 测试**：配置加载、保存、默认值、环境变量
- **Dispatcher 测试**：SQL 检测、输入路由、技能执行
- **Skills Registry 测试**：技能注册、别名、帮助文本
- **Web Adapter 测试**：WebFormatter 格式化、WebSession 会话管理
- **Web Session 测试**：SessionManager 创建、删除、过期清理

#### 测试统计
- **57 个测试用例**
- 覆盖核心模块：Config、Dispatcher、Skills、Web Interface

### 🔧 CI/CD

#### GitHub Actions
- **自动化测试**：每次 push 和 PR 自动运行测试
- **多版本支持**：Python 3.10、3.11、3.12
- **覆盖率报告**：pytest-cov 生成覆盖率报告

### 📝 其他改进

- 修复 dispatcher/parser.py 导入错误
- 添加 pytest-asyncio 支持

### 📦 新增依赖

- pytest-asyncio>=0.21

---

## v1.3.0 (2026-05-07)

🎨 **Web Interface UI 重构与体验升级**

swat_skill v1.3.0 对 Web Interface 进行了全面的 UI 重构，提供更现代美观的用户界面。

### 🎨 UI 重构

#### 整体设计
- **GitHub 风格深色主题**：采用 GitHub Dark 配色方案，视觉更舒适
- **JetBrains Mono 字体**：专业编程字体，代码显示更清晰
- **卡片式布局**：表格、健康报告采用卡片式设计，层次分明

#### Header 顶部栏
- **Logo + 连接状态**：实时显示连接状态，动画指示器
- **快捷键提示**：Tab 补全、↑↓ 历史、Enter 执行

#### Sidebar 侧边栏
- **常用诊断技能**：一键点击即可执行常用命令
- **图标美化**：每个技能配有直观图标

#### Banner 优化
- **大号 LOGO**：居中显示 "SWAT SKILL"，带发光效果
- **版本号高亮**：紫色版本号标签，一目了然
- **渐变背景**：卡片式 Banner，更醒目直观

### ✨ 功能优化

#### 输入区域
- **聚焦高亮**：输入框聚焦时绿色边框高亮
- **清屏/帮助按钮**：快捷操作按钮
- **Placeholder 提示**：输入提示更友好

#### 输出效果
- **表格美化**：悬停效果、圆角边框、斑马纹
- **健康报告卡片**：分类展示，状态图标直观
- **渐变分隔线**：各输出块之间优雅分隔
- **淡入动画**：结果加载动画效果

#### 交互体验
- **自定义滚动条**：美观的滚动条样式
- **响应式设计**：小屏幕自动隐藏侧边栏
- **快捷键补全**：Tab 键智能补全命令

### 📝 文档更新

- 版本号统一更新为 1.3.0

---

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
| v1.6.0 | 2026-05-07 | dbtop 显示重构（参考 pg_top，Layout 布局） |
| v1.5.0 | 2026-05-07 | dbtop 命令优化（实时刷新、格式化显示） |
| v1.4.0 | 2026-05-07 | 测试框架与 CI/CD |
| v1.3.0 | 2026-05-07 | Web Interface UI 重构与体验升级 |
| v1.2.0 | 2026-05-07 | Web Interface Bug 修复与体验优化 |
| v1.1.0 | 2026-05-07 | Web Interface 新功能 |
| v1.0.1 | 2026-05-06 | Bug 修复与样式更新 |
| v1.0.0 | 2026-05-06 | 首个正式版本 |
| v1.0.0 | 2026-05-06 | 首个正式版本 |