import asyncio
import sys
import os
import logging
from pathlib import Path

import requests
import tqdm

from dotenv import load_dotenv

from backend.manager import Manager
from backend.docker_manager import DockerManager
from backend.database_manager import DB_Manager
from models import *
from access import *


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def download(url: str, filename: str, desc: str):
    with open(filename, 'wb') as f:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            filesize = int(r.headers.get('content-length', 0))

            tqdm_params = {
                'desc': desc,
                'total': filesize,
                'miniters': 1,
                'unit': 'B',
                'unit_scale': True,
                'unit_divisor': 1024,
            }
            with tqdm.tqdm(**tqdm_params) as pb:
                for chunk in r.iter_content(chunk_size=8192):
                    pb.update(len(chunk))
                    f.write(chunk)


def download_meetings_scenarios(base_path: str):
    print("Downloading meetings... ")
    baseurl = "https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/"
    # scenarios = ["ES2002","ES2003","ES2004","ES2005","ES2006","ES2007","ES2008","ES2009",]
    scenarios = ["ES2002", "ES2003"]
    meetings = ["a", "b", "c", "d"]
    for scenario in scenarios:
        for meeting in meetings:
            url = f"{baseurl}{scenario}{meeting}/audio/{scenario}{meeting}.Mix-Headset.wav"
            filename = f"{base_path}{scenario}{meeting}.Mix-Headset.wav"
            description = f"Downloading {scenario}{meeting}.Mix-Headset.wav"
            download(url, filename, description)
    print("Done")

def download_meetings(base_path: str):
    print("Downloading meetings... ")
    baseurl = "https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/"
    meetings = ["ES2002a", "ES2002b", "ES2002c", "ES2002d","EN2002a","EN2002b","EN2002c","EN2002d","EN2006a","EN2006b"]
    for meeting in meetings:
        url = f"{baseurl}{meeting}/audio/{meeting}.Mix-Headset.wav"
        filename = f"{base_path}{meeting}.Mix-Headset.wav"
        description = f"Downloading {meeting}.Mix-Headset.wav"
        download(url, filename, description)
    print("Done")

async def create_meetings(base_path: str):
    print("Creating meetings... ")
    with DockerManager(stop_when_done=False) as m:
        m.full_setup()
        await DB_Manager.full_setup()
        t = Manager()
        p = Path(base_path)
        tag_names = set()
        meetings = []
        for file in sorted(p.glob("*")):
            name = file.stem[:7]
            date=datetime.now()
            file_recording = str(file)
            file_transcript = ""
            summary = ""
            meeting = await t.create_meeting(name, date, file_recording, file_transcript, summary)
            meetings.append(meeting)
            tag_names.add(file.stem[:6])

        for tag_name in sorted(tag_names):
            tag_meetings = list(filter(lambda meeting: meeting.name[:6]==tag_name, meetings))
            await t.create_tag(tag_name, tag_meetings)
    print("Done")


def main():
    base_dir = "data/recordings/"
    # try:
    #     os.makedirs(base_dir)
    # except FileExistsError as e:
    #     print("Recordings directory already exists, skipping setup")
    #     return
    
    # download_meetings(base_dir)
    asyncio.run(create_meetings(base_dir))

if __name__ == "__main__":
    main()    


