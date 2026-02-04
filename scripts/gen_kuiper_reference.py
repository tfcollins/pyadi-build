import hashlib
import json
import lzma
import os
import pathlib
import shutil
import time
import zipfile
import logging
import requests
import subprocess
from difflib import SequenceMatcher
from pprint import pprint

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from tqdm import tqdm

from imageextractor import IMGFileExtractor

logger = logging.getLogger(__name__)

# Show only errors
logger.setLevel(logging.ERROR)


# Custom Exception
class NoDTSFoundError(Exception):
    """Raised when no DTS file is found in the extracted image."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Downloader:
    """Utility class for downloading and verifying Kuiper Linux releases.

    This class handles downloading release archives from ADI's servers,
    verifying MD5 checksums, and extracting compressed archives. It supports
    both .xz and .zip compressed formats and displays progress bars using tqdm.

    The Downloader is used internally by KuiperDLDriver but can also be used
    standalone via the kuiperdl CLI tool.

    Example:
        >>> dl = Downloader()
        >>> rel = dl.releases("2023_R2_P1")
        >>> dl.download(rel["link"], rel["zipname"])
        >>> dl.check(rel["zipname"], rel["zipmd5"])
        >>> dl.extract(rel["zipname"], rel["imgname"])
    """

    def releases(self, release="2019_R1"):
        rel = {}
        valid_releases = ["2018_R2", "2019_R1", "2023_R2_P1"]
        if release == "2018_R2":
            rel["imgname"] = "2018_R2-2019_05_23.img"
            rel["xzmd5"] = "c377ca95209f0f3d6901fd38ef2b4dfd"
            rel["imgmd5"] = "59c2fe68118c3b635617e36632f5db0b"
        elif release == "2019_R1":
            rel["imgname"] = "2019_R1-2020_02_04.img"
            rel["xzmd5"] = "49c121d5e7072ab84760fed78812999f"
            rel["imgmd5"] = "40aa0cd80144a205fc018f479eff5fce"
        elif release == "2022_R2":
            rel["imgname"] = "image_2023-12-13-ADI-Kuiper-full"
            rel["zipmd5"] = "9dfd5d57573e14e06715a08b19a6a26a"
            rel["imgmd5"] = "e3620b6d36ad0481b79eee6041769f38"
        elif release == "2023_R2":
            # https://swdownloads.analog.com/cse/kuiper/image_2024-11-08-ADI-Kuiper-full.zip
            rel["imgname"] = "image_2024-11-08-ADI-Kuiper-full"
            rel["zipmd5"] = "338f747964283b518c6492addca90ad5"
            rel["imgmd5"] = "7764911b0b0da4a022706418a012c411"
        elif release == "2023_R2_P1":
            # https://swdownloads.analog.com/cse/kuiper/image_2025-03-18-ADI-Kuiper-full.zip
            rel["imgname"] = "image_2025-03-18-ADI-Kuiper-full"
            # rel["imgname"] = "2023_R2_P1-2025_03_18.img"
            rel["zipmd5"] = "6c92259dd61520d08244012f6c92d7c6"
            rel["imgmd5"] = "873b4977617e40725025aa4958f3ca7e"
        else:
            raise Exception(f"Unknown release version {release}. Valid releases: {valid_releases}")
        if "xzmd5" in rel:
            rel["link"] = "http://swdownloads.analog.com/cse/" + rel["imgname"] + ".xz"
            rel["xzname"] = rel["imgname"] + ".xz"
        elif "zipmd5" in rel:
            rel["link"] = "https://swdownloads.analog.com/cse/kuiper/" + rel["imgname"] + ".zip"
            rel["zipname"] = rel["imgname"] + ".zip"
        return rel

    def retry_session(
        self,
        retries=3,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 504),
        session=None,
    ):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def download(self, url, fname):
        resp = self.retry_session().get(url, stream=True)
        if not resp.ok:
            raise Exception(os.path.basename(fname) + " - File not found!")
        total = int(resp.headers.get("content-length", 0))
        sha256_hash = hashlib.sha256()
        with (
            open(fname, "wb") as file,
            tqdm(
                desc=fname,
                total=total,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar,
        ):
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                sha256_hash.update(data)
                bar.update(size)
        hash = sha256_hash.hexdigest()
        with open(os.path.join(os.path.dirname(fname), "hashes.txt"), "a") as h:
            h.write(f"{os.path.basename(fname)},{hash}\n")

    def check(self, fname, ref, find_img=False):
        print("Checking " + fname + " against reference MD5: " + ref)
        hash_md5 = hashlib.md5()
        if find_img and not os.path.isfile(fname):
            # Search for img file in same directory
            dirpath = os.path.abspath(fname)
            # dirpath = os.path.dirname(fname)
            for file in os.listdir(dirpath):
                if file.endswith(".img"):
                    fname = os.path.join(dirpath, file)
                    print(f"Found image file {fname} for MD5 check")
                    break
            if not os.path.isfile(fname):
                raise Exception("No image file found for MD5 check")
        else:
            print("Using file " + fname + " for MD5 check")
        tlfile = pathlib.Path(fname)
        total = os.path.getsize(tlfile)
        with (
            open(fname, "rb") as f,
            tqdm(
                desc="Hashing: " + fname,
                total=total,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar,
        ):
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
                size = len(chunk)
                bar.update(size)
        h = hash_md5.hexdigest()
        if h == ref:
            print("MD5 Check: PASSED")
        else:
            print("MD5 Check: FAILEDZz")
            raise Exception("MD5 hash check failed")

        return fname

    def extract(self, inname, outname):
        print("Extracting " + inname + " to " + outname)
        if inname.endswith(".xz"):
            self.extract_xz(inname, outname)
        elif inname.endswith(".zip"):
            self.extract_zip(inname, outname)
        else:
            raise Exception("Unknown compression format for " + inname)

    def extract_xz(self, inname, outname):
        tlfile = pathlib.Path(inname)

        decompressor = lzma.LZMADecompressor()
        with open(tlfile, "rb") as ifile:
            total = 0
            with (
                open(outname, "wb") as file,
                tqdm(
                    desc="Decompressing: " + outname,
                    total=total,
                    unit="iB",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar,
            ):
                data = ifile.read(1024)
                while data:
                    result = decompressor.decompress(data)
                    if result != b"":
                        size = file.write(result)
                        bar.update(size)
                    data = ifile.read(1024)

    def extract_zip(self, inname, outdir):
        tlfile = pathlib.Path(inname)
        with zipfile.ZipFile(tlfile, "r") as zip_ref:
            zip_ref.extractall(outdir)


class KuiperDLDriver:
    """KuiperDLDriver - Driver to download and manage Kuiper releases and provide
    files to the target device.
    """

    sw_downloads_template = "https://swdownloads.analog.com/cse/boot_partition_files/{release}/latest_boot_partition.tar.gz"

    cache_datafile = "cache_info.json"

    cache_path = "/tmp/kuiper_cache"

    release_version = "2023_R2_P1"

    def __init__(self, release_version=None, output_dir=None):
        self.release_version = release_version
        self.output_dir = output_dir
        self._boot_files = []
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())

    def check_cached(self, release_version=None):
        """Check if the specified Kuiper release version is cached locally.
        Args:
            release_version (str): Version of the Kuiper release to check. If None, uses the version from kuiper_resource.

        Returns:
            bool: True if the release is cached, False otherwise.
        """
        cache_path = self.cache_path
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        cache_file_path = os.path.join(cache_path, self.cache_datafile)
        if not os.path.exists(cache_file_path):
            return False

        if release_version is None:
            release_version = self.release_version

        # Read cache file and check version
        with open(cache_file_path) as f:
            cache_data = json.load(f)

        for release in cache_data:
            if release == release_version:
                # Verify that the tarball path exists
                image_path = cache_data[release]["image_path"]
                if os.path.exists(image_path):
                    return True
        return False

    def download_release(self, release_version=None, get_boot_files=False):
        """Download the specified Kuiper release version if not already cached.
        Args:
            release_version (str): Version of the Kuiper release to download. If None, uses the version from kuiper_resource.
        """
        if release_version is None:
            release_version = self.release_version

        if self.check_cached(release_version):
            self.logger.info(f"Kuiper release {release_version} is already cached.")
            return

        if get_boot_files:
            url = self.sw_downloads_template.format(release=release_version)
            self.logger.info(f"Downloading Kuiper boot_files {release_version} from {url}")

            cache_path = self.cache_path
            if not os.path.exists(cache_path):
                os.makedirs(cache_path)

            tarball_path = os.path.join(cache_path, f"{release_version}_boot_partition.tar.gz")
            raise NotImplementedError("Boot files download not implemented yet.")
        else:
            downloader = Downloader()
            rel_info = downloader.releases(release_version)
            url = rel_info["link"]
            self.logger.info(f"Downloading Kuiper release {release_version} from {url}")

            cache_path = self.cache_path
            if not os.path.exists(cache_path):
                os.makedirs(cache_path)

            if "xzname" in rel_info:
                tarball_path = os.path.join(cache_path, rel_info["xzname"])
            elif "zipname" in rel_info:
                tarball_path = os.path.join(cache_path, rel_info["zipname"])
            else:
                raise Exception("Unknown file name for release " + release_version)

            name_archive = rel_info["xzname"] if "xzname" in rel_info else rel_info["zipname"]
            md5_archive = rel_info["xzmd5"] if "xzmd5" in rel_info else rel_info["zipmd5"]
            downloader.download(rel_info["link"], name_archive)
            downloader.check(name_archive, md5_archive)
            downloader.extract(name_archive, rel_info["imgname"])
            img_file = downloader.check(rel_info["imgname"], rel_info["imgmd5"], find_img=True)

            # Move img file to cache path
            self.logger.info(f"Caching Kuiper release {release_version} files to {cache_path}")
            img_filename = os.path.basename(img_file)
            target_path = os.path.join(cache_path, img_filename)
            shutil.move(img_file, target_path)

            # Cleanup
            self.logger.info("Cleaning up temporary files")
            if os.path.exists(tarball_path):
                os.remove(tarball_path)
                # shutil.move(tarball_path, cache_path)
            if os.path.isfile(name_archive):
                os.remove(name_archive)
            if os.path.isdir(rel_info["imgname"]):
                os.rmdir(rel_info["imgname"])

        # Update cache info
        cache_file_path = os.path.join(cache_path, self.cache_datafile)
        cache_data = {}
        if os.path.exists(cache_file_path):
            with open(cache_file_path) as f:
                cache_data = json.load(f)

        cache_data[release_version] = {
            # "tarball_path": tarball_path,
            "image_path": target_path,
            "download_time": time.ctime(),
            "download_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }

        with open(cache_file_path, "w") as f:
            json.dump(cache_data, f, indent=4)

        self.logger.info(f"Kuiper release {release_version} cached successfully.")

    def __del__(self):
        ...
        # try:
        #     self.unmount_partition()
        # except Exception:
        #     pass

    def get_boot_files_from_release(self, get_all_files=True):
        if not self.check_cached():
            self.download_release(get_boot_files=False)

        with open(os.path.join(self.cache_path, self.cache_datafile)) as f:
            cache_data = json.load(f)
        release_info = cache_data[self.release_version]

        img = IMGFileExtractor(release_info["image_path"], logger=self.logger)
        for i, part in enumerate(img.get_partitions()):
            self.logger.debug(f"  {i}: {part['description']} - Offset: {part['start']} bytes")

        # List files in FAT partition
        partitions_info = img.get_partitions()
        fat_partition = None
        for part in partitions_info:
            if "FAT" in part["description"]:
                fat_partition = part
                break
        if fat_partition is None:
            raise Exception("No FAT partition found in Kuiper image")

        fs = img.open_filesystem(fat_partition["start"])
        files = img.list_files(fs, "/")
        files_str = ""
        for f in files:
            files_str += f"{f['type']}: {f['path']} ({f['size']} bytes)\n"

        if get_all_files:
            return files

def clone_repo(repo_url, branch, dest_dir):
    """Clone a git repository to a destination directory.

    Args:
        repo_url (str): URL of the git repository.
        branch (str): Branch to clone.
        dest_dir (str): Destination directory.
    """
    # Use subprocess to clone the repository
    print(f"Cloning {repo_url} branch {branch} to {dest_dir}")
    if os.path.exists(dest_dir):
        print(f"Directory {dest_dir} already exists. Skipping clone.")
        # Check branch of the repository is what we want
        output = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=dest_dir)
        current_branch = output.decode("utf-8").strip()
        if current_branch != branch:
            print(f"Changing branch from {current_branch} to {branch}")
            subprocess.run(["git", "checkout", branch], cwd=dest_dir, check=True)
            # raise Exception(f"Branch of the repository is {current_branch}, expected {branch}. Skipping clone.")
        return
    # subprocess.run(["git", "clone", "--depth", "1", "--branch", branch, repo_url, dest_dir], check=True)
    subprocess.run(["git", "clone", "--branch", branch, repo_url, dest_dir], check=True)

def parse_kuiper_release(release_version, files, linux_source_dir=None, hdl_source_dir=None, score_required=0.90):
    """Parse Kuiper file list and generate map to source tree files.

    Args:
        release_version (str): Version of the Kuiper release.
        files (list): List of files in the Kuiper release.
        linux_source_dir (str): Path to the Linux source directory.
        hdl_source_dir (str): Path to the HDL source directory.
    Returns:
        dict: Dictionary mapping Kuiper files to source tree paths.
    """
    if not linux_source_dir:
        linux_source_dir = os.path.join(os.path.dirname(__file__), "linux")


    if not hdl_source_dir:
        hdl_source_dir = os.path.join(os.path.dirname(__file__), "hdl")

    # Map linux branch to release version
    if release_version == "2023_R2_P1":
        linux_branch = "2023_R2"
    elif release_version == "2023_R2":
        linux_branch = "2023_R2"
    elif release_version == "2022_R2":
        linux_branch = "2022_R2"
    else:
        raise Exception(f"Linux branch not found for release version {release_version}")


    clone_repo("https://github.com/analogdevicesinc/linux.git", linux_branch, linux_source_dir)

    # Map hdl branch to release version
    if release_version == "2023_R2_P1":
        hdl_branch = "hdl_2023_r2"
    elif release_version == "2023_R2":
        hdl_branch = "hdl_2023_r2"
    elif release_version == "2022_R2":
        hdl_branch = "hdl_2022_r2"
    else:
        raise Exception(f"HDL branch not found for release version {release_version}")

    clone_repo("https://github.com/analogdevicesinc/hdl.git", hdl_branch, hdl_source_dir)

    project_map = {}

    def find_devicetree_file_in_kernel_source(devicetree_filename, kernel_source_dir, fuzzy=False, score_required=0.7):
        # Make sure devicetree_filename ends with .dts
        ext = devicetree_filename[-4:]
        if ext != ".dts":
            devicetree_filename += ".dts"
        for root, dirs, files in os.walk(kernel_source_dir):
            for file in files:
                if file == devicetree_filename:
                    return os.path.join(root, file)
        if fuzzy:
            for root, dirs, files in os.walk(kernel_source_dir):
                for file in files:
                    if file.endswith(".dts"):
                        score = SequenceMatcher(None, devicetree_filename, file).ratio()
                        if score >= score_required:
                            return os.path.join(root, file)
        return None

    def parse_dts_for_hdl_info(devicetree_file):
        with open(devicetree_file, "r") as f:
            devicetree_content = f.read()
        # Look for line with hdl_project: <project/carrier> ex: <ad9081_fmca_ebz/zcu102>
        for line in devicetree_content.split("\n"):
            if "hdl_project" in line:
                project_carrier = line.split(":")[1].strip()
                project_carrier = project_carrier.replace("<", "").replace(">", "")
                project = project_carrier.split("/")[0].strip()
                if len(project_carrier.split("/")) != 2:
                    return project, None
                carrier = project_carrier.split("/")[1].strip()
                return project, carrier
        return None, None
        

    


    # Handl all xilinx/amd designs
    not_found = []
    for file in files:
        if "zynq" in file['path'] and file['type'] == "file":
            filename = file['path'].split("/")[-1]
            if filename[-4:] != ".dtb":
                continue
            slash_count = file['path'].count("/")
            # if slash_count == 3:
            #     devicetree_filename = file['path'].split("/")[2]
            # else:
            #     devicetree_filename = file['path'].split("/")[1]

            for i in range(1,slash_count):
                devicetree_filename = file['path'].split("/")[i]
                devicetree_file = find_devicetree_file_in_kernel_source(devicetree_filename, linux_source_dir)
                if devicetree_file:
                    break
            if not devicetree_file:
                # Try fuzzy find
                for i in range(1,slash_count):
                    devicetree_filename = file['path'].split("/")[i]
                    devicetree_file = find_devicetree_file_in_kernel_source(devicetree_filename, linux_source_dir, fuzzy=True, score_required=score_required)
                    if devicetree_file:
                        break


            if devicetree_file:
                logger.debug(f"Found {devicetree_filename}")
                project, carrier = parse_dts_for_hdl_info(devicetree_file)
                # Get devicetree file in reference to linux path
                devicetree_file_from_linux = os.path.relpath(devicetree_file, linux_source_dir)
                kernel_common = "zynqmp-common/Image" if "zynqmp" in devicetree_file_from_linux else "zynq-common/uImage"
                hdl_project_folder = f"{project}/{carrier}" if project and carrier else project
                logger.debug(f"HDL Project: {hdl_project_folder} : {devicetree_file_from_linux}")
                if project:
                    if project not in project_map:
                        project_map[project] = [{'carrier': carrier, 'devicetree': devicetree_file_from_linux, 'kernel': kernel_common, 'hdl_project': hdl_project_folder}]
                    else:
                        project_map[project].append({'carrier': carrier, 'devicetree': devicetree_file_from_linux, 'kernel': kernel_common, 'hdl_project': hdl_project_folder})
                else:
                    not_found.append({"devicetree_filename": devicetree_filename, "path":  file['path']})
            if not devicetree_file:
                not_found.append({"devicetree_filename": devicetree_filename, "path":  file['path']})
                raise NoDTSFoundError(f"Devicetree file {devicetree_filename} not found in kernel source directory {linux_source_dir}")
    
    # Check for duplicate devicetrees
    # all_dts = []
    # for project in project_map:
    #     for carrier in project_map[project]:
    #         all_dts.append(carrier['devicetree'])
    
    # duplicates = []
    # for dts in all_dts:
    #     if all_dts.count(dts) > 1:
    #         duplicates.append(dts)
    
    # print(f"Duplicate devicetrees: {duplicates}")
    # if len(duplicates) > 0:
    #     raise Exception(f"Duplicate devicetrees found: {duplicates}")

    metadata = {
        "project_map": project_map,
        "release_version": release_version,
        "linux_branch": linux_branch,
        "hdl_branch": hdl_branch,
    }
    logger.debug(f"Metadata: {metadata}")
    logger.debug(f"Not Found: {not_found}")

    return metadata, not_found



if __name__ == "__main__":

    release_metadata = {}
    for release in ["2022_R2", "2023_R2", "2023_R2_P1"]:
        kuiper_dl_driver = KuiperDLDriver(
            release_version=release,
            # output_dir="/tmp/kuiper_reference",
        )
        files = kuiper_dl_driver.get_boot_files_from_release()
        for fuzz_score in range(99, 89, -1):
            fuzz_score = float(fuzz_score)/100
            print(f"\nParse release {release} with fuzz score {fuzz_score}")
            try:
                metadata, not_found = parse_kuiper_release(kuiper_dl_driver.release_version, files, score_required=fuzz_score)
                if not not_found:
                    break
            except NoDTSFoundError as e:
                logger.error(e)
                not_found = True
                metadata = None
        release_metadata[release] = metadata
        # break # Debug
    
    pprint(release_metadata)

    # Write to JSON
    json_filename = "kuiper_release_info.json"
    with open(json_filename, "w") as f:
        json.dump(release_metadata, f, indent=4)
    print(f"Generated JSON {json_filename}")

    # Move to adibuild folder
    here = os.path.dirname(os.path.abspath(__file__))
    adibuild = os.path.join(here, "..", "adibuild")
    if not os.path.exists(adibuild):
        raise Exception(f"adibuild folder not found at {adibuild}")
    os.rename(json_filename, os.path.join(adibuild, json_filename))
    print(f"Moved to {adibuild}")

        