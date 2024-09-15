from openai import OpenAI
import torch
import whisperx
import gc
import tempfile
import json
import os
from pathlib import Path


class ASR:

    def __init__(self, open_ai_client: OpenAI):
        """Initialise an ASR instance using an OpenAI client."""
        self.asr = "OpenAI"
        self.open_ai_asr_model = "whisper-1"
        self.open_ai_client = open_ai_client

    def __init__(self, hf_token: str):
        """Initialise an ASR instance using WhisperX."""
        self.asr = "WhisperX"
        self.hf_token = hf_token
        self.cache_dir = ".cache"
        os.makedirs(self.cache_dir, exist_ok = True)

    def transcribe_audio_file(self, file_path: str) -> str:
        """Transcribe audio from file path."""
        if self.asr == "OpenAI":
            return self.transcribe_audio_file_openai(file_path)
        elif self.asr == "WhisperX":
            return self.transcribe_audio_file_whisperx(file_path)

    def transcribe_audio(self, audio_file):
        """Transcribe audio from data."""
        if self.asr == "OpenAI":
            return self.transcribe_audio_openai(audio_file)
        elif self.asr == "WhisperX":
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name
            return self.transcribe_audio_file_whisperx(tmp_file_path)

    def transcribe_audio_openai(self, audio_file):
        """Transcribe audio from data using OpenAI client."""
        return self.open_ai_client.audio.transcriptions.create(
            model=self.open_ai_asr_model,
            file=audio_file
        ).text

    def transcribe_audio_file_openai(self, file_path: str) -> str:
        """Transcribe audio from file path using OpenAI client."""
        with open(file_path, "rb") as audio_file:
            transcription = self.transcribe_audio(audio_file)
        return transcription

    def transcribe_audio_file_whisperx(self, file_path: str) -> str:
        """Create JSONL transcript with speaker diarization of audio from file path."""
        cache_file = self.cache_dir / (Path(file_path).stem + ".json")
        try:
            with open(cache_file, 'r') as file:
                diarized = json.load(file)
        except FileNotFoundError:
            diarized = self.transcribe_audio_file_whisperx_raw(file_path)
            with open(cache_file, "w", encoding="utf-8") as file:
                json.dump(diarized, file)

        transcript = self.transcript_to_jsonl(diarized)

        return transcript

    def transcribe_audio_file_whisperx_raw(self, file_path: str):
        """Create transcript with speaker diarization of audio from file path."""
        device = "cuda" if torch.cuda.is_available() else "cpu"
        audio = whisperx.load_audio(file_path)

        base_transcription = self.whisperx_transcribe(device, audio)

        aligned = self.whisperx_align(device, audio, base_transcription)

        diarized = self.whisperx_diarize(device, audio, aligned)

        return diarized

    def seg_to_jsonl(self, segment) -> str:
        """Format transcript segment as JSONL."""
        text = segment["text"].strip()
        start = segment["start"]
        end = segment["end"]
        speaker = "UNKNOWN_SPEAKER" if not "speaker" in segment else segment["speaker"]
        return f'{{"speaker":"{speaker}","start_time":{start},"end_time":{end},"text":"{text}"}}'

    def seg_to_txt(self, segment) -> str:
        """Format transcript segment as plain text."""
        text = segment["text"].strip()
        speaker = "UNKNOWN_SPEAKER" if not "speaker" in segment else segment["speaker"]
        return f'{speaker}: {text}'

    def transcript_to_jsonl(self, transcript):
        segments = (self.seg_to_jsonl(seg) for seg in transcript['segments'])
        return '\n'.join(segments)

    def jsonl_to_txt(self, jsonl: str) -> str:
        """Convert JSONL transcript to basic transcript with speaker labels."""
        segments = (json.loads(seg) for seg in jsonl.split('\n'))
        transcript = "\n".join(self.seg_to_txt(segment)
                               for segment in segments)
        return transcript

    def whisperx_transcribe(self, device, audio):
        batch_size = 8
        compute_type = "float16"
        model = whisperx.load_model(
            "distil-large-v3", device, compute_type=compute_type)
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
