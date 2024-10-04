import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging

from .file_manager import FileManager
from models import *
from utils import *

from pydantic import BaseModel, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.docstore.document import Document
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

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
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        else:
            self.llm = ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1e"), temperature=0.2)
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        connection = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('HOSTNAME')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"
        
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=os.environ.get("VECTOR_STORE_NAME", "deco3801"),
            connection=connection,
            use_jsonb=True,
        )

    def invoke_llm(self, system_prompt: str, user_prompt: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [("system","{system_prompt}",),
                ("human", "{user_prompt}"),])
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
            ("human","{text}")
        ])
        structured_llm = self.llm.with_structured_output(model) | RunnableLambda(self.check_none)
        session = prompt | structured_llm.with_retry()
        try:
            response = session.invoke({"text":text})
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
        return self.extract_specific_objects(transcript, DB_KeyPoints)

    def action_item_extraction(self, transcription):
        transcript = jsonl_to_txt(transcription)
        return self.extract_specific_objects(transcript, DB_ActionItems)

    def summarise_meeting(self, transcription) -> dict:
        return {
            'abstract_summary': self.abstract_summary_extraction(transcription),
            'key_points': self.key_points_extraction(transcription),
            'action_items': self.action_item_extraction(transcription),
        }
    
    def embed_meeting(self, meeting: DB_Meeting, chunks: list[Document]):
        for doc in chunks:
            if isinstance(self.embeddings, OllamaEmbeddings):
                doc.page_content = "search_document: " + doc.page_content
            doc.metadata["meeting_id"] = meeting.id
        
        self.vector_store.add_documents(chunks)

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def query_retrieval(self, query_text):
        retriever = self.vector_store.as_retriever()
        system_prompt = "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Do not include any general information unless necessary. Use three sentences maximum and keep the answer concise. \n\n Context: {context}"
        prompt = ChatPromptTemplate.from_messages(
            [("system",system_prompt,),
                ("human", "{question}"),])

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

