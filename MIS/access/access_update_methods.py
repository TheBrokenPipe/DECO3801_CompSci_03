from .access_base import AccessBase
from ..models import DatabaseModel
from pydantic import BaseModel
from json import dumps
from typing import TypeVar, Dict, Any, List, Type

# Define a generic type variable that must be a subclass of BaseModel
BaseModelSubClass = TypeVar('BaseModelSubClass', bound=BaseModel)


async def delete_from_table(
    model: Type[BaseModelSubClass],
    value: int | str | tuple | list[int | str | tuple],
    key_name: str | tuple = None,
    always_return_list=True
) -> BaseModelSubClass | List[BaseModelSubClass]:
    # Ensure the input is a subclass of BaseModel
    assert issubclass(model, BaseModel), \
        f"Model is not a subclass of BaseModel: {model}"
    if key_name is None:
        key_name = model.__primarykey__

    # Handle composite keys
    if isinstance(key_name, tuple):  # Composite Key
        assert isinstance(value, tuple), \
            f"Both key_name and value must be tuples: {key_name} != {value}"
        assert len(key_name) == len(value), \
            "The length of key_name and value must match."
    else:  # Single Key
        key_name = [key_name]
        value = (value,)

    # Construct the filter clause for the WHERE condition
    filter_clause = ' AND '.join([f"{k} = %s" for k in key_name])

    # Generate the DELETE SQL query
    sql = (f"DELETE FROM public.{model.__tablename__} "
           f"WHERE {filter_clause} RETURNING *;")

    try:
        # Execute the SQL query
        deleted_rows = await AccessBase.db_fetchall(
            sql,
            value,
            lambda f: model(**f)
        )
        if not always_return_list and len(deleted_rows):
            return deleted_rows[0]
        return deleted_rows
    except Exception as e:
        print(e)
        raise e


async def update_table_from_model(obj: BaseModelSubClass) -> BaseModelSubClass:
    assert issubclass(type(obj), BaseModel), \
        f"Object is not a pydantic model: {obj}"
    # Convert the Pydantic model object to a dictionary
    data = obj.model_dump()

    # Identify the primary key column and value for updating,
    # assuming the primary key column is defined in the model
    primary_key_column = obj.__primarykey__
    primary_key_value = data.get(primary_key_column)

    # Ensure the primary key is present
    assert primary_key_value is not None, \
        "Primary key value must be provided for updating."

    # Remove the primary key from the data to avoid updating it
    data.pop(primary_key_column)

    # Dynamically generate column names and placeholders for the SET clause
    set_clause = ', '.join([f"{key} = %s" for key in data.keys()])

    # Generate the SQL query
    sql = f"""
        UPDATE public.{obj.__tablename__}
        SET {set_clause}
        WHERE {primary_key_column} = %s
        RETURNING *;
    """
    try:
        # Execute the SQL query
        return await AccessBase.db_fetchone(
            sql,
            tuple(
                map(
                    lambda v:
                    dumps(v) if isinstance(v, dict) else
                    list(map(lambda i_v: dumps(i_v) if isinstance(i_v, dict)
                             else i_v, v))
                    if isinstance(v, list)
                    else v, data.values()
                )
            ) + (primary_key_value,),
            lambda f: obj.__class__(**f)
        )
    except Exception as e:
        print(e)
        raise e


async def update_table(
    model: Type[BaseModelSubClass],
    updates: Dict[str, Any],
    conditions: Dict[str, Any],
    always_return_list=True
) -> BaseModelSubClass | List[BaseModelSubClass]:
    """
    Update specified columns for all rows that match given conditions.
    """
    assert issubclass(model, DatabaseModel), \
        f"Object is not a Database Pydantic model: {model}"

    # Retrieve valid fields from the model
    valid_fields = model.__fields__.keys()

    # Validate update keys
    for key in updates.keys():
        if key not in valid_fields:
            raise ValueError(f"Invalid update field: {key}")

    # Validate condition keys
    for key in conditions.keys():
        if key not in valid_fields:
            raise ValueError(f"Invalid condition field: {key}")

    # Get the table name from the model
    table_name = model.__tablename__

    # Dynamically generate SET clause
    set_clause = ', '.join([f"{key} = %s" for key in updates.keys()])

    # Dynamically generate WHERE clause
    where_clause = ' AND '.join([f"{key} = %s" for key in conditions.keys()])

    # Combine updates and conditions for parameter substitution
    parameters = tuple(
        dumps(value) if isinstance(value, dict)
        else value for value in updates.values()
    ) + tuple(
        dumps(value) if isinstance(value, dict)
        else value for value in conditions.values()
    )

    # Generate the SQL query
    sql = f"""
        UPDATE public.{table_name}
        SET {set_clause}
        WHERE {where_clause}
        RETURNING *;
    """

    try:
        # Execute the SQL query and fetch all updated rows
        updated_rows = await AccessBase.db_fetchall(
            sql,
            parameters,
            lambda row: model(**row)
        )
        if not always_return_list and len(updated_rows):
            return updated_rows[0]
        return updated_rows
    except Exception as e:
        print(f"Error updating table: {e}")
        raise e
