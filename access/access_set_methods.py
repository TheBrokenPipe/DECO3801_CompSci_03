from .access_base import AccessBase
from pydantic import BaseModel
from json import dumps
from typing import TypeVar

BaseModelSubClass = TypeVar('BaseModelSubClass', bound=BaseModel)


async def insert_into_table(objs: BaseModel | list[BaseModel], always_return_list=False) -> BaseModelSubClass | list[BaseModelSubClass]:
    if not isinstance(objs, list):
        objs = [objs]

    for obj in objs:
        assert issubclass(type(obj), BaseModel), f"Object is not a pydantic model: {obj}"

    first_obj = objs[0]
    data_list = [obj.model_dump() for obj in objs]

    columns = ', '.join(data_list[0].keys())
    placeholders = ', '.join(['%s'] * len(data_list[0]))

    sql = f"""
        INSERT INTO app.{first_obj.__db_model__.__tablename__} ({columns}) 
        VALUES {', '.join([f"({placeholders})" for _ in objs])}
        RETURNING *;
    """

    try:
        params = []
        for data in data_list:
            params.extend(
                map(lambda v: dumps(v) if isinstance(v, dict) else v, data.values())
            )

        results = await AccessBase.db_fetchall(
            sql,
            tuple(params),
            lambda f: first_obj.__db_model__(**f)
        )

        if always_return_list:
            return results
        else:
            return results if len(results) > 1 else results[0]

    except Exception as e:
        print(e)
        raise e
