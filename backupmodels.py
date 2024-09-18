from pydantic import BaseModel


class Relationship(BaseModel):
    """
    name: name or title of related person
    relation: brief description of how this person is related to the main entity
    """
    name: str
    relation: str


class Person(BaseModel):
    """
    name: name of person
    description: brief description of person
    related_people: list of relations this person has to other people
    """
    name: str
    description: str
    related_people: list[Relationship]


class Date(BaseModel):
    name: str
    year: str | None
    month: str | None
    day: str | None
    description: str


class Place(BaseModel):
    """
    name: name of place
    description: brief description of place
    """
    name: str
    description: str


class Place(BaseModel):
    """
    name: name of place
    description: brief description of place
    """
    name: str
    description: str


class MiscObjects(BaseModel):
    name: str
    instances_from_text: list[str]


class ExtractedObjects(BaseModel):
    people: list[Person]
    dates: list[Date]
    places: list[Place]
    # misc_objects: list[MiscObjects]


class ExtractedObjects2(BaseModel):
    people: list[Person]
    dates: list[Date]
    places: list[Place]
    # misc_objects: list[MiscObjects]