from .access_base import AccessBase
from json import dumps
from typing import TypeVar
from pydantic import BaseModel

# Define a generic type variable that must be a subclass of BaseModel
BaseModelSubClass = TypeVar('BaseModelSubClass', bound=BaseModel)


async def insert_into_table(
    objs: BaseModel | list[BaseModel], always_return_list=False
) -> BaseModelSubClass | list[BaseModelSubClass]:
    # Handle a single object case by converting it to a list
    if not isinstance(objs, list):
        objs = [objs]

    if len(objs) == 0:
        return []

    # Check if all objects are instances of BaseModel
    for obj in objs:
        assert issubclass(type(obj), BaseModel), \
            f"Object is not a pydantic model: {obj}"

    # Prepare the first object to extract table details
    first_obj = objs[0]

    # Remove attributes that are None from the dictionary
    data_list = [{k: v for k, v in obj.model_dump().items() if v is not None}
                 for obj in objs]

    # Dynamically generate column names and placeholders for the first object
    columns = ', '.join(data_list[0].keys())
    placeholders = ', '.join(['%s'] * len(data_list[0]))

    # Generate SQL query
    sql = f"""
        INSERT INTO public.{first_obj.__tablename__} ({columns})
        VALUES {', '.join([f"({placeholders})" for _ in objs])}
        RETURNING *;
    """

    try:
        # Flatten the parameters for all objects
        params = []
        for data in data_list:
            params.extend(
                map(lambda v: dumps(v) if isinstance(v, dict)
                    else v, data.values())
            )

        # Execute the SQL query and fetch all results
        results = await AccessBase.db_fetchall(
            sql,
            tuple(params),
            lambda f: first_obj.__class__(**f)
        )

        # Return a list if multiple objects were provided;
        # otherwise, return a single object
        if always_return_list:
            return results
        else:
            return results if len(results) > 1 else results[0]

    except Exception as e:
        raise e
