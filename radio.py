import subprocess
import threading
import os
import numpy as np


from datetime import datetime

from discord import Webhook, RequestsWebhookAdapter, Embed, Color, File

import signal
import time
import glob
import whisper
import torch

import gc

# Get the current script's directory
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct the path to the submittal module
submittal_path = os.path.join(script_dir, 'submittal.py')

# Import the ContestEntryBot class from the submittal module
from importlib.machinery import SourceFileLoader
ContestEntryBot = SourceFileLoader('submittal', submittal_path).load_module().ContestEntryBot

class RadioListener:
    def __init__(self, temp_folder = "temp_audio_clips", listener_duration = (20 * 60), stream_url = "",
                 transcribe_folder = "transcribe", whisper_model = "base"):
        self.temp_folder = temp_folder
        self.transcribe_folder = transcribe_folder
        
        signal.signal(signal.SIGINT, self.signal_handler)
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(transcribe_folder, exist_ok=True)
        
        self.num_files_threshold = 3
        self.listener_duration = listener_duration
        self.shutdown_signal = False
        self.stream_url = stream_url
        self.whisper_model = whisper_model
        
    def signal_handler(self, signal, frame):
        print("Received signal to gracefully shut down.")
        self.shutdown_signal = True
        with torch.no_grad():
            torch.cuda.empty_cache()
        gc.collect()
        

    def webhook(self, msg, file_path=None):
        webhook_url = 'https://discord.com/api/webhooks/1197650847664980029/VlpzbKii8dBYb5slvOHP3Q1wJmvgGGu30YDiRZMchXW-sYHOtdTczchO02CNFCxsP1mZ'
        webhook = Webhook.from_url(webhook_url, adapter=RequestsWebhookAdapter())
    
        embed = Embed(title=msg['title'], description=msg['msg'], url=msg['url'], color=Color.blue())
    
        if file_path:
            with open(file_path, mode="rb") as f:
                audio_file = File(f)
            webhook.send(embed=embed, file=audio_file)
        else:
            webhook.send(embed=embed)

    def return_keyword(self, audio_trans):
        from openai import OpenAI
        print ("sending to chatgpt to find keyword")
        client = OpenAI(
            api_key= "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"
        )
        chat = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Find the keyword in this string: '{audio_trans}'",
                }
            ],
            model="gpt-3.5-turbo",
        )
        
        return chat.choices[0].message.content

        
    def find_keyword(self, transcribed_string, file):
        import re
        # Use regular expression to find the keyword
        matches = re.search(r'\b' + re.escape("keyword") + r'\b', transcribed_string, flags=re.IGNORECASE)

        # Check if the keyword is found
        if matches:
            print ("Match found")
            try:
                keyword = self.return_keyword(transcribed_string)
            except Exception as e:
                print (e)
                keyword = transcribed_string
            print (keyword)
            keyword = keyword.split('"')[1]
            share_url = self.contest_entry(keyword)
            print (share_url)
            
            if share_url != "FAILED":
                print ("sending discord message with share URL")
                found_msg = {
                        "title":"RadioListener Found Keyword",
                        "msg":keyword,
                        "url":share_url
                        } 
            else:
                print ("sending discord message without share URL")
                found_msg = {
                        "title":"RadioListener Found Keyword",
                        "msg":keyword,
                        "url":"https://www.iheartradio.ca/virginradio/kelowna/contests/virgin-radio-s-100-000-destroy-your-debt-1.21030390"
                        }
                self.webhook(found_msg, file_path=file)

    
    def contest_entry(self, keyword):
        bot = ContestEntryBot()
        bot.enter_contest(keyword)
        share_url = bot.get_share_url()
        return share_url
            
    def transcribe_audio_file(self, audio_file_path):
        print(f"Transcribing {audio_file_path}...")
        # Check if the file exists
        if not os.path.exists(audio_file_path):
            print(f"Error: File {audio_file_path} does not exist.")
            return

        try:
            self.model = whisper.load_model(self.whisper_model)
            result = self.model.transcribe(audio_file_path)
            
            search_thread = threading.Thread(target=self.find_keyword, args=(result['text'],audio_file_path))
            search_thread.start()
            # Append inferred text to the output text file
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output_text_file = f"{self.transcribe_folder}/Transcribed Audio.txt"
            with open(output_text_file, 'a') as text_file:
                text_file.write(f"{timestamp}: {result['text']}\n")
                
            search_thread.join()
            # Delete the audio file
            os.remove(audio_file_path)
            print(f"Transcription complete. Audio file deleted.")
        except Exception as e:
            print(f"Error: {e}")

    # Function to monitor and transcribe audio clips
    def monitor_and_transcribe(self):
        start_time = time.time()

        while not self.shutdown_signal:
            elapsed_time = time.time() - start_time
            print (f"elapsed time: {elapsed_time}", end="\r")

            if elapsed_time >= self.listener_duration:
                print(f"Listener has been running for {self.listener_duration} seconds. Stopping.")
                self.shutdown_signal = True
                break

            files = glob.glob(os.path.join(self.temp_folder, "*.wav"))

            if len(files) >= self.num_files_threshold:
                files.sort(key=os.path.getmtime)

                oldest_file = files[0]
                print(oldest_file)
                self.transcribe_audio_file(oldest_file)

                time.sleep(5)
                
    def remove_all_files_in_folder(self):
        # Get the list of files in the folder
        files = os.listdir(self.temp_folder)

        # Iterate over the list and remove each file
        for file in files:
            file_path = os.path.join(self.temp_folder, file)
            try:
                if os.path.isfile(file_path):
                    self.transcribe_audio_file(file_path)
                    os.remove(file_path)
                    print(f"File removed: {file_path}")
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")
        with torch.no_grad():
            torch.cuda.empty_cache()
        gc.collect()

    def download_clip(self):
        temp_file = os.path.join(self.temp_folder, "output_audio_%Y%m%d%H%M%S.wav")

        ffmpeg_command = [
            'ffmpeg',
            '-i', self.stream_url,
            '-f', 'wav',
            #'-ar', '16000',
            '-ac', '1',
            #'-af', 'volume=10,highpass=f=1000,lowpass=f=8000',
            '-acodec', 'pcm_s16le',  # Set audio codec to pcm_s16le
            '-f', 'segment',  # Specify the segment format
            '-segment_time', '00:01:00',
            '-strftime', '1',
            temp_file
        ]
        try:
            process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            while process.poll() is None and not self.shutdown_signal:
                pass
            print (f"shutdown signal {self.shutdown_signal}")
            process.terminate()
            print("Clip download process terminated forcefully.")
            
            # Optionally, you can capture and print the output
            # stdout, stderr = process.communicate()
            # print("STDOUT:", stdout.decode())
            # print("STDERR:", stderr.decode())
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        finally:
            if process:
                process.kill()
                print("Clip download process terminated.")
                
            if self.shutdown_signal:
                # Perform any cleanup or finalization steps here
                print("Graceful shutdown completed.")
                print ("transcoding and removing all remaining files")
                self.remove_all_files_in_folder()
                with torch.no_grad():
                    torch.cuda.empty_cache()
                gc.collect()
            else:
                print("Process completed without a shutdown signal.")

    def listener_start(self):
        start_msg = {
            "title":"RadioListener",
            "msg":"Radio Listener bot is starting to listen and transcribe",
            "url":""
        }
        #
        #self.webhook(start_msg)
        #
        download_thread = threading.Thread(target=self.download_clip, args=(), daemon=True)
        monitor_thread = threading.Thread(target=self.monitor_and_transcribe, args=(), daemon=True)
    
        # Start the download clip thread
        print (f"Starting downloading {self.stream_url} radio stream")
        download_thread.start()

        # Start the monitor and transcribe thread
        print("Starting folder monitor")
        monitor_thread.start()
    
        # for clean shutdown
        download_thread.join()
        monitor_thread.join()
        
        print ("Listener has shut down")
        print("Download thread is alive:", download_thread.is_alive())
        print("Monitor thread is alive:", monitor_thread.is_alive())
        self.shutdown_signal = False