from adibuild.platforms.base import Platform


class HDLPlatform(Platform):
    """Platform for HDL projects."""

    @property
    def name(self) -> str:
        """Get platform name."""
        return self.config.get("name", "unknown")

    def get_make_env(self) -> dict[str, str]:
        """
        Get environment variables for make.

        Returns:
            Dictionary of environment variables
        """
        return {}

    def validate_toolchain(self) -> bool:
        """
        Validate toolchain.

        Returns:
            True if toolchain is valid
        """
        # For HDL, we assume the environment is set up or handled by the builder
        # We can implement specific checks for Vivado/Quartus here if needed
        return True
