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


class HDL(Common):

    gitrepo_https = "https://github.com/analogdevicesinc/hdl.git"
    gitrepo_ssh = "git@github.com:analogdevicesinc/hdl.git"
    gitrepo_preferred = "https"  # or "ssh" or None
    git_tool = "cli"  # or "python"

    branch = "main"

    def __init__(self, parent, tools):
        self.parent = parent
        self.tools = tools
        self.log_commands = True
        self.log_output = True
        self.log_file = "hdl.log"
        self.commands_file = "hdl_commands.txt"

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
        print("Checking tools for HDL")

    def get_source(self):
        log.info("Getting source for HDL")
        if self.git_tool:
            dir_loc = os.path.join(self.parent.build_dir, "hdl")
            self._run_shell_cmd(
                f"git clone --depth=1 {self.gitrepo_https} -b {self.branch} {dir_loc}"
            )
        else:
            raise NotImplementedError("Only git is supported at this time")

    @gen_script
    def build_source(self):
        log.info("Building source for HDL")
        cwd = os.getcwd()
        os.chdir(self.parent.build_dir)
        cmd = f"{self.tools.source_cmd} &&"
        project = self.parent.fmc.hdl_project_folder
        carrier = self.parent.fpga.name.lower()
        cmd += f" cd hdl/projects/{project}/{carrier} &&"
        cmd += f" make -j{self.parent.fpga.num_cores}"
        # self._run_shell_cmd(cmd)
        os.chdir(cwd)

    def collect_metadata(self):
        print("Collecting metadata for HDL")
        # find folder that ends with .sdk
        project = self.parent.fmc.hdl_project_folder
        carrier = self.parent.fpga.name.lower()
        sdk_folder = None
        for root, dirs, files in os.walk(
            os.path.join(self.parent.build_dir, "hdl", "projects", project, carrier)
        ):
            for d in dirs:
                if d.endswith(".sdk"):
                    sdk_folder = os.path.join(root, d)
                    break
            if sdk_folder:
                break
        # any file that ends with .log within projects/<project>/<carrier>/
        logs = []
        valid_files = [
            "timing_synth.log",
            "timing_impl.log",
            "vivado.log",
            f"{project}_{carrier}_vivado.log",
        ]
        for root, dirs, files in os.walk(
            os.path.join(self.parent.build_dir, "hdl", "projects", project, carrier)
        ):
            for f in files:
                if f.endswith(".log"):
                    if f in valid_files:
                        logs.append(os.path.join(root, f))
        build_artifacts = [
            f"{sdk_folder}/system_top.xsa",
        ]
        logs += [os.path.join(self.parent.log_dir, self.log_file)]
        logs += [os.path.join(self.parent.log_dir, self.commands_file)]

        return build_artifacts, logs
