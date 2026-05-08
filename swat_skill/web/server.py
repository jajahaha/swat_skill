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
    version="1.9.1",
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

        /* Sidebar - Two sections */
        .sidebar {
            width: 280px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            overflow: hidden;
        }

        /* Skills Section - Top */
        .sidebar-skills {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }

        .sidebar-section-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--accent-green);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Search Input */
        .skill-search-container {
            margin-bottom: 8px;
        }

        .skill-search {
            width: 100%;
            padding: 6px 10px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            color: var(--text-primary);
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            outline: none;
        }

        .skill-search:focus {
            border-color: var(--accent-green);
        }

        .skill-search::placeholder {
            color: var(--text-muted);
        }

        .skill-count {
            font-size: 10px;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        /* Skill Categories */
        .skill-category-group {
            margin-bottom: 8px;
        }

        .skill-category-title {
            font-size: 10px;
            color: var(--accent-blue);
            padding: 4px 0;
            border-bottom: 1px dashed var(--border-color);
            margin-bottom: 4px;
            font-weight: 500;
        }

        .skill-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .skill-item {
            padding: 5px 8px;
            margin-bottom: 1px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s ease;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .skill-item:hover {
            background: var(--bg-tertiary);
        }

        .skill-item.active {
            background: var(--accent-green);
            color: var(--bg-primary);
        }

        .skill-item.hidden {
            display: none;
        }

        .skill-name {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .skill-desc {
            font-size: 10px;
            color: var(--text-muted);
            line-height: 1.3;
        }

        .skill-item.active .skill-desc {
            color: rgba(255,255,255,0.7);
        }

        /* Connection Section - Bottom */
        .sidebar-connection {
            padding: 12px;
            background: var(--bg-tertiary);
            flex-shrink: 0;
            max-height: 180px;
            overflow-y: auto;
        }

        .connection-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--accent-yellow);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .connection-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 0;
            font-size: 11px;
            border-bottom: 1px dashed var(--border-color);
        }

        .connection-item:last-child {
            border-bottom: none;
        }

        .connection-label {
            color: var(--text-muted);
        }

        .connection-value {
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
            font-weight: 500;
            max-width: 160px;
            overflow: hidden;
            text-overflow: ellipsis;
            text-align: right;
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 0;
            margin-top: 4px;
        }

        .connection-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--text-muted);
        }

        .connection-dot.connected {
            background: var(--accent-green);
        }

        .connection-dot.error {
            background: var(--accent-red);
        }

        .connection-status-text {
            font-size: 10px;
            color: var(--text-muted);
        }

        .connection-dot.connected + .connection-status-text {
            color: var(--accent-green);
        }

        .connection-dot.error + .connection-status-text {
            color: var(--accent-red);
        }

        .skill-icon {
            width: 14px;
            text-align: center;
            font-size: 10px;
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
            position: relative;
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

        /* Banner - 更紧凑 */
        .banner-container {
            background: linear-gradient(135deg, rgba(63, 185, 80, 0.08) 0%, rgba(88, 166, 255, 0.08) 100%);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
        }

        .banner-logo {
            font-family: 'JetBrains Mono', monospace;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 2px;
            color: var(--accent-green);
        }

        .banner-title {
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .banner-version {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: var(--accent-purple);
            padding: 2px 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
        }

        /* Output Controls - 整合到输入区域上方 */
        .output-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 12px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            font-size: 11px;
        }

        .output-stats {
            color: var(--text-muted);
        }

        .output-actions {
            display: flex;
            gap: 4px;
        }

        .output-btn {
            padding: 3px 8px;
            font-size: 10px;
            background: transparent;
            border: 1px solid var(--border-color);
            border-radius: 3px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .output-btn:hover {
            background: var(--bg-tertiary);
            border-color: var(--accent-green);
            color: var(--accent-green);
        }

        .output-btn.active {
            background: rgba(63, 185, 80, 0.2);
            border-color: var(--accent-green);
            color: var(--accent-green);
        }

        .scroll-to-top {
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 32px;
            height: 32px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            display: none;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 50;
            transition: all 0.15s ease;
            font-size: 14px;
        }

        .scroll-to-top.show {
            display: flex;
        }

        .scroll-to-top:hover {
            background: var(--accent-green);
            color: var(--bg-primary);
        }

        /* Collapsible Output Block */
        .result-block {
            margin: 12px 0;
            animation: fadeIn 0.2s ease;
        }

        .result-block.collapsed .result-content {
            display: none;
        }

        .result-block-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 10px;
            background: var(--bg-tertiary);
            border-radius: 4px 4px 0 0;
            cursor: pointer;
            font-size: 11px;
        }

        .result-block.collapsed .result-block-header {
            border-radius: 4px;
        }

        .result-block-title {
            color: var(--text-primary);
            font-weight: 500;
        }

        .result-block-toggle {
            font-size: 10px;
            color: var(--text-muted);
        }

        .result-content {
            border-top: 1px solid var(--border-color);
        }

        /* Table with max height and scroll */
        .result-table-wrapper {
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            max-height: 350px;
            overflow-y: auto;
        }

        .result-table-wrapper.expanded {
            max-height: none;
        }

        .table-expand-btn {
            padding: 5px 10px;
            font-size: 10px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            color: var(--accent-blue);
            cursor: pointer;
            text-align: center;
        }

        .table-expand-btn:hover {
            background: var(--bg-tertiary);
        }
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

        /* dbtop Container - 紧凑版 */
        .dbtop-container {
            background: var(--bg-card);
            border-radius: 6px;
            padding: 8px;
            border: 1px solid var(--border-color);
            font-size: 12px;
        }

        .dbtop-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 4px 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            margin-bottom: 6px;
        }

        .dbtop-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--accent-green);
        }

        .dbtop-time {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: var(--text-muted);
        }

        /* DB Activity - 单行紧凑 */
        .dbtop-db-activity {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 6px 8px;
            background: rgba(63, 185, 80, 0.05);
            border-radius: 4px;
            margin-bottom: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
        }

        .dbtop-activity-title {
            color: var(--accent-yellow);
            font-weight: 600;
            font-size: 10px;
        }

        .dbtop-activity-values {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .dbtop-activity-item {
            display: flex;
            gap: 3px;
        }

        .dbtop-label {
            color: var(--text-muted);
            font-size: 10px;
        }

        .dbtop-value {
            color: var(--accent-green);
            font-weight: 600;
        }

        .dbtop-value.warning {
            color: var(--accent-yellow);
        }

        .dbtop-value.success {
            color: var(--accent-green);
        }

        /* Session States - 单行 */
        .dbtop-states {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 8px;
            font-size: 11px;
        }

        .dbtop-states-label {
            color: var(--accent-blue);
            font-weight: 600;
        }

        .dbtop-states-value {
            color: var(--text-primary);
        }

        .dbtop-states-active {
            color: var(--accent-green);
            font-weight: 600;
        }

        .dbtop-states-idle {
            color: var(--text-muted);
        }

        .dbtop-states-idle-tx {
            color: var(--accent-yellow);
            font-weight: 600;
        }

        /* Wait Events - 单行 */
        .dbtop-wait-events {
            padding: 4px 8px;
            font-size: 10px;
            color: var(--text-muted);
            border-top: 1px dashed var(--border-color);
            margin-top: 4px;
        }

        .wait-event-item {
            color: var(--accent-yellow);
            font-weight: 500;
        }

        /* dbtop compact table */
        .dbtop-table-wrapper {
            max-height: 200px;
            overflow-y: auto;
            margin: 4px 0;
        }

        .dbtop-table {
            width: 100%;
            font-size: 10px;
            border-collapse: collapse;
        }

        .dbtop-table th {
            background: var(--bg-tertiary);
            padding: 3px 6px;
            text-align: left;
            font-weight: 600;
            color: var(--accent-green);
            border-bottom: 1px solid var(--border-color);
            font-size: 10px;
        }

        .dbtop-table td {
            padding: 2px 6px;
            border-bottom: 1px solid var(--border-color);
            font-size: 10px;
        }

        .dbtop-table tr:hover td {
            background: var(--bg-tertiary);
        }

        .dbtop-table .query-cell {
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .state-active {
            color: var(--accent-green);
            font-weight: 600;
        }

        .state-idle-tx {
            color: var(--accent-yellow);
            font-weight: 600;
        }

        .dbtop-footer {
            font-size: 10px;
            color: var(--text-muted);
            padding: 4px 8px;
            text-align: right;
            border-top: 1px dashed var(--border-color);
        }

        .query-cell {
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .state-active {
            color: var(--accent-green);
            font-weight: 600;
        }

        .state-idle-tx {
            color: var(--accent-yellow);
            font-weight: 600;
        }

        /* Input Container */
        .input-container {
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            padding: 0;
            display: flex;
            flex-direction: column;
        }

        .input-wrapper {
            flex: 1;
            display: flex;
            align-items: center;
            background: var(--bg-primary);
            border: 1px solid transparent;
            padding: 10px 16px;
            transition: all 0.15s ease;
        }

        .input-wrapper:focus-within {
            border-color: var(--accent-green);
            background: rgba(63, 185, 80, 0.05);
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
            <!-- Skills Section - Top -->
            <div class="sidebar-skills">
                <div class="sidebar-section-title">📚 诊断技能</div>
                <div class="skill-search-container">
                    <input type="text" class="skill-search" id="skill-search" placeholder="搜索技能..." />
                </div>
                <div class="skill-count" id="skill-count">36 个技能</div>

                <!-- Monitor Category -->
                <div class="skill-category-group" data-category="monitor">
                    <div class="skill-category-title">📊 监控诊断</div>
                    <ul class="skill-list" id="skill-list">
                        <li class="skill-item" data-command="/health" data-search="健康 体检">
                            <div class="skill-name">/health</div>
                            <div class="skill-desc">全维度健康体检，检查连接、缓存、事务、死锁等</div>
                        </li>
                        <li class="skill-item" data-command="/dbtop" data-search="实时 性能 面板 top">
                            <div class="skill-name">/dbtop</div>
                            <div class="skill-desc">实时性能面板，类似pg_top</div>
                        </li>
                        <li class="skill-item" data-command="/sessions" data-search="会话 连接">
                            <div class="skill-name">/sessions</div>
                            <div class="skill-desc">显示所有数据库会话</div>
                        </li>
                        <li class="skill-item" data-command="/activesessions" data-search="活跃 会话">
                            <div class="skill-name">/activesessions</div>
                            <div class="skill-desc">显示活跃的数据库会话</div>
                        </li>
                        <li class="skill-item" data-command="/waits" data-search="等待 事件">
                            <div class="skill-name">/waits</div>
                            <div class="skill-desc">显示等待事件统计</div>
                        </li>
                        <li class="skill-item" data-command="/locks" data-search="锁 阻塞">
                            <div class="skill-name">/locks</div>
                            <div class="skill-desc">显示所有锁信息</div>
                        </li>
                        <li class="skill-item" data-command="/blocked" data-search="阻塞 锁">
                            <div class="skill-name">/blocked</div>
                            <div class="skill-desc">显示被阻塞的锁</div>
                        </li>
                        <li class="skill-item" data-command="/blocktree" data-search="阻塞 链 树">
                            <div class="skill-name">/blocktree</div>
                            <div class="skill-desc">显示锁阻塞链树状结构</div>
                        </li>
                        <li class="skill-item" data-command="/longtx" data-search="长 事务">
                            <div class="skill-name">/longtx</div>
                            <div class="skill-desc">显示超过60秒的长事务</div>
                        </li>
                        <li class="skill-item" data-command="/idletx" data-search="idle 事务">
                            <div class="skill-name">/idletx</div>
                            <div class="skill-desc">显示idle in transaction会话</div>
                        </li>
                    </ul>
                </div>

                <!-- Space Category -->
                <div class="skill-category-group" data-category="space">
                    <div class="skill-category-title">💾 空间分析</div>
                    <ul class="skill-list">
                        <li class="skill-item" data-command="/space" data-search="空间 大小">
                            <div class="skill-name">/space</div>
                            <div class="skill-desc">显示数据库空间使用</div>
                        </li>
                        <li class="skill-item" data-command="/tablesizes" data-search="表 大小">
                            <div class="skill-name">/tablesizes</div>
                            <div class="skill-desc">显示大表空间占用</div>
                        </li>
                        <li class="skill-item" data-command="/indexsizes" data-search="索引 大小">
                            <div class="skill-name">/indexsizes</div>
                            <div class="skill-desc">显示索引空间占用</div>
                        </li>
                        <li class="skill-item" data-command="/bloat" data-search="膨胀">
                            <div class="skill-name">/bloat</div>
                            <div class="skill-desc">检测表和索引膨胀</div>
                        </li>
                        <li class="skill-item" data-command="/unusedindexes" data-search="未使用 索引">
                            <div class="skill-name">/unusedindexes</div>
                            <div class="skill-desc">显示未使用的索引</div>
                        </li>
                    </ul>
                </div>

                <!-- PostgreSQL Category -->
                <div class="skill-category-group" data-category="pg">
                    <div class="skill-category-title">🐘 PostgreSQL</div>
                    <ul class="skill-list">
                        <li class="skill-item" data-command="/vacuum" data-search="vacuum 清理">
                            <div class="skill-name">/vacuum</div>
                            <div class="skill-desc">显示Vacuum状态和需要清理的表</div>
                        </li>
                        <li class="skill-item" data-command="/wal" data-search="wal 日志">
                            <div class="skill-name">/wal</div>
                            <div class="skill-desc">显示WAL日志状态</div>
                        </li>
                        <li class="skill-item" data-command="/replication" data-search="复制 主从">
                            <div class="skill-name">/replication</div>
                            <div class="skill-desc">显示复制状态</div>
                        </li>
                        <li class="skill-item" data-command="/slots" data-search="复制 槽">
                            <div class="skill-name">/slots</div>
                            <div class="skill-desc">显示复制槽状态</div>
                        </li>
                        <li class="skill-item" data-command="/xid" data-search="xid 事务 wraparound">
                            <div class="skill-name">/xid</div>
                            <div class="skill-desc">显示事务ID使用情况(wraparound监控)</div>
                        </li>
                        <li class="skill-item" data-command="/buffers" data-search="缓存 命中">
                            <div class="skill-name">/buffers</div>
                            <div class="skill-desc">显示缓存命中率统计</div>
                        </li>
                    </ul>
                </div>

                <!-- SQL Category -->
                <div class="skill-category-group" data-category="sql">
                    <div class="skill-category-title">📝 SQL 分析</div>
                    <ul class="skill-list">
                        <li class="skill-item" data-command="/slowsql" data-search="慢 sql">
                            <div class="skill-name">/slowsql</div>
                            <div class="skill-desc">查找慢SQL(需pg_stat_statements)</div>
                        </li>
                        <li class="skill-item" data-command="/topsql" data-search="top sql 耗时">
                            <div class="skill-name">/topsql</div>
                            <div class="skill-desc">显示总耗时最高的SQL</div>
                        </li>
                        <li class="skill-item" data-command="/topsqlcalls" data-search="top sql 调用">
                            <div class="skill-name">/topsqlcalls</div>
                            <div class="skill-desc">显示调用次数最高的SQL</div>
                        </li>
                        <li class="skill-item" data-command="/explain" data-search="执行计划">
                            <div class="skill-name">/explain</div>
                            <div class="skill-desc">显示SQL执行计划</div>
                        </li>
                        <li class="skill-item" data-command="/sql" data-search="执行 sql">
                            <div class="skill-name">/sql</div>
                            <div class="skill-desc">执行自定义SQL语句</div>
                        </li>
                    </ul>
                </div>

                <!-- Management Category -->
                <div class="skill-category-group" data-category="manage">
                    <div class="skill-category-title">🔧 管理</div>
                    <ul class="skill-list">
                        <li class="skill-item" data-command="/kill" data-search="终止 会话">
                            <div class="skill-name">/kill</div>
                            <div class="skill-desc">终止数据库会话</div>
                        </li>
                        <li class="skill-item" data-command="/params" data-search="参数 配置">
                            <div class="skill-name">/params</div>
                            <div class="skill-desc">搜索和显示数据库参数</div>
                        </li>
                        <li class="skill-item" data-command="/memory" data-search="内存 参数">
                            <div class="skill-name">/memory</div>
                            <div class="skill-desc">显示内存相关参数</div>
                        </li>
                        <li class="skill-item" data-command="/users" data-search="用户">
                            <div class="skill-name">/users</div>
                            <div class="skill-desc">显示数据库用户</div>
                        </li>
                        <li class="skill-item" data-command="/tableinfo" data-search="表 结构">
                            <div class="skill-name">/tableinfo</div>
                            <div class="skill-desc">显示表结构信息</div>
                        </li>
                        <li class="skill-item" data-command="/tableindexes" data-search="表 索引">
                            <div class="skill-name">/tableindexes</div>
                            <div class="skill-desc">显示表的索引信息</div>
                        </li>
                    </ul>
                </div>

                <!-- AI Category -->
                <div class="skill-category-group" data-category="ai">
                    <div class="skill-category-title">🤖 AI 诊断</div>
                    <ul class="skill-list">
                        <li class="skill-item" data-command="/llm" data-search="llm 智能 诊断">
                            <div class="skill-name">/llm</div>
                            <div class="skill-desc">使用LLM进行智能诊断</div>
                        </li>
                        <li class="skill-item" data-command="/model" data-search="模型 llm">
                            <div class="skill-name">/model</div>
                            <div class="skill-desc">切换或显示LLM模型</div>
                        </li>
                    </ul>
                </div>

                <!-- System Category -->
                <div class="skill-category-group" data-category="system">
                    <div class="skill-category-title">⚙️ 系统</div>
                    <ul class="skill-list">
                        <li class="skill-item" data-command="/help" data-search="帮助">
                            <div class="skill-name">/help</div>
                            <div class="skill-desc">显示所有可用命令</div>
                        </li>
                        <li class="skill-item" data-command="/exit" data-search="退出">
                            <div class="skill-name">/exit</div>
                            <div class="skill-desc">退出程序</div>
                        </li>
                    </ul>
                </div>
            </div>

            <!-- Connection Section - Bottom -->
            <div class="sidebar-connection">
                <div class="connection-title">🔗 数据库连接</div>
                <div class="connection-item">
                    <span class="connection-label">Host</span>
                    <span class="connection-value" id="conn-host">-</span>
                </div>
                <div class="connection-item">
                    <span class="connection-label">Port</span>
                    <span class="connection-value" id="conn-port">-</span>
                </div>
                <div class="connection-item">
                    <span class="connection-label">Database</span>
                    <span class="connection-value" id="conn-database">-</span>
                </div>
                <div class="connection-item">
                    <span class="connection-label">User</span>
                    <span class="connection-value" id="conn-user">-</span>
                </div>
                <div class="connection-item">
                    <span class="connection-label">Version</span>
                    <span class="connection-value" id="conn-version">-</span>
                </div>
                <div class="connection-status">
                    <div class="connection-dot" id="conn-dot"></div>
                    <span class="connection-status-text" id="conn-status-text">连接中...</span>
                </div>
            </div>
        </aside>

        <div class="terminal-area">
            <div class="output-container" id="output">
                <div class="banner-container">
                    <div class="banner-logo">SWAT SKILL</div>
                    <div class="banner-title">PostgreSQL 智能诊断</div>
                    <div class="banner-version">v1.9.4</div>
                </div>
            </div>

            <!-- Scroll to top button -->
            <div class="scroll-to-top" id="scroll-to-top" title="返回顶部">
                ↑
            </div>

            <div class="input-container">
                <!-- Output controls toolbar -->
                <div class="output-controls">
                    <div class="output-stats">
                        <span id="output-count">0 个输出</span>
                    </div>
                    <div class="output-actions">
                        <button class="output-btn active" id="auto-scroll-btn" title="自动滚动到底部">滚动</button>
                        <button class="output-btn" id="collapse-all-btn" title="折叠所有输出">折叠</button>
                        <button class="output-btn" id="expand-all-btn" title="展开所有输出">展开</button>
                        <button class="output-btn" id="clear-btn" title="清空输出">清屏</button>
                        <button class="output-btn" id="help-btn" title="显示帮助">帮助</button>
                    </div>
                </div>

                <div class="input-wrapper">
                    <span class="input-prompt">swat_skill&gt;</span>
                    <input type="text" id="command-input" placeholder="输入命令或 SQL..." autofocus autocomplete="off" spellcheck="false">
                </div>
            </div>
        </div>
    </main>

    <script>
        const outputEl = document.getElementById('output');
        const inputEl = document.getElementById('command-input');
        const statusEl = document.getElementById('connection-status');
        const badgeEl = document.getElementById('connection-badge');
        const skillListEl = document.querySelector('.sidebar-skills');  // Use parent container for all skill items
        const clearBtn = document.getElementById('clear-btn');
        const helpBtn = document.getElementById('help-btn');
        const autoScrollBtn = document.getElementById('auto-scroll-btn');
        const collapseAllBtn = document.getElementById('collapse-all-btn');
        const expandAllBtn = document.getElementById('expand-all-btn');
        const scrollToTopBtn = document.getElementById('scroll-to-top');
        const outputCountEl = document.getElementById('output-count');

        let ws = null;
        let sessionId = null;
        let commandHistory = [];
        let historyIndex = -1;
        let skillNames = [];
        let outputBlockCount = 0;
        let autoScroll = true;  // Auto scroll to bottom by default
        let MAX_OUTPUT_BLOCKS = 50;  // Max output blocks before warning

        // Initialize auto-scroll button
        autoScrollBtn.classList.add('active');

        // Skill list click handler
        skillListEl.addEventListener('click', (e) => {
            const item = e.target.closest('.skill-item');
            if (item) {
                const command = item.dataset.command;
                inputEl.value = command;
                inputEl.focus();
                // Mark active
                document.querySelectorAll('.skill-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            }
        });

        // Skill search functionality
        const skillSearchEl = document.getElementById('skill-search');
        const skillCountEl = document.getElementById('skill-count');

        skillSearchEl.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const items = document.querySelectorAll('.skill-item');
            const categories = document.querySelectorAll('.skill-category-group');
            let visibleCount = 0;

            items.forEach(item => {
                const command = item.dataset.command.toLowerCase();
                const searchTerms = (item.dataset.search || '').toLowerCase();
                const desc = item.querySelector('.skill-desc')?.textContent.toLowerCase() || '';

                const matches = query === '' ||
                    command.includes(query) ||
                    searchTerms.includes(query) ||
                    desc.includes(query);

                if (matches) {
                    item.classList.remove('hidden');
                    visibleCount++;
                } else {
                    item.classList.add('hidden');
                }
            });

            // Show/hide categories based on visible items
            categories.forEach(cat => {
                const visibleItems = cat.querySelectorAll('.skill-item:not(.hidden)');
                if (visibleItems.length === 0) {
                    cat.style.display = 'none';
                } else {
                    cat.style.display = 'block';
                }
            });

            skillCountEl.textContent = `${visibleCount} 个技能`;
        });

        // Auto scroll toggle
        autoScrollBtn.addEventListener('click', () => {
            autoScroll = !autoScroll;
            autoScrollBtn.classList.toggle('active', autoScroll);
            if (autoScroll) {
                scrollToBottom();
            }
        });

        // Collapse all output blocks
        collapseAllBtn.addEventListener('click', () => {
            document.querySelectorAll('.result-block.collapsible').forEach(block => {
                block.classList.add('collapsed');
                block.querySelector('.result-block-toggle').textContent = '展开';
            });
        });

        // Expand all output blocks
        expandAllBtn.addEventListener('click', () => {
            document.querySelectorAll('.result-block.collapsible').forEach(block => {
                block.classList.remove('collapsed');
                block.querySelector('.result-block-toggle').textContent = '折叠';
            });
        });

        // Clear button
        clearBtn.addEventListener('click', () => {
            outputBlockCount = 0;
            updateOutputCount();
            outputEl.innerHTML = `
                <div class="banner-container">
                    <div class="banner-logo">SWAT SKILL</div>
                    <div class="banner-title">PostgreSQL 智能诊断</div>
                    <div class="banner-version">v1.9.4</div>
                </div>
            `;
        });

        // Help button
        helpBtn.addEventListener('click', () => {
            sendCommand('/help');
        });

        // Scroll to top button visibility
        outputEl.addEventListener('scroll', () => {
            if (outputEl.scrollTop > 200) {
                scrollToTopBtn.classList.add('show');
            } else {
                scrollToTopBtn.classList.remove('show');
            }
        });

        // Scroll to top action
        scrollToTopBtn.addEventListener('click', () => {
            outputEl.scrollTo({ top: 0, behavior: 'smooth' });
        });

        // Update output count
        function updateOutputCount() {
            const countEl = document.getElementById('output-count');
            if (countEl) {
                countEl.textContent = `${outputBlockCount} 个输出`;
                if (outputBlockCount >= MAX_OUTPUT_BLOCKS) {
                    countEl.style.color = 'var(--accent-yellow)';
                } else {
                    countEl.style.color = '';
                }
            }
        }

        // Add collapsible block header
        function createCollapsibleBlock(title) {
            const block = document.createElement('div');
            block.className = 'result-block collapsible';
            block.dataset.index = outputBlockCount;

            const header = document.createElement('div');
            header.className = 'result-block-header';
            header.innerHTML = `
                <span class="result-block-title">${title}</span>
                <span class="result-block-toggle">折叠</span>
            `;
            header.addEventListener('click', () => {
                block.classList.toggle('collapsed');
                const toggle = block.querySelector('.result-block-toggle');
                toggle.textContent = block.classList.contains('collapsed') ? '展开' : '折叠';
            });

            const content = document.createElement('div');
            content.className = 'result-content';

            block.appendChild(header);
            block.appendChild(content);

            outputBlockCount++;
            updateOutputCount();

            return { block, content };
        }

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
                // Update sidebar connection status
                document.getElementById('conn-dot').className = 'connection-dot error';
                document.getElementById('conn-status-text').textContent = '连接错误';
                appendLine('WebSocket 连接错误', 'error');
            };

            ws.onclose = () => {
                statusEl.textContent = '已断开';
                badgeEl.className = 'connection-badge error';
                // Update sidebar connection status
                document.getElementById('conn-dot').className = 'connection-dot error';
                document.getElementById('conn-status-text').textContent = '已断开';
                appendLine('连接已关闭', 'warning');
            };
        }

        function handleResult(result) {
            switch (result.type) {
                case 'connected':
                    sessionId = result.session_id;
                    skillNames = result.skill_names || [];

                    // Update connection info in sidebar
                    const connDot = document.getElementById('conn-dot');
                    const connStatusText = document.getElementById('conn-status-text');

                    if (result.db_config) {
                        document.getElementById('conn-host').textContent = result.db_config.host || '-';
                        document.getElementById('conn-port').textContent = result.db_config.port || '-';
                        document.getElementById('conn-database').textContent = result.db_config.database || '-';
                        document.getElementById('conn-user').textContent = result.db_config.user || '-';
                    }

                    if (result.server_info && result.server_info.success) {
                        const info = result.server_info.info;
                        // Extract PostgreSQL version (e.g., "PostgreSQL 15.3")
                        const versionMatch = (info.version || '').match(/PostgreSQL\s+[\d.]+/i);
                        const version = versionMatch ? versionMatch[0] : 'PostgreSQL';
                        document.getElementById('conn-version').textContent = version;

                        // Update connection status
                        connDot.className = 'connection-dot connected';
                        connStatusText.textContent = '已连接';

                        appendLine(`✓ 已连接到 ${version}`, 'success');
                        addSeparator();
                    } else {
                        connDot.className = 'connection-dot error';
                        connStatusText.textContent = '连接失败';
                        document.getElementById('conn-version').textContent = '-';
                        appendLine('✗ 数据库连接失败', 'error');
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
                case 'dbtop_start':
                    // Clear output and show dbtop container for streaming updates
                    clearDbtopContainer();
                    appendLine(result.message, 'info');
                    break;
                case 'dbtop_update':
                    // Real-time streaming update - update the dbtop display
                    renderDbtopStreaming(result);
                    break;
                case 'dbtop_end':
                    appendLine(result.message, 'success');
                    addSeparator();
                    break;
                case 'dbtop':
                    renderDbtop(result);
                    break;
                default:
                    if (result.content) {
                        appendLine(result.content);
                        addSeparator();
                    }
            }
        }

        // dbtop streaming container reference
        let dbtopStreamingContainer = null;

        function clearDbtopContainer() {
            // Remove any existing streaming dbtop container
            if (dbtopStreamingContainer) {
                dbtopStreamingContainer.remove();
                dbtopStreamingContainer = null;
            }
        }

        function renderDbtopStreaming(result) {
            // Create or update streaming dbtop display
            if (!dbtopStreamingContainer) {
                dbtopStreamingContainer = document.createElement('div');
                dbtopStreamingContainer.className = 'result-block';
                outputEl.appendChild(dbtopStreamingContainer);
            }

            const data = result.data;
            const iteration = result.iteration;
            const total = result.total_iterations;

            // Build dbtop content
            dbtopStreamingContainer.innerHTML = buildDbtopHtml(data, iteration, total);
            scrollToBottom();
        }

        function buildDbtopHtml(data, iteration, total) {
            const db_activity = data.db_activity || {};
            const session_states = data.session_states || {};
            const sessions = data.sessions || [];
            const wait_events = data.wait_events || [];

            // Limit sessions to display (max 8 for compact view)
            const displaySessions = sessions.slice(0, 8);
            const hasMoreSessions = sessions.length > 8;

            let html = `
                <div class="dbtop-container">
                    <!-- Header: Title + Time + Iteration -->
                    <div class="dbtop-header">
                        <span class="dbtop-title">📊 dbtop</span>
                        <span class="dbtop-time">${data.timestamp || ''} | ${iteration}/${total}</span>
                    </div>

                    <!-- DB Activity: Single line metrics -->
                    <div class="dbtop-db-activity">
                        <span class="dbtop-activity-title">DB:</span>
                        <span class="dbtop-activity-item"><span class="dbtop-label">tps</span><span class="dbtop-value ${db_activity.tps > 100 ? 'warning' : ''}">${db_activity.tps || 0}</span></span>
                        <span class="dbtop-activity-item"><span class="dbtop-label">rb/s</span><span class="dbtop-value ${db_activity.rollbacks_ps > 0 ? 'warning' : ''}">${db_activity.rollbacks_ps || 0}</span></span>
                        <span class="dbtop-activity-item"><span class="dbtop-label">buf/s</span><span class="dbtop-value">${db_activity.buffer_reads_ps || 0}</span></span>
                        <span class="dbtop-activity-item"><span class="dbtop-label">hit%</span><span class="dbtop-value ${db_activity.buffer_hit_pct >= 90 ? 'success' : db_activity.buffer_hit_pct >= 70 ? '' : 'warning'}">${db_activity.buffer_hit_pct || 0}</span></span>
                        <span class="dbtop-activity-item"><span class="dbtop-label">r/s</span><span class="dbtop-value">${db_activity.row_reads_ps || 0}</span></span>
                        <span class="dbtop-activity-item"><span class="dbtop-label">w/s</span><span class="dbtop-value">${db_activity.row_writes_ps || 0}</span></span>
                    </div>

                    <!-- Session States: Single line -->
                    <div class="dbtop-states">
                        <span class="dbtop-states-label">Sessions:</span>
                        <span class="dbtop-states-value">${session_states.total || 0}</span>
                        <span class="dbtop-states-active">${session_states.active || 0} active</span>
                        <span class="dbtop-states-idle">${session_states.idle || 0} idle</span>
                        ${session_states.idle_tx > 0 ? `<span class="dbtop-states-idle-tx">${session_states.idle_tx} idle_tx</span>` : ''}
                    </div>
            `;

            // Sessions table - compact, max 8 rows
            if (displaySessions.length > 0) {
                html += `
                    <div class="dbtop-table-wrapper">
                        <table class="dbtop-table">
                            <tr>
                                <th style="width:50px">PID</th>
                                <th style="width:80px">User</th>
                                <th style="width:70px">State</th>
                                <th style="width:50px">Dur</th>
                                <th style="width:50px">Xact</th>
                                <th style="width:80px">Wait</th>
                                <th>Query</th>
                            </tr>
                `;
                displaySessions.forEach(row => {
                    const stateClass = row.State === 'active' ? 'state-active' :
                                       row.State === 'idle in transaction' ? 'state-idle-tx' : '';
                    // Shorten state name
                    const shortState = row.State === 'idle in transaction' ? 'idle_tx' :
                                       row.State === 'idle in transaction aborted' ? 'abort' :
                                       row.State || '';
                    html += `
                        <tr>
                            <td>${row.PID || ''}</td>
                            <td>${(row.User || '').substring(0, 8)}</td>
                            <td class="${stateClass}">${shortState.substring(0, 8)}</td>
                            <td>${row.Duration || '-'}</td>
                            <td>${row.Xact || '-'}</td>
                            <td>${(row.Wait || '-').substring(0, 10)}</td>
                            <td class="query-cell">${row.Query || ''}</td>
                        </tr>
                    `;
                });
                html += `</table></div>`;

                if (hasMoreSessions) {
                    html += `<div style="font-size:10px;color:var(--text-muted);padding:2px 8px">... 还有 ${sessions.length - 8} 个会话</div>`;
                }
            }

            // Wait Events: Single line at bottom
            if (wait_events.length > 0) {
                html += `
                    <div class="dbtop-wait-events">
                        <span style="color:var(--accent-yellow)">Wait:</span>
                        ${wait_events.slice(0, 5).map(e => `<span class="wait-event-item">${e.Event}(${e.Count})</span>`).join(' ')}
                        ${wait_events.length > 5 ? `<span style="color:var(--text-muted)">+${wait_events.length - 5} more</span>` : ''}
                    </div>
                `;
            }

            // Uptime at bottom
            if (data.uptime) {
                html += `<div class="dbtop-footer">Up: ${data.uptime}</div>`;
            }

            html += `</div>`;
            return html;
        }

        function renderTable(result) {
            if (!result.columns || !result.rows) {
                appendLine('无数据', 'info');
                addSeparator();
                return;
            }

            // Create collapsible block for large tables
            const isLarge = result.row_count > 20;
            const { block, content } = createCollapsibleBlock(
                `表格结果 (${result.row_count} 行, ${result.execution_time.toFixed(3)}s)`
            );

            // Collapse large tables by default
            if (isLarge) {
                block.classList.add('collapsed');
                block.querySelector('.result-block-toggle').textContent = '展开';
            }

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

            // Rows - limit display for large tables
            const displayRows = isLarge ? result.rows.slice(0, 20) : result.rows;
            displayRows.forEach(row => {
                const tr = table.insertRow();
                result.columns.forEach(col => {
                    const td = tr.insertCell();
                    const value = row[col];
                    td.textContent = value !== null && value !== undefined ? String(value) : '';
                });
            });

            wrapper.appendChild(table);
            content.appendChild(wrapper);

            // Add expand button for large tables
            if (isLarge) {
                const expandBtn = document.createElement('div');
                expandBtn.className = 'table-expand-btn';
                expandBtn.textContent = `点击展开查看全部 ${result.row_count} 行 (当前显示前 20 行)`;
                expandBtn.addEventListener('click', () => {
                    wrapper.classList.toggle('expanded');
                    if (wrapper.classList.contains('expanded')) {
                        // Add remaining rows
                        const remainingRows = result.rows.slice(20);
                        remainingRows.forEach(row => {
                            const tr = table.insertRow();
                            result.columns.forEach(col => {
                                const td = tr.insertCell();
                                const value = row[col];
                                td.textContent = value !== null && value !== undefined ? String(value) : '';
                            });
                        });
                        expandBtn.textContent = '折叠表格';
                    } else {
                        expandBtn.textContent = `点击展开查看全部 ${result.row_count} 行`;
                    }
                });
                content.appendChild(expandBtn);
            }

            // Row count footer
            const footer = document.createElement('div');
            footer.className = 'row-count';
            footer.innerHTML = `
                <span>${result.row_count} 行结果</span>
                <span class="execution-time">${result.execution_time.toFixed(3)}s</span>
            `;
            content.appendChild(footer);

            outputEl.appendChild(block);
            addSeparator();
            scrollToBottom();
        }

        function renderHealth(result) {
            const { block, content } = createCollapsibleBlock(
                `健康报告 (${result.overall === 'ok' ? '✓ 健康' : result.overall === 'warning' ? '⚠ 警告' : '✗ 异常'})`
            );

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

            content.appendChild(container);
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

        function renderDbtop(result) {
            const block = document.createElement('div');
            block.className = 'result-block';

            const container = document.createElement('div');
            container.className = 'dbtop-container';

            // Header
            const header = document.createElement('div');
            header.className = 'dbtop-header';
            header.innerHTML = `
                <span class="dbtop-title">📊 Database Top</span>
                <span class="dbtop-time">${result.timestamp || ''}</span>
            `;
            container.appendChild(header);

            // Summary section
            const summary = result.summary || {};
            const summaryDiv = document.createElement('div');
            summaryDiv.className = 'dbtop-summary';
            summaryDiv.innerHTML = `
                <div class="dbtop-summary-item">
                    <span class="label">活跃会话</span>
                    <span class="value">${summary.active_sessions || 0}</span>
                </div>
                <div class="dbtop-summary-item">
                    <span class="label">连接数</span>
                    <span class="value">${summary.connections || '0/0'}</span>
                </div>
                <div class="dbtop-summary-item">
                    <span class="label">缓存命中率</span>
                    <span class="value">${summary.cache_hit_ratio || 0}%</span>
                </div>
                <div class="dbtop-summary-item">
                    <span class="label">事务提交</span>
                    <span class="value">${summary.xact_commit || 0}</span>
                </div>
                <div class="dbtop-summary-item">
                    <span class="label">事务回滚</span>
                    <span class="value">${summary.xact_rollback || 0}</span>
                </div>
            `;
            container.appendChild(summaryDiv);

            // Sessions table
            if (result.sessions && result.sessions.length > 0) {
                const sessionsTitle = document.createElement('div');
                sessionsTitle.className = 'dbtop-section-title';
                sessionsTitle.textContent = '活跃会话';
                container.appendChild(sessionsTitle);

                const tableWrapper = document.createElement('div');
                tableWrapper.className = 'result-table-wrapper';

                const table = document.createElement('table');
                table.className = 'result-table';

                const headerRow = table.insertRow();
                ['PID', 'User', 'State', 'Duration', 'Wait', 'Query'].forEach(col => {
                    const th = document.createElement('th');
                    th.textContent = col;
                    headerRow.appendChild(th);
                });

                result.sessions.forEach(row => {
                    const tr = table.insertRow();
                    ['PID', 'User', 'State', 'Duration', 'Wait', 'Query'].forEach(col => {
                        const td = tr.insertCell();
                        td.textContent = row[col] || '';
                    });
                });

                tableWrapper.appendChild(table);
                container.appendChild(tableWrapper);
            }

            // Wait events table
            if (result.wait_events && result.wait_events.length > 0) {
                const waitTitle = document.createElement('div');
                waitTitle.className = 'dbtop-section-title';
                waitTitle.textContent = '等待事件';
                container.appendChild(waitTitle);

                const tableWrapper = document.createElement('div');
                tableWrapper.className = 'result-table-wrapper';

                const table = document.createElement('table');
                table.className = 'result-table';

                const headerRow = table.insertRow();
                ['Type', 'Event', 'Count'].forEach(col => {
                    const th = document.createElement('th');
                    th.textContent = col;
                    headerRow.appendChild(th);
                });

                result.wait_events.forEach(row => {
                    const tr = table.insertRow();
                    ['Type', 'Event', 'Count'].forEach(col => {
                        const td = tr.insertCell();
                        td.textContent = row[col] || '';
                    });
                });

                tableWrapper.appendChild(table);
                container.appendChild(tableWrapper);
            }

            // Footer
            const footer = document.createElement('div');
            footer.className = 'dbtop-footer';
            footer.textContent = `共 ${result.snapshots || 1} 次采样`;
            container.appendChild(footer);

            block.appendChild(container);
            outputEl.appendChild(block);
            addSeparator();
            scrollToBottom();
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
            if (autoScroll) {
                outputEl.scrollTop = outputEl.scrollHeight;
            }
        }

        function sendCommand(command) {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                appendLine('未连接', 'error');
                return;
            }

            // Show command in output with timestamp
            const cmdBlock = document.createElement('div');
            cmdBlock.className = 'output-line command';
            const timestamp = new Date().toLocaleTimeString();
            cmdBlock.innerHTML = `
                <span class="prompt">swat_skill&gt;</span>
                <span style="color: var(--text-primary)">${command}</span>
                <span style="color: var(--text-muted); font-size: 11px; margin-left: 8px">${timestamp}</span>
            `;
            outputEl.appendChild(cmdBlock);

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
        "version": "1.6.0",
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