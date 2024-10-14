import torch
import whisperx
import gc
import json
import logging
import os
from pathlib import Path
from time import monotonic


class ASR:

    def __init__(self, hf_token: str, cache_dir="data/.cache",
                 transcript_dir="data/transcripts"):
        """Initialise an ASR instance using WhisperX."""
        self.logger = logging.getLogger(__name__)

        # Hugging Face API token for speech diarization pipeline access
        self.hf_token = hf_token

        # Setup raw transcript cache directory if needed
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        # Setup transcript output directory if needed
        self.transcript_dir = transcript_dir
        os.makedirs(self.transcript_dir, exist_ok=True)

        # Utilise GPU acceleration with CUDA if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def transcribe_audio_file(self, file_path: str) -> str:
        """Save JSONL transcript with speaker diarization of audio."""
        # Use cache if available, else run transcription and cache result
        cache_file = Path(self.cache_dir) / (Path(file_path).stem + ".json")
        try:
            with open(cache_file, 'r', encoding="utf-8") as file:
                diarized = json.load(file)
        except FileNotFoundError:
            diarized = self.transcribe_audio_file_whisperx_raw(file_path)
            with open(cache_file, "w", encoding="utf-8") as file:
                json.dump(diarized, file)

        # Format transcript
        segments = (self.seg_to_jsonl(seg) for seg in diarized['segments'])
        transcript = '\n'.join(segments)

        # Save transcript
        transcript_file = (Path(file_path).stem + "_transcript.jsonl")
        transcript_path = Path(self.transcript_dir) / transcript_file
        with open(transcript_path, "w", encoding="utf-8") as jsonl_file:
            jsonl_file.write(transcript)

        return str(transcript_path)

    def transcribe_audio_file_whisperx_raw(self, file_path: str):
        """Create a transcript with speaker diarization of an audio file."""
        # Load audio file
        time = monotonic()
        audio = whisperx.load_audio(file_path)
        duration = monotonic() - time
        self.logger.debug(f"Loaded '{file_path}' in {duration:.3f}s")

        # Base transcription
        time = monotonic()
        base_transcription = self.whisperx_transcribe(audio)
        duration = monotonic() - time
        self.logger.debug(f"Transcribed '{file_path}' in {duration:.3f}s")

        # Transcript timestamp alignment
        time = monotonic()
        aligned = self.whisperx_align(audio, base_transcription)
        duration = monotonic() - time
        self.logger.debug(f"Aligned '{file_path}' in {duration:.3f}s")

        # Speech diarization
        time = monotonic()
        diarized = self.whisperx_diarize(audio, aligned)
        duration = monotonic() - time
        self.logger.debug(f"Diarized '{file_path}' in {duration:.3f}s")

        return diarized

    def seg_to_jsonl(self, segment) -> str:
        """Format transcript segment as JSONL."""
        # Extract components
        text = segment["text"].strip()
        start = segment["start"]
        end = segment["end"]

        # Label if speaker is identified or unknown
        if "speaker" in segment:
            speaker = segment["speaker"]
        else:
            speaker = "UNKNOWN_SPEAKER"

        # Format timing and create JSONL
        timing = f'"start_time":{start},"end_time":{end}'
        jsonl = f'{{"speaker":"{speaker}",{timing},"text":"{text}"}}'

        return jsonl

    def whisperx_transcribe(self, audio):
        """Run basic transcription of audio."""
        model_size = os.getenv("WHISPER_MODEL", "distil-large-v3")

        if self.device == "cuda":
            # Setup for CUDA acceleration
            batch_size = 6
            compute_type = "float16"
            model = whisperx.load_model(model_size, self.device,
                                        compute_type=compute_type)
        else:
            # Setup for CPU inference
            threads = os.cpu_count()
            batch_size = 8
            compute_type = "int8"
            torch.set_num_threads(threads)
            model = whisperx.load_model(model_size, self.device,
                                        compute_type=compute_type,
                                        threads=threads)

        # Run transcription inference
        result = model.transcribe(audio, batch_size=batch_size)

        # Cleanup model and free memory
        del model
        gc.collect()
        torch.cuda.empty_cache()

        return result

    def whisperx_align(self, audio, transcription):
        """Align transcription timestamps to audio."""
        # Setup model based on device and transcript language
        model, metadata = whisperx.load_align_model(
            language_code=transcription["language"],
            device=self.device)

        # Run alignment inference
        result = whisperx.align(
            transcription["segments"], model, metadata, audio, self.device)

        # Cleanup model and free memory
        del model
        gc.collect()
        torch.cuda.empty_cache()

        return result

    def whisperx_diarize(self, audio, aligned):
        # Setup diarization pipeline
        model = whisperx.DiarizationPipeline(
            use_auth_token=self.hf_token,
            device=self.device)

        # Run diarization inference
        diarize_segments = model(audio)

        # Assign speakers to transcript segments
        result = whisperx.assign_word_speakers(diarize_segments, aligned)

        # Cleanup model and free memory
        del model
        gc.collect()
        torch.cuda.empty_cache()

        return result
