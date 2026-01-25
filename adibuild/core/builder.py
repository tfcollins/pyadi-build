"""Abstract base class for project builders."""

from abc import ABC, abstractmethod
from pathlib import Path

from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildExecutor, ScriptBuilder
from adibuild.core.toolchain import ToolchainInfo
from adibuild.platforms.base import Platform
from adibuild.utils.logger import get_logger


class BuilderBase(ABC):
    """Abstract base class for project builders."""

    def __init__(
        self,
        config: BuildConfig,
        platform: Platform,
        work_dir: Path | None = None,
        script_mode: bool = False,
    ):
        """
        Initialize BuilderBase.

        Args:
            config: Build configuration
            platform: Target platform
            work_dir: Working directory (defaults to ~/.adibuild/work)
            script_mode: If True, generate bash script instead of executing
        """
        self.config = config
        self.platform = platform
        self.work_dir = work_dir or (Path.home() / ".adibuild" / "work")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.script_mode = script_mode

        self.logger = get_logger(f"adibuild.builder.{self.__class__.__name__}")

        # Initialize script builder if in script mode
        script_builder = None
        if self.script_mode:
            script_path = (
                self.work_dir / f"build_{self.config.get_project()}_{self.platform.arch}.sh"
            )
            script_builder = ScriptBuilder(script_path)
            self.logger.info(f"Generating build script at {script_path}")

        # Initialize executor with log file and optional script builder
        log_file = self.work_dir / f"build-{self.platform.arch}.log"
        self.executor = BuildExecutor(log_file=log_file, script_builder=script_builder)

        self._toolchain: ToolchainInfo | None = None

    def copy_file(self, src: Path, dst: Path) -> None:
        """Copy file (handles script generation)."""
        if self.script_mode:
            self.executor.execute(f"cp {src} {dst}")
        else:
            import shutil

            shutil.copy(src, dst)

    def download_file(self, url: str, dst: Path) -> None:
        """Download file (handles script generation)."""
        if self.script_mode:
            self.executor.execute(f"wget -O {dst} {url} || curl -L -o {dst} {url}")
        else:
            import requests

            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(dst, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

    def make_directory(self, path: Path) -> None:
        """Create directory (handles script generation)."""
        if self.script_mode:
            self.executor.execute(f"mkdir -p {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)

    @property
    def toolchain(self) -> ToolchainInfo:
        """
        Get toolchain for this builder.

        Returns:
            ToolchainInfo
        """
        if not self._toolchain:
            self._toolchain = self.platform.get_toolchain()
        return self._toolchain

    @abstractmethod
    def prepare_source(self) -> Path:
        """
        Prepare source code for building.

        Returns:
            Path to prepared source directory
        """
        pass

    @abstractmethod
    def configure(self) -> None:
        """Configure the build."""
        pass

    @abstractmethod
    def build(self) -> None:
        """Execute the build."""
        pass

    @abstractmethod
    def clean(self, deep: bool = False) -> None:
        """
        Clean build artifacts.

        Args:
            deep: If True, perform deep clean (mrproper)
        """
        pass

    def validate_environment(self) -> bool:
        """
        Validate build environment and prerequisites.

        Returns:
            True if environment is valid

        Raises:
            BuildError: If environment validation fails
        """
        self.logger.info("Validating build environment...")

        # Check basic build tools
        self.executor.check_tools(["make", "gcc", "git"])

        # Validate platform and toolchain
        self.platform.validate_toolchain()

        self.logger.info("Environment validation passed")
        return True

    def get_output_dir(self) -> Path:
        """
        Get output directory for build artifacts.

        Returns:
            Path to output directory
        """
        output_base = Path(self.config.get("build.output_dir", "./build"))
        output_dir = (
            output_base
            / f"{self.config.get_project()}-{self.config.get_tag()}-{self.platform.arch}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"project={self.config.get_project()}, "
            f"platform={self.platform.arch})"
        )
