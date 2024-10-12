import os
import sys

import logging
from datetime import datetime

from .RAG import RAG

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import DB_Meeting, DB_MeetingTag, DB_Tag
from models import DB_ActionItem, DB_KeyPoint
from access import select_many_from_table, insert_into_table, select_with_joins


class Manager:
    _logger = logging.getLogger(__name__)

    def __init__(self):
        self.rag = RAG()

    @staticmethod
    async def get_all_meetings() -> list[DB_Meeting]:
        return await select_many_from_table(DB_Meeting)

    @staticmethod
    async def get_all_tags() -> list[DB_Tag]:
        return await select_many_from_table(DB_Tag)

    @classmethod
    async def create_tag(cls, name, meetings: list[DB_Meeting]) -> DB_Tag:
        tag = await insert_into_table(
            DB_Tag(name=name, last_modified=datetime.now()),
            always_return_list=False
        )
        cls._logger.debug(f"Tag added: {tag.name}")
        await Manager.add_meetings_to_tag(tag, meetings)
        cls._logger.debug(f"Meetings added to {tag.name}")
        return tag

    @classmethod
    async def create_meeting(
            cls, name: str, date: datetime, file_recording: str,
            file_transcript: str, summary: str
    ) -> DB_Meeting:
        meeting = await insert_into_table(
            DB_Meeting(
                name=name,
                date=date,
                file_recording=file_recording,
                file_transcript=file_transcript,
                summary=summary,
                status="Queued"
            ), always_return_list=False
        )
        cls._logger.debug(f"Meeting added: {meeting.name}")
        return meeting

    @staticmethod
    async def create_action_item(item: str, meeting: DB_Meeting):
        return await insert_into_table(
            DB_ActionItem(text=item, meeting_id=meeting.id)
        )

    @staticmethod
    async def create_key_point(point: str, meeting: DB_Meeting):
        return await insert_into_table(
            DB_KeyPoint(text=point, meeting_id=meeting.id)
        )

    @staticmethod
    async def add_meetings_to_tag(
            tag: DB_Tag, meetings: DB_Meeting | list[DB_Meeting]
    ) -> list[DB_MeetingTag]:

        if isinstance(meetings, DB_Meeting):
            return await insert_into_table(
                DB_MeetingTag(meeting_id=meetings.id, tag_id=tag.id)
            )
        elif isinstance(meetings, list) and len(meetings):
            meeting_tags = []
            for meeting in meetings:
                meeting_tags.append(
                    DB_MeetingTag(meeting_id=meeting.id, tag_id=tag.id)
                )
            return await insert_into_table(meeting_tags)

    @staticmethod
    async def get_tag_meetings(tag: DB_Tag) -> list[DB_Meeting]:
        meetings = await select_with_joins(
            tag.id, [DB_Tag, DB_MeetingTag, DB_Meeting]
        )
        return meetings
