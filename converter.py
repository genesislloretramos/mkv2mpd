import subprocess
import os
import json
import datetime
from PyQt5.QtCore import pyqtSignal, QObject

class Converter(QObject):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.total_tracks = 0

    def convert_track(self, file_path, track_index, codec_type, output_dir):
        output_file = os.path.join(output_dir, f"track_{track_index}")
        command = [
            os.path.join('bin', 'ffmpeg'),  # Specify the path to ffmpeg
            '-i', file_path,
            '-map', f'0:{track_index}'
        ]

        if codec_type == "video":
            output_file += ".mp4"  # Use .mp4 for compatibility with shaka-packager
            command.extend([
                '-c:v', 'libx264',  # Specify the video codec
                '-preset', 'fast',  # Preset for x264 encoding speed
                '-crf', '23',  # Quality setting for x264 (lower is better)
                '-pix_fmt', 'yuv420p',  # Ensure pixel format is correct
                '-profile:v', 'high',  # Profile for x264
                '-level:v', '4.0',  # Level for x264
                '-movflags', '+faststart',  # Ensure the output is streamable
                output_file
            ])
        elif codec_type == "audio":
            output_file += ".m4a"
            command.extend([
                '-c:a', 'aac',  # Specify the audio codec
                output_file
            ])
        elif codec_type == "subtitle":
            output_file += ".vtt"
            command.extend([
                '-c:s', 'webvtt',  # Specify the subtitle codec
                output_file
            ])
        else:
            self.log_signal.emit(f"Unsupported codec type: {codec_type}")
            return None

        try:
            subprocess.run(command, check=True)
            self.log_signal.emit(f"Track {track_index} converted successfully.")
            return output_file
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"Error converting track {track_index}: {e}")
            return None

    def generate_data_json(self, file_path):
        command = [
            os.path.join('bin', 'ffprobe'),  # Specify the path to ffprobe
            '-v', 'error',
            '-print_format', 'json',
            '-show_streams',
            '-show_format',
            file_path
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            with open('data.json', 'w') as f:
                f.write(result.stdout)
            self.log_signal.emit("data.json file generated successfully.")
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"Error generating data.json: {e}")
            return False
        return True

    def process_mkv_file(self, file_path):
        if not self.generate_data_json(file_path):
            return {"error": "Failed to generate data.json"}

        output_dir = os.path.join('uploads', datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        os.makedirs(output_dir, exist_ok=True)

        try:
            with open("data.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.log_signal.emit("Error: 'data.json' file not found.")
            return {"error": "'data.json' file not found"}

        converted_files = []
        self.total_tracks = len(data['streams'])

        for i, stream in enumerate(data['streams']):
            self.progress_signal.emit(int((i / self.total_tracks) * 100))
            track_index = stream['index']
            codec_type = stream['codec_type']
            if codec_type == "mjpeg" or codec_type == "ttf":
                self.log_signal.emit(f"Skipping MJPEG or TTF stream at index {track_index}.")
                continue
            converted_file = self.convert_track(file_path, track_index, codec_type, output_dir)
            if converted_file:
                converted_files.append({
                    "index": track_index,
                    "output_file": converted_file
                })

        converted_json_path = "converted.json"
        with open(converted_json_path, "w") as f:
            json.dump({"streams": converted_files}, f, indent=4)

        self.progress_signal.emit(100)

        # Ensure the file is created
        if not os.path.exists(converted_json_path):
            self.log_signal.emit("Error: 'converted.json' file not created.")
            return {"error": "'converted.json' file not created"}

        self.log_signal.emit("Conversion completed successfully.")
        return {"status": "success", "output_dir": output_dir}
