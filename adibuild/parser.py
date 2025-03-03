import os
import json

from artifactory import ArtifactoryPath


class Parser:

    root_repo_url = "https://artifactory.analog.com:443/artifactory/"
    repo = "sdg-generic-development"
    api_key = None
    branch = "main"

    def __get_api_env(self):
        if self.api_key is None:
            api_key = os.getenv("ARTIFACTORY_API_KEY")
            if api_key is None:
                raise ValueError("API key not set")
            self.api_key = api_key
        return self.api_key

    def collect_hdl_metadata_artifactory(self):
        # For each commit in main get:
        # - commit hash
        # - commit message
        # - Link to boot files
        # - power report
        # - timing report
        # - utilization report

        folder = f"/hdl/{self.branch}/boot_files"
        logs_folder = f"/hdl/{self.branch}/logs"

        table = {}
        # path = ArtifactoryPath(
        #     self.root_repo_url + self.repo + folder, auth=(self.__get_api_env(), "")
        # )
        path = ArtifactoryPath(
            self.root_repo_url + self.repo + folder,
        )
        # Get dates list
        dates = [x.name for x in path]
        # Get boards list for each date
        lend = len(dates)
        for i, date in enumerate(dates):
            # path = ArtifactoryPath(
            #     self.root_repo_url + self.repo + folder + "/" + date,
            # )
            path_date = path / date
            print(f"Processing {i}/{lend} - {date}")
            boards = [x.name for x in path_date]
            for board in boards:
                if board not in table:
                    table[board] = {}
                # properties = ArtifactoryPath(
                #     self.root_repo_url
                #     + self.repo
                #     + folder
                #     + "/"
                #     + date
                #     + "/"
                #     + board
                #     + "/bootgen_sysfiles.tgz",
                # )
                properties = path_date / board / "bootgen_sysfiles.tgz"
                if not properties.exists():
                    continue
                properties = properties.properties
                log_folder = ArtifactoryPath(
                    self.root_repo_url
                    + self.repo
                    + logs_folder
                    + "/"
                    + date
                    + "/"
                    + board,
                )
                if log_folder.exists():
                    log_files = [x.name for x in log_folder]
                    log_files = [
                        f"{self.root_repo_url}{self.repo}{logs_folder}/{date}/{board}/{x}"
                        for x in log_files
                    ]
                    properties["log_files"] = log_files
                properties[
                    "bootgen_sysfiles.tgz"
                ] = f"{self.root_repo_url}{self.repo}{folder}/{date}/{board}/bootgen_sysfiles.tgz"
                table[board][date] = properties

        print("table")
        print(table)

        # Save to file
        with open("hdl_metadata.json", "w") as f:
            json.dump(table, f)
            print("Saved to hdl_metadata.json")


if __name__ == "__main__":
    p = Parser()
    p.collect_hdl_metadata_artifactory()
