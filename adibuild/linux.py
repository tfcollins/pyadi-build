import logging
import os
import shutil

from .common import Common

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
            # self._run_shell_cmd(f"git clone --depth=1 {self.gitrepo_https} -b {self.branch} {dir_loc}")
        else:
            raise NotImplementedError("Only git is supported at this time")

    @gen_script
    def build_source(self):
        log.info("Building source for Linux")
        cwd = os.getcwd()
        os.chdir(self.parent.build_dir)
        cmd = f"{self.tools.source_cmd} &&"
        cmd += " cd linux &&"
        cmd += f" export ARCH={self.parent.fpga.arch} &&"
        cmd += f" export CROSS_COMPILE={self.parent.fpga.cc_compiler} &&"
        cmd += f" make {self.parent.fpga.def_config} &&"
        cmd += f" make -j{self.parent.fpga.num_cores} {self.parent.fpga.make_args} &&"
        fpga = self.parent.fpga.name
        cmd += f" make xilinx/{self.parent.fmc.devicetrees_per_carrier[fpga]}.dtb"
        self._run_shell_cmd(cmd)
        os.chdir(cwd)

    def collect_metadata(self):
        print("Collecting metadata for Linux")
        arch = self.parent.fpga.arch
        image_name = "uImage" if arch == "arm" else "Image"
        dtb_name = (
            f"{self.parent.fmc.devicetrees_per_carrier[self.parent.fpga.name]}.dtb"
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
