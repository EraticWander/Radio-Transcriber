from radio import RadioListener
import schedule

radio_listener = RadioListener(stream_url= "http://19473.live.streamtheworld.com:80/CHSUFM_ADP_SC",
                               listener_duration=40 * 60,
                               temp_folder="/tmp/temp_audio_clips")
#radio_listener.listener_start()

time_list = ["06:55", "08:55", "10:55", "12:55", "14:55", "16:55", "18:55"]
for i in time_list:
    schedule.every().monday.at(i).do(radio_listener.listener_start)
    schedule.every().tuesday.at(i).do(radio_listener.listener_start)
    schedule.every().wednesday.at(i).do(radio_listener.listener_start)
    schedule.every().thursday.at(i).do(radio_listener.listener_start)
    schedule.every().friday.at(i).do(radio_listener.listener_start)
print ("Listener started")
while True:
    schedule.run_pending()

