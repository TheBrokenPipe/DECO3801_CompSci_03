import os
import sys
from typing import Any, List, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import sqlalchemy
import asyncio

from models import DB_Meeting
from access import *
from ..models import *

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
            llm_model = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
            self.llm = ChatOpenAI(model=llm_model, temperature=0.2)

            if os.getenv("EMBED_PROVIDER", "openai") == "openai":
                embed_model = "text-embedding-3-large"
                self.embeddings = OpenAIEmbeddings(model=embed_model, dimensions=500)
            else:
                embed_model = "nomic-embed-text"
                self.embeddings = OllamaEmbeddings(model=embed_model)

        else:
            llm_model = os.getenv("OLLAMA_MODEL", "llama3.1e")
            self.llm = ChatOllama(model=llm_model, temperature=0.2)

            embed_model = "nomic-embed-text"
            self.embeddings = OllamaEmbeddings(model=embed_model)

        login = f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        host = os.getenv('HOSTNAME')
        port = os.getenv('PORT')
        db = os.getenv('DB_NAME')
        connection = f"postgresql+psycopg://{login}@{host}:{port}/{db}"
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
                ("human", "{user_prompt}"),])
        parser = StrOutputParser()
        session = prompt | self.llm | parser
        response = session.invoke({"system_prompt": system_prompt,
                                   "user_prompt": user_prompt})
        return response

    def seg_to_txt(self, segment) -> str:
        """Format transcript segment as plain text."""
        text = segment["text"].strip()
        if "speaker" in segment:
            speaker = segment["speaker"]
        else:
            speaker = "UNKNOWN_SPEAKER"

        return f'{speaker}: {text}'

    def jsonl_to_txt(self, jsonl: str) -> str:
        """Convert JSONL transcript to basic transcript with speaker labels."""
        segments = (json.loads(seg) for seg in jsonl.split('\n'))
        transcript = "\n".join(self.seg_to_txt(segment)
                               for segment in segments)
        return transcript

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
                "If you do not know the value of an attribute asked to "
                "extract, return null for the attribute's value.",
            ),
            ("human", "{text}")
        ])

        structured_llm = self.llm.with_structured_output(model)
        llm = structured_llm | RunnableLambda(self.check_none)
        session = prompt | llm.with_retry()
        try:
            response = session.invoke({"text": text})
        except Exception:
            response = None
        return response

    def abstract_summary_extraction(self, transcription):
        transcript = self.jsonl_to_txt(transcription)
        system_prompt = (
            "You are a highly skilled AI trained in language comprehension "
            "and summarization. I would like you to read the following text "
            "and summarize it into a concise abstract paragraph. Aim to "
            "retain the most important points, providing a coherent and "
            "readable summary that could help a person understand the main "
            "points of the discussion without needing to read the entire "
            "text. Please avoid unnecessary details or tangential points.")
        summary = self.invoke_llm(system_prompt, transcript)
        if isinstance(self.llm, ChatOllama) and summary[:4] == "Here":
            summary = summary[summary.find("\n\n"):].strip()
        return summary

    def summarise_chat(self, meeting_summaries: list[str]):
        system_prompt = (
            "You are a highly skilled AI trained in language comprehension "
            "and summarization. I would like you to read the following "
            "meeting-summaries and summarize it into a single concise "
            "abstract paragraph. Aim to retain the most important points, "
            "providing a coherent and readable summary that could help a "
            "person understand the main points of the discussions without "
            "needing to read each of the meeting summaries. Please avoid "
            "unnecessary details or tangential points."
        )
        summary = self.invoke_llm(system_prompt, '\n'.join(meeting_summaries))
        if isinstance(self.llm, ChatOllama) and summary[:4] == "Here":
            summary = summary[summary.find("\n\n"):].strip()
        return summary

    def key_points_extraction(self, transcription):
        transcript = self.jsonl_to_txt(transcription)
        return self.extract_specific_objects(transcript, KeyPoints)

    def action_item_extraction(self, transcription):
        transcript = self.jsonl_to_txt(transcription)
        return self.extract_specific_objects(transcript, ActionItems)

    def summarise_meeting(self, transcript) -> dict:
        return {
            'abstract_summary': self.abstract_summary_extraction(transcript),
            'key_points': self.key_points_extraction(transcript),
            'action_items': self.action_item_extraction(transcript),
        }

    def embed_meeting(self, meeting, chunks: list[Document]):
        for chunk in chunks:
            if isinstance(self.embeddings, OllamaEmbeddings):
                chunk.page_content = "search_document: " + chunk.page_content
            chunk.metadata["meeting_id"] = meeting.id

        self.vector_store.add_documents(chunks)

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    async def query_retrieval(self, query_text: str, meetings: List[DB_Meeting]) -> tuple[str, list]:
        set_debug(True)

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

        docs = retriever.invoke(query_text)
        sources = await self.get_sources_list(docs)

        qa_chain = (
                {"context": retriever | self.format_docs, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
        )

        llm_response = qa_chain.invoke(query_text)
        
        # response = llm_response + "\n\nSources:\n" + str(sources)
        # print(response)

        return llm_response, sources

    def query(self, query_text: str):
        with open(self.get_closest_docs(query_text)[0], 'r') as f:
            context = f.read()

        system_prompt = (
            "You are an assistant for question-answering tasks. Use the "
            "following pieces of retrieved context to answer the question. "
            "If you don't know the answer, say that you don't know. Do not "
            "include any general information unless necessary. Use three "
            "sentences maximum and keep the answer concise. \n\n"
            f"Context: {context}"
        )
        user_prompt = query_text

        # Alternative with context in user prompt instead of system prompt
        # system_prompt = (
        #     "You are an assistant for question-answering tasks. Use the "
        #     "following pieces of retrieved context to answer the question. "
        #     "If you don't know the answer, say that you don't know. Do not "
        #     "include any general information unless necessary. Use three "
        #     "sentences maximum and keep the answer concise. \n\n"
        #     f"Context: {context}"
        # )
        # user_prompt = f"Context: {context}\n\nQuestion: {query_text}""

        return self.invoke_llm(system_prompt, user_prompt)

    async def get_sources_list(self, chunks: List[Document]) -> List[str]:
        meetings_dict = {m.id: m for m in await select_many_from_table(
            DB_Meeting,
            list(set([c.metadata["meeting_id"] for c in chunks]))
        )}
        sources = [
            {
                "start_time": chunk.metadata["start_time"],
                "end_time": chunk.metadata["end_time"],
                "meeting": meetings_dict[chunk.metadata["meeting_id"]]
            } for chunk in chunks
        ]
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
