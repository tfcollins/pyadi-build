"""no-OS bare-metal firmware builder."""

import json
from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.utils.git import GitRepository


class NoOSBuilder(BuilderBase):
    """Builder for no-OS bare-metal firmware projects."""

    def __init__(
        self,
        config: BuildConfig,
        platform: Platform,
        work_dir: Path | None = None,
        script_mode: bool = False,
    ):
        """
        Initialize NoOSBuilder.

        Args:
            config: Build configuration
            platform: Target platform configuration (must contain 'noos_project' and 'noos_platform')
            work_dir: Working directory
            script_mode: If True, generate bash script instead of executing
        """
        super().__init__(config, platform, work_dir, script_mode=script_mode)
        self.source_dir: Path | None = None

    def prepare_source(self) -> Path:
        """
        Prepare no-OS source code.

        Returns:
            Path to no-OS source directory
        """
        self.logger.info("Preparing no-OS source...")

        repo_url = self.config.get_repository()
        tag = self.config.get_tag()

        # Cache no-OS repo at ~/.adibuild/repos/noos/
        repo_cache = Path.home() / ".adibuild" / "repos" / "noos"
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
        """no-OS has no separate configure step; configuration is via make variables."""
        self.logger.info(
            "no-OS configuration is handled during build via make variables."
        )

    def build(self, clean_before: bool = False, jobs: int | None = None) -> dict:
        """
        Execute no-OS build.

        Args:
            clean_before: Run make clean before building
            jobs: Number of parallel jobs (defaults to config value)

        Returns:
            Dictionary with 'artifacts' and 'output_dir' keys
        """
        platform_config = self.platform.config
        noos_project = platform_config.get("noos_project")
        noos_platform = platform_config.get("noos_platform")

        if not noos_project:
            raise BuildError("'noos_project' not specified in platform configuration")
        if not noos_platform:
            raise BuildError("'noos_platform' not specified in platform configuration")

        self.logger.info(
            f"Starting no-OS build for project '{noos_project}' "
            f"on platform '{noos_platform}'..."
        )

        # 1. Prepare source
        self.prepare_source()

        # 2. Validate toolchain
        if not self.script_mode:
            self.platform.validate_toolchain()

        # 3. Set up project directory
        project_dir = self.source_dir / "projects" / noos_project

        if not self.script_mode and not project_dir.exists():
            raise BuildError(f"no-OS project directory not found: {project_dir}")

        # 4. Clean if requested
        if clean_before:
            self.logger.info("Cleaning project before build...")
            self.clean(deep=False)

        # 5. Copy hardware file if specified
        hw_file = self.platform.hardware_file
        if hw_file:
            if not self.script_mode and not hw_file.exists():
                raise BuildError(f"Hardware file not found: {hw_file}")
            dest = project_dir / hw_file.name
            self.logger.info(f"Copying hardware file {hw_file} -> {dest}")
            self.copy_file(hw_file, dest)

        # 6. Construct make variables
        make_vars = [
            f"PLATFORM={noos_platform}",
            f"NO-OS={self.source_dir}",  # explicit root avoids path resolution issues
        ]
        if self.platform.profile:
            make_vars.append(f"PROFILE={self.platform.profile}")
        make_vars.append(f"IIOD={'y' if self.platform.iiod else 'n'}")
        for k, v in self.platform.make_variables.items():
            make_vars.append(f"{k}={v}")

        if jobs is None:
            jobs = self.config.get_parallel_jobs()

        make_args = ["-C", str(project_dir)] + make_vars
        make_env = self.platform.get_make_env() or None

        # 7. Execute build
        self.logger.info(f"Building project in {project_dir}...")
        self.executor.make(target=None, extra_args=make_args, env=make_env, jobs=jobs)

        # 8. Package artifacts
        return self.package_artifacts(project_dir, noos_project, noos_platform)

    def package_artifacts(
        self, project_dir: Path, noos_project: str, noos_platform: str
    ) -> dict:
        """Collect and package build artifacts (.elf and .axf files)."""
        output_dir = self.get_output_dir()
        self.make_directory(output_dir)

        artifacts = {"elf": [], "axf": []}

        if not self.script_mode:
            for pattern in ["**/*.elf", "**/*.axf"]:
                for f in project_dir.glob(pattern):
                    dest = output_dir / f.name
                    self.copy_file(f, dest)
                    key = "elf" if f.suffix == ".elf" else "axf"
                    artifacts[key].append(str(dest))

            if not any(artifacts.values()):
                self.logger.warning("No artifacts (.elf or .axf) found after build.")

            metadata = {
                "project": noos_project,
                "platform": noos_platform,
                "tag": self.config.get_tag(),
                "artifacts": artifacts,
            }
            (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        else:
            # Script mode: generate copy commands
            self.executor.execute(
                f"find {project_dir} -name '*.elf' -exec cp {{}} {output_dir} \\;"
            )
            self.executor.execute(
                f"find {project_dir} -name '*.axf' -exec cp {{}} {output_dir} \\;"
            )

        self.logger.info(f"Artifacts packaged in {output_dir}")
        return {"artifacts": artifacts, "output_dir": str(output_dir)}

    def clean(self, deep: bool = False) -> None:
        """
        Clean build artifacts.

        Args:
            deep: If True, use 'reset' target (full clean); otherwise 'clean'
        """
        if not self.source_dir:
            self.prepare_source()

        platform_config = self.platform.config
        noos_project = platform_config.get("noos_project")

        if not noos_project:
            self.logger.warning(
                "Cannot clean: 'noos_project' not defined in platform config"
            )
            return

        project_dir = self.source_dir / "projects" / noos_project

        if not self.script_mode and not project_dir.exists():
            self.logger.warning(
                f"Project directory not found for cleaning: {project_dir}"
            )
            return

        target = "reset" if deep else "clean"
        self.logger.info(f"Cleaning project (target: {target})...")
        self.executor.make(target, extra_args=["-C", str(project_dir)])

    def get_output_dir(self) -> Path:
        """Get output directory for artifacts."""
        base_out = self.config.get("build.output_dir")
        output_base = Path(base_out) if base_out else (self.work_dir / "build")

        noos_project = self.platform.config.get("noos_project", "unknown")
        noos_platform = self.platform.config.get("noos_platform", "unknown")
        tag = self.config.get_tag() or "unknown"

        return output_base / f"noos-{noos_project}-{tag}-{noos_platform}"
