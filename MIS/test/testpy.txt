import os
from openai import OpenAI
from pydantic import BaseModel
import json
from dotenv import load_dotenv
from backend.docker_manager import DockerManager
from backend.database_manager import DB_Manager

load_dotenv()
open_ai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
open_ai_text_model = "gpt-4o-mini"
open_ai_embedding_model = "text-embedding-3-small"


"""
response = open_ai_client.embeddings.create(
    input="question",
    model=open_ai_embedding_model,
    dimensions=10
)
question = response.data[0].embedding
print(question)
print(type(response.data[0].embedding[0]))
print(response.usage)

print()

response = open_ai_client.embeddings.create(
    input="answer",
    model=open_ai_embedding_model,
    dimensions=10
)
answer = response.data[0].embedding
print(answer)
print(type(response.data[0].embedding[0]))
print(response.usage)

print(np.array(answer) - np.array(question))

exit()
"""


class PersonDetail(BaseModel):
    """
    type: type of detail, e.g. "age", "role"
    text: detail text, e.g. "25", "friend"
    """
    type: str
    text: str


class Person(BaseModel):
    """
    details: list of known details about the person.
    """
    first_name: str | None
    last_name: str | None
    age: int | None
    details: list[PersonDetail]


class People(BaseModel):
    """
    people: list of individuals mentioned in text
    """
    people: list[Person]


class KeyPoint(BaseModel):
    """text: key / main point and important idea, finding, or topic that are crucial to the essence"""
    text: str


class KeyPoints(BaseModel):
    """
    people: list of key points mentioned in text
    """
    key_points: list[KeyPoint]


class ActionItem(BaseModel):
    """
    text: task, assignment or action that was agreed upon or mentioned as needing to be done.
    assigned_people_names: list of names of people assigned to this task
    due_date: date and/or time of when the task should be completed
    """
    text: str
    assigned_people_names: list[str]
    due_date: str


class ActionItems(BaseModel):
    """
    people: list of action items mentioned in text
    """
    action_items: list[ActionItem]


class ExtractedObjects(BaseModel):
    """
    key_points: list of key / main points and most important ideas, findings, or topics that are crucial to the essence
        of the discussion. A list that someone could read to quickly understand what was talked about.
    action_items: list of tasks, assignments, or actions that were agreed upon or mentioned as needing to be done.
        This can be tasks, assignments, or actions that were agreed upon or mentioned as needing to be done.
    """
    # people: list[Person]
    # key_points: list[KeyPoint]
    action_items: list[ActionItem]
    # clients: list[Person]
    # events: list[Event]
    # places: list[Union[PlaceAbstract, PlacePhysical]]
    # other_object: str


# print(json.dumps(ExtractedObjects.model_json_schema(), indent=4))
# exit()
database_tables = {
    "people": {
        "description": "People, individual humans.",
        "description_embedding": [
            0.4212183654308319, 0.30845123529434204, 0.1626555174589157, 0.5527799725532532, 0.28827476501464844,
            -0.36732229590415955, 0.0764218345284462, 0.22746896743774414, -0.020936543121933937, -0.345487505197525
        ],
        "columns": {
            "name": "name of person",
            "age": "age of person",
            "description": "brief description of person",
        }
    }
}

data = {
    "people": []
}
"""
print(
    open_ai_client.chat.completions.create(
        model=open_ai_text_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "Given a description of a table in a database, "
                           "give me a brief description of the object contained in the table.\n\n"
                           "example:\nTable containing information about people.\nPeople, individual humans."
            },
            {
                "role": "user",
                "content": "Table containing information about events."
            }
        ]
    ).choices[0].message.content
)
"""
# response = open_ai_client.embeddings.create(
#     input="People, individual humans.",
#     model=open_ai_embedding_model,
#     dimensions=10
# )
# print(response.data[0].embedding)
# print(type(response.data[0].embedding[0]))
# print(response.usage)

"""
class ExtractedObject(BaseModel):
    ""
    text: the text pertaining to the object
    type: fewest words possible to describe the object
    ""
    text: str
    type: str


class ExtractedObjects(BaseModel):
    object: list[ExtractedObject]
"""


def extract_objects(text):
    system_prompt = [
        {
            "role": "system",
            "content": f"You find and list all the objects in the text.\n"
                       f"Known object types include: {', '.join(['Action Item'])}"
        },
        {
            "role": "user",
            "content": text
        }
    ]

    response = open_ai_client.beta.chat.completions.parse(
        model=open_ai_text_model,
        messages=system_prompt,
        temperature=0,
        response_format=ExtractedObjects,
    )
    # print(response.choices[0].message.json())
    # print(type(response.choices[0].message.json()))
    # print(json.loads(response.choices[0].message.content))
    # print(json.dumps(json.loads(response.choices[0].message.content), indent=4))
    # print()
    # print(response.usage.total_tokens)
    # print((response.usage.total_tokens/1e6) * 0.150)
    return json.loads(response.choices[0].message.content)


def extract_specific_objects(text, model):
    system_prompt = [
        {
            "role": "system",
            "content": f"You are tasked with finding objects in the text matching the provided model."
        },
        {
            "role": "user",
            "content": text
        }
    ]

    response = open_ai_client.beta.chat.completions.parse(
        model=open_ai_text_model,
        messages=system_prompt,
        response_format=model,
    )
    # print((response.usage.total_tokens/1e6) * 0.150)
    # print(response.choices[0].message.json())
    # print(type(response.choices[0].message.json()))
    # print(json.loads(response.choices[0].message.content))
    # print(json.dumps(json.loads(response.choices[0].message.content), indent=4))
    # exit()

    return json.loads(response.choices[0].message.content)


with DockerManager() as m:
    m.full_setup(False)
    DB_Manager.full_setup()

    with open("data/saved_docs/file_test_1724978229.543099", 'r') as f:
        text_data = f.read()

    # people = extract_specific_objects(text_data, People)
    # key_points = extract_specific_objects(text_data, KeyPoints)
    action_items = extract_specific_objects(text_data, ActionItems)
    # print(json.dumps(people, indent=4))
    # print(json.dumps(key_points, indent=4))
    # print(json.dumps(action_items, indent=4))

    # for person in People(**people).people:
    #     DB_Manager.insert_model_to_db(person, "people")

    # for key_points in KeyPoints(**key_points).key_points:
    #     DB_Manager.insert_model_to_db(key_points, "key_points")

    for action_item in ActionItems(**action_items).action_items:
        DB_Manager.insert_model_to_db(action_item, "action_items")

    ret = DB_Manager.get_action_items()

    print(ret)
    print(type(ret))
    print()
    print(json.dumps(ret, indent=4))

    input("\n\nConnect to db manually now:")
