from dataclasses import dataclass

from .common import DeviceType


@dataclass
class ADSY1100_VU11P:
    device_type: DeviceType = DeviceType.SOM
    name: str = "ADSY1100-VU11P"
    description: str = (
        "4 Tx/4 Rx, 0.1 GHz to 20 GHz Apollo MxFE 3UVPX Tuner + Digitizer + Processor"
    )

    url: str = "https://www.analog.com/en/products/adsy1100.html"

    hdl_project_folder = None
    fpga = "apollo_som_vu11p"
    devicetrees_per_carrier = {
        "ADSY1100-VU11P": [
            "vu11p-vpx-apollo",
        ]
    }

    # FPGA Software Info
    type: str = "COTS Board"
    vendor: str = "ADI"
    family: str = "VPX Modules"
    # device: str = "xczu11"
    # package: str = "ffvc900"
    # speedgrade: str = "2"

    # Linux Toolchain
    cc_compiler: str = "aarch64-linux-gnu-"
    arch: str = "arm64"
    def_config: str = "adi_zynqmp_adsy1100_b0_defconfig"
    make_args: str = "Image UIMAGE_LOADADDR=0x8000"

    # u-boot Toolchain (Share components with Linux)
    u_boot_def_config: str = 'xilinx_zynqmp_virt_defconfig' #"xilinx_zynqmp_zcu102_rev1_0_defconfig"
    u_boot_arch: str = "aarch64"

    # General
    num_cores: int = 4

    cores = 4

@dataclass
class ADSY1100_ZU4EG(ADSY1100_VU11P):
    name: str = "ADSY1100-ZU4EG"
    hdl_project_folder = None
    fpga = "apollo_som_zu4eg"
    devicetrees_per_carrier = {
        "ADSY1100-ZU4EG": [
            "zynqmp-vpx-apollo",
        ]
    }

    # FPGA Software Info
    type: str = "COTS Board"
    vendor: str = "ADI"
    family: str = "VPX Modules"
    # device: str = "xczu4"
    # package: str = "ffvc900"
    # speedgrade: str = "2"

    # Linux Toolchain
    cc_compiler: str = "aarch64-linux-gnu-"
    arch: str = "arm64"
    def_config: str = "adi_zynqmp_adsy1100_b0_defconfig"
    make_args: str = "Image UIMAGE_LOADADDR=0x8000"

    # u-boot Toolchain (Share components with Linux)
    u_boot_def_config: str = 'xilinx_zynqmp_virt_defconfig' #"xilinx_zynqmp_zcu102_rev1_0_defconfig"
    u_boot_arch: str = "aarch64"

    # General
    num_cores: int = 4

    cores = 4
