from __future__ import annotations
from typing import List
from datetime import date
import sys
import os
import asyncio
from backend.manager import Manager
from access import *
from models import *
from setup_test_data import setup_test_data1

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '...')))

manager = Manager()


class Server:

    def __init__(self) -> None:
        self.topics = []
        self.users = []
        self.meetings = []
        self.chats = []

    def upload_meeting(self, data: bytes, filename: str, name: str, date: datetime, attendees: list[User], callback: callable) -> Meeting:

        # result = Meeting(id=rand(), date=date, name=name, file_recording=filename, file_transcript=None, summary=None)

        result = Meeting(data, filename, name, date, attendees, callback)
        self.meetings.append(result)
        return result

    def get_meetings(self) -> list[Meeting]:
        meetings = []
        for meeting in Manager.get_all_meetings():
            meetings.append(Meeting(meeting))
        return meetings

    def get_chats(self) -> list[Chat]:
        return self.chats

        # return self.meetings

    async def create_chat(self, name: str) -> Chat:
        chat = Chat(
            await insert_into_table(
                DB_Chat(
                    name=name
                )
            )
        )
        self.chats.append(chat)
        return chat

    async def create_topic(self, name: str, meetings: list[Meeting]) -> Topic:
        return Topic(
            await insert_into_table(
                DB_Tag(
                    name=name
                )
            )
        )
        result = Topic(asyncio.run(manager.create_tag(name, meetings)))

        # result = Topic(name, meetings, users)
        # self.topics.append(result)

        return result


    def get_topics(self) -> list[Topic]:

        topics = []
        for topic in asyncio.run(manager.get_all_tags()):
            topics.append(Topic(topic))
        return topics

        # return self.topics


class Topic:
    def __init__(self, tag: DB_Tag) -> None:
        self._tag = tag
        self.last_modified = datetime.now()
        self.summary = "AI-generated summary for all meeting under self topic..."
        self.action_items = ["Eat", "Sleep", "Die"]

        
    # def __init__(self, name: str, meetings: list[Meeting], users: list[User]) -> None:
    #     self.name = name
    #     self.users = users
    #     self.last_modified = datetime.now()
    #     self.summary = "AI-generated summary for all meeting under self topic..."
    #     self.action_items = ["Eat", "Sleep", "Die"]

    #     for meeting in self.meetings:
    #         meeting._link_topic(self)


    def get_name(self) -> str:
        return self._tag.name

    def set_name(self, name: str) -> None:
        self._tag.name = name
        update_table(self._tag)
        # self.name = name

    @property
    def meetings(self):
        return select_with_joins(self._tag.name, [DB_MeetingTag, DB_Meeting], )

    def get_meetings(self) -> list[Meeting]:
        return Meeting()
        # return Meeting(Manager.get_tag_meetings(self._tag))
        return self.meetings

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
    def __init__(self, data: bytes, filename: str, name: str, date: datetime, attendees: list[User], callback: callable) -> None:

        # self._obj = backend.Meeting(id=rand(), date=date, name=name, file_recording=filename, file_transcript=None, summary=None)

        self.data = data
        self.filename = filename
        self.name = name
        self.date = date
        self.transcript = "self is the meeting transcript..."
        self.summary = "AI-generated summary for self particular meeting..."

        self.action_items = ["Thing 1", "Thing 2", "Thing 3"]
        self.summary, self.action_items = callback(self.summary, self.action_items)

        self._topics = []

    def get_transcript(self: Meeting) -> str:

        # return self._obj.file_transcript

        return self.transcript

    def get_original_upload(self: Meeting) -> tuple[bytes, str]:
        return (self.data, self.filename)

    def get_meeting_date(self: Meeting) -> datetime:
        # return self._obj.date
        return self.date

    def set_meeting_date(self: Meeting, date: datetime) -> None:
        # self._obj.date = date
        self.date = date

    def get_topics(self: Meeting) -> list[Topic]:
        # TODO: Manager.get_meeting_tags(meeting)
        return self._topics

    def get_meeting_summary(self: Meeting) -> str:

        # return self._obj.summary

        return self.summary


    def get_meeting_action_items(self: Meeting) -> list[str]:
        # TODO: @Rick API or field?
        return self.action_items

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

    def get_messages(self) -> list[Message]:
        return self.messages

    def delete_message(self, message: Message) -> None:
        self.messages.remove(message)

    def get_topics(self) -> list[Topic]:
        return self.topics

    def query(self, message: Message) -> Message:
        self.messages.append(message)
        resp = Message("assistant", "You asked: " + message.get_text())
        self.messages.append(resp)
        return resp

    def get_summary(self) -> str:
        return self.summary

    def get_action_items(self) -> list[str]:
        return self.action_items

    def __str__(self) -> str:
        return self.user.get_name() + "'s chat"


class Message:
    def __init__(self, sender: str, text: str) -> None:
        self.sender = sender
        self.text = text
        self.time = datetime.now()

    def get_sender(self):
        return self.sender

    def get_time(self) -> datetime:
        return self.time

    def get_text(self) -> str:
        return self.text

    def __str__(self) -> str:
        return self.sender.get_name() + ": " + self.text

# def updateSummary(currentSummary, actionItems):
    # print("Current summary is: " + currentSummary)
    # print("Current action items are: " + str(actionItems))
    # newSummary = input("New summary (or ENTER to accept current one):")
    # if newSummary == "":
        # newSummary = currentSummary
    # newActionItems = []
    # print("New action items (empty line to stop entering):")
    # while True:
        # item = input("")
        # if item == "":
            # break
        # newActionItems.append(item)
    # if len(newActionItems) == 0:
        # newActionItems = actionItems
    # return (newSummary, actionItems)


# server = Server()
# me = server.create_user("TestUser", "p@ssword")
# topic = server.create_topic("Executive Meetings", [], [me])
# exec1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Executive Meeting", datetime.now(), [me], updateSummary)
# topic.add_meeting(exec1)


server = Server()

def updateSummary(currentSummary, actionItems):
    return (currentSummary, actionItems)

asyncio.run(setup_test_data1(server))
