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


class UBoot(Common):

    gitrepo_https = "https://github.com/Xilinx/u-boot-xlnx.git"
    gitrepo_ssh = "git@github.com:Xilinx/u-boot-xlnx .git"
    gitrepo_preferred = "https"  # or "ssh" or None
    git_tool = "cli"  # or "python"

    branch_custom = None
    branch_map_vivado = {'2023.2': 'xlnx_rebase_v2023.01_2023.2'}

    def __init__(self, parent, tools):
        self.parent = parent
        self.tools = tools
        self.log_commands = True
        self.log_output = True
        self.log_file = "uboot.log"
        self.commands_file = "uboot_commands.txt"

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
        print("Checking tools for uboot")

    def get_source(self):
        log.info("Getting source for uboot")
        if self.git_tool:
            dir_loc = os.path.join(self.parent.build_dir, "uboot")
            if self.branch_custom:
                branch = self.branch_custom
            else:
                if self.tools.version in self.branch_map_vivado:
                    branch = self.branch_map_vivado[self.tools.version]
                else:
                    raise NotImplementedError(f"Vivado version {self.tools.version} not supported")
            self._run_shell_cmd(f"git clone --depth=1 {self.gitrepo_https} -b {branch} {dir_loc}")
        else:
            raise NotImplementedError("Only git is supported at this time")

    @gen_script
    def build_source(self):
        log.info("Building source for uboot")
        cwd = os.getcwd()
        os.chdir(self.parent.build_dir)
        cmd = f"{self.tools.source_cmd} &&"
        cmd += " cd uboot &&"
        cmd += f" export ARCH={self.parent.fpga.arch} &&"
        cmd += f" export CROSS_COMPILE={self.parent.fpga.cc_compiler} &&"
        cmd += f" make {self.parent.fpga.u_boot_def_config} &&"
        cmd += f" make -j{self.parent.fpga.num_cores}"
        self._run_shell_cmd(cmd)
        os.chdir(cwd)

    def collect_metadata(self):
        print("Collecting metadata for uboot")
        # ./build/uboot/u-boot.elf
        build_artifacts = [
            f"{self.parent.build_dir}/uboot/u-boot.elf",
        ]
        # logs = [
        #     os.path.join(self.parent.log_dir, self.log_file),
        #     os.path.join(self.parent.log_dir, self.commands_file),
        # ]
        # return build_artifacts, logs
        return build_artifacts, []
