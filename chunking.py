import json
import openai
from langchain.docstore.document import Document
from sklearn.metrics.pairwise import cosine_similarity
from typing import List

# Chunking and Retrieving strategies
# 1. propositional chunking
# 2. semantic chunking
# 3. parent document retriever
# using some combination of 2 or 3 of these

openai.api_key = 'api-key'

def get_openai_embedding(text):
    response = openai.Embedding.create(
        input=[text],
        model="text-embedding-ada-002"  # You can change the model if needed
    )
    return response['data'][0]['embedding']

def load_jsonl_file(file_path):
    """Load a JSONL file from the given file path and return its content as a string."""
    with open(file_path, 'r', encoding='utf-8') as file:
        jsonl_string = file.read()
    return jsonl_string

def merge_speaker_lines(jsonl_string):
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

    return merged_jsonl_string

def semantic_chunking(merged_lines: List[dict], filename: str) -> List[Document]:
    # Calculate embeddings for each transcript line
    embeddings = []
    for line in merged_lines:
        text = line['text']
        embedding = get_openai_embedding(text)
        embeddings.append(embedding)

    # Group lines into semantically similar chunks
    chunks = []
    current_chunk = []
    current_start_time = merged_lines[0]['start_time']

    for i in range(1, len(merged_lines)):
        # Calculate similarity between current line and the last line in the chunk
        similarity = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]

        # Threshold for creating a new chunk
        if similarity < 0.85:  # Adjust this threshold based on needs
            end_time = merged_lines[i-1]['end_time']
            chunk_text = " ".join([f"{line['speaker']}: {line['text']}" for line in current_chunk])

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
            current_start_time = merged_lines[i]['start_time']

        current_chunk.append(merged_lines[i])

    # Add last chunk
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
file_path = "data/ES2002d.Mix-Headset_transcript.jsonl"
jsonl_input = load_jsonl_file(file_path)
merged = merge_speaker_lines(jsonl_input)
print(merged)