"""Output formatting utilities.

Provides table formatting and report generation using rich library.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.style import Style
from rich import box


@dataclass
class HealthItem:
    """Single health check item."""

    category: str
    name: str
    value: str
    status: str  # "ok", "warning", "critical"
    tip: Optional[str] = None


# SWAT SKILL banner using pyfiglet bulbhead font (white-filled letters)
SWAT_SKILL_BANNER = r"""
 ___  _    _    __   ____    ___  _  _  ____  __    __
/ __)( \/\/ )  /__\ (_  _)  / __)( )/ )(_  _)(  )  (  )
\__ \ )    (  /(__)\  )(    \__ \ )  (  _)(_  )(__  )(__
(___/(__/\__)(__)(__)(__)   (___/(_)\_)(____)(____)(____)
"""


class Formatter:
    """Output formatter for swat_skill CLI."""

    def __init__(self, theme: str = "dark", table_style: str = "rounded"):
        self.console = Console()
        self.theme = theme
        self.table_style = table_style

    def format_table(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
        show_header: bool = True,
    ) -> Table:
        """Format data as a rich table."""
        if not data:
            return Table(title=title or "No data")

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        # Choose box style
        box_styles = {
            "plain": None,
            "simple": box.SIMPLE,
            "rounded": box.ROUNDED,
            "double": box.DOUBLE,
        }
        box_style = box_styles.get(self.table_style, box.ROUNDED)

        table = Table(
            title=title,
            box=box_style,
            show_header=show_header,
            header_style="bold cyan",
        )

        # Add columns
        for col in columns:
            table.add_column(col)

        # Add rows
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])

        return table

    def print_table(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
    ) -> None:
        """Print formatted table to console."""
        table = self.format_table(data, columns, title)
        self.console.print(table)

    def format_health_report(
        self,
        items: List[HealthItem],
        title: str = "Database Health",
        overall_status: str = "ok",
    ) -> Panel:
        """Format health check report."""
        # Status symbols
        status_symbols = {
            "ok": "[green]✓[/green]",
            "warning": "[yellow]⚠[/yellow]",
            "critical": "[red]✗[/red]",
        }

        # Build content
        lines = []

        # Overall status
        overall_symbol = status_symbols.get(overall_status, "?")
        lines.append(f"Overall: {overall_symbol} {overall_status.upper()}")

        # Group by category
        categories = {}
        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        # Format each category
        for category, cat_items in categories.items():
            lines.append("")
            lines.append(f"[bold]{category}[/bold]")
            for item in cat_items:
                symbol = status_symbols.get(item.status, "?")
                line = f"  {item.name}: {item.value} {symbol}"
                lines.append(line)

        # Add tips for warnings/criticals
        alerts = [i for i in items if i.status in ("warning", "critical") and i.tip]
        if alerts:
            lines.append("")
            lines.append("[bold]Alerts[/bold]")
            for item in alerts:
                symbol = status_symbols.get(item.status, "?")
                lines.append(f"  {symbol} {item.name}: {item.tip}")

        return Panel("\n".join(lines), title=title, border_style="cyan")

    def print_health_report(
        self,
        items: List[HealthItem],
        title: str = "Database Health",
        overall_status: str = "ok",
    ) -> None:
        """Print health report to console."""
        panel = self.format_health_report(items, title, overall_status)
        self.console.print(panel)

    def format_error(self, error: str) -> Panel:
        """Format error message."""
        return Panel(error, title="Error", border_style="red")

    def print_error(self, error: str) -> None:
        """Print error to console."""
        self.console.print(self.format_error(error))

    def format_success(self, message: str) -> Panel:
        """Format success message."""
        return Panel(message, title="Success", border_style="green")

    def print_success(self, message: str) -> None:
        """Print success message to console."""
        self.console.print(self.format_success(message))

    def format_info(self, message: str) -> Panel:
        """Format info message."""
        return Panel(message, title="Info", border_style="blue")

    def print_info(self, message: str) -> None:
        """Print info message to console."""
        self.console.print(self.format_info(message))

    def format_sql_result(
        self,
        rows: List[Dict[str, Any]],
        columns: List[str],
        execution_time: float,
    ) -> str:
        """Format SQL query result."""
        if not rows:
            return "No rows returned"

        table = self.format_table(rows, columns)
        result = f"{table}\n"
        result += f"[dim]{len(rows)} rows, {execution_time:.3f}s[/dim]"
        return result

    def print_sql_result(
        self,
        rows: List[Dict[str, Any]],
        columns: List[str],
        execution_time: float,
    ) -> None:
        """Print SQL query result."""
        self.print_table(rows, columns)
        self.console.print(f"[dim]{len(rows)} rows, {execution_time:.3f}s[/dim]")

    def print_welcome(self) -> None:
        """Print welcome message with SWAT SKILL banner."""
        self.console.print(Panel(SWAT_SKILL_BANNER, border_style="cyan"))
        self.console.print("[bold]PostgreSQL Database CLI Agent[/bold]")
        self.console.print("[dim]Type /help for available commands[/dim]")

    def clear(self) -> None:
        """Clear console."""
        self.console.clear()


def get_formatter(theme: str = "dark", table_style: str = "rounded") -> Formatter:
    """Get formatter instance."""
    return Formatter(theme, table_style)