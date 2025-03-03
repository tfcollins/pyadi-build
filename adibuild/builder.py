import os
from .models.common import DeviceType

class Builder:
    def __init__(self, name="adi_project", build_dir: str = "build"):
        self.build_dir = build_dir
        self.name = name
        self.fpga = None
        self.software = []
        self.fmc = None
        self.som = None
        self.log_dir = os.path.join(os.getcwd(), "logs")

    @property
    def project_type(self):
        if self.fmc and self.fpga:
            return DeviceType.FPGA_FMC
        elif self.som:
            return DeviceType.SOM
        else:
            raise ValueError("Device not set")

    def add_fmc(self, fmc):
        if self.som:
            raise ValueError("Cannot have both FMC and SOM in the same project")
        self.fmc = fmc

    def add_fpga(self, fpga):
        if self.som:
            raise ValueError("Cannot have both FMC and SOM in the same project")
        self.fpga = fpga

    def add_som(self, som):
        if self.fmc or self.fpga:
            raise ValueError("Cannot have both FMC and SOM in the same project")
        self.som = som

    def add_software(self, software, tools):
        software.parent = self
        software.tools = tools
        self.software.append(software)

    def build(self):

        self.build_dir = os.path.abspath(self.build_dir)

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)

        all_artifacts = []
        all_logs = []

        for sw in self.software:

            # Reset logs
            sw.reset_logs()

            # Check tools
            sw.tools_check()

            # Get source
            sw.get_source()

            # Build source
            sw.build_source()

            # Collect metadata and build artifacts
            files, logs = sw.collect_metadata()
            all_artifacts.extend(files)
            all_logs.extend(logs)

        return all_artifacts, all_logs
