import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import *
from access import *
from .ASR import ASR
from .manager import Manager

class Ingestion:
    def __init__(self):
        self.manager = Manager()
        self.asr = ASR(os.environ['HF_TOKEN'])
        self.logger = logging.getLogger(__name__)

    async def ingest_next_meeting(self):
        meetings = await select_ingestion_meeting(Meeting,(""),("summary"))
        if len(meetings) > 0:
            meeting = meetings[0]
            with open(meeting.file_transcript, 'r', encoding="utf-8") as file:
                transcript = file.read()

            full_summary = self.manager.rag.summarise_meeting(transcript)
            self.logger.debug(full_summary)

            meeting.summary = full_summary['abstract_summary']
            await update_table(meeting)

            for action_item in full_summary['action_items'].action_items:
                await self.manager.create_action_item(action_item, meeting)

            for key_point in full_summary['key_points'].key_points:
                await self.manager.create_key_point(key_point, meeting)
            
            # TODO: RAG chunking and embedding goes here
            
    async def transcribe_next_meeting(self):
        meetings = await select_many_from_table(Meeting,(""),("file_transcript"))
        if len(meetings) > 0:
            meeting = meetings[0]
            recording = meeting.file_recording
            meeting.file_transcript = self.asr.transcribe_audio_file(recording)
            await update_table(meeting)
    

