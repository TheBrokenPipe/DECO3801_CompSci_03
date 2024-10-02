import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import *
from access import *
from .ASR import ASR
from .manager import Manager
from .chunking import Chunks


class Ingestion:
    def __init__(self):
        self.manager = Manager()
        self.asr = ASR(os.environ['HF_TOKEN'])
        self.chunks = Chunks()
        self.logger = logging.getLogger(__name__)

    async def transcribe_next_meeting(self):
        meetings = await select_many_from_table(Meeting, ["Queued"], "status")
        if not len(meetings) > 0:
            return
        
        meeting = meetings[0]
        recording = meeting.file_recording
        meeting.file_transcript = self.asr.transcribe_audio_file(recording)
        meeting.status = "Transcribed"
        await update_table(meeting)

    async def summarise_next_meeting(self):
        meetings = await select_many_from_table(Meeting, ["Transcribed"],("status"))
        if not len(meetings) > 0:
            return
    
        meeting = meetings[0]
        with open(meeting.file_transcript, 'r', encoding="utf-8") as file:
            transcript = file.read()

        summary = self.manager.rag.summarise_meeting(transcript)
        self.logger.debug(summary)

        action_items = summary["action_items"]
        if action_items is None:
            self.logger.warning("Failed to extract action items meeting id {meeting.id}")
        else:
            for action_item in action_items.action_items:
                await self.manager.create_action_item(action_item, meeting)

        key_points = summary["key_points"]
        if key_points is None:
            self.logger.warning("Failed to extract key points meeting id {meeting.id}")
        else:
            for key_point in key_points.key_points:
                await self.manager.create_key_point(key_point, meeting)

        meeting.summary = summary["abstract_summary"]
        meeting.status = "Summarised"
        await update_table(meeting)

    async def ingest_next_meeting(self):
        meetings = await select_many_from_table(Meeting, ["Summarised"],("status"))
        if not len(meetings) > 0:
            return
        
        meeting = meetings[0]
        chunks = self.chunks.chunk_transcript(meeting)
        
        self.manager.rag.embed_meeting(meeting, chunks)

        meeting.status = "Ready"
        await update_table(meeting)
