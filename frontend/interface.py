from __future__ import annotations
from typing import List
import datetime

class Server:
    def __init__(this) -> None:
        this.topics = []
        this.users = []
        this.meetings = []
        this.chats = []
        this.create_user("ChatBot", "")

    def create_user(this, name: str, password: str) -> User | None:
        for user in this.users:
            if user.get_name() == name:
                return None
        result = User(name, password)
        this.users.append(result)
        return result

    def get_users(this) -> list[User]:
        return this.users.copy()

    def upload_meeting(this, data: bytes, filename: str, name: str, date: datetime.datetime, attendees: list[User], callback: callable) -> Meeting:
        result = Meeting(data, filename, name, date, attendees, callback)
        this.meetings.append(result)
        return result

    def get_meetings(this) -> list[Meeting]:
        return this.meetings.copy()

    def create_topic(this, name: str, meetings: list[Meeting], users: list[User]) -> Topic:
        result = Topic(name, meetings, users)
        this.topics.append(result)
        return result

    def get_topics(this) -> list[Topic]:
        return this.topics.copy()

class Topic:
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
        return this.name

    def set_name(this, name: str) -> None:
        this.name = name

    def get_meetings(this) -> Meeting:
        return this.meetings.copy()

    def add_meeting(this, meeting: Meeting) -> None:
        if meeting not in this.meetings:
            this.meetings.append(meeting)
            meeting._link_topic(this)
            this.last_modified = datetime.datetime.now()

    def remove_meeting(this, meeting: Meeting) -> None:
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
        this.data = data
        this.filename = filename
        this.name = name
        this.date = date
        this.attendees = attendees
        this.transcript = "This is the meeting transcript..."
        this.summary = "AI-generated summary for this particular meeting..."
        this.action_items = ["Thing 1", "Thing 2", "Thing 3"]
        this.summary, this.action_items = callback(this.summary, this.action_items.copy())

        this._topics = []

    def get_transcript(this: Meeting) -> str:
        return this.transcript

    def get_original_upload(this: Meeting) -> tuple[bytes, str]:
        return (this.data, this.filename)

    def get_meeting_date(this: Meeting) -> datetime.datetime:
        return this.date

    def set_meeting_date(this: Meeting, date: datetime.datetime) -> None:
        this.date = date

    def get_meeting_name(this: Meeting) -> str:
        return this.name

    def set_meeting_name(this: Meeting, name: str) -> None:
        this.name = name

    def get_topics(this: Meeting) -> list[Topic]:
        return this._topics.copy()

    def get_attendees(this: Meeting) -> list[User]:
        return this.attendees.copy()

    def add_attendee(this: Meeting, attendee: User) -> None:
        if attendee not in this.attendees:
            this.attendees.append(attendee)

    def remove_attendee(this: Meeting, attendee: User) -> None:
        this.attendees.remove(attendee)

    def get_meeting_summary(this: Meeting) -> str:
        return this.summary

    def get_meeting_action_items(this: Meeting) -> list[str]:
        return this.action_items.copy()

    def _link_topic(this: Meeting, topic: Topic) -> None:
        if topic not in this._topics:
            this._topics.append(topic)

    def _unlink_topic(this: Meeting, topic: Topic) -> None:
        this._topics.remove(topic)

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
        resp = Message(User("ChatBot", ""), "AI response haha.")
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


# server = Server()
# me = server.create_user("TestUser", "p@ssword")
# topic = server.create_topic("Executive Meetings", [], [me])
# exec1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Executive Meeting", datetime.datetime.now(), [me], updateSummary)
# topic.add_meeting(exec1)


server = Server()

users = server.get_users()
user = None
if len(users) < 2:
    user = server.create_user("TestUser", "p@ssword")
else:
    user = users[1]

def updateSummary(currentSummary, actionItems):
    return (currentSummary, actionItems)

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
