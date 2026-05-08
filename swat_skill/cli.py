"""CLI entry point and interactive interface.

Provides the main interactive loop for swat_skill.
"""

import sys
import os

# Handle both package import and standalone execution
if __name__ == "__main__" and not __package__:
    # Running as standalone script (PyInstaller bundled)
    # Add parent directory to path for imports
    import importlib.util
    import pathlib

    # When running from PyInstaller, modules are in _internal
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle
        bundle_dir = sys._MEIPASS
        sys.path.insert(0, bundle_dir)

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings


# Custom style for prompt
PROMPT_STYLE = Style.from_dict({
    "prompt": "ansicyan bold",
    "": "ansidefault",
})


def _get_imports():
    """Get imports when running as main."""
    from swat_skill.config import Config, load_config, save_config, find_config_file
    from swat_skill.database.connection import ConnectionManager, create_connection_manager
    from swat_skill.database.queries import SQL_KEYWORDS
    from swat_skill.dispatcher.router import Dispatcher
    from swat_skill.llm.agent import LLMAgent, create_llm_agent
    from swat_skill.skills.base import SkillResult, SkillRegistry
    from swat_skill.utils.formatter import Formatter, get_formatter
    return {
        "Config": Config,
        "load_config": load_config,
        "save_config": save_config,
        "create_connection_manager": create_connection_manager,
        "SQL_KEYWORDS": SQL_KEYWORDS,
        "Dispatcher": Dispatcher,
        "create_llm_agent": create_llm_agent,
        "get_formatter": get_formatter,
    }


# Import for package usage
try:
    from .config import Config, load_config, save_config
    from .database.connection import ConnectionManager, create_connection_manager
    from .database.queries import SQL_KEYWORDS
    from .dispatcher.router import Dispatcher
    from .llm.agent import LLMAgent, create_llm_agent
    from .skills.base import SkillResult, SkillRegistry
    from .utils.formatter import Formatter, get_formatter
except ImportError:
    # Fallback for standalone execution
    from swat_skill.config import Config, load_config, save_config
    from swat_skill.database.connection import ConnectionManager, create_connection_manager
    from swat_skill.database.queries import SQL_KEYWORDS
    from swat_skill.dispatcher.router import Dispatcher
    from swat_skill.llm.agent import LLMAgent, create_llm_agent
    from swat_skill.skills.base import SkillResult, SkillRegistry
    from swat_skill.utils.formatter import Formatter, get_formatter


def create_completer(dispatcher: Dispatcher) -> WordCompleter:
    """Create word completer with skill names and SQL keywords."""
    words = dispatcher.get_skill_names() + SQL_KEYWORDS
    return WordCompleter(words, ignore_case=True)


def run_interactive(config: Config) -> None:
    """Run interactive CLI session."""
    # Initialize components
    formatter = get_formatter(config.display.theme, config.display.table_style)

    # Print welcome banner
    formatter.print_welcome()

    # Connect to database
    try:
        conn = create_connection_manager(config.database)
        server_info = conn.get_server_info()
        formatter.print_info(f"Connected to: {server_info.get('version', 'Unknown')}")
    except Exception as e:
        formatter.print_error(f"Failed to connect to database: {e}")
        return

    # Create dispatcher
    dispatcher = Dispatcher(conn, config, formatter)

    # Create LLM agent if configured
    llm_agent = None
    if config.llm.get_api_key():
        try:
            llm_agent = create_llm_agent(conn, config.llm)
        except Exception as e:
            formatter.print_error(f"Failed to initialize LLM: {e}")

    # Setup prompt session
    history_file = os.path.expanduser("~/.swat_skill/history")
    os.makedirs(os.path.dirname(history_file), exist_ok=True)

    session = PromptSession(
        history=FileHistory(history_file),
        auto_suggest=AutoSuggestFromHistory(),
        completer=create_completer(dispatcher),
        style=PROMPT_STYLE,
    )

    # Main loop
    while True:
        try:
            user_input = session.prompt("swat_skill> ", style=PROMPT_STYLE)

            if not user_input.strip():
                continue

            # Dispatch input
            result, skill = dispatcher.dispatch(user_input)

            # Handle result based on type
            if result.result_type == "empty":
                continue

            elif result.result_type == "exit":
                formatter.print_success(result.message or "Goodbye!")
                conn.disconnect()
                break

            elif result.result_type == "llm":
                # Handle LLM request
                if llm_agent:
                    question = result.data.get("question", "")
                    formatter.print_info("Starting LLM diagnosis...")
                    try:
                        diagnosis = llm_agent.diagnose(question)
                        formatter.console.print(diagnosis)
                    except Exception as e:
                        formatter.print_error(f"LLM diagnosis failed: {e}")
                else:
                    formatter.print_error("LLM not configured. Set ANTHROPIC_API_KEY environment variable.")

            elif result.result_type == "health":
                # Health report
                items = result.data.get("items", [])
                overall = result.data.get("overall", "ok")
                formatter.print_health_report(items, "Database Health", overall)

            elif result.result_type == "table":
                # Table output
                if result.success:
                    formatter.print_table(result.data)
                    if result.execution_time:
                        formatter.console.print(
                            f"[dim]{len(result.data)} rows, {result.execution_time:.3f}s[/dim]"
                        )
                else:
                    formatter.print_error(result.error or "Unknown error")

            elif result.result_type == "text":
                # Text output
                if result.success:
                    if result.message:
                        formatter.print_success(result.message)
                    elif result.data:
                        formatter.console.print(result.data)
                else:
                    formatter.print_error(result.error or "Unknown error")

            else:
                # Default handling
                if result.success:
                    if result.data:
                        formatter.console.print(result.data)
                else:
                    formatter.print_error(result.error or "Unknown error")

        except KeyboardInterrupt:
            # Ctrl+C: continue
            formatter.console.print("\n[dim]Interrupted. Press Ctrl+D to exit.[/dim]")
            continue

        except EOFError:
            # Ctrl+D: exit
            formatter.print_success("Goodbye!")
            conn.disconnect()
            break

        except Exception as e:
            formatter.print_error(f"Error: {e}")


def run_setup() -> None:
    """Run initial setup wizard."""
    formatter = get_formatter()

    formatter.print_info("swat_skill Setup Wizard")
    formatter.console.print("")

    # Database configuration
    formatter.console.print("[bold]Database Configuration[/bold]")

    host = input("Host [localhost]: ") or "localhost"
    port = input("Port [5432]: ") or "5432"
    database = input("Database [postgres]: ") or "postgres"
    user = input("User [postgres]: ") or "postgres"
    password = input("Password: ")

    config = Config()
    config.database.host = host
    config.database.port = int(port)
    config.database.database = database
    config.database.user = user
    config.database.password = password

    # LLM configuration
    formatter.console.print("\n[bold]LLM Configuration[/bold]")

    llm_choice = input("Enable LLM diagnostics? [y/N]: ").lower()
    if llm_choice == "y":
        provider = input("Provider [anthropic]: ") or "anthropic"
        model = input("Model [claude-sonnet-4-6]: ") or "claude-sonnet-4-6"
        api_key = input("API Key (or press Enter to use environment variable): ")

        config.llm.provider = provider
        config.llm.model = model
        if api_key:
            config.llm.api_key = api_key

    # Save configuration
    config_path = os.path.expanduser("~/.swat_skill/config.yaml")
    save_config(config, config_path)
    formatter.print_success(f"Configuration saved to {config_path}")

    # Test connection
    formatter.console.print("\nTesting database connection...")
    try:
        conn = create_connection_manager(config.database)
        server_info = conn.get_server_info()
        formatter.print_success(f"Connected to PostgreSQL {server_info.get('version', '')}")
        conn.disconnect()
    except Exception as e:
        formatter.print_error(f"Connection failed: {e}")
        formatter.print_info("You can modify the configuration with: swat_skill configure")


def run_configure() -> None:
    """Run configuration editor."""
    config = load_config()
    run_setup()


def run_web(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Run web interface."""
    formatter = get_formatter()
    formatter.print_info(f"Starting swat_skill Web Server on {host}:{port}")
    formatter.console.print(f"[dim]Open http://localhost:{port} in your browser[/dim]")

    try:
        from .web.server import run_web_server
        run_web_server(host, port)
    except ImportError as e:
        formatter.print_error(f"Web dependencies not installed: {e}")
        formatter.print_info("Install with: pip install swat_skill[web]")
    except Exception as e:
        formatter.print_error(f"Failed to start web server: {e}")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="swat_skill - PostgreSQL Database CLI Agent"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["setup", "configure", "run", "web"],
        default="run",
        help="Command to run",
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Configuration file path",
    )
    parser.add_argument(
        "--host",
        help="Database host (or web server host for 'web' command)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Database port (or web server port for 'web' command)",
    )
    parser.add_argument(
        "--database",
        "-d",
        help="Database name",
    )
    parser.add_argument(
        "--user",
        "-u",
        help="Database user",
    )

    args = parser.parse_args()

    if args.command == "setup":
        run_setup()
        return

    if args.command == "configure":
        run_configure()
        return

    if args.command == "web":
        web_host = args.host or "0.0.0.0"
        web_port = args.port or 8080
        run_web(web_host, web_port)
        return

    # Load configuration
    config = load_config(args.config)

    # Override with command line arguments
    if args.host:
        config.database.host = args.host
    if args.port:
        config.database.port = args.port
    if args.database:
        config.database.database = args.database
    if args.user:
        config.database.user = args.user

    # Check if database is configured
    if not config.database.host:
        formatter = get_formatter()
        formatter.print_error("Database not configured. Run: swat_skill setup")
        return

    # Run interactive session
    run_interactive(config)


if __name__ == "__main__":
    main()