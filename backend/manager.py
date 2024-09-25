import os
import faiss
from openai import OpenAI
from typing import Union
from datetime import datetime
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .file_manager import FileManager
from .RAG_local import RAG
# from .RAG import RAG
from .ASR import ASR
from streamlit.runtime.uploaded_file_manager import UploadedFile as streamFile
from .docker_manager import DockerManager
from models import *
from access import *
import logging

class Manager:

    def __init__(
        self, n_dimensions: int = 400,
        pg_manager: DockerManager = None
    ):
        self.open_ai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        self.vdb_index: Union[faiss.IndexFlatL2, None] = None

        self.rag = RAG()
        self.asr = ASR(os.environ['HF_TOKEN'])
        self.pg_manager = pg_manager
        self.logger = logging.getLogger(__name__)

    @staticmethod
    async def get_all_meetings() -> list[Meeting]:
        return await select_many_from_table(Meeting)

    @staticmethod
    async def get_all_tags() -> list[Tag]:
        return await select_many_from_table(Tag)

    @staticmethod
    async def create_tag(name, meetings: list[Meeting]) -> Tag:
        tag = await insert_into_table(TagCreation(name=name), always_return_list=False)
        print(f"Tag added: {tag.name}")
        await Manager.add_meetings_to_tag(tag, meetings)
        print(f"Meetings added")
        return tag

    @staticmethod
    async def create_meeting(
            name: str, date: datetime, file_recording: str, file_transcript: str, summary: str
    ) -> Meeting:
        meeting = await insert_into_table(
            MeetingCreation(
                name=name,
                date=date,
                file_recording=file_recording,
                file_transcript=file_transcript,
                summary=summary
            ), always_return_list=False
        )
        print(f"Meeting added: {meeting.name}")
        return meeting

    @staticmethod
    async def create_action_item(item: str, meeting: Meeting):
        return await insert_into_table(ActionItemCreation(text=item, meeting_id=meeting.id))

    @staticmethod
    async def create_key_point(point: str, meeting: Meeting):
        return await insert_into_table(KeyPointCreation(text=point, meeting_id=meeting.id))

    @staticmethod
    async def add_meetings_to_tag(tag: Tag, meetings: Meeting | list[Meeting]) -> list[MeetingTag]:
        if isinstance(meetings, Meeting):
            return await insert_into_table(MeetingTagCreation(meeting_id=meetings.id, tag_id=tag.id))
        elif isinstance(meetings, list) and len(meetings):
            return await insert_into_table([MeetingTagCreation(meeting_id=meeting.id, tag_id=tag.id) for meeting in meetings])

    @staticmethod
    async def get_tag_meetings(tag: Tag) -> list[Meeting]:
        return await select_with_joins(tag.id, [Tag, MeetingTag, Meeting])

    def upload_file_from_streamlit(self, uploaded_file: streamFile):
        time_tag = datetime.now().timestamp()
        audio_file_path = f"audio_recordings/audio_uploaded_{time_tag}.wav"

        # Open a file in write-binary mode and write the contents of the uploaded file to it
        with open(audio_file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer().tobytes())

        print(f"File saved to {audio_file_path}")
        """from uploaded file"""
        # Save the uploaded file to a temporary file
        # print(uploaded_file.read())
        # return 1
        # with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        #     tmp_file.write(uploaded_file.read())
        #     tmp_file_path = tmp_file.name
        transcription = self.asr.transcribe_audio(uploaded_file)
        # self.rag.extract_objects(transcription)
        # exit()
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
        summary = self.rag.summarise_meeting(text)
        print(summary)
        return summary
        self.rag.add_document(text, file_path)
        self.file_manager.save(self.rag.vdb_index, self.rag.link_db)

    def query(self, query_text: str):
        return self.rag.query(query_text)
    
    async def transcribe_meeting(self):
        meetings = await select_many_from_table(Meeting,(""),("file_transcript"))
        if len(meetings) > 0:
            meeting = meetings[0]
            recording = meeting.file_recording
            meeting.file_transcript = self.asr.transcribe_audio_file(recording)
            await update_table(meeting)

    async def ingest_meeting(self):
        meetings = await select_ingestion_meeting(Meeting,(""),("summary"))
        if len(meetings) > 0:
            meeting = meetings[0]
            with open(meeting.file_transcript, 'r', encoding="utf-8") as file:
                transcript = file.read()

            full_summary = self.rag.summarise_meeting(transcript)
            self.logger.debug(full_summary)

            meeting.summary = full_summary['abstract_summary']
            await update_table(meeting)

            for action_item in full_summary['action_items'].action_items:
                await self.create_action_item(action_item, meeting)

            for key_point in full_summary['key_points'].key_points:
                await self.create_key_point(key_point, meeting)
            
            # TODO: RAG chunking and embedding goes here
            