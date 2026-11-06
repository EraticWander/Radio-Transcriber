from radio import RadioListener
import schedule
import multiprocessing

# Find stream URLS
# https://provisioning.streamtheworld.com/pls/CHSUFMAAC.pls
def define_task(stream_url, listener_duration, temp_folder, whisper_model, transcribe_folder, contest, contest_url, monitor_word,
                time_list):
    """
    Defines a scheduled task to start a RadioListener instance at specified times.
    
    Args:
        stream_url (str): The URL of the radio stream to listen to.
        listener_duration (int): The duration in seconds for the radio listener to run.
        temp_folder (str): The temporary folder to store audio clips.
        whisper_model (str): The Whisper model to use for transcription.
        transcribe_folder (str): The folder to store transcribed text.
        contest (str): The name of the contest associated with this task.
        contest_url (str): The URL of the contest page.
        monitor_word (list[str]): A list of keywords to monitor for in the transcription.
        time_list (list[str]): A list of times in the format "HH:MM" when the task should be scheduled to run.
    
    Returns:
        None
    """
    try:
        radio = RadioListener(stream_url = stream_url,
                                listener_duration = listener_duration,
                                temp_folder = temp_folder,
                                whisper_model = whisper_model,
                                transcribe_folder = transcribe_folder,
                                contest = contest,
                                contest_url = contest_url,
                                monitor_word = monitor_word)
    except ValueError as e:
        return False
    radio_task = multiprocessing.Process(target=radio.listener_start)
    for i in time_list:
        schedule.every().monday.at(i).do(radio_task.start)
        schedule.every().tuesday.at(i).do(radio_task.start)
        schedule.every().wednesday.at(i).do(radio_task.start)
        schedule.every().thursday.at(i).do(radio_task.start)
        schedule.every().friday.at(i).do(radio_task.start)
    
    print (f"{contest} task has been scheduled for {time_list}")
    
            
# Destroy your debt
print ("Destroy Your Debt")
destroy_your_debt = define_task(stream_url= ["http://18423.live.streamtheworld.com:80/CHSUFMAAC_SC",
                                        "http://14623.live.streamtheworld.com:80/CHSUFMAAC_SC",
                                        "http://18423.live.streamtheworld.com:3690/CHSUFMAAC_SC",
                                        "http://14623.live.streamtheworld.com:3690/CHSUFMAAC_SC"
                                        ],
                           listener_duration=20 * 60,
                            temp_folder="/tmp/temp_audio_clips/dd",
                            whisper_model="turbo",
                            transcribe_folder = "transcribe_dd",
                            contest = "Destroy Your Debt",
                            contest_url = "https://campaign.aptivada.com/contest/1723374?js=true&parent=https%3A%2F%2Fwww.virginradio.ca%2Fkelowna%2Fcontests%2Fvirgin-radios-destroy-your-debt-kelowna.html&apt_widget_type=preview&apt_widget_action=default",
                            monitor_word = ["keyword", "key word"],
                            time_list = ["06:57", "08:57", "10:57", "12:57", "14:57", "16:57", "18:57"])

while True:
    schedule.run_pending()