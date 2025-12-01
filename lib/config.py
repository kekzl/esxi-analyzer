"""
Configuration management for ESXi Analyzer.

This module handles loading and accessing configuration settings from config.yaml
"""

from pathlib import Path
from typing import Any, ClassVar, Optional

import yaml


class Config:
    """Configuration manager for ESXi Analyzer."""

    _instance: ClassVar[Optional["Config"]] = None
    _config: ClassVar[dict[str, Any]] = {}

    def __new__(cls) -> "Config":
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str | None = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml file. If None, looks in standard locations.
        """
        if not self._config:  # Only load once
            self._load_config(config_path)

    def _load_config(self, config_path: str | None = None) -> None:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml file.
        """
        if config_path is None:
            # Try standard locations
            possible_paths = [
                Path(__file__).parent.parent / "config.yaml",
                Path.home() / ".esxi-analyzer" / "config.yaml",
                Path("/etc/esxi-analyzer/config.yaml"),
            ]

            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break

        config_file = Path(config_path) if config_path else None
        if config_file and config_file.exists():
            try:
                self._config = yaml.safe_load(config_file.read_text()) or {}
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")
                self._load_defaults()
        else:
            print("Warning: No config file found, using defaults")
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = {
            "thresholds": {
                "high_latency_ms": 20.0,
                "low_datastore_space_percent": 10,
                "high_cpu_percent": 80,
                "high_memory_percent": 90,
                "max_uptime_days": 180,
                "max_snapshot_age_days": 3,
                "min_network_redundancy": 2,
            },
            "ssh": {
                "timeout": 30,
                "command_timeout": 60,
                "retry_attempts": 3,
                "retry_delay": 2,
                "verify_host_keys": True,
                "known_hosts_file": "~/.ssh/known_hosts",
                "use_key_auth": False,
                "key_file": "~/.ssh/id_rsa",
            },
            "web": {
                "port": 8080,
                "host": "0.0.0.0",
            },
            "logging": {
                "level": "INFO",
                "log_file": "esxi_analyzer.log",
                "max_bytes": 10485760,
                "backup_count": 5,
            },
            "report": {
                "auto_open_browser": True,
                "include_raw_data": False,
            },
            "kb_articles": {
                "psod": "https://kb.vmware.com/s/article/1004250",
                "storage_latency": "https://kb.vmware.com/s/article/1021244",
                "memory_errors": "https://kb.vmware.com/s/article/2146954",
                "high_cpu": "https://kb.vmware.com/s/article/2001003",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'thresholds.high_latency_ms')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> config = Config()
            >>> config.get('thresholds.high_latency_ms')
            20.0
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_threshold(self, name: str) -> Any:
        """Get a threshold value."""
        return self.get(f"thresholds.{name}")

    def get_ssh(self, name: str) -> Any:
        """Get an SSH configuration value."""
        return self.get(f"ssh.{name}")

    def get_logging(self, name: str) -> Any:
        """Get a logging configuration value."""
        return self.get(f"logging.{name}")

    def get_web(self, name: str) -> Any:
        """Get a web interface configuration value."""
        return self.get(f"web.{name}")

    def get_report(self, name: str) -> Any:
        """Get a report configuration value."""
        return self.get(f"report.{name}")

    def get_kb_article(self, name: str) -> str:
        """Get a VMware KB article URL."""
        return self.get(f"kb_articles.{name}", "")

    @property
    def all(self) -> dict[str, Any]:
        """Get all configuration as a dictionary."""
        return self._config.copy()


# Global config instance
config = Config()
