"""iio-emu CMake builder."""

import json
import shutil
from pathlib import Path
from typing import Any

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.platforms.lib import LibPlatform
from adibuild.utils.git import GitRepository

#: Default upstream repository URL.
DEFAULT_REPO_URL = "https://github.com/analogdevicesinc/iio-emu.git"

#: Subdirectory name used when caching the repo under ``~/.adibuild/repos/``.
REPO_CACHE_NAME = "iio-emu"


class IIOEmuBuilder(BuilderBase):
    """
    Builder for the iio-emu server application.

    Clones `<https://github.com/analogdevicesinc/iio-emu>`_ (or a
    user-supplied mirror/fork), configures it with CMake, and builds the
    emulator executable suitable for the requested target architecture.

    **Build pipeline**::

        prepare_source() → configure() → build() → package_artifacts()

    **Output artifacts** (collected into ``get_output_dir()``)::

        iio-emu                  # main emulator executable
        iio-emu_gen_xml          # XML generation tool
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
        Clone or update the iio-emu repository.

        The repo is cached at ``~/.adibuild/repos/iio-emu/``.  A local path
        can be supplied via ``repository:`` in the project config to bypass
        cloning.

        Returns:
            Path to the repository root.
        """
        self.logger.info("Preparing iio-emu source...")

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
        """
        if not self.source_dir:
            self.prepare_source()

        build_dir = self.source_dir / "build"
        self.make_directory(build_dir)

        cmake_args = list(self.platform.get_cmake_args())

        # Wire up libtinyiiod if the platform provides a pre-built path
        if isinstance(self.platform, LibPlatform) and self.platform.tinyiiod_path:
            tinyiiod = self.platform.tinyiiod_path
            cmake_args += [
                f"-DTINYIIOD_INCLUDE_DIR={tinyiiod}/include",
                f"-DTINYIIOD_LIBRARIES={tinyiiod}/lib/libtinyiiod.so",
            ]

        # Wire up libiio if the platform provides a pre-built path
        if isinstance(self.platform, LibPlatform) and self.platform.libiio_path:
            libiio = self.platform.libiio_path
            cmake_args += [
                f"-DLIBIIO_INCLUDE_DIR={libiio}/include",
                f"-DLIBIIO_LIBRARIES={libiio}/lib/libiio.so",
            ]

        cmake_args += [
            "..",  # source dir is parent of build dir
        ]

        self.logger.info("Running cmake configure...")
        self.executor.cmake(cmake_args, build_dir=build_dir)

    def build(
        self, clean_before: bool = False, jobs: int | None = None
    ) -> dict[str, Any]:
        """
        Configure and build iio-emu.

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

        self.logger.info(f"Building iio-emu with {jobs} job(s)...")
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
        - ``iio-emu`` (executable)
        - ``iio-emu_gen_xml`` (executable)

        Returns:
            List of paths to files placed in the output directory.
        """
        if not self.source_dir:
            raise BuildError("Source directory not set; call prepare_source() first.")

        build_dir = self.source_dir / "build"
        output_dir = self.get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        artifacts: list[Path] = []

        if not self.script_mode:
            # Executables
            for exe_name in ["iio-emu", "iio-emu_gen_xml"]:
                exe_file = build_dir / exe_name
                if exe_file.exists():
                    dst = output_dir / exe_name
                    shutil.copy2(exe_file, dst)
                    artifacts.append(dst)

            # Write metadata
            metadata = {
                "project": "iio-emu",
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

        Format: ``<output_dir>/iio-emu-<tag>-<arch>/``
        """
        tag = self.config.get_tag() or "unknown"
        arch = self.platform.arch
        output_base = Path(self.config.get("build.output_dir", "./build"))
        output_dir = output_base / f"iio-emu-{tag}-{arch}"
        if not self.script_mode:
            output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
