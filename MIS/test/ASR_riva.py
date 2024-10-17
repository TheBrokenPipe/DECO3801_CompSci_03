import os
from time import monotonic
from pathlib import Path

import grpc
import riva.client
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    metadata = [["function-id", os.getenv("RIVA_FUNCTION")],
                ["authorization", "Bearer " + os.getenv("RIVA_API_KEY")]]
    auth = riva.client.Auth(None, True, "grpc.nvcf.nvidia.com:443", metadata)
    asr_service = riva.client.ASRService(auth)
    config = riva.client.RecognitionConfig()
    config.language_code = "en-US"
    config.max_alternatives = 1
    config.enable_automatic_punctuation = False
    config.audio_channel_count = 1
    p = Path("data/recordings/")
    base_path = Path("data/riva_transcripts/")
    os.makedirs(base_path, exist_ok=True)

    files = p.glob("*.wav")
    for file in files:
        with open(file, 'rb') as fh:
            data = fh.read()
        try:
            time = monotonic()
            response = asr_service.offline_recognize(data, config)
            duration = monotonic() - time
            print(f"Transcribed {file} in {duration:.3f}s")
            final_transcript = ""
            for result in response.results:
                final_transcript += result.alternatives[0].transcript

            transcript_file = base_path / (file.stem + "-riva.txt")
            with open(transcript_file, "w", encoding="utf-8") as file:
                file.write(final_transcript)
        except grpc.RpcError as e:
            print(e.details())


if __name__ == "__main__":
    main()
