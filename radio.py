import subprocess
import threading
import os
from deepspeech import Model
import wave
import numpy as np

from datetime import datetime

from discord import Webhook, RequestsWebhookAdapter, Embed, Color

import signal
import time
import glob

shutdown_signal = False
num_files_threshold = 3

def signal_handler(signal, frame):
    global shutdown_signal
    print("Received signal to gracefully shut down.")
    shutdown_signal = True
                
def webhook(msg):
    webhook = Webhook.from_url('https://discord.com/api/webhooks/1069460895333371986/jVfdkcxuomx75XxBTcvKPqeRtLCG6ViZH2H0-iHNnGu1YRFl4Qr8eJ_lVR-iu6gm5UVn',
    adapter=RequestsWebhookAdapter())
    embed = Embed(title=msg['title'], description=msg['msg'], color=Color.blue())
    webhook.send(embed=embed)

def transcribe_audio_file(audio_file_path):
    model_path = "./deepspeech-0.9.3-models.pbmm"
    scorer_path = "./deepspeech-0.9.3-models.scorer"
    
    model = Model(model_path)
    model.enableExternalScorer(scorer_path)
    
    print(f"Transcribing {audio_file_path}...")

    # Check if the file exists
    if not os.path.exists(audio_file_path):
        print(f"Error: File {audio_file_path} does not exist.")
        return

    try:
        # Read audio file
        fin = wave.open(audio_file_path, 'rb')
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
        fin.close()

        # Perform inference
        infered_text = model.stt(audio)

        # Append inferred text to the output text file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_text_file = "transcribe/Transcribed Audio.txt"
        with open(output_text_file, 'a') as text_file:
            text_file.write(f"{timestamp}: {infered_text}\n")

        # Delete the audio file
        os.remove(audio_file_path)

        print(f"Transcription complete. Audio file deleted.")
    except Exception as e:
        print(f"Error: {e}")

# Function to monitor and transcribe audio clips
def monitor_and_transcribe(temp_folder):
    while not shutdown_signal:
        # Get the list of files in the temp folder
        files = glob.glob(os.path.join(temp_folder, "*.wav"))

        # Check if the number of files exceeds the threshold
        if len(files) >= num_files_threshold:
            # Sort files by modification time (oldest first)
            files.sort(key=os.path.getmtime)

            # Transcribe the oldest file
            oldest_file = files[0]
            transcribe_audio_file(oldest_file)

            # Sleep to avoid immediate re-triggering
            time.sleep(5)  # You can adjust this value as needed
            
def remove_all_files_in_folder(folder_path):
    # Get the list of files in the folder
    files = os.listdir(folder_path)

    # Iterate over the list and remove each file
    for file in files:
        file_path = os.path.join(folder_path, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"File removed: {file_path}")
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")

def download_clip(url, temp_folder):
    temp_file = os.path.join(temp_folder, "output_audio_%Y%m%d%H%M%S.wav")

    ffmpeg_command = [
        'ffmpeg',
        '-i', url,
        '-f', 'wav',
        '-ar', '16000',
        '-ac', '1',
        '-af', 'volume=10,highpass=f=1000,lowpass=f=8000',
        '-acodec', 'pcm_s16le',  # Set audio codec to pcm_s16le
        '-f', 'segment',  # Specify the segment format
        '-segment_time', '00:01:00',
        '-strftime', '1',
        temp_file
    ]
    try:
        process = subprocess.Popen(ffmpeg_command)
        # Wait for the process to finish or for a shutdown signal
        while process.poll() is None and not shutdown_signal:
            pass
        print("Clip download process terminated.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    finally:
        if process:
            process.terminate()
            process.wait()
        if shutdown_signal:
            # Perform any cleanup or finalization steps here
            print("Graceful shutdown completed.")
            remove_all_files_in_folder(temp_folder)
        else:
            print("Process completed without a shutdown signal.")

def listener_start():
    stream_url = "http://19473.live.streamtheworld.com:80/CHSUFM_ADP_SC"
    temp_folder = "temp_audio_clips"
    #clip_duration = 600
    signal.signal(signal.SIGINT, signal_handler)
    os.makedirs(temp_folder, exist_ok=True)
    os.makedirs("transcribe", exist_ok=True)
    start_msg = {
            "title":"RadioListener",
            "msg":"Radio Listener bot is starting to listen and transcribe",
            }
    webhook(start_msg)
    
    # Start the download clip thread
    download_thread = threading.Thread(target=download_clip, args=(stream_url, temp_folder,))
    download_thread.start()

    # Start the monitor and transcribe thread
    monitor_thread = threading.Thread(target=monitor_and_transcribe, args=(temp_folder,))
    monitor_thread.start()
    
    #for clean shutdown
    download_thread.join()
    monitor_thread.join()


if __name__ == "__main__":
    listener_start()