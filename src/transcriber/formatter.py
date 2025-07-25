"""Output formatting for transcription results."""

import json
from pathlib import Path
from typing import Dict


class OutputFormatter:
    """Handles saving transcription results in multiple formats."""
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """Convert seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def format_srt_time(seconds: float) -> str:
        """Convert seconds to SRT subtitle format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    @classmethod
    def save_results(cls, results: Dict, output_file: str) -> None:
        """
        Save transcription results in JSON, TXT, and SRT formats.
        
        Args:
            results: Transcription results dictionary
            output_file: Base output filename (extension will be added)
        """
        output_path = Path(output_file)
        if output_path.suffix:
            output_path = output_path.with_suffix("")

        # Save JSON (detailed data)
        json_path = output_path.with_suffix(".json")
        cls._save_json(results, json_path)

        # Save readable text
        text_path = output_path.with_suffix(".txt")
        cls._save_text(results, text_path)

        # Save SRT subtitles
        srt_path = output_path.with_suffix(".srt")
        cls._save_srt(results, srt_path)

        print(f"\nResults saved:")
        print(f"  • {json_path} (detailed data)")
        print(f"  • {text_path} (readable format)")
        print(f"  • {srt_path} (subtitle format)")
    
    @staticmethod
    def _save_json(results: Dict, filename: str) -> None:
        """Save results as JSON."""
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def _save_text(cls, results: Dict, filename: str) -> None:
        """Save results as readable text."""
        with open(filename, "w", encoding='utf-8') as f:
            f.write(f"Language: {results['language']}\n")
            f.write("=" * 50 + "\n\n")
            
            current_speaker = None
            for segment in results['segments']:
                start_time = cls.format_time(segment["start"])
                end_time = cls.format_time(segment["end"])
                
                # Add speaker change indicator
                if segment['speaker'] != current_speaker:
                    if current_speaker is not None:
                        f.write("\n")
                    f.write(f"[{segment['speaker']}]\n")
                    current_speaker = segment['speaker']
                
                f.write(f"[{start_time} - {end_time}] {segment['text']}\n")
    
    @classmethod
    def _save_srt(cls, results: Dict, filename: str) -> None:
        """Save results as SRT subtitles."""
        with open(filename, "w", encoding='utf-8') as f:
            for i, segment in enumerate(results['segments'], 1):
                start_time = cls.format_srt_time(segment["start"])
                end_time = cls.format_srt_time(segment["end"])
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment['speaker']}: {segment['text']}\n\n")