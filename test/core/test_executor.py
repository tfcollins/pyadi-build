"""Tests for executor module including SSH execution."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adibuild.core.executor import (
    BuildError,
    BuildExecutor,
    ExecutionResult,
    SSHExecutor,
    SSHTarget,
)


class TestSSHTarget:
    """Test SSHTarget configuration class."""

    def test_init_with_defaults(self):
        """Test SSHTarget initialization with default values."""
        target = SSHTarget(
            name="test-server",
            hostname="example.com",
            username="user",
        )

        assert target.name == "test-server"
        assert target.hostname == "example.com"
        assert target.username == "user"
        assert target.port == 22
        assert target.key_file is None
        assert target.work_dir == "~/.adibuild/work"

    def test_init_with_custom_values(self):
        """Test SSHTarget initialization with custom values."""
        target = SSHTarget(
            name="dev-server",
            hostname="192.168.1.100",
            username="developer",
            port=2222,
            key_file="/home/user/.ssh/id_rsa",
            work_dir="/opt/builds",
        )

        assert target.name == "dev-server"
        assert target.port == 2222
        assert target.key_file == "/home/user/.ssh/id_rsa"
        assert target.work_dir == "/opt/builds"

    def test_to_dict(self):
        """Test converting SSHTarget to dictionary."""
        target = SSHTarget(
            name="test-server",
            hostname="example.com",
            username="user",
            port=2222,
            key_file="/path/to/key",
        )

        target_dict = target.to_dict()

        assert target_dict["name"] == "test-server"
        assert target_dict["hostname"] == "example.com"
        assert target_dict["username"] == "user"
        assert target_dict["port"] == 2222
        assert target_dict["key_file"] == "/path/to/key"

    def test_from_dict(self):
        """Test creating SSHTarget from dictionary."""
        data = {
            "name": "test-server",
            "hostname": "example.com",
            "username": "user",
            "port": 2222,
            "key_file": "/path/to/key",
            "work_dir": "/opt/builds",
        }

        target = SSHTarget.from_dict(data)

        assert target.name == "test-server"
        assert target.hostname == "example.com"
        assert target.port == 2222
        assert target.work_dir == "/opt/builds"


class TestSSHExecutor:
    """Test SSHExecutor for remote command execution."""

    @pytest.fixture
    def ssh_target(self):
        """Create a test SSH target."""
        return SSHTarget(
            name="test-server",
            hostname="example.com",
            username="testuser",
            port=22,
        )

    @pytest.fixture
    def ssh_executor(self, ssh_target, tmp_path):
        """Create a test SSH executor."""
        log_file = tmp_path / "test.log"
        return SSHExecutor(target=ssh_target, log_file=log_file)

    def test_build_ssh_command_default_port(self, ssh_executor):
        """Test SSH command building with default port."""
        cmd = ssh_executor._build_ssh_command("echo 'test'")

        assert cmd[0] == "ssh"
        assert "testuser@example.com" in cmd
        assert "echo 'test'" in cmd
        assert "-p" not in cmd  # Default port should not be included

    def test_build_ssh_command_custom_port(self, ssh_target):
        """Test SSH command building with custom port."""
        ssh_target.port = 2222
        executor = SSHExecutor(target=ssh_target)

        cmd = executor._build_ssh_command("echo 'test'")

        assert "-p" in cmd
        assert "2222" in cmd

    def test_build_ssh_command_with_key_file(self, ssh_target):
        """Test SSH command building with key file."""
        ssh_target.key_file = "/home/user/.ssh/id_rsa"
        executor = SSHExecutor(target=ssh_target)

        cmd = executor._build_ssh_command("echo 'test'")

        assert "-i" in cmd
        assert "/home/user/.ssh/id_rsa" in cmd

    def test_execute_success(self, ssh_executor, mocker):
        """Test successful remote command execution."""
        # Mock subprocess.Popen
        mock_process = MagicMock()
        mock_process.stdout = ["Test output\n"]
        mock_process.wait.return_value = 0

        mocker.patch("subprocess.Popen", return_value=mock_process)

        result = ssh_executor.execute("echo 'test'")

        assert result.success
        assert result.return_code == 0
        assert "Test output" in result.stdout

    def test_execute_failure(self, ssh_executor, mocker):
        """Test failed remote command execution."""
        mock_process = MagicMock()
        mock_process.stdout = ["Error occurred\n"]
        mock_process.wait.return_value = 1

        mocker.patch("subprocess.Popen", return_value=mock_process)

        result = ssh_executor.execute("false")

        assert result.failed
        assert result.return_code == 1

    def test_execute_with_env_vars(self, ssh_executor, mocker):
        """Test remote command execution with environment variables."""
        mock_process = MagicMock()
        mock_process.stdout = []
        mock_process.wait.return_value = 0

        mock_popen = mocker.patch("subprocess.Popen", return_value=mock_process)

        env = {"VAR1": "value1", "VAR2": "value2"}
        ssh_executor.execute("echo $VAR1", env=env)

        # Check that SSH command includes environment variables
        call_args = mock_popen.call_args
        ssh_cmd = call_args[0][0]
        ssh_cmd_str = " ".join(ssh_cmd)

        assert "VAR1='value1'" in ssh_cmd_str
        assert "VAR2='value2'" in ssh_cmd_str

    def test_check_tool_success(self, ssh_executor, mocker):
        """Test successful tool check on remote."""
        import io

        mock_process = MagicMock()
        mock_process.stdout = io.StringIO("/usr/bin/make\n")
        mock_process.wait.return_value = 0

        mocker.patch("subprocess.Popen", return_value=mock_process)

        result = ssh_executor.check_tool("make")

        assert result is True

    def test_check_tool_failure(self, ssh_executor, mocker):
        """Test failed tool check on remote."""
        import io

        mock_process = MagicMock()
        mock_process.stdout = io.StringIO("")
        mock_process.wait.return_value = 127  # Command not found

        mocker.patch("subprocess.Popen", return_value=mock_process)

        with pytest.raises(BuildError, match="Required tool 'make' not found"):
            ssh_executor.check_tool("make")

    def test_check_tools_success(self, ssh_executor, mocker):
        """Test successful check of multiple tools on remote."""
        import io

        mock_process = MagicMock()
        mock_process.stdout = io.StringIO("/usr/bin/tool\n")
        mock_process.wait.return_value = 0

        mocker.patch("subprocess.Popen", return_value=mock_process)

        result = ssh_executor.check_tools(["gcc", "make", "git"])

        assert result is True

    def test_check_tools_failure(self, ssh_executor, mocker):
        """Test failed check of multiple tools on remote."""
        import io

        # For multiple tool checks, we need to return different results for each call
        def side_effect(*args, **kwargs):
            mock = MagicMock()
            mock.stdout = io.StringIO("")
            mock.wait.return_value = 127
            return mock

        mocker.patch("subprocess.Popen", side_effect=side_effect)

        with pytest.raises(BuildError, match="Required tools not found"):
            ssh_executor.check_tools(["gcc", "make", "git"])


class TestBuildExecutor:
    """Test BuildExecutor functionality."""

    def test_execute_command_success(self, tmp_path, mocker):
        """Test successful local command execution."""
        executor = BuildExecutor(cwd=tmp_path)

        mocker.patch(
            "subprocess.Popen",
            return_value=MagicMock(
                stdout=["Success\n"],
                wait=MagicMock(return_value=0),
            ),
        )

        result = executor.execute("echo 'test'")

        assert result.success
        assert result.return_code == 0

    def test_execute_command_failure(self, tmp_path, mocker):
        """Test failed local command execution."""
        executor = BuildExecutor(cwd=tmp_path)

        mocker.patch(
            "subprocess.Popen",
            return_value=MagicMock(
                stdout=["Error\n"],
                wait=MagicMock(return_value=1),
            ),
        )

        result = executor.execute("false")

        assert result.failed
        assert result.return_code == 1


class TestExecutionResult:
    """Test ExecutionResult data class."""

    def test_success_property(self):
        """Test success property."""
        result_success = ExecutionResult(
            command="echo test",
            return_code=0,
            stdout="test",
            stderr="",
            duration=1.0,
        )

        result_failure = ExecutionResult(
            command="false",
            return_code=1,
            stdout="",
            stderr="error",
            duration=0.5,
        )

        assert result_success.success is True
        assert result_failure.success is False

    def test_failed_property(self):
        """Test failed property."""
        result_success = ExecutionResult(
            command="echo test",
            return_code=0,
            stdout="test",
            stderr="",
            duration=1.0,
        )

        result_failure = ExecutionResult(
            command="false",
            return_code=1,
            stdout="",
            stderr="error",
            duration=0.5,
        )

        assert result_success.failed is False
        assert result_failure.failed is True
