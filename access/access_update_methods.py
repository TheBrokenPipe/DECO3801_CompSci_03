from .access_base import AccessBase
from pydantic import BaseModel
from json import dumps
from typing import TypeVar, Type

BaseModelSubClass = TypeVar('BaseModelSubClass', bound=BaseModel)


async def delete_from_table(
    model: Type[BaseModelSubClass],
    value: int | str | tuple | list[int | str | tuple],
    key_name: str | tuple = None
) -> list[BaseModelSubClass]:
    assert issubclass(model, BaseModel), f"Model is not a subclass of BaseModel: {model}"
    if key_name is None:
        key_name = model.__primarykey__

    if isinstance(key_name, tuple):  # Composite Key
        assert isinstance(value, tuple), f"Both key_name and value must be tuples: {key_name} != {value}"
        assert len(key_name) == len(value), "The length of key_name and value must match."
    else:  # Single Key
        key_name = [key_name]
        value = (value,)

    filter_clause = ' AND '.join([f"{k} = %s" for k in key_name])

    sql = f"DELETE FROM {model.__tablename__} WHERE {filter_clause} RETURNING *;"

    try:
        # Execute the SQL query
        return await AccessBase.db_fetchall(
            sql,
            value,
            lambda f: model(**f)
        )
    except Exception as e:
        print(e)
        raise e


async def update_table(obj: BaseModel) -> BaseModelSubClass:
    assert issubclass(type(obj), BaseModel), f"Object is not a pydantic model: {obj}"
    data = obj.model_dump()

    primary_key_column = obj.__primarykey__
    primary_key_value = data.get(primary_key_column)

    assert primary_key_value is not None, "Primary key value must be provided for updating."

    data.pop(primary_key_column)

    set_clause = ', '.join([f"{key} = %s" for key in data.keys()])

    sql = f"""
        UPDATE {obj.__tablename__} 
        SET {set_clause}
        WHERE {primary_key_column} = %s
        RETURNING *;
    """

    try:
        return await AccessBase.db_fetchone(
            sql,
            tuple(map(lambda v: dumps(v) if isinstance(v, dict) else v, data.values())) + (primary_key_value,),
            lambda f: obj.__class__(**f)
        )
    except Exception as e:
        print(e)
        raise e

