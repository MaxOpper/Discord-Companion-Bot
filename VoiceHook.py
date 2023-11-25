from pynput.keyboard import Key, Listener
import requests
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import re
import g4f
import threading
import numpy as np
import json

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
IDENTITY = config.get('identity')
DISCORD_CHANNEL_WEBHOOK_TRANSCRIBE = config.get('channel_webhook_transcribe')
DISCORD_CHANNEL_WEBHOOK_OUTPUT = config.get('webhook_link')
PREFERRED_KEYBRIND = config.get('preferred_keybind', 'F6')  # Default to 'F6' if not set
SAMPLE_RATE = 44100
FILENAME = "recording.wav"
model = whisper.load_model("base.en")
is_recording = False

print(f"Voice script activated, Press {PREFERRED_KEYBRIND} to use:", flush=True)
def prepend_exclamation(match):
    return f"!{match.group()}"

def transcribe_audio():
    # Transcribe the audio file using Whisper
    result = model.transcribe(FILENAME)
    text = result["text"]
    print("Transcribed text: " + text, flush=True)
    return text

def record_audio():
    global is_recording, record_thread
    def recording_thread():
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=2) as stream:
            audio_data = []
            while is_recording:
                data, overflowed = stream.read(SAMPLE_RATE)  # Read one second of audio data
                if overflowed:
                    print("Warning: Audio buffer overflowed",flush=True)
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
    try:
        if hasattr(key, 'char'):
            key_char = key.char.upper()  # Convert to uppercase if it's a character key
        else:
            key_char = key.name.upper()  # Convert to uppercase for special keys like F6

        if key_char == PREFERRED_KEYBRIND and not is_recording:
            print(f"{PREFERRED_KEYBRIND} pressed, starting recording...", flush=True)
            record_audio()
    except AttributeError:
        pass  # Handle attribute errors if any
    

def on_release(key):
    try:
        if hasattr(key, 'char'):
            key_char = key.char.upper()  # Convert to uppercase if it's a character key
        else:
            key_char = key.name.upper()  # Convert to uppercase for special keys like F6

        if key_char == PREFERRED_KEYBRIND:
            print(f"{PREFERRED_KEYBRIND} released, stopping recording...", flush=True)
            stop_recording()
            text = transcribe_audio()
            text = re.sub(r"\breplay\b|\bskip\b|\bplay\b|\bweather\b|\bweather\b|\bqueue\b|\bclear\b", prepend_exclamation, text)
            if text:
                send_to_discord(text, DISCORD_CHANNEL_WEBHOOK_TRANSCRIBE, False)
            if any(keyword in text for keyword in ["!play", "!skip", "!replay", "!weather", "!forecast", "!weather", "!queue", "!clear"]):
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
    except AttributeError:
        pass  # Handle attribute errors if any

def send_to_discord(text, hook, ringo):
    # Send the text to Discord
    if ringo == True:
        data = {"color": "feff01",
                "content": text}
    else:
        data = {"content": text}
    response = requests.post(hook, json=data)
    print(f"Response from Discord: {response.text}", flush=True)

# Start listening for key press events
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
