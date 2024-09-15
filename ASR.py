import torch
import whisperx
import gc
import json
import logging
import os
from pathlib import Path
from time import monotonic


class ASR:

    def __init__(self, hf_token: str):
        """Initialise an ASR instance using WhisperX."""
        self.hf_token = hf_token
        self.cache_dir = "data/.cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def transcribe_audio_file(self, file_path: str) -> str:
        """Create JSONL transcript with speaker diarization of audio from file path."""
        cache_file = Path(self.cache_dir) / (Path(file_path).stem + ".json")
        try:
            with open(cache_file, 'r') as file:
                diarized = json.load(file)
        except FileNotFoundError:
            diarized = self.transcribe_audio_file_whisperx_raw(file_path)
            with open(cache_file, "w", encoding="utf-8") as file:
                json.dump(diarized, file)

        segments = (self.seg_to_jsonl(seg) for seg in diarized['segments'])

        transcript = '\n'.join(segments)

        return transcript

    def transcribe_audio_file_whisperx_raw(self, file_path: str):
        """Create transcript with speaker diarization of audio from file path."""
        device = "cuda" if torch.cuda.is_available() else "cpu"

        time = monotonic()
        audio = whisperx.load_audio(file_path)
        duration = monotonic() - time
        self.logger.info("Loaded audio file in %.3fs - '%s'",
                         duration, file_path)

        time = monotonic()
        base_transcription = self.whisperx_transcribe(device, audio)
        duration = monotonic() - time
        self.logger.info("Transcribed audio file in %.3fs - '%s'",
                         duration, file_path)

        time = monotonic()
        aligned = self.whisperx_align(device, audio, base_transcription)
        duration = monotonic() - time
        self.logger.info("Aligned audio file in %.3fs - '%s'",
                         duration, file_path)

        time = monotonic()
        diarized = self.whisperx_diarize(device, audio, aligned)
        duration = monotonic() - time
        self.logger.info("Diarized audio file in %.3fs - '%s'",
                         duration, file_path)

        return diarized

    def seg_to_jsonl(self, segment) -> str:
        """Format transcript segment as JSONL."""
        text = segment["text"].strip()
        start = segment["start"]
        end = segment["end"]
        speaker = "UNKNOWN_SPEAKER" if not "speaker" in segment else segment["speaker"]
        return f'{{"speaker":"{speaker}","start_time":{start},"end_time":{end},"text":"{text}"}}'

    def whisperx_transcribe(self, device, audio):
        if device == "cuda":
            batch_size = 6
            compute_type = "float16"
            model = whisperx.load_model(
                "distil-large-v3", device, compute_type=compute_type)
        else:
            threads = os.cpu_count()
            batch_size = 8
            compute_type = "int8"
            torch.set_num_threads(threads)
            model = whisperx.load_model(
                "distil-large-v3", device, compute_type=compute_type, threads=threads)
        result = model.transcribe(audio, batch_size=batch_size)
        del model
        gc.collect()
        torch.cuda.empty_cache()
        return result

    def whisperx_align(self, device, audio, transcription):
        model, metadata = whisperx.load_align_model(
            language_code=transcription["language"],
            device=device)
        result = whisperx.align(
            transcription["segments"], model, metadata, audio, device)
        del model
        gc.collect()
        torch.cuda.empty_cache()
        return result

    def whisperx_diarize(self, device, audio, aligned):
        model = whisperx.DiarizationPipeline(
            use_auth_token=self.hf_token,
            device=device)

        diarize_segments = model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, aligned)
        del model
        gc.collect()
        torch.cuda.empty_cache()
        return result
