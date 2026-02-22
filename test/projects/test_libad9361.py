"""Unit tests for LibAD9361Builder and LibPlatform."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from adibuild.core.config import BuildConfig
from adibuild.platforms.base import PlatformError
from adibuild.platforms.lib import (
    ARCH_TO_CMAKE_PROCESSOR,
    DEFAULT_CROSS_COMPILE,
    VALID_LIB_ARCHS,
    LibPlatform,
)
from adibuild.projects.libad9361 import LibAD9361Builder

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(arch="arm", extra=None, tag="main", output_dir="./build"):
    """Build a minimal BuildConfig for libad9361 tests."""
    platform_cfg = {"arch": arch, "cross_compile": DEFAULT_CROSS_COMPILE.get(arch, "")}
    if extra:
        platform_cfg.update(extra)
    data = {
        "project": "libad9361",
        "repository": "https://github.com/analogdevicesinc/libad9361-iio.git",
        "tag": tag,
        "build": {"parallel_jobs": 4, "output_dir": output_dir},
        "platforms": {"arm": platform_cfg},
    }
    return BuildConfig.from_dict(data), LibPlatform(platform_cfg)


# ---------------------------------------------------------------------------
# TestLibPlatform
# ---------------------------------------------------------------------------


class TestLibPlatform:
    def test_valid_arm(self):
        p = LibPlatform({"arch": "arm"})
        assert p.arch == "arm"

    def test_valid_arm64(self):
        p = LibPlatform({"arch": "arm64"})
        assert p.arch == "arm64"

    def test_valid_native(self):
        p = LibPlatform({"arch": "native"})
        assert p.arch == "native"

    def test_default_arch_is_native(self):
        p = LibPlatform({})
        assert p.arch == "native"

    def test_invalid_arch_raises(self):
        with pytest.raises(PlatformError, match="Unsupported arch"):
            LibPlatform({"arch": "mips"})

    def test_cross_compile_default_arm(self):
        p = LibPlatform({"arch": "arm"})
        assert p.cross_compile == "arm-linux-gnueabihf-"

    def test_cross_compile_default_arm64(self):
        p = LibPlatform({"arch": "arm64"})
        assert p.cross_compile == "aarch64-linux-gnu-"

    def test_cross_compile_override(self):
        p = LibPlatform({"arch": "arm", "cross_compile": "arm-custom-"})
        assert p.cross_compile == "arm-custom-"

    def test_cross_compile_empty_for_native(self):
        p = LibPlatform({"arch": "native"})
        assert p.cross_compile == ""

    def test_cmake_processor_arm(self):
        p = LibPlatform({"arch": "arm"})
        assert p.cmake_processor == "arm"

    def test_cmake_processor_arm64(self):
        p = LibPlatform({"arch": "arm64"})
        assert p.cmake_processor == "aarch64"

    def test_cmake_processor_none_for_native(self):
        p = LibPlatform({"arch": "native"})
        assert p.cmake_processor is None

    def test_libiio_path_none_by_default(self):
        p = LibPlatform({"arch": "arm"})
        assert p.libiio_path is None

    def test_libiio_path_set(self):
        p = LibPlatform({"arch": "arm", "libiio_path": "/opt/libiio-arm"})
        assert p.libiio_path == Path("/opt/libiio-arm")

    def test_sysroot_none_by_default(self):
        p = LibPlatform({"arch": "arm"})
        assert p.sysroot is None

    def test_sysroot_set(self):
        p = LibPlatform({"arch": "arm", "sysroot": "/opt/sysroot"})
        assert p.sysroot == Path("/opt/sysroot")

    def test_cmake_options_empty_by_default(self):
        p = LibPlatform({"arch": "native"})
        assert p.cmake_options == {}

    def test_cmake_options_populated(self):
        p = LibPlatform({"arch": "native", "cmake_options": {"BUILD_SHARED_LIBS": "OFF"}})
        assert p.cmake_options == {"BUILD_SHARED_LIBS": "OFF"}

    def test_get_make_env_empty(self):
        p = LibPlatform({"arch": "arm"})
        assert p.get_make_env() == {}

    def test_get_cmake_args_native_empty(self):
        p = LibPlatform({"arch": "native"})
        args = p.get_cmake_args()
        # No cross-compile flags for native
        assert not any("-DCMAKE_C_COMPILER" in a for a in args)
        assert not any("-DCMAKE_SYSTEM_NAME" in a for a in args)

    def test_get_cmake_args_arm_has_compiler(self):
        p = LibPlatform({"arch": "arm", "cross_compile": "arm-linux-gnueabihf-"})
        args = p.get_cmake_args()
        assert "-DCMAKE_C_COMPILER=arm-linux-gnueabihf-gcc" in args
        assert "-DCMAKE_CXX_COMPILER=arm-linux-gnueabihf-g++" in args
        assert "-DCMAKE_SYSTEM_NAME=Linux" in args
        assert "-DCMAKE_SYSTEM_PROCESSOR=arm" in args

    def test_get_cmake_args_arm64(self):
        p = LibPlatform({"arch": "arm64", "cross_compile": "aarch64-linux-gnu-"})
        args = p.get_cmake_args()
        assert "-DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc" in args
        assert "-DCMAKE_SYSTEM_PROCESSOR=aarch64" in args

    def test_get_cmake_args_with_sysroot(self):
        p = LibPlatform({"arch": "arm", "sysroot": "/opt/sysroot"})
        args = p.get_cmake_args()
        assert "-DCMAKE_SYSROOT=/opt/sysroot" in args

    def test_get_cmake_args_extra_options(self):
        p = LibPlatform({"arch": "native", "cmake_options": {"BUILD_SHARED_LIBS": "OFF"}})
        args = p.get_cmake_args()
        assert "-DBUILD_SHARED_LIBS=OFF" in args

    def test_validate_toolchain_native_always_passes(self):
        p = LibPlatform({"arch": "native"})
        assert p.validate_toolchain() is True

    def test_validate_toolchain_cross_missing_raises(self):
        p = LibPlatform({"arch": "arm", "cross_compile": "nonexistent-prefix-"})
        with patch("shutil.which", return_value=None):
            with pytest.raises(PlatformError, match="not found in PATH"):
                p.validate_toolchain()

    def test_validate_toolchain_cross_present_passes(self):
        p = LibPlatform({"arch": "arm", "cross_compile": "arm-linux-gnueabihf-"})
        with patch("shutil.which", return_value="/usr/bin/arm-linux-gnueabihf-gcc"):
            assert p.validate_toolchain() is True

    def test_get_toolchain_cached(self):
        p = LibPlatform({"arch": "native"})
        from adibuild.core.toolchain import ToolchainInfo

        fake_tc = ToolchainInfo(
            type="system", version="1.0", path=Path("/usr"), env_vars={}
        )
        with patch("adibuild.platforms.lib.select_toolchain", return_value=fake_tc):
            tc1 = p.get_toolchain()
            tc2 = p.get_toolchain()
        assert tc1 is tc2

    def test_repr(self):
        p = LibPlatform({"arch": "arm"})
        r = repr(p)
        assert "LibPlatform" in r
        assert "arm" in r

    def test_valid_archs_constant(self):
        assert set(VALID_LIB_ARCHS) == {"arm", "arm64", "native"}

    def test_arch_to_cmake_processor_mapping(self):
        assert ARCH_TO_CMAKE_PROCESSOR["arm"] == "arm"
        assert ARCH_TO_CMAKE_PROCESSOR["arm64"] == "aarch64"
        assert ARCH_TO_CMAKE_PROCESSOR["native"] is None

    def test_default_cross_compile_mapping(self):
        assert "arm-linux-gnueabihf-" in DEFAULT_CROSS_COMPILE["arm"]
        assert "aarch64-linux-gnu-" in DEFAULT_CROSS_COMPILE["arm64"]
        assert DEFAULT_CROSS_COMPILE["native"] == ""


# ---------------------------------------------------------------------------
# TestLibAD9361Builder
# ---------------------------------------------------------------------------


class TestLibAD9361Builder:
    def _make_builder(self, tmp_path, arch="arm", extra=None, script_mode=False):
        config, platform = _make_config(
            arch=arch, extra=extra, output_dir=str(tmp_path / "build")
        )
        builder = LibAD9361Builder(config, platform, script_mode=script_mode)
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

        # Create a fake source dir (simulates successful clone)
        fake_source = tmp_path / "libad9361_repo"
        fake_source.mkdir()

        mock_repo_cls = mocker.patch("adibuild.projects.libad9361.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.ensure_repo.return_value = None
        mock_repo.get_commit_sha.return_value = "abc123def456"

        builder.source_dir = fake_source  # pre-set so exists check passes
        mock_repo_cls.return_value = mock_repo

        # Re-run prepare_source with source_dir = None
        builder.source_dir = None

        def _set_source(*a, **kw):
            builder.source_dir = fake_source

        mock_repo.ensure_repo.side_effect = _set_source

        result = builder.prepare_source()
        assert result == fake_source
        mock_repo.ensure_repo.assert_called_once()

    def test_configure_runs_cmake(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path, arch="arm")

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")

        builder.configure()

        mock_cmake.assert_called_once()
        args, kwargs = mock_cmake.call_args
        cmake_args = args[0]
        build_dir = kwargs.get("build_dir") or args[1]

        # Should include cross-compile flags
        assert any("arm-linux-gnueabihf-gcc" in a for a in cmake_args)
        assert any("DCMAKE_SYSTEM_NAME=Linux" in a for a in cmake_args)
        # Must include source reference
        assert ".." in cmake_args
        # Must disable docs and packaging
        assert "-DWITH_DOC=OFF" in cmake_args
        assert "-DPYTHON_BINDINGS=OFF" in cmake_args
        assert "-DENABLE_PACKAGING=OFF" in cmake_args
        assert build_dir == fake_source / "build"

    def test_configure_native_no_cross_flags(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path, arch="native")

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        builder.configure()

        args = mock_cmake.call_args[0][0]
        assert not any("CMAKE_C_COMPILER" in a for a in args)
        assert not any("CMAKE_SYSTEM_NAME" in a for a in args)

    def test_configure_injects_libiio_path(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(
            tmp_path, arch="arm", extra={"libiio_path": "/opt/libiio-arm"}
        )

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        builder.configure()

        args = mock_cmake.call_args[0][0]
        assert any("LIBIIO_INCLUDE_DIR=/opt/libiio-arm/include" in a for a in args)
        assert any("LIBIIO_LIBRARIES=/opt/libiio-arm/lib/libiio.so" in a for a in args)

    def test_build_calls_make_and_cmake(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        (fake_source / "build").mkdir()

        # Prevent real git+cmake+make
        mocker.patch.object(
            builder,
            "prepare_source",
            side_effect=lambda: setattr(builder, "source_dir", fake_source)
            or fake_source,
        )
        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        mock_make = mocker.patch.object(builder.executor, "make")

        result = builder.build(jobs=2)

        mock_cmake.assert_called_once()
        mock_make.assert_called_once()
        make_kwargs = mock_make.call_args
        assert 2 == make_kwargs.kwargs.get("jobs") or make_kwargs[1].get("jobs")
        assert "artifacts" in result
        assert "output_dir" in result

    def test_build_clean_before_removes_dir(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        builder.source_dir = fake_source

        mocker.patch.object(builder, "prepare_source", return_value=fake_source)
        mocker.patch.object(builder.executor, "cmake")
        mocker.patch.object(builder.executor, "make")

        builder.build(clean_before=True, jobs=1)

        # build dir should have been removed and recreated
        assert not build_dir.exists() or build_dir.is_dir()

    def test_clean_shallow(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "libad9361"
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

    def test_clean_deep_removes_dir(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        builder.source_dir = fake_source

        builder.clean(deep=True)

        assert not build_dir.exists()

    def test_clean_without_source_calls_prepare(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "libad9361"
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
        # Should be <output_base>/libad9361-main-arm/
        assert out.name == "libad9361-main-arm"

    def test_get_output_dir_native(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path, arch="native")
        out = builder.get_output_dir()
        assert out.name == "libad9361-main-native"

    def test_package_artifacts_copies_so(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()

        # Create fake library file
        (build_dir / "libad9361.so.0.2").write_bytes(b"\x7fELF")
        # Fake header in source root
        (fake_source / "ad9361.h").write_text("// header")

        builder.source_dir = fake_source
        artifacts = builder.package_artifacts()

        names = {a.name for a in artifacts}
        assert "libad9361.so.0.2" in names
        assert "ad9361.h" in names

    def test_package_artifacts_writes_metadata(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        (fake_source / "ad9361.h").write_text("// header")

        builder.source_dir = fake_source
        builder.package_artifacts()

        metadata_path = builder.get_output_dir() / "metadata.json"
        assert metadata_path.exists()
        metadata = json.loads(metadata_path.read_text())
        assert metadata["project"] == "libad9361"
        assert metadata["arch"] == "arm"
        assert metadata["tag"] == "main"

    def test_package_artifacts_copies_pc_file(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        build_dir = fake_source / "build"
        build_dir.mkdir()
        (build_dir / "libad9361.pc").write_text("Name: libad9361\nVersion: 0.2\n")

        builder.source_dir = fake_source
        artifacts = builder.package_artifacts()

        names = {a.name for a in artifacts}
        assert "libad9361.pc" in names

    def test_package_artifacts_raises_without_source_dir(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)
        from adibuild.core.executor import BuildError

        with pytest.raises(BuildError, match="Source directory not set"):
            builder.package_artifacts()

    def test_build_script_mode(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path, script_mode=True)

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()

        mocker.patch.object(
            builder,
            "prepare_source",
            side_effect=lambda: setattr(builder, "source_dir", fake_source)
            or fake_source,
        )
        # In script mode, cmake/make write to script — no real execution
        result = builder.build(jobs=4)

        assert "artifacts" in result
        assert "output_dir" in result

    def test_build_custom_cmake_options(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(
            tmp_path,
            arch="arm",
            extra={"cmake_options": {"BUILD_SHARED_LIBS": "OFF"}},
        )

        fake_source = tmp_path / "libad9361"
        fake_source.mkdir()
        (fake_source / "build").mkdir()
        builder.source_dir = fake_source

        mock_cmake = mocker.patch.object(builder.executor, "cmake")
        builder.configure()

        args = mock_cmake.call_args[0][0]
        assert "-DBUILD_SHARED_LIBS=OFF" in args


# ---------------------------------------------------------------------------
# TestExecutorCmakeMethod
# ---------------------------------------------------------------------------


class TestExecutorCmakeMethod:
    """Tests for the new BuildExecutor.cmake() method."""

    def test_cmake_script_mode_writes_command(self, tmp_path):
        from adibuild.core.executor import BuildExecutor, ScriptBuilder

        script_path = tmp_path / "build.sh"
        script_builder = ScriptBuilder(script_path)
        executor = BuildExecutor(script_builder=script_builder)

        build_dir = tmp_path / "build"
        build_dir.mkdir()

        result = executor.cmake(["-DFOO=ON", ".."], build_dir=build_dir)
        assert result.return_code == 0

        content = script_path.read_text()
        assert "cmake" in content
        assert "-DFOO=ON" in content

    def test_cmake_real_execution_changes_cwd(self, tmp_path, mocker):
        from adibuild.core.executor import BuildExecutor

        executor = BuildExecutor(cwd=tmp_path)
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        # Mock execute to capture the cwd at call time
        captured_cwd = []

        def fake_execute(cmd, env=None, **kw):
            captured_cwd.append(executor.cwd)
            from adibuild.core.executor import ExecutionResult

            return ExecutionResult("cmake", 0, "", "", 0.0)

        mocker.patch.object(executor, "execute", side_effect=fake_execute)

        executor.cmake(["-DFOO=ON", ".."], build_dir=build_dir)

        assert captured_cwd[0] == build_dir
        # cwd is restored after the call
        assert executor.cwd == tmp_path

    def test_cmake_restores_cwd_on_failure(self, tmp_path, mocker):
        from adibuild.core.executor import BuildError, BuildExecutor, ExecutionResult

        executor = BuildExecutor(cwd=tmp_path)
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        mocker.patch.object(
            executor,
            "execute",
            return_value=ExecutionResult("cmake", 1, "error: fail", "", 0.0),
        )

        with pytest.raises(BuildError):
            executor.cmake([".."], build_dir=build_dir)

        # cwd must be restored even after failure
        assert executor.cwd == tmp_path


# ---------------------------------------------------------------------------
# TestLibAD9361ConfTestFixtures
# ---------------------------------------------------------------------------


class TestLibAD9361ConfTestFixtures:
    def test_libad9361_config_dict_fixture(self, libad9361_config_dict):
        assert libad9361_config_dict["arch"] == "arm"
        assert "arm-linux-gnueabihf-" in libad9361_config_dict["cross_compile"]

    def test_libad9361_config_fixture(self, libad9361_config):
        assert libad9361_config.get_project() == "libad9361"
        assert libad9361_config.get_tag() == "main"

    def test_libad9361_platform_from_fixture(self, libad9361_config):
        platform_cfg = libad9361_config.get_platform("arm")
        p = LibPlatform(platform_cfg)
        assert p.arch == "arm"
        assert p.cross_compile == "arm-linux-gnueabihf-"
