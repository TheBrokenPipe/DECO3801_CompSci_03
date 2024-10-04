import os
import logging

from access import *
from models import *

class DB_Manager:

    @staticmethod
    async def setup_table_structure():
        logger = logging.getLogger(__name__)
        logger.debug("Starting Table Setup.")

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
        logger.debug("pgvector extension installed successfully.")

        await AccessBase.db_execute(
            f"""
            CREATE TABLE IF NOT EXISTS meeting (
                id SERIAL PRIMARY KEY,
                date DATE,
                name TEXT,
                file_recording TEXT,
                file_transcript TEXT,
                summary TEXT,
                status TEXT
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
                name TEXT,
                last_modified DATE
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
                name TEXT,
                filter JSONB,
                history JSONB
            );
            """
        )
        logger.debug("Tables setup successfully.")

    @classmethod
    async def full_setup(cls):
        await cls.setup_table_structure()
