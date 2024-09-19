from pydantic import BaseModel
from datetime import datetime
from .db_models import *

import warnings
warnings.filterwarnings("ignore", message="Field .* has conflict with protected namespace .*")


class MeetingCreation(BaseModel):
    __db_model__ = Meeting
    name: str
    date: datetime
    file_recording: str
    file_transcript: str
    summary: str


class KeyPointCreation(BaseModel):
    __db_model__ = KeyPoint
    meeting_id: int
    text: str


class ActionItemCreation(BaseModel):
    __db_model__ = ActionItem
    meeting_id: int
    text: str


class TagCreation(BaseModel):
    __db_model__ = Tag
    name: str


class MeetingTagCreation(BaseModel):
    __db_model__ = MeetingTag
    meeting_id: int
    tag_id: int


class DocumentCreation(BaseModel):
    __db_model__ = Document
    meeting_id: int
    metadata: dict
    text: str
    embedding: list[float]


class ChatCreation(BaseModel):
    __db_model__ = Chat
    filter: dict
    history: dict
