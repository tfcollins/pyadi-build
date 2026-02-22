"""ARM Trusted Firmware (ATF) builder."""

import shutil
from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.utils.git import GitRepository

#: Default upstream repository URL.
DEFAULT_REPO_URL = "https://github.com/analogdevicesinc/arm-trusted-firmware.git"

#: Subdirectory name used when caching the repo under ``~/.adibuild/repos/``.
REPO_CACHE_NAME = "atf"


class ATFBuilder(BuilderBase):
    """
    Builder for ARM Trusted Firmware (ATF).

    Clones `<https://github.com/analogdevicesinc/arm-trusted-firmware>`_
    and builds the bl31.elf runtime services for ZynqMP.
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

    def prepare_source(self) -> Path:
        """Clone or update the ATF repository."""
        self.logger.info("Preparing ATF source...")

        repo_url = self.config.get_repository() or DEFAULT_REPO_URL
        tag = self.config.get_tag() or "master"

        repo_cache = Path.home() / ".adibuild" / "repos" / REPO_CACHE_NAME
        self.source_dir = repo_cache

        self.repo = GitRepository(
            repo_url, repo_cache, script_builder=self.executor.script_builder
        )

        self.logger.info("Ensuring repository is ready...")
        self.repo.ensure_repo(ref=tag)

        if not self.script_mode and not self.source_dir.exists():
            raise BuildError(f"Failed to prepare source at {self.source_dir}")

        return self.source_dir

    def configure(self) -> None:
        """ATF configuration is handled via make variables."""
        self.logger.info("ATF configuration is handled during build.")

    def build(self, clean_before: bool = False, jobs: int | None = None) -> dict:
        """Build ATF (bl31.elf)."""
        self.prepare_source()

        if clean_before:
            self.clean(deep=True)

        jobs = jobs or self.config.get_parallel_jobs()

        # Determine PLAT from platform class
        platform_name = self.platform.__class__.__name__
        atf_plat = "zynqmp"
        reset_to_bl31 = "1"

        if "Versal" in platform_name:
            atf_plat = "versal"
            reset_to_bl31 = "0"  # Versal typically doesn't use this

        # Build bl31.elf
        make_vars = {
            "PLAT": atf_plat,
            "CROSS_COMPILE": self.platform.get_toolchain().cross_compile_arm64,
        }

        if reset_to_bl31 == "1":
            make_vars["RESET_TO_BL31"] = "1"

        # Override with any config-specified variables
        make_vars.update(self.config.get("atf.make_variables", {}))

        extra_args = [f"{k}={v}" for k, v in make_vars.items()]
        extra_args.extend(["-C", str(self.source_dir), "bl31"])

        self.logger.info(f"Building ATF for {atf_plat} with {jobs} jobs...")
        self.executor.make(
            jobs=jobs, extra_args=extra_args, env=self.platform.get_make_env()
        )

        output_dir = self.get_output_dir()
        self.make_directory(output_dir)

        # bl31.elf is typically in build/<plat>/release/bl31/bl31.elf
        bl31_src = self.source_dir / "build" / atf_plat / "release" / "bl31" / "bl31.elf"
        if not self.script_mode and not bl31_src.exists():
            # Try debug build if release not found
            bl31_src = (
                self.source_dir / "build" / atf_plat / "debug" / "bl31" / "bl31.elf"
            )

        bl31_dst = output_dir / "bl31.elf"
        self.copy_file(bl31_src, bl31_dst)

        # Also copy bl31.bin if it exists (U-Boot binman often needs it)
        # It's usually in build/<plat>/release/bl31.bin (parent of the bl31/ directory where .elf is)
        bl31_bin_src = bl31_src.parent.parent / "bl31.bin"
        if bl31_bin_src.exists() or self.script_mode:
            bl31_bin_dst = output_dir / "bl31.bin"
            self.copy_file(bl31_bin_src, bl31_bin_dst)
            return {
                "artifacts": {"bl31": str(bl31_dst), "bl31_bin": str(bl31_bin_dst)},
                "output_dir": str(output_dir),
            }

        return {
            "artifacts": {"bl31": str(bl31_dst)},
            "output_dir": str(output_dir),
        }

    def clean(self, deep: bool = False) -> None:
        """Clean ATF build artifacts."""
        if not self.source_dir or not self.source_dir.exists():
            return

        if deep:
            if self.script_mode:
                self.executor.execute(f"rm -rf {self.source_dir / 'build'}")
            else:
                shutil.rmtree(self.source_dir / "build", ignore_errors=True)
        else:
            self.executor.make("clean", extra_args=["PLAT=zynqmp"])

    def get_output_dir(self) -> Path:
        """Get output directory for ATF artifacts."""
        tag = self.config.get_tag() or "unknown"
        output_base = Path(self.config.get("build.output_dir", "./build"))
        return output_base / f"atf-{tag}-zynqmp"
