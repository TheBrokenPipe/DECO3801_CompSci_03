import asyncio
import sys
from dotenv import load_dotenv
from backend.manager import Manager
from backend.docker_manager import DockerManager
from backend.database_manager import DB_Manager
import logging
from models import *

# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)

load_dotenv()
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    with DockerManager(stop_when_done=False) as m:
        m.full_setup()
        try:
            print("SETUP")
            await DB_Manager.full_setup(True)
        except Exception as e:
            print(e)
        t = Manager(10, pg_manager=m)
        await t.create_tag("Marketing", [])
        await t.create_tag("Engineering", [])

        tags = await t.get_all_tags()

        logging.info(tags)

        exec1 = MeetingCreation(
            date=datetime.now(),
            name="ES2016a",
            file_recording="data/recordings/ES2016a.Mix-Headset.wav",
            file_transcript="",
            summary=""
        )

        exec2 = MeetingCreation(
            date=datetime.now(),
            name="ES2016b",
            file_recording="data/recordings/ES2016b.Mix-Headset.wav",
            file_transcript="",
            summary=""
        )

        exec3 = MeetingCreation(
            date=datetime.now(),
            name="ES2016c",
            file_recording="data/recordings/ES2016c.Mix-Headset.wav",
            file_transcript="",
            summary=""
        )

        exec4 = MeetingCreation(
            date=datetime.now(),
            name="ES2016d",
            file_recording="data/recordings/ES2016d.Mix-Headset.wav",
            file_transcript="",
            summary=""
        )
        meeting = await t.create_meeting("ES2016b", datetime.now(), "1", "2")
        await t.add_meetings_to_tag(tags[0], meeting)
        # await t.add_meetings_to_tag([exec1,exec2, exec3, exec4], tags[0])

asyncio.run(main())