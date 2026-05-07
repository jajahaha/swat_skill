"""FastAPI web server for swat_skill.

Provides web interface with WebSocket for real-time terminal interaction.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ..config import Config, load_config
from .websocket import session_manager, handle_websocket, handle_command_http
from .adapter import WebFormatter


# Create FastAPI app
app = FastAPI(
    title="swat_skill Web",
    description="PostgreSQL Database CLI Agent - Web Interface",
    version="1.3.0",
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Get templates and static directories
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# HTML template for terminal interface
TERMINAL_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SWAT SKILL - PostgreSQL 智能诊断</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-card: #1c2128;
            --border-color: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --accent-green: #3fb950;
            --accent-blue: #58a6ff;
            --accent-yellow: #d29922;
            --accent-red: #f85149;
            --accent-purple: #a371f7;
            --accent-orange: #db6d28;
            --gradient-start: #238636;
            --gradient-end: #3fb950;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
            line-height: 1.6;
        }

        /* Header */
        .header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo {
            font-family: 'JetBrains Mono', monospace;
            font-size: 18px;
            font-weight: 600;
            color: var(--accent-green);
            letter-spacing: 1px;
        }

        .logo-sub {
            font-size: 12px;
            color: var(--text-secondary);
            margin-left: 8px;
        }

        .connection-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: var(--bg-tertiary);
            border-radius: 6px;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
        }

        .connection-badge::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-yellow);
            animation: pulse 2s infinite;
        }

        .connection-badge.connected::before {
            background: var(--accent-green);
        }

        .connection-badge.error::before {
            background: var(--accent-red);
            animation: none;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .快捷键提示 {
            font-size: 11px;
            color: var(--text-muted);
            padding: 4px 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
        }

        .kbd {
            background: var(--bg-primary);
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid var(--border-color);
            font-size: 10px;
        }

        /* Main Container */
        .main-container {
            display: flex;
            height: calc(100vh - 60px);
        }

        /* Sidebar */
        .sidebar {
            width: 240px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            padding: 16px;
            overflow-y: auto;
            flex-shrink: 0;
        }

        .sidebar-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .skill-list {
            list-style: none;
        }

        .skill-item {
            padding: 8px 12px;
            margin-bottom: 2px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
        }

        .skill-item:hover {
            background: var(--bg-tertiary);
        }

        .skill-item.active {
            background: var(--accent-green);
            color: var(--bg-primary);
        }

        .skill-icon {
            width: 16px;
            text-align: center;
        }

        .skill-category {
            font-size: 11px;
            color: var(--text-muted);
            padding: 8px 12px;
            margin-top: 16px;
            border-top: 1px solid var(--border-color);
        }

        /* Terminal Area */
        .terminal-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Output Container */
        .output-container {
            flex: 1;
            background: var(--bg-primary);
            padding: 20px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
        }

        .output-container::-webkit-scrollbar {
            width: 8px;
        }

        .output-container::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        .output-container::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }

        .output-container::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }

        /* Banner */
        .banner-container {
            background: linear-gradient(135deg, rgba(63, 185, 80, 0.1) 0%, rgba(88, 166, 255, 0.1) 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            text-align: center;
        }

        .banner-logo {
            font-family: 'JetBrains Mono', monospace;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: 4px;
            color: var(--accent-green);
            text-shadow: 0 0 20px rgba(63, 185, 80, 0.3);
            margin-bottom: 8px;
        }

        .banner-title {
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            color: var(--text-secondary);
            letter-spacing: 1px;
        }

        .banner-version {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--accent-purple);
            margin-top: 8px;
        }

        .banner-ascii {
            color: var(--accent-green);
            font-size: 10px;
            line-height: 1.2;
            white-space: pre;
            opacity: 0.6;
            margin-top: 16px;
            font-family: 'JetBrains Mono', monospace;
        }

        /* Output Elements */
        .output-line {
            margin: 8px 0;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .output-line.command {
            color: var(--text-primary);
            display: flex;
            align-items: flex-start;
        }

        .output-line.error {
            color: var(--accent-red);
            background: rgba(248, 81, 73, 0.1);
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid var(--accent-red);
        }

        .output-line.success {
            color: var(--accent-green);
        }

        .output-line.info {
            color: var(--accent-blue);
        }

        .output-line.warning {
            color: var(--accent-yellow);
        }

        .prompt {
            color: var(--accent-green);
            font-weight: 600;
            user-select: none;
        }

        /* Separator */
        .separator {
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border-color), transparent);
            margin: 20px 0;
        }

        /* Result Block */
        .result-block {
            margin: 16px 0;
            animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Table Styling */
        .result-table-wrapper {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        .result-table {
            border-collapse: collapse;
            width: 100%;
            font-size: 13px;
        }

        .result-table th {
            background: var(--bg-tertiary);
            color: var(--accent-green);
            padding: 12px 16px;
            text-align: left;
            font-weight: 500;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }

        .result-table td {
            padding: 10px 16px;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
        }

        .result-table tr:last-child td {
            border-bottom: none;
        }

        .result-table tr:hover td {
            background: var(--bg-secondary);
        }

        .result-table tr:nth-child(even) td {
            background: rgba(22, 27, 34, 0.5);
        }

        .row-count {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 16px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            font-size: 12px;
            color: var(--text-secondary);
            border-radius: 0 0 8px 8px;
        }

        .execution-time {
            color: var(--accent-purple);
        }

        /* Health Report */
        .health-container {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border-color);
        }

        .health-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }

        .health-overall {
            font-size: 14px;
            font-weight: 600;
        }

        .health-status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }

        .health-status-badge.ok {
            background: rgba(63, 185, 80, 0.15);
            color: var(--accent-green);
        }

        .health-status-badge.warning {
            background: rgba(210, 153, 34, 0.15);
            color: var(--accent-yellow);
        }

        .health-status-badge.critical {
            background: rgba(248, 81, 73, 0.15);
            color: var(--accent-red);
        }

        .health-category {
            font-size: 12px;
            font-weight: 600;
            color: var(--accent-blue);
            margin: 16px 0 8px 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .health-items {
            display: grid;
            gap: 6px;
        }

        .health-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 12px;
            background: var(--bg-tertiary);
            border-radius: 6px;
        }

        .health-item-name {
            flex: 1;
            color: var(--text-primary);
        }

        .health-item-value {
            color: var(--text-secondary);
            font-family: 'JetBrains Mono', monospace;
        }

        .health-item-tip {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        /* Status Icons */
        .status-icon {
            width: 20px;
            text-align: center;
            font-weight: 600;
        }

        .status-ok { color: var(--accent-green); }
        .status-warning { color: var(--accent-yellow); }
        .status-critical { color: var(--accent-red); }

        /* Input Container */
        .input-container {
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .input-wrapper {
            flex: 1;
            display: flex;
            align-items: center;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            transition: all 0.15s ease;
        }

        .input-wrapper:focus-within {
            border-color: var(--accent-green);
            box-shadow: 0 0 0 3px rgba(63, 185, 80, 0.1);
        }

        .input-prompt {
            color: var(--accent-green);
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            margin-right: 12px;
            user-select: none;
        }

        #command-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            outline: none;
        }

        #command-input::placeholder {
            color: var(--text-muted);
        }

        .input-actions {
            display: flex;
            gap: 8px;
        }

        .action-btn {
            padding: 8px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-secondary);
            font-size: 12px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .action-btn:hover {
            background: var(--accent-green);
            color: var(--bg-primary);
            border-color: var(--accent-green);
        }

        /* Autocomplete Dropdown */
        .autocomplete-list {
            position: absolute;
            bottom: 100%;
            left: 0;
            right: 0;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 8px;
            padding: 8px;
            display: none;
        }

        .autocomplete-list.show {
            display: block;
        }

        .autocomplete-item {
            padding: 6px 12px;
            cursor: pointer;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
        }

        .autocomplete-item:hover {
            background: var(--bg-tertiary);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
            .header-right {
                display: none;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-left">
            <div class="logo">SWAT SKILL</div>
            <span class="logo-sub">PostgreSQL 智能诊断</span>
            <div id="connection-badge" class="connection-badge">
                <span id="connection-status">连接中...</span>
            </div>
        </div>
        <div class="header-right">
            <span class="快捷键提示"><kbd>Tab</kbd> 补全</span>
            <span class="快捷键提示"><kbd>↑↓</kbd> 历史</span>
            <span class="快捷键提示"><kbd>Enter</kbd> 执行</span>
        </div>
    </header>

    <main class="main-container">
        <aside class="sidebar">
            <div class="sidebar-title">诊断技能</div>
            <ul class="skill-list" id="skill-list">
                <li class="skill-item" data-command="/health">
                    <span class="skill-icon">🔍</span>
                    <span>/health</span>
                </li>
                <li class="skill-item" data-command="/sessions">
                    <span class="skill-icon">👥</span>
                    <span>/sessions</span>
                </li>
                <li class="skill-item" data-command="/locks">
                    <span class="skill-icon">🔒</span>
                    <span>/locks</span>
                </li>
                <li class="skill-item" data-command="/space">
                    <span class="skill-icon">📊</span>
                    <span>/space</span>
                </li>
                <li class="skill-item" data-command="/slowsql">
                    <span class="skill-icon">⚡</span>
                    <span>/slowsql</span>
                </li>
                <li class="skill-item" data-command="/topsql">
                    <span class="skill-icon">📈</span>
                    <span>/topsql</span>
                </li>
                <li class="skill-item" data-command="/vacuum">
                    <span class="skill-icon">🧹</span>
                    <span>/vacuum</span>
                </li>
                <li class="skill-item" data-command="/waits">
                    <span class="skill-icon">⏳</span>
                    <span>/waits</span>
                </li>
                <div class="skill-category">更多命令见 /help</div>
            </ul>
        </aside>

        <div class="terminal-area">
            <div class="output-container" id="output">
                <div class="banner-container">
                    <div class="banner-logo">SWAT SKILL</div>
                    <div class="banner-title">PostgreSQL 智能诊断 Agent</div>
                    <div class="banner-version">v1.3.0</div>
                </div>
            </div>

            <div class="input-container">
                <div class="input-wrapper">
                    <span class="input-prompt">swat_skill&gt;</span>
                    <input type="text" id="command-input" placeholder="输入命令或 SQL..." autofocus autocomplete="off" spellcheck="false">
                </div>
                <div class="input-actions">
                    <button class="action-btn" id="clear-btn">清屏</button>
                    <button class="action-btn" id="help-btn">帮助</button>
                </div>
            </div>
        </div>
    </main>

    <script>
        const outputEl = document.getElementById('output');
        const inputEl = document.getElementById('command-input');
        const statusEl = document.getElementById('connection-status');
        const badgeEl = document.getElementById('connection-badge');
        const skillListEl = document.getElementById('skill-list');
        const clearBtn = document.getElementById('clear-btn');
        const helpBtn = document.getElementById('help-btn');

        let ws = null;
        let sessionId = null;
        let commandHistory = [];
        let historyIndex = -1;
        let skillNames = [];

        // Skill list click handler
        skillListEl.addEventListener('click', (e) => {
            const item = e.target.closest('.skill-item');
            if (item) {
                const command = item.dataset.command;
                inputEl.value = command;
                inputEl.focus();
            }
        });

        // Clear button
        clearBtn.addEventListener('click', () => {
            outputEl.innerHTML = `
                <div class="banner-container">
                    <div class="banner-logo">SWAT SKILL</div>
                    <div class="banner-title">PostgreSQL 智能诊断 Agent</div>
                    <div class="banner-version">v1.3.0</div>
                </div>
            `;
        });

        // Help button
        helpBtn.addEventListener('click', () => {
            sendCommand('/help');
        });

        function connect() {
            const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${wsProtocol}//${location.host}/ws`);

            ws.onopen = () => {
                statusEl.textContent = '已连接';
                badgeEl.className = 'connection-badge connected';
            };

            ws.onmessage = (event) => {
                const result = JSON.parse(event.data);
                handleResult(result);
            };

            ws.onerror = () => {
                statusEl.textContent = '连接错误';
                badgeEl.className = 'connection-badge error';
                appendLine('WebSocket 连接错误', 'error');
            };

            ws.onclose = () => {
                statusEl.textContent = '已断开';
                badgeEl.className = 'connection-badge error';
                appendLine('连接已关闭', 'warning');
            };
        }

        function handleResult(result) {
            switch (result.type) {
                case 'connected':
                    sessionId = result.session_id;
                    skillNames = result.skill_names || [];
                    if (result.server_info && result.server_info.success) {
                        const info = result.server_info.info;
                        appendLine(`✓ 已连接到 PostgreSQL ${info.version || 'Unknown'}`, 'success');
                        addSeparator();
                    }
                    break;
                case 'table':
                    renderTable(result);
                    break;
                case 'health':
                    renderHealth(result);
                    break;
                case 'error':
                    appendLine(result.message, 'error');
                    addSeparator();
                    break;
                case 'success':
                    appendLine(result.message, 'success');
                    addSeparator();
                    break;
                case 'info':
                    appendLine(result.message, 'info');
                    addSeparator();
                    break;
                case 'text':
                    appendLine(result.content);
                    addSeparator();
                    break;
                case 'exit':
                    appendLine(result.message, 'info');
                    ws.close();
                    break;
                case 'llm_step':
                    appendLine(`[${result.step}] ${result.content}`, 'info');
                    break;
                case 'llm':
                    if (result.error) {
                        appendLine(result.error, 'error');
                        addSeparator();
                    }
                    break;
                default:
                    if (result.content) {
                        appendLine(result.content);
                        addSeparator();
                    }
            }
        }

        function renderTable(result) {
            if (!result.columns || !result.rows) {
                appendLine('无数据', 'info');
                addSeparator();
                return;
            }

            const block = document.createElement('div');
            block.className = 'result-block';

            const wrapper = document.createElement('div');
            wrapper.className = 'result-table-wrapper';

            const table = document.createElement('table');
            table.className = 'result-table';

            // Header
            const headerRow = table.insertRow();
            result.columns.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col;
                headerRow.appendChild(th);
            });

            // Rows
            result.rows.forEach(row => {
                const tr = table.insertRow();
                result.columns.forEach(col => {
                    const td = tr.insertCell();
                    const value = row[col];
                    td.textContent = value !== null && value !== undefined ? String(value) : '';
                });
            });

            wrapper.appendChild(table);
            block.appendChild(wrapper);

            // Row count footer
            const footer = document.createElement('div');
            footer.className = 'row-count';
            footer.innerHTML = `
                <span>${result.row_count} 行结果</span>
                <span class="execution-time">${result.execution_time.toFixed(3)}s</span>
            `;
            block.appendChild(footer);

            outputEl.appendChild(block);
            addSeparator();
            scrollToBottom();
        }

        function renderHealth(result) {
            const block = document.createElement('div');
            block.className = 'result-block';

            const container = document.createElement('div');
            container.className = 'health-container';

            // Header
            const header = document.createElement('div');
            header.className = 'health-header';
            header.innerHTML = `
                <span class="health-overall">数据库健康状态</span>
                <span class="health-status-badge ${result.overall}">${getStatusText(result.overall)}</span>
            `;
            container.appendChild(header);

            // Group items by category
            const categories = {};
            result.items.forEach(item => {
                if (!categories[item.category]) {
                    categories[item.category] = [];
                }
                categories[item.category].push(item);
            });

            // Render categories
            for (const [category, items] of Object.entries(categories)) {
                const catDiv = document.createElement('div');
                catDiv.className = 'health-category';
                catDiv.textContent = category;
                container.appendChild(catDiv);

                const itemsDiv = document.createElement('div');
                itemsDiv.className = 'health-items';

                items.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'health-item';
                    itemDiv.innerHTML = `
                        <span class="status-icon ${item.status}">${getStatusSymbol(item.status)}</span>
                        <span class="health-item-name">${item.name}</span>
                        <span class="health-item-value">${item.value}</span>
                    `;
                    if (item.tip) {
                        const tipDiv = document.createElement('div');
                        tipDiv.className = 'health-item-tip';
                        tipDiv.textContent = item.tip;
                        itemDiv.appendChild(tipDiv);
                    }
                    itemsDiv.appendChild(itemDiv);
                });
                container.appendChild(itemsDiv);
            }

            block.appendChild(container);
            outputEl.appendChild(block);
            addSeparator();
            scrollToBottom();
        }

        function getStatusSymbol(status) {
            switch (status) {
                case 'ok': return '✓';
                case 'warning': return '⚠';
                case 'critical': return '✗';
                default: return '?';
            }
        }

        function getStatusText(status) {
            switch (status) {
                case 'ok': return '健康';
                case 'warning': return '警告';
                case 'critical': return '异常';
                default: return '未知';
            }
        }

        function appendLine(text, type = '') {
            const div = document.createElement('div');
            div.className = 'output-line ' + type;
            div.textContent = text;
            outputEl.appendChild(div);
            scrollToBottom();
        }

        function addSeparator() {
            const sep = document.createElement('div');
            sep.className = 'separator';
            outputEl.appendChild(sep);
            scrollToBottom();
        }

        function scrollToBottom() {
            outputEl.scrollTop = outputEl.scrollHeight;
        }

        function sendCommand(command) {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                appendLine('未连接', 'error');
                return;
            }

            // Show command in output
            const cmdDiv = document.createElement('div');
            cmdDiv.className = 'output-line command';
            cmdDiv.innerHTML = `<span class="prompt">swat_skill&gt;</span> ${command}`;
            outputEl.appendChild(cmdDiv);

            // Add to history
            if (command.trim()) {
                commandHistory.push(command);
                historyIndex = commandHistory.length;
            }

            ws.send(JSON.stringify({ command }));
            scrollToBottom();
        }

        // Input handler
        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const command = inputEl.value;
                sendCommand(command);
                inputEl.value = '';
            } else if (e.key === 'Tab') {
                autocomplete();
                e.preventDefault();
            } else if (e.key === 'ArrowUp') {
                if (historyIndex > 0) {
                    historyIndex--;
                    inputEl.value = commandHistory[historyIndex] || '';
                }
                e.preventDefault();
            } else if (e.key === 'ArrowDown') {
                if (historyIndex < commandHistory.length - 1) {
                    historyIndex++;
                    inputEl.value = commandHistory[historyIndex] || '';
                } else {
                    historyIndex = commandHistory.length;
                    inputEl.value = '';
                }
                e.preventDefault();
            }
        });

        function autocomplete() {
            const input = inputEl.value;
            if (!input.startsWith('/')) return;

            const matches = skillNames.filter(s => s.startsWith(input));
            if (matches.length === 0) return;

            if (matches.length === 1) {
                inputEl.value = matches[0] + ' ';
            } else {
                appendLine(`匹配: ${matches.join('  ')}`, 'info');
                let commonPrefix = matches[0];
                for (let i = 1; i < matches.length; i++) {
                    while (!matches[i].startsWith(commonPrefix) && commonPrefix.length > input.length) {
                        commonPrefix = commonPrefix.slice(0, -1);
                    }
                }
                if (commonPrefix.length > input.length) {
                    inputEl.value = commonPrefix;
                }
                scrollToBottom();
            }
        }

        // Connect on page load
        connect();
    </script>
</body>
</html>
"""


@app.on_event("startup")
async def startup_event():
    """Start session cleanup task."""
    await session_manager.start_cleanup_task()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop session cleanup task."""
    await session_manager.stop_cleanup_task()
    # Disconnect all sessions
    for session_id in list(session_manager.sessions.keys()):
        session_manager.remove_session(session_id)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Render terminal interface."""
    return TERMINAL_HTML


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time interaction."""
    await handle_websocket(websocket)


@app.websocket("/ws/{session_id}")
async def websocket_endpoint_with_session(websocket: WebSocket, session_id: str):
    """WebSocket endpoint with existing session."""
    await handle_websocket(websocket, session_id)


@app.get("/api/status")
async def get_status():
    """Get server status."""
    return {
        "active_sessions": session_manager.get_active_count(),
        "version": "1.3.0",
    }


@app.post("/api/connect")
async def create_session():
    """Create new session."""
    config = load_config()
    session = session_manager.create_session(config)
    server_info = session.get_server_info()
    return {
        "session_id": session.id,
        "server_info": server_info,
    }


@app.post("/api/command/{session_id}")
async def execute_command(session_id: str, command: str):
    """Execute command via HTTP."""
    result = await handle_command_http(session_id, command)
    return result


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete session."""
    session_manager.remove_session(session_id)
    return {"success": True}


def run_web_server(host: str = "0.0.0.0", port: int = 8080):
    """Run web server.

    Args:
        host: Server host.
        port: Server port.
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)