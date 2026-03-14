"""Unit tests for validators."""

import shutil
from pathlib import Path
import pytest
from adibuild.utils.validators import (
    ValidationError,
    validate_platform,
    validate_tag,
    validate_path,
    validate_defconfig,
    validate_tool_available,
    validate_tools_available,
    validate_build_environment,
    validate_cross_compile_prefix
)

def test_validate_platform():
    assert validate_platform("zynq") == "zynq"
    assert validate_platform("ZYNQ ") == "zynq"
    assert validate_platform("zynqmp", ["zynq", "zynqmp"]) == "zynqmp"
    with pytest.raises(ValidationError):
        validate_platform("invalid", ["zynq", "zynqmp"])
    with pytest.raises(ValidationError):
        validate_platform(None)

def test_validate_tag():
    assert validate_tag("2023_R2") == "2023_R2"
    assert validate_tag("2022_R1_P1") == "2022_R1_P1"
    assert validate_tag("master") == "master"
    with pytest.raises(ValidationError):
        validate_tag("invalid-tag-!")

def test_validate_path_basic(tmp_path):
    assert validate_path(tmp_path) == tmp_path
    assert validate_path(str(tmp_path)) == tmp_path
    
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    assert validate_path(file_path, must_exist=True) == file_path
    
    with pytest.raises(ValidationError):
        validate_path(tmp_path / "nonexistent", must_exist=True)

def test_validate_path_dir(tmp_path):
    assert validate_path(tmp_path, must_be_dir=True) == tmp_path
    
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    with pytest.raises(ValidationError):
        validate_path(file_path, must_be_dir=True)

def test_validate_tool_available(mocker):
    mocker.patch("shutil.which", side_effect=lambda x: "/bin/" + x if x == "ls" else None)
    assert validate_tool_available("ls") is True
    with pytest.raises(ValidationError):
        validate_tool_available("nonexistent")

def test_validate_tools_available(mocker):
    mocker.patch("shutil.which", side_effect=lambda x: "/bin/" + x if x in ["make", "gcc"] else None)
    assert validate_tools_available(["make", "gcc"]) is True
    with pytest.raises(ValidationError) as exc:
        validate_tools_available(["make", "gcc", "missing"])
    assert "missing" in str(exc.value)

def test_validate_build_environment(mocker):
    mock_which = mocker.patch("shutil.which", return_value="/usr/bin/tool")
    validate_build_environment()
    assert mock_which.call_count >= 3

def test_validate_cross_compile_prefix(mocker):
    mocker.patch("shutil.which", side_effect=lambda x: "/bin/" + x if x == "arm-gcc" else None)
    assert validate_cross_compile_prefix("arm-") == "arm-"
    with pytest.raises(ValidationError):
        validate_cross_compile_prefix("mips-")

def test_validate_defconfig():
    assert validate_defconfig("zynq_adi_defconfig") == "zynq_adi_defconfig"
    # Should warn but return for unusual name
    assert validate_defconfig("custom") == "custom"
