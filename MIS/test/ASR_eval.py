from pathlib import Path
import pandas as pd
import jiwer
from collections import defaultdict
from whisper_normalizer.english import EnglishTextNormalizer
from whisper_normalizer.basic import BasicTextNormalizer

paths = {
    "ami": Path("data/ami_transcripts/"),
    "distil-whisper": Path("data/whisper_transcripts/"),
    "whisper": Path("data/whisper_v3_transcripts/"),
    "riva": Path("data/riva_transcripts/"),
}

transcripts = defaultdict(list)

for name, path in paths.items():
    files = path.glob("*.txt")
    for file in files:
        transcripts[file.stem[:7]].append({
            "type": name,
            "path": file
        })

print(f"Transcripts: {len(transcripts)}")

english_normalizer = EnglishTextNormalizer()
normalizer = BasicTextNormalizer()

metrics = []


def metric(meeting, asr, metric, value):
    return {"meeting": meeting, "ASR": asr,
            "metric": metric, "value": value}


for meeting, files in transcripts.items():
    if not len(files) == 4:
        continue

    ami_transcript = ""
    whisper_transcript = ""
    riva_transcript = ""
    distil_whisper_transcript = ""

    for file in files:
        with open(file["path"], encoding="utf-8") as f:
            transcript = f.read()
            transcript = english_normalizer(transcript)

        if file["type"] == "ami":
            ami_transcript = transcript
        elif file["type"] == "whisper":
            whisper_transcript = transcript
        elif file["type"] == "riva":
            riva_transcript = transcript
        elif file["type"] == "distil-whisper":
            distil_whisper_transcript = transcript

    whisper_out = jiwer.process_words(ami_transcript, whisper_transcript)
    distil_whisper_out = jiwer.process_words(ami_transcript, distil_whisper_transcript)
    riva_out = jiwer.process_words(ami_transcript, riva_transcript)

    metrics.extend([
        metric(meeting, "riva", "wer", riva_out.wer),
        metric(meeting, "riva", "mer", riva_out.mer),
        metric(meeting, "riva", "wil", riva_out.wil),
        metric(meeting, "whisper", "wer", whisper_out.wer),
        metric(meeting, "whisper", "mer", whisper_out.mer),
        metric(meeting, "whisper", "wil", whisper_out.wil),
        metric(meeting, "distil-whisper", "wer", distil_whisper_out.wer),
        metric(meeting, "distil-whisper", "mer", distil_whisper_out.mer),
        metric(meeting, "distil-whisper", "wil", distil_whisper_out.wil),
    ])

df = pd.DataFrame(metrics)
df.to_csv("asr_eval.csv")
