import json
import os
import psycopg
from psycopg import sql
from pydantic import BaseModel
from access import AccessBase

# from dotenv import load_dotenv
# load_dotenv()


class DB_Manager:

    @staticmethod
    async def setup_table_structure(verbose=False):
        if verbose: print("Starting Table Setup.")
        # table_exists = await AccessBase.db_fetchone(
        #     """
        #     SELECT EXISTS (
        #         SELECT FROM information_schema.tables
        #         WHERE table_name = 'document'
        #     );
        #     """
        # )
        # # Exit if the tables have already been set up
        # if table_exists:
        #     if verbose: print("Database tables are already set up.")
        #     return

        await AccessBase.db_execute("CREATE EXTENSION IF NOT EXISTS vector;")
        if verbose: print("pgvector extension installed successfully.")

        await AccessBase.db_execute(
            f"""
            CREATE TABLE IF NOT EXISTS meeting (
                id SERIAL PRIMARY KEY,
                date DATE,
                name TEXT,
                file_recording TEXT,
                file_transcript TEXT,
                summary TEXT
            );

            CREATE TABLE IF NOT EXISTS key_points (
                id SERIAL PRIMARY KEY,
                meeting_id INTEGER REFERENCES meeting(id) ON DELETE CASCADE ON UPDATE CASCADE,
                text TEXT
            );

            CREATE TABLE IF NOT EXISTS action_items (
                id SERIAL PRIMARY KEY,
                meeting_id INTEGER REFERENCES meeting(id) ON DELETE CASCADE ON UPDATE CASCADE,
                text TEXT
            );

            CREATE TABLE IF NOT EXISTS tag (
                id SERIAL PRIMARY KEY,
                name TEXT
            ); 

            CREATE TABLE IF NOT EXISTS meeting_tag (
                meeting_id INTEGER REFERENCES meeting(id) ON DELETE CASCADE ON UPDATE CASCADE,
                tag_id INTEGER REFERENCES tag(id) ON DELETE CASCADE ON UPDATE CASCADE,
                PRIMARY KEY (meeting_id, tag_id)
            ); 

            CREATE TABLE IF NOT EXISTS document (
                id SERIAL PRIMARY KEY,
                meeting_id INTEGER REFERENCES meeting(id) ON DELETE CASCADE ON UPDATE CASCADE,
                metadata JSONB,
                text TEXT,
                embedding VECTOR({os.getenv('VECTOR_SIZE')})
            );

            CREATE TABLE IF NOT EXISTS chat (
                id SERIAL PRIMARY KEY,
                filter JSONB,
                history JSONB
            );
            """
        )
        if verbose: print("Tables setup successfully.")

    @staticmethod
    def get_action_items():
        # Establish a connection to the PostgreSQL database
        with psycopg.connect(
                host=os.getenv("HOSTNAME"),
                port=os.getenv("PORT"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
        ) as conn:
            # Create a cursor object
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                # Execute the SELECT statement
                cur.execute("SELECT * FROM action_items;")

                # Fetch all rows from the result
                rows = cur.fetchone()

        return rows

    @staticmethod
    def insert_model_to_db(model_instance: BaseModel, table_name: str):
        """
        Inserts a Pydantic model instance into the specified SQL table.

        :param conn: Database connection object.
        :param model_instance: Instance of the Pydantic model to be inserted.
        :param table_name: Name of the SQL table.
        """
        # Get field names and values from the Pydantic model instance
        """
        data = model_instance.model_dump()
        print(data)
        fields = list(data.keys())
        values = list(data.values())
        print(values)
        """
        fields = model_instance.__fields__.keys()
        values = [getattr(model_instance, field) for field in fields]
        print(values)
        values = [v.model_dump_json() if issubclass(type(v), BaseModel) else v for v in values]
        print(values)

        # Prepare the SQL query
        query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({placeholders})").format(
            table=sql.Identifier(table_name),
            fields=sql.SQL(', ').join(map(sql.Identifier, fields)),
            placeholders=sql.SQL(', ').join(sql.Placeholder() * len(fields))
        )
        with psycopg.connect(
                host=os.getenv("HOSTNAME"),  # Use 'localhost' since we're connecting to the Docker container
                port=os.getenv("PORT"),  # Port that PostgreSQL is exposed on
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
        ) as conn:
            # Execute the query
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    @classmethod
    async def full_setup(cls, verbose=False):
        await cls.setup_table_structure(verbose)
