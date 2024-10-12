import os
import sys

import logging
import json

from pydantic import BaseModel, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.docstore.document import Document
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import DB_Meeting


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
                self.embeddings = OpenAIEmbeddings(model=embed_model,
                                                   dimensions=1000)
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

        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=os.environ.get("VECTOR_STORE_NAME", "deco3801"),
            connection=connection,
            use_jsonb=True,
        )

    def invoke_llm(self, system_prompt: str, user_prompt: str) -> str:
        print("invoke_llm")
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

    def embed_meeting(self, meeting: DB_Meeting, chunks: list[Document]):
        for chunk in chunks:
            if isinstance(self.embeddings, OllamaEmbeddings):
                chunk.page_content = "search_document: " + chunk.page_content
            chunk.metadata["meeting_id"] = meeting.id

        self.vector_store.add_documents(chunks)

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def query_retrieval(self, query_text) -> str:
        retriever = self.vector_store.as_retriever()
        system_prompt = (
            "You are an assistant for question-answering tasks. Use the "
            "following pieces of retrieved context to answer the question. "
            "If you don't know the answer, say that you don't know. "
            "Do not include any general information unless necessary. "
            "Use three sentences maximum and keep the answer concise. \n\n"
            "Context: {context}"
        )
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt,), ("human", "{question}")]
        )

        qa_chain = (
            {"context": retriever | self.format_docs,
             "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return qa_chain.invoke(query_text)

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
