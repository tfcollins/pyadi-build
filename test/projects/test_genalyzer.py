"""Unit tests for GenalyzerBuilder."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from adibuild.core.config import BuildConfig
from adibuild.platforms.lib import DEFAULT_CROSS_COMPILE, LibPlatform
from adibuild.projects.genalyzer import GenalyzerBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(arch="arm", extra=None, tag="main", output_dir="./build"):
    """Build a minimal BuildConfig for genalyzer tests."""
    platform_cfg = {"arch": arch, "cross_compile": DEFAULT_CROSS_COMPILE.get(arch, "")}
    if extra:
        platform_cfg.update(extra)
    data = {
        "project": "genalyzer",
        "repository": "https://github.com/analogdevicesinc/genalyzer.git",
        "tag": tag,
        "build": {"parallel_jobs": 4, "output_dir": output_dir},
        "platforms": {"arm": platform_cfg},
    }
    return BuildConfig.from_dict(data), LibPlatform(platform_cfg)


# ---------------------------------------------------------------------------
# TestGenalyzerBuilder
# ---------------------------------------------------------------------------


class TestGenalyzerBuilder:
    def _make_builder(self, tmp_path, arch="arm", extra=None, script_mode=False):
        config, platform = _make_config(
            arch=arch, extra=extra, output_dir=str(tmp_path / "build")
        )
        builder = GenalyzerBuilder(config, platform, script_mode=script_mode)
        return builder, config, platform

    def test_builder_init(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)
        assert builder.source_dir is None
        assert builder.script_mode is False

    def test_builder_init_script_mode(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path, script_mode=True)
        assert builder.script_mode is True

    def test_prepare_source(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer_repo"
        fake_source.mkdir()

        mock_repo_cls = mocker.patch("adibuild.projects.genalyzer.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "deadbeef1234"

        def _set_source(*a, **kw):
            builder.source_dir = fake_source

        mock_repo.ensure_repo.side_effect = _set_source

        result = builder.prepare_source()
        assert result == fake_source
        mock_repo.ensure_repo.assert_called_once()

    def test_configure_runs_cmake(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path, arch="arm")

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        builder.configure()

        mock_cmake.assert_called_once()
        args, kwargs = mock_cmake.call_args
        cmake_args = args[0]
        build_dir = kwargs.get("build_dir") or args[1]

        # Cross-compile flags present for arm
        assert any("arm-linux-gnueabihf-gcc" in a for a in cmake_args)
        assert any("DCMAKE_SYSTEM_NAME=Linux" in a for a in cmake_args)
        # Standard genalyzer options
        assert "-DBUILD_DOC=OFF" in cmake_args
        assert "-DBUILD_TESTS_EXAMPLES=OFF" in cmake_args
        # Source reference
        assert ".." in cmake_args
        # Correct build directory
        assert build_dir == fake_source / "build"

    def test_configure_native_no_cross_flags(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path, arch="native")

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        builder.configure()

        args = mock_cmake.call_args[0][0]
        assert not any("CMAKE_C_COMPILER" in a for a in args)
        assert not any("CMAKE_SYSTEM_NAME" in a for a in args)

    def test_configure_injects_fftw_path(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(
            tmp_path, arch="arm", extra={"fftw_path": "/opt/fftw3-arm"}
        )

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        builder.configure()

        args = mock_cmake.call_args[0][0]
        assert any("FFTW_INCLUDE_DIRS=/opt/fftw3-arm/include" in a for a in args)
        assert any("FFTW_LIBRARIES=/opt/fftw3-arm/lib/libfftw3.so" in a for a in args)

    def test_configure_no_fftw_when_not_set(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path, arch="native")

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        builder.configure()

        args = mock_cmake.call_args[0][0]
        assert not any("FFTW" in a for a in args)

    def test_build_calls_cmake_and_make(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        (fake_source / "build").mkdir()

        mocker.patch.object(
            builder,
            "prepare_source",
            side_effect=lambda: setattr(builder, "source_dir", fake_source)
            or fake_source,
        )
        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        mock_make = mocker.patch.object(builder.executor, "make")

        result = builder.build(jobs=4)

        mock_cmake.assert_called_once()
        mock_make.assert_called_once()
        assert "artifacts" in result
        assert "output_dir" in result

    def test_build_clean_before_removes_dir(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        builder.source_dir = fake_source

        mocker.patch.object(builder, "prepare_source", return_value=fake_source)
        mocker.patch.object(builder.executor, "cmake")
        mocker.patch.object(builder.executor, "make")

        builder.build(clean_before=True, jobs=1)
        # build dir should have been removed and recreated by configure()
        assert build_dir.is_dir()

    def test_build_with_jobs(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mocker.patch.object(builder, "prepare_source", return_value=fake_source)
        mocker.patch.object(builder.executor, "cmake")
        mock_make = mocker.patch.object(builder.executor, "make")

        builder.build(jobs=8)

        call_kwargs = mock_make.call_args[1]
        assert call_kwargs.get("jobs") == 8

    def test_clean_shallow(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        (build_dir / "Makefile").write_text("all:\n\nclean:\n")
        builder.source_dir = fake_source

        mock_make = mocker.patch.object(builder.executor, "make")
        builder.clean(deep=False)

        mock_make.assert_called_once_with(
            target="clean", extra_args=["-C", str(build_dir)]
        )

    def test_clean_deep_removes_dir(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        builder.source_dir = fake_source

        builder.clean(deep=True)
        assert not build_dir.exists()

    def test_clean_without_source_calls_prepare(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()

        mocker.patch.object(
            builder,
            "prepare_source",
            side_effect=lambda: setattr(builder, "source_dir", fake_source)
            or fake_source,
        )
        mocker.patch.object(builder.executor, "make")

        builder.clean(deep=False)
        builder.prepare_source.assert_called_once()

    def test_get_output_dir_format(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)
        out = builder.get_output_dir()
        assert out.name == "genalyzer-main-arm"

    def test_get_output_dir_native(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path, arch="native")
        out = builder.get_output_dir()
        assert out.name == "genalyzer-main-native"

    def test_get_output_dir_arm64(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path, arch="arm64")
        out = builder.get_output_dir()
        assert out.name == "genalyzer-main-arm64"

    def test_package_artifacts_copies_so(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()

        # Create fake library file
        (build_dir / "libgenalyzer_plus_plus.so.0.1.2").write_bytes(b"\x7fELF")
        builder.source_dir = fake_source

        artifacts = builder.package_artifacts()
        names = {a.name for a in artifacts}
        assert "libgenalyzer_plus_plus.so.0.1.2" in names

    def test_package_artifacts_copies_so_from_src_subdir(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        src_dir = build_dir / "src"
        src_dir.mkdir(parents=True)

        (src_dir / "libgenalyzer_plus_plus.so").write_bytes(b"\x7fELF")
        builder.source_dir = fake_source

        artifacts = builder.package_artifacts()
        names = {a.name for a in artifacts}
        assert "libgenalyzer_plus_plus.so" in names

    def test_package_artifacts_copies_headers(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        include_dir = fake_source / "include"
        include_dir.mkdir()
        (include_dir / "fourier_analysis.hpp").write_text("// header")
        (include_dir / "version.h").write_text("#define VERSION 1")

        builder.source_dir = fake_source
        artifacts = builder.package_artifacts()

        out_include = builder.get_output_dir() / "include"
        assert (out_include / "fourier_analysis.hpp").exists()
        assert (out_include / "version.h").exists()

    def test_package_artifacts_copies_pc_file(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        (build_dir / "genalyzer.pc").write_text("Name: genalyzer\nVersion: 0.1.2\n")

        builder.source_dir = fake_source
        artifacts = builder.package_artifacts()

        names = {a.name for a in artifacts}
        assert "genalyzer.pc" in names

    def test_package_artifacts_writes_metadata(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        (fake_source / "build").mkdir()

        builder.source_dir = fake_source
        builder.package_artifacts()

        metadata_path = builder.get_output_dir() / "metadata.json"
        assert metadata_path.exists()
        metadata = json.loads(metadata_path.read_text())
        assert metadata["project"] == "genalyzer"
        assert metadata["arch"] == "arm"
        assert metadata["tag"] == "main"

    def test_package_artifacts_raises_without_source_dir(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)
        from adibuild.core.executor import BuildError

        with pytest.raises(BuildError, match="Source directory not set"):
            builder.package_artifacts()

    def test_build_script_mode(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path, script_mode=True)

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()

        mocker.patch.object(
            builder,
            "prepare_source",
            side_effect=lambda: setattr(builder, "source_dir", fake_source)
            or fake_source,
        )
        result = builder.build(jobs=4)

        assert "artifacts" in result
        assert "output_dir" in result

    def test_build_custom_cmake_options(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(
            tmp_path,
            arch="native",
            extra={"cmake_options": {"BUILD_SHARED_LIBS": "OFF"}},
        )

        fake_source = tmp_path / "genalyzer"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        builder.configure()

        args = mock_cmake.call_args[0][0]
        assert "-DBUILD_SHARED_LIBS=OFF" in args

    def test_tag_used_in_output_dir(self, tmp_path):
        config, platform = _make_config(
            arch="arm", tag="v0.1.2", output_dir=str(tmp_path / "build")
        )
        builder = GenalyzerBuilder(config, platform)
        out = builder.get_output_dir()
        assert "v0.1.2" in out.name


# ---------------------------------------------------------------------------
# TestGenalyzerCLI
# ---------------------------------------------------------------------------


class TestGenalyzerCLI:
    """CLI integration tests using Click's test runner."""

    def _make_config_file(self, tmp_path):
        cfg = tmp_path / "genalyzer.yaml"
        cfg.write_text(
            "project: genalyzer\n"
            "repository: https://github.com/analogdevicesinc/genalyzer.git\n"
            "tag: main\n"
            "build:\n"
            "  parallel_jobs: 4\n"
            "  output_dir: ./build\n"
            "platforms:\n"
            "  native:\n"
            "    arch: native\n"
            "  arm:\n"
            "    arch: arm\n"
            "    cross_compile: arm-linux-gnueabihf-\n"
        )
        return cfg

    def test_genalyzer_help(self):
        from click.testing import CliRunner

        from adibuild.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["genalyzer", "--help"])
        assert result.exit_code == 0
        assert "genalyzer" in result.output.lower()

    def test_genalyzer_build_help(self):
        from click.testing import CliRunner

        from adibuild.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["genalyzer", "build", "--help"])
        assert result.exit_code == 0
        assert "--platform" in result.output
        assert "--fftw-path" in result.output
        assert "--generate-script" in result.output

    def test_genalyzer_clean_help(self):
        from click.testing import CliRunner

        from adibuild.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["genalyzer", "clean", "--help"])
        assert result.exit_code == 0
        assert "--deep" in result.output

    def test_genalyzer_build_script_native(self, tmp_path, mocker):
        from click.testing import CliRunner

        from adibuild.cli.main import cli

        cfg = self._make_config_file(tmp_path)

        mocker.patch("adibuild.projects.genalyzer.GitRepository")
        mocker.patch("adibuild.core.executor.BuildExecutor.cmake")
        mocker.patch("adibuild.core.executor.BuildExecutor.make")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--config",
                str(cfg),
                "genalyzer",
                "build",
                "-p",
                "native",
                "--generate-script",
            ],
        )
        assert result.exit_code == 0

    def test_genalyzer_build_script_has_cmake_flags(self, tmp_path, mocker):
        from click.testing import CliRunner

        from adibuild.cli.main import cli

        cfg = self._make_config_file(tmp_path)

        mocker.patch("adibuild.projects.genalyzer.GitRepository")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--config",
                str(cfg),
                "genalyzer",
                "build",
                "-p",
                "arm",
                "--generate-script",
            ],
        )
        assert result.exit_code == 0

        # Find the generated script
        script_files = list(tmp_path.rglob("build_genalyzer_arm.sh"))
        if not script_files:
            # Look in the default work dir
            import os

            work_dir = Path.home() / ".adibuild" / "work"
            script_files = list(work_dir.glob("build_genalyzer_arm.sh"))

        if script_files:
            content = script_files[0].read_text()
            assert "cmake" in content
            assert "BUILD_DOC=OFF" in content

    def test_genalyzer_missing_platform_flag(self, tmp_path):
        from click.testing import CliRunner

        from adibuild.cli.main import cli

        cfg = self._make_config_file(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--config", str(cfg), "genalyzer", "build"]
        )
        assert result.exit_code != 0
        assert "platform" in result.output.lower() or "missing" in result.output.lower()

    def test_genalyzer_fftw_path_override(self, tmp_path, mocker):
        from click.testing import CliRunner

        from adibuild.cli.main import cli

        cfg = self._make_config_file(tmp_path)

        captured = {}

        original_init = GenalyzerBuilder.__init__

        def mock_init(self, config, platform, *args, **kwargs):
            captured["fftw_path"] = platform.config.get("fftw_path")
            original_init(self, config, platform, *args, **kwargs)

        mocker.patch.object(GenalyzerBuilder, "__init__", mock_init)
        mocker.patch.object(GenalyzerBuilder, "build", return_value={"artifacts": [], "output_dir": ""})

        runner = CliRunner()
        runner.invoke(
            cli,
            [
                "--config",
                str(cfg),
                "genalyzer",
                "build",
                "-p",
                "arm",
                "--fftw-path",
                "/opt/fftw3-arm",
            ],
        )
        assert captured.get("fftw_path") == "/opt/fftw3-arm"


# ---------------------------------------------------------------------------
# TestGenalyzerConfTestFixtures
# ---------------------------------------------------------------------------


class TestGenalyzerConfTestFixtures:
    def test_genalyzer_config_dict_fixture(self, genalyzer_config_dict):
        assert genalyzer_config_dict["arch"] == "arm"
        assert "arm-linux-gnueabihf-" in genalyzer_config_dict["cross_compile"]

    def test_genalyzer_config_fixture(self, genalyzer_config):
        assert genalyzer_config.get_project() == "genalyzer"
        assert genalyzer_config.get_tag() == "main"

    def test_genalyzer_platform_from_fixture(self, genalyzer_config):
        platform_cfg = genalyzer_config.get_platform("arm")
        p = LibPlatform(platform_cfg)
        assert p.arch == "arm"
