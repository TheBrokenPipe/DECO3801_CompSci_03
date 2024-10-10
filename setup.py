import asyncio
import sys
import os
import logging
import subprocess
from pathlib import Path

import requests
import tqdm
from dotenv import load_dotenv

from backend.manager import Manager
from backend.docker_manager import DockerManager
from backend.database_manager import DB_Manager
from models import *
from access import *

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


def setup_meetings(base_path: str) -> bool:
    dl_meetings = input("Download ten sample meetings? (Y, N, default Y): ").strip().upper() or "Y"
    if dl_meetings == "Y":
        try:
            os.makedirs(base_path)
        except FileExistsError as e:
            print("Recordings directory already exists, exiting setup")
            return False
        
        download_meetings(base_path)

    elif not dl_meetings == "N":
        print("Invalid input, exiting setup")
        return False
        
    cr_meetings = input("Create meetings in DB? (Y, N, default Y): ").strip().upper() or "Y"
    if cr_meetings == "Y":
        asyncio.run(create_meetings(base_path))

    elif not dl_meetings == "N":
        print("Invalid input, exiting setup")
        return False
    
    return True

def setup_env() -> bool:
    env = Path(".env")
    if env.is_file():
        print("A .env file already exists, skipping .env file setup")
        return True
    
    openai_key = input("Enter your OpenAI API key (sk-proj-...): ").strip()
    if not openai_key[:8] == "sk-proj-":
        print("Invalid OpenAI API key, exiting setup")
        return False
    
    hf_token = input("Enter your Hugging Face token (hf_...): ").strip()
    if not hf_token[:3] == "hf_":
        print("Invalid Hugging Face token, exiting setup")
        return False
    
    hostname = input("Enter database hostname (default localhost): ").strip() or "localhost"
    if not len(hostname) > 0:
        print("Invalid hostname, exiting setup")
        return False
    
    port = input("Enter database port (default 5432): ").strip() or "5432"
    if not len(port) > 0:
        print("Invalid port, exiting setup")
        return False

    name = input("Enter database name (default deco3801): ").strip() or "deco3801"
    if not len(name) > 0:
        print("Invalid database name, exiting setup")
        return False

    username = input("Enter database username: ").strip()
    if not len(username) > 0:
        print("Invalid username, exiting setup")
        return False
    
    password = input("Enter database password: ").strip()
    if not len(password) > 0:
        print("Invalid password, exiting setup")
        return False
    
    container_name = input("Enter docker container name (default deco3801): ").strip() or "deco3801"
    if not len(container_name) > 0:
        print("Invalid container name, exiting setup")
        return False
    
    volume_name = input("Enter docker volume name (default deco3801): ").strip()  or "deco3801"
    if not len(volume_name) > 0:
        print("Invalid volume name, exiting setup")
        return False


    with open(env, 'w', encoding="utf-8") as env_file:
        env_file.write(f"OPENAI_API_KEY=\"{openai_key}\"\n")
        env_file.write(f"HF_TOKEN=\"{hf_token}\"\n")
        env_file.write(f"HOSTNAME=\"{hostname}\"\n")
        env_file.write(f"PORT=\"{port}\"\n")
        env_file.write(f"DB_NAME=\"{name}\"\n")
        env_file.write(f"DB_USER=\"{username}\"\n")
        env_file.write(f"DB_PASSWORD=\"{password}\"\n")
        env_file.write(f"CONTAINER_NAME=\"{container_name}\"\n")
        env_file.write(f"VOLUME_NAME=\"{volume_name}\"\n")
        
    return True

def setup_ollama() -> bool:
    print("Downloading nomic embedding using ollama")
    try:
        subprocess.call(["ollama", "pull", "nomic-embed-text"])
    except FileNotFoundError:
        print("ollama not found, exiting setup")
        return False
    
    return True

def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    print("==========================")
    print("Minutes in Seconds - Setup")
    print("==========================")
    

    if not setup_env():
        return

    load_dotenv()

    base_path = "data/recordings/"
    if not setup_meetings(base_path):
        return

    if os.getenv("EMBED_PROVIDER","ollama") == "ollama" and not setup_ollama():
        return


if __name__ == "__main__":
    main()    


