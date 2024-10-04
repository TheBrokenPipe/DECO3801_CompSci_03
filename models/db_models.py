from pydantic import BaseModel
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", message="Field .* has conflict with protected namespace .*")


class DatabaseModel(BaseModel):
    __tablename__: str
    __primarykey__: str
    __foreignkeys__: dict[str: tuple[str, str]] = {}

    def __init__(self, **data):
        super().__init__(**data)
        self._initial_state = self.dict()

    def has_changes(self) -> bool:
        """
        Checks if any attributes have been modified from their original state.
        Returns True if changes are detected, False otherwise.
        """
        current_state = self.dict()
        return current_state != self._initial_state

    def get_changes(self) -> dict:
        """
        Returns a dictionary of fields that have been modified, with the format:
        {field_name: (original_value, current_value)}
        """
        current_state = self.dict()
        changes = {
            key: (self._initial_state[key], value)
            for key, value in current_state.items()
            if self._initial_state[key] != value
        }
        return changes

    def __hash__(self):
        return hash(getattr(self, self.__primarykey__, None))
    """
    def __h__(self):
        return hash(self.)
    """

class DB_Meeting(DatabaseModel):
    __tablename__ = "meeting"
    __primarykey__ = "id"
    id: int | None = None
    name: str
    date: datetime
    file_recording: str
    file_transcript: str
    summary: str
    status: str


class DB_KeyPoint(DatabaseModel):
    __tablename__ = "key_points"
    __primarykey__ = "id"
    __foreignkeys__ = {
        'meeting_id': ('meeting', 'id')
    }
    id: int | None = None
    meeting_id: int
    text: str


class DB_ActionItem(DatabaseModel):
    __tablename__ = "action_items"
    __primarykey__ = "id"
    __foreignkeys__ = {
        'meeting_id': ('meeting', 'id')
    }
    id: int | None = None
    meeting_id: int
    text: str


class DB_Tag(DatabaseModel):
    __tablename__ = "tag"
    __primarykey__ = "id"
    id: int | None = None
    name: str
    last_modified: datetime | None = None


class DB_MeetingTag(DatabaseModel):
    __tablename__ = "meeting_tag"
    __primarykey__ = ("meeting_id", "tag_id")
    __foreignkeys__ = {
        'meeting_id': ('meeting', 'id'),
        'tag_id': ('tag', 'id')
    }
    meeting_id: int
    tag_id: int


class DB_Doc(DatabaseModel):
    __tablename__ = "document"
    __primarykey__ = "id"
    __foreignkeys__ = {
        'meeting_id': ('meeting', 'id')
    }
    id: int | None = None
    meeting_id: int
    metadata: dict
    text: str
    embedding: list[float]


class DB_Chat(DatabaseModel):
    __tablename__ = "chat"
    __primarykey__ = "id"
    id: int | None = None
    name: str
    filter: dict = {}
    history: dict = {}
