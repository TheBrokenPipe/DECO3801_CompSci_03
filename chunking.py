import json
import openai
from langchain.docstore.document import Document
from sklearn.metrics.pairwise import cosine_similarity

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

def semantic_chunking(jsonl_string, filename):
    # Parse JSONL input
    transcript_lines = []
    for line in jsonl_string.strip().split("\n"):
        transcript_lines.append(json.loads(line))

    # Calculate embeddings for each transcript line
    embeddings = []
    for line in transcript_lines:
        text = line['text']
        embedding = get_openai_embedding(text)
        embeddings.append(embedding)

    # Group lines into semantically similar chunks
    chunks = []
    current_chunk = []
    current_start_time = transcript_lines[0]['start_time']

    for i in range(1, len(transcript_lines)):
        # Calculate similarity between current line and the last line in the chunk
        similarity = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]

        # Threshold for creating a new chunk
        if similarity < 0.85:  # Adjust this threshold based on needs
            end_time = transcript_lines[i-1]['end_time']
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
            current_start_time = transcript_lines[i]['start_time']

        current_chunk.append(transcript_lines[i])

    # Add last chunk
    if current_chunk:
        chunk_text = " ".join([f"{line['speaker']}: {line['text']}" for line in current_chunk])
        end_time = transcript_lines[-1]['end_time']
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

# prompt
def propositional_chunking(text, filename):
    system_prompt = [
        {
            "role": "system",
            "content": f"Decompose the meeting transcript into clear and simple propositions, ensuring they are interpretable out of context. Each chunk should represent a complete statement or actionable idea. In meeting transcripts, propositions might include decisions, plans, tasks, suggestions, or pieces of information."
                       " \n1. Maintain the original phrasing and speaker labels from the input whenever possible. "
                       " \n2. For any named entity that is accompanied by additional descriptive information, separate this information into its own distinct proposition."
                       " \n3. Propositions might span several sentences but should not span multiple speakers unless it’s a direct continuation of the previous thought. If multiple lines from the same speaker form a cohesive block, you can merge them into one propositional chunk."
                       " \n4. Decontextualize the proposition by adding necessary modifier to nouns or entire sentences and replacing pronouns (e.g., it, he, she, they, this, that) with the full name of the entities they refer to. "
                       " \n5. Present the results as a list of strings with the start and finish line number in brackets at the end, formatted for python"
                       " \nExample:"
                       "\nInput: "
                       " \n1 SPEAKER_00: Sue, if you want to present your prototype, go ahead."
                       " \n2 SPEAKER_02: This is it. "
                       " \n3 SPEAKER_02: Ninja Homer, made in Japan. "
                       " \n4 SPEAKER_02: There are a few changes we've made. "
                       " \n5 SPEAKER_02: Well, I'll look at the expense sheet. "
                       " \n6 SPEAKER_02: It turned it to be quite a lot of expensive to have it open up and have lots of buttons and stuff inside. "
                       " \n7 SPEAKER_02: So this is going to be an LCD screen. "
                       " \n8 SPEAKER_02: Just a very, very basic one, very small, with access to the menu through the scroll wheel and confirm. "
                       " \n9 SPEAKER_02: button."
                       " Output: [\"SPEAKER_00: Sue, if you want to present your prototype, go ahead. (1-1)\", "
                       " \"SPEAKER_02: This is Sue's prototype. \\nSPEAKER_02: Ninja Homer, made in Japan. (2-3)\", "
                       " \"SPEAKER_02: There are a few changes we've made to the Ninja Homer prototype. (4-4)\", "
                       " \"SPEAKER_02: Well, I'll look at the expense sheet for Ninja Homer prototype. \\nSPEAKER_02: It turned it to be quite a lot of expensive to have it open up and have lots of buttons and stuff inside. \\nSPEAKER_02: So this is going to be an LCD screen. (5-7)\", "
                       " \"SPEAKER_02: Just a very, very basic one, very small LCD on Ninja Homer prototype, with access to the menu through the scroll wheel and confirm. \\nSPEAKER_02: button. (8-9)\"]"
        },
        {
            "role": "user",
            "content": text
        }
    ]



# test
file_path = "path/to/your/transcript.jsonl"
jsonl_input = load_jsonl_file(file_path)
filename = "transcript.jsonl"
semantic_chunks = semantic_chunking(jsonl_input, filename)