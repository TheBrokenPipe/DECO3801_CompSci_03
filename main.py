import asyncio
import sys
import logging
import argparse

from dotenv import load_dotenv

from MIS.backend.docker_manager import DockerManager
from MIS.backend.database_manager import DB_Manager
from MIS.backend.ingestion import Ingestion

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    """Runs the backend, infinitely looping over and processing meetings."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true")

    args = parser.parse_args()

    logging.basicConfig()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    with DockerManager(stop_when_done=False) as m:
        m.full_setup()
        await DB_Manager.full_setup()
        ingestion = Ingestion()
        while True:
            await ingestion.transcribe_next_meeting()
            await ingestion.summarise_next_meeting()
            await ingestion.ingest_next_meeting()


asyncio.run(main())
