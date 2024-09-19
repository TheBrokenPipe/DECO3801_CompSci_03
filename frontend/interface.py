from __future__ import annotations
from typing import List
import datetime


class Server:
    def __init__(self) -> None:
        self.topics = []
        self.users = []
        self.meetings = []
        self.chats = []
        self.create_user("assistant", "")

    def create_user(self, name: str, password: str) -> User | None:
        for user in self.users:
            if user.get_name() == name:
                return None
        result = User(name, password)
        self.users.append(result)
        return result

    def get_users(self) -> list[User]:
        return self.users.copy()

    def get_user(self, name: str) -> User | None:
        for user in self.users:
            if user.get_name() == name:
                return user
        return None

    def upload_meeting(self, data: bytes, filename: str, name: str, date: datetime.datetime, attendees: list[User], callback: callable) -> Meeting:
        result = Meeting(data, filename, name, date, attendees, callback)
        self.meetings.append(result)
        return result

    def get_meetings(self) -> list[Meeting]:
        return self.meetings.copy()

    def create_topic(self, name: str, meetings: list[Meeting], users: list[User]) -> Topic:
        result = Topic(name, meetings, users)
        self.topics.append(result)
        return result

    def get_topics(self) -> list[Topic]:
        return self.topics.copy()


class Topic:
    def __init__(self, name: str, meetings: list[Meeting], users: list[User]) -> None:
        self.name = name
        self.meetings = meetings.copy()
        self.users = users.copy()
        self.last_modified = datetime.datetime.now()
        self.summary = "AI-generated summary for all meeting under self topic..."
        self.action_items = ["Eat", "Sleep", "Die"]

        for meeting in self.meetings:
            meeting._link_topic(self)

    def get_name(self) -> str:
        return self.name

    def set_name(self, name: str) -> None:
        self.name = name

    def get_meetings(self) -> Meeting:
        return self.meetings.copy()

    def add_meeting(self, meeting: Meeting) -> None:
        if meeting not in self.meetings:
            self.meetings.append(meeting)
            meeting._link_topic(self)
            self.last_modified = datetime.datetime.now()

    def remove_meeting(self, meeting: Meeting) -> None:
        self.meetings.remove(meeting)
        meeting._unlink_topic(self)
        self.last_modified = datetime.datetime.now()

    def add_user(self, user: User) -> None:
        if user not in self.users:
            self.users.append(user)
            user._link_topic(self)

    def remove_user(self, user: User) -> None:
        self.users.remove(user)
        user._unlink_topic(self)

    def get_modified_time(self) -> datetime.datetime:
        return self.last_modified

    def get_topic_summary(self):
        return self.summary

    def get_topic_action_items(self):
        return self.action_items.copy()

class Meeting:
    def __init__(self, data: bytes, filename: str, name: str, date: datetime.datetime, attendees: list[User], callback: callable) -> None:
        self.data = data
        self.filename = filename
        self.name = name
        self.date = date
        self.attendees = attendees
        self.transcript = "self is the meeting transcript..."
        self.summary = "AI-generated summary for self particular meeting..."
        self.action_items = ["Thing 1", "Thing 2", "Thing 3"]
        self.summary, self.action_items = callback(self.summary, self.action_items.copy())

        self._topics = []

    def get_transcript(self: Meeting) -> str:
        return self.transcript

    def get_original_upload(self: Meeting) -> tuple[bytes, str]:
        return (self.data, self.filename)

    def get_meeting_date(self: Meeting) -> datetime.datetime:
        return self.date

    def set_meeting_date(self: Meeting, date: datetime.datetime) -> None:
        self.date = date

    def get_meeting_name(self: Meeting) -> str:
        return self.name

    def set_meeting_name(self: Meeting, name: str) -> None:
        self.name = name

    def get_topics(self: Meeting) -> list[Topic]:
        return self._topics.copy()

    def get_attendees(self: Meeting) -> list[User]:
        return self.attendees.copy()

    def add_attendee(self: Meeting, attendee: User) -> None:
        if attendee not in self.attendees:
            self.attendees.append(attendee)

    def remove_attendee(self: Meeting, attendee: User) -> None:
        self.attendees.remove(attendee)

    def get_meeting_summary(self: Meeting) -> str:
        return self.summary

    def get_meeting_action_items(self: Meeting) -> list[str]:
        return self.action_items.copy()

    def _link_topic(self: Meeting, topic: Topic) -> None:
        if topic not in self._topics:
            self._topics.append(topic)

    def _unlink_topic(self: Meeting, topic: Topic) -> None:
        self._topics.remove(topic)

# Most secure thing ever!
class User:
    def __init__(self, name: str, password: str) -> None:
        self.name = name
        self.password = password
        self.topics = []
        self.chats = []

    def get_name(self) -> str:
        return self.name

    def set_name(self, name: str) -> None:
        self.name = name

    def set_password(self, password: str) -> None:
        self.password = password

    def authenticate(self, password: str) -> bool:
        return self.password == password

    def get_chats(self) -> list[Chat]:
        return self.chats.copy()

    def add_chat(self, chat: Chat) -> None:
        if chat not in self.chats:
            self.chats.append(chat)

    def remove_chat(self, chat: Chat) -> None:
        self.chats.remove(chat)

    def get_accessible_topics(self) -> list[Topic]:
        return self.topics.copy()

    def __str__(self) -> str:
        return self.name

class Chat:
    def __init__(self, user: User, topics: list[Topic]) -> None:
        self.user = user
        self.topics = topics.copy()
        self.messages = []
        self.summary = "Summary for all meetings in all selected topics..."
        self.action_items = ["Hi", "Hello", "G'day"]

    def get_user(self) -> User:
        return self.user

    def get_messages(self) -> list[Message]:
        return self.messages.copy()

    def delete_message(self, message: Message) -> None:
        self.messages.remove(message)

    def get_topics(self) -> list[Topic]:
        return self.topics.copy()

    def query(self, message: Message) -> Message:
        self.messages.append(message)
        resp = Message(User("assistant", ""), "You asked: " + message.get_text())
        self.messages.append(resp)
        return resp

    def get_summary(self) -> str:
        return self.summary

    def get_action_items(self) -> list[str]:
        return self.action_items.copy()

    def __str__(self) -> str:
        return self.user.get_name() + "'s chat"

class Message:
    def __init__(self, sender: User, text: str) -> None:
        self.sender = sender
        self.text = text
        self.time = datetime.datetime.now()

    def get_sender(self) -> User:
        return self.sender

    def get_time(self) -> datetime.datetime:
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
# exec1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Executive Meeting", datetime.datetime.now(), [me], updateSummary)
# topic.add_meeting(exec1)


server = Server()

users = server.get_users()
user = None
if len(users) < 2:
    user = server.create_user("user", "p@ssword")
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
chat2.query(Message(chat.get_user(), "When is self due?"))
