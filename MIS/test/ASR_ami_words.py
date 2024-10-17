import os
import pandas as pd
from pathlib import Path

base_path = Path("data/ami_transcripts/")
os.makedirs(base_path, exist_ok=True)

p = Path("data/ami_public_manual_1.6.2/words")
files = p.glob("*.xml")

dfs = []

for file in files:
    try:
        file_df = pd.read_xml(file)
        dfs.append(file_df)
    except Exception:
        print(f"Failed to read {file}")

df = pd.concat(dfs)
df["meeting"] = df.id.str[:7]
df = df.sort_values(["meeting", "starttime"])
df = df.groupby("meeting")

for meeting, frame in df:
    frame = frame[frame["punc"].isnull()]
    words_series = frame["w"].dropna()
    words = words_series.str.cat(sep=" ")
    with open(base_path / f"{meeting}.txt", "w", encoding="utf-8") as f:
        f.write(words)
