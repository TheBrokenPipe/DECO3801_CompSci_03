import json
import os
import psycopg
from psycopg import sql
from pydantic import BaseModel

# from dotenv import load_dotenv
# load_dotenv()


class DB_Manager:

    @staticmethod
    def setup_table_structure(verbose=False):
        with psycopg.connect(
            host=os.getenv("HOSTNAME"),  # Use 'localhost' since we're connecting to the Docker container
            port=os.getenv("PORT"),  # Port that PostgreSQL is exposed on
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        ) as conn:
            if verbose: print("Connected to the PostgreSQL database successfully.")

            # Install the pgvector extension
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                if verbose: print("pgvector extension installed successfully.")

            # Create a new table named 'people'
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS people (
                        id SERIAL PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        age INT,
                        details JSONB[]  -- Storing details as JSON for flexibility
                    );
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        local_file_path TEXT,
                        embedding VECTOR({os.getenv('VECTOR_SIZE')})
                    );
                    CREATE TABLE IF NOT EXISTS key_points (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE ON UPDATE CASCADE,
                        text TEXT
                    );
                    CREATE TABLE IF NOT EXISTS action_items (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE ON UPDATE CASCADE,
                        text TEXT,
                        assigned_people_names TEXT[],  -- Storing list of names as an array
                        due_date TEXT
                    );
                """)
                conn.commit()
                if verbose:
                    print("Tables created successfully.")

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
    def full_setup(cls, verbose=False):
        cls.setup_table_structure(verbose)
