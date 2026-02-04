import sys
from unittest.mock import MagicMock, patch

# Mock fastmcp before importing the module under test
mock_fastmcp = MagicMock()
mock_mcp_instance = MagicMock()
mock_fastmcp.FastMCP.return_value = mock_mcp_instance
# make @mcp.tool() work as a simple decorator
mock_mcp_instance.tool.return_value = lambda f: f

sys.modules["fastmcp"] = mock_fastmcp

# Now import the module
from adibuild import __version__  # noqa: E402
from adibuild.cli import mcp_server  # noqa: E402


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
        mock_config.config = {"platforms": {"zynq": {}, "zynqmp": {}}}
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
        mock_builder.build.assert_called_once_with(clean_before=False)

    @patch("adibuild.cli.mcp_server.HDLBuilder")
    def test_build_hdl_project_failure(self, mock_builder_cls):
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
        mock_builder.build.assert_called_once_with(clean_before=True)

    @patch("adibuild.cli.mcp_server._load_config")
    def test_build_linux_platform_failure(self, mock_load):
        """Test build_linux_platform failure path."""
        mock_load.side_effect = Exception("Config not found")

        result = mcp_server.build_linux_platform("zynqmp")
        assert "Build failed: Config not found" in result

    def test_cli_integration(self):
        """Test that 'mcp' command is registered in CLI."""
        from adibuild.cli.main import cli

        assert "mcp" in cli.commands
