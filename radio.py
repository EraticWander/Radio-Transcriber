import subprocess
import threading
import os

from datetime import datetime

import requests
from discord import Webhook, SyncWebhook, Embed, Color, File

import signal
import time
import glob
import whisper
import torch

import gc

script_dir = os.path.dirname(os.path.realpath(__file__))
# add sumbittal.py to directory. this is so we can call ContestEneryBot
submittal_path = os.path.join(script_dir, 'submittal.py')

from importlib.machinery import SourceFileLoader
# import submittal.py using SourceFileLoader
ContestEntryBot = SourceFileLoader('submittal', submittal_path).load_module().ContestEntryBot

class RadioListener:
    """
    Class for handling radio stream monitoring, transcription, and keyword recognition.

    Args:
        temp_folder (str): Path to the folder where temporary audio clips are stored.
        listener_duration (int): Duration (in seconds) for which the radio listener should run.
        stream_url (str): URL of the radio stream.
        transcribe_folder (str): Path to the folder where transcriptions are stored.
        whisper_model (str): Name of the whisper model used for transcription.
        contest_url (str): URL of the radio contest.
        contest (str): Name of the radio contest.
        monitor_word (list[str]): List of keywords to monitor for in transcriptions.
    """
    def __init__(self, temp_folder:str = "temp_audio_clips", listener_duration:int = (20 * 60), stream_url:str = "",
                 transcribe_folder:str = "transcribe", whisper_model:str = "base", contest_url:str = "", contest:str = "",
                 monitor_word:list[str] = ["keyword", "key word"]):
        """
        Initializes the RadioListener object.

        Args:
            temp_folder (str): Path to the folder where temporary audio clips are stored.
            listener_duration (int): Duration (in seconds) for which the radio listener should run.
            stream_url (str): URL of the radio stream.
            transcribe_folder (str): Path to the folder where transcriptions are stored.
            whisper_model (str): Name of the whisper model used for transcription.
            contest_url (str): URL of the radio contest.
            contest (str): Name of the radio contest.
            monitor_word (list[str]): List of keywords to monitor for in transcriptions.
        """
        self.temp_folder = temp_folder
        self.transcribe_folder = transcribe_folder
        self.contest_url = contest_url
        self.contest = contest
        self.monitor_word = monitor_word
        
        signal.signal(signal.SIGINT, self.__signal_handler)
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(transcribe_folder, exist_ok=True)
        
        self.num_files_threshold = 3
        self.listener_duration = listener_duration
        self.shutdown_signal = False
        self.stream_url = stream_url
        self.current_stream = None
        self.whisper_model = whisper_model
        
        if not self.__stream_alive():
            stream_fail_msg = {
            "title":f"{self.contest} failed to start",
            "msg":f"Stream URL is no longer valid",
            "url":""
                }
                
            self.webhook(stream_fail_msg)
            raise ValueError(f"Stream is not reachable: {self.stream_url}")
            
        
    def __signal_handler(self, signal, frame):
        """
        Signal handler function to gracefully shut down the radio listener.

        Args:
            signal: The signal received.
            frame: The current stack frame.
        """
        print("Received signal to gracefully shut down.")
        self.shutdown_signal = True
        with torch.no_grad():
            torch.cuda.empty_cache()
        gc.collect()
        

    def webhook(self, msg, file_path=None):
        """
        Sends a message with an optional audio file to a Discord webhook.

        Args:
            msg (dict): Dictionary containing message details (title, msg, url).
            file_path (str): Path to the audio file to be sent. Default is None.
        """
        webhook = SyncWebhook.from_url('https://discord.com/api/webhooks/1197650847664980029/VlpzbKii8dBYb5slvOHP3Q1wJmvgGGu30YDiRZMchXW-sYHOtdTczchO02CNFCxsP1mZ')
    
        embed = Embed(title=msg['title'], description=msg['msg'], url=msg['url'], color=Color.blue())
    
        if file_path:
            with open(file_path, mode="rb") as f:
                audio_file = File(f)
            webhook.send(embed=embed, file=audio_file)
        else:
            webhook.send(embed=embed)
            
    def __stream_alive(self):
        try:
            response = requests.get(self.stream_url, stream=True, timeout=5)
            if response.status_code != 200:
                return False
            response.iter_content(chunk_size=1024)
            return True
        except requests.exceptions.RequestException:
            return False
        
    def __return_keyword(self, audio_trans):
        """
        Sends the audio transcription to ChatGPT and returns the identified keyword.

        Args:
            audio_trans (str): Transcription of the audio.

        Returns:
            str: Identified keyword.
        """
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

        
    def __find_keyword(self, transcribed_string, file):
        """
        Checks if any keyword from the monitor_word list is present in the transcription.

        Args:
            transcribed_string (str): Transcription of the audio.
            file (str): Path to the audio file.

        Side Effects:
            Sends a Discord message with the identified keyword and contest details.
        """
        print ("finding keyword")
        if any(phrase in transcribed_string.lower() for phrase in self.monitor_word):
            print ("Match found")
            try:
                keyword = self.__return_keyword(transcribed_string)
                print (keyword)
                keyword = keyword.split('"')[1]
            except Exception as e:
                print (e)
                keyword = transcribed_string
            print (keyword)
            
            # check if keyword returned is just "keyword"
            if "keyword" not in keyword or "key word" not in keyword:
                share_url = self.__contest_entry(keyword)
                print (share_url)
                
                if share_url != "FAILED":
                    print ("sending discord message with share URL")
                    found_msg = {
                            "title":f"Found Keyword for {self.contest}",
                            "msg":keyword,
                            "url":share_url
                            } 
                    self.webhook(found_msg, file_path=file)
                    self.shutdown_signal = True
                    
                else:
                    print ("sending discord message without share URL")
                    found_msg = {
                            "title":f"Found Keyword for {self.contest}",
                            "msg":keyword,
                            "url":self.contest_url
                            }
                    self.webhook(found_msg, file_path=file)
                
    def __contest_entry(self, keyword):
        """
        Enters the radio contest with the provided keyword and returns the share URL.

        Args:
            keyword (str): Keyword to enter the contest.

        Returns:
            str: Share URL of the entered contest.
        """
        bot = ContestEntryBot(contest_url = self.contest_url)
        bot.enter_contest(keyword)
        share_url = bot.get_share_url()
        return share_url
            
    def __transcribe_audio_file(self, audio_file_path):
        """
        Transcribes the audio file using the Whisper ASR model.

        Args:
            audio_file_path (str): Path to the audio file.

        Side Effects:
            Sends Discord messages with identified keywords and contest details.
            Appends transcriptions to the output text file.
            Deletes the transcribed audio file.
        """
        print(f"Transcribing {audio_file_path}...")
        # Check if the file exists
        if not os.path.exists(audio_file_path):
            print(f"Error: File {audio_file_path} does not exist.")
            return

        try:
            model = whisper.load_model(self.whisper_model)
            result = model.transcribe(audio_file_path, language="en",)
            
            search_thread = threading.Thread(target=self.__find_keyword, args=(result['text'],audio_file_path))
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
    def __monitor_and_transcribe(self):
        """
        Monitors the temporary folder for audio clips and transcribes them.
        Runs until the specified listener duration is reached or a shutdown signal is received.

        Side Effects:
            Calls __transcribe_audio_file for each audio clip.
            Removes all files in the temporary folder at the end.
        """
        start_time = time.time()

        while not self.shutdown_signal:
            elapsed_time = time.time() - start_time
            # print (f"elapsed time: {elapsed_time}", end="\r")

            if elapsed_time >= self.listener_duration:
                print(f"Listener has been running for {self.listener_duration} seconds. Stopping.")
                self.shutdown_signal = True
                break

            files = glob.glob(os.path.join(self.temp_folder, "*.wav"))

            if len(files) >= self.num_files_threshold:
                files.sort(key=os.path.getmtime)

                oldest_file = files[0]
                print(oldest_file)
                self.__transcribe_audio_file(oldest_file)

                time.sleep(5)
                
    def remove_all_files_in_folder(self):
        """
        Removes all files in the temporary folder.

        Side Effects:
            Calls __transcribe_audio_file for each file.
            Clears GPU memory and performs garbage collection.
        """
        # Get the list of files in the folder
        files = os.listdir(self.temp_folder)

        # Iterate over the list and remove each file
        for file in files:
            file_path = os.path.join(self.temp_folder, file)
            try:
                if os.path.isfile(file_path):
                    self.__transcribe_audio_file(file_path)
                    os.remove(file_path)
                    print(f"File removed: {file_path}")
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")
        with torch.no_grad():
            torch.cuda.empty_cache()
        gc.collect()
    
    def __stream_alive(self):
        for url in self.stream_url:
            try:
                response = requests.get(url, stream=True, timeout=5)
                if response.status_code == 200:
                    response.iter_content(chunk_size=1024)
                    self.current_stream = url  # Store the working URL
                    return True
            except requests.exceptions.RequestException:
                continue
        return False



    def __download_clip(self):
        """
        Downloads the radio stream and saves it as segmented audio clips.

        Side Effects:
            Calls __transcribe_audio_file for each downloaded clip.
            Cleans up resources upon shutdown signal.
        """
        temp_file = os.path.join(self.temp_folder, "output_audio_%Y%m%d%H%M%S.wav")

        ffmpeg_command = [
            'ffmpeg',
            '-i', self.current_stream,
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
        """
        Starts the radio listener by initiating the __download_clip and __monitor_and_transcribe threads.

        Side Effects:
            Sends Discord messages for the start and stop of the radio listener.
        """
        start_msg = {
            "title":f"{self.contest} listener has started (DEBUGGING)",
            "msg":f"Radio Listener bot is starting to listen and transcribe for {self.contest}",
            "url":""
        }
        
        # self.webhook(start_msg)
        
        download_thread = threading.Thread(target=self.__download_clip, args=(), daemon=True)
        monitor_thread = threading.Thread(target=self.__monitor_and_transcribe, args=(), daemon=True)
    
        # Start the download clip thread
        print (f"Starting task {self.contest}")
        print (f"Starting downloading {self.current_stream} radio stream")
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
        end_msg = {
            "title":f"{self.contest} listener has stopped (DEBUGGING)",
            "msg":f"Radio Listener bot has stopped",
            "url":""
        }
        #
        # self.webhook(end_msg)
        # 
        self.shutdown_signal = False

if __name__ == "__main__":
        radio = RadioListener(stream_url= ["http://18323.live.streamtheworld.com:3690/CHSUFM_SC","http://18423.live.streamtheworld.com:80/CHSUFMAAC_SC"],
                              listener_duration=20 * 60,
                              temp_folder="temp_audio_clips/dd",
                              whisper_model="base",
                              transcribe_folder = "transcribe_test",
                              contest = "5K A Day",
                              contest_url = "https://campaign.aptivada.com/contest/1698972?js=true&parent=https%3A%2F%2Fwww.virginradio.ca%2Fkelowna%2Fcontests%2Fvirgin-radios-5k-a-day-kelowna.html&apt_widget_type=preview&apt_widget_action=default",
                              monitor_word = ["keyword", "key word"]
        )
        
        radio.listener_start()
        