from __future__ import annotations
from typing import List
from datetime import datetime
import asyncio

from MIS.access import select_many_from_table, AccessBase, select_from_table
from MIS.access import insert_into_table, select_with_joins
from MIS.access import update_table_from_model
from MIS.models import DB_Meeting, DB_Tag, DB_Chat, DB_MeetingTag, DB_ChatTag
from MIS.models import DB_ActionItem
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from MIS.backend.RAG import RAG


@st.cache_resource  # 👈 Add the caching decorator
def get_rag():
    print("getting rag")
    return RAG()


rag = get_rag()


class Server:

    @staticmethod
    async def get_all_meetings() -> List[Meeting]:
        """Returns a meetings in the database, with each wrapped around in a
        Meeting object."""
        return [Meeting(m) for m in await select_many_from_table(DB_Meeting)]

    @staticmethod
    async def get_all_topics() -> List[Topic]:
        """Returns all topics in the database, with each wrapped in a Topic
        object."""
        return [Topic(t) for t in await select_many_from_table(DB_Tag)]

    @staticmethod
    async def get_all_chats() -> List[Chat]:
        """Returns a list of chats, with most recently added chat at the
        beginning."""
        return list(
            reversed([Chat(c) for c in await select_many_from_table(DB_Chat)])
        )

    @staticmethod
    async def get_latest_chats() -> Chat:
        """Returns the latest chat."""
        return Chat(
            await AccessBase.db_fetchone(
                """
                    SELECT * FROM chat
                    ORDER BY id
                    DESC LIMIT 1;
                """,
                function=lambda f: DB_Chat(**f)
            )
        )

    @staticmethod
    async def get_chat_by_id(id: int) -> Chat:
        """Gets a Chat object for the chat based on its ID."""
        return Chat(await select_from_table(DB_Chat, id))

    @staticmethod
    async def get_meeting_by_id(id: int) -> Meeting:
        """Gets a Meeting object based on its ID."""
        return Meeting(await select_from_table(DB_Meeting, id))

    @staticmethod
    async def upload_meeting(
            name: str, date: datetime, file: UploadedFile, topics: List[Topic]
    ) -> Meeting:
        """Uploads a meeting to the database, and returns a Meeting object
        which captures the meeting."""
        filename = "data/recordings/" + file.name
        with open(filename, "wb") as audiofile:
            audiofile.write(file.read())
        meeting = Meeting(
            await insert_into_table(
                DB_Meeting(
                    name=name,
                    date=date,
                    file_recording=filename,
                    file_transcript=None,
                    summary="",
                ), always_return_list=False
            )
        )

        await insert_into_table(
            [
                DB_MeetingTag(
                    meeting_id=meeting.id,
                    tag_id=topic.id
                ) for topic in topics
            ]
        )
        return meeting

    @staticmethod
    async def get_meetings_by_name(meeting_names: List[str]) -> List[Meeting]:
        """Gets a list of meetings based on the meeting name."""
        return [
            Meeting(m) for m in await select_many_from_table(
                DB_Meeting, meeting_names, "name"
            )
        ]

    @staticmethod
    async def create_chat(name: str, topics: List[Topic]) -> Chat:
        """Creates a new chat and returns it as a Chat object."""
        chat = Chat(
            await insert_into_table(
                DB_Chat(
                    name=name
                )
            )
        )
        await insert_into_table(
            [
                DB_ChatTag(
                    chat_id=chat.id,
                    tag_id=topic.id
                ) for topic in topics
            ]
        )
        return chat

    @staticmethod
    async def create_topic(name: str, meetings: List[Meeting]) -> Topic:
        """Creates a new topic and returns it as a Topic object."""
        topic = Topic(
            await insert_into_table(
                DB_Tag(
                    name=name
                )
            )
        )
        await insert_into_table(
            [
                DB_MeetingTag(
                    meeting_id=meeting.id,
                    tag_id=topic.id
                ) for meeting in meetings
            ]
        )
        return Topic


class Topic:
    def __init__(self, tag: DB_Tag) -> None:
        self._tag = tag

    @property
    def id(self) -> int:
        """Gets the ID of a topic."""
        return self._tag.id

    @property
    def name(self) -> str:
        """Gets the name of a topic."""
        return self._tag.name

    @name.setter
    async def name(self, value: str) -> None:
        """Sets the name of a topic."""
        self._tag.name = value
        self._tag = await update_table_from_model(self._tag)

    @property
    async def meetings(self):
        """Gets the list of meetings which have been put under this
        particular topic."""
        return await select_with_joins(
            self._tag.name, [DB_MeetingTag, DB_Meeting]
        )

    @property
    async def action_items(self):
        """Gets the list of action items collated from the meetings in this
        topic."""
        return await select_with_joins(
            self._tag.name, [DB_MeetingTag, DB_Meeting, DB_ActionItem]
        )

    async def add_meeting(self, meeting: DB_Meeting) -> None:
        """Adds a meeting to this topic."""
        await insert_into_table(
            DB_MeetingTag(
                meeting_id=meeting.id,
                tag_id=self._tag.id
            )
        )

    def remove_meeting(self, meeting: Meeting) -> None:
        """Removes a meeting from the topic."""
        self.meetings.remove(meeting)
        meeting._unlink_topic(self)

        self.last_modified = datetime.now()

    def get_modified_time(self) -> datetime:
        """Gets the last modified time of the topic - when a meeting was last
        added or removed."""
        return self.last_modified

    def get_topic_summary(self):
        """Returns the summary of all meetings in the topic."""
        return self.summary

    def get_topic_action_items(self):
        """Public accessor for the action_items property."""
        return self.action_items


class Meeting:
    def __init__(self, meeting: DB_Meeting) -> None:
        self._meeting = meeting

    @property
    def id(self) -> int:
        """Gets the ID of a meeting object."""
        return self._meeting.id

    @property
    def name(self) -> str:
        """Gets the name of a meeting object."""
        return self._meeting.name

    @property
    def transcript(self) -> str:
        """Gets the transcript for a meeting."""
        return self._meeting.file_transcript

    @property
    def date(self: Meeting) -> datetime:
        """Gets the date of the meeting."""
        return self._meeting.date

    @property
    async def topics(self: Meeting) -> List[Topic]:
        """Gets the list of topics which the meeting belongs to."""
        return [
            Topic(t) for t in await select_with_joins(
                self._meeting.id, [DB_Meeting, DB_MeetingTag, DB_Tag]
            )
        ]

    @property
    def summary(self: Meeting) -> str:
        """Gets the summary for this particular meeting."""
        return self._meeting.summary

    @property
    async def action_items(self: Meeting) -> List[str]:
        """Gets the list of action items for this particular meeting."""
        return [
            a.text for a in await select_with_joins(
                self._meeting.id,
                [DB_Meeting, DB_ActionItem]
            )
        ]

    def get_original_upload(self: Meeting) -> str:
        """Gets the original upload for this meeting."""
        return self._meeting.file_recording

    # def _link_topic(self: Meeting, topic: Topic) -> None:
    #     if topic not in self.topics:
    #         self._topics.append(topic)

    # def _unlink_topic(self: Meeting, topic: Topic) -> None:
    #     self._topics.remove(topic)

    # def get_underlying_object(self: Meeting) -> backend.Meeting:
        # return self._obj


class Chat:
    def __hash__(self) -> int:
        return self._chat.id

    def __init__(self, chat: DB_Chat) -> None:
        self._chat = chat

    @property
    def id(self):
        """Gets the ID for the chat."""
        return self._chat.id

    @property
    def name(self):
        """Gets the name of the chat."""
        return self._chat.name

    @property
    def history(self):
        """Gets the message history for the chat."""
        return self._chat.history

    @property
    async def topics(self) -> List[Topic]:
        """Gets the list of topics which the chat includes."""
        return [
            Topic(t) for t in await select_with_joins(
                self._chat.id, [DB_Chat, DB_ChatTag, DB_Tag]
            )
        ]

    @property
    async def meetings(self) -> List[Meeting]:
        """Gets the list of meetings accesssible by the chat."""
        return [
            Meeting(m) for m in await select_with_joins(
                self._chat.id,
                [DB_Chat, DB_ChatTag, DB_Tag, DB_MeetingTag, DB_Meeting]
            )
        ]

    @property
    async def action_items(self) -> List[str]:
        """Gets the list of action items for the chat, based on the topics
        associated with the chat."""
        return [
            a.text for a in await select_with_joins(
                self._chat.id,
                [DB_Chat, DB_ChatTag, DB_Tag, DB_MeetingTag,
                 DB_Meeting, DB_ActionItem]
            )
        ]

    @property
    @st.cache_data(hash_funcs={"MIS.frontend.interface.Chat": __hash__})
    def summary(self) -> str:
        """Returns the summary for all meetings in the chat."""
        print("summarising")
        return rag.summarise_chat(
            [m.summary for m in asyncio.run(self.meetings)]
        )

        # result = ""
        # for meeting in asyncio.run(self.meetings):
        #     result += meeting.get_meeting_summary() + "\n\n"
        # return result.strip()
        # return f"Summary for \"{self.name}\" (" + str(self.id) + ") Go HERE"

    async def add_message(self, username, message):
        """Adds a message to the chat history."""
        self._chat.history.append(
            {
                "username": username,
                "message": message
            }
        )
        return await update_table_from_model(self._chat)

    async def send_message(self, text):
        """Sends a message to the chatbot/server."""
        return await rag.query_retrieval(
            text, [m.id for m in await self.meetings]
        )  # chat_input  #

    def get_action_items(self) -> List[str]:
        """Gets the list of action items from the topics associated with the
        chat."""
        result = []
        for meeting in asyncio.run(self.meetings):
            result += asyncio.run(meeting.action_items)
        return result
        # return ["thing 1", "thing 2"]


# server = Server()
# me = server.create_user("TestUser", "p@ssword")
# topic = server.create_topic("Executive Meetings", [], [me])
# exec1 = server.upload_meeting(b'Hello World!', "meeting.txt",
#                               "First Executive Meeting",
#                               datetime.now(), [me], updateSummary)
# topic.add_meeting(exec1)


server = Server()


def updateSummary(currentSummary, actionItems):
    return (currentSummary, actionItems)

# asyncio.run(setup_test_data1(server))
