#!/usr/bin/env python3
"""
Example: Build kernel with custom configuration.

This example shows how to use a custom kernel configuration
and run menuconfig before building.
"""

from pathlib import Path

from adibuild import LinuxBuilder, BuildConfig
from adibuild.platforms import ZynqMPPlatform


def main():
    """Build kernel with custom configuration."""
    # Load base configuration
    config_path = Path(__file__).parent.parent / "configs" / "linux" / "zynqmp.yaml"
    config = BuildConfig.from_yaml(config_path)

    # Override tag
    config.set("tag", "2023_R2")

    # Get platform
    platform_config = config.get_platform("zynqmp")
    platform = ZynqMPPlatform(platform_config)

    print("Building kernel with custom configuration")
    print()

    # Create builder
    builder = LinuxBuilder(config, platform)

    # Prepare source
    print("Preparing kernel source...")
    builder.prepare_source()

    # Run initial configuration
    print("Running defconfig...")
    builder.configure()

    # Run menuconfig for customization
    print()
    print("Running menuconfig for customization...")
    print("TIP: Navigate to your desired options and save the configuration")
    print()
    builder.menuconfig()

    # Build with custom config
    print()
    print("Building kernel with custom configuration...")
    kernel_image = builder.build_kernel()
    dtbs = builder.build_dtbs()

    # Package
    output_dir = builder.package_artifacts(kernel_image, dtbs)

    print()
    print(f"Build completed with custom configuration!")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
