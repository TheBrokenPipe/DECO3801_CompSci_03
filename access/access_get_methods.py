from collections import deque
from .access_base import AccessBase
from typing import TypeVar, List, Any, Optional
from pydantic import BaseModel
from typing import Type

BaseModelSubClass = TypeVar('BaseModelSubClass', bound=BaseModel)

async def count_from_table(
    model: Type[BaseModelSubClass],
    value: int | str | tuple | list[int | str | tuple],
    key_name: str | tuple = None
) -> BaseModelSubClass:
    assert issubclass(model, BaseModel), f"Model is not a subclass of BaseModel: {model}"
    if key_name is None:
        key_name = model.__primarykey__

    assert type(key_name) is type(value)

    if type(key_name) is tuple:  # Composite Key
        assert len(key_name) == len(value)
        value = tuple(value)
    else:  # Single Key
        key_name = [key_name]
        value = (value,)

    filter_clause = ' AND '.join([f"{k} = %s" for k in key_name])
    sql = f"SELECT COUNT(*) FROM {model.__tablename__} WHERE {filter_clause};"

    return await AccessBase.db_fetchone(
        sql,
        value,
        lambda f: model(**f)
    )


async def select_from_table(
    model: Type[BaseModelSubClass],
    value: int | str | tuple | list[int | str | tuple],
    key_name: str | tuple = None
) -> BaseModelSubClass:
    assert issubclass(model, BaseModel), f"Model is not a subclass of BaseModel: {model}"
    if key_name is None:
        key_name = model.__primarykey__

    if type(key_name) is tuple:  # Composite Key
        assert type(key_name) is type(value), f"both key_name and value must be tuples: {key_name} != {value}"
        assert len(key_name) == len(value)
        value = tuple(value)
    else:  # Single Key
        key_name = [key_name]
        value = (value,)

    filter_clause = ' AND '.join([f"{k} = %s" for k in key_name])
    sql = f"SELECT * FROM {model.__tablename__} WHERE {filter_clause};"

    return await AccessBase.db_fetchone(
        sql,
        value,
        lambda f: model(**f)
    )


async def select_many_from_table(
        model: Type[BaseModelSubClass],
        values: list[int | str | tuple] = None,
        key_name: str | tuple = None
) -> List[BaseModelSubClass]:
    assert issubclass(model, BaseModel), f"Model is not a subclass of BaseModel: {model}"

    if key_name is None:
        key_name = model.__primarykey__

    if values is None:
        # Select all rows if no values are provided
        sql = f"SELECT * FROM {model.__tablename__};"
        params = []
    else:
        if not isinstance(values, list):
            values = [values]

        if isinstance(key_name, str):
            key_name = [key_name]

        assert type(key_name) in [list, tuple], "key_name must be a string, list, or tuple."

        if isinstance(key_name, tuple):  # Composite Key
            assert all(isinstance(pkey, tuple) and len(pkey) == len(key_name) for pkey in values), \
                "All provided keys must be tuples of the correct length."

            placeholder = f"({', '.join(['%s'] * len(key_name))})"
            placeholders = ', '.join([placeholder] * len(values))
            params = [item for pkey in values for item in pkey]
            filter_clause = f"({', '.join(key_name)}) IN ({placeholders})"
        else:  # Single Key
            assert all(isinstance(pkey, (int, str)) for pkey in values), \
                "All provided keys must be int or str for a single primary key."

            placeholders = ', '.join(['%s'] * len(values))
            params = values
            filter_clause = f"{key_name[0]} IN ({placeholders})"

        sql = f"SELECT * FROM {model.__tablename__} WHERE {filter_clause};"

    return await AccessBase.db_fetchall(
        sql,
        params,
        lambda f: model(**f)
    )


def get_join_condition(
    model_a: Type[BaseModel], alias_a: str,
    model_b: Type[BaseModel], alias_b: str
) -> str:
    """
    Given two models and their aliases, find the join condition between them.
    Returns a string representing the JOIN clause.
    """
    fk_a = getattr(model_a, '__foreignkeys__', {})
    fk_b = getattr(model_b, '__foreignkeys__', {})

    for field_name, (fk_table, fk_field) in fk_a.items():
        if fk_table == model_b.__tablename__:
            return f"INNER JOIN {model_b.__tablename__} AS {alias_b} ON {alias_a}.{field_name} = {alias_b}.{fk_field}"

    for field_name, (fk_table, fk_field) in fk_b.items():
        if fk_table == model_a.__tablename__:
            return f"INNER JOIN {model_b.__tablename__} AS {alias_b} ON {alias_b}.{field_name} = {alias_a}.{fk_field}"

    raise Exception(f"No foreign key relationship found between {model_a.__tablename__} and {model_b.__tablename__}")


async def select_with_joins(
    start_value: Any,
    join_path: List[Type[BaseModel]],
    start_key: Optional[str] = None,
    table_conditions: Optional[dict[Any, dict[str, Any]]] = None,
    fetch_many=True
) -> Any:
    """
    Fetches an instance of the target model by traversing foreign keys along the specified join_path.
    Allows additional conditions on any table in the path via table_conditions.
    """
    if not join_path or len(join_path) < 2:
        raise ValueError("join_path must contain at least two models (start_model and target_model)")

    start_model = join_path[0]
    target_model = join_path[-1]

    model_counts = {}
    table_aliases = []
    model_occurrences = []

    for model in join_path:
        model_name = model.__tablename__
        count = model_counts.get(model_name, 0) + 1
        model_counts[model_name] = count
        alias = f"{model_name}_{count}"
        table_aliases.append(alias)
        model_occurrences.append((model, count))

    sql = f"SELECT {table_aliases[-1]}.* FROM {start_model.__tablename__} AS {table_aliases[0]}"
    joins = []

    for i in range(len(join_path) - 1):
        model_a = join_path[i]
        alias_a = table_aliases[i]
        model_b = join_path[i + 1]
        alias_b = table_aliases[i + 1]
        join_clause = get_join_condition(model_a, alias_a, model_b, alias_b)
        joins.append(join_clause)

    sql += " " + " ".join(joins)

    params = []
    where_clauses = []

    if start_key is None:
        start_key = start_model.__primarykey__
    if isinstance(start_key, (tuple, list)):
        if not isinstance(start_value, (tuple, list)):
            raise ValueError("start_value must be a tuple or list when start_key is composite")
        if len(start_key) != len(start_value):
            raise ValueError("start_key and start_value must have the same length")
        where_clauses.extend([f"{table_aliases[0]}.{k} = %s" for k in start_key])
        params.extend(start_value)
    else:
        where_clauses.append(f"{table_aliases[0]}.{start_key} = %s")
        params.append(start_value)

    if table_conditions:
        for key, conditions in table_conditions.items():
            if isinstance(key, tuple):
                model_class, occurrence_index = key
                indexes = [i for i, (m, occ) in enumerate(model_occurrences) if m == model_class and occ == occurrence_index]
                if not indexes:
                    raise ValueError(f"Model {model_class} with occurrence {occurrence_index} is not in the join_path")
            else:
                model_class = key
                indexes = [i for i, (m, occ) in enumerate(model_occurrences) if m == model_class]
                if not indexes:
                    raise ValueError(f"Model {model_class} is not in the join_path")

            for index in indexes:
                alias = table_aliases[index]
                for field_name, value in conditions.items():
                    where_clauses.append(f"{alias}.{field_name} = %s")
                    params.append(value)

    if where_clauses:
        where_clause = ' AND '.join(where_clauses)
        sql += f" WHERE {where_clause}"

    sql += ";"

    if fetch_many:
        result = await AccessBase.db_fetchall(
            sql,
            params,
            lambda f: target_model(**f)
        )
    else:
        result = await AccessBase.db_fetchone(
            sql,
            params,
            lambda f: target_model(**f)
        )
    return result

