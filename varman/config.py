"""Configuration management for the varman package.

This module provides configuration settings for the varman package,
including database location and other settings.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Environment variable for config file path
CONFIG_PATH_ENV_VAR = "VARMAN_CONFIG_PATH"


class Config:
    """Configuration manager for the varman package."""

    # Default configuration values
    DEFAULT_CONFIG = {
        # Database settings
        "database": {
            "path": str(Path.home() / ".varman" / "varman.db"),
            "backup_dir": str(Path.home() / ".varman" / "backups"),
        },
        # Logging settings
        "logging": {
            "level": "INFO",
            "file": str(Path.home() / ".varman" / "varman.log"),
            "max_size": 10 * 1024 * 1024,  # 10 MB
            "backup_count": 3,
        },
        # Performance settings
        "performance": {
            "page_size": 20,
            "max_page_size": 100,
            "cache_size": 1000,
        },
        # Export/Import settings
        "export": {
            "default_format": "json",
            "default_directory": str(Path.home() / "varman_exports"),
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, uses the default path.
        """
        self.config_data = self.DEFAULT_CONFIG.copy()
        
        # Set default config path if not provided
        if config_path is None:
            home_dir = Path.home()
            config_dir = home_dir / ".varman"
            config_dir.mkdir(exist_ok=True)
            self.config_path = str(config_dir / "config.json")
        else:
            self.config_path = config_path
        
        # Load configuration from file if it exists
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Update default config with user config
                self._update_nested_dict(self.config_data, user_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading configuration file: {e}")
    
    def _update_nested_dict(self, d: Dict[str, Any], u: Dict[str, Any]):
        """Update a nested dictionary with another nested dictionary."""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    def save(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config_data, f, indent=4)
        except IOError as e:
            print(f"Error saving configuration file: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            section: The configuration section.
            key: The configuration key.
            default: Default value if the key is not found.

        Returns:
            The configuration value.
        """
        try:
            return self.config_data[section][key]
        except KeyError:
            return default
    
    def set(self, section: str, key: str, value: Any):
        """Set a configuration value.

        Args:
            section: The configuration section.
            key: The configuration key.
            value: The configuration value.
        """
        if section not in self.config_data:
            self.config_data[section] = {}
        
        self.config_data[section][key] = value
    
    def get_database_path(self) -> str:
        """Get the database path.

        Returns:
            The path to the database file.
        """
        return self.get("database", "path")
    
    def get_backup_directory(self) -> str:
        """Get the backup directory.

        Returns:
            The path to the backup directory.
        """
        return self.get("database", "backup_dir")
    
    def get_log_file(self) -> str:
        """Get the log file path.

        Returns:
            The path to the log file.
        """
        return self.get("logging", "file")
    
    def get_log_level(self) -> str:
        """Get the log level.

        Returns:
            The log level.
        """
        return self.get("logging", "level")
    
    def get_default_page_size(self) -> int:
        """Get the default page size for pagination.

        Returns:
            The default page size.
        """
        return self.get("performance", "page_size")
    
    def get_max_page_size(self) -> int:
        """Get the maximum page size for pagination.

        Returns:
            The maximum page size.
        """
        return self.get("performance", "max_page_size")


# Singleton instance for global use
_config_instance = None
_config_path = None


def set_config_path(config_path: str) -> None:
    """Set the configuration file path.
    
    This function sets the path to be used for the configuration file.
    It will reset the current configuration instance so that the next call
    to get_config() will load the configuration from the new path.
    
    Args:
        config_path: Path to the configuration file.
    """
    global _config_instance, _config_path
    _config_instance = None
    _config_path = None
    # Next call to get_config() will create a new instance with this path
    get_config(config_path)


def get_config(config_path: Optional[str] = None) -> Config:
    """Get the configuration singleton instance.

    Args:
        config_path: Path to the configuration file. If None, checks for the VARMAN_CONFIG_PATH
            environment variable, and if not set, uses the default path.
            If a different path is provided than what was used previously,
            a new instance will be created with the new path.

    Returns:
        The configuration instance.
    """
    global _config_instance, _config_path
    
    # Check environment variable if no path is provided
    if config_path is None:
        env_config_path = os.environ.get(CONFIG_PATH_ENV_VAR)
        if env_config_path:
            config_path = env_config_path
    
    # Create a new instance if none exists or if a different path is provided
    if _config_instance is None or (config_path is not None and config_path != _config_path):
        _config_instance = Config(config_path)
        _config_path = config_path
        
    return _config_instance