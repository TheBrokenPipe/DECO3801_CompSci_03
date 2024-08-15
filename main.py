import os
import faiss
from openai import OpenAI
from openai.pagination import SyncPage
import json
from typing import Union
import numpy as np
import json
from bidict import bidict

from file_manager import FileManager

os.environ['OPENAI_API_KEY'] = "sk-proj-5Ay4ISQv4kBgYs7ijKreT3BlbkFJeTIi2OKaevKN2bGcu0sc"


class Thingo:

    open_ai_asr_model = "whisper-1"
    open_ai_text_model = "gpt-4o-mini"

    def __init__(
        self, n_dimensions: int = 400,
            vector_db_path: str = "data/databases/index_file.index",
            link_db_path: str = "data/databases/link.json"
    ):
        self.open_ai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        self.n_dimensions = n_dimensions
        self.vdb_index: Union[faiss.IndexFlatL2, None] = None

        self.file_manager = FileManager(
            vector_db_path,
            link_db_path
        )

        self.link_db: bidict = bidict()

        if os.path.isfile(vector_db_path) and os.path.isfile(link_db_path):
            self.file_manager.load_db()
            self.file_manager.load_link()
        else:
            self.setup_db()

    def setup_db(self):
        assert self.vdb_index is None, "Vector database is already setup"
        self.vdb_index = faiss.IndexFlatL2(self.n_dimensions)  # L2 distance (Euclidean distance)

    @property
    def size(self):
        return self.vdb_index.ntotal

    def add_to_db(self, embedding: np.ndarray, file_path: str):
        # TODO verify / ensure size
        next_index = self.size
        self.vdb_index.add(np.atleast_2d(embedding))
        self.link_db[next_index] = file_path

    def get_closest_indexes(self, embedding: np.ndarray, k=5) -> tuple[list[float], list[int]]:
        """returns distances, indexes"""
        # TODO verify / ensure size
        return self.vdb_index.search(np.atleast_2d(embedding), k=k)

    def transcribe_audio_file(self, file_path: str) -> str:
        """from path"""
        with open(file_path, "rb") as audio_file:
            transcription = self.open_ai_client.audio.transcriptions.create(
                model=self.open_ai_asr_model,
                file=audio_file
            )
        return transcription.text

    def summary_section(self, messages: list[dict]) -> str:
        response = self.open_ai_client.chat.completions.create(
            model=self.open_ai_text_model,
            temperature=0,
            messages=messages
        )
        return response.choices[0].message.content

    def abstract_summary_extraction(self, transcription):
        return self.summary_section(
            [
                {
                    "role": "system",
                    "content": "You are a highly skilled AI trained in language comprehension and summarization. "
                               "I would like you to read the following text and summarize it into a concise abstract "
                               "paragraph. Aim to retain the most important points, providing a coherent and readable "
                               "summary that could help a person understand the main points of the discussion without "
                               "needing to read the entire text. Please avoid unnecessary details or tangential points."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )

    def key_points_extraction(self, transcription):
        return self.summary_section(
            [
                {
                    "role": "system",
                    "content": "You are a proficient AI with a specialty in distilling information into key points. "
                               "Based on the following text, identify and list the main points that were discussed or "
                               "brought up. These should be the most important ideas, findings, or topics that are "
                               "crucial to the essence of the discussion. Your goal is to provide a list that someone "
                               "could read to quickly understand what was talked about."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )

    def action_item_extraction(self, transcription):
        return self.summary_section(
            [
                {
                    "role": "system",
                    "content": "You are an AI expert in analyzing conversations and extracting action items. "
                               "Please review the text and identify any tasks, assignments, or actions that were "
                               "agreed upon or mentioned as needing to be done. These could be tasks assigned to "
                               "specific individuals, or general actions that the group has decided to take. "
                               "Please list these action items clearly and concisely."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )

    def sentiment_analysis(self, transcription):
        return self.summary_section(
            [
                {
                    "role": "system",
                    "content": "As an AI with expertise in language and emotion analysis, "
                               "your task is to analyze the sentiment of the following text. "
                               "Please consider the overall tone of the discussion, "
                               "the emotion conveyed by the language used, and the context in which words and "
                               "phrases are used. Indicate whether the sentiment is generally positive, negative, "
                               "or neutral, and provide brief explanations for your analysis where possible."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )

    def summarise_meeting(self, transcription) -> dict:
        abstract_summary = self.abstract_summary_extraction(transcription)
        key_points = self.key_points_extraction(transcription)
        action_items = self.action_item_extraction(transcription)
        sentiment = self.sentiment_analysis(transcription)
        return {
            'abstract_summary': abstract_summary,
            'key_points': key_points,
            'action_items': action_items,
            'sentiment': sentiment
        }

    def save_text_file(self, text: str) -> str:
        file_path = "data/saved_docs/file_test.txt"
        with open(file_path, 'w') as f:
            f.write(text)
        return file_path

    def add_audio_meeting_transcript_document(self, file_path: str):
        """from path"""
        # assert False  # TODO save transcript as a txt file
        transcription = self.transcribe_audio_file(file_path)
        summary = self.summarise_meeting(transcription)['abstract_summary']  # TODO just using the abstract for now
        save_transcript_file_path = self.save_text_file(summary)
        self._add_doc(summary, save_transcript_file_path)

    def add_text_document(self, file_path: str):
        """from path"""
        with open(file_path, "r") as file:
            text = str(file.read())
        self._add_doc(text, file_path)

    def _add_doc(self, text: str, file_path: str):
        embedding = self.embed_text(text)
        self.add_to_db(embedding, file_path)

    def embed_text(self, text: str) -> np.ndarray:
        model_name = "text-embedding-3-small"  # allows for dim def (unlike ada-002)
        response = self.open_ai_client.embeddings.create(
            input=text,
            model=model_name,
            dimensions=self.n_dimensions
        )
        return np.array(response.data[0].embedding)

    def get_closest_docs(self, query: str, k=3):
        embedding = self.embed_text(query)
        distances, indexes = self.get_closest_indexes(embedding, k)
        print(indexes)
        # 1:40 am, im going to bed


t = Thingo(10)
print("Transcribing:")
# t.add_audio_meeting_transcript_document("en-US_AntiBERTa_for_word_boosting_testing.wav")
# t.add_to_db(t.embed_text("Pizza hut"))
# t.save_db()

transcription = t.transcribe_audio_file("data/audio_recordings/en-US_AntiBERTa_for_word_boosting_testing.wav")
print(transcription)

# em = t.embed_text(transcription)

print()
print("Num embeddings saved: ", t.vdb_index.ntotal)
print()

for i in ["pizza is tasty", "chatgpt is an llm used to design proteins", "protein"]:
    em = t.embed_text(i)
    print(t.get_closest_indexes(em, 1))

# ids = t.vdb_index.reconstruct_n(0, t.vdb_index.ntotal)
# print("All IDs:", ids)
# print(t.transcribe_audio_file("en-US_AntiBERTa_for_word_boosting_testing.wav"))

