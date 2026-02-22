import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock fastmcp and git before importing the module under test
mock_fastmcp = MagicMock()
mock_mcp_instance = MagicMock()
mock_fastmcp.FastMCP.return_value = mock_mcp_instance
# make @mcp.tool() work as a simple decorator
mock_mcp_instance.tool.return_value = lambda f: f

sys.modules["fastmcp"] = mock_fastmcp
sys.modules["git"] = MagicMock()

# Now import the module
from adibuild import __version__  # noqa: E402
from adibuild.cli import mcp_server  # noqa: E402
from adibuild.core.toolchain import ToolchainInfo  # noqa: E402


class TestMCPServer:
    """Test suite for MCP server functions."""

    def test_get_version(self):
        """Test get_version tool."""
        assert mcp_server.get_version() == __version__

    @patch("adibuild.cli.mcp_server._load_config")
    def test_list_platforms_success(self, mock_load_config):
        """Test list_platforms with valid config."""
        # Setup mock config
        mock_config = MagicMock()
        mock_config.to_dict.return_value = {"platforms": {"zynq": {}, "zynqmp": {}}}
        mock_load_config.return_value = mock_config

        platforms = mcp_server.list_platforms()
        assert "zynq" in platforms
        assert "zynqmp" in platforms
        assert len(platforms) == 2

    @patch("adibuild.cli.mcp_server._load_config")
    def test_list_platforms_error(self, mock_load_config):
        """Test list_platforms handling errors."""
        mock_load_config.side_effect = Exception("Config error")

        result = mcp_server.list_platforms()
        assert len(result) == 1
        assert result[0].startswith("Error: Config error")

    @patch("adibuild.cli.mcp_server.HDLBuilder")
    @patch("adibuild.cli.mcp_server._get_platform_instance")
    @patch("adibuild.cli.mcp_server.BuildConfig")
    def test_build_hdl_project_success(
        self, mock_config_cls, mock_get_platform, mock_builder_cls
    ):
        """Test build_hdl_project success path."""
        # Setup mocks
        mock_builder = mock_builder_cls.return_value
        mock_builder.build.return_value = {"output_dir": "/tmp/build"}

        result = mcp_server.build_hdl_project("fmcomms2", "zed")

        assert "HDL Build completed" in result
        assert "/tmp/build" in result

        # Verify calls
        mock_config_cls.assert_called_once()
        mock_get_platform.assert_called_once()
        mock_builder.build.assert_called_once()

    @patch("adibuild.cli.mcp_server._get_platform_instance")
    @patch("adibuild.cli.mcp_server._load_config")
    @patch("adibuild.cli.mcp_server.HDLBuilder")
    def test_build_hdl_project_failure(
        self, mock_builder_cls, mock_load_config, mock_get_platform
    ):
        """Test build_hdl_project failure path."""
        mock_builder_cls.side_effect = Exception("Build failed")

        result = mcp_server.build_hdl_project("fmcomms2", "zed")
        assert "Build failed: Build failed" in result

    @patch("adibuild.cli.mcp_server.LinuxBuilder")
    @patch("adibuild.cli.mcp_server._get_platform_instance")
    @patch("adibuild.cli.mcp_server._load_config")
    def test_build_linux_platform_success(
        self, mock_load, mock_get_platform, mock_builder_cls
    ):
        """Test build_linux_platform success path."""
        # Setup mocks
        mock_builder = mock_builder_cls.return_value
        mock_builder.build.return_value = {"output_dir": "/tmp/linux_build"}

        result = mcp_server.build_linux_platform("zynqmp", clean=True)

        assert "Linux Build completed" in result
        assert "/tmp/linux_build" in result

        mock_load.assert_called_once()
        mock_builder.build.assert_called_once()

    @patch("adibuild.cli.mcp_server._load_config")
    def test_build_linux_platform_failure(self, mock_load):
        """Test build_linux_platform failure path."""
        mock_load.side_effect = Exception("Config not found")

        result = mcp_server.build_linux_platform("zynqmp")
        assert "Build failed: Config not found" in result

    @patch("adibuild.cli.mcp_server.LinuxBuilder")
    @patch("adibuild.cli.mcp_server._get_platform_instance")
    @patch("adibuild.cli.mcp_server._load_config")
    def test_configure_linux_platform(
        self, mock_load, mock_get_platform, mock_builder_cls
    ):
        """Test configure_linux_platform."""
        mock_builder = mock_builder_cls.return_value

        result = mcp_server.configure_linux_platform("zynqmp", defconfig="my_defconfig")

        assert "Kernel configured successfully" in result
        mock_builder.prepare_source.assert_called_once()
        mock_builder.configure.assert_called_once()
        mock_load.assert_called_once()

    @patch("adibuild.cli.mcp_server.LinuxBuilder")
    @patch("adibuild.cli.mcp_server._get_platform_instance")
    @patch("adibuild.cli.mcp_server._load_config")
    def test_build_linux_dtbs(self, mock_load, mock_get_platform, mock_builder_cls):
        """Test build_linux_dtbs."""
        mock_builder = mock_builder_cls.return_value
        mock_builder.build_dtbs.return_value = ["test.dtb"]

        result = mcp_server.build_linux_dtbs("zynqmp", dtb_files=["test.dtb"])

        assert "Built 1 DTBs successfully" in result
        mock_builder.build_dtbs.assert_called_once_with(dtbs=["test.dtb"])

    @patch("adibuild.cli.mcp_server.LinuxBuilder")
    @patch("adibuild.cli.mcp_server._get_platform_instance")
    @patch("adibuild.cli.mcp_server._load_config")
    def test_clean_linux_platform(self, mock_load, mock_get_platform, mock_builder_cls):
        """Test clean_linux_platform."""
        mock_builder = mock_builder_cls.return_value

        result = mcp_server.clean_linux_platform("zynqmp", deep=True)

        assert "Clean completed" in result
        mock_builder.clean.assert_called_once_with(deep=True)

    @patch("adibuild.cli.mcp_server.VivadoToolchain")
    @patch("adibuild.cli.mcp_server.ArmToolchain")
    @patch("adibuild.cli.mcp_server.SystemToolchain")
    def test_list_toolchains(self, mock_system, mock_arm, mock_vivado):
        """Test list_toolchains."""
        # Setup mocks
        mock_vivado_inst = mock_vivado.return_value
        mock_vivado_inst.detect.return_value = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt/Xilinx"), env_vars={}
        )

        mock_arm_inst = mock_arm.return_value
        mock_arm_inst.detect.return_value = None

        mock_system_inst = mock_system.return_value
        mock_system_inst.detect.return_value = None

        result = mcp_server.list_toolchains()

        assert "vivado" in result
        assert result["vivado"]["version"] == "2023.2"
        assert "arm_gnu" not in result

    @patch("adibuild.cli.mcp_server.BuildConfig")
    @patch("pathlib.Path.exists")
    def test_validate_configuration(self, mock_exists, mock_config_cls):
        """Test validate_configuration."""
        mock_exists.return_value = True
        mock_config = mock_config_cls.from_yaml.return_value

        result = mcp_server.validate_configuration("config.yaml")

        assert "Configuration valid" in result
        mock_config.validate.assert_called_once()

    def test_cli_integration(self):
        """Test that 'mcp' command is registered in CLI."""
        from adibuild.cli.main import cli

        assert "mcp" in cli.commands
