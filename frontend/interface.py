from __future__ import annotations
from typing import List
from datetime import date
import sys
import os
import asyncio
from backend.manager import Manager
from access import *
from models import *
from streamlit.runtime.uploaded_file_manager import UploadedFile
from setup_test_data import setup_test_data1

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '...')))

manager = Manager()


class Server:

    @staticmethod
    async def get_all_meetings() -> list[Meeting]:
        return [Meeting(m) for m in await select_many_from_table(DB_Meeting)]

    @staticmethod
    async def get_all_topics() -> list[Topic]:
        return [Topic(t) for t in await select_many_from_table(DB_Tag)]

    @staticmethod
    async def get_all_chats() -> list[Chat]:
        return [Chat(c) for c in await select_many_from_table(DB_Chat)]

    @staticmethod
    async def get_chat_by_id(id):
        return Chat(await select_from_table(DB_Chat, id))

    @staticmethod
    async def upload_meeting(name: str, date: datetime, file: UploadedFile) -> Meeting:
        filename = "data/recordings/" + file.name
        with open(filename, "wb") as audiofile:
            audiofile.write(file.read())
        return Meeting(
            await insert_into_table(
                DB_Meeting(
                    name=name,
                    date=date,
                    file_recording=filename,
                    file_transcript="file_transcript",
                    summary="",
                ), always_return_list=False
            )
        )

    @staticmethod
    async def create_chat(name: str) -> Chat:
        return Chat(
            await insert_into_table(
                DB_Chat(
                    name=name
                )
            )
        )

    @staticmethod
    async def create_topic(name: str, meetings: list[Meeting]) -> Topic:
        return Topic(
            await insert_into_table(
                DB_Tag(
                    name=name
                )
            )
        )


class Topic:
    def __init__(self, tag: DB_Tag) -> None:
        self._tag = tag
        # self.last_modified = datetime.now()
        # self.summary = "AI-generated summary for all meeting under self topic..."
        # self.action_items = ["Eat", "Sleep", "Die"]

    @property
    def name(self) -> str:
        return self._tag.name

    @name.setter
    async def set_name(self, value: str) -> None:
        self._tag.name = value
        self._tag = await update_table_from_model(self._tag)

    @property
    def meetings(self):
        return select_with_joins(self._tag.name, [DB_MeetingTag, DB_Meeting])

    async def add_meeting(self, meeting: DB_Meeting) -> None:
        await insert_into_table(
            DB_MeetingTag(
                meeting_id=meeting.id,
                tag_id=self._tag.id
            )
        )

    def remove_meeting(self, meeting: Meeting) -> None:

        self.meetings.remove(meeting)
        meeting._unlink_topic(self)

        self.last_modified = datetime.now()

    def get_modified_time(self) -> datetime:
        return self.last_modified

    def get_topic_summary(self):
        return self.summary

    def get_topic_action_items(self):
        return self.action_items


class Meeting:
    def __init__(self, meeting: DB_Meeting) -> None:
        self._meeting = meeting
        pass

    def get_transcript(self: Meeting) -> str:
        return self._meeting.file_transcript

    def get_original_upload(self: Meeting) -> tuple[bytes, str]:
        return self._meeting.file_recording

    def get_meeting_date(self: Meeting) -> datetime:
        return self._meeting.date
    
    def get_meeting_name(self: Meeting) -> str:
        return self._meeting.name

    @property
    async def topics(self: Meeting) -> list[Topic]:
        return [
            Topic(t) for t in await select_with_joins(
                self._meeting.id, [DB_Meeting, DB_MeetingTag, DB_Tag]
            )
        ]

    def get_meeting_summary(self: Meeting) -> str:
        return self._meeting.summary

    @property
    async def action_items(self: Meeting) -> list[str]:
        return ["ACTION!!!"]
        return [
            Topic(t) for t in await select_with_joins(
                self._meeting.id, [DB_Meeting, DB_MeetingTag, DB_Tag]
            )
        ]

    def _link_topic(self: Meeting, topic: Topic) -> None:
        if topic not in self._topics:
            self._topics.append(topic)

    def _unlink_topic(self: Meeting, topic: Topic) -> None:
        self._topics.remove(topic)


    # def get_underlying_object(self: Meeting) -> backend.Meeting:
        # return self._obj


class Chat:
    def __init__(self, chat: DB_Chat, topics: list[Topic] = None) -> None:
        self._chat = chat
        self.topics = topics
        self.messages = []
        self.summary = "Summary for all meetings in all selected topics..."
        self.action_items = ["Hi", "Hello", "G'day"]

    @property
    def id(self):
        return self._chat.id

    @property
    def name(self):
        return self._chat.name

    @property
    def history(self):
        return self._chat.history

    async def add_message(self, username, message):
        self._chat.history.append(
            {
                "username": username,
                "message": message
            }
        )
        return await update_table_from_model(self._chat)

    async def topics(self) -> list[Topic]:
        return [
            Topic(t) for t in await select_with_joins(
                self._chat.id, [DB_Chat, DB_MeetingTag, DB_Tag]
            )
        ]

    def get_summary(self) -> str:
        return self.summary

    def get_action_items(self) -> list[str]:
        return self.action_items

    def __str__(self) -> str:
        return self.user.get_name() + "'s chat"


# server = Server()
# me = server.create_user("TestUser", "p@ssword")
# topic = server.create_topic("Executive Meetings", [], [me])
# exec1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Executive Meeting", datetime.now(), [me], updateSummary)
# topic.add_meeting(exec1)


server = Server()

def updateSummary(currentSummary, actionItems):
    return (currentSummary, actionItems)

# asyncio.run(setup_test_data1(server))
