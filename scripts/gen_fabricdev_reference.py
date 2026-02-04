"""Similar to Kuiper gen but for fabric devices (Virtex/Kintex)."""
import os
from pprint import pprint
import json

from gen_kuiper_reference import clone_repo, parse_dts_for_hdl_info

def find_hdl_parameters(dts_path):
    """Find the HDL parameters in the given DTS file."""
    with open(dts_path, "r") as f:
        content = f.read()
    lines = content.splitlines()
    keys = ['JESD_', 'KS_PER_CHANNEL', 'REF_CLK=', 'RATE=']
    negatives = ['MODE', 'SUBCLASS','VERSION','AD9']
    parameters = {}
    for line in lines:
        for key in keys:
            if key in line:
                if any(neg in line for neg in negatives):
                    print(f"Skipping line due to negative match: {line}")
                    continue
                # Extract the value after the '=' sign and before the ';' sign
                value = line.split('=')[1].strip()
                param = line.split('=')[0].strip().replace("/","").strip()
                parameters[param] = value
                
    return parameters

def parse_fabric_designs(release):
    """Parse the fabric design files for the given release."""
    # Clone repo if not already done
    linux_source_dir = "linux"
    if release == "2023_R2_P1":
        release = "2023_R2"
    clone_repo("https://github.com/analogdevicesinc/linux.git", release, linux_source_dir)

    # Parse ADI devicetrees that are in the repo
    # Search within the arch/microblaze/boot/dts directory for files that match the pattern ad9361-*.dts
    # and print the names of those files
    project_map = {}
    dts_dir = os.path.join(linux_source_dir, "arch/microblaze/boot/dts")
    carriers = ["vcu118", "kcu105"]
    for carrier in carriers:
        for root, dirs, files in os.walk(dts_dir):
            for file in files:
                if carrier in file and file.endswith(".dts"):
                    full_path = os.path.join(root, file)
                    print(f"Found fabric design: {file}")
                    print(f"Path: {full_path}")
                else:
                    continue
                with open(full_path, "r") as f:
                    content = f.read()
                lines = content.splitlines()
                for line in lines:
                    if "hdl_project" in line:
                        project, fpga = parse_dts_for_hdl_info(full_path)
                        print(f"Project: {project}, Carrier: {fpga}")
                        if project:
                            # relative path from the root of the repo
                            dts_path = os.path.relpath(full_path, linux_source_dir)
                            if project not in project_map:
                                project_map[project] = []
                            project_map[project].append({
                                "carrier": fpga,
                                "dts_path": dts_path,
                                "hdl_parameters": find_hdl_parameters(full_path)
                            })
                        break
    
    print("\nSummary of fabric designs:")
    pprint(project_map)

    return project_map



if __name__ == "__main__":

    # Example usage
    all_projects = {}
    for release in ["2022_R2", "2023_R2", "2023_R2_P1"]:
        project_map = parse_fabric_designs(release)
        all_projects[release] = project_map

    print("\nFinal summary of all fabric designs across releases:")
    pprint(all_projects)

    # Save the results to a JSON file
    with open("fabric_release_info.json", "w") as f:
        json.dump(all_projects, f, indent=4)

    # Move to adibuild directory
    here = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(here, "..", "adibuild")
    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"Target directory {target_dir} does not exist.")
    os.rename("fabric_release_info.json", os.path.join(target_dir, "fabric_release_info.json"))