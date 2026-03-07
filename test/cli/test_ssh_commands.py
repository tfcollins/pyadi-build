"""Tests for SSH target management CLI commands."""

import pytest

from adibuild.cli.main import cli
from adibuild.core.config import BuildConfig


class TestSSHAddCommand:
    """Test SSH add command."""

    def test_add_ssh_target_basic(self, cli_runner, tmp_path, mocker):
        """Test adding a basic SSH target."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")  # Create empty config file

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "add",
                "test-server",
                "example.com",
                "testuser",
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "SSH target 'test-server' added" in result.output

        # Verify config was created
        assert config_file.exists()
        cfg = BuildConfig.from_yaml(config_file)
        target = cfg.get_ssh_target("test-server")

        assert target["hostname"] == "example.com"
        assert target["username"] == "testuser"
        assert target["port"] == 22

    def test_add_ssh_target_with_options(self, cli_runner, tmp_path):
        """Test adding SSH target with all options."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")  # Create empty config file
        key_file = tmp_path / "id_rsa"
        key_file.write_text("dummy key")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "add",
                "dev-server",
                "dev.example.com",
                "developer",
                "--port",
                "2222",
                "--key-file",
                str(key_file),
                "--work-dir",
                "/opt/builds",
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        cfg = BuildConfig.from_yaml(config_file)
        target = cfg.get_ssh_target("dev-server")

        assert target["hostname"] == "dev.example.com"
        assert target["username"] == "developer"
        assert target["port"] == 2222
        assert target["key_file"] == str(key_file)
        assert target["work_dir"] == "/opt/builds"


class TestSSHRemoveCommand:
    """Test SSH remove command."""

    def test_remove_existing_target(self, cli_runner, tmp_path):
        """Test removing an existing SSH target."""
        config_file = tmp_path / "config.yaml"

        # Create config with a target
        cfg = BuildConfig.from_dict({})
        cfg.add_ssh_target("test-server", "example.com", "user")
        cfg.to_yaml(config_file)

        # Remove the target
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "remove",
                "test-server",
            ],
        )

        assert result.exit_code == 0
        assert "SSH target 'test-server' removed" in result.output

        # Verify it's gone
        cfg = BuildConfig.from_yaml(config_file)
        assert cfg.get_ssh_target("test-server") is None

    def test_remove_nonexistent_target(self, cli_runner, tmp_path):
        """Test removing a non-existent SSH target."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("ssh_targets: {}")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "remove",
                "nonexistent",
            ],
        )

        assert result.exit_code != 0
        assert "SSH target 'nonexistent' not found" in result.output


class TestSSHListCommand:
    """Test SSH list command."""

    def test_list_targets(self, cli_runner, tmp_path):
        """Test listing SSH targets."""
        config_file = tmp_path / "config.yaml"

        # Create config with targets
        cfg = BuildConfig.from_dict({})
        cfg.add_ssh_target("server1", "example1.com", "user1")
        cfg.add_ssh_target("server2", "example2.com", "user2", port=2222)
        cfg.to_yaml(config_file)

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "list",
            ],
        )

        assert result.exit_code == 0
        assert "server1" in result.output
        assert "server2" in result.output
        assert "example1.com" in result.output
        assert "example2.com" in result.output

    def test_list_empty(self, cli_runner, tmp_path):
        """Test listing when no targets configured."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("ssh_targets: {}")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "list",
            ],
        )

        assert result.exit_code == 0
        assert "No SSH targets configured" in result.output


class TestSSHShowCommand:
    """Test SSH show command."""

    def test_show_target(self, cli_runner, tmp_path):
        """Test showing SSH target details."""
        config_file = tmp_path / "config.yaml"

        # Create config with a target
        cfg = BuildConfig.from_dict({})
        cfg.add_ssh_target(
            "test-server",
            "example.com",
            "testuser",
            port=2222,
            key_file="/path/to/key",
        )
        cfg.to_yaml(config_file)

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "show",
                "test-server",
            ],
        )

        assert result.exit_code == 0
        assert "test-server" in result.output
        assert "example.com" in result.output
        assert "testuser" in result.output
        assert "2222" in result.output
        assert "/path/to/key" in result.output

    def test_show_nonexistent_target(self, cli_runner, tmp_path):
        """Test showing non-existent target."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("ssh_targets: {}")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "show",
                "nonexistent",
            ],
        )

        assert result.exit_code != 0
        assert "SSH target 'nonexistent' not found" in result.output


class TestSSHSelectCommand:
    """Test SSH select command."""

    def test_select_target(self, cli_runner, tmp_path):
        """Test selecting SSH target for builds."""
        config_file = tmp_path / "config.yaml"

        # Create config with a target
        cfg = BuildConfig.from_dict({})
        cfg.add_ssh_target("test-server", "example.com", "user")
        cfg.to_yaml(config_file)

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "select",
                "test-server",
            ],
        )

        assert result.exit_code == 0
        assert "Selected SSH target 'test-server'" in result.output

        # Verify selection was saved
        cfg = BuildConfig.from_yaml(config_file)
        assert cfg.get_selected_target() == "test-server"

    def test_clear_selection(self, cli_runner, tmp_path):
        """Test clearing SSH target selection."""
        config_file = tmp_path / "config.yaml"

        # Create config with a selected target
        cfg = BuildConfig.from_dict({})
        cfg.add_ssh_target("test-server", "example.com", "user")
        cfg.set_selected_target("test-server")
        cfg.to_yaml(config_file)

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "select",
            ],
        )

        assert result.exit_code == 0
        assert "Cleared SSH target selection" in result.output

        # Verify selection was cleared
        cfg = BuildConfig.from_yaml(config_file)
        assert cfg.get_selected_target() is None

    def test_select_nonexistent_target(self, cli_runner, tmp_path):
        """Test selecting non-existent target."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("ssh_targets: {}")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "ssh",
                "select",
                "nonexistent",
            ],
        )

        assert result.exit_code != 0
        assert "SSH target 'nonexistent' not found" in result.output
