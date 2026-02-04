"""Base platform abstraction for different hardware architectures."""

from abc import ABC, abstractmethod
from pathlib import Path

from adibuild.core.toolchain import ToolchainInfo, select_toolchain
from adibuild.utils.logger import get_logger


class PlatformError(Exception):
    """Exception raised for platform errors."""

    pass


class Platform(ABC):
    """Abstract base class for hardware platforms."""

    def __init__(self, config: dict[str, any]):
        """
        Initialize Platform.

        Args:
            config: Platform configuration dictionary
        """
        self.config = config
        self.logger = get_logger(f"adibuild.platform.{self.__class__.__name__}")
        self._toolchain: ToolchainInfo | None = None

    @property
    def arch(self) -> str:
        """
        Get target architecture.

        Returns:
            Architecture string (e.g., 'arm', 'arm64')
        """
        arch = self.config.get("arch")
        if not arch:
            raise PlatformError("Architecture not specified in platform configuration")
        return arch

    @property
    def cross_compile(self) -> str:
        """
        Get cross-compile prefix.

        Returns:
            Cross-compile prefix (e.g., 'arm-linux-gnueabihf-')
        """
        cross_compile = self.config.get("cross_compile")
        if not cross_compile:
            raise PlatformError(
                "Cross-compile prefix not specified in platform configuration"
            )
        return cross_compile

    @property
    def defconfig(self) -> str:
        """
        Get default kernel configuration.

        Returns:
            Defconfig name
        """
        defconfig = self.config.get("defconfig")
        if not defconfig:
            raise PlatformError("Defconfig not specified in platform configuration")
        return defconfig

    @property
    def kernel_target(self) -> str:
        """
        Get kernel build target.

        Returns:
            Kernel target (e.g., 'uImage', 'Image')
        """
        target = self.config.get("kernel_target")
        if not target:
            raise PlatformError("Kernel target not specified in platform configuration")
        return target

    @property
    def dtbs(self) -> list[str]:
        """
        Get list of device tree blobs to build.

        Returns:
            List of DTB filenames
        """
        return self.config.get("dtbs", [])

    @property
    def uimage_loadaddr(self) -> str | None:
        """
        Get uImage load address.

        Returns:
            Load address in hex format (e.g., '0x8000') or None
        """
        return self.config.get("uimage_loadaddr")

    @property
    def dtb_path(self) -> str | None:
        """
        Get relative path to DTB directory in kernel source.

        Returns:
            Relative path to DTB directory
        """
        return self.config.get("dtb_path")

    @property
    def kernel_image_path(self) -> str | None:
        """
        Get relative path to kernel image in kernel source.

        Returns:
            Relative path to kernel image
        """
        return self.config.get("kernel_image_path")

    @abstractmethod
    def get_make_env(self) -> dict[str, str]:
        """
        Get environment variables for make.

        Returns:
            Dictionary of environment variables
        """
        pass

    def get_toolchain(self, tool_version: str | None = None) -> ToolchainInfo:
        """
        Get or select toolchain for this platform.

        Args:
            tool_version: Preferred tool version (e.g., "2023.2") for toolchain selection.
                          If not specified, checks self.config.get("tool_version").

        Returns:
            ToolchainInfo for selected toolchain
        """
        if self._toolchain:
            return self._toolchain

        # Get toolchain preferences from config
        toolchain_config = self.config.get("toolchain", {})
        preferred = toolchain_config.get("preferred", "vivado")
        fallbacks = toolchain_config.get("fallback", ["arm", "system"])

        # Use tool_version from parameter, or fall back to config
        if not tool_version:
            tool_version = self.config.get("tool_version")

        # Get strict_version from config (defaults to False)
        strict_version = self.config.get("strict_version", False)

        self.logger.info(f"Selecting toolchain for {self.arch} architecture")
        if tool_version:
            self.logger.info(f"Preferred tool version: {tool_version}")
            if strict_version:
                self.logger.info("Strict version matching enabled")

        self._toolchain = select_toolchain(
            preferred, fallbacks, tool_version, strict_version
        )

        return self._toolchain

    def validate_toolchain(self) -> bool:
        """
        Validate that toolchain is available and suitable for this platform.

        Returns:
            True if toolchain is valid

        Raises:
            PlatformError: If toolchain is not suitable
        """
        toolchain = self.get_toolchain()

        # Check if toolchain supports this architecture
        if self.arch == "arm" and not toolchain.cross_compile_arm32:
            raise PlatformError(
                f"Toolchain {toolchain.type} does not support ARM32 architecture"
            )
        elif self.arch == "arm64" and not toolchain.cross_compile_arm64:
            raise PlatformError(
                f"Toolchain {toolchain.type} does not support ARM64 architecture"
            )
        elif self.arch == "microblaze" and not toolchain.cross_compile_microblaze:
            raise PlatformError(
                f"Toolchain {toolchain.type} does not support MicroBlaze architecture"
            )

        self.logger.info(
            f"Toolchain validation passed: {toolchain.type} v{toolchain.version}"
        )
        return True

    def get_dtb_full_paths(self, kernel_source: Path) -> list[Path]:
        """
        Get full paths to DTB files in kernel source tree.

        Args:
            kernel_source: Path to kernel source directory

        Returns:
            List of full paths to DTB files
        """
        if not self.dtb_path:
            raise PlatformError("DTB path not specified in platform configuration")

        dtb_dir = kernel_source / self.dtb_path
        dtb_paths = []

        for dtb in self.dtbs:
            dtb_file = dtb_dir / dtb
            dtb_paths.append(dtb_file)

        return dtb_paths

    def get_dtb_make_target(self, dtb_filename: str) -> str:
        """
        Get the make target for a DTB file.

        The kernel Makefile requires DTB targets to include the subdirectory
        relative to arch/<arch>/boot/dts/. This method extracts that subdirectory
        from dtb_path and prepends it to the filename.

        Examples:
            dtb_path="arch/arm/boot/dts", filename="zynq-zc702.dtb"
            -> Returns: "zynq-zc702.dtb"

            dtb_path="arch/arm64/boot/dts/xilinx", filename="zynqmp-zcu102.dtb"
            -> Returns: "xilinx/zynqmp-zcu102.dtb"

        Args:
            dtb_filename: DTB filename (e.g., "zynqmp-zcu102.dtb")

        Returns:
            Make target with subdirectory if needed (e.g., "xilinx/zynqmp-zcu102.dtb")
        """
        if not self.dtb_path:
            return dtb_filename

        # Extract subdirectory after arch/<arch>/boot/dts/
        # e.g., "arch/arm64/boot/dts/xilinx" -> "xilinx"
        #       "arch/arm/boot/dts" -> ""
        parts = Path(self.dtb_path).parts

        # Find "dts" in the path
        dts_idx = -1
        for i, part in enumerate(parts):
            if part == "dts":
                dts_idx = i
                break

        # If there are parts after "dts/", they form the subdirectory
        if dts_idx >= 0 and dts_idx < len(parts) - 1:
            subdirs = parts[dts_idx + 1 :]
            subdir_path = "/".join(subdirs)
            return f"{subdir_path}/{dtb_filename}"
        else:
            # No subdirectory, just return filename
            return dtb_filename

    def get_kernel_image_full_path(self, kernel_source: Path) -> Path:
        """
        Get full path to kernel image in kernel source tree.

        Args:
            kernel_source: Path to kernel source directory

        Returns:
            Path to kernel image
        """
        if not self.kernel_image_path:
            raise PlatformError(
                "Kernel image path not specified in platform configuration"
            )

        return kernel_source / self.kernel_image_path

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}(arch={self.arch}, "
            f"target={self.kernel_target}, defconfig={self.defconfig})"
        )
