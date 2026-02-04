"""Xilinx MicroBlaze (Virtex) platform implementation."""

from adibuild.platforms.base import Platform


class MicroBlazePlatform(Platform):
    """Xilinx MicroBlaze platform for Virtex FPGAs."""

    def __init__(self, config: dict[str, any]):
        """
        Initialize MicroBlazePlatform.

        Args:
            config: Platform configuration dictionary
        """
        super().__init__(config)

        # Validate required configuration
        if self.arch != "microblaze":
            raise ValueError(
                f"MicroBlazePlatform requires arch='microblaze', got '{self.arch}'"
            )

        if not self.kernel_target.startswith("simpleImage"):
            self.logger.warning(
                f"Unusual kernel target '{self.kernel_target}' for MicroBlaze platform. "
                "Typically 'simpleImage.<dts>' format is used."
            )

    def get_make_env(self) -> dict[str, str]:
        """
        Get environment variables for make.

        Returns:
            Dictionary of environment variables
        """
        # Get toolchain and use its cross-compile prefix
        toolchain = self.get_toolchain()
        cross_compile = toolchain.cross_compile_microblaze or self.cross_compile

        # Start with toolchain environment variables
        env = dict(toolchain.env_vars)

        # Add platform-specific variables (these take precedence)
        env.update(
            {
                "ARCH": self.arch,
                "CROSS_COMPILE": cross_compile,
            }
        )

        return env

    def get_default_dtb_path(self) -> str:
        """
        Get default DTB path for MicroBlaze platform.

        Returns:
            Default DTB path
        """
        return "arch/microblaze/boot/dts"

    def get_default_kernel_image_path(self) -> str:
        """
        Get default kernel image path for MicroBlaze platform.

        Returns:
            Default kernel image path
        """
        return f"arch/microblaze/boot/{self.kernel_target}"

    @property
    def simpleimage_targets(self) -> list[str]:
        """
        Get list of simpleImage targets to build.

        Returns:
            List of simpleImage target names
        """
        return self.config.get("simpleimage_targets", [self.kernel_target])

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
