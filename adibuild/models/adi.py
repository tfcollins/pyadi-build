from dataclasses import dataclass

@dataclass
class FMComms5:
    name: str = "AD-FMCOMMS5-EBZ"
    description: str = (
        "The AD-FMCOMMS5-EBZ is a high-speed analog module designed to showcase the AD9361, a high performance, highly integrated RF transceiver intended for use in RF applications, such as 3G and 4G base station and test equipment applications, and software defined radios."
    )
    url: str = "https://wiki.analog.com/resources/eval/user-guides/ad-fmcomms5-ebz"

    hdl_project_folder = "fmcomms5"
    supported_carrier = ["ZC702", "ZC706", "ZCU102"]
    devicetrees_per_carrier = {
        "ZC702": "zynq-zc702-adv7511-ad9361-fmcomms2-3",
        "ZC706": "zynq-zc706-adv7511-ad9361-fmcomms2-3",
        "ZCU102": "zynqmp-zcu102-rev10-ad9361-fmcomms2-3",
    }

    cores = 4


@dataclass
class FMComms2:
    name: str = "AD-FMCOMMS2-EBZ"
    description: str = (
        "The AD-FMCOMMS2-EBZ is a high-speed analog module designed to showcase the AD9361, a high performance, highly integrated RF transceiver intended for use in RF applications, such as 3G and 4G base station and test equipment applications, and software defined radios."
    )
    url: str = "https://wiki.analog.com/resources/eval/user-guides/ad-fmcomms2-ebz"

    hdl_project_folder = "fmcomms2"
    supported_carrier = ["ZED", "ZC702", "ZC706", "ZCU102", "VCU118"]
    devicetrees_per_carrier = {
        "ZED": "zynq-zed-adv7511-ad9361-fmcomms2-3",
        "ZCU102": "zynqmp-zcu102-rev10-ad9361-fmcomms2-3",
    }

    cores = 4
