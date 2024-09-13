from openai import OpenAI
import torch
import whisperx
import gc 
import tempfile
import json


class ASR:

    open_ai_asr_model = "whisper-1"

    def __init__(self, open_ai_client: OpenAI):
        self.asr = "OpenAI"
        self.open_ai_client = open_ai_client

    def __init__(self, hf_token: str):
        self.asr = "WhisperX"
        self.hf_token = hf_token

    def transcribe_audio_file(self, file_path: str) -> str:
        if self.asr == "OpenAI":
            return self.transcribe_audio_file_openai(file_path)
        elif self.asr == "WhisperX":
            return self.transcribe_audio_file_whisperx(file_path)

    def transcribe_audio(self, audio_file):
        if self.asr == "OpenAI":
            return self.transcribe_audio_openai(audio_file)
        elif self.asr == "WhisperX":
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name
            return self.transcribe_audio_file_whisperx(tmp_file_path)

    def transcribe_audio_openai(self, audio_file):
        return self.open_ai_client.audio.transcriptions.create(
            model=self.open_ai_asr_model,
            file=audio_file
        ).text

    def transcribe_audio_file_openai(self, file_path: str) -> str:
        """from path"""
        with open(file_path, "rb") as audio_file:
            transcription = self.transcribe_audio(audio_file)
        return transcription

    def transcribe_audio_file_whisperx(self, file_path: str) -> str:
        
        device = "cuda" if torch.cuda.is_available() else "cpu" 
        audio = whisperx.load_audio(file_path)

        base_transcription = self.whisperx_transcribe(device, audio)

        aligned = self.whisperx_align(device, audio, base_transcription)

        diarized = self.whisperx_diarize(device, audio, aligned)

        transcript = '\r\n'.join(self.format_jsonl(segment) for segment in diarized['segments'])

        return transcript
        
    def format_jsonl(self, segment) -> str:
        text = segment["text"].strip()
        start = segment["start"]
        end = segment["end"]
        speaker = "UNKNOWN_SPEAKER" if not "speaker" in segment else segment["speaker"]
        return f'{{"speaker":"{speaker}","start_time":{start},"end_time":{end},"text":"{text}"}}'


    def whisperx_transcribe(self, device, audio):
        batch_size = 8 
        compute_type = "float16" 
        model = whisperx.load_model("distil-large-v3", device, compute_type=compute_type)
        result = model.transcribe(audio, batch_size=batch_size)
        del model
        gc.collect()
        torch.cuda.empty_cache()
        return result
    

    def whisperx_align(self, device, audio, transcription):
        model, metadata = whisperx.load_align_model(language_code=transcription["language"], device=device)
        result = whisperx.align(transcription["segments"], model, metadata, audio, device, return_char_alignments=False)
        del model
        gc.collect()
        torch.cuda.empty_cache()
        return result
        

    def whisperx_diarize(self, device, audio, aligned):
        model = whisperx.DiarizationPipeline(use_auth_token=self.hf_token, device=device)
        diarize_segments = model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, aligned)
        del model
        gc.collect()
        torch.cuda.empty_cache()
        return result
        
