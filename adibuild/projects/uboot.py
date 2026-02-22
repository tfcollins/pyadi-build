"""U-Boot bootloader builder."""

from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.utils.git import GitRepository

#: Default upstream repository URL.
DEFAULT_REPO_URL = "https://github.com/analogdevicesinc/u-boot.git"

#: Subdirectory name used when caching the repo under ``~/.adibuild/repos/``.
REPO_CACHE_NAME = "uboot"


class UBootBuilder(BuilderBase):
    """
    Builder for U-Boot bootloader.

    Clones `<https://github.com/analogdevicesinc/u-boot>`_
    and builds the u-boot.elf for Zynq/ZynqMP.
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
        """Clone or update the U-Boot repository."""
        self.logger.info("Preparing U-Boot source...")

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
        """Configure U-Boot with defconfig."""
        if not self.source_dir:
            self.prepare_source()

        defconfig = self.config.get("uboot.defconfig")
        if not defconfig:
            if self.platform.__class__.__name__ == "VersalPlatform":
                defconfig = "xilinx_versal_virt_defconfig"
            elif self.platform.arch == "arm64":
                defconfig = "xilinx_zynqmp_virt_defconfig"
            else:
                defconfig = "zynq_adi_defconfig"

        self.logger.info(f"Configuring U-Boot with {defconfig}...")
        self.executor.make(
            defconfig,
            env=self.platform.get_make_env(),
            extra_args=["-C", str(self.source_dir)],
        )

    def validate_environment(self) -> bool:
        """Validate build environment for U-Boot."""
        super().validate_environment()
        # U-Boot needs some extra tools for modern versions (especially for pylibfdt)
        self.executor.check_tools(["swig", "bison", "flex", "pkg-config", "bc"])

        # Check for setuptools (needed for pylibfdt and binman)
        import sys

        res = self.executor.execute(
            f'{sys.executable} -c "import setuptools"', stream_output=False
        )
        if res.failed:
            raise BuildError(
                "Required Python package 'setuptools' not found. "
                "Please install it using 'pip install setuptools' or 'apt install python3-setuptools'."
            )

        # Check for pkg_resources (needed by binman)
        res = self.executor.execute(
            f'{sys.executable} -c "import pkg_resources"', stream_output=False
        )
        if res.failed:
            raise BuildError(
                "Required Python package 'pkg_resources' not found (usually provided by setuptools < 60.0.0). "
                "Binman requires this to run."
            )

        # Check for gnutls (needed for tools/mkeficapsule)
        res = self.executor.execute("pkg-config --exists gnutls", stream_output=False)
        if res.failed:
            raise BuildError(
                "Required library 'gnutls' not found (pkg-config check failed). "
                "Please install 'libgnutls28-dev' (on Debian/Ubuntu) or equivalent."
            )

        return True

    def build(
        self,
        clean_before: bool = False,
        jobs: int | None = None,
        env_overrides: dict[str, str] | None = None,
    ) -> dict:
        """Build U-Boot (u-boot.elf)."""
        self.prepare_source()

        if clean_before:
            self.clean(deep=True)

        self.configure()

        jobs = jobs or self.config.get_parallel_jobs()
        self.logger.info(f"Building U-Boot with {jobs} jobs...")

        # U-Boot build output targets
        # ZynqMP: u-boot.elf
        # Zynq: u-boot.img, u-boot.elf

        env = self.platform.get_make_env()
        if env_overrides:
            env.update(env_overrides)

        self.executor.make(jobs=jobs, env=env, extra_args=["-C", str(self.source_dir)])

        output_dir = self.get_output_dir()
        self.make_directory(output_dir)

        artifacts = {}

        targets = ["u-boot.elf", "u-boot.img", "u-boot.bin", "u-boot"]
        for target in targets:
            src = self.source_dir / target
            if src.exists() or self.script_mode:
                dst = output_dir / target
                self.copy_file(src, dst)
                artifacts[target] = str(dst)

        return {
            "artifacts": artifacts,
            "output_dir": str(output_dir),
        }

    def clean(self, deep: bool = False) -> None:
        """Clean U-Boot build artifacts."""
        if not self.source_dir or not self.source_dir.exists():
            return

        target = "distclean" if deep else "clean"
        self.executor.make(
            target,
            env=self.platform.get_make_env(),
            extra_args=["-C", str(self.source_dir)],
        )

    def get_output_dir(self) -> Path:
        """Get output directory for U-Boot artifacts."""
        tag = self.config.get_tag() or "unknown"
        output_base = Path(self.config.get("build.output_dir", "./build"))
        return output_base / f"uboot-{tag}-{self.platform.arch}"
