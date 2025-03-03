# import pytest
import logging

import adibuild as build

# enable logging to show info messages
logging.basicConfig(level=logging.DEBUG)

build_type = "Linux"

b = build.Builder(name="build")

if build_type == "Linux":
    b.add_fmc(build.models.adi.FMComms2())
    b.add_fpga(build.models.xilinx.ZCU102())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    b.add_software(build.Linux, vivado)

    a,c = b.build()
    print(a)
    print(c)

elif build_type == "HDL":
    b.add_fmc(build.models.adi.FMComms2())
    b.add_fpga(build.models.xilinx.ZCU102())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    b.add_software(build.HDL, vivado)

    a,c = b.build()
    print(a)
    print(c)

elif build_type == "GHDL":
    # b.add_som(build.models.adi_som.ADSY1100_VU11P())
    b.add_som(build.models.adi_som.ADSY1100_ZU4EG())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    ghdl = build.gen_ghdl_project("apollo_som", "hdl_2023_r2")

    def copy_hsci(self):
        print("Copying HSCI")
        import os
        source_dir = os.path.join(
            self.parent.build_dir, self.hdl_clone_folder_name, "projects", "apollo_som_vu11p", "axi_hsci"
        )
        target_dir = os.path.join(
            self.parent.build_dir, self.ghdl_us_hdl_clone_folder_name
        )
        os.system(f"cp -r {source_dir} {target_dir}")
        

    b.add_software(ghdl, vivado)

    b.som.pre_build_func = copy_hsci

    a,c = b.build()
    print(a)
    print(c)

elif build_type == "Linux_ADSY":
    b.add_som(build.models.adi_som.ADSY1100_VU11P())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    linux = build.Linux
    linux.gitrepo_https = "https://bitbucket.analog.com/scm/sdg/linux-apollo.git"
    linux.branch = "main"
    b.add_software(linux, vivado)

    a,c = b.build()
    print(a)
    print(c)

else:
    print("Invalid build type")
