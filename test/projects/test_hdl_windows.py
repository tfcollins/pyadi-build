from unittest.mock import MagicMock

import pytest

from adibuild.core.config import BuildConfig
from adibuild.platforms.hdl import HDLPlatform
from adibuild.projects.hdl import HDLBuilder


@pytest.fixture
def hdl_config(tmp_path):
    config_data = {
        "project": "hdl",
        "repository": "https://github.com/analogdevicesinc/hdl.git",
        "tag": "hdl_2023_r2",
        "build": {"output_dir": str(tmp_path / "output")},
        "platforms": {
            "zed_fmcomms2": {
                "name": "zed_fmcomms2",
                "arch": "arm",
                "hdl_project": "fmcomms2",
                "carrier": "zed",
            }
        },
    }
    return BuildConfig(config_data)


def test_build_win_execution(hdl_config, mocker, tmp_path):
    """Test Windows build execution logic."""
    platform_config = hdl_config.get_platform("zed_fmcomms2")
    platform = HDLPlatform(platform_config)
    builder = HDLBuilder(hdl_config, platform)

    # Mock prepare_source and dependencies
    mocker.patch.object(builder, "prepare_source")
    builder.source_dir = tmp_path / "hdl"
    project_dir = builder.source_dir / "projects" / "fmcomms2" / "zed"
    project_dir.mkdir(parents=True, exist_ok=True)

    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch.object(builder, "package_artifacts", return_value={"output_dir": "out"})

    # Mock executor
    mock_execute = mocker.patch.object(builder.executor, "execute")

    # Force _is_windows to return True
    mocker.patch.object(builder, "_is_windows", return_value=True)

    builder.build()

    # Verify Windows flow
    # 1. Should not call make
    assert not any(call[0][0].startswith("make") for call in mock_execute.call_args_list)

    # 2. Should call vivado with adibuild_win.tcl
    # Checking the execute call arguments
    args, kwargs = mock_execute.call_args
    cmd = args[0]
    assert "vivado -mode batch -source adibuild_win.tcl" in cmd
    assert kwargs["cwd"] == project_dir

    # 3. Verify TCL script was created
    tcl_file = project_dir / "adibuild_win.tcl"
    assert tcl_file.exists()
    content = tcl_file.read_text()
    assert "source ../../scripts/adi_make.tcl" in content
    assert "adi_make::lib all" in content
    assert "source system_project.tcl" in content


def test_build_linux_execution(hdl_config, mocker, tmp_path):
    """Test Linux build execution logic (regression check)."""
    platform_config = hdl_config.get_platform("zed_fmcomms2")
    platform = HDLPlatform(platform_config)
    builder = HDLBuilder(hdl_config, platform)

    mocker.patch.object(builder, "prepare_source")
    builder.source_dir = tmp_path / "hdl"
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch.object(builder, "package_artifacts", return_value={"output_dir": "out"})

    mock_make = mocker.patch.object(builder.executor, "make")
    mocker.patch.object(builder, "_is_windows", return_value=False)

    builder.build()

    mock_make.assert_called_once()


def test_build_win_script_mode(hdl_config, mocker, tmp_path):
    """Test Windows build script generation."""
    platform_config = hdl_config.get_platform("zed_fmcomms2")
    platform = HDLPlatform(platform_config)
    builder = HDLBuilder(hdl_config, platform, script_mode=True)

    mocker.patch.object(builder, "_is_windows", return_value=True)

    # Mock ScriptBuilder
    mock_sb = MagicMock()
    builder.executor.script_builder = mock_sb

    builder.build()

    # Verify script commands
    calls = mock_sb.write_command.call_args_list
    cmds = [call[0][0] for call in calls]

    # Should see creation of TCL file and execution
    assert any("echo" in cmd and "adibuild_win.tcl" in cmd for cmd in cmds)
    assert any("vivado -mode batch" in cmd for cmd in cmds)
