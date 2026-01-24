"""Configuration management for build system."""

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from adibuild.utils.logger import get_logger


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""

    pass


class BuildConfig:
    """Manages build configuration with support for YAML/JSON and hierarchical loading."""

    def __init__(self, config_data: dict[str, Any]):
        """
        Initialize BuildConfig.

        Args:
            config_data: Configuration dictionary
        """
        self._data = config_data
        self.logger = get_logger("adibuild.config")

    @classmethod
    def from_yaml(cls, path: str | Path) -> "BuildConfig":
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            BuildConfig instance

        Raises:
            ConfigurationError: If file cannot be loaded
        """
        path = Path(path)
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return cls(data or {})
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML file {path}: {e}") from e

    @classmethod
    def from_json(cls, path: str | Path) -> "BuildConfig":
        """
        Load configuration from JSON file.

        Args:
            path: Path to JSON configuration file

        Returns:
            BuildConfig instance

        Raises:
            ConfigurationError: If file cannot be loaded
        """
        path = Path(path)
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        try:
            with open(path) as f:
                data = json.load(f)
            return cls(data or {})
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Failed to parse JSON file {path}: {e}") from e

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BuildConfig":
        """
        Create configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            BuildConfig instance
        """
        return cls(data)

    @classmethod
    def load_with_defaults(
        cls,
        config_path: str | Path | None = None,
        user_config_path: str | Path | None = None,
    ) -> "BuildConfig":
        """
        Load configuration with hierarchical merging.

        Load hierarchy: defaults → user config → runtime config

        Args:
            config_path: Runtime configuration file path
            user_config_path: User configuration file path (defaults to ~/.adibuild/config.yaml)

        Returns:
            BuildConfig instance with merged configuration
        """
        logger = get_logger("adibuild.config")
        merged_data: dict[str, Any] = {}

        # Load user config if exists
        if user_config_path is None:
            user_config_path = Path.home() / ".adibuild" / "config.yaml"

        if Path(user_config_path).exists():
            logger.debug(f"Loading user config from {user_config_path}")
            user_config = cls.from_yaml(user_config_path)
            merged_data = cls._deep_merge(merged_data, user_config._data)

        # Load runtime config if provided
        if config_path:
            logger.debug(f"Loading runtime config from {config_path}")
            runtime_config = cls.from_yaml(config_path)
            merged_data = cls._deep_merge(merged_data, runtime_config._data)

        return cls(merged_data)

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = BuildConfig._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (supports dot notation, e.g., 'build.parallel_jobs')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        data = self._data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def get_platform(self, platform_name: str) -> dict[str, Any]:
        """
        Get platform-specific configuration.

        Args:
            platform_name: Platform name

        Returns:
            Platform configuration dictionary

        Raises:
            ConfigurationError: If platform not found
        """
        platforms = self.get("platforms", {})
        if platform_name not in platforms:
            available = ", ".join(platforms.keys()) if platforms else "none"
            raise ConfigurationError(
                f"Platform '{platform_name}' not found in configuration. "
                f"Available platforms: {available}"
            )
        return platforms[platform_name]

    def get_project(self) -> str:
        """
        Get project name.

        Returns:
            Project name

        Raises:
            ConfigurationError: If project not specified
        """
        project = self.get("project")
        if not project:
            raise ConfigurationError("Project not specified in configuration")
        return project

    def get_repository(self) -> str:
        """
        Get repository URL.

        Returns:
            Repository URL

        Raises:
            ConfigurationError: If repository not specified
        """
        repo = self.get("repository")
        if not repo:
            raise ConfigurationError("Repository URL not specified in configuration")
        return repo

    def get_tag(self) -> str | None:
        """
        Get git tag.

        Returns:
            Git tag or None
        """
        return self.get("tag")

    def get_parallel_jobs(self, default: int = 4) -> int:
        """
        Get number of parallel build jobs.

        Args:
            default: Default value if not specified

        Returns:
            Number of parallel jobs
        """
        jobs = self.get("build.parallel_jobs", default)
        try:
            return int(jobs)
        except (ValueError, TypeError):
            return default

    def validate(self, schema_path: str | Path) -> bool:
        """
        Validate configuration against JSON schema.

        Args:
            schema_path: Path to JSON schema file

        Returns:
            True if validation passes

        Raises:
            ConfigurationError: If validation fails
        """
        schema_path = Path(schema_path)
        if not schema_path.exists():
            raise ConfigurationError(f"Schema file not found: {schema_path}")

        try:
            with open(schema_path) as f:
                schema = json.load(f)

            jsonschema.validate(self._data, schema)
            self.logger.debug("Configuration validation passed")
            return True

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Failed to parse schema file: {e}") from e
        except jsonschema.ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {e.message}") from e

    def to_dict(self) -> dict[str, Any]:
        """
        Get configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self._data.copy()

    def to_yaml(self, path: str | Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            path: Output file path
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self._data, f, default_flow_style=False)

    def to_json(self, path: str | Path) -> None:
        """
        Save configuration to JSON file.

        Args:
            path: Output file path
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self._data, f, indent=2)

    def __repr__(self) -> str:
        """String representation."""
        return f"BuildConfig({self._data})"
