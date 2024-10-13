import asyncio
import sys
import logging
import argparse

from dotenv import load_dotenv

from MIS import DockerManager
from MIS import DB_Manager
from MIS import Ingestion

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
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
