# import pytest
import logging

import adibuild as build

# enable logging to show info messages
logging.basicConfig(level=logging.DEBUG)

b = build.Builder(name="ADSY1100 ZU4EG", build_dir="build_zu4eg")

# Add hardware
b.add_som(build.models.adi_som.ADSY1100_ZU4EG())

# Add Linux build
vivado = build.models.vivado.generate_vivado_config("2023.2")
linux = build.Linux
linux.gitrepo_https = "https://bitbucket.analog.com/scm/sdg/linux-apollo.git"
linux.branch = "main"
b.add_software(linux, vivado)

# Add HDL build
ghdl_zu4eg = build.gen_ghdl_project("apollo_som", "dev_selmap")
b.add_software(ghdl_zu4eg, vivado)

# Run the build
a,c = b.build()
print(a)
print(c)

## VU11P
del b
b = build.Builder(name="ADSY1100 VU11P", build_dir="build_vu11p")

# Add hardware
b.add_som(build.models.adi_som.ADSY1100_VU11P())

# Add Linux build
vivado = build.models.vivado.generate_vivado_config("2023.2")
linux = build.Linux
linux.gitrepo_https = "https://bitbucket.analog.com/scm/sdg/linux-apollo.git"
linux.branch = "main"
b.add_software(linux, vivado)

# Add HDL build
ghdl_vu11p = build.gen_ghdl_project("apollo_som", "xilinx_project_generate_bin")
b.add_software(ghdl_vu11p, vivado)

# Run the build
a,c = b.build()
print(a)