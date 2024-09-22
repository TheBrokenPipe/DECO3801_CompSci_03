import asyncio
import sys
from dotenv import load_dotenv
from backend.manager import Manager
from backend.docker_manager import DockerManager
from backend.database_manager import DB_Manager
import logging
from models import *

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    with DockerManager(stop_when_done=False) as m:
        m.full_setup()
        await DB_Manager.full_setup()
        t = Manager(10, pg_manager=m)
        while True:
            await t.ingest_meeting()
        
        
asyncio.run(main())
