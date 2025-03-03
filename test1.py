# import pytest
import logging

import adibuild as build

# enable logging to show info messages
logging.basicConfig(level=logging.DEBUG)

build_type = "Linux_ADSY"

b = build.Builder(name="build")

if build_type == "Linux":
    b.add_fmc(build.models.adi.FMComms2())
    b.add_fpga(build.models.xilinx.ZCU102())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    b.add_software(build.Linux(), vivado)

    a,c = b.build()
    print(a)
    print(c)

elif build_type == "HDL":
    b.add_fmc(build.models.adi.FMComms2())
    b.add_fpga(build.models.xilinx.ZCU102())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    b.add_software(build.HDL(), vivado)

    a,c = b.build()
    print(a)
    print(c)

elif build_type == "GHDL":
    # b.add_som(build.models.adi_som.ADSY1100_VU11P())
    b.add_som(build.models.adi_som.ADSY1100_ZU4EG())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    # ghdl = build.gen_ghdl_project("apollo_som", "xilinx_project_generate_bin")
    ghdl = build.gen_ghdl_project("apollo_som", "dev_selmap")

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
        

    b.add_software(ghdl(), vivado)

    b.software[0].pre_build_func = copy_hsci

    a,c = b.build()
    print(a)
    print(c)

elif build_type == "Linux_ADSY":
    b.add_som(build.models.adi_som.ADSY1100_VU11P())

    vivado = build.models.vivado.generate_vivado_config("2023.2", "linux")
    linux = build.Linux()
    linux.gitrepo_https = "https://bitbucket.analog.com/scm/sdg/linux-apollo.git"
    linux.branch = "main"
    b.add_software(linux, vivado)

    def update_profile(self):
        print("Updating profile")
        filename = "vu11p-vpx-apollo.dts"
        # Find the file with glob recursively
        import glob

        dts_file = glob.glob(f"{self.parent.build_dir}/linux/**/{filename}", recursive=True)
        if not dts_file:
            raise FileNotFoundError(f"Could not find {filename}")
        
        with open(dts_file[0], "r") as f:
            lines = f.readlines()

        def replace_line(target, new_line, lines):
            out_lines = []
            for line in lines:
                if target in line:
                    out_lines.append(new_line)
                else:
                    out_lines.append(line)
            return out_lines
        
        def replace_line_after_found(target, new_line, lines):
            out_lines = []
            found = False
            for line in lines:
                if found:
                    out_lines.append(new_line)
                    found = False
                else:
                    out_lines.append(line)
                if target in line:
                    found = True
            return out_lines
        
        # Apollo profile
        ref = "adi,device-profile-fw-name"
        lines = replace_line(ref, f'{ref} = "id01_uc26_ffsom.bin";\n', lines)

        # ADF4382
        ref = "adi,power-up-frequency"
        lines = replace_line(ref, f'{ref} = /bits/ 64 <8000000000>;\n', lines)

        # LTC6952
        ref = "adi,vco-frequency-hz"
        lines = replace_line(ref, f'{ref} = /bits/ 64 <2500000000>;\n', lines)

        ref = "adi,extended-name = \"VUP Core CLK\";"
        new = "adi,divider = <20>;\n"
        lines = replace_line_after_found(ref, new, lines)

        ref = "adi,extended-name = \"JESD REF CLK 1\";"
        new = "adi,divider = <10>;\n"
        lines = replace_line_after_found(ref, new, lines)

        ref = "adi,extended-name = \"JESD REF CLK 2\";"
        new = "adi,divider = <10>;\n"
        lines = replace_line_after_found(ref, new, lines)

        print("Writing to file")
        with open(dts_file[0], "w") as f:
            f.writelines(lines)


    b.software[0].pre_build_func = update_profile

    a,c = b.build()
    print(a)
    print(c)

else:
    print("Invalid build type")
