from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
import logging
import os
from psycopg import AsyncCursor
from psycopg.sql import SQL


class AccessBase:

    connection_string = (
        f"host={os.getenv('HOSTNAME')} "
        f"port={os.getenv('PORT')} "
        f"dbname={os.getenv('DB_NAME')} "
        f"user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASSWORD')}"
    )

    pool = AsyncConnectionPool(
        connection_string,
        min_size=1,
        max_size=10,
        open=False
    )

    @staticmethod
    def db_access(func):
        async def wrapper(*args, **kwargs):
            await AccessBase.pool.open()
            try:
                async with AccessBase.pool.connection(30) as conn:
                    await conn.set_autocommit(True)
                    async with conn.cursor(row_factory=dict_row) as cursor:
                        return await func(*args, **kwargs, cursor=cursor)
            except Exception as e:
                raise e

        return wrapper

    @staticmethod
    @db_access
    async def db_fetchone(sql, values=None, function=lambda f: f, cursor: AsyncCursor = None):
        assert cursor is not None
        await cursor.execute(SQL(sql), values)
        ret = await cursor.fetchone()
        return function(ret) if ret else None

    @staticmethod
    @db_access
    async def db_fetchall(sql, values=None, function=lambda f: f, cursor: AsyncCursor = None) -> list:
        assert cursor is not None
        await cursor.execute(SQL(sql), values)
        ret = await cursor.fetchall()
        return list(map(function, ret))

    @staticmethod
    @db_access
    async def db_execute(sql, values=None, cursor: AsyncCursor = None) -> None:
        assert cursor is not None
        await cursor.execute(SQL(sql), values)
