#!/usr/bin/env python3
"""
Example: Build MicroBlaze Linux kernel using Python API.

This example demonstrates how to use pyadi-build as a Python library
to build a Linux kernel for the MicroBlaze platform on VCU118 with AD9081.
"""

from pathlib import Path

from adibuild import LinuxBuilder, BuildConfig
from adibuild.platforms import MicroBlazePlatform


def main():
    """Build MicroBlaze kernel for VCU118 + AD9081."""
    # Load configuration
    config_path = Path(__file__).parent.parent / "configs" / "linux" / "microblaze_vcu118_ad9081.yaml"
    config = BuildConfig.from_yaml(config_path)

    # Get MicroBlaze platform configuration
    platform_config = config.get_platform("microblaze_vcu118")
    platform = MicroBlazePlatform(platform_config)

    print(f"Building Linux kernel for {platform.arch} platform")
    print(f"Defconfig: {platform.defconfig}")
    print(f"Kernel target: {platform.kernel_target}")
    print(f"simpleImage targets: {platform.simpleimage_targets}")
    print()

    # Note: MicroBlaze requires Vivado toolchain
    print("Note: Ensure Xilinx Vivado is installed and sourced:")
    print("  source /opt/Xilinx/Vivado/2023.2/settings64.sh")
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

    # Build kernel (returns List[Path] for MicroBlaze with multiple targets)
    print("Building kernel...")
    kernel_images = builder.build_kernel()

    # MicroBlaze build_kernel() returns a list of images
    if isinstance(kernel_images, list):
        print(f"Built {len(kernel_images)} simpleImage(s):")
        for img in kernel_images:
            print(f"  - {img}")
    else:
        print(f"Kernel image: {kernel_images}")
    print()

    # Build DTBs (skipped for MicroBlaze - DT embedded in simpleImage)
    print("Building device tree blobs...")
    dtbs = builder.build_dtbs()
    if dtbs:
        print(f"Built {len(dtbs)} DTBs")
    else:
        print("No separate DTBs for MicroBlaze (embedded in simpleImage)")
    print()

    # Package artifacts
    print("Packaging artifacts...")
    output_dir = builder.package_artifacts(kernel_images, dtbs)
    print(f"Build artifacts available at: {output_dir}")
    print()

    print("Build completed successfully!")
    print()
    print("To boot on VCU118:")
    print("  1. Load FPGA bitstream with MicroBlaze system")
    print("  2. Use XSCT/XSDB to load simpleImage to DDR")
    print("  3. Boot from loaded address")


if __name__ == "__main__":
    main()
