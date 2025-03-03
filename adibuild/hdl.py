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


def gen_ghdl_project(
    ghdl_branch: str,
    hdl_branch: str,
    ghdl_gitrepo_https: str = None,
    ghdl_gitrepo_ssh: str = None,
    ghdl_gitrepo_preferred: str = "https",
    hdl_gitrepo_https: str = None,
    hdl_gitrepo_ssh: str = None,
    hdl_gitrepo_preferred: str = "https",
):
    ghdl = HDL
    ghdl.ghdl_project = True

    # Take defaults from HDL class
    if not hdl_gitrepo_https:
        hdl_gitrepo_https = ghdl.gitrepo_https
    if not hdl_gitrepo_ssh:
        hdl_gitrepo_ssh = ghdl.gitrepo_ssh
    if not ghdl_gitrepo_https:
        ghdl_gitrepo_https = ghdl.ghdl_us_hdl_repo_https
    if not ghdl_gitrepo_ssh:
        ghdl_gitrepo_ssh = ghdl.ghdl_us_hdl_repo_ssh

    # Set main project build path to use GHDL
    ghdl.branch = ghdl_branch
    ghdl.hdl_clone_folder_name = "ghdl"
    ghdl.gitrepo_https = ghdl_gitrepo_https
    ghdl.gitrepo_ssh = ghdl_gitrepo_ssh
    ghdl.gitrepo_preferred = ghdl_gitrepo_preferred

    # Set secondary HDL path to use upstream HDL
    ghdl.ghdl_us_hdl_branch = hdl_branch
    ghdl.ghdl_us_hdl_clone_folder_name = "hdl"
    ghdl.ghdl_us_hdl_repo_https = hdl_gitrepo_https
    ghdl.ghdl_us_hdl_repo_ssh = hdl_gitrepo_ssh
    ghdl.ghdl_us_hdl_repo_preferred = hdl_gitrepo_preferred

    return ghdl


class HDL(Common):

    gitrepo_https = "https://github.com/analogdevicesinc/hdl.git"
    gitrepo_ssh = "git@github.com:analogdevicesinc/hdl.git"
    gitrepo_preferred = "https"  # or "ssh" or None
    git_tool = "cli"  # or "python"

    branch = "main"

    hdl_clone_folder_name = "hdl"

    # GHDL related
    ghdl_project = False
    ghdl_us_hdl_branch = "main"
    ghdl_us_hdl_clone_folder_name = None
    ghdl_us_hdl_repo_https = "https://bitbucket.analog.com/scm/sdg/ghdl.git"
    ghdl_us_hdl_repo_ssh = None
    ghdl_us_hdl_repo_preferred = "https"

    def __init__(self, parent, tools, pre_clone_func=None, pre_build_func=None):
        self.parent = parent
        self.tools = tools
        self.log_commands = True
        self.log_output = True
        self.log_file = "hdl.log"
        self.commands_file = "hdl_commands.txt"
        self.make_prepend_commands = []

        self.pre_clone_func = pre_clone_func
        self.pre_build_func = pre_build_func

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
        if self.pre_clone_func:
            log.info("Running pre-clone function")
            self.pre_clone_func()
        if self.ghdl_project:
            log.info("Getting upstream HDL source")
            # Check if target clone folders are the same
            if self.ghdl_us_hdl_clone_folder_name == self.hdl_clone_folder_name:
                raise ValueError(
                    "ghdl_us_clone_folder_name and hdl_clone_folder_name cannot be the same"
                )
            if self.git_tool:
                dir_loc = os.path.join(
                    self.parent.build_dir, self.ghdl_us_hdl_clone_folder_name
                )
                self._run_shell_cmd(
                    f"git clone --depth=1 {self.ghdl_us_hdl_repo_https} -b {self.ghdl_us_hdl_branch} {dir_loc}"
                )
            else:
                raise NotImplementedError("Only git is supported at this time")
        log.info("Getting source for HDL")
        if self.git_tool:
            dir_loc = os.path.join(self.parent.build_dir, self.hdl_clone_folder_name)
            self._run_shell_cmd(
                f"git clone --depth=1 {self.gitrepo_https} -b {self.branch} {dir_loc}"
            )
        else:
            raise NotImplementedError("Only git is supported at this time")

    @gen_script
    def build_source(self):
        if self.pre_build_func:
            log.info("Running pre-build function")
            self.pre_build_func()
        log.info("Building source for HDL")
        cwd = os.getcwd()
        os.chdir(self.parent.build_dir)
        cmd = f"{self.tools.source_cmd} &&"
        if self.parent.project_type == DeviceType.FPGA_FMC:
            project = self.parent.fmc.hdl_project_folder
            carrier = self.parent.fpga.name.lower()
            pc_path = os.path.join(project, carrier)
        elif self.parent.project_type == DeviceType.SOM:
            project = self.parent.som.hdl_project_folder
            fpga = self.parent.som.fpga
            if not project:
                pc_path = fpga
            else:
                pc_path = os.path.join(project, fpga)
        else:
            raise ValueError(f"Unknown project type {self.parent.project_type}")
        if self.ghdl_project:
            upstream_hdl_dir = os.path.join(
                self.parent.build_dir, self.ghdl_us_hdl_clone_folder_name
            )
            cmd += f" export ADI_HDL_DIR={upstream_hdl_dir} &&"
        cmd += f" cd {self.hdl_clone_folder_name}/projects/{pc_path} &&"
        if self.make_prepend_commands:
            cmd += " "
            cmd += " ".join(self.make_prepend_commands) + " "
        if self.parent.project_type == DeviceType.FPGA_FMC:
            cores = self.parent.fmc.cores
        elif self.parent.project_type == DeviceType.SOM:
            cores = self.parent.som.cores
        cmd += f" make -j{cores}"
        self._run_shell_cmd(cmd)
        os.chdir(cwd)

    def collect_metadata(self):
        print("Collecting metadata for HDL")
        # find folder that ends with .sdk
        if self.parent.project_type == DeviceType.FPGA_FMC:
            project = self.parent.fmc.hdl_project_folder
            carrier = self.parent.fpga.name.lower()
            pc_path = os.path.join(project, carrier)
            project_name = f"{project}_{carrier}"
        elif self.parent.project_type == DeviceType.SOM:
            project = self.parent.som.hdl_project_folder
            fpga = self.parent.som.fpga
            if not project:
                pc_path = fpga
            else:
                pc_path = os.path.join(project, fpga)
            project_name = f"{project}"
        sdk_folder = None
        for root, dirs, files in os.walk(
            os.path.join(
                self.parent.build_dir,
                self.hdl_clone_folder_name,
                "projects",
                pc_path,
            )
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
            f"{project_name}_vivado.log",
        ]
        for root, dirs, files in os.walk(
            os.path.join(
                self.parent.build_dir,
                self.hdl_clone_folder_name,
                "projects",
                pc_path,
            )
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
