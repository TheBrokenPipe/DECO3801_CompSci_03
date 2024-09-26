from pydantic import BaseModel
from datetime import datetime

import warnings
warnings.filterwarnings("ignore", message="Field .* has conflict with protected namespace .*")


class Meeting(BaseModel):
    __tablename__ = "meeting"
    __primarykey__ = "id"
    id: int
    name: str
    date: datetime
    file_recording: str
    file_transcript: str
    summary: str
    status: str


class KeyPoint(BaseModel):
    __tablename__ = "key_points"
    __primarykey__ = "id"
    __foreignkeys__ = {
        'meeting_id': ('meeting', 'id')
    }
    id: int
    meeting_id: int
    text: str


class ActionItem(BaseModel):
    __tablename__ = "action_items"
    __primarykey__ = "id"
    __foreignkeys__ = {
        'meeting_id': ('meeting', 'id')
    }
    id: int
    meeting_id: int
    text: str


class Tag(BaseModel):
    __tablename__ = "tag"
    __primarykey__ = "id"
    id: int
    name: str
    last_modified: datetime


class MeetingTag(BaseModel):
    __tablename__ = "meeting_tag"
    __primarykey__ = ("meeting_id", "tag_id")
    __foreignkeys__ = {
        'meeting_id': ('meeting', 'id'),
        'tag_id': ('tag', 'id')
    }
    meeting_id: int
    tag_id: int


class Document(BaseModel):
    __tablename__ = "document"
    __primarykey__ = "id"
    __foreignkeys__ = {
        'meeting_id': ('meeting', 'id')
    }
    id: int
    meeting_id: int
    metadata: dict
    text: str
    embedding: list[float]


class Chat(BaseModel):
    __tablename__ = "chat"
    __primarykey__ = "id"
    id: int
    filter: dict
    history: dict
