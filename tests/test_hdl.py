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

    lnx = build.Linux(tools=vivado)
    lnx.branch = "2023_R2"

    hdl = build.HDL(tools=vivado)
    hdl.branch = "hdl_2023_r2"

    b.add_software(lnx)
    b.add_software(hdl)

    all_artifacts, all_logs = b.build()

    # Verify all artifacts are present
    for file in all_artifacts + all_logs:
        assert os.path.exists(file)

def test_hdl_adsy1100_zu4eg():

    b = build.Builder(name="build")

    # Define hardware
    b.add_som(build.models.adi_som.ADSY1100_ZU4EG())

    # Define tools
    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")

    # Define source code
    # hdl = build.HDL
    # hdl.branch = "hdl_2023_r2"
    ghdl = build.gen_ghdl_project("apollo_som", "hdl_2023_r2")
    ghdl.tools = vivado

    # b.add_software(build.Linux, vivado)
    # b.add_software(build.HDL, vivado)
    # b.add_software(hdl, vivado)
    b.add_software(ghdl, "ghdl_adsy1100_zu4eg")
    # b.add_software(build.UBoot, vivado)

    # b.add_tool()
    all_artifacts, all_logs = b.build()

    # Verify all artifacts are present
    for file in all_artifacts + all_logs:
        assert os.path.exists(file)
