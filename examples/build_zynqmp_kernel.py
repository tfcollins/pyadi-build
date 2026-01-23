#!/usr/bin/env python3
"""
Example: Build ZynqMP Linux kernel using Python API.

This example demonstrates how to use pyadi-build as a Python library
to build a Linux kernel for the ZynqMP platform.
"""

from pathlib import Path

from adibuild import LinuxBuilder, BuildConfig
from adibuild.platforms import ZynqMPPlatform


def main():
    """Build ZynqMP kernel."""
    # Load configuration
    config_path = Path(__file__).parent.parent / "configs" / "linux" / "2023_R2.yaml"
    config = BuildConfig.from_yaml(config_path)

    # Get ZynqMP platform configuration
    platform_config = config.get_platform("zynqmp")
    platform = ZynqMPPlatform(platform_config)

    print(f"Building Linux kernel for {platform.arch} platform")
    print(f"Defconfig: {platform.defconfig}")
    print(f"Kernel target: {platform.kernel_target}")
    print()

    # Create builder
    builder = LinuxBuilder(config, platform)

    # Execute full build
    print("Starting build...")
    result = builder.build(clean_before=False)

    print()
    print("=" * 60)
    print("Build Summary")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Duration: {result['duration']:.1f}s")
    print(f"Kernel image: {result['kernel_image']}")
    print(f"DTBs built: {len(result['dtbs'])}")
    print(f"Output directory: {result['artifacts']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
