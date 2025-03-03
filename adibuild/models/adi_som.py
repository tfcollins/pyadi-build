from dataclasses import dataclass

from .common import DeviceType


@dataclass
class ADSY1100_VU11P:
    device_type: DeviceType = DeviceType.SOM
    name: str = "ADSY1100 VU11P Design"
    description: str = (
        "4 Tx/4 Rx, 0.1 GHz to 20 GHz Apollo MxFE 3UVPX Tuner + Digitizer + Processor"
    )

    url: str = "https://www.analog.com/en/products/adsy1100.html"

    hdl_project_folder = None
    fpga = "apollo_som_vu11p"
    devicetrees_per_carrier = {
        "apollo_som_vu11p": [
            "apollo_som_vu11p",
        ]
    }

    cores = 4

@dataclass
class ADSY1100_ZU4EG(ADSY1100_VU11P):
    name: str = "ADSY1100 ZU4EG Design"
    hdl_project_folder = None
    fpga = "apollo_som_zu4eg"
    devicetrees_per_carrier = {
        "apollo_som_zu4eg": [
            "apollo_som_zu4eg",
        ]
    }

    cores = 4
