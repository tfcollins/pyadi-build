"""Tooling Model for Xilinx FPGAs."""

# Dataclass

from dataclasses import dataclass


@dataclass
class ZCU102:
    type: str = "Development Board"
    name: str = "ZCU102"
    vendor: str = "Xilinx"
    family: str = "Zynq UltraScale+ MPSoC"
    device: str = "xczu9eg-ffvc900-2-i"
    package: str = "ffvc900"
    speedgrade: str = "2"

    # Linux Toolchain
    cc_compiler: str = "aarch64-linux-gnu-"
    arch: str = "arm64"
    def_config: str = "adi_zynqmp_defconfig"
    make_args: str = "Image UIMAGE_LOADADDR=0x8000"

    # u-boot Toolchain (Share components with Linux)
    u_boot_def_config: str = 'xilinx_zynqmp_virt_defconfig' #"xilinx_zynqmp_zcu102_rev1_0_defconfig"
    u_boot_arch: str = "aarch64"

    # General
    num_cores: int = 4
