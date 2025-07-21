# Transcriber

Audio transcription with speaker diarization using OpenAI Whisper and pyannote.audio.

## Installation

Install using pipx for global CLI access:

```bash
pipx install .
```

For development (editable install):

```bash
pipx install -e .
```

## Usage

After installation, use the `transcribe` command from anywhere:

```bash
# Basic usage
transcribe meeting.wav

# Specify model and speakers
transcribe interview.m4a --model large --min-speakers 2 --max-speakers 4

# Custom output location
transcribe podcast.mp3 --output my_transcript --output-dir ~/Documents
```

## Requirements

- ffmpeg for audio conversion: `sudo pacman -S ffmpeg`
- HUGGINGFACE_TOKEN environment variable for speaker diarization

Set the token in a `.env` file in your home directory or current directory:
```
HUGGINGFACE_TOKEN=your_token_here
```