import tkinter as tk
from tkinter import messagebox
import json
import os
import subprocess
import threading
import queue

def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as config_file:
            return json.load(config_file)
    else:
        return {}
    
def save_config():

    for script_name in script_processes:
        if script_processes[script_name] and script_processes[script_name].poll() is None:
            script_processes[script_name].terminate()
            status_labels[script_name].config(text='Offline', fg='red')
            if script_name == 'DiscordFunction':
                start_discord_button.config(text='Start Discord Bot')
            elif script_name == 'VoiceHook':
                start_voicehook_button.config(text='Start Voice Hook')
    config_data = {
        "bot_token": bot_token_entry.get(),
        "webhook_link": webhook_link_entry.get(),
        "weather_api": weather_link_entry.get(),
        "channel_webhook_transcribe": channel_webhook_transcribe_entry.get(),
        "identity": identity_entry.get("1.0", tk.END).strip(),
        "preferred_voice_channel": preferred_voice_channel_entry.get(),
        "preferred_text_channel": preferred_text_channel_entry.get(),
        "preferred_keybind": preferred_voice_command_keybind_entry.get(),
        "tts_enabled": tts_enabled_var.get(),  
    }
    if all([bot_token_entry.get(), webhook_link_entry.get()]):
        start_discord_button.config(state=tk.NORMAL)
        start_voicehook_button.config(state=tk.NORMAL)
    update_button_states()
    with open('config.json', 'w') as config_file:
        json.dump(config_data, config_file)
    if bot_token_entry.get():
        bot_token_entry.config(state=tk.DISABLED)
    if webhook_link_entry.get():
        webhook_link_entry.config(state=tk.DISABLED)
    if weather_link_entry.get():
        weather_link_entry.config(state=tk.DISABLED)
    messagebox.showinfo("Info", "Configuration saved successfully")

def clear_config(field):
    if field == "bot_token":
        bot_token_entry.delete(0, tk.END)
        bot_token_entry.config(state=tk.NORMAL)
    elif field == "webhook_link":
        webhook_link_entry.delete(0, tk.END)
        webhook_link_entry.config(state=tk.NORMAL)
    elif field == "weather_api":
        weather_link_entry.delete(0, tk.END)
        weather_link_entry.config(state=tk.NORMAL)
    elif field == "channel_webhook_transcribe":
        channel_webhook_transcribe_entry.delete(0, tk.END)
        channel_webhook_transcribe_entry.config(state=tk.NORMAL)
    elif field == "identity":
        identity_entry.delete("1.0", tk.END)
        identity_entry.config(state=tk.NORMAL)
    elif field == "preferred_voice_channel":
        preferred_voice_channel_entry.delete(0, tk.END)
        preferred_voice_channel_entry.config(state=tk.NORMAL)
    elif field == "preferred_text_channel":
        preferred_text_channel_entry.delete(0, tk.END)
        preferred_text_channel_entry.config(state=tk.NORMAL)
    elif field == "preferred_keybind":
        preferred_voice_command_keybind_entry.delete(0, tk.END)
        preferred_voice_command_keybind_entry.config(state=tk.NORMAL)
        set_keybind()
    # ... other fields as needed

def set_keybind(event=None):
    def on_key(event):
        # Capture the key press and display it in the entry widget
        preferred_voice_command_keybind_entry.delete(0, tk.END)
        preferred_voice_command_keybind_entry.insert(0, event.keysym)
        keybind_window.destroy()

    keybind_window = tk.Toplevel(app)
    keybind_window.title("Set Keybind")
    keybind_window.geometry("200x50")

    tk.Label(keybind_window, text="Press a key for voice command").pack()

    # Set the focus to the new window and grab all events
    keybind_window.focus_set()
    keybind_window.grab_set()

    keybind_window.bind("<Key>", on_key)


def redirect_output(text_widget, output_queue):
    """ Continuously update the text widget with script output. """
    while True:
        output = output_queue.get()
        if output is None:  # A None in the queue indicates the thread should stop
            break
        text_widget.insert(tk.END, output)
        text_widget.see(tk.END)

def toggle_script(script_name, button, output_queue):
    global script_processes
    venv_python = 'venv/Scripts/python.exe'
    if script_name not in script_processes or script_processes[script_name].poll() is not None:
        # Redirect output to a queue
        script_processes[script_name] = subprocess.Popen([venv_python, f'{script_name}.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        
        # Start a thread to read output from the subprocess and put it in the queue
        threading.Thread(target=lambda: [output_queue.put(line) for line in iter(script_processes[script_name].stdout.readline, '')], daemon=True).start()
        threading.Thread(target=lambda: [output_queue.put(line) for line in iter(script_processes[script_name].stderr.readline, '')], daemon=True).start()

        status_labels[script_name].config(text='Online', fg='green')
        button.config(text=f"Stop {script_name.replace('_', ' ').title()}")
    else:
        # Stop the script
        script_processes[script_name].terminate()
        status_labels[script_name].config(text='Offline', fg='red')
        button.config(text=f"Start {script_name.replace('_', ' ').title()}")

app = tk.Tk()
app.title("Bot Launcher")
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
app_width = screen_width // 2  # Half the screen width
app_height = screen_height  # Full screen height
app.geometry(f"{app_width}x{app_height}")
config = load_config()
script_processes = {}
status_labels = {}
app.columnconfigure(1, weight=1)  # Give expansion property to the second column
tts_enabled_var = tk.BooleanVar()

# Bot Token Field
tk.Label(app, text="Bot Token:").grid(row=0, column=0, sticky="w")
bot_token_entry = tk.Entry(app)
bot_token_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
tk.Button(app, text="Edit", command=lambda: clear_config("bot_token")).grid(row=0, column=2, padx=5, pady=5)

# Preferred Voice Command Keybind Field
tk.Label(app, text="Preferred Voice Command Keybind:").grid(row=1, column=0, sticky="w")
preferred_voice_command_keybind_entry = tk.Entry(app, width=10)
preferred_voice_command_keybind_entry.grid(row=1, column=1, sticky="w", padx=5)

# Edit Button for the Preferred Voice Command Keybind Field
edit_button = tk.Button(app, text="Edit", command=lambda: clear_config("preferred_keybind"))
# Placing the button in the same column but with an offset
edit_button.grid(row=1, column=1, sticky="w", padx=(60, 50))

# TTS Checkbox and Label
# Placing the label in the same column but with an offset
tk.Label(app, text="Enable TTS:").grid(row=1, column=1, sticky="w", padx=(100, 50))
tts_checkbox = tk.Checkbutton(app, variable=tts_enabled_var)
# Placing the checkbox in the same column but with an offset
tts_checkbox.grid(row=1, column=1, sticky="w", padx=(165, 130))


# Channel Webhook Transcribe Field
tk.Label(app, text="Channel Webhook For Transcription:").grid(row=2, column=0, sticky="w")
channel_webhook_transcribe_entry = tk.Entry(app)
channel_webhook_transcribe_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
tk.Button(app, text="Edit", command=lambda: clear_config("channel_webhook_transcribe")).grid(row=2, column=2, padx=5, pady=5)

# Webhook Link Field
tk.Label(app, text="Channel Webhook For Output:").grid(row=3, column=0, sticky="w")
webhook_link_entry = tk.Entry(app)
webhook_link_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
tk.Button(app, text="Edit", command=lambda: clear_config("webhook_link")).grid(row=3, column=2, padx=5, pady=5)

# Weather API Field
tk.Label(app, text="Weather API:").grid(row=4, column=0, sticky="w")
weather_link_entry = tk.Entry(app)
weather_link_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
tk.Button(app, text="Edit", command=lambda: clear_config("weather_api")).grid(row=4, column=2, padx=5, pady=5)

# Identity Field
tk.Label(app, text="Identity:").grid(row=5, column=0, sticky="nw", padx=5, pady=5)  # Align label to the north-west (top-left)
identity_entry = tk.Text(app, height=4, width=40)  # Specify the size of the Text widget
identity_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
tk.Button(app, text="Edit", command=lambda: clear_config("identity")).grid(row=5, column=2, padx=5, pady=5)

# Preferred Voice Channel Field
tk.Label(app, text="Preferred Voice Channel:").grid(row=6, column=0, sticky="w")
preferred_voice_channel_entry = tk.Entry(app)
preferred_voice_channel_entry.grid(row=6, column=1, sticky="ew", padx=5, pady=5)
tk.Button(app, text="Edit", command=lambda: clear_config("preferred_voice_channel")).grid(row=6, column=2, padx=5, pady=5)

# Preferred Text Channel Field
tk.Label(app, text="Preferred Text Channel:").grid(row=7, column=0, sticky="w")
preferred_text_channel_entry = tk.Entry(app)
preferred_text_channel_entry.grid(row=7, column=1, sticky="ew", padx=5, pady=5)
tk.Button(app, text="Edit", command=lambda: clear_config("preferred_text_channel")).grid(row=7, column=2, padx=5, pady=5)

# Start DiscordFunction.py Button and Status
start_discord_button = tk.Button(app, text="Start Discord Bot", command=lambda: toggle_script('DiscordFunction', start_discord_button, discord_output_queue), state=tk.DISABLED)
start_discord_button.grid(row=8, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
status_labels['DiscordFunction'] = tk.Label(app, text='Offline', fg='red')
status_labels['DiscordFunction'].grid(row=8, column=2)

# Start VoiceHook.py Button and Status
start_voicehook_button = tk.Button(app, text="Start Voice Hook", command=lambda: toggle_script('VoiceHook', start_voicehook_button, voicehook_output_queue), state=tk.DISABLED)
start_voicehook_button.grid(row=9, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
status_labels['VoiceHook'] = tk.Label(app, text='Offline', fg='red')
status_labels['VoiceHook'].grid(row=9, column=2)

tk.Button(app, text="Save Configuration", command=save_config).grid(row=10, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

# DiscordFunction Output
discord_output = tk.Text(app, height=10)  # Height set to 5 lines
discord_output.grid(row=11, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
discord_output_queue = queue.Queue()
# VoiceHook Output
voicehook_output = tk.Text(app, height=10)  # Height set to 5 lines, same as discord_output
voicehook_output.grid(row=12, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
voicehook_output_queue = queue.Queue()


def update_button_states():
    if all([bot_token_entry.get(), webhook_link_entry.get(), weather_link_entry.get()]):
        start_discord_button.config(state=tk.NORMAL)
        start_voicehook_button.config(state=tk.NORMAL)
    else:
        start_discord_button.config(state=tk.DISABLED)
        start_voicehook_button.config(state=tk.DISABLED)

# Fill the fields if data exists
if "bot_token" in config:
    bot_token_entry.insert(0, config["bot_token"])
    bot_token_entry.config(state=tk.DISABLED)
if "webhook_link" in config:
    webhook_link_entry.insert(0, config["webhook_link"])
    webhook_link_entry.config(state=tk.DISABLED)
if "weather_api" in config:
    weather_link_entry.insert(0, config["weather_api"])
    weather_link_entry.config(state=tk.DISABLED)
if "channel_webhook_transcribe" in config:
    channel_webhook_transcribe_entry.insert(0, config["channel_webhook_transcribe"])
    channel_webhook_transcribe_entry.config(state=tk.DISABLED)
if "identity" in config:
    identity_entry.insert("1.0", config["identity"])
    identity_entry.config(state=tk.DISABLED)
if "preferred_voice_channel" in config:
    preferred_voice_channel_entry.insert(0, config["preferred_voice_channel"])
    preferred_voice_channel_entry.config(state=tk.DISABLED)
if "preferred_text_channel" in config:
    preferred_text_channel_entry.insert(0, config["preferred_text_channel"])
    preferred_text_channel_entry.config(state=tk.DISABLED)
if "preferred_keybind" in config:
    preferred_voice_command_keybind_entry.insert(0, config["preferred_keybind"])
    preferred_voice_command_keybind_entry.config(state=tk.DISABLED)
if "tts_enabled" in config:
    tts_enabled_var.set(config["tts_enabled"])
else:
    tts_enabled_var.set(False)  # Default value if not specified in the config


update_button_states()
# Queue for handling output
output_queue = queue.Queue()

# Thread for updating terminal_output from output_queue
threading.Thread(target=redirect_output, args=(discord_output, discord_output_queue), daemon=True).start()
threading.Thread(target=redirect_output, args=(voicehook_output, voicehook_output_queue), daemon=True).start()

app.mainloop()
