import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from time import monotonic

from backend.chunking import Chunks
# test
file_path = "data/transcripts/ES2002d.Mix-Headset_transcript.jsonl"
# file_path = "data/ES2002d.Mix-Headset_transcript.jsonl"
chunking = Chunks()
jsonl = chunking.load_jsonl_file(file_path)
merged = chunking.merge_speaker_lines(jsonl)
# with open("merged.txt", "w", encoding="utf-8") as merged_file:
#     for merge in merged:
#         merged_file.write(str(merge) + "\n")
# print("Merging done!")

for threshold in [0.5, 0.55, 0.6, 0.65]:
    time = monotonic()
    chunked = chunking.semantic_chunking(merged, file_path, threshold)
    duration = monotonic() - time
    print(f"Chunked at threshold {threshold:.2f} in {duration:.3f}s")
    chunks_path = f"chunks_{threshold:.2f}.txt"
    with open(chunks_path, "w", encoding="utf-8") as chunks_file:
        for doc in chunked:
            # docstr = str(doc).replace("\n", " ")
            chunks_file.write(str(doc) + "\n\n")
print("Chunking done!")
