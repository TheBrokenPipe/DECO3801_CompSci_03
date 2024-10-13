import os
import sys
from typing import Any, List, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import sqlalchemy

from .file_manager import FileManager
from models import *
from utils import *
from access import *

from pydantic import BaseModel, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.docstore.document import Document
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import SQLColumnExpression, cast, create_engine, delete, func, select, Integer
from sqlalchemy.dialects.postgresql import JSON, JSONB, JSONPATH, UUID, insert
from langchain.globals import set_debug

set_debug(True)

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

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if "OPENAI_API_KEY" in os.environ:
            self.llm = ChatOpenAI(model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"), temperature=0.2)

            if os.getenv("EMBED_PROVIDER", "openai") == "openai":
                self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=1000)
            else:
                self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

        else:
            self.llm = ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1e"), temperature=0.2)
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

        connection = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('HOSTNAME')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"
        self.logger.debug(connection)

        self.vector_store = DB_MeetingChunk(
            embeddings=self.embeddings,
            collection_name=os.environ.get("VECTOR_STORE_NAME", "deco3801"),
            connection=connection,
            use_jsonb=True,
        )

    def invoke_llm(self, system_prompt: str, user_prompt: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "{system_prompt}",),
             ("human", "{user_prompt}"), ])
        parser = StrOutputParser()
        session = prompt | self.llm | parser
        response = session.invoke({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return response

    @staticmethod
    def check_none(model: BaseModel) -> BaseModel:
        if model is None:
            raise ValidationError
        return model

    def extract_specific_objects(self, text, model):
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert extraction algorithm. "
                "Only extract relevant information from the text. "
                "If you do not know the value of an attribute asked to extract, "
                "return null for the attribute's value.",
            ),
            ("human", "{text}")
        ])
        structured_llm = self.llm.with_structured_output(model) | RunnableLambda(self.check_none)
        session = prompt | structured_llm.with_retry()
        try:
            response = session.invoke({"text": text})
        except Exception as e:
            response = None
        return response

    def abstract_summary_extraction(self, transcription):
        transcript = jsonl_to_txt(transcription)
        system_prompt = "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
        summary = self.invoke_llm(system_prompt, transcript)
        if isinstance(self.llm, ChatOllama) and summary[:4] == "Here":
            summary = summary[summary.find("\n\n"):].strip()
        return summary

    def key_points_extraction(self, transcription):
        transcript = jsonl_to_txt(transcription)
        return self.extract_specific_objects(transcript, KeyPoints)

    def action_item_extraction(self, transcription):
        transcript = jsonl_to_txt(transcription)
        return self.extract_specific_objects(transcript, ActionItems)

    def summarise_meeting(self, transcription) -> dict:
        return {
            'abstract_summary': self.abstract_summary_extraction(transcription),
            'key_points': self.key_points_extraction(transcription),
            'action_items': self.action_item_extraction(transcription),
        }

    def embed_meeting(self, meeting: DB_Meeting, chunks: list[Document]):
        for chunk in chunks:
            if isinstance(self.embeddings, OllamaEmbeddings):
                chunk.page_content = "search_document: " + chunk.page_content
            chunk.metadata["meeting_id"] = meeting.id

        self.vector_store.add_documents(chunks)

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def query_retrieval(self, query_text: str, meetings: List[DB_Meeting]) -> str:

        if len(meetings) > 0:
            meeting_ids = [meeting.id for meeting in meetings]
            retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
                                                       search_kwargs={'k': 3, 'score_threshold': 0.5,
                                                                      'filter': {"meeting_id": {"$in": meeting_ids}}})
        else:
            retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
                                                       search_kwargs={'k': 3, 'score_threshold': 0.5})

        system_prompt = (
            "You are an assistant for question-answering tasks. Use the following pieces of "
            "retrieved context to answer the question. If you don't know the answer, say that "
            "you don't know. Do not include any general information unless necessary. "
            "Use three sentences maximum and keep the answer concise. \n\n Context: {context}"
        )
        prompt = ChatPromptTemplate.from_messages([("system", system_prompt,), ("human", "{question}")])

        qa_chain = (
                {"context": retriever | self.format_docs, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
        )

        return qa_chain.invoke(query_text)

    def query(self, query_text: str):
        with open(self.get_closest_docs(query_text)[0], 'r') as f:
            context = f.read()

        system_prompt = f"You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Do not include any general information unless necessary. Use three sentences maximum and keep the answer concise. \n\n Context: {context}"
        user_prompt = query_text

        # Alternative prompts with context in user prompt rather than system prompt
        # system_prompt = "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Do not include any general information unless necessary. Use three sentences maximum and keep the answer concise."
        # user_prompt = f"Context: {context}\n\nQuestion: {query_text}""

        return self.invoke_llm(system_prompt, user_prompt)

    def get_sources_list(self, chunks: List[Document]) -> List[str]:
        sources = []
        for chunk in chunks:
            meeting_id = chunk.metadata["meeting_id"]

            meeting_name = select_from_table(DB_meeting, meeting_id).name
            start_time: float = chunk.metadata["start_time"]
            end_time: float = chunk.metadata["end_time"]
            source_string = f"{meeting_name} at {start_time:.2f} - {end_time:.2f}"

            sources.append(source_string)
        return sources

class DB_MeetingChunk(PGVector):
    def _results_to_docs_and_scores(self, results: Any) -> List[Tuple[Document, float]]:
        """Return docs and scores from results."""
        docs = [
            (
                Document(
                    id=str(result.EmbeddingStore.id),
                    page_content=self.get_content_with_context(result, 3),
                    metadata=result.EmbeddingStore.cmetadata,
                ),
                result.distance if self.embeddings is not None else None,
            )
            for result in results
        ]
        return docs

    def get_content_with_context(self, chunk, n=2) -> str:
        # n is number of chunks to get, if n=2 it will return the original with the 2 chunks above and 2 chunks below
        with self._make_sync_session() as session:  # type: ignore[arg-type]
            collection = self.get_collection(session)

            meeting_id = chunk.EmbeddingStore.cmetadata["meeting_id"]
            chunk_id = chunk.EmbeddingStore.cmetadata["chunk_id"]

            # create list of id's to get
            ids = []
            for i in range(chunk_id-n, chunk_id):
                ids.append(i)
            ids.append(chunk_id)
            for i in range(chunk_id+1, chunk_id+n+1):
                ids.append(i)

            # filter to get the ids of the filepath from the
            filter = {
                "$and": [
                    {"meeting_id": {"$eq": meeting_id}},
                    {"chunk_id": {"$in": ids}},
                ]
            }
            filter_by = [self.EmbeddingStore.collection_id == collection.uuid, self._create_filter_clause(filter)]

            consecutive_chunks: List[Any] = (
                session.query(
                    self.EmbeddingStore,
                )
                .filter(*filter_by)
                .order_by(sqlalchemy.asc(cast(self.EmbeddingStore.cmetadata["chunk_id"].astext, Integer)))  # check
                .join(
                    self.CollectionStore,
                    self.EmbeddingStore.collection_id == self.CollectionStore.uuid,)
                .all()
            )

        # Concatenate all chunks into one string
        doc_content = "\n".join(chunk.document for chunk in consecutive_chunks)

        return doc_content
