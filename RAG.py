import faiss
import numpy as np
import json
import os
from file_manager import FileManager
from bidict import bidict
from openai import OpenAI
from pydantic import BaseModel
from datetime import datetime

open_ai_text_model = "gpt-4o-mini"
open_ai_embedding_model = "text-embedding-3-small"


class KeyPoint(BaseModel):
    """
    text: key / main point and important idea, finding, or topic that are crucial to the essence
    """
    text: str


class KeyPoints(BaseModel):
    """
    people: list of key points mentioned in text
    """
    key_points: list[KeyPoint]


class ActionItem(BaseModel):
    """
    text: task, assignment or action that was agreed upon or mentioned as needing to be done.
    assigned_people_names: list of names of people assigned to this task
    due_date: date and/or time of when the task should be completed
    """
    text: str
    assigned_people_names: list[str]
    due_date: str


class ActionItems(BaseModel):
    """
    people: list of action items mentioned in text
    """
    action_items: list[ActionItem]


class Speaker(BaseModel):
    """
    original_name: name of the speaker in the transcript
    identified_name: name identified from the text
    """
    original_name: str
    identified_name: str


class IdentifiedSpeakers(BaseModel):
    """
    identified_speakers: list of speakers identified from text
    """
    identified_speakers: list[Speaker]



class RAG:

    open_ai_text_model = "gpt-4o-mini"

    def __init__(
            self,
            open_ai_client: OpenAI,
            n_dimensions: int = 400
    ):
        self.open_ai_client = open_ai_client
        self.n_dimensions = n_dimensions

    def llm_completion(self, messages: list[dict]) -> str:
        response = self.open_ai_client.chat.completions.create(
            model=self.open_ai_text_model,
            temperature=0,
            messages=messages
        )
        return response.choices[0].message.content

    def extract_specific_objects(self, text, model) -> dict:
        system_prompt = [
            {
                "role": "system",
                "content": f"You are tasked with finding objects in the text matching the provided model."
            },
            {
                "role": "user",
                "content": text
            }
        ]

        response = self.open_ai_client.beta.chat.completions.parse(
            model=self.open_ai_text_model,
            messages=system_prompt,
            response_format=model,
        )

        return json.loads(response.choices[0].message.content)

    def identify_speakers(self, lines: list[dict]) -> list[dict]:
        """
        replaced SPEAKER_XX with names if they can be identified.
        """
        # print(text)
        text = "\n".join(f"{line['speaker']}: {line['text']}" for line in lines)
        id_speakers = IdentifiedSpeakers(**self.extract_specific_objects(text, IdentifiedSpeakers))
        speaker_dict = {}
        for speaker in id_speakers.identified_speakers:
            speaker_dict[speaker.original_name] = speaker.identified_name

        for line in lines:
            line["speaker"] = speaker_dict.get(line["speaker"], line["speaker"])

        return lines

    def embed_text(self, text: str) -> np.ndarray:
        model_name = open_ai_embedding_model  # allows for dim def (unlike ada-002)
        response = self.open_ai_client.embeddings.create(
            input=text,
            model=model_name,
            dimensions=self.n_dimensions
        )
        return np.array(response.data[0].embedding)

    def query(self, query_text: str):
        with open(self.get_closest_docs(query_text)[0], 'r') as f:
            context = f.read()

        system_prompt = [
            {
                "role": "system",
                "content": f"You are an assistant for question-answering tasks. "
                           f"Use the following pieces of retrieved context to answer "
                           f"the question. If you don't know the answer, say that you "
                           f"don't know. Do not include any general information unless necessary\n\n"
                           f"{context}"
            },
            {
                "role": "user",
                "content": query_text
            }
        ]

        return self.llm_completion(system_prompt)

    def get_closest_indexes(self, embedding: np.ndarray, k=5) -> tuple[list[float], list[int]]:
        """returns distances, indexes"""
        # TODO verify / ensure size
        return self.vdb_index.search(np.atleast_2d(embedding), k=k)

    def _add_to_db(self, embedding: np.ndarray, file_path: str):
        # TODO verify / ensure size
        next_index = self.size
        print(self.size)
        self.vdb_index.add(np.atleast_2d(embedding))
        self.link_db[str(next_index)] = file_path

    def add_document(self, text: str, file_path: str):
        embedding = self.embed_text(text)
        self._add_to_db(embedding, file_path)

    def get_docs_from_indexes(self, indexes: list):
        return [self.link_db[str(i)] for i in indexes if i not in [str(-1), -1]]

    def get_closest_docs(self, query_text: str, k=3):
        embedding = self.embed_text(query_text)
        distances, indexes = self.get_closest_indexes(embedding, k)
        return self.get_docs_from_indexes(indexes[0])

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
        return self.extract_specific_objects(transcription, KeyPoints)

    def action_item_extraction(self, transcription):
        return self.extract_specific_objects(transcription, ActionItems)

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
        return {
            'abstract_summary': self.abstract_summary_extraction(transcription),
            'key_points': self.key_points_extraction(transcription),
            'action_items': self.action_item_extraction(transcription),
            # 'sentiment': self.sentiment_analysis(transcription)
        }
