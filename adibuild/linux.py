import logging
import os
import shutil

from .common import Common
from .models.common import DeviceType

log = logging.getLogger(__name__)


def gen_script(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.log_commands:
            self._log_commands = True
            self._log_commands_file = os.path.join(
                self.parent.log_dir, self.commands_file
            )
        if self.log_output:
            self._log_output = True
            self._log_output_file = os.path.join(self.parent.log_dir, self.log_file)
        log.info(f"Generating script for {args[0].__class__.__name__}")
        out = func(*args, **kwargs)
        self._log_commands = False
        return out

    return wrapper


class Linux(Common):

    gitrepo_https = "https://github.com/analogdevicesinc/linux.git"
    gitrepo_ssh = "git@github.com:analogdevicesinc/linux.git"
    gitrepo_preferred = "https"  # or "ssh" or None
    git_tool = "cli"  # or "python"

    branch = "main"

    def __init__(self, parent, tools):
        self.parent = parent
        self.tools = tools
        self.log_commands = True
        self.log_output = True
        self.log_file = "linux.log"
        self.commands_file = "linux_commands.txt"

        self.pre_clone_func = None
        self.pre_build_func = None

    def reset_logs(self):
        full_log_path = os.path.join(self.parent.log_dir, self.log_file)
        full_cmd_path = os.path.join(self.parent.log_dir, self.commands_file)
        if not os.path.exists(self.parent.log_dir):
            os.makedirs(self.parent.log_dir)
        with open(full_log_path, "w") as f:
            f.write("")
        with open(full_cmd_path, "w") as f:
            f.write("")

    def tools_check(self):
        print("Checking tools for Linux")

    def get_source(self):
        log.info("Getting source for Linux")
        if self.git_tool:
            dir_loc = os.path.join(self.parent.build_dir, "linux")
            self._run_shell_cmd(f"git clone --depth=1 {self.gitrepo_https} -b {self.branch} {dir_loc}")
        else:
            raise NotImplementedError("Only git is supported at this time")

    @gen_script
    def build_source(self):
        log.info("Building source for Linux")
        cwd = os.getcwd()

        if self.pre_build_func:
            self.pre_build_func(self)

        if self.parent.project_type == DeviceType.FPGA_FMC:
            dev = self.parent.fpga
            dt = self.parent.fmc.devicetrees_per_carrier[dev.name]
        elif self.parent.project_type == DeviceType.SOM:
            dev = self.parent.som
            dt = self.parent.som.devicetrees_per_carrier[dev.name]
        else:
            raise ValueError("Device not set")
        
        os.chdir(self.parent.build_dir)
        cmd = f"{self.tools.source_cmd} &&"
        cmd += " cd linux &&"
        cmd += f" export ARCH={dev.arch} &&"
        cmd += f" export CROSS_COMPILE={dev.cc_compiler} &&"
        cmd += f" make {dev.def_config} &&"
        cmd += f" make -j{dev.num_cores} {dev.make_args} &&"
        cmd += f" make xilinx/{dt}.dtb"
        self._run_shell_cmd(cmd)
        os.chdir(cwd)

    def collect_metadata(self):
        print("Collecting metadata for Linux")
        if self.parent.project_type == DeviceType.FPGA_FMC:
            dev = self.parent.fpga
        elif self.parent.project_type == DeviceType.SOM:
            dev = self.parent.som
        else:
            raise ValueError("Device not set")
        arch = dev.arch
        image_name = "uImage" if arch == "arm" else "Image"
        dtb_name = (
            f"{self.parent.fmc.devicetrees_per_carrier[dev.name]}.dtb"
        )
        build_artifacts = [
            f"{self.parent.build_dir}/linux/arch/{arch}/boot/{image_name}",
            f"{self.parent.build_dir}/linux/arch/{arch}/boot/dts/xilinx/{dtb_name}",
        ]
        logs = [
            os.path.join(self.parent.log_dir, self.log_file),
            os.path.join(self.parent.log_dir, self.commands_file),
        ]
        return build_artifacts, logs
