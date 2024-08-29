import os
import faiss
from openai import OpenAI
from typing import Union

from file_manager import FileManager
from RAG import RAG
from ASR import ASR
from streamlit.runtime.uploaded_file_manager import UploadedFile as streamFile


class Thingo:

    def __init__(
        self, n_dimensions: int = 400,
        vector_db_path: str = "data/databases/index_file.index",
        link_db_path: str = "data/databases/link.json"
    ):
        self.open_ai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        self.vdb_index: Union[faiss.IndexFlatL2, None] = None

        self.file_manager = FileManager(
            vector_db_path,
            link_db_path
        )
        self.rag = RAG(self.file_manager, self.open_ai_client)
        self.asr = ASR(self.open_ai_client)

    def upload_file_from_streamlit(self, uploaded_file: streamFile):
        """from uploaded file"""
        # Save the uploaded file to a temporary file
        # print(uploaded_file.read())
        # return 1
        # with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        #     tmp_file.write(uploaded_file.read())
        #     tmp_file_path = tmp_file.name
        transcription = self.asr.transcribe_audio(uploaded_file)
        self.rag.extract_objects(transcription)
        exit()
        summary = self.rag.summarise_meeting(transcription)['abstract_summary']  # TODO just using the abstract for now
        save_transcript_file_path = self.file_manager.save_text_file(summary)
        self.rag.add_document(summary, save_transcript_file_path)
        self.file_manager.save(self.rag.vdb_index, self.rag.link_db)

    def add_audio_meeting_transcript_document(self, file_path: str):

        """from path"""
        # assert False  # TODO save transcript as a txt file
        transcription = self.asr.transcribe_audio_file(file_path)
        summary = self.rag.summarise_meeting(transcription)['abstract_summary']  # TODO just using the abstract for now
        save_transcript_file_path = self.file_manager.save_text_file(summary)
        self.rag.add_document(summary, save_transcript_file_path)
        self.file_manager.save(self.rag.vdb_index, self.rag.link_db)

    def add_text_document(self, file_path: str):
        """from path"""
        with open(file_path, "r") as file:
            text = str(file.read())
        self.rag.add_document(text, file_path)
        self.file_manager.save(self.rag.vdb_index, self.rag.link_db)

    def query(self, query_text: str):
        return self.rag.query(query_text)