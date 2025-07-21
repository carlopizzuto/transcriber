#!/usr/bin/env python3
"""Command-line interface for the transcriber."""

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .transcriber import AudioTranscriber
from .formatter import OutputFormatter

# Suppress warnings for cleaner output
logging.getLogger("lightning").setLevel(logging.ERROR)
logging.getLogger("pytorch_lightning").setLevel(logging.ERROR)


def main():
    """Main function with command-line interface."""
    # Load environment variables from .env file in current directory or home
    load_dotenv()
    if Path.home().joinpath('.env').exists():
        load_dotenv(Path.home() / '.env')
    
    parser = argparse.ArgumentParser(
        description="Transcribe audio with speaker diarization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    transcribe meeting.wav
    transcribe interview.m4a --model large --min-speakers 2 --max-speakers 4
    transcribe podcast.mp3 --output my_transcript --output-dir ~/Documents

Requirements:
    - Set HUGGINGFACE_TOKEN in environment or .env file for speaker diarization
    - Install ffmpeg for audio format conversion: sudo pacman -S ffmpeg
        """
    )
    
    parser.add_argument(
        "audio_file",
        help="Path to audio file (supports MP3, WAV, M4A, etc.)"
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )
    parser.add_argument(
        "--min-speakers",
        type=int,
        default=2,
        help="Minimum number of speakers (default: 2)"
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        default=4,
        help="Maximum number of speakers (default: 4)"
    )
    parser.add_argument(
        "--output",
        help="Output file prefix (default: same as input file)"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--device",
        choices=["cuda", "cpu"],
        help="Force specific device (auto-detected by default)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file '{args.audio_file}' not found")
        return 1
    
    # Determine output directory and filename
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.output:
        output_file = output_dir / args.output
    else:
        input_path = Path(args.audio_file)
        output_file = output_dir / input_path.stem
    
    try:
        # Initialize transcriber
        transcriber = AudioTranscriber(
            model_size=args.model,
            device=args.device
        )
        
        # Perform transcription with diarization
        results = transcriber.transcribe(
            args.audio_file,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers
        )
        
        # Save results in multiple formats
        OutputFormatter.save_results(results, str(output_file))
        
        print("\nTranscription completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())