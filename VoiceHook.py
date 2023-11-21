from pynput.keyboard import Key, Listener
import requests
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import re
import g4f
import threading
import numpy as np
from SetUp import DISCORD_CHANNEL_WEBHOOK_TRANSCRIBE, DISCORD_CHANNEL_WEBHOOK_OUTPUT, IDENTITY
RECORD_SECONDS = 5
SAMPLE_RATE = 44100
FILENAME = "recording.wav"
model = whisper.load_model("base")
is_recording = False


def prepend_exclamation(match):
    return f"!{match.group()}"

def transcribe_audio():
    # Transcribe the audio file using Whisper
    result = model.transcribe(FILENAME)
    text = result["text"]
    print("Transcribed text: " + text)
    return text

def record_audio():
    global is_recording, record_thread
    def recording_thread():
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=2) as stream:
            audio_data = []
            while is_recording:
                data, overflowed = stream.read(SAMPLE_RATE)  # Read one second of audio data
                if overflowed:
                    print("Warning: Audio buffer overflowed")
                audio_data.append(data)
            recording = np.concatenate(audio_data, axis=0)
            write(FILENAME, SAMPLE_RATE, recording)  # Save the recording

    is_recording = True
    record_thread = threading.Thread(target=recording_thread)
    record_thread.start()

def stop_recording():
    global is_recording
    is_recording = False
    record_thread.join()

# Function to execute when a key is pressed
def on_press(key):
    global is_recording
    if key == Key.insert:  # Replace with your key of choice
        # Send a post request to the Discord webhook URL to trigger the bot command
        requests.post(DISCORD_CHANNEL_WEBHOOK_TRANSCRIBE, json={"content": "!replay"})
    if key == Key.home:
        requests.post(DISCORD_CHANNEL_WEBHOOK_TRANSCRIBE, json={"content": "!skip"})
    if key == Key.f6 and not is_recording:
        print("F6 pressed, starting recording...")
        record_audio()
    

def on_release(key):

    if key == Key.f6:
        print("DONE")
        stop_recording()
        text = transcribe_audio()
        text = re.sub(r"\breplay\b|\bskip\b|\bplay\b", prepend_exclamation, text)
        if text:
            send_to_discord(text, DISCORD_CHANNEL_WEBHOOK_TRANSCRIBE, False)
        if "!play" or "!skip" or "!replay" or "!weather" or "!forecast" in text:
            return

        res = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": IDENTITY + " Current Prompt: " + text}],
            proxy="http://host:port",
            # or socks5://user:pass@host:port
            timeout=120,  # in secs
        )


        if len(res) > 2000:
            split_point = res[:2000].rfind(" ")
            first_part = res[:split_point]
            second_part = res[split_point:]
            send_to_discord(first_part, DISCORD_CHANNEL_WEBHOOK_OUTPUT)
            send_to_discord(second_part, DISCORD_CHANNEL_WEBHOOK_OUTPUT)
        else:
            res = res + " :pear:"
            send_to_discord(res, DISCORD_CHANNEL_WEBHOOK_OUTPUT, True)
        pass

def send_to_discord(text, hook, ringo):
    # Send the text to Discord
    if ringo == True:
        data = {"color": "feff01",
                "content": text}
    else:
        data = {"content": text}
    response = requests.post(hook, json=data)
    print(f"Response from Discord: {response.text}")

# Start listening for key press events
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
