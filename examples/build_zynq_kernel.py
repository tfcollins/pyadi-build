#!/usr/bin/env python3
"""
Example: Build Zynq Linux kernel using Python API.

This example demonstrates how to use pyadi-build as a Python library
to build a Linux kernel for the Zynq platform.
"""

from pathlib import Path

from adibuild import BuildConfig, LinuxBuilder
from adibuild.platforms import ZynqPlatform


def main():
    """Build Zynq kernel."""
    # Load configuration
    config_path = Path(__file__).parent.parent / "configs" / "linux" / "2023_R2.yaml"
    config = BuildConfig.from_yaml(config_path)

    # Get Zynq platform configuration
    platform_config = config.get_platform("zynq")
    platform = ZynqPlatform(platform_config)

    print(f"Building Linux kernel for {platform.arch} platform")
    print(f"Defconfig: {platform.defconfig}")
    print(f"Kernel target: {platform.kernel_target}")
    print()

    # Create builder
    builder = LinuxBuilder(config, platform)

    # Prepare source
    print("Preparing kernel source...")
    source_dir = builder.prepare_source()
    print(f"Source directory: {source_dir}")
    print()

    # Configure
    print("Configuring kernel...")
    builder.configure()
    print()

    # Build kernel
    print("Building kernel...")
    kernel_image = builder.build_kernel()
    print(f"Kernel image: {kernel_image}")
    print()

    # Build DTBs
    print("Building device tree blobs...")
    dtbs = builder.build_dtbs()
    print(f"Built {len(dtbs)} DTBs:")
    for dtb in dtbs:
        print(f"  - {dtb.name}")
    print()

    # Package artifacts
    print("Packaging artifacts...")
    output_dir = builder.package_artifacts(kernel_image, dtbs)
    print(f"Build artifacts available at: {output_dir}")
    print()

    print("Build completed successfully!")


if __name__ == "__main__":
    main()
