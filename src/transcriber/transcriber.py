#!/usr/bin/env python3
"""
Audio Transcription with Speaker Diarization

A comprehensive tool for transcribing audio files with speaker identification.
Uses OpenAI Whisper for transcription and pyannote.audio for speaker diarization.

Requirements:
    - ffmpeg (for audio conversion)
    - CUDA-capable GPU (optional, but recommended for speed)
    - HuggingFace token for pyannote models

Author: Transcription Tool
"""

import os
import subprocess
import tempfile
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import whisper
from pyannote.audio import Pipeline

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")


class AudioTranscriber:
    """Main transcription class with speaker diarization capabilities."""
    
    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Device to use ('cuda' or 'cpu'). Auto-detected if None.
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_size = model_size
        self.whisper_model = None
        self.diarization_pipeline = None
        
        print(f"Using device: {self.device}")
    
    def _load_whisper_model(self) -> None:
        """Load the Whisper model for transcription."""
        if self.whisper_model is None:
            print(f"Loading Whisper model ({self.model_size})...")
            self.whisper_model = whisper.load_model(self.model_size, device=self.device)
    
    def _load_diarization_pipeline(self) -> bool:
        """
        Load the pyannote diarization pipeline.
        
        Returns:
            bool: True if successfully loaded, False otherwise.
        """
        if self.diarization_pipeline is not None:
            return True
        
        print("Loading speaker diarization pipeline...")
        
        # Get HuggingFace token
        hf_token = os.getenv('HUGGINGFACE_TOKEN')
        if not hf_token:
            print("Warning: No HUGGINGFACE_TOKEN found in environment variables or .env file.")
            print("Speaker diarization requires authentication. Add your token to .env file:")
            print("HUGGINGFACE_TOKEN=your_token_here")
            return False
        
        try:
            # Try latest version first
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
        except Exception as e:
            print(f"Failed to load speaker-diarization-3.1: {e}")
            try:
                # Fallback to older version
                print("Trying older diarization model...")
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization",
                    use_auth_token=hf_token
                )
            except Exception as e2:
                print(f"Failed to load diarization pipeline: {e2}")
                return False
        
        # Move to GPU if available
        if self.device == "cuda":
            print("Moving diarization pipeline to GPU...")
            self.diarization_pipeline = self.diarization_pipeline.to(torch.device("cuda"))
        
        return True
    
    def _convert_audio_format(self, audio_file: str) -> Tuple[str, bool]:
        """
        Convert audio to WAV format if needed for diarization compatibility.
        
        Args:
            audio_file: Path to the input audio file
            
        Returns:
            Tuple of (converted_file_path, is_temporary_file)
        """
        file_ext = Path(audio_file).suffix.lower()
        
        # Return original file if already WAV
        if file_ext == '.wav':
            return audio_file, False
        
        # Create temporary WAV file
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav.close()
        
        print(f"Converting {file_ext} to WAV for diarization...")
        
        try:
            subprocess.run([
                'ffmpeg', '-i', audio_file,
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',          # 16kHz sample rate
                '-ac', '1',              # Mono
                '-y',                    # Overwrite output
                temp_wav.name
            ], check=True, capture_output=True, text=True)
            
            return temp_wav.name, True
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Audio conversion failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found. Install with: sudo pacman -S ffmpeg")
    
    def transcribe(self, audio_file: str, min_speakers: int = 2, max_speakers: int = 4) -> Dict:
        """
        Transcribe audio file with speaker diarization.
        
        Args:
            audio_file: Path to audio file
            min_speakers: Minimum number of speakers expected
            max_speakers: Maximum number of speakers expected
            
        Returns:
            Dictionary containing transcription results with speaker labels
        """
        print(f"Processing: {audio_file}")
        print(f"Expected speakers: {min_speakers}-{max_speakers}")
        
        # Load Whisper model
        self._load_whisper_model()
        
        # Transcribe audio
        print("Transcribing audio...")
        result = self.whisper_model.transcribe(audio_file, verbose=False)
        print(f"Language detected: {result['language']}")
        
        # Attempt speaker diarization
        diarization_available = self._load_diarization_pipeline()
        
        if diarization_available:
            # Convert audio format if needed
            diarization_audio, is_temp = self._convert_audio_format(audio_file)
            
            try:
                print("Performing speaker diarization...")
                diarization = self.diarization_pipeline(
                    diarization_audio,
                    min_speakers=min_speakers,
                    max_speakers=max_speakers
                )
                
                # Combine transcription with diarization
                print("Combining transcription with speaker labels...")
                final_segments = self._combine_transcription_and_diarization(
                    result["segments"], diarization
                )
                
            finally:
                # Clean up temporary file
                if is_temp and os.path.exists(diarization_audio):
                    os.unlink(diarization_audio)
        else:
            # Use transcription without diarization
            print("Using transcription without speaker diarization...")
            final_segments = [
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "speaker": "SPEAKER_1"
                }
                for segment in result["segments"]
            ]
        
        return {
            "language": result["language"],
            "segments": final_segments
        }
    
    def _combine_transcription_and_diarization(self, segments: List[Dict], diarization) -> List[Dict]:
        """Combine Whisper transcription with pyannote diarization results."""
        final_segments = []
        
        for segment in segments:
            segment_start = segment["start"]
            segment_end = segment["end"]
            segment_mid = (segment_start + segment_end) / 2
            
            # Find speaker at segment midpoint
            speaker = "UNKNOWN"
            for turn, _, speaker_label in diarization.itertracks(yield_label=True):
                if turn.start <= segment_mid <= turn.end:
                    speaker = speaker_label
                    break
            
            final_segments.append({
                "start": segment_start,
                "end": segment_end,
                "text": segment["text"].strip(),
                "speaker": speaker
            })
        
        return final_segments