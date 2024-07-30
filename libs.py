import os
import platform
import requests
import zipfile
import io
import tarfile
import subprocess
import json
import datetime
from converter import Converter
from packager import create_packager_command, run_packager_command

def download_and_extract(url, file_name, extract_dir):
    response = requests.get(url)
    if 'zip' in file_name:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(extract_dir)
    elif 'tar' in file_name:
        with tarfile.open(fileobj=io.BytesIO(response.content)) as t:
            t.extractall(extract_dir)
    else:
        with open(file_name, 'wb') as f:
            f.write(response.content)
    print(f"Downloaded and extracted {file_name}")

def check_ffmpeg_ffprobe():
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == 'windows':
        bin_url = "https://ffbinaries.com/api/v1/version/latest"
        os_type = 'windows-64' if '64' in arch else 'windows-32'
    elif system == 'linux':
        bin_url = "https://ffbinaries.com/api/v1/version/latest"
        if 'arm' in arch:
            os_type = 'linux-arm64' if '64' in arch else 'linux-armhf'
        else:
            os_type = 'linux-64' if '64' in arch else 'linux-32'
    elif system == 'darwin':
        bin_url = "https://ffbinaries.com/api/v1/version/latest"
        os_type = 'osx-64'
    else:
        raise Exception("Unsupported OS")

    bin_dir = os.path.join(os.getcwd(), 'bin')
    ffmpeg_path = os.path.join(bin_dir, 'ffmpeg')
    ffprobe_path = os.path.join(bin_dir, 'ffprobe')

    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)

    if not os.path.exists(ffmpeg_path) or not os.path.exists(ffprobe_path):
        response = requests.get(bin_url)
        data = response.json()
        ffmpeg_url = data['bin'][os_type]['ffmpeg']
        ffprobe_url = data['bin'][os_type]['ffprobe']
        zip_response = requests.get(ffmpeg_url)
        with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
            z.extractall(bin_dir)
        zip_response = requests.get(ffprobe_url)
        with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
            z.extractall(bin_dir)
        print(f"ffmpeg and ffprobe downloaded and extracted to {bin_dir}")
    else:
        print("ffmpeg and ffprobe already exist")

def check_shaka_packager():
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    bin_url = "https://api.github.com/repos/shaka-project/shaka-packager/releases/latest"
    bin_dir = os.path.join(os.getcwd(), 'bin')
    
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)

    response = requests.get(bin_url)
    data = response.json()
    assets = data['assets']
    
    target_files = {
        "windows": ["packager-win-x64.exe", "mpd_generator-win-x64.exe"],
        "linux": [f"packager-linux-{arch}", f"mpd_generator-linux-{arch}"],
        "darwin": [f"packager-osx-{arch}", f"mpd_generator-osx-{arch}"]
    }
    
    for asset in assets:
        for key, file_names in target_files.items():
            for file_name in file_names:
                if key in system and file_name in asset['name']:
                    download_url = asset['browser_download_url']
                    file_path = os.path.join(bin_dir, asset['name'])
                    
                    if not os.path.exists(file_path):
                        download_and_extract(download_url, file_path, bin_dir)
                    else:
                        print(f"{asset['name']} already exists in {bin_dir}")

def process_mkv_file(file_path, log_signal, progress_signal):
    if not file_path.endswith('.mkv'):
        return {"error": "Invalid file type"}

    if not os.path.exists(file_path):
        return {"error": f"File does not exist: {file_path}"}

    converter = Converter()
    converter.log_signal.connect(log_signal)
    converter.progress_signal.connect(progress_signal)
    result = converter.process_mkv_file(file_path)

    if "error" in result:
        return result

    converted_json_path = 'converted.json'
    data_json_path = 'data.json'
    output_directory = 'output'

    # Ensure converted.json exists before proceeding
    if not os.path.exists(converted_json_path):
        log_signal.emit("Error: 'converted.json' file not found.")
        return {"error": "'converted.json' file not found"}

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    packager_command = create_packager_command(converted_json_path, data_json_path, output_directory)
    run_packager_command(packager_command)

    return result

def initialize():
    check_ffmpeg_ffprobe()
    check_shaka_packager()
