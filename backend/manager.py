import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
from datetime import datetime

from .file_manager import FileManager
from .RAG import RAG
from models import *
from access import *

from streamlit.runtime.uploaded_file_manager import UploadedFile as streamFile


class Manager:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rag = RAG()

    @staticmethod
    async def get_all_meetings() -> list[DB_Meeting]:
        return await select_many_from_table(DB_Meeting)

    @staticmethod
    async def get_all_tags() -> list[DB_Tag]:
        return await select_many_from_table(DB_Tag)

    @staticmethod
    async def create_tag(name, meetings: list[DB_Meeting]) -> DB_Tag:
        tag = await insert_into_table(DB_Tag(name=name, last_modified=datetime.now()), always_return_list=False)
        print(f"Tag added: {tag.name}")
        await Manager.add_meetings_to_tag(tag, meetings)
        print(f"Meetings added")
        return tag

    @staticmethod
    async def create_meeting(
            name: str, date: datetime, file_recording: str, file_transcript: str, summary: str
    ) -> DB_Meeting:
        meeting = await insert_into_table(
            DB_Meeting(
                name=name,
                date=date,
                file_recording=file_recording,
                file_transcript=file_transcript,
                summary=summary,
                status = "Queued"
            ), always_return_list=False
        )
        print(f"Meeting added: {meeting.name}")
        return meeting

    @staticmethod
    async def create_action_item(item: str, meeting: DB_Meeting):
        return await insert_into_table(DB_ActionItem(text=item, meeting_id=meeting.id))

    @staticmethod
    async def create_key_point(point: str, meeting: DB_Meeting):
        return await insert_into_table(DB_KeyPoint(text=point, meeting_id=meeting.id))

    @staticmethod
    async def add_meetings_to_tag(tag: DB_Tag, meetings: DB_Meeting | list[DB_Meeting]) -> list[DB_MeetingTag]:
        if isinstance(meetings, DB_Meeting):
            return await insert_into_table(DB_MeetingTag(meeting_id=meetings.id, tag_id=tag.id))
        elif isinstance(meetings, list) and len(meetings):
            return await insert_into_table([DB_MeetingTag(meeting_id=meeting.id, tag_id=tag.id) for meeting in meetings])

    @staticmethod
    async def get_tag_meetings(tag: DB_Tag) -> list[DB_Meeting]:
        return await select_with_joins(tag.id, [DB_Tag, DB_MeetingTag, DB_Meeting])

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
    