"""Abstract base class for project builders."""

from abc import ABC, abstractmethod
from pathlib import Path

from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildExecutor
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
    ):
        """
        Initialize BuilderBase.

        Args:
            config: Build configuration
            platform: Target platform
            work_dir: Working directory (defaults to ~/.adibuild/work)
        """
        self.config = config
        self.platform = platform
        self.work_dir = work_dir or (Path.home() / ".adibuild" / "work")
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger(f"adibuild.builder.{self.__class__.__name__}")

        # Initialize executor with log file
        log_file = self.work_dir / f"build-{self.platform.arch}.log"
        self.executor = BuildExecutor(log_file=log_file)

        self._toolchain: ToolchainInfo | None = None

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
