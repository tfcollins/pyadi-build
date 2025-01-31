from dataclasses import dataclass


@dataclass
class Vivado:
    version: str = "2020.2"
    path: str = "/opt/Xilinx/Vivado/2020.2/bin/vivado"
    source_cmd: str = "source /opt/Xilinx/Vivado/2020.2/settings64.sh"


def generate_vivado_config(version: str = "2023.2", os: str = "linux"):
    return Vivado(
        version=version,
        path=f"/opt/Xilinx/Vivado/{version}/bin/vivado",
        source_cmd=f"source /opt/Xilinx/Vivado/{version}/settings64.sh",
    )
