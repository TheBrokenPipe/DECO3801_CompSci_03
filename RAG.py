import faiss
import numpy as np
import os
from file_manager import FileManager
from bidict import bidict
from openai import OpenAI
from pydantic import BaseModel
import json
from datetime import datetime


class Relationship(BaseModel):
    """
    name: name or title of related person
    relation: brief description of how this person is related to the main entity
    """
    name: str
    relation: str


class Person(BaseModel):
    """
    name: name of person
    description: brief description of person
    related_people: list of relations this person has to other people
    """
    name: str
    description: str
    related_people: list[Relationship]


class Date(BaseModel):
    name: str
    year: str | None
    month: str | None
    day: str | None
    description: str


class Place(BaseModel):
    """
    name: name of place
    description: brief description of place
    """
    name: str
    description: str


class Place(BaseModel):
    """
    name: name of place
    description: brief description of place
    """
    name: str
    description: str


class MiscObjects(BaseModel):
    name: str
    instances_from_text: list[str]


class ExtractedObjects(BaseModel):
    people: list[Person]
    dates: list[Date]
    places: list[Place]
    # misc_objects: list[MiscObjects]


class ExtractedObjects2(BaseModel):
    people: list[Person]
    dates: list[Date]
    places: list[Place]
    # misc_objects: list[MiscObjects]







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
        # print("Num embeddings saved: ", self.vdb_index.ntotal)
        return self.vdb_index.ntotal

    def init_db(self):
        assert self.vdb_index is None, "Vector database is already setup"
        self.vdb_index = faiss.IndexFlatL2(self.n_dimensions)  # L2 distance (Euclidean distance)
        self.link_db = bidict()

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
        print(self.size)
        self.vdb_index.add(np.atleast_2d(embedding))
        self.link_db[str(next_index)] = file_path

    def add_document(self, text: str, file_path: str):
        embedding = self.embed_text(text)
        self._add_to_db(embedding, file_path)

    def get_closest_indexes(self, embedding: np.ndarray, k=5) -> tuple[list[float], list[int]]:
        """returns distances, indexes"""
        # TODO verify / ensure size
        return self.vdb_index.search(np.atleast_2d(embedding), k=k)

    def get_docs_from_indexes(self, indexes: list):
        return [self.link_db[str(i)] for i in indexes if i not in [str(-1), -1]]

    def get_closest_docs(self, query_text: str, k=3):
        embedding = self.embed_text(query_text)
        distances, indexes = self.get_closest_indexes(embedding, k)
        return self.get_docs_from_indexes(indexes[0])

    def query(self, query_text: str):
        with open(self.get_closest_docs(query_text)[0], 'r') as f:
            context = f.read()

        system_prompt = [
            {
                "role": "system",
                "content": f"You are an assistant for question-answering tasks. "
                           f"Use the following pieces of retrieved context to answer "
                           f"the question. If you don't know the answer, say that you "
                           f"don't know. Do not include any general information unless neccisary\n\n"
                           f"{context}"
            },
            {
                "role": "user",
                "content": query_text
            }
        ]

        return self.llm_completion(system_prompt)

    def llm_completion(self, messages: list[dict]) -> str:
        response = self.open_ai_client.chat.completions.create(
            model=self.open_ai_text_model,
            temperature=0,
            messages=messages
        )
        return response.choices[0].message.content

    def abstract_summary_extraction(self, transcription):
        return self.llm_completion(
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
        return self.llm_completion(
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
        return self.llm_completion(
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
        return self.llm_completion(
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

    def extract_objects(self, text):
        system_prompt = [
            {
                "role": "system",
                "content": f"existing classes of objects:\npeople\nevents\nplaces\n\n"
                           f"find all the instances of the classes in the following text "
                           f"and create new classes if needed."
                           f"each class should be in the json format provided:"
            },
            {
                "role": "user",
                "content": text
            }
        ]

        response = self.open_ai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=system_prompt,
            response_format=ExtractedObjects,
        )
        print((response.usage.total_tokens/1e6) * 0.150)
        # print(response.choices[0].message.json())
        # print(type(response.choices[0].message.json()))
        print(json.loads(response.choices[0].message.content))
        print(json.dumps(json.loads(response.choices[0].message.content), indent=4))

        exit()

        return response.choices[0].message.content
