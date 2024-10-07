from __future__ import annotations
from typing import List
import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from backend.manager import Manager
import models
from access import *

USE_BACKEND = False

if USE_BACKEND:
    manager = Manager()

class Server:
    def __init__(this) -> None:
        this.topics = []
        this.users = []
        this.meetings = []
        this.chats = []
        this.create_user("assistant", "")

    def create_user(this, name: str, password: str) -> User | None:
        for user in this.users:
            if user.get_name() == name:
                return None
        result = User(name, password)
        this.users.append(result)
        return result

    def get_users(this) -> list[User]:
        return this.users.copy()

    def get_user(this, name: str) -> User | None:
        for user in this.users:
            if user.get_name() == name:
                return user
        return None

    def upload_meeting(this, data: bytes, filename: str, name: str, date: datetime.datetime, attendees: list[User], callback: callable) -> Meeting:
        if USE_BACKEND:
            result = Meeting(id=rand(), date=date, name=name, file_recording=filename, file_transcript=None, summary=None)
        else:
            result = Meeting(data, filename, name, date, attendees, callback)
            this.meetings.append(result)
            return result

    def get_meetings(this) -> list[Meeting]:
        if USE_BACKEND:
            meetings = []
            for meeting in Manager.get_all_meetings():
                meetings.append(Meeting(meeting))
            return meetings
        else:
            return this.meetings.copy()

    def create_topic(this, name: str, meetings: list[Meeting], users: list[User]) -> Topic:
        if USE_BACKEND:
            result = Topic(asyncio.run(manager.create_tag(name, meetings)))
        else:
            result = Topic(name, meetings, users)
            this.topics.append(result)
        return result

    def get_topics(this) -> list[Topic]:
        if USE_BACKEND:
            topics = []
            for topic in asyncio.run(manager.get_all_tags()):
                topics.append(Topic(topic))
            return topics
        else:
            return this.topics.copy()
#endif


class Topic:
    def __init__(this, tag: models.Tag) -> None:
        this._tag = tag
        this.users = users.copy()
        this.last_modified = datetime.datetime.now()
        this.summary = "AI-generated summary for all meeting under this topic..."
        this.action_items = ["Eat", "Sleep", "Die"]
        
    def __init__(this, name: str, meetings: list[Meeting], users: list[User]) -> None:
        this.name = name
        this.meetings = meetings.copy()
        this.users = users.copy()
        this.last_modified = datetime.datetime.now()
        this.summary = "AI-generated summary for all meeting under this topic..."
        this.action_items = ["Eat", "Sleep", "Die"]

        for meeting in this.meetings:
            meeting._link_topic(this)

    def get_name(this) -> str:
        if USE_BACKEND:
            return this._tag.name
        else:
            return this.name

    def set_name(this, name: str) -> None:
        if USE_BACKEND:
            this._tag.name = name
            update_table(this._tag)
        else:
            this.name = name

    def get_meetings(this) -> Meeting:
        if USE_BACKEND:
            return Meeting(Manager.get_tag_meetings(this._tag))
        else:
            return this.meetings.copy()

    def add_meeting(this, meeting: Meeting) -> None:
        if USE_BACKEND:
            Manager.add_meetings_to_tag(this._tag, meeting.get_underlying_object())
        else:
            if meeting not in this.meetings:
                this.meetings.append(meeting)
                meeting._link_topic(this)

            this.last_modified = datetime.datetime.now()

    def remove_meeting(this, meeting: Meeting) -> None:
        if USE_BACKEND:
            this.meetings.remove(meeting)
            meeting._unlink_topic(this)

        this.last_modified = datetime.datetime.now()

    def add_user(this, user: User) -> None:
        if user not in this.users:
            this.users.append(user)
            user._link_topic(this)

    def remove_user(this, user: User) -> None:
        this.users.remove(user)
        user._unlink_topic(this)

    def get_modified_time(this) -> datetime.datetime:
        return this.last_modified

    def get_topic_summary(this):
        return this.summary

    def get_topic_action_items(this):
        return this.action_items.copy()

class Meeting:
    def __init__(this, data: bytes, filename: str, name: str, date: datetime.datetime, attendees: list[User], callback: callable) -> None:
        if USE_BACKEND:
            this._obj = backend.Meeting(id=rand(), date=date, name=name, file_recording=filename, file_transcript=None, summary=None)
        else:
            this.data = data
            this.filename = filename
            this.name = name
            this.date = date
            this.transcript = "This is the meeting transcript..."
            this.summary = "AI-generated summary for this particular meeting..."

            this.attendees = attendees
            this.action_items = ["Thing 1", "Thing 2", "Thing 3"]
            this.summary, this.action_items = callback(this.summary, this.action_items.copy())

            this._topics = []

    def get_transcript(this: Meeting) -> str:
        if USE_BACKEND:
            return this._obj.file_transcript
        else:
            return this.transcript

    def get_original_upload(this: Meeting) -> tuple[bytes, str]:
        return (this.data, this.filename)

    def get_meeting_date(this: Meeting) -> datetime.datetime:
        if USE_BACKEND:
            return this._obj.date
        else:
            return this.date

    def set_meeting_date(this: Meeting, date: datetime.datetime) -> None:
        if USE_BACKEND:
            this._obj.date = date
        else:
            this.date = date

    def get_meeting_name(this: Meeting) -> str:
        if USE_BACKEND:
            return this._obj.name
        else:
            return this.name

    def set_meeting_name(this: Meeting, name: str) -> None:
        if USE_BACKEND:
            this._obj.name = name
        else:
            this.name = name

    def get_topics(this: Meeting) -> list[Topic]:
        # TODO: Manager.get_meeting_tags(meeting)
        return this._topics.copy()

    def get_attendees(this: Meeting) -> list[User]:
        return this.attendees.copy()

    def add_attendee(this: Meeting, attendee: User) -> None:
        if attendee not in this.attendees:
            this.attendees.append(attendee)

    def remove_attendee(this: Meeting, attendee: User) -> None:
        this.attendees.remove(attendee)

    def get_meeting_summary(this: Meeting) -> str:
        if USE_BACKEND:
            return this._obj.summary
        else:
            return this.summary

    def get_meeting_action_items(this: Meeting) -> list[str]:
        # TODO: @Rick API or field?
        return this.action_items.copy()

    def _link_topic(this: Meeting, topic: Topic) -> None:
        if topic not in this._topics:
            this._topics.append(topic)

    def _unlink_topic(this: Meeting, topic: Topic) -> None:
        this._topics.remove(topic)

    def get_underlying_object(this: Meeting) -> backend.Meeting:
        return this._obj


# Most secure thing ever!
class User:
    def __init__(this, name: str, password: str) -> None:
        this.name = name
        this.password = password
        this.topics = []
        this.chats = []

    def get_name(this) -> str:
        return this.name

    def set_name(this, name: str) -> None:
        this.name = name

    def set_password(this, password: str) -> None:
        this.password = password

    def authenticate(this, password: str) -> bool:
        return this.password == password

    def get_chats(this) -> list[Chat]:
        return this.chats.copy()

    def add_chat(this, chat: Chat) -> None:
        if chat not in this.chats:
            this.chats.append(chat)

    def remove_chat(this, chat: Chat) -> None:
        this.chats.remove(chat)

    def get_accessible_topics(this) -> list[Topic]:
        return this.topics.copy()

    def __str__(this) -> str:
        return this.name

class Chat:
    def __init__(this, user: User, topics: list[Topic]) -> None:
        this.user = user
        this.topics = topics.copy()
        this.messages = []
        this.summary = "Summary for all meetings in all selected topics..."
        this.action_items = ["Hi", "Hello", "G'day"]

    def get_user(this) -> User:
        return this.user

    def get_messages(this) -> list[Message]:
        return this.messages.copy()

    def delete_message(this, message: Message) -> None:
        this.messages.remove(message)

    def get_topics(this) -> list[Topic]:
        return this.topics.copy()

    def query(this, message: Message) -> Message:
        this.messages.append(message)
        resp = Message(User("assistant", ""), "You asked: " + message.get_text())
        this.messages.append(resp)
        return resp

    def get_summary(this) -> str:
        return this.summary

    def get_action_items(this) -> list[str]:
        return this.action_items.copy()

    def __str__(this) -> str:
        return this.user.get_name() + "'s chat"

class Message:
    def __init__(this, sender: User, text: str) -> None:
        this.sender = sender
        this.text = text
        this.time = datetime.datetime.now()

    def get_sender(this) -> User:
        return this.sender

    def get_time(this) -> datetime.datetime:
        return this.time

    def get_text(this) -> str:
        return this.text

    def __str__(this) -> str:
        return this.sender.get_name() + ": " + this.text

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

def updateSummary(currentSummary, actionItems):
    return (currentSummary, actionItems)


# server = Server()
# me = server.create_user("TestUser", "p@ssword")
# topic = server.create_topic("Executive Meetings", [], [me])
# exec1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Executive Meeting", datetime.datetime.now(), [me], updateSummary)
# topic.add_meeting(exec1)


server = Server()

users = server.get_users()
user = None
if len(users) < 2:
    user = server.create_user("user", "p@ssword")
else:
    user = users[1]

if not USE_BACKEND:
    # set up the static state
    topic = server.create_topic("Executive Meetings", [], [user])
    exec1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Executive Meeting", datetime.datetime.now(), [user], updateSummary)
    exec2 = server.upload_meeting(b'Hello World!', "meeting.txt", "Second Executive Meeting", datetime.datetime.now(), [user], updateSummary)
    topic.add_meeting(exec1)
    topic.add_meeting(exec2)
    topic2 = server.create_topic("Marketing Meetings", [], [user])
    mark1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Marketing Meeting", datetime.datetime.now(), [user], updateSummary)
    mark2 = server.upload_meeting(b'Hello World!', "meeting.txt", "Second Marketing Meeting", datetime.datetime.now(), [user], updateSummary)
    topic2.add_meeting(mark1)
    topic2.add_meeting(mark2)

    chat = Chat(user, [topic])
    user.add_chat(chat)
    chat2 = Chat(user, [topic2])
    user.add_chat(chat2)

    chat.query(Message(chat.get_user(), "What's my name?"))
    chat.query(Message(chat.get_user(), "How are you?"))
    chat2.query(Message(chat.get_user(), "How much money did we get?"))
    chat2.query(Message(chat.get_user(), "When is this due?"))
