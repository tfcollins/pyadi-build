"""Real SSH integration tests for HDL builds on hdl-dev-2 target."""

import pytest

from adibuild.core.executor import SSHExecutor


pytestmark = pytest.mark.real_ssh


class TestSSHHDLBuild:
    """Real SSH integration tests for HDL builds."""

    @pytest.fixture
    def hdl_dev_2_config(self, request):
        """Load SSH target config from pytest options."""
        from adibuild.core.config import BuildConfig
        from adibuild.core.executor import SSHTarget

        target_name = request.config.getoption("--ssh-target")

        config_data = {
            "project": "hdl",
            "repository": "https://github.com/analogdevicesinc/hdl.git",
            "tag": "main",
            "build": {"parallel_jobs": 4, "selected_target": target_name},
            "ssh_targets": {
                target_name: {
                    "hostname": target_name,
                    "username": "builder",
                    "port": 22,
                }
            },
        }

        return BuildConfig.from_dict(config_data), target_name

    def test_ssh_connection_to_hdl_dev_2(self, request):
        """Test SSH connection to hdl-dev-2 target."""
        target_name = request.config.getoption("--ssh-target")

        from adibuild.core.executor import SSHTarget

        target = SSHTarget(
            name=target_name,
            hostname=target_name,
            username="builder",
        )

        executor = SSHExecutor(target=target)

        # Test simple echo command
        result = executor.execute("echo 'Connection successful'")

        assert result.success, f"Failed to connect to {target_name}: {result.stdout}"
        assert "Connection successful" in result.stdout

    def test_check_vivado_on_hdl_dev_2(self, request):
        """Test Vivado availability on hdl-dev-2."""
        target_name = request.config.getoption("--ssh-target")

        from adibuild.core.executor import SSHTarget

        target = SSHTarget(
            name=target_name,
            hostname=target_name,
            username="builder",
        )

        executor = SSHExecutor(target=target)

        # Check for vivado binary
        try:
            result = executor.check_tool("vivado")
            assert result is True
        except Exception as e:
            pytest.skip(f"Vivado not available on {target_name}: {e}")

    def test_check_build_tools_on_hdl_dev_2(self, request):
        """Test required build tools on hdl-dev-2."""
        target_name = request.config.getoption("--ssh-target")

        from adibuild.core.executor import SSHTarget

        target = SSHTarget(
            name=target_name,
            hostname=target_name,
            username="builder",
        )

        executor = SSHExecutor(target=target)

        # Check for essential build tools
        tools = ["make", "git", "bash"]

        try:
            result = executor.check_tools(tools)
            assert result is True
        except Exception as e:
            pytest.fail(f"Required tools missing on {target_name}: {e}")

    def test_create_remote_directory(self, request):
        """Test creating directory on remote system."""
        target_name = request.config.getoption("--ssh-target")

        from adibuild.core.executor import SSHTarget
        import time

        target = SSHTarget(
            name=target_name,
            hostname=target_name,
            username="builder",
        )

        executor = SSHExecutor(target=target)

        # Create a unique test directory
        test_dir = f"/tmp/adibuild_test_{int(time.time())}"
        result = executor.execute(f"mkdir -p {test_dir} && test -d {test_dir} && echo 'OK'")

        assert result.success, f"Failed to create directory on {target_name}"
        assert "OK" in result.stdout

        # Cleanup
        executor.execute(f"rm -rf {test_dir}")

    def test_remote_environment_variables(self, request):
        """Test passing environment variables to remote execution."""
        target_name = request.config.getoption("--ssh-target")

        from adibuild.core.executor import SSHTarget

        target = SSHTarget(
            name=target_name,
            hostname=target_name,
            username="builder",
        )

        executor = SSHExecutor(target=target)

        # Test environment variable passing
        env = {"TEST_VAR": "test_value"}
        result = executor.execute("echo $TEST_VAR", env=env)

        assert result.success
        assert "test_value" in result.stdout

    def test_remote_hdl_source_check(self, request):
        """Test accessing HDL source on remote."""
        target_name = request.config.getoption("--ssh-target")

        from adibuild.core.executor import SSHTarget

        target = SSHTarget(
            name=target_name,
            hostname=target_name,
            username="builder",
        )

        executor = SSHExecutor(target=target)

        # Check if typical HDL repo cache exists or can be created
        result = executor.execute(
            "ls -la ~/.adibuild/repos/hdl/ 2>/dev/null || echo 'Not cloned yet'"
        )

        assert result.success


class TestSSHBuildConfig:
    """Test configuration management for SSH builds."""

    def test_ssh_target_in_config(self, hdl_config_with_ssh_target):
        """Test SSH target configuration storage."""
        targets = hdl_config_with_ssh_target.get_ssh_targets()

        assert "hdl-dev-2" in targets
        assert targets["hdl-dev-2"]["hostname"] == "hdl-dev-2"
        assert targets["hdl-dev-2"]["username"] == "builder"

    def test_selected_target_in_config(self, hdl_config_with_ssh_target):
        """Test selected target configuration."""
        selected = hdl_config_with_ssh_target.get_selected_target()

        assert selected == "hdl-dev-2"

    def test_add_multiple_ssh_targets(self):
        """Test adding multiple SSH targets to config."""
        from adibuild.core.config import BuildConfig

        cfg = BuildConfig.from_dict({})

        cfg.add_ssh_target("server1", "example1.com", "user1")
        cfg.add_ssh_target("server2", "example2.com", "user2", port=2222)
        cfg.add_ssh_target("server3", "example3.com", "user3", key_file="/path/to/key")

        targets = cfg.get_ssh_targets()

        assert len(targets) == 3
        assert targets["server1"]["hostname"] == "example1.com"
        assert targets["server2"]["port"] == 2222
        assert targets["server3"]["key_file"] == "/path/to/key"
