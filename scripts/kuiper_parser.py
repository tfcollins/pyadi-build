# Download Kuiper boots files

release = "2022_r2"
url = f"https://swdownloads.analog.com/cse/boot_partition_files/{release}/latest_boot_partition.tar.gz"

import os
import subprocess
import tarfile

# Download the file
import requests
from tqdm import tqdm


def download_file(url, local_filename):
    # NOTE the stream=True parameter below
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get("content-length", 0))
    block_size = 1024  # 1 Kibibyte
    progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
    with open(local_filename, "wb") as f:
        for data in r.iter_content(block_size):
            progress_bar.update(len(data))
            f.write(data)
    progress_bar.close()
    if total_size != 0 and progress_bar.n != total_size:
        print("ERROR, something went wrong")
    else:
        print("Download completed successfully!")


# Create a directory to store the downloaded files
download_dir = "kuiper_boot_files"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)
# Download the file
# download_file(url, os.path.join(download_dir, f"{release}_boot_partition.tar.gz"))


# Extract the tar.gz file
def extract_and_parse():
    print("Extracting the tar.gz file...")
    to_ignore = ["zynq-common", "zynqmp-common"]

    tar_file_path = os.path.join(download_dir, f"{release}_boot_partition.tar.gz")
    with tarfile.open(tar_file_path, "r:gz") as tar:
        tar.extractall(path=download_dir)
    # Remove the tar.gz file after extraction
    # os.remove(tar_file_path)
    # List the extracted files
    extracted_files = os.listdir(download_dir)
    print("Extracted files:")
    devicetree_targets = []
    for file in extracted_files:
        if file in to_ignore:
            print(f"Skipping: {file}")
            continue
        # check if folder
        if os.path.isdir(os.path.join(download_dir, file)):
            # Check if the folder contains subfolders
            subfolder_name = os.listdir(os.path.join(download_dir, file))
            folders = [
                f
                for f in subfolder_name
                if os.path.isdir(os.path.join(download_dir, file, f))
            ]
            if len(folders) > 0:
                for subfolder in folders:
                    if subfolder not in to_ignore:
                        # subfolder_full = os.path.join(file, subfolder)
                        devicetree_targets.append(subfolder)
                        # print(f"Subfolder saved: {subfolder_full}")
            else:
                devicetree_targets.append(file)

    print("Device tree targets:")
    for target in devicetree_targets:
        print(target)

    return devicetree_targets


devicetree_targets = extract_and_parse()


def check_urls(devicetree_targets):
    linux_url_template_arm_xilinx = "https://github.com/analogdevicesinc/linux/blob/main/arch/arm/boot/dts/{dts}.dts"
    linux_url_template_arm64_xilinx = "https://github.com/analogdevicesinc/linux/blob/main/arch/arm64/boot/dts/xilinx/{dts}.dts"

    valid_urls = {}
    for target in devicetree_targets:
        if "zynqmp" in target:
            linux_url = linux_url_template_arm64_xilinx.format(dts=target)
        elif "zynq" in target:
            linux_url = linux_url_template_arm_xilinx.format(dts=target)
        else:
            valid_urls[target] = "NA"
            continue

        # Check is url is valid
        response = requests.head(linux_url)
        if response.status_code == 200:
            print(f"Valid URL: {linux_url}")
            valid_urls[target] = "OK"
        else:
            print(f"Invalid URL: {linux_url}")
            valid_urls[target] = "Invalid URL"
            # continue

        import time

        time.sleep(3)

    return valid_urls


# Check the URLs
# valid_urls = check_urls(devicetree_targets)


def clone_linux_and_parse(devicetree_targets):

    target_dir = "linux"

    if not os.path.exists(target_dir):
        print(f"Cloning Linux repository into {target_dir}...")
        cmds = [
            "git",
            "clone",
            "--depth=1",
            "-b",
            "2023_R2",
            "https://github.com/analogdevicesinc/linux.git",
            target_dir,
        ]
        # Run the command
        result = subprocess.run(cmds, capture_output=True, text=True)
        # Check the result
        if result.returncode == 0:
            print("Linux repository cloned successfully.")
        else:
            print("Error cloning Linux repository:")
            print(result.stderr)

    # Parse for the device tree files
    dts_files = {}
    for target in devicetree_targets:
        if "zynqmp" in target:
            dts_file = f"arch/arm64/boot/dts/xilinx/{target}.dts"
        elif "zynq" in target:
            dts_file = f"arch/arm/boot/dts/{target}.dts"
        else:
            print(f"Unknown target: {target}")
            continue

        if os.path.exists(os.path.join(target_dir, dts_file)):
            print(f"Found: {dts_file}")
            dts_files[target] = dts_file
        else:
            print(f"Not found: {dts_file}")
            dts_files[target] = "Not found"

    # Parse the dts files
    projects = {}
    for target in dts_files:
        dts_file = dts_files[target]
        if dts_file == "Not found":
            print(f"Skipping: {target} - {dts_file}")
            projects[target] = {
                "project_path": "Not found",
                "dts_file": "Not found",
            }
            continue
        with open(os.path.join(target_dir, dts_file), "r") as f:
            lines = f.readlines()
            for line in lines:
                if "hdl_project" in line:
                    # parse the line for the project name
                    #  hdl_project: <ad7768evb/zed>
                    project_path = (
                        line.split(":")[1].strip().replace("<", "").replace(">", "")
                    )
                    projects[target] = {
                        "project_path": project_path,
                        "dts_file": dts_file,
                    }
                    print(f"Found project: {project_path} in {dts_file}")

    return projects


projects = clone_linux_and_parse(devicetree_targets)


def clone_hdl_and_parse(projects):

    target_dir = "hdl"

    if not os.path.isdir(target_dir):
        print(f"Cloning HDL repository into {target_dir}...")
        cmds = [
            "git",
            "clone",
            "--depth=1",
            "-b",
            "hdl_2023_r2",
            "https://github.com/analogdevicesinc/hdl.git",
            target_dir,
        ]

        # Run the command
        result = subprocess.run(cmds, capture_output=True, text=True)

        # Check the result
        if result.returncode == 0:
            print("HDL repository cloned successfully.")
        else:
            print("Error cloning HDL repository:")
            print(result.stderr)
            return None

    # verify if the project exists
    projects_with_valids = {}
    for project in projects:
        if projects[project]["project_path"] == "Not found":
            projects_with_valids[project] = {
                "dts_file": projects[project]["dts_file"],
                "hdl_path": "Not found",
            }

        project_dir = projects[project]["project_path"]
        project_path = os.path.join(target_dir, "projects", project_dir)
        if os.path.exists(project_path):
            print(f"Found project: {project}")
            pdir = project_dir
        else:
            print(f"Project not found: {project}")
            pdir = "Not found"

        projects_with_valids[project] = {
            "dts_file": projects[project]["dts_file"],
            "hdl_path": pdir,
        }

    return projects_with_valids


projects_with_valids = clone_hdl_and_parse(projects)

from pprint import pprint

pprint(projects_with_valids)

# Generate markdown table from results in projects_with_valids
def generate_markdown_table(projects_with_valids):
    table = "| Project | DTS File | HDL Path |\n"
    table += "| ------- | -------- | -------- |\n"
    for project, data in projects_with_valids.items():
        table += f"| {project} | {data['dts_file']} | {data['hdl_path']} | \n"
    return table


markdown_table = generate_markdown_table(projects_with_valids)

# Save the markdown table to a file
with open("projects_with_valids.md", "w") as f:
    f.write(markdown_table)
