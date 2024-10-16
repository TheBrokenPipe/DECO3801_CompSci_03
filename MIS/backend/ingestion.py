import os
import logging

from ..models import DB_Meeting
from ..access import select_many_from_table, update_table_from_model
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
        meetings = await select_many_from_table(
            DB_Meeting, ["Queued"], ("status")
        )
        if not len(meetings) > 0:
            return

        meeting = meetings[0]
        recording = meeting.file_recording
        meeting.file_transcript = self.asr.transcribe_audio_file(recording)
        meeting.status = "Transcribed"
        await update_table_from_model(meeting)

    async def summarise_next_meeting(self):
        meetings = await select_many_from_table(
            DB_Meeting, ["Transcribed"], ("status")
        )
        if not len(meetings) > 0:
            return

        meeting = meetings[0]
        self.logger.debug(f"Starting summarisation of {meeting.name}")
        with open(meeting.file_transcript, 'r', encoding="utf-8") as file:
            transcript = file.read()

        summary = self.manager.rag.summarise_meeting(transcript)
        self.logger.debug(summary)

        action_items = summary["action_items"]
        if action_items is None:
            self.logger.warning(
                f"Action item extraction failed for meeting id {meeting.id}"
            )
        else:
            for action_item in action_items.action_items:
                await self.manager.create_action_item(action_item, meeting)

        key_points = summary["key_points"]
        if key_points is None:
            self.logger.warning(
                f"Key points extraction failed for meeting id {meeting.id}"
            )
        else:
            for key_point in key_points.key_points:
                await self.manager.create_key_point(key_point, meeting)

        meeting.summary = summary["abstract_summary"]
        meeting.status = "Summarised"
        await update_table_from_model(meeting)

    async def ingest_next_meeting(self):
        meetings = await select_many_from_table(
            DB_Meeting, ["Summarised"], ("status")
        )
        if not len(meetings) > 0:
            return

        meeting = meetings[0]
        chunks = self.chunks.chunk_transcript(meeting)

        self.manager.rag.embed_meeting(meeting, chunks)

        meeting.status = "Ready"
        await update_table_from_model(meeting)
