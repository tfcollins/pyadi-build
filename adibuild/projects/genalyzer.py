"""Genalyzer CMake library builder."""

import json
import os
import shutil
from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.utils.git import GitRepository

#: Default upstream repository URL.
DEFAULT_REPO_URL = "https://github.com/analogdevicesinc/genalyzer.git"

#: Subdirectory name used when caching the repo under ``~/.adibuild/repos/``.
REPO_CACHE_NAME = "genalyzer"


class GenalyzerBuilder(BuilderBase):
    """
    Builder for the genalyzer C++ DSP analysis library.

    Clones `<https://github.com/analogdevicesinc/genalyzer>`_ (or a
    user-supplied mirror/fork), configures it with CMake, and builds a
    shared library suitable for the requested target architecture.

    The primary dependency is **FFTW3**. For cross-compiled targets, supply
    the path to a pre-built FFTW3 via ``fftw_path`` in the platform config
    (must contain ``include/`` and ``lib/`` subdirectories).

    **Build pipeline**::

        prepare_source() → configure() → build() → package_artifacts()

    **Output artifacts** (collected into ``get_output_dir()``)::

        libgenalyzer_plus_plus.so.<version>  # versioned shared library
        libgenalyzer_plus_plus.so            # development symlink
        include/                             # public headers directory
        metadata.json                        # build metadata

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
        Clone or update the genalyzer repository.

        The repo is cached at ``~/.adibuild/repos/genalyzer/``.  A local path
        can be supplied via ``repository:`` in the project config to bypass
        cloning.

        Returns:
            Path to the repository root.
        """
        self.logger.info("Preparing genalyzer source...")

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
        Documentation and tests/examples are disabled for CI builds.
        If ``fftw_path`` is set in the platform config, FFTW3 headers and
        libraries are injected via ``-DFFTW_INCLUDE_DIRS`` and
        ``-DFFTW_LIBRARIES``.
        """
        if not self.source_dir:
            self.prepare_source()

        build_dir = self.source_dir / "build"
        self.make_directory(build_dir)

        cmake_args = list(self.platform.get_cmake_args())

        # Wire up FFTW3 if the platform config provides a pre-built path
        fftw_path = self.platform.config.get("fftw_path")
        if fftw_path:
            fftw = Path(fftw_path)
            cmake_args += [
                f"-DFFTW_INCLUDE_DIRS={fftw}/include",
                f"-DFFTW_LIBRARIES={fftw}/lib/libfftw3.so",
            ]

        # Disable targets that require additional tools or aren't needed for CI
        cmake_args += [
            "-DBUILD_DOC=OFF",
            "-DBUILD_TESTS_EXAMPLES=OFF",
            "..",  # source dir is parent of build dir
        ]

        self.logger.info("Running cmake configure...")
        self.executor.cmake(cmake_args, build_dir=build_dir)

    def build(self, clean_before: bool = False, jobs: int | None = None) -> dict:
        """
        Configure and build genalyzer.

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

        self.logger.info(f"Building genalyzer with {jobs} job(s)...")
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
        - ``libgenalyzer*.so*`` (shared library + symlinks)
        - ``include/`` directory contents (public headers, ``.hpp`` and ``.h``)
        - ``*.pc`` (pkg-config file, if generated)

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
            for so_file in sorted(build_dir.glob("libgenalyzer*.so*")):
                dst = output_dir / so_file.name
                if so_file.is_symlink():
                    link_target = os.readlink(so_file)
                    if dst.exists() or dst.is_symlink():
                        dst.unlink()
                    dst.symlink_to(link_target)
                else:
                    shutil.copy2(so_file, dst)
                artifacts.append(dst)

            # Also check src/ subdirectory (cmake sometimes places the .so there)
            src_build = build_dir / "src"
            if src_build.is_dir():
                for so_file in sorted(src_build.glob("libgenalyzer*.so*")):
                    dst = output_dir / so_file.name
                    if dst.exists() or dst.is_symlink():
                        continue  # already copied from top-level
                    if so_file.is_symlink():
                        link_target = os.readlink(so_file)
                        dst.symlink_to(link_target)
                    else:
                        shutil.copy2(so_file, dst)
                    artifacts.append(dst)

            # Public headers (live in source root include/)
            include_src = self.source_dir / "include"
            if include_src.is_dir():
                include_dst = output_dir / "include"
                include_dst.mkdir(exist_ok=True)
                for hdr in include_src.iterdir():
                    if hdr.suffix in (".hpp", ".h"):
                        dst = include_dst / hdr.name
                        shutil.copy2(hdr, dst)
                        artifacts.append(dst)

            # pkg-config file (if generated)
            for pc_file in list(build_dir.glob("*.pc")) + list(build_dir.glob("**/*.pc")):
                dst = output_dir / pc_file.name
                shutil.copy2(pc_file, dst)
                artifacts.append(dst)

            # Write metadata
            metadata = {
                "project": "genalyzer",
                "tag": self.config.get_tag(),
                "arch": self.platform.arch,
                "artifacts": [str(a.relative_to(output_dir)) for a in artifacts],
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

        Format: ``<output_dir>/genalyzer-<tag>-<arch>/``
        """
        tag = self.config.get_tag() or "unknown"
        arch = self.platform.arch
        output_base = Path(self.config.get("build.output_dir", "./build"))
        output_dir = output_base / f"genalyzer-{tag}-{arch}"
        if not self.script_mode:
            output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
