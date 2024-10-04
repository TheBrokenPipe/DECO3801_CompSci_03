import asyncio
import sys
from dotenv import load_dotenv
from backend.docker_manager import DockerManager
from backend.database_manager import DB_Manager
import logging
from models import *
from access import *
from backend.ingestion import Ingestion

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    with DockerManager(stop_when_done=False) as m:
        m.full_setup()
        await DB_Manager.full_setup()
        return
        ingestion = Ingestion()
        while True:
            await ingestion.transcribe_next_meeting()
            await ingestion.summarise_next_meeting()
            # await ingestion.ingest_next_meeting()
        
        
asyncio.run(main())
