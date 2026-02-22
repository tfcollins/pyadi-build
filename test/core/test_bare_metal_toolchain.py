"""Unit tests for BareMetalToolchain."""

from pathlib import Path
from unittest.mock import patch

import pytest

from adibuild.core.toolchain import BareMetalToolchain, ToolchainError, select_toolchain


class TestBareMetalToolchain:
    def test_detect_returns_none_when_not_found(self):
        tc = BareMetalToolchain()
        with patch("shutil.which", return_value=None):
            result = tc.detect()
        assert result is None

    def test_detect_returns_info_when_found(self):
        tc = BareMetalToolchain()
        fake_gcc = "/usr/bin/arm-none-eabi-gcc"
        with patch("shutil.which", return_value=fake_gcc):
            with patch.object(tc, "_get_gcc_version", return_value="12.2.0"):
                result = tc.detect()

        assert result is not None
        assert result.type == "bare_metal"
        assert result.version == "12.2.0"
        assert result.cross_compile_bare_metal == "arm-none-eabi-"
        assert result.path == Path("/usr/bin").parent

    def test_detect_sets_empty_env_vars(self):
        tc = BareMetalToolchain()
        fake_gcc = "/usr/bin/arm-none-eabi-gcc"
        with patch("shutil.which", return_value=fake_gcc):
            with patch.object(tc, "_get_gcc_version", return_value="12.2.0"):
                result = tc.detect()
        assert result.env_vars == {}

    def test_get_cross_compile_arm(self):
        tc = BareMetalToolchain()
        assert tc.get_cross_compile("arm") == "arm-none-eabi-"

    def test_get_cross_compile_bare_metal(self):
        tc = BareMetalToolchain()
        assert tc.get_cross_compile("bare_metal") == "arm-none-eabi-"

    def test_get_cross_compile_unsupported_raises(self):
        tc = BareMetalToolchain()
        with pytest.raises(ToolchainError, match="does not support arch"):
            tc.get_cross_compile("arm64")

    def test_get_gcc_version_parses_correctly(self):
        tc = BareMetalToolchain()
        fake_output = (
            "arm-none-eabi-gcc (GNU Arm Embedded Toolchain 12.2.Rel1) 12.2.1 20221205\n"
            "Copyright ...\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = fake_output
            version = tc._get_gcc_version("/usr/bin/arm-none-eabi-gcc")
        assert version == "12.2.1"

    def test_get_gcc_version_returns_unknown_on_failure(self):
        tc = BareMetalToolchain()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            version = tc._get_gcc_version("/usr/bin/arm-none-eabi-gcc")
        assert version == "unknown"

    def test_get_gcc_version_returns_unknown_on_exception(self):
        tc = BareMetalToolchain()
        with patch("subprocess.run", side_effect=OSError("not found")):
            version = tc._get_gcc_version("/usr/bin/arm-none-eabi-gcc")
        assert version == "unknown"


class TestSelectToolchainBareMetalType:
    def test_select_toolchain_bare_metal_found(self):
        from adibuild.core.toolchain import ToolchainInfo

        fake_info = ToolchainInfo(
            type="bare_metal",
            version="12.2.0",
            path=Path("/usr"),
            env_vars={},
            cross_compile_bare_metal="arm-none-eabi-",
        )
        with patch(
            "adibuild.core.toolchain.BareMetalToolchain.detect", return_value=fake_info
        ):
            result = select_toolchain(preferred="bare_metal", fallbacks=[])
        assert result.type == "bare_metal"
        assert result.cross_compile_bare_metal == "arm-none-eabi-"

    def test_select_toolchain_bare_metal_not_found_raises(self):
        with patch(
            "adibuild.core.toolchain.BareMetalToolchain.detect", return_value=None
        ):
            with pytest.raises(ToolchainError, match="No suitable toolchain found"):
                select_toolchain(preferred="bare_metal", fallbacks=[])

    def test_select_toolchain_bare_metal_fallback_to_system(self):
        from adibuild.core.toolchain import ToolchainInfo

        system_info = ToolchainInfo(
            type="system",
            version="11.4.0",
            path=Path("/usr"),
            env_vars={},
            cross_compile_arm32="arm-linux-gnueabihf-",
        )
        with patch(
            "adibuild.core.toolchain.BareMetalToolchain.detect", return_value=None
        ):
            with patch(
                "adibuild.core.toolchain.SystemToolchain.detect", return_value=system_info
            ):
                result = select_toolchain(preferred="bare_metal", fallbacks=["system"])
        assert result.type == "system"


class TestToolchainInfoBareMetalField:
    def test_bare_metal_field_defaults_none(self):
        from adibuild.core.toolchain import ToolchainInfo

        info = ToolchainInfo(
            type="vivado",
            version="2023.2",
            path=Path("/opt"),
            env_vars={},
        )
        assert info.cross_compile_bare_metal is None

    def test_bare_metal_field_set(self):
        from adibuild.core.toolchain import ToolchainInfo

        info = ToolchainInfo(
            type="bare_metal",
            version="12.2.0",
            path=Path("/usr"),
            env_vars={},
            cross_compile_bare_metal="arm-none-eabi-",
        )
        assert info.cross_compile_bare_metal == "arm-none-eabi-"
