"""Xilinx Zynq (ARM32) platform implementation."""

from adibuild.platforms.base import Platform


class ZynqPlatform(Platform):
    """Xilinx Zynq (ARM32) platform configuration."""

    def __init__(self, config: dict[str, any]):
        """
        Initialize ZynqPlatform.

        Args:
            config: Platform configuration dictionary
        """
        super().__init__(config)

        # Validate required configuration
        if self.arch != "arm":
            raise ValueError(f"ZynqPlatform requires arch='arm', got '{self.arch}'")

        if self.kernel_target not in ["uImage", "zImage"]:
            self.logger.warning(
                f"Unusual kernel target '{self.kernel_target}' for Zynq platform. "
                "Typically 'uImage' or 'zImage' is used."
            )

    def get_make_env(self) -> dict[str, str]:
        """
        Get environment variables for make.

        Returns:
            Dictionary of environment variables
        """
        # Get toolchain and use its cross-compile prefix
        toolchain = self.get_toolchain()
        cross_compile = toolchain.cross_compile_arm32 or self.cross_compile

        # Start with toolchain environment variables
        env = dict(toolchain.env_vars)

        # Add platform-specific variables (these take precedence)
        env.update(
            {
                "ARCH": self.arch,
                "CROSS_COMPILE": cross_compile,
            }
        )

        # Add LOADADDR for uImage builds (kernel Makefile converts this to UIMAGE_LOADADDR)
        if self.kernel_target == "uImage" and self.uimage_loadaddr:
            env["LOADADDR"] = self.uimage_loadaddr

        return env

    def get_default_dtb_path(self) -> str:
        """
        Get default DTB path for Zynq platform.

        Returns:
            Default DTB path
        """
        return "arch/arm/boot/dts"

    def get_default_kernel_image_path(self) -> str:
        """
        Get default kernel image path for Zynq platform.

        Returns:
            Default kernel image path
        """
        if self.kernel_target == "uImage":
            return "arch/arm/boot/uImage"
        elif self.kernel_target == "zImage":
            return "arch/arm/boot/zImage"
        else:
            return f"arch/arm/boot/{self.kernel_target}"

    @property
    def dtb_path(self) -> str:
        """
        Get DTB path (with default fallback).

        Returns:
            DTB path
        """
        return self.config.get("dtb_path") or self.get_default_dtb_path()

    @property
    def kernel_image_path(self) -> str:
        """
        Get kernel image path (with default fallback).

        Returns:
            Kernel image path
        """
        return (
            self.config.get("kernel_image_path") or self.get_default_kernel_image_path()
        )
