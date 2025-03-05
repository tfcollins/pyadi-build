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
    b.add_software(build.Linux(), vivado)
    b.add_software(build.HDL(), vivado)

    all_artifacts, all_logs = b.build()

    # Verify all artifacts are present
    for file in all_artifacts + all_logs:
        assert os.path.exists(file)
