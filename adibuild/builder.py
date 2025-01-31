import os


class Builder:
    def __init__(self, name="adi_project", build_dir: str = "build"):
        self.build_dir = build_dir
        self.name = name
        self.fpga = None
        self.software = []
        self.fmc = None
        self.log_dir = os.path.join(os.getcwd(), "logs")

    def add_fmc(self, fmc):
        self.fmc = fmc

    def add_fpga(self, fpga):
        self.fpga = fpga

    def add_software(self, software, tools):
        self.software.append(software(self, tools))

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
