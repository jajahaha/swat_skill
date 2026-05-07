"""Test configuration management."""

import os
import tempfile
import pytest

from swat_skill.config import (
    Config,
    DatabaseConfig,
    LLMConfig,
    DisplayConfig,
    load_config,
    save_config,
)


class TestDatabaseConfig:
    """Test DatabaseConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DatabaseConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "postgres"
        assert config.user == "postgres"
        assert config.password == ""
        assert config.ssl_mode == "prefer"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = DatabaseConfig(
            host="192.168.1.100",
            port=5433,
            database="mydb",
            user="myuser",
            password="mypassword",
            ssl_mode="require",
        )
        assert config.host == "192.168.1.100"
        assert config.port == 5433
        assert config.database == "mydb"
        assert config.user == "myuser"
        assert config.password == "mypassword"
        assert config.ssl_mode == "require"

    def test_get_connection_info(self):
        """Test connection info dict."""
        config = DatabaseConfig(host="localhost", port=5432)
        info = config.get_connection_info()
        assert info["host"] == "localhost"
        assert info["port"] == 5432
        assert info["dbname"] == "postgres"

    def test_get_connection_string(self):
        """Test connection string generation."""
        config = DatabaseConfig(host="localhost", port=5432)
        conn_str = config.get_connection_string()
        assert "host=localhost" in conn_str
        assert "port=5432" in conn_str


class TestLLMConfig:
    """Test LLMConfig class."""

    def test_default_values(self):
        """Test default LLM configuration."""
        config = LLMConfig()
        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-6"
        assert config.max_tokens == 4096
        assert config.max_turns == 20

    def test_get_api_key_from_config(self):
        """Test API key from config."""
        config = LLMConfig(api_key="test-key")
        assert config.get_api_key() == "test-key"

    def test_get_api_key_from_env_anthropic(self):
        """Test API key from environment variable for Anthropic."""
        os.environ["ANTHROPIC_API_KEY"] = "env-test-key"
        config = LLMConfig(provider="anthropic")
        assert config.get_api_key() == "env-test-key"
        del os.environ["ANTHROPIC_API_KEY"]

    def test_get_api_key_from_env_openai(self):
        """Test API key from environment variable for OpenAI."""
        os.environ["OPENAI_API_KEY"] = "openai-test-key"
        config = LLMConfig(provider="openai")
        assert config.get_api_key() == "openai-test-key"
        del os.environ["OPENAI_API_KEY"]


class TestConfig:
    """Test main Config class."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.database.host == "localhost"
        assert config.llm.provider == "anthropic"

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "database": {"host": "testhost", "port": 5434},
            "llm": {"provider": "openai"},
            "display": {"theme": "light"},
        }
        config = Config.from_dict(data)
        assert config.database.host == "testhost"
        assert config.database.port == 5434
        assert config.llm.provider == "openai"
        assert config.display.theme == "light"

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config(
            database=DatabaseConfig(host="testhost"),
            llm=LLMConfig(provider="openai"),
        )
        data = config.to_dict()
        assert data["database"]["host"] == "testhost"
        assert data["llm"]["provider"] == "openai"


class TestLoadSaveConfig:
    """Test config file loading and saving."""

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            config = Config(
                database=DatabaseConfig(host="myhost", port=5435),
                llm=LLMConfig(provider="openai", model="gpt-4"),
            )
            save_config(config, temp_path)

            loaded = load_config(temp_path)
            assert loaded.database.host == "myhost"
            assert loaded.database.port == 5435
            assert loaded.llm.provider == "openai"
            assert loaded.llm.model == "gpt-4"
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test loading non-existent config file."""
        config = load_config("/nonexistent/path/config.yaml")
        # Should return default config
        assert config.database.host == "localhost"
        assert config.llm.provider == "anthropic"