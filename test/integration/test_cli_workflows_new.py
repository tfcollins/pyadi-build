"""New integration tests for CLI workflows."""

import textwrap
from click.testing import CliRunner
import pytest
from adibuild.cli.main import cli
from adibuild.core.config import ConfigurationError

def test_cli_linux_build_zynqmp_flow(mocker, tmp_path):
    """Test full ZynqMP linux build flow in CLI."""
    # Mock home to avoid touching real ~/.adibuild
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    
    # Mock executor to avoid real tool calls
    mock_execute = mocker.patch("adibuild.core.executor.BuildExecutor.execute")
    from adibuild.core.executor import ExecutionResult
    mock_execute.return_value = ExecutionResult("cmd", 0, "ok", "", 0.1)
    
    runner = CliRunner()
    result = runner.invoke(cli, ["-vv", "linux", "build", "-p", "zynqmp", "-t", "2023_R2", "--generate-script"])
    
    assert result.exit_code == 0
    # Verify logging output from Phase 2
    assert "Starting Linux kernel build pipeline" in result.output
    # Use parts of the string because rich might wrap lines
    assert "Script generation mode enabled" in result.output
    assert "skipping runtime environment" in result.output
    assert "Linux kernel build pipeline completed successfully" in result.output

def test_cli_hdl_build_flow(mocker, tmp_path):
    """Test full HDL build flow in CLI."""
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    
    # Create a mock config file
    config_file = tmp_path / "hdl_config.yaml"
    config_content = textwrap.dedent("""
        project: hdl
        repository: https://github.com/analogdevicesinc/hdl.git
        tag: 2023_R2
        platforms:
          zed:
            arch: arm
            hdl_project: fmcomms2
            carrier: zed
    """).strip()
    config_file.write_text(config_content)
    
    mock_execute = mocker.patch("adibuild.core.executor.BuildExecutor.execute")
    from adibuild.core.executor import ExecutionResult
    mock_execute.return_value = ExecutionResult("cmd", 0, "ok", "", 0.1)
    
    runner = CliRunner()
    result = runner.invoke(cli, ["-vv", "--config", str(config_file), "hdl", "build", "-p", "zed", "--generate-script"])
    
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "Starting HDL build for project" in result.output
    assert "HDL build completed successfully" in result.output

def test_cli_noos_build_flow(mocker, tmp_path):
    """Test full no-OS build flow in CLI."""
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    
    # Create a mock config file
    config_file = tmp_path / "noos_config.yaml"
    config_content = textwrap.dedent("""
        project: noos
        repository: https://github.com/analogdevicesinc/no-OS.git
        tag: 2023_R2
        platforms:
          ad9361:
            noos_platform: zynqmp
            noos_project: ad9361
    """).strip()
    config_file.write_text(config_content)
    
    mock_execute = mocker.patch("adibuild.core.executor.BuildExecutor.execute")
    from adibuild.core.executor import ExecutionResult
    mock_execute.return_value = ExecutionResult("cmd", 0, "ok", "", 0.1)
    
    runner = CliRunner()
    result = runner.invoke(cli, ["-vv", "--config", str(config_file), "noos", "build", "-p", "ad9361", "--generate-script"])
    
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "Starting no-OS build for project" in result.output
    assert "Artifacts packaged in" in result.output
