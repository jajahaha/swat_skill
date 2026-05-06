"""Configuration management for swat_skill.

Supports YAML configuration files with database and LLM settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class DatabaseConfig:
    """PostgreSQL connection configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: str = ""
    ssl_mode: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full

    def get_connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.database}",
            f"user={self.user}",
        ]
        if self.password:
            parts.append(f"password={self.password}")
        if self.ssl_mode != "disable":
            parts.append(f"sslmode={self.ssl_mode}")
        return " ".join(parts)

    def get_connection_info(self) -> dict:
        """Return connection parameters as dict for psycopg."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password if self.password else None,
            "sslmode": self.ssl_mode,
        }


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    provider: str = "anthropic"  # anthropic | openai
    model: str = "claude-sonnet-4-6"
    api_key: Optional[str] = None
    max_tokens: int = 4096
    max_turns: int = 20

    def get_api_key(self) -> Optional[str]:
        """Get API key from config or environment variable."""
        if self.api_key:
            return self.api_key
        if self.provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY")
        elif self.provider == "openai":
            return os.environ.get("OPENAI_API_KEY")
        return None


@dataclass
class DisplayConfig:
    """Display and formatting configuration."""

    theme: str = "dark"
    table_style: str = "rounded"  # plain, simple, rounded, double


@dataclass
class Config:
    """Main configuration container."""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    config_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict, config_path: Optional[str] = None) -> "Config":
        """Create Config from dictionary."""
        db_data = data.get("database", {})
        llm_data = data.get("llm", {})
        display_data = data.get("display", {})

        return cls(
            database=DatabaseConfig(**db_data),
            llm=LLMConfig(**llm_data),
            display=DisplayConfig(**display_data),
            config_path=config_path,
        )

    def to_dict(self) -> dict:
        """Convert Config to dictionary."""
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "user": self.database.user,
                "password": self.database.password,
                "ssl_mode": self.database.ssl_mode,
            },
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "api_key": self.llm.api_key or "",
                "max_tokens": self.llm.max_tokens,
                "max_turns": self.llm.max_turns,
            },
            "display": {
                "theme": self.display.theme,
                "table_style": self.display.table_style,
            },
        }


DEFAULT_CONFIG_PATHS = [
    Path.home() / ".swat_skill" / "config.yaml",
    Path.home() / ".config" / "swat_skill" / "config.yaml",
    Path("config.yaml"),
]


def find_config_file() -> Optional[Path]:
    """Find configuration file in default locations."""
    for path in DEFAULT_CONFIG_PATHS:
        if path.exists():
            return path
    return None


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file.

    Args:
        config_path: Optional explicit path to config file.
                    If not provided, searches default locations.

    Returns:
        Config object with loaded settings.
    """
    if config_path:
        path = Path(config_path)
    else:
        path = find_config_file()

    if path and path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return Config.from_dict(data, str(path))

    # Return default config if no file found
    return Config()


def save_config(config: Config, config_path: Optional[str] = None) -> None:
    """Save configuration to file.

    Args:
        config: Config object to save.
        config_path: Optional explicit path. If not provided,
                    uses config.config_path or default location.
    """
    if config_path:
        path = Path(config_path)
    elif config.config_path:
        path = Path(config.config_path)
    else:
        # Use default location
        path = Path.home() / ".swat_skill" / "config.yaml"

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)


def create_default_config() -> Config:
    """Create and save default configuration."""
    config = Config()
    save_config(config)
    return config