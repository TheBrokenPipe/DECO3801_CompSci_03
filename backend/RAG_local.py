import numpy as np
import json
import os
from .file_manager import FileManager

from pydantic import BaseModel
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

import logging
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import *

class KeyPoints(BaseModel):
    """
    key_points: list of key points mentioned in text
    """
    key_points: list[str]


class ActionItems(BaseModel):
    """
    action_items: list of action items mentioned in text
    """
    action_items: list[str]

class RAG:

    def __init__(
            self,
            n_dimensions: int = 400
    ):
        self.n_dimensions = n_dimensions
        self.logger = logging.getLogger(__name__)
        if "OPENAI_API_KEY" in os.environ:
            self.llm = ChatOpenAI(model=os.environ.get("OPENAI_LLM_MODEL", "gpt-4o-mini"), temperature=0)
        else:
            self.llm = ChatOllama(model=os.environ.get("OLLAMA_MODEL", "llama3.1e"), temperature=0)


    def invoke_llm(self, system_prompt: str, user_prompt: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [("system","{system_prompt}",),
                ("human", "{user_prompt}"),])
        parser = StrOutputParser()
        session = prompt | self.llm | parser
        response = session.invoke({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return response

    def extract_specific_objects(self, text, model) -> dict:
        structured_llm = self.llm.with_structured_output(model)
        response = structured_llm.invoke(text)
        return response


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

        system_prompt = f"You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Do not include any general information unless necessary. Use three sentences maximum and keep the answer concise. \n\n Context: {context}"
        user_prompt = query_text

        # Alternative prompts with context in user prompt rather than system prompt
        # system_prompt = "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Do not include any general information unless necessary. Use three sentences maximum and keep the answer concise."
        # user_prompt = f"Context: {context}\n\nQuestion: {query_text}""
        
        return self.invoke_llm(system_prompt, user_prompt)

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
        system_prompt = "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
        return self.invoke_llm(system_prompt, transcription)

    def key_points_extraction(self, transcription):
        transcript = jsonl_to_txt(transcription)
        return self.extract_specific_objects("What are the key points in this transcript?\n\n" + transcript, KeyPoints)

    def action_item_extraction(self, transcription):
        transcript = jsonl_to_txt(transcription)
        return self.extract_specific_objects("What action items are in this transcript?\n\n" + transcript, ActionItems)

    def summarise_meeting(self, transcription) -> dict:
        return {
            'abstract_summary': self.abstract_summary_extraction(transcription),
            'key_points': self.key_points_extraction(transcription),
            'action_items': self.action_item_extraction(transcription),
        }
