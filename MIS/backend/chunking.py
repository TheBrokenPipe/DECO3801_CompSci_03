import os
import logging
import json
from typing import List
from time import monotonic

from langchain.docstore.document import Document
from langchain_community.utils.math import cosine_similarity
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from ..models import DB_Meeting
from math import exp


class Chunks:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        provider = os.getenv("CHUNKING_EMBED_PROVIDER", "ollama")
        if "OPENAI_API_KEY" in os.environ and provider == "openai":
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=500)
        else:
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

    def get_embedding(self, text):
        if isinstance(self.embeddings, OpenAIEmbeddings):
            embedding = self.embeddings.embed_documents([text])[0]
        else:
            text = "clustering: " + text
            embedding = self.embeddings.embed_documents([text])[0]
        return embedding

    def load_jsonl_file(self, file_path):
        """Load a JSONL file from the given file path as a string."""
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

        return merged_lines

    def get_batch_embedding(self, texts: List[str]):
        if isinstance(self.embeddings, OllamaEmbeddings):
            texts = ["clustering: " + t for t in texts]
        embedding = self.embeddings.embed_documents(texts)
        return embedding

    def get_text(self, chunk: List[dict]) -> List[str]:
        return [line['text'] for line in chunk]

    def get_chunk_text(self, chunk: List[dict]):
        lines = [f"{line['speaker']}: {line['text']}" for line in chunk]
        text = "\n".join(lines)
        return text

    @staticmethod
    def thresh_multiplier(lines, alpha=10, k=10):
        return 1 - (
            1 / (
                1 + exp(
                    -k*(
                        lines/(alpha**2) - 0.5
                    )
                )
            )
        )

    def semantic_chunking(self, merged_lines: List[dict], filename: str, threshold=0.6) -> List[Document]:
        original_threshold = threshold

        embeddings = self.get_batch_embedding(self.get_text(merged_lines))

        chunks = []
        current_chunk = []
        current_start_time = merged_lines[0]['start_time']

        for i in range(len(merged_lines)):
            current_chunk.append(merged_lines[i])

            # Check if there is a next line to compare
            if i + 1 < len(merged_lines):
                threshold = 1 - self.thresh_multiplier(len(current_chunk), 10) * (1 - original_threshold)
                print(threshold)
                # Calculate similarity between current chunk and next line
                combined_text = " ".join(self.get_text(current_chunk))
                # Create embedding for combined text
                combined_embedding = self.get_embedding(combined_text)
                next_embedding = embeddings[i + 1]
                similarity = cosine_similarity([combined_embedding],
                                               [next_embedding])[0][0]

                # Threshold for creating a new chunk
                next_line_len = len(merged_lines[i+1]['text'].split())
                if similarity < threshold and next_line_len > 5:
                    end_time = merged_lines[i]['end_time']
                    chunk_text = self.get_chunk_text(current_chunk)

                    # Create a LangChain document with metadata
                    doc = Document(
                        page_content=chunk_text,
                        metadata={
                            "chunk_id": len(chunks),
                            "start_time": current_start_time,
                            "end_time": end_time,
                            "filepath": filepath
                        }
                    )
                    chunks.append(doc)

                    # Start new chunk
                    current_chunk = []
                    current_start_time = merged_lines[i + 1]['start_time']

        # Add last chunk if exists
        if current_chunk:
            chunk_text = self.get_chunk_text(current_chunk)
            end_time = merged_lines[-1]['end_time']
            doc = Document(
                page_content=chunk_text,
                metadata={
                    "chunk_id": len(chunks),
                    "start_time": current_start_time,
                    "end_time": end_time,
                    "filepath": filepath
                }
            )
            chunks.append(doc)

        return chunks

    def chunk_transcript(self, meeting: DB_Meeting) -> List[Document]:
        file_path = meeting.file_transcript
        jsonl = self.load_jsonl_file(file_path)
        merged = self.merge_speaker_lines(jsonl)
        time = monotonic()
        chunks = self.semantic_chunking(merged, file_path, 0.3)
        duration = monotonic() - time
        self.logger.debug(f"Chunked {file_path} in {duration:.3f}s")
        return chunks
