import logging
import os
import shutil
import datetime

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


def get_ci_info():
    # Get jenkins CI information if available
    ci_info = {
        "BUILD_NUMBER": os.environ.get("BUILD_NUMBER", None),
        "BUILD_URL": os.environ.get("BUILD_URL", None),
        "JOB_NAME": os.environ.get("JOB_NAME", None),
        "NODE_NAME": os.environ.get("NODE_NAME", None),
    }
    return ci_info


def get_jesd_mode():
    return {
        "rx": {
            "M": 4,
            "Np": 16,
            "K": 4,
            "L": 8,
            "S": 1,
            "F": 1,
            "jesd_class": "204C",
            "lane_rate_mbps": 20625,
        },
        "tx": {
            "M": 4,
            "Np": 16,
            "K": 4,
            "L": 8,
            "S": 1,
            "F": 1,
            "jesd_class": "204C",
            "lane_rate_mbps": 20625,
        },
    }


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
    ghdl = HDL()
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

    def __init__(
        self, parent=None, tools=None, pre_clone_func=None, pre_build_func=None
    ):
        self.parent = parent
        self.tools = tools
        self.log_commands = True
        self.log_output = True
        self.log_file = "hdl.log"
        self.commands_file = "hdl_commands.txt"
        self.make_prepend_commands = []
        self.make_postpend_commands = []

        self.pre_clone_func = pre_clone_func
        self.pre_build_func = pre_build_func

        self.gitrepo_https = "https://github.com/analogdevicesinc/hdl.git"
        self.gitrepo_ssh = "git@github.com:analogdevicesinc/hdl.git"
        self.gitrepo_preferred = "https"  # or "ssh" or None
        self.git_tool = "cli"  # or "python"

        self.branch = "main"

        self.hdl_clone_folder_name = "hdl"

        # Cache
        self._logs = None
        self._build_artifacts = None
        self._patch = None
        self._project = None
        self._carrier = None

        # GHDL related
        self.ghdl_project = False
        self.ghdl_us_hdl_branch = "main"
        self.ghdl_us_hdl_clone_folder_name = None
        self.ghdl_us_hdl_repo_https = "https://github.com/adi-innersource/ghdl.git"
        self.ghdl_us_hdl_repo_ssh = "git@github.com:adi-innersource/ghdl.git"
        self.ghdl_us_hdl_repo_preferred = "https"

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
            self.pre_clone_func(self)
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
                if self.ghdl_us_hdl_repo_preferred == 'https':
                    self._run_shell_cmd(
                        f"git clone {self.ghdl_us_hdl_repo_https} -b {self.ghdl_us_hdl_branch} {dir_loc}"
                    )
                else:
                    self._run_shell_cmd(
                        f"git clone {self.ghdl_us_hdl_repo_ssh} -b {self.ghdl_us_hdl_branch} {dir_loc}"
                    )
            else:
                raise NotImplementedError("Only git is supported at this time")
        log.info("Getting source for HDL")
        if self.git_tool:
            dir_loc = os.path.join(self.parent.build_dir, self.hdl_clone_folder_name)
            if self.gitrepo_preferred == 'https':
                self._run_shell_cmd(
                    f"git clone {self.gitrepo_https} -b {self.branch} {dir_loc}"
                )
            else:
                self._run_shell_cmd(
                    f"git clone {self.gitrepo_ssh} -b {self.branch} {dir_loc}"
                )
        else:
            raise NotImplementedError("Only git is supported at this time")

    @gen_script
    def build_source(self):
        if self.pre_build_func:
            log.info("Running pre-build function")
            self.pre_build_func(self)
        log.info("Building source for HDL")
        cwd = os.getcwd()
        os.chdir(self.parent.build_dir)
        cmd = f"{self.tools.source_cmd} &&"
        if self.parent.project_type == DeviceType.FPGA_FMC:
            project = self.parent.fmc.hdl_project_folder
            carrier = self.parent.fpga.name.lower()
            pc_path = os.path.join(project, carrier)
            self._project = project
            self._carrier = carrier
        elif self.parent.project_type == DeviceType.SOM:
            project = self.parent.som.hdl_project_folder
            self._project = project
            fpga = self.parent.som.fpga
            self._carrier = fpga
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
        # cmd += f" make -j{cores}"
        cmd += f" make"
        if self.make_postpend_commands:
            cmd += " "
            cmd += " ".join(self.make_postpend_commands) + " "
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

        self._logs = logs
        self._build_artifacts = build_artifacts

        return build_artifacts, logs

    def upload(self):
        """Upload HDL metadata and build artifacts to the parent project."""
        # Define metadata and artifacts
        assert self._build_artifacts, "No build artifacts found"
        assert self._logs, "No logs found"

        jesd_configs = get_jesd_mode()
        ci_info = get_ci_info()

        upload_date_time = datetime.datetime.now().isoformat()

        def convert_enum_to_str(enum_value):
            if isinstance(enum_value, DeviceType):
                return enum_value.name
            return str(enum_value)

        metadata = {
            "fpga": (
                self.parent.fpga.name
                if self.parent.project_type == DeviceType.FPGA_FMC
                else self.parent.som.fpga.name
            ),
            "fmc": (
                self.parent.fmc.name
                if self.parent.project_type == DeviceType.FPGA_FMC
                else None
            ),
            # "build_artifacts": self._build_artifacts,
            # "log_files": self._logs,
            "make_prepend_commands": self.make_prepend_commands,
            "make_postpend_commands": self.make_postpend_commands,
            "branch": self.branch,
            "commit_hash": self._get_git_commit(),
            "git_tag": self._get_git_commit(tag_check=True),
            "project_type": convert_enum_to_str(self.parent.project_type),
            "patch": self._patch,
            "timing_passed": True,
            "jesd_project": True,
            "jesd_configs": jesd_configs,
            "ci_info": ci_info,
            "upload_date_time": upload_date_time,
        }

        results_bas = self.parent.upload_artifacts("HDL", self._build_artifacts)
        result_logs = self.parent.upload_artifacts("HDL", self._logs)

        # Update metadata with upload results
        metadata["build_artifacts"] = []
        for key in results_bas:
            metadata["build_artifacts"].append({
                "file_name": key,
                "location": results_bas[key].location,
                "object_name": results_bas[key].object_name,
                "etag": results_bas[key].etag,
                "bucket_name": results_bas[key].bucket_name,
            })
        metadata["log_files"] = []
        for key in result_logs:
            metadata["log_files"].append({
                "file_name": key,
                "location": result_logs[key].location,
                "object_name": result_logs[key].object_name,
                "etag": result_logs[key].etag,
                "bucket_name": result_logs[key].bucket_name,
            })


        self.parent.upload_metadata("HDL", metadata)

