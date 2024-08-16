
class ASR:

    open_ai_asr_model = "whisper-1"

    def __init__(self, open_ai_client):
        self.open_ai_client = open_ai_client

    def transcribe_audio_file(self, file_path: str) -> str:
        """from path"""
        with open(file_path, "rb") as audio_file:
            transcription = self.open_ai_client.audio.transcriptions.create(
                model=self.open_ai_asr_model,
                file=audio_file
            )
        return transcription.text