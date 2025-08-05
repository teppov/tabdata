"""Tests for the configuration module."""

import os
import json
import tempfile
import pytest
from pathlib import Path

from varman.config import Config, get_config, set_config_path, CONFIG_PATH_ENV_VAR


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        temp_path = temp_file.name
    
    yield temp_path
    
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def reset_config_singleton():
    """Reset the configuration singleton for testing."""
    # Store original values
    import varman.config
    original_instance = varman.config._config_instance
    original_path = varman.config._config_path
    
    # Reset for test
    varman.config._config_instance = None
    varman.config._config_path = None
    
    # Clear environment variable if set
    env_var_was_set = CONFIG_PATH_ENV_VAR in os.environ
    if env_var_was_set:
        env_var_value = os.environ[CONFIG_PATH_ENV_VAR]
        del os.environ[CONFIG_PATH_ENV_VAR]
    
    yield
    
    # Restore original values
    varman.config._config_instance = original_instance
    varman.config._config_path = original_path
    
    # Restore environment variable if it was set
    if env_var_was_set:
        os.environ[CONFIG_PATH_ENV_VAR] = env_var_value
    elif CONFIG_PATH_ENV_VAR in os.environ:
        del os.environ[CONFIG_PATH_ENV_VAR]


def test_config_init_default():
    """Test that Config initializes with default values."""
    config = Config()
    assert config.config_path.endswith("config.json")
    assert "database" in config.config_data
    assert "logging" in config.config_data
    assert "performance" in config.config_data
    assert "export" in config.config_data


def test_config_init_custom_path():
    """Test that Config initializes with a custom path."""
    custom_path = "/tmp/custom_config.json"
    config = Config(custom_path)
    assert config.config_path == custom_path


def test_config_get_set():
    """Test getting and setting configuration values."""
    config = Config()
    
    # Test getting existing value
    db_path = config.get("database", "path")
    assert db_path is not None
    
    # Test getting non-existent value with default
    test_value = config.get("test", "nonexistent", "default_value")
    assert test_value == "default_value"
    
    # Test setting a value
    config.set("test", "new_key", "new_value")
    assert config.get("test", "new_key") == "new_value"


def test_config_helper_methods():
    """Test the helper methods for common configuration options."""
    config = Config()
    
    # Test database path
    assert config.get_database_path() == config.get("database", "path")
    
    # Test backup directory
    assert config.get_backup_directory() == config.get("database", "backup_dir")
    
    # Test log file
    assert config.get_log_file() == config.get("logging", "file")
    
    # Test log level
    assert config.get_log_level() == config.get("logging", "level")
    
    # Test page size
    assert config.get_default_page_size() == config.get("performance", "page_size")
    
    # Test max page size
    assert config.get_max_page_size() == config.get("performance", "max_page_size")


def test_config_save_load(temp_config_file):
    """Test saving and loading configuration."""
    # Create a config with custom path
    config = Config(temp_config_file)
    
    # Modify a value
    test_value = "test_save_load_value"
    config.set("test", "save_load", test_value)
    
    # Save the configuration
    config.save()
    
    # Verify the file exists
    assert os.path.exists(temp_config_file)
    
    # Load the configuration in a new instance
    new_config = Config(temp_config_file)
    
    # Verify the value was loaded
    assert new_config.get("test", "save_load") == test_value


def test_get_config_singleton(reset_config_singleton):
    """Test that get_config returns a singleton instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2


def test_get_config_custom_path(reset_config_singleton, temp_config_file):
    """Test get_config with a custom path."""
    # Create a test configuration file
    test_config = {
        "test": {
            "custom_path": "custom_path_value"
        }
    }
    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)
    
    # Get configuration with custom path
    config = get_config(temp_config_file)
    
    # Verify the path was set
    assert config.config_path == temp_config_file
    
    # Verify the test value was loaded
    assert config.get("test", "custom_path") == "custom_path_value"


def test_get_config_env_var(reset_config_singleton, temp_config_file):
    """Test get_config with environment variable."""
    # Create a test configuration file
    test_config = {
        "test": {
            "env_var": "env_var_value"
        }
    }
    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)
    
    # Set environment variable
    os.environ[CONFIG_PATH_ENV_VAR] = temp_config_file
    
    # Get configuration (should use environment variable)
    config = get_config()
    
    # Verify the path was set from environment variable
    assert config.config_path == temp_config_file
    
    # Verify the test value was loaded
    assert config.get("test", "env_var") == "env_var_value"


def test_set_config_path(reset_config_singleton, temp_config_file):
    """Test setting the configuration path programmatically."""
    # Create a test configuration file
    test_config = {
        "test": {
            "programmatic": "programmatic_value"
        }
    }
    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)
    
    # Set the configuration path programmatically
    set_config_path(temp_config_file)
    
    # Get configuration (should use the path set programmatically)
    config = get_config()
    
    # Verify the path was set
    assert config.config_path == temp_config_file
    
    # Verify the test value was loaded
    assert config.get("test", "programmatic") == "programmatic_value"


def test_config_path_precedence(reset_config_singleton, temp_config_file):
    """Test the precedence of configuration path settings."""
    # Create two temporary files with different values
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as env_file:
        env_path = env_file.name
    
    try:
        # Create config files with different test values
        with open(temp_config_file, 'w') as f:
            json.dump({"test": {"source": "direct_parameter"}}, f)
        
        with open(env_path, 'w') as f:
            json.dump({"test": {"source": "environment_variable"}}, f)
        
        # Set environment variable
        os.environ[CONFIG_PATH_ENV_VAR] = env_path
        
        # Direct parameter should take precedence over environment variable
        config = get_config(temp_config_file)
        assert config.get("test", "source") == "direct_parameter"
        
        # Reset for next test
        import varman.config
        varman.config._config_instance = None
        varman.config._config_path = None
        
        # Environment variable should be used if no direct parameter
        config = get_config()
        assert config.get("test", "source") == "environment_variable"
        
    finally:
        # Clean up
        if os.path.exists(env_path):
            os.unlink(env_path)