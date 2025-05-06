import pytest
import logging
import os

import adibuild as build

logging.basicConfig(level=logging.DEBUG)


def test_linux_build_zcu102():

    b = build.Builder(name="build")

    b.add_fmc(build.models.adi.FMComms2())
    b.add_fpga(build.models.xilinx.ZCU102())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    linux = build.Linux(tools=vivado)
    linux.branch = '2023_R2'
    hdl = build.HDL(tools=vivado)
    hdl.branch = 'hdl_2023_r2'
    b.add_software(linux)
    b.add_software(hdl)

    all_artifacts, all_logs = b.build()

    # Verify all artifacts are present
    for file in all_artifacts + all_logs:
        assert os.path.exists(file)
