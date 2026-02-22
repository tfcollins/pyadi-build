"""Xilinx Versal (ARM64) platform implementation."""

from adibuild.platforms.base import Platform


class VersalPlatform(Platform):
    """Xilinx Versal (ARM64) platform configuration."""

    def __init__(self, config: dict[str, any]):
        """
        Initialize VersalPlatform.

        Args:
            config: Platform configuration dictionary
        """
        super().__init__(config)

        # Validate required configuration
        if self.arch != "arm64":
            raise ValueError(f"VersalPlatform requires arch='arm64', got '{self.arch}'")

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

        # Add platform-specific variables
        env.update(
            {
                "ARCH": self.arch,
                "CROSS_COMPILE": cross_compile,
            }
        )

        return env

    def get_default_dtb_path(self) -> str:
        """Get default DTB path for Versal."""
        return "arch/arm64/boot/dts/xilinx"

    def get_default_kernel_image_path(self) -> str:
        """Get default kernel image path for Versal."""
        return "arch/arm64/boot/Image"

    @property
    def dtb_path(self) -> str:
        """Get DTB path."""
        return self.config.get("dtb_path") or self.get_default_dtb_path()

    @property
    def kernel_image_path(self) -> str:
        """Get kernel image path."""
        return (
            self.config.get("kernel_image_path") or self.get_default_kernel_image_path()
        )

    @property
    def plm_path(self) -> str | None:
        """Get path to PLM executable."""
        return self.config.get("plm_path")

    @property
    def psmfw_path(self) -> str | None:
        """Get path to PSMFW executable."""
        return self.config.get("psmfw_path")

    @property
    def atf_path(self) -> str | None:
        """Get path to ATF (bl31.elf)."""
        return self.config.get("atf_path")

    @property
    def uboot_path(self) -> str | None:
        """Get path to U-Boot executable."""
        return self.config.get("uboot_path")

    @property
    def pdi_path(self) -> str | None:
        """Get path to PDI (Programmable Device Image)."""
        return self.config.get("pdi_path")
