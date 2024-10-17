import os
import pandas as pd
import json
from pathlib import Path

base_path = Path("data/whisper_v3_transcripts/")
os.makedirs(base_path, exist_ok=True)

p = Path("data/.cache-large-v3/")
files = p.glob("*.json")

dfs = []

for file in files:
    try:
        with open(file) as json_data:
            data = json.load(json_data)
        file_df = pd.DataFrame(data['word_segments'])
        file_df["meeting"] = file.stem[:7]
        dfs.append(file_df)
    except Exception as e:
        print(f"Failed to read {file} with exception {e}")

df = pd.concat(dfs)
df = df.sort_values(["meeting", "start"])
df = df.groupby("meeting")

for meeting, frame in df:
    words_series = frame["word"].dropna()
    words = words_series.str.cat(sep=" ")
    with open(base_path / f"{meeting}-asr.txt", "w", encoding="utf-8") as f:
        f.write(words)
