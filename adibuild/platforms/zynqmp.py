"""Xilinx ZynqMP (ARM64) platform implementation."""

from adibuild.platforms.base import Platform


class ZynqMPPlatform(Platform):
    """Xilinx ZynqMP (ARM64) platform configuration."""

    def __init__(self, config: dict[str, any]):
        """
        Initialize ZynqMPPlatform.

        Args:
            config: Platform configuration dictionary
        """
        super().__init__(config)

        # Validate required configuration
        if self.arch != "arm64":
            raise ValueError(f"ZynqMPPlatform requires arch='arm64', got '{self.arch}'")

        if self.kernel_target not in ["Image", "Image.gz"]:
            self.logger.warning(
                f"Unusual kernel target '{self.kernel_target}' for ZynqMP platform. "
                "Typically 'Image' or 'Image.gz' is used."
            )

    def get_make_env(self) -> dict[str, str]:
        """
        Get environment variables for make.

        Returns:
            Dictionary of environment variables
        """
        # Get toolchain and use its cross-compile prefix
        toolchain = self.get_toolchain()
        cross_compile = toolchain.cross_compile_arm64 or self.cross_compile

        # Start with toolchain environment variables
        env = dict(toolchain.env_vars)

        # Add platform-specific variables (these take precedence)
        env.update(
            {
                "ARCH": self.arch,
                "CROSS_COMPILE": cross_compile,
            }
        )

        # ARM64 kernels typically don't need UIMAGE_LOADADDR, but include if specified
        if self.uimage_loadaddr:
            env["UIMAGE_LOADADDR"] = self.uimage_loadaddr

        return env

    def get_default_dtb_path(self) -> str:
        """
        Get default DTB path for ZynqMP platform.

        Returns:
            Default DTB path
        """
        return "arch/arm64/boot/dts/xilinx"

    def get_default_kernel_image_path(self) -> str:
        """
        Get default kernel image path for ZynqMP platform.

        Returns:
            Default kernel image path
        """
        if self.kernel_target == "Image":
            return "arch/arm64/boot/Image"
        elif self.kernel_target == "Image.gz":
            return "arch/arm64/boot/Image.gz"
        else:
            return f"arch/arm64/boot/{self.kernel_target}"

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
        return self.config.get("kernel_image_path") or self.get_default_kernel_image_path()
