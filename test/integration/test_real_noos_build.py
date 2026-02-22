"""Real build tests for no-OS firmware."""

from pathlib import Path

import pytest

from adibuild.core.config import BuildConfig
from adibuild.platforms.noos import NoOSPlatform
from adibuild.projects.noos import NoOSBuilder


@pytest.mark.real_build
@pytest.mark.slow
class TestRealNoOSBuild:
    def test_real_noos_stm32_build_mocked(self, tmp_path, mocker):
        """
        Test no-OS STM32 build flow.
        We still mock the actual compiler execution to keep it fast in CI
        unless we really want to wait for a full no-OS clone.
        """
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        config_data = {
            "project": "noos",
            "repository": "https://github.com/analogdevicesinc/no-OS.git",
            "tag": "master",
            "build": {"parallel_jobs": 4, "output_dir": str(tmp_path / "output")},
            "platforms": {
                "stm32_ad9081": {
                    "noos_platform": "stm32",
                    "noos_project": "ad9081_fmca_ebz",
                    "toolchain": {"preferred": "bare_metal", "fallback": []},
                }
            },
        }
        config = BuildConfig.from_dict(config_data)
        platform = NoOSPlatform(config.get_platform("stm32_ad9081"))

        builder = NoOSBuilder(config, platform, work_dir=tmp_path / "work")

        # Mock repository to avoid large clone
        mock_repo = mocker.patch("adibuild.projects.noos.GitRepository").return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        # Create fake project directory
        noos_dir = tmp_path / ".adibuild" / "repos" / "noos"
        project_dir = noos_dir / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)
        # We don't set builder.source_dir here, let prepare_source do it

        # Mock toolchain detection to return a fake info
        from adibuild.core.toolchain import ToolchainInfo

        mock_tc = ToolchainInfo(
            type="bare_metal",
            version="12.2.0",
            path=Path("/usr"),
            env_vars={},
            cross_compile_bare_metal="arm-none-eabi-",
        )
        mocker.patch.object(platform, "get_toolchain", return_value=mock_tc)

        # Mock make execution
        mock_make = mocker.patch.object(builder.executor, "make")

        # Create a dummy elf file to find
        (project_dir / "ad9081_fmca_ebz.elf").write_text("dummy elf")

        result = builder.build()

        assert "artifacts" in result
        assert any(
            "PLATFORM=stm32" in str(arg)
            for arg in mock_make.call_args.kwargs["extra_args"]
        )
        assert "ad9081_fmca_ebz.elf" in result["artifacts"]["elf"][0]
