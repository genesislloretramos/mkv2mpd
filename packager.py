import json
import os
import subprocess

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_stream_info(data_json, index):
    for stream in data_json['streams']:
        if stream['index'] == index:
            return stream
    return None

def create_packager_command(converted_json_path, data_json_path, output_directory):
    converted_json = load_json(converted_json_path)
    data_json = load_json(data_json_path)
    
    packager_command = [
        os.path.join(os.getcwd(), 'bin', 'packager-win-x64.exe'),  # Ensure this path is correct
        '--generate_static_live_mpd',
        '--mpd_output', os.path.join(output_directory, 'manifest.mpd')
    ]
    
    for stream in converted_json['streams']:
        stream_info = get_stream_info(data_json, stream['index'])
        if stream_info:
            input_file = stream['output_file']
            output_file = input_file.replace('uploads', 'output')
            name = stream_info['tags'].get('title', '')
            if name =="":
                name = stream_info['tags'].get('language', 'und')
            lang = stream_info['tags'].get('language', 'und')

            if stream_info['codec_type'] == 'audio':
                packager_command.append(
                    f'in={input_file},stream=audio,output={output_file},language={lang},dash_label={name}'
                )
            elif stream_info['codec_type'] == 'subtitle':
                packager_command.append(
                    f'in={input_file},stream=text,output={output_file},language={lang},dash_label={name}'
                )
            elif stream_info['codec_type'] == 'video':
                packager_command.append(
                    f'in={input_file},stream=video,output={output_file}'
                )
    
    return packager_command

def run_packager_command(packager_command):
    try:
        subprocess.run(packager_command, check=True)
        print("Packaging completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during packaging: {e}")

if __name__ == "__main__":
    converted_json_path = 'converted.json'
    data_json_path = 'data.json'
    output_directory = 'output'
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    packager_command = create_packager_command(converted_json_path, data_json_path, output_directory)
    run_packager_command(packager_command)
