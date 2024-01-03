# Discord Companion Bot

Full Write Up:
https://drive.google.com/file/d/125cyK3xAI4foVghxPTdsPzTwDH8AVd31/view?usp=sharing

## Description
This project consists of a Discord bot integrated with advanced voice command capabilities. It's designed to enhance user interaction within Discord channels by offering functionalities like playing songs, retrieving GPT 3.5 queries, and more, all controlled via text and voice commands.

## Components
1. **DiscordFunction.py**: Manages the Discord bot operations and hosting, with the bot residing in a channel to process various commands.
2. **VoiceHook.py**: Handles the voice command features, leveraging 3.5 GPT technology for advanced interaction.

## Features
- **Voice Commands**: Interact with the bot using voice commands.
- **Music Playback**: Play, pause, and queue songs directly within Discord.
- **Custom Commands**: Tailored commands for diverse interactions.
- **Advanced AI Interaction**: Utilizes GPT-3.5 for sophisticated responses and interactions.

## Setup
### Prerequisites
- Python 3.10
- Discord API Token
- Discord Channel Webhooks

### Installation
1. Clone the repository:
   ```
   git clone git@github.com:MaxOpper/Discord-Companion-Bot.git
   ```
2. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```
3. Setup your Discord API token and any other necessary configurations in the SetUp.py file.

### Running the Bot
1. Run DiscordFunction.py to start the Discord bot:
   ```
   python DiscordFunction.py
   ```
2. Run VoiceHook.py for enabling voice command features:
   ```
   python VoiceHook.py
   ```

## Usage
DiscordFunction.py and VoiceHook.py can run independently of one another, if the user doesn't need voice commands or is only utilizing voice commands without the channel features.

The !play command queries youtube, downloads a song, then plays it through the specified voice channel
The !ringo command queries GPT-3.5
