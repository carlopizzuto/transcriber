# Transcriber

Audio transcription with speaker diarization using OpenAI Whisper and pyannote.audio.

## Features

- **Multi-device support**: Automatically detects and uses the best available device:
  - **CUDA** (NVIDIA GPUs) - fastest for most workloads
  - **Apple Metal** (Apple Silicon Macs) - optimized for M1/M2/M3 chips
  - **CPU** - universal fallback
- **Speaker diarization**: Identifies different speakers in audio
- **Multiple audio formats**: Supports MP3, WAV, M4A, and more
- **Flexible output**: Multiple output formats available

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
# Basic usage (auto-detects best device)
transcribe meeting.wav

# Specify model and speakers
transcribe interview.m4a --model large --min-speakers 2 --max-speakers 4

# Custom output location
transcribe podcast.mp3 --output my_transcript --output-dir ~/Documents

# Force specific device
transcribe recording.wav --device mps     # Use Apple Metal (Mac)
transcribe recording.wav --device cuda    # Use NVIDIA CUDA
transcribe recording.wav --device cpu     # Use CPU only
```

## Requirements

- **ffmpeg** for audio conversion:
  - Linux: `sudo pacman -S ffmpeg` or `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/)
- **HUGGINGFACE_TOKEN** environment variable for speaker diarization

Set the token in a `.env` file in your home directory or current directory:
```
HUGGINGFACE_TOKEN=your_token_here
```