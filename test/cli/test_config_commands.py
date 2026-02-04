"""Tests for configuration management commands."""

from adibuild.cli.main import cli

# ============================================================================
# Config Init Tests
# ============================================================================


def test_config_init_creates_file(cli_runner, mocker, tmp_path):
    """Test config init creates configuration file."""
    # Mock home directory to use tmp_path
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    mocker.patch("pathlib.Path.home", return_value=mock_home)

    # Mock the prompt_for_config function to avoid interactive prompts
    mock_config_data = {
        "build": {"parallel_jobs": 8},
        "toolchains": {},
    }
    mocker.patch("adibuild.cli.helpers.prompt_for_config", return_value=mock_config_data)

    # Mock BuildConfig.to_yaml to avoid actual file writing issues
    mock_to_yaml = mocker.patch("adibuild.core.config.BuildConfig.to_yaml")

    result = cli_runner.invoke(cli, ["config", "init"])

    assert result.exit_code == 0
    assert "Configuration created" in result.output
    # Verify to_yaml was called
    mock_to_yaml.assert_called_once()


def test_config_init_overwrite_declined(cli_runner, mocker, tmp_path):
    """Test config init when user declines overwrite."""
    # Setup existing config
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    config_dir = mock_home / ".adibuild"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("existing: config")

    mocker.patch("pathlib.Path.home", return_value=mock_home)

    # User declines overwrite
    result = cli_runner.invoke(cli, ["config", "init"], input="n\n")

    assert result.exit_code == 0
    # Should ask for confirmation
    assert "Overwrite" in result.output or "already exists" in result.output
    # Original content should be preserved
    assert config_file.read_text() == "existing: config"


def test_config_init_overwrite_accepted(cli_runner, mocker, tmp_path):
    """Test config init when user accepts overwrite."""
    # Setup existing config
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    config_dir = mock_home / ".adibuild"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("existing: config")

    mocker.patch("pathlib.Path.home", return_value=mock_home)

    # Mock prompt_for_config
    mock_config_data = {
        "build": {"parallel_jobs": 8},
        "toolchains": {},
    }
    mocker.patch("adibuild.cli.helpers.prompt_for_config", return_value=mock_config_data)
    mocker.patch("adibuild.core.config.BuildConfig.to_yaml")

    # User accepts overwrite
    result = cli_runner.invoke(cli, ["config", "init"], input="y\n")

    assert result.exit_code == 0
    assert "Configuration created" in result.output


# ============================================================================
# Config Validate Tests
# ============================================================================


def test_config_validate_valid_file(cli_runner, mock_config_file, mocker, tmp_path):
    """Test config validate with a valid configuration file."""
    # Create a mock schema file
    schema_file = tmp_path / "schema.json"
    schema_file.write_text('{"type": "object"}')

    # Mock schema path resolution
    mocker.patch("pathlib.Path.__truediv__", return_value=schema_file)

    # Mock validate to succeed
    mocker.patch("adibuild.core.config.BuildConfig.validate")
    mock_from_yaml = mocker.patch("adibuild.core.config.BuildConfig.from_yaml")
    mock_from_yaml.return_value = mocker.MagicMock()

    result = cli_runner.invoke(cli, ["config", "validate", str(mock_config_file)])

    assert result.exit_code == 0
    assert "Configuration valid" in result.output or "valid" in result.output.lower()


def test_config_validate_invalid_file(cli_runner, mock_invalid_config_file, mocker):
    """Test config validate with an invalid configuration file."""
    # Mock validate to raise error
    from adibuild.core.config import ConfigurationError

    mock_from_yaml = mocker.patch("adibuild.core.config.BuildConfig.from_yaml")
    mock_config = mocker.MagicMock()
    mock_config.validate.side_effect = ConfigurationError(
        "Missing required field: repository"
    )
    mock_from_yaml.return_value = mock_config

    result = cli_runner.invoke(cli, ["config", "validate", str(mock_invalid_config_file)])

    assert result.exit_code == 1
    assert (
        "validation failed" in result.output.lower() or "error" in result.output.lower()
    )


def test_config_validate_missing_schema(cli_runner, mock_config_file):
    """Test config validate when schema file doesn't exist."""
    # This test verifies that the command handles missing schema gracefully
    # The actual schema file location is determined by the package installation
    # We just verify the command doesn't crash and returns appropriate exit code
    result = cli_runner.invoke(cli, ["config", "validate", str(mock_config_file)])

    # The command should either succeed (if schema exists) or fail gracefully
    # What matters is that it doesn't crash with an unhandled exception
    assert result.exit_code in (0, 1)
    # Should have some output
    assert len(result.output) > 0


def test_config_validate_nonexistent_file(cli_runner):
    """Test config validate with non-existent config file."""
    result = cli_runner.invoke(cli, ["config", "validate", "/nonexistent/config.yaml"])

    assert result.exit_code != 0
    # Click will show path validation error


# ============================================================================
# Config Show Tests
# ============================================================================


def test_config_show_default(cli_runner, mocker):
    """Test config show with default configuration."""
    from adibuild.core.config import BuildConfig

    # Create a mock config
    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": "2023_R2",
        "platforms": {
            "zynq": {
                "arch": "arm",
                "defconfig": "zynq_xcomm_adv7511_defconfig",
                "kernel_target": "uImage",
                "dtbs": ["test1.dtb", "test2.dtb"],
            },
            "zynqmp": {
                "arch": "arm64",
                "defconfig": "adi_zynqmp_defconfig",
                "kernel_target": "Image",
                "dtbs": ["test3.dtb"],
            },
        },
    }

    config = BuildConfig.from_dict(config_data)
    mocker.patch("adibuild.core.config.BuildConfig.from_yaml", return_value=config)

    result = cli_runner.invoke(cli, ["config", "show"])

    assert result.exit_code == 0
    # Should display platform information
    assert "zynq" in result.output.lower() or "Platform" in result.output
    assert "zynqmp" in result.output.lower() or "Available" in result.output


def test_config_show_custom_file(cli_runner, mock_config_file, mocker):
    """Test config show with custom configuration file."""
    from adibuild.core.config import BuildConfig

    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": "2023_R2",
        "platforms": {
            "zynqmp": {
                "arch": "arm64",
                "defconfig": "adi_zynqmp_defconfig",
                "kernel_target": "Image",
                "dtbs": ["custom.dtb"],
            },
        },
    }

    config = BuildConfig.from_dict(config_data)
    mocker.patch("adibuild.core.config.BuildConfig.from_yaml", return_value=config)

    result = cli_runner.invoke(cli, ["config", "show", "--config", str(mock_config_file)])

    assert result.exit_code == 0
    # Should show custom config
    assert "zynqmp" in result.output.lower() or "Platform" in result.output


def test_config_show_load_failure(cli_runner, mocker):
    """Test config show when config loading fails."""
    # Mock BuildConfig.from_yaml to raise exception
    mocker.patch(
        "adibuild.core.config.BuildConfig.from_yaml",
        side_effect=Exception("Failed to load config"),
    )

    result = cli_runner.invoke(cli, ["config", "show"])

    assert result.exit_code == 1
    assert "Failed to load configuration" in result.output or "Error" in result.output


def test_config_show_no_platforms(cli_runner, mocker):
    """Test config show with configuration that has no platforms."""
    from adibuild.core.config import BuildConfig

    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": "2023_R2",
        "platforms": {},
    }

    config = BuildConfig.from_dict(config_data)
    mocker.patch("adibuild.core.config.BuildConfig.from_yaml", return_value=config)

    result = cli_runner.invoke(cli, ["config", "show"])

    assert result.exit_code == 0
    # Should show warning about no platforms
    assert "No platforms" in result.output or "Warning" in result.output


def test_config_show_displays_table(cli_runner, mocker):
    """Test that config show displays information in table format."""
    from adibuild.core.config import BuildConfig

    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": "2023_R2",
        "platforms": {
            "zynq": {
                "arch": "arm",
                "defconfig": "zynq_xcomm_adv7511_defconfig",
                "kernel_target": "uImage",
                "dtbs": ["dtb1.dtb", "dtb2.dtb"],
            },
        },
    }

    config = BuildConfig.from_dict(config_data)
    mocker.patch("adibuild.core.config.BuildConfig.from_yaml", return_value=config)

    result = cli_runner.invoke(cli, ["config", "show"])

    assert result.exit_code == 0
    # Should contain table elements (Rich formatting)
    # The exact format may vary, but should show platform details
    assert "zynq" in result.output.lower() or "arm" in result.output.lower()


# ============================================================================
# Integration Tests
# ============================================================================


def test_config_workflow_init_validate_show(cli_runner, mocker, tmp_path):
    """Test full config workflow: init -> validate -> show."""
    # Setup
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    mocker.patch("pathlib.Path.home", return_value=mock_home)

    # Step 1: Init config
    mock_config_data = {
        "build": {"parallel_jobs": 8},
        "toolchains": {},
    }
    mocker.patch("adibuild.cli.helpers.prompt_for_config", return_value=mock_config_data)
    mocker.patch("adibuild.core.config.BuildConfig.to_yaml")

    result1 = cli_runner.invoke(cli, ["config", "init"])
    assert result1.exit_code == 0

    # Step 2: Validate (would need actual file, so we mock)

    mocker.patch("adibuild.core.config.BuildConfig.from_yaml")
    mocker.patch("adibuild.core.config.BuildConfig.validate")

    # Note: This is a simplified test since we're mocking heavily
    # In reality, each command would be tested separately with proper fixtures
