"""Unit tests for no-OS builder and platform."""

from pathlib import Path
from unittest.mock import patch

import pytest

from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.core.toolchain import ToolchainInfo
from adibuild.platforms.base import PlatformError
from adibuild.platforms.noos import VALID_NOOS_PLATFORMS, NoOSPlatform
from adibuild.projects.noos import NoOSBuilder

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vivado_toolchain():
    return ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vitis/2023.2"),
        env_vars={"XILINX_VITIS": "/opt/Xilinx/Vitis/2023.2", "PATH": "/opt/Xilinx/bin"},
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
    )


@pytest.fixture
def bare_metal_toolchain():
    return ToolchainInfo(
        type="bare_metal",
        version="12.2.0",
        path=Path("/usr/bin"),
        env_vars={},
        cross_compile_bare_metal="arm-none-eabi-",
    )


@pytest.fixture
def xilinx_platform_config():
    return {
        "noos_platform": "xilinx",
        "noos_project": "ad9081_fmca_ebz",
        "hardware_file": "/tmp/system_top.xsa",
        "iiod": False,
        "toolchain": {"preferred": "vivado", "fallback": []},
    }


@pytest.fixture
def stm32_platform_config():
    return {
        "noos_platform": "stm32",
        "noos_project": "ad9081_fmca_ebz",
        "iiod": False,
        "toolchain": {"preferred": "bare_metal", "fallback": []},
    }


@pytest.fixture
def noos_build_config(tmp_path):
    config_data = {
        "project": "noos",
        "repository": "https://github.com/analogdevicesinc/no-OS.git",
        "tag": "2023_R2",
        "build": {"parallel_jobs": 4, "output_dir": str(tmp_path / "output")},
        "platforms": {
            "xilinx_ad9081": {
                "noos_platform": "xilinx",
                "noos_project": "ad9081_fmca_ebz",
                "hardware_file": str(tmp_path / "system_top.xsa"),
                "iiod": False,
                "toolchain": {"preferred": "vivado", "fallback": []},
            }
        },
    }
    return BuildConfig(config_data)


# ---------------------------------------------------------------------------
# TestNoOSPlatform
# ---------------------------------------------------------------------------


class TestNoOSPlatform:
    def test_init_valid_xilinx(self, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        assert platform.noos_platform == "xilinx"
        assert platform.noos_project == "ad9081_fmca_ebz"

    def test_init_valid_stm32(self, stm32_platform_config):
        platform = NoOSPlatform(stm32_platform_config)
        assert platform.noos_platform == "stm32"

    def test_noos_platform_invalid(self):
        config = {"noos_platform": "nonexistent", "noos_project": "test"}
        platform = NoOSPlatform(config)
        with pytest.raises(PlatformError, match="Invalid noos_platform"):
            _ = platform.noos_platform

    def test_noos_platform_missing(self):
        config = {"noos_project": "test"}
        platform = NoOSPlatform(config)
        with pytest.raises(PlatformError, match="'noos_platform' not specified"):
            _ = platform.noos_platform

    def test_noos_project_missing(self):
        config = {"noos_platform": "xilinx"}
        platform = NoOSPlatform(config)
        with pytest.raises(PlatformError, match="'noos_project' not specified"):
            _ = platform.noos_project

    def test_arch_bare_metal(self, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        assert platform.arch == "bare_metal"

    def test_arch_native_for_linux(self):
        config = {"noos_platform": "linux", "noos_project": "test"}
        platform = NoOSPlatform(config)
        assert platform.arch == "native"

    def test_arch_bare_metal_for_stm32(self, stm32_platform_config):
        platform = NoOSPlatform(stm32_platform_config)
        assert platform.arch == "bare_metal"

    def test_hardware_file_property(self, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        assert platform.hardware_file == Path("/tmp/system_top.xsa")

    def test_hardware_file_none(self, stm32_platform_config):
        platform = NoOSPlatform(stm32_platform_config)
        assert platform.hardware_file is None

    def test_iiod_property(self, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        assert platform.iiod is False

    def test_iiod_enabled(self):
        config = {"noos_platform": "linux", "noos_project": "test", "iiod": True}
        platform = NoOSPlatform(config)
        assert platform.iiod is True

    def test_profile_property(self):
        config = {
            "noos_platform": "xilinx",
            "noos_project": "ad9081_fmca_ebz",
            "profile": "vcu118_ad9081_m8_l4",
        }
        platform = NoOSPlatform(config)
        assert platform.profile == "vcu118_ad9081_m8_l4"

    def test_profile_none(self, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        assert platform.profile is None

    def test_make_variables_empty(self, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        assert platform.make_variables == {}

    def test_make_variables_populated(self):
        config = {
            "noos_platform": "xilinx",
            "noos_project": "test",
            "make_variables": {"FOO": "bar", "NUM": "42"},
        }
        platform = NoOSPlatform(config)
        assert platform.make_variables == {"FOO": "bar", "NUM": "42"}

    def test_all_valid_platforms_exist(self):
        for p in VALID_NOOS_PLATFORMS:
            config = {"noos_platform": p, "noos_project": "test"}
            platform = NoOSPlatform(config)
            assert platform.noos_platform == p

    def test_get_make_env_returns_toolchain_env(
        self, xilinx_platform_config, vivado_toolchain
    ):
        platform = NoOSPlatform(xilinx_platform_config)
        platform._toolchain = vivado_toolchain
        env = platform.get_make_env()
        assert "XILINX_VITIS" in env

    def test_get_make_env_empty_for_bare_metal(
        self, stm32_platform_config, bare_metal_toolchain
    ):
        platform = NoOSPlatform(stm32_platform_config)
        platform._toolchain = bare_metal_toolchain
        env = platform.get_make_env()
        assert env == {}

    def test_validate_toolchain_xilinx_passes(
        self, xilinx_platform_config, vivado_toolchain
    ):
        platform = NoOSPlatform(xilinx_platform_config)
        platform._toolchain = vivado_toolchain
        assert platform.validate_toolchain() is True

    def test_validate_toolchain_xilinx_fails_without_vivado(
        self, xilinx_platform_config, bare_metal_toolchain
    ):
        platform = NoOSPlatform(xilinx_platform_config)
        platform._toolchain = bare_metal_toolchain
        with pytest.raises(PlatformError, match="requires a Vivado toolchain"):
            platform.validate_toolchain()

    def test_get_toolchain_uses_select_toolchain(
        self, xilinx_platform_config, vivado_toolchain
    ):
        platform = NoOSPlatform(xilinx_platform_config)
        with patch(
            "adibuild.platforms.noos.select_toolchain", return_value=vivado_toolchain
        ):
            tc = platform.get_toolchain()
        assert tc.type == "vivado"

    def test_get_toolchain_cached(self, xilinx_platform_config, vivado_toolchain):
        platform = NoOSPlatform(xilinx_platform_config)
        platform._toolchain = vivado_toolchain
        # Should return cached value without calling select_toolchain
        with patch("adibuild.platforms.noos.select_toolchain") as mock_select:
            tc = platform.get_toolchain()
            mock_select.assert_not_called()
        assert tc is vivado_toolchain

    def test_repr(self, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        r = repr(platform)
        assert "xilinx" in r
        assert "ad9081_fmca_ebz" in r


# ---------------------------------------------------------------------------
# TestNoOSBuilder
# ---------------------------------------------------------------------------


class TestNoOSBuilder:
    def test_builder_init(self, noos_build_config, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)
        assert builder.config == noos_build_config
        assert builder.platform == platform
        assert builder.source_dir is None

    def test_prepare_source(
        self, noos_build_config, xilinx_platform_config, mocker, tmp_path
    ):
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        mock_repo_cls = mocker.patch("adibuild.projects.noos.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        repo_path = tmp_path / ".adibuild" / "repos" / "noos"
        repo_path.mkdir(parents=True)

        source = builder.prepare_source()

        assert source == repo_path
        mock_repo_cls.assert_called_once()
        mock_repo.ensure_repo.assert_called_with(ref="2023_R2")

    def test_configure_is_noop(self, noos_build_config, xilinx_platform_config):
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)
        # Should not raise
        builder.configure()

    def test_build_platform_in_make_args(self, noos_build_config, mocker, tmp_path):
        # Use config without hardware_file to avoid file-not-found during copy
        config = {
            "noos_platform": "xilinx",
            "noos_project": "ad9081_fmca_ebz",
            "iiod": False,
            "toolchain": {"preferred": "vivado", "fallback": []},
        }
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado",
            version="2023.2",
            path=Path("/opt/Xilinx"),
            env_vars={},
        )
        builder = NoOSBuilder(noos_build_config, platform)

        # Mock prepare_source
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"

        # Create real project dir so exists() check passes
        project_dir = builder.source_dir / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)

        # Mock validate_toolchain
        mocker.patch.object(platform, "validate_toolchain", return_value=True)

        # Mock make
        mock_make = mocker.patch.object(builder.executor, "make")

        # Mock package_artifacts
        mocker.patch.object(
            builder,
            "package_artifacts",
            return_value={"artifacts": {}, "output_dir": str(tmp_path / "out")},
        )

        builder.build()

        mock_make.assert_called_once()
        extra_args = mock_make.call_args.kwargs.get("extra_args", [])
        # Verify PLATFORM=xilinx is in make args
        assert any("PLATFORM=xilinx" in arg for arg in extra_args)
        assert any("NO-OS=" in arg for arg in extra_args)

    def test_build_copies_hardware_file(
        self, noos_build_config, xilinx_platform_config, mocker, tmp_path
    ):
        # Create a hardware file
        hw_file = tmp_path / "system_top.xsa"
        hw_file.write_text("dummy xsa")

        config = dict(xilinx_platform_config)
        config["hardware_file"] = str(hw_file)
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt"), env_vars={}
        )

        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"

        project_dir = builder.source_dir / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)

        mocker.patch.object(platform, "validate_toolchain", return_value=True)
        mocker.patch.object(builder.executor, "make")
        mocker.patch.object(
            builder,
            "package_artifacts",
            return_value={"artifacts": {}, "output_dir": str(tmp_path / "out")},
        )

        builder.build()

        # Verify hardware file was copied into project dir
        assert (project_dir / "system_top.xsa").exists()

    def test_build_iiod_flag(self, noos_build_config, mocker, tmp_path):
        config = {
            "noos_platform": "xilinx",
            "noos_project": "ad9081_fmca_ebz",
            "iiod": True,
            "toolchain": {"preferred": "vivado", "fallback": []},
        }
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt"), env_vars={}
        )

        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch.object(platform, "validate_toolchain", return_value=True)
        mock_make = mocker.patch.object(builder.executor, "make")
        mocker.patch.object(
            builder,
            "package_artifacts",
            return_value={"artifacts": {}, "output_dir": str(tmp_path / "out")},
        )

        builder.build()

        extra_args = mock_make.call_args.kwargs.get("extra_args", [])
        assert "IIOD=y" in extra_args

    def test_build_iiod_disabled(self, noos_build_config, mocker, tmp_path):
        # Use config without hardware_file to avoid file-not-found during copy
        config = {
            "noos_platform": "xilinx",
            "noos_project": "ad9081_fmca_ebz",
            "iiod": False,
            "toolchain": {"preferred": "vivado", "fallback": []},
        }
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt"), env_vars={}
        )

        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        # Create real project dir
        (builder.source_dir / "projects" / "ad9081_fmca_ebz").mkdir(parents=True)
        mocker.patch.object(platform, "validate_toolchain", return_value=True)
        mock_make = mocker.patch.object(builder.executor, "make")
        mocker.patch.object(
            builder,
            "package_artifacts",
            return_value={"artifacts": {}, "output_dir": str(tmp_path / "out")},
        )

        builder.build()

        extra_args = mock_make.call_args.kwargs.get("extra_args", [])
        assert "IIOD=n" in extra_args

    def test_build_profile_in_make_args(self, noos_build_config, mocker, tmp_path):
        config = {
            "noos_platform": "xilinx",
            "noos_project": "ad9081_fmca_ebz",
            "profile": "vcu118_ad9081_m8_l4",
            "iiod": False,
            "toolchain": {"preferred": "vivado", "fallback": []},
        }
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt"), env_vars={}
        )

        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch.object(platform, "validate_toolchain", return_value=True)
        mock_make = mocker.patch.object(builder.executor, "make")
        mocker.patch.object(
            builder,
            "package_artifacts",
            return_value={"artifacts": {}, "output_dir": str(tmp_path / "out")},
        )

        builder.build()

        extra_args = mock_make.call_args.kwargs.get("extra_args", [])
        assert "PROFILE=vcu118_ad9081_m8_l4" in extra_args

    def test_clean(self, noos_build_config, xilinx_platform_config, mocker, tmp_path):
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        project_dir = builder.source_dir / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)

        mock_make = mocker.patch.object(builder.executor, "make")

        builder.clean(deep=False)

        mock_make.assert_called_once_with("clean", extra_args=["-C", str(project_dir)])

    def test_clean_deep(
        self, noos_build_config, xilinx_platform_config, mocker, tmp_path
    ):
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        project_dir = builder.source_dir / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)

        mock_make = mocker.patch.object(builder.executor, "make")

        builder.clean(deep=True)

        mock_make.assert_called_once_with("reset", extra_args=["-C", str(project_dir)])

    def test_get_output_dir(self, noos_build_config, xilinx_platform_config, tmp_path):
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        output_dir = builder.get_output_dir()
        assert "noos" in str(output_dir)
        assert "ad9081_fmca_ebz" in str(output_dir)
        assert "2023_R2" in str(output_dir)
        assert "xilinx" in str(output_dir)

    def test_package_artifacts_finds_elf(
        self, noos_build_config, xilinx_platform_config, tmp_path
    ):
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        # Create fake project dir with .elf file
        project_dir = tmp_path / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)
        (project_dir / "firmware.elf").write_bytes(b"\x7fELF")

        result = builder.package_artifacts(project_dir, "ad9081_fmca_ebz", "xilinx")

        assert len(result["artifacts"]["elf"]) == 1
        assert "firmware.elf" in result["artifacts"]["elf"][0]
        assert result["output_dir"] is not None

    def test_build_raises_without_noos_project(self, noos_build_config, mocker, tmp_path):
        config = {"noos_platform": "xilinx"}  # missing noos_project
        platform = NoOSPlatform(config)
        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"

        with pytest.raises(BuildError, match="'noos_project' not specified"):
            builder.build()

    def test_build_script_mode(
        self, noos_build_config, xilinx_platform_config, mocker, tmp_path
    ):
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        platform = NoOSPlatform(xilinx_platform_config)

        builder = NoOSBuilder(noos_build_config, platform, script_mode=True)

        mock_repo_cls = mocker.patch("adibuild.projects.noos.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        # In script mode, no real file ops
        mocker.patch.object(builder.executor, "make")

        # Should not raise even though paths don't exist
        result = builder.build()
        assert "output_dir" in result


# ---------------------------------------------------------------------------
# TestNoOSBuilderEdgeCases — additional coverage
# ---------------------------------------------------------------------------


class TestNoOSBuilderEdgeCases:
    def test_build_raises_without_noos_platform(
        self, noos_build_config, mocker, tmp_path
    ):
        """build() raises BuildError when noos_platform is missing from config."""
        config = {"noos_project": "ad9081_fmca_ebz"}  # missing noos_platform
        platform = NoOSPlatform(config)
        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"

        with pytest.raises(BuildError, match="'noos_platform' not specified"):
            builder.build()

    def test_build_raises_when_project_dir_missing(
        self, noos_build_config, mocker, tmp_path
    ):
        """build() raises BuildError when the project subdirectory does not exist."""
        config = {
            "noos_platform": "xilinx",
            "noos_project": "nonexistent_project",
            "toolchain": {"preferred": "vivado", "fallback": []},
        }
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt"), env_vars={}
        )

        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        (builder.source_dir).mkdir(
            parents=True
        )  # repo root exists, but no projects subdir

        mocker.patch.object(platform, "validate_toolchain", return_value=True)

        with pytest.raises(BuildError, match="project directory not found"):
            builder.build()

    def test_build_raises_when_hardware_file_missing(
        self, noos_build_config, mocker, tmp_path
    ):
        """build() raises BuildError when hardware_file path does not exist."""
        config = {
            "noos_platform": "xilinx",
            "noos_project": "ad9081_fmca_ebz",
            "hardware_file": str(tmp_path / "nonexistent.xsa"),
            "toolchain": {"preferred": "vivado", "fallback": []},
        }
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt"), env_vars={}
        )

        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        project_dir = builder.source_dir / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)
        mocker.patch.object(platform, "validate_toolchain", return_value=True)

        with pytest.raises(BuildError, match="Hardware file not found"):
            builder.build()

    def test_build_custom_make_variables(self, noos_build_config, mocker, tmp_path):
        """Extra make_variables appear in the make call."""
        config = {
            "noos_platform": "xilinx",
            "noos_project": "ad9081_fmca_ebz",
            "iiod": False,
            "make_variables": {"RELEASE": "y", "DEBUG": "n"},
            "toolchain": {"preferred": "vivado", "fallback": []},
        }
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt"), env_vars={}
        )

        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        (builder.source_dir / "projects" / "ad9081_fmca_ebz").mkdir(parents=True)
        mocker.patch.object(platform, "validate_toolchain", return_value=True)
        mock_make = mocker.patch.object(builder.executor, "make")
        mocker.patch.object(
            builder,
            "package_artifacts",
            return_value={"artifacts": {}, "output_dir": str(tmp_path / "out")},
        )

        builder.build()

        extra_args = mock_make.call_args.kwargs.get("extra_args", [])
        assert "RELEASE=y" in extra_args
        assert "DEBUG=n" in extra_args

    def test_clean_without_source_dir_calls_prepare_source(
        self, noos_build_config, xilinx_platform_config, mocker, tmp_path
    ):
        """clean() triggers prepare_source when source_dir is not set."""
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        mock_prepare = mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"  # set after mock to satisfy clean logic
        project_dir = builder.source_dir / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)
        mocker.patch.object(builder.executor, "make")

        # Manually unset source_dir to force prepare_source call
        builder.source_dir = None

        def fake_prepare():
            builder.source_dir = tmp_path / "noos"

        mock_prepare.side_effect = fake_prepare
        builder.clean()

        mock_prepare.assert_called_once()

    def test_package_artifacts_finds_axf(
        self, noos_build_config, xilinx_platform_config, tmp_path
    ):
        """package_artifacts() also collects .axf files."""
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        project_dir = tmp_path / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)
        (project_dir / "firmware.axf").write_bytes(b"AXF")

        result = builder.package_artifacts(project_dir, "ad9081_fmca_ebz", "xilinx")

        assert len(result["artifacts"]["axf"]) == 1
        assert "firmware.axf" in result["artifacts"]["axf"][0]

    def test_package_artifacts_writes_metadata_json(
        self, noos_build_config, xilinx_platform_config, tmp_path
    ):
        """package_artifacts() writes metadata.json into the output directory."""
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        project_dir = tmp_path / "projects" / "test_proj"
        project_dir.mkdir(parents=True)

        result = builder.package_artifacts(project_dir, "test_proj", "xilinx")

        output_dir = Path(result["output_dir"])
        metadata_file = output_dir / "metadata.json"
        assert metadata_file.exists()

        import json

        metadata = json.loads(metadata_file.read_text())
        assert metadata["project"] == "test_proj"
        assert metadata["platform"] == "xilinx"
        assert metadata["tag"] == "2023_R2"

    def test_get_output_dir_uses_config_output_dir(
        self, noos_build_config, xilinx_platform_config, tmp_path
    ):
        """get_output_dir() respects build.output_dir from config."""
        platform = NoOSPlatform(xilinx_platform_config)
        builder = NoOSBuilder(noos_build_config, platform)

        output_dir = builder.get_output_dir()
        # noos_build_config sets output_dir = tmp_path / "output"
        assert str(tmp_path / "output") in str(output_dir)

    def test_build_with_jobs_override(self, noos_build_config, mocker, tmp_path):
        """build(jobs=N) passes -jN to make."""
        config = {
            "noos_platform": "xilinx",
            "noos_project": "ad9081_fmca_ebz",
            "iiod": False,
            "toolchain": {"preferred": "vivado", "fallback": []},
        }
        platform = NoOSPlatform(config)
        platform._toolchain = ToolchainInfo(
            type="vivado", version="2023.2", path=Path("/opt"), env_vars={}
        )

        builder = NoOSBuilder(noos_build_config, platform)
        mocker.patch.object(builder, "prepare_source")
        builder.source_dir = tmp_path / "noos"
        (builder.source_dir / "projects" / "ad9081_fmca_ebz").mkdir(parents=True)
        mocker.patch.object(platform, "validate_toolchain", return_value=True)
        mock_make = mocker.patch.object(builder.executor, "make")
        mocker.patch.object(
            builder,
            "package_artifacts",
            return_value={"artifacts": {}, "output_dir": str(tmp_path / "out")},
        )

        builder.build(jobs=16)

        call_kwargs = mock_make.call_args.kwargs
        assert call_kwargs.get("jobs") == 16


# ---------------------------------------------------------------------------
# TestNoOSConfTestFixtures — verify fixtures used across the test suite
# ---------------------------------------------------------------------------


class TestNoOSConfTestFixtures:
    def test_noos_config_dict_fixture(self, noos_config_dict):
        """The shared noos_config_dict fixture has required keys."""
        assert "noos_platform" in noos_config_dict
        assert "noos_project" in noos_config_dict
        assert noos_config_dict["noos_platform"] == "xilinx"

    def test_noos_config_fixture(self, noos_config):
        """The shared noos_config fixture creates a valid BuildConfig."""
        assert noos_config.get_project() == "noos"
        assert noos_config.get_tag() == "2023_R2"
        platform = noos_config.get_platform("xilinx_ad9081")
        assert platform["noos_platform"] == "xilinx"
        assert platform["noos_project"] == "ad9081_fmca_ebz"

    def test_noos_platform_from_fixture(self, noos_config):
        """NoOSPlatform can be instantiated from the noos_config fixture."""
        platform_config = noos_config.get_platform("xilinx_ad9081")
        platform = NoOSPlatform(platform_config)
        assert platform.noos_platform == "xilinx"
        assert platform.arch == "bare_metal"
