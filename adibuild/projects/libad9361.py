"""libad9361-iio CMake library builder."""

import json
import os
import shutil
from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.platforms.lib import LibPlatform
from adibuild.utils.git import GitRepository

#: Default upstream repository URL.
DEFAULT_REPO_URL = "https://github.com/analogdevicesinc/libad9361-iio.git"

#: Subdirectory name used when caching the repo under ``~/.adibuild/repos/``.
REPO_CACHE_NAME = "libad9361"


class LibAD9361Builder(BuilderBase):
    """
    Builder for the libad9361-iio C library.

    Clones `<https://github.com/analogdevicesinc/libad9361-iio>`_ (or a
    user-supplied mirror/fork), configures it with CMake, and builds a
    shared library suitable for the requested target architecture.

    **Build pipeline**::

        prepare_source() → configure() → build() → package_artifacts()

    **Output artifacts** (collected into ``get_output_dir()``)::

        libad9361.so.<version>   # versioned shared library
        libad9361.so.<soversion> # soname symlink
        libad9361.so             # development symlink
        ad9361.h                 # public header
        libad9361.pc             # pkg-config file
        metadata.json            # build metadata

    Args:
        config: :class:`~adibuild.core.config.BuildConfig` instance.
        platform: :class:`~adibuild.platforms.lib.LibPlatform` instance.
        work_dir: Override working/cache directory (default: ``~/.adibuild/work``).
        script_mode: When ``True`` write a bash script instead of executing.
    """

    def __init__(
        self,
        config: BuildConfig,
        platform: Platform,
        work_dir: Path | None = None,
        script_mode: bool = False,
    ):
        super().__init__(config, platform, work_dir, script_mode=script_mode)
        self.source_dir: Path | None = None

    # ------------------------------------------------------------------
    # BuilderBase interface
    # ------------------------------------------------------------------

    def prepare_source(self) -> Path:
        """
        Clone or update the libad9361-iio repository.

        The repo is cached at ``~/.adibuild/repos/libad9361/``.  A local path
        can be supplied via ``repository:`` in the project config to bypass
        cloning.

        Returns:
            Path to the repository root.
        """
        self.logger.info("Preparing libad9361-iio source...")

        repo_url = self.config.get_repository() or DEFAULT_REPO_URL
        tag = self.config.get_tag()

        repo_cache = Path.home() / ".adibuild" / "repos" / REPO_CACHE_NAME
        self.source_dir = repo_cache

        self.repo = GitRepository(
            repo_url, repo_cache, script_builder=self.executor.script_builder
        )

        self.logger.info("Ensuring repository is ready...")
        self.repo.ensure_repo(ref=tag)

        if not self.script_mode and not self.source_dir.exists():
            raise BuildError(f"Failed to prepare source at {self.source_dir}")

        commit = self.repo.get_commit_sha()
        self.logger.info(f"Using commit {commit[:8]}")

        return self.source_dir

    def configure(self) -> None:
        """
        Run CMake configuration inside ``<source>/build/``.

        CMake variables are derived from the platform's
        :meth:`~adibuild.platforms.lib.LibPlatform.get_cmake_args`.
        Documentation, Python bindings, and packaging targets are disabled
        for CI/cross-build compatibility.
        """
        if not self.source_dir:
            self.prepare_source()

        build_dir = self.source_dir / "build"
        self.make_directory(build_dir)

        cmake_args = list(self.platform.get_cmake_args())

        # Wire up libiio if the platform provides a pre-built path
        if isinstance(self.platform, LibPlatform) and self.platform.libiio_path:
            libiio = self.platform.libiio_path
            cmake_args += [
                f"-DLIBIIO_INCLUDE_DIR={libiio}/include",
                f"-DLIBIIO_LIBRARIES={libiio}/lib/libiio.so",
            ]

        # Disable targets that require additional tools or are irrelevant for CI
        cmake_args += [
            "-DWITH_DOC=OFF",
            "-DPYTHON_BINDINGS=OFF",
            "-DENABLE_PACKAGING=OFF",
            "..",  # source dir is parent of build dir
        ]

        self.logger.info("Running cmake configure...")
        self.executor.cmake(cmake_args, build_dir=build_dir)

    def build(self, clean_before: bool = False, jobs: int | None = None) -> dict:
        """
        Configure and build libad9361-iio.

        Args:
            clean_before: Remove the ``build/`` directory before configuring.
            jobs: Parallel make jobs (defaults to ``build.parallel_jobs``).

        Returns:
            Dict with keys ``artifacts`` (list of paths) and ``output_dir``.
        """
        self.prepare_source()

        if clean_before:
            build_dir = self.source_dir / "build"
            if not self.script_mode and build_dir.exists():
                shutil.rmtree(build_dir)
            elif self.script_mode:
                self.executor.execute(f"rm -rf {build_dir}")

        self.configure()

        build_dir = self.source_dir / "build"
        jobs = jobs or self.config.get_parallel_jobs()

        self.logger.info(f"Building libad9361-iio with {jobs} job(s)...")
        self.executor.make(jobs=jobs, extra_args=["-C", str(build_dir)])

        artifacts = self.package_artifacts()
        output_dir = self.get_output_dir()

        self.logger.info(f"Build complete. {len(artifacts)} artifact(s) in {output_dir}")
        return {
            "artifacts": [str(a) for a in artifacts],
            "output_dir": str(output_dir),
        }

    def package_artifacts(self) -> list[Path]:
        """
        Copy build outputs to the configured output directory.

        Collects:
        - ``libad9361.so*`` (shared library + symlinks)
        - ``ad9361.h`` (public header, from source root)
        - ``*.pc`` (pkg-config file)

        Returns:
            List of paths to files/symlinks placed in the output directory.
        """
        if not self.source_dir:
            raise BuildError("Source directory not set; call prepare_source() first.")

        build_dir = self.source_dir / "build"
        output_dir = self.get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        artifacts: list[Path] = []

        if not self.script_mode:
            # Shared library files and symlinks
            for so_file in sorted(build_dir.glob("libad9361.so*")):
                dst = output_dir / so_file.name
                if so_file.is_symlink():
                    link_target = os.readlink(so_file)
                    if dst.exists() or dst.is_symlink():
                        dst.unlink()
                    dst.symlink_to(link_target)
                else:
                    shutil.copy2(so_file, dst)
                artifacts.append(dst)

            # Public header (lives in source root)
            header = self.source_dir / "ad9361.h"
            if header.exists():
                dst = output_dir / "ad9361.h"
                shutil.copy2(header, dst)
                artifacts.append(dst)

            # pkg-config file
            for pc_file in build_dir.glob("*.pc"):
                dst = output_dir / pc_file.name
                shutil.copy2(pc_file, dst)
                artifacts.append(dst)

            # Write metadata
            metadata = {
                "project": "libad9361",
                "tag": self.config.get_tag(),
                "arch": self.platform.arch,
                "artifacts": [a.name for a in artifacts],
            }
            (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        return artifacts

    def clean(self, deep: bool = False) -> None:
        """
        Clean the build directory.

        Args:
            deep: If ``True``, remove the entire ``build/`` directory tree.
                  If ``False``, run ``make clean`` inside it.
        """
        if not self.source_dir:
            self.prepare_source()

        build_dir = self.source_dir / "build"

        if deep:
            if self.script_mode:
                self.executor.execute(f"rm -rf {build_dir}")
            else:
                shutil.rmtree(build_dir, ignore_errors=True)
            self.logger.info("Deep clean: removed build directory.")
        else:
            if build_dir.exists() or self.script_mode:
                self.executor.make(target="clean", extra_args=["-C", str(build_dir)])
            self.logger.info("Clean complete.")

    def get_output_dir(self) -> Path:
        """
        Return the output directory for this build.

        Format: ``<output_dir>/libad9361-<tag>-<arch>/``
        """
        tag = self.config.get_tag() or "unknown"
        arch = self.platform.arch
        output_base = Path(self.config.get("build.output_dir", "./build"))
        output_dir = output_base / f"libad9361-{tag}-{arch}"
        if not self.script_mode:
            output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
