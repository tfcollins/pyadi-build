import os

import pytest

import adibuild as build

# def test_hdl_kuiper_upload(kuiper_client, hdl_file):
#     """
#     Test the upload of an HDL file to Kuiper.
#     """
#     response = kuiper_client.upload_hdl(hdl_file)
#     assert response.status_code == 200
#     assert response.json().get("status") == "success"

@pytest.mark.upload
def test_mock_files_upload():

    b = build.Builder(name="build", use_upload_features=True)

    b.add_fmc(build.models.adi.FMComms2())
    b.add_fpga(build.models.xilinx.ZCU102())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    b.add_software(build.HDL, vivado)

    # Manually set build artifacts and logs for testing

    # all_artifacts, all_logs = b.build()

    here = os.path.dirname(os.path.abspath(__file__))

    all_artifacts = [
        os.path.join(here, "mocks", "hdl", "system_top.xsa"),
    ]
    all_logs = [
        os.path.join(here, "mocks", "hdl", "timing_impl.log"),
        os.path.join(here, "mocks", "hdl", "timing_synth.log"),
        os.path.join(here, "mocks", "hdl", "vivado.log"),
    ]

    b.software[0]._build_artifacts = all_artifacts
    b.software[0]._logs = all_logs

    b.software[0].upload()
    
