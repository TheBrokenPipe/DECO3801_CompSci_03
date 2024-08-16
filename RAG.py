import faiss
import numpy as np
import os
from file_manager import FileManager
from bidict import bidict
from openai import OpenAI


class RAG:

    open_ai_text_model = "gpt-4o-mini"

    def __init__(self, file_manager: FileManager, open_ai_client: OpenAI, n_dimensions: int = 400):
        self.file_manager = file_manager
        self.open_ai_client = open_ai_client

        self.n_dimensions = n_dimensions

        self.vdb_index: faiss.IndexFlatL2
        self.link_db: bidict

        self.vdb_index, self.link_db = self.file_manager.load()
        if self.vdb_index is None or self.link_db is None:
            self.init_db()

    @property
    def size(self):
        return self.vdb_index.ntotal

    def init_db(self):
        assert self.vdb_index is None, "Vector database is already setup"
        self.vdb_index = faiss.IndexFlatL2(self.n_dimensions)  # L2 distance (Euclidean distance)

    def embed_text(self, text: str) -> np.ndarray:
        model_name = "text-embedding-3-small"  # allows for dim def (unlike ada-002)
        response = self.open_ai_client.embeddings.create(
            input=text,
            model=model_name,
            dimensions=self.n_dimensions
        )
        return np.array(response.data[0].embedding)

    def _add_to_db(self, embedding: np.ndarray, file_path: str):
        # TODO verify / ensure size
        next_index = self.size
        self.vdb_index.add(np.atleast_2d(embedding))
        self.link_db[next_index] = file_path

    def add_document(self, text: str, file_path: str):
        embedding = self.embed_text(text)
        self._add_to_db(embedding, file_path)

    def get_closest_indexes(self, embedding: np.ndarray, k=5) -> tuple[list[float], list[int]]:
        """returns distances, indexes"""
        # TODO verify / ensure size
        return self.vdb_index.search(np.atleast_2d(embedding), k=k)

    def get_closest_docs(self, query: str, k=3):
        embedding = self.embed_text(query)
        distances, indexes = self.get_closest_indexes(embedding, k)
        print(indexes)
        return indexes

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
