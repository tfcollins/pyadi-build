from unittest.mock import MagicMock

import pytest

from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError, BuildExecutor
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.projects.uboot import UBootBuilder


class TestEnvValidation:
    @pytest.fixture
    def executor(self):
        return BuildExecutor(log_file=None)

    def test_check_tools_success(self, executor, mocker):
        """Test check_tools succeeds when tools exist."""
        # Mock execute to return success (return_code 0)
        mock_res = MagicMock()
        mock_res.failed = False
        mocker.patch.object(executor, "execute", return_value=mock_res)

        assert executor.check_tools(["make", "gcc"]) is True

    def test_check_tools_failure(self, executor, mocker):
        """Test check_tools raises BuildError when a tool is missing."""

        # Mock execute to fail for 'missing_tool'
        def side_effect(cmd, **kwargs):
            res = MagicMock()
            if "missing_tool" in cmd:
                res.failed = True
            else:
                res.failed = False
            return res

        mocker.patch.object(executor, "execute", side_effect=side_effect)

        with pytest.raises(BuildError, match="Required tools not found: missing_tool"):
            executor.check_tools(["make", "missing_tool"])


class TestUBootEnvValidation:
    @pytest.fixture
    def uboot_builder(self, mocker):
        # Patch select_toolchain globally for these tests to avoid real detection/downloads
        mocker.patch("adibuild.platforms.base.select_toolchain")

        config = BuildConfig.from_dict(
            {
                "project": "uboot",
                "build": {"output_dir": "build"},
                "platforms": {"zynqmp": {"arch": "arm64"}},
            }
        )
        platform = ZynqMPPlatform({"arch": "arm64", "kernel_target": "Image"})
        return UBootBuilder(config, platform)

    def test_validate_environment_success(self, uboot_builder, mocker):
        """Test validation passes with all tools."""
        # Mock executor methods
        mocker.patch.object(uboot_builder.executor, "check_tools")

        # Mock successful python package checks and pkg-config checks
        mock_exec = mocker.patch.object(uboot_builder.executor, "execute")
        mock_exec.return_value.failed = False

        # Mock parent validation (which checks basic tools and toolchain)
        mocker.patch(
            "adibuild.core.builder.BuilderBase.validate_environment", return_value=True
        )

        assert uboot_builder.validate_environment() is True

    def test_validate_environment_missing_pkg_resources(self, uboot_builder, mocker):
        """Test validation fails if pkg_resources is missing."""
        mocker.patch.object(uboot_builder.executor, "check_tools")
        mocker.patch(
            "adibuild.core.builder.BuilderBase.validate_environment", return_value=True
        )

        # Mock setuptools check pass, but pkg_resources check fail
        def side_effect(cmd, **kwargs):
            res = MagicMock()
            # Handle both string and list commands just in case
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            if "pkg_resources" in cmd_str:
                res.failed = True
            else:
                res.failed = False
            return res

        mocker.patch.object(uboot_builder.executor, "execute", side_effect=side_effect)

        with pytest.raises(BuildError, match="pkg_resources"):
            uboot_builder.validate_environment()
