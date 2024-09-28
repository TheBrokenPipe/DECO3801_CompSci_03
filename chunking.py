import json
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.utils.math import cosine_similarity
from typing import List
from langchain_ollama import OllamaEmbeddings

from time import monotonic
# Chunking and Retrieving strategies
# 1. propositional chunking
# 2. semantic chunking
# 3. parent document retriever
# using some combination of 2 or 3 of these

class chunks:
    def __init__(self):
        # self.embeddings = OpenAIEmbeddings()
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
        )

    def get_embedding(self, text):
        # embedding = self.embeddings.embed_documents(["clustering: " + text])[0]
        embedding = self.embeddings.embed_documents([text])[0]
        return embedding

    def load_jsonl_file(self, file_path):
        """Load a JSONL file from the given file path and return its content as a string."""
        with open(file_path, 'r', encoding='utf-8') as file:
            jsonl_string = file.read()
        return jsonl_string

    def merge_speaker_lines(self, jsonl_string):
        # Parse the JSONL input into a list of dictionaries
        transcript_lines = []
        for line in jsonl_string.strip().split("\n"):
            transcript_lines.append(json.loads(line))

        # Combine consecutive lines by the same speaker
        merged_lines = []
        current_block = transcript_lines[0]  # Start with the first line

        for i in range(1, len(transcript_lines)):
            current_line = transcript_lines[i]
            if current_line['speaker'] == current_block['speaker']:
                current_block['text'] += " " + current_line['text']
                current_block['end_time'] = current_line['end_time']
            else:
                merged_lines.append(current_block)
                current_block = current_line

        merged_lines.append(current_block)
        merged_jsonl_string = "\n".join([json.dumps(line) for line in merged_lines])

        return merged_lines

    def semantic_chunking(self, merged_lines: List[dict], filename: str, threshold = 0.6) -> List[Document]:
        embeddings = [self.get_embedding(line['text']) for line in merged_lines]

        chunks = []
        current_chunk = []
        current_start_time = merged_lines[0]['start_time']

        for i in range(len(merged_lines)):
            current_chunk.append(merged_lines[i])

            # if len(merged_lines[i]['text'].split()) < 5:
            #     continue

            # Check if there is a next line to compare
            if i + 1 < len(merged_lines):
                # Calculate similarity between the combined current chunk and the next line
                combined_text = " ".join([line['text'] for line in current_chunk])
                combined_embedding = self.get_embedding(combined_text)  # Create embedding for combined text
                next_embedding = embeddings[i + 1]
                similarity = cosine_similarity([combined_embedding], [next_embedding])[0][0]

                # Threshold for creating a new chunk
                if similarity < threshold and len(merged_lines[i+1]['text'].split()) > 5:
                    end_time = merged_lines[i]['end_time']
                    chunk_text = "\n".join([f"{line['speaker']}: {line['text']}" for line in current_chunk])

                    # Create a LangChain document with metadata
                    doc = Document(
                        page_content=chunk_text,
                        metadata={
                            "start_time": current_start_time,
                            "end_time": end_time,
                            "filename": filename
                        }
                    )
                    chunks.append(doc)

                    # Start new chunk
                    current_chunk = []
                    current_start_time = merged_lines[i + 1]['start_time']

        # Add last chunk if exists
        if current_chunk:
            chunk_text = " ".join([f"{line['speaker']}: {line['text']}" for line in current_chunk])
            end_time = merged_lines[-1]['end_time']
            doc = Document(
                page_content=chunk_text,
                metadata={
                    "start_time": current_start_time,
                    "end_time": end_time,
                    "filename": filename
                }
            )
            chunks.append(doc)

        return chunks

# test
file_path = "./data/transcripts/ES2002d.Mix-Headset_transcript.jsonl"
chunking = chunks()
jsonl = chunking.load_jsonl_file(file_path)
merged = chunking.merge_speaker_lines(jsonl)
# with open("merged.txt", "w", encoding="utf-8") as merged_file:
#     for merge in merged:
#         merged_file.write(str(merge) + "\n")
# print("Merging done!")

for threshold in [0.5, 0.55, 0.6, 0.65]:
    time = monotonic()
    chunked = chunking.semantic_chunking(merged,file_path, threshold)
    duration = monotonic() - time
    print(f"Chunked at threshold {threshold:.2f} in {duration:.3f}s")
    with open(f"chunks_{threshold:.2f}.txt", "w", encoding="utf-8") as chunks_file:
        for doc in chunked:
            docstr = str(doc).replace("\n", " ")
            chunks_file.write(docstr + "\n")
print("Chunking done!")

# jsonl_input = load_jsonl_file(file_path)
# merged = merge_speaker_lines(jsonl_input)
# print(merged)