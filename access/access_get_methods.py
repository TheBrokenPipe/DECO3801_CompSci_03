from time import time
import asyncio
import logging
from collections import deque

from .access_base import AccessBase
from json import dumps
from typing import TypeVar, Callable, List, Type, Any, Optional
from pydantic import BaseModel
from typing import Type
import importlib
import inspect
from collections import defaultdict

# Define a generic type variable that must be a subclass of BaseModel
BaseModelSubClass = TypeVar('BaseModelSubClass', bound=BaseModel)


async def count_from_table(
    model: Type[BaseModelSubClass],
    value: [int | str | float | tuple | List[int | str | float | tuple]],
    key_names: str | tuple[str, tuple[str, ...]],
    always_return_list=True
) -> int | List[int]:
    """
    Counts the number of records in the table that match the given key(s) and value(s).
    Processes the SQL as if it's always handling multiple values.
    Returns either a single count or a list of counts based on always_return_list.

    Parameters:
        model (BaseModelSubClass): The database model class to query.
        value (int | str | float | tuple | list): The value(s) to match against the key_names column(s).
        key_names (str | tuple): The column name(s) to match the value(s) against.
        always_return_list (bool): If True, always return a list of counts, even if there's only one value.
                                   If False, return a single count if only one value is provided.

    Returns:
        int or List[int]: The count(s) of matching records.
    """
    # Ensure the input is a subclass of BaseModel
    if not issubclass(model, BaseModel):
        raise TypeError(f"Model is not a subclass of BaseModel: {model}")

    # Convert key_names to a tuple for uniform processing
    if not isinstance(key_names, tuple):
        if isinstance(key_names, str):
            key_names = (key_names,)
        else:
            raise TypeError("key_names must be a string or a tuple of strings")

    # Ensure value(s) are in a list for uniform processing
    if isinstance(value, list):
        values = value
    else:
        values = [value]

    # Validate that each value matches the length of key_names
    for val in values:
        if len(key_names) == 1:
            if isinstance(val, tuple):
                raise ValueError(f"Expected single value for key_name '{key_names[0]}', got tuple {val}")
        else:
            if not isinstance(val, (tuple, list)):
                raise ValueError(f"Expected tuple value for composite key {key_names}, got {val}")
            if len(val) != len(key_names):
                raise ValueError(f"Length of value tuple {val} does not match length of key_names {key_names}")

    # Build the WHERE clause and parameters
    params = []
    clauses = []
    for val in values:
        if len(key_names) == 1:
            # Single key
            clauses.append(f"{key_names[0]} = %s")
            params.append(val)
        else:
            # Composite key
            clause_parts = []
            for k, v in zip(key_names, val):
                clause_parts.append(f"{k} = %s")
                params.append(v)
            clauses.append("(" + " AND ".join(clause_parts) + ")")

    # Combine clauses with OR
    where_clause = " OR ".join(clauses)

    # Build the SQL query
    # Always process as if handling multiple values
    key_fields = ", ".join(key_names)
    sql = f"""
        SELECT {key_fields}, COUNT(*) as count
        FROM public.{model.__tablename__}
        WHERE {where_clause}
        GROUP BY {key_fields};
    """

    try:
        # Execute the SQL query
        results = await AccessBase.db_fetchall(sql, params)
        # Process results to map counts
        counts_dict = {}
        for row in results:
            # Assuming row is a dict
            count = row['count']
            key_values = tuple(row[k] for k in key_names)
            if len(key_names) == 1:
                counts_dict[key_values[0]] = count
            else:
                counts_dict[key_values] = count

        # Build the counts list in the same order as the input values
        counts = []
        for val in values:
            key = val if len(key_names) == 1 else tuple(val)
            counts.append(counts_dict.get(key, 0))

        # Decide whether to return a list or a single count
        if not always_return_list and len(counts) == 1:
            return counts[0]
        else:
            return counts
    except Exception as e:
        print(f"Error in count_from_table: {e}")
        raise e


async def select_from_table(
    model: Type[BaseModelSubClass],
    value: int | str | tuple | list[int | str | tuple],
    key_name: str | tuple = None
) -> BaseModelSubClass:
    # Ensure the input is a subclass of BaseModel
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
    sql = f"SELECT * FROM public.{model.__tablename__} WHERE {filter_clause};"

    try:
        # Execute the SQL query
        return await AccessBase.db_fetchone(
            sql,
            value,
            lambda f: model(**f)
        )

    except Exception as e:
        print(e)
        raise e


async def select_many_from_table(
    model: Type[BaseModelSubClass],
    values: list[int | str | tuple],
    key_name: str | tuple = None,
    grouped: bool = False,
    one_per_input: bool = False
) -> List[BaseModelSubClass] | list[List[BaseModelSubClass]]:
    # Ensure the input is a subclass of BaseModel
    assert issubclass(model, BaseModel), f"Model is not a subclass of BaseModel: {model}"

    # Default to the model's primary key if no key_name is provided
    if key_name is None:
        key_name = model.__primarykey__

    # Ensure key_name type matches the type of keys provided
    if not isinstance(values, list):
        values = [values]

    if isinstance(key_name, str):
        key_name = [key_name]  # Convert to list for consistent handling

    assert type(key_name) in [list, tuple], "key_name must be a string, list, or tuple."

    # Handle composite keys or single keys
    if isinstance(key_name, tuple):  # Composite Key
        # Ensure all provided keys are tuples of the correct length
        assert all(isinstance(pkey, tuple) and len(pkey) == len(key_name) for pkey in values), \
            "All provided keys must be tuples of the correct length."

        # Generate SQL placeholders for composite keys
        placeholder = f"({', '.join(['%s'] * len(key_name))})"
        placeholders = ', '.join([placeholder] * len(values))
        params = [item for pkey in values for item in pkey]
        filter_clause = f"({', '.join(key_name)}) IN ({placeholders})"

    else:  # Single Key
        # Ensure all provided keys are of the correct type
        assert all(isinstance(pkey, (int, str)) for pkey in values), \
            "All provided keys must be int or str for a single primary key."

        placeholders = ', '.join(['%s'] * len(values))
        params = values
        filter_clause = f"{key_name[0]} IN ({placeholders})"

    # Generate the SQL query
    sql = f"SELECT * FROM public.{model.__tablename__} WHERE {filter_clause};"

    try:
        results = await AccessBase.db_fetchall(
            sql,
            params,
            lambda f: model(**f)
        )

        if not grouped:
            return results
        else:
            # Build a mapping from key values to list of results
            key_to_results = defaultdict(list)

            for result in results:
                if isinstance(key_name, tuple):
                    # Composite key
                    key_value = tuple(getattr(result, k) for k in key_name)
                else:
                    key_value = getattr(result, key_name[0])
                key_to_results[key_value].append(result)

            # Build the list of lists corresponding to the input values
            grouped_results = []
            for v in values:
                grouped_results.append(key_to_results.get(v, []))
            if one_per_input:
                grouped_results = [g[0] if len(g) else None for g in grouped_results]
            return grouped_results

    except Exception as e:
        print(f"Error fetching data with {'{'}{select_many_from_table.__name__}{'}'}: {e}")
        raise e


# Function to get the join condition between two models
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

    # Check if model_a has a foreign key to model_b
    for field_name, (fk_table, fk_field) in fk_a.items():
        if fk_table == model_b.__tablename__:
            return f"INNER JOIN public.{model_b.__tablename__} AS {alias_b} ON {alias_a}.{field_name} = {alias_b}.{fk_field}"

    # Check if model_b has a foreign key to model_a
    for field_name, (fk_table, fk_field) in fk_b.items():
        if fk_table == model_a.__tablename__:
            return f"INNER JOIN public.{model_b.__tablename__} AS {alias_b} ON {alias_b}.{field_name} = {alias_a}.{fk_field}"

    raise Exception(f"No foreign key relationship found between {model_a.__tablename__} and {model_b.__tablename__}")


# The updated get_related_model function remains the same
async def select_with_joins_2(
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

    # Assign aliases to tables and keep track of model occurrences
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

    # Build SQL query
    sql = f"SELECT {table_aliases[-1]}.* FROM public.{start_model.__tablename__} AS {table_aliases[0]}"
    joins = []

    # Build joins for each consecutive pair in the join_path
    for i in range(len(join_path) - 1):
        model_a = join_path[i]
        alias_a = table_aliases[i]
        model_b = join_path[i + 1]
        alias_b = table_aliases[i + 1]
        join_clause = get_join_condition(model_a, alias_a, model_b, alias_b)
        joins.append(join_clause)

    sql += " " + " ".join(joins)

    # Build the WHERE clause
    params = []
    where_clauses = []

    # Add condition for start_value
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

    # Add conditions from table_conditions
    if table_conditions:
        for key, conditions in table_conditions.items():
            if isinstance(key, tuple):
                # Key is (model_class, occurrence_index)
                model_class, occurrence_index = key
                # Find the index in model_occurrences
                indexes = [i for i, (m, occ) in enumerate(model_occurrences) if m == model_class and occ == occurrence_index]
                if not indexes:
                    raise ValueError(f"Model {model_class} with occurrence {occurrence_index} is not in the join_path")
            else:
                # Key is model_class, apply to all occurrences
                model_class = key
                indexes = [i for i, (m, occ) in enumerate(model_occurrences) if m == model_class]
                if not indexes:
                    raise ValueError(f"Model {model_class} is not in the join_path")

            for index in indexes:
                alias = table_aliases[index]
                for field_name, value in conditions.items():
                    where_clauses.append(f"{alias}.{field_name} = %s")
                    params.append(value)

    # Combine all WHERE clauses
    if where_clauses:
        where_clause = ' AND '.join(where_clauses)
        sql += f" WHERE {where_clause}"

    sql += ";"

    # Debugging: Log the SQL query and parameters
    # print()
    # logger.debug(f"SQL Query: {sql}")
    # logger.debug(f"Parameters: {params}")
    # print()

    # Execute the query
    try:
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
    except Exception as e:
        print(f"Error fetching data: {e}")
        raise e


async def select_with_joins(
    start_values: Any,
    join_path: List[Type[BaseModel]],
    start_key: Optional[str] = None,
    table_conditions: Optional[dict[Any, dict[str, Any]]] = None,
    fetch_many=True,
    grouped=False
) -> Any:
    """
    Fetches instances of the target model by traversing foreign keys along the specified join_path.
    Allows additional conditions on any table in the path via table_conditions.
    If grouped is True, returns a list of lists corresponding to start_values.
    """
    if not join_path or len(join_path) < 2:
        raise ValueError("join_path must contain at least two models (start_model and target_model)")

    start_model = join_path[0]
    target_model = join_path[-1]

    # Ensure start_values is a list
    if not isinstance(start_values, list):
        start_values = [start_values]

    # Assign aliases to tables and keep track of model occurrences
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

    # Build SELECT clause, including start_key fields with aliases
    if start_key is None:
        start_key = start_model.__primarykey__

    if isinstance(start_key, (tuple, list)):
        start_key_list = list(start_key)
    else:
        start_key_list = [start_key]

    start_key_aliases = [f"start_{k}" for k in start_key_list]
    start_key_select = ', '.join([f"{table_aliases[0]}.{k} AS {alias}" for k, alias in zip(start_key_list, start_key_aliases)])

    sql = f"SELECT {table_aliases[-1]}.*, {start_key_select} FROM public.{start_model.__tablename__} AS {table_aliases[0]}"

    # Build joins for each consecutive pair in the join_path
    joins = []

    for i in range(len(join_path) - 1):
        model_a = join_path[i]
        alias_a = table_aliases[i]
        model_b = join_path[i + 1]
        alias_b = table_aliases[i + 1]
        join_clause = get_join_condition(model_a, alias_a, model_b, alias_b)
        joins.append(join_clause)

    sql += " " + " ".join(joins)

    # Build the WHERE clause
    params = []
    where_clauses = []

    # Add condition for start_values
    if isinstance(start_key, (tuple, list)):
        # Composite key
        if not all(isinstance(v, (tuple, list)) for v in start_values):
            raise ValueError("start_values must be a list of tuples when start_key is composite")
        if not all(len(v) == len(start_key_list) for v in start_values):
            raise ValueError("Each start_value must have the same length as start_key")
        # Build composite key IN clause
        placeholder = '(' + ', '.join(['%s'] * len(start_key_list)) + ')'
        placeholders = ', '.join([placeholder] * len(start_values))
        where_clauses.append(f"({', '.join([f'{table_aliases[0]}.{k}' for k in start_key_list])}) IN ({placeholders})")
        params.extend([item for value in start_values for item in value])
    else:
        # Single key
        placeholders = ', '.join(['%s'] * len(start_values))
        where_clauses.append(f"{table_aliases[0]}.{start_key} IN ({placeholders})")
        params.extend(start_values)

    # Add conditions from table_conditions
    if table_conditions:
        for key, conditions in table_conditions.items():
            if isinstance(key, tuple):
                # Key is (model_class, occurrence_index)
                model_class, occurrence_index = key
                # Find the index in model_occurrences
                indexes = [i for i, (m, occ) in enumerate(model_occurrences) if m == model_class and occ == occurrence_index]
                if not indexes:
                    raise ValueError(f"Model {model_class} with occurrence {occurrence_index} is not in the join_path")
            else:
                # Key is model_class, apply to all occurrences
                model_class = key
                indexes = [i for i, (m, occ) in enumerate(model_occurrences) if m == model_class]
                if not indexes:
                    raise ValueError(f"Model {model_class} is not in the join_path")

            for index in indexes:
                alias = table_aliases[index]
                for field_name, value in conditions.items():
                    where_clauses.append(f"{alias}.{field_name} = %s")
                    params.append(value)

    # Combine all WHERE clauses
    if where_clauses:
        where_clause = ' AND '.join(where_clauses)
        sql += f" WHERE {where_clause}"

    sql += ";"

    # Execute the query
    try:
        if not grouped and not fetch_many:
            results = await AccessBase.db_fetchone(
                sql=sql,
                values=params,
                function=lambda f: target_model(**f)  # Return row as is (dictionary)
            )
            return results
        else:
            results = await AccessBase.db_fetchall(
                sql=sql,
                values=params,
                function=lambda f: f  # Return row as is (dictionary)
            )
            if not grouped:  # and not fetch_many
                return [target_model(**r) for r in results]  # return the list of models

            # Build a mapping from start_value to list of target_model instances
            key_to_results = defaultdict(list)

            for r in results:
                # Extract start_value
                if isinstance(start_key, (tuple, list)):
                    start_value = tuple(r[f'start_{k}'] for k in start_key_list)
                    # Remove 'start_{k}' from r
                    for k in start_key_list:
                        del r[f'start_{k}']
                else:
                    start_value = r[f'start_{start_key}']
                    del r[f'start_{start_key}']

                key_to_results[start_value].append(target_model(**r))

            # Build the list of lists corresponding to the input start_values
            grouped_results = []
            for v in start_values:
                grouped_results.append(key_to_results.get(v, []))

            if fetch_many:
                return grouped_results
            else:
                return [g[0] if len(g) else None for g in grouped_results]

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise e

