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
from ..utils.formatter import SWAT_SKILL_BANNER
from .websocket import session_manager, handle_websocket, handle_command_http
from .adapter import WebFormatter


# Create FastAPI app
app = FastAPI(
    title="swat_skill Web",
    description="PostgreSQL Database CLI Agent - Web Interface",
    version="1.2.0",
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>swat_skill Web Terminal</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            background: #1a1a2e;
            color: #eee;
            font-family: 'Courier New', Courier, monospace;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .banner {
            color: #00ff88;
            font-size: 14px;
            margin-bottom: 20px;
            white-space: pre;
        }
        .output-container {
            background: #16213e;
            border-radius: 8px;
            padding: 15px;
            min-height: 60vh;
            max-height: 70vh;
            overflow-y: auto;
            margin-bottom: 15px;
        }
        .output-line {
            margin: 5px 0;
            line-height: 1.4;
            white-space: pre-wrap;
        }
        .output-line.command {
            color: #fff;
        }
        .output-line.error {
            color: #ff4444;
        }
        .output-line.success {
            color: #00ff88;
        }
        .output-line.info {
            color: #4da6ff;
        }
        .prompt {
            color: #00ff88;
            font-weight: bold;
        }
        .input-container {
            display: flex;
            align-items: center;
            background: #16213e;
            border-radius: 8px;
            padding: 10px 15px;
        }
        .input-container .prompt {
            margin-right: 10px;
        }
        #command-input {
            background: transparent;
            border: none;
            color: #fff;
            font-family: inherit;
            font-size: inherit;
            width: 100%;
            outline: none;
        }
        /* Table styling */
        .result-table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }
        .result-table th {
            background: #0f3460;
            color: #00ff88;
            padding: 8px;
            border: 1px solid #1a1a2e;
            text-align: left;
        }
        .result-table td {
            padding: 8px;
            border: 1px solid #1a1a2e;
        }
        .result-table tr:nth-child(even) td {
            background: #1a1a2e;
        }
        /* Health report styling */
        .health-container {
            margin: 10px 0;
        }
        .health-category {
            font-weight: bold;
            color: #4da6ff;
            margin: 10px 0 5px 0;
        }
        .health-item {
            margin: 3px 0;
        }
        .status-ok { color: #00ff88; }
        .status-warning { color: #ffcc00; }
        .status-critical { color: #ff4444; }
        .dim { color: #888; font-size: 12px; margin-bottom: 10px; }
        .separator {
            border-bottom: 1px solid #2a2a4e;
            margin: 15px 0;
        }
        .result-block {
            margin-bottom: 15px;
        }
        .connection-status {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .connection-status.connected {
            background: #0f3460;
            color: #00ff88;
        }
        .connection-status.error {
            background: #2f1f1f;
            color: #ff4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="banner">{banner}</div>

        <div id="connection-status" class="connection-status">
            Connecting...
        </div>

        <div id="output" class="output-container"></div>

        <div class="input-container">
            <span class="prompt">swat_skill> </span>
            <input type="text" id="command-input" autofocus autocomplete="off">
        </div>
    </div>

    <script>
        const banner = `{banner}`;
        const outputEl = document.getElementById('output');
        const inputEl = document.getElementById('command-input');
        const statusEl = document.getElementById('connection-status');
        let ws = null;
        let sessionId = null;
        let commandHistory = [];
        let historyIndex = -1;
        let skillNames = [];  // Available skill names for autocomplete

        function connect() {
            const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${wsProtocol}//${location.host}/ws`);

            ws.onopen = () => {
                statusEl.textContent = 'Connected';
                statusEl.className = 'connection-status connected';
                appendLine('Welcome to swat_skill Web Terminal');
                appendLine('Type /help for available commands', 'info');
            };

            ws.onmessage = (event) => {
                const result = JSON.parse(event.data);
                handleResult(result);
            };

            ws.onerror = (error) => {
                statusEl.textContent = 'Connection error';
                statusEl.className = 'connection-status error';
                appendLine('WebSocket error', 'error');
            };

            ws.onclose = () => {
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'connection-status error';
                appendLine('Connection closed', 'info');
            };
        }

        function handleResult(result) {
            switch (result.type) {
                case 'connected':
                    sessionId = result.session_id;
                    skillNames = result.skill_names || [];
                    if (result.server_info && result.server_info.success) {
                        const info = result.server_info.info;
                        appendLine(`Connected to PostgreSQL ${info.version || 'Unknown'}`, 'success');
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
                appendLine('No data', 'info');
                addSeparator();
                return;
            }

            const block = document.createElement('div');
            block.className = 'result-block';

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
                    td.textContent = row[col] !== null && row[col] !== undefined ? String(row[col]) : '';
                });
            });

            block.appendChild(table);

            // Row count
            const count = document.createElement('div');
            count.className = 'dim';
            count.textContent = `${result.row_count} rows, ${result.execution_time.toFixed(3)}s`;
            block.appendChild(count);

            outputEl.appendChild(block);
            addSeparator();
            scrollToBottom();
        }

        function renderHealth(result) {
            const block = document.createElement('div');
            block.className = 'result-block';

            const container = document.createElement('div');
            container.className = 'health-container';

            // Overall status
            const overallDiv = document.createElement('div');
            overallDiv.innerHTML = `<strong>Overall: </strong>${getStatusSymbol(result.overall)} ${result.overall.toUpperCase()}`;
            container.appendChild(overallDiv);

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

                items.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'health-item';
                    itemDiv.innerHTML = `${getStatusSymbol(item.status)} ${item.name}: ${item.value}`;
                    container.appendChild(itemDiv);
                });
            }

            block.appendChild(container);
            outputEl.appendChild(block);
            addSeparator();
            scrollToBottom();
        }

        function getStatusSymbol(status) {
            switch (status) {
                case 'ok': return '<span class="status-ok">✓</span>';
                case 'warning': return '<span class="status-warning">⚠</span>';
                case 'critical': return '<span class="status-critical">✗</span>';
                default: return '?';
            }
        }

        function appendLine(text, type = '') {
            const div = document.createElement('div');
            div.className = 'output-line ' + type;
            div.innerHTML = text;
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
                appendLine('Not connected', 'error');
                return;
            }

            // Show command in output
            appendLine(`<span class="prompt">swat_skill> </span>${command}`, 'command');

            // Add to history
            if (command.trim()) {
                commandHistory.push(command);
                historyIndex = commandHistory.length;
            }

            // Send to server
            ws.send(JSON.stringify({ command }));
        }

        // Input handler
        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const command = inputEl.value;
                sendCommand(command);
                inputEl.value = '';
            } else if (e.key === 'Tab') {
                // Autocomplete
                autocomplete();
                e.preventDefault();
            } else if (e.key === 'ArrowUp') {
                // History navigation
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
            if (!input.startsWith('/')) {
                return;  // Only autocomplete commands
            }

            // Find matching skills
            const matches = skillNames.filter(s => s.startsWith(input));
            if (matches.length === 0) {
                return;
            }

            if (matches.length === 1) {
                // Single match: complete it
                inputEl.value = matches[0] + ' ';
            } else {
                // Multiple matches: show them
                appendLine(`Matches: ${matches.join('  ')}`, 'info');
                // Find common prefix
                let commonPrefix = matches[0];
                for (let i = 1; i < matches.length; i++) {
                    while (!matches[i].startsWith(commonPrefix) && commonPrefix.length > input.length) {
                        commonPrefix = commonPrefix.slice(0, -1);
                    }
                }
                if (commonPrefix.length > input.length) {
                    inputEl.value = commonPrefix;
                }
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
    html = TERMINAL_HTML.replace("{banner}", SWAT_SKILL_BANNER)
    return html


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
        "version": "1.2.0",
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