"""LLM Agent for intelligent database diagnostics.

Uses Claude API with function calling for multi-round reasoning.
"""

import time
from typing import Any, Dict, List, Optional

import anthropic

from ..config import Config, LLMConfig
from ..database.connection import ConnectionManager
from ..database.queries import get_query
from ..skills.base import SkillResult
from .tools import build_tools, execute_tool


# System prompt for LLM agent
SYSTEM_PROMPT = """You are an expert PostgreSQL database diagnostic agent. Your role is to analyze database issues and provide actionable recommendations.

Key principles:
1. Always base conclusions on actual data from tool calls - never guess or halluciate
2. When diagnosing, start with broad checks then drill down to specific issues
3. Provide concrete, executable SQL commands for fixes when possible
4. Prioritize issues by severity and impact
5. Explain your reasoning step by step

Available diagnostic tools:
- query_health: Get overall health status
- query_sessions: Get active sessions
- query_waits: Get wait events
- query_locks: Get lock information
- query_space: Get space usage
- query_slowsql: Get slow SQL (requires pg_stat_statements)
- execute_sql: Run custom SQL query
- get_server_info: Get PostgreSQL version and info

When asked to diagnose, follow this pattern:
1. First call query_health to get overview
2. Based on findings, call appropriate specific tools
3. Analyze results and form hypothesis
4. If needed, call execute_sql for additional data
5. Summarize findings with root cause and recommendations

Remember: You must always verify data exists before suggesting fixes. Never recommend dropping or altering objects without first checking they exist."""


class LLMAgent:
    """LLM-powered diagnostic agent."""

    def __init__(
        self,
        conn: ConnectionManager,
        config: LLMConfig,
    ):
        self.conn = conn
        self.config = config
        self.client: Optional[anthropic.Anthropic] = None
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.max_turns = config.max_turns
        self.tools = build_tools()

    def _init_client(self) -> None:
        """Initialize Anthropic client."""
        api_key = self.config.get_api_key()
        if not api_key:
            raise ValueError("No API key available. Set ANTHROPIC_API_KEY environment variable.")

        self.client = anthropic.Anthropic(api_key=api_key)

    def diagnose(self, question: str) -> str:
        """Run multi-round diagnostic reasoning.

        Args:
            question: User's diagnostic question.

        Returns:
            Diagnostic report as formatted text.
        """
        if not self.client:
            self._init_client()

        messages: List[Dict] = [{"role": "user", "content": question}]
        evidence: List[Dict] = []
        start_time = time.time()

        for turn in range(self.max_turns):
            # Add convergence hint for last 2 turns
            if turn >= self.max_turns - 2:
                system_prompt = SYSTEM_PROMPT + "\n\nThis is one of your final turns. Please start summarizing your findings and provide a clear diagnosis."
            else:
                system_prompt = SYSTEM_PROMPT

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    tools=self.tools,
                    messages=messages,
                )
            except anthropic.APIError as e:
                return f"LLM API error: {str(e)}"

            # Check if LLM finished reasoning
            if response.stop_reason == "end_turn":
                # Extract text response
                text_content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text_content += block.text

                elapsed_time = time.time() - start_time
                return self._format_report(text_content, evidence, turn + 1, elapsed_time)

            # Process tool calls
            assistant_message = {"role": "assistant", "content": []}
            user_message = {"role": "user", "content": []}

            for block in response.content:
                if block.type == "tool_use":
                    # Execute tool
                    tool_name = block.name
                    tool_input = block.input
                    tool_result = execute_tool(self.conn, tool_name, tool_input)

                    # Track evidence
                    evidence.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": tool_result,
                    })

                    # Build messages for next turn
                    assistant_message["content"].append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": tool_name,
                        "input": tool_input,
                    })

                    user_message["content"].append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(tool_result),
                    })

                elif hasattr(block, "text"):
                    assistant_message["content"].append({
                        "type": "text",
                        "text": block.text,
                    })

            messages.append(assistant_message)
            messages.append(user_message)

        # Timeout: force summary
        elapsed_time = time.time() - start_time
        return self._format_timeout_response(evidence, self.max_turns, elapsed_time)

    def _format_report(
        self,
        text_content: str,
        evidence: List[Dict],
        turns: int,
        elapsed_time: float,
    ) -> str:
        """Format diagnostic report."""
        report = f"LLM诊断完成 ({turns}轮推理, {elapsed_time:.1f}秒)\n\n"
        report += text_content

        if evidence:
            report += "\n\n--- 证据链 ---\n"
            for i, e in enumerate(evidence, 1):
                report += f"{i}. {e['tool']}: {e['result'][:100]}...\n"

        return report

    def _format_timeout_response(
        self,
        evidence: List[Dict],
        turns: int,
        elapsed_time: float,
    ) -> str:
        """Format timeout response."""
        report = f"LLM诊断超时 ({turns}轮推理, {elapsed_time:.1f}秒)\n\n"
        report += "未能完成完整诊断。已收集的证据：\n"

        for i, e in enumerate(evidence, 1):
            report += f"{i}. {e['tool']}: {str(e['result'])[:200]}...\n"

        report += "\n建议使用 /health 或 /rule 命令获取确定性诊断。"
        return report


def create_llm_agent(conn: ConnectionManager, config: LLMConfig) -> LLMAgent:
    """Create LLM agent instance."""
    return LLMAgent(conn, config)