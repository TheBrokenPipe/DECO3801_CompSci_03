import asyncio
import sys
import os
import logging
import subprocess
import datetime
from pathlib import Path

import requests
import tqdm
from dotenv import load_dotenv

from backend.manager import Manager
from backend.docker_manager import DockerManager
from backend.database_manager import DB_Manager


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def download(url: str, filename: str, desc: str):
    with open(filename, 'wb') as file:
        with requests.get(url, stream=True) as request:
            request.raise_for_status()
            filesize = int(request.headers.get('content-length', 0))

            tqdm_params = {
                'desc': desc,
                'total': filesize,
                'dynamic_ncols': True,
                'miniters': 1,
                'unit': 'B',
                'unit_scale': True,
                'unit_divisor': 2**10,
            }
            with tqdm.tqdm(**tqdm_params) as progress_bar:
                for chunk in request.iter_content(chunk_size=2**12):
                    progress_bar.update(len(chunk))
                    file.write(chunk)


def download_meetings(base_path: str):
    baseurl = "https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/"

    meetings = ["ES2002a", "ES2002b", "ES2002c", "ES2002d", "EN2002a",
                "EN2002b", "EN2002c", "EN2002d", "EN2006a", "EN2006b"]

    for index, meeting in enumerate(meetings):
        url = f"{baseurl}{meeting}/audio/{meeting}.Mix-Headset.wav"
        filename = f"{base_path}{meeting}.Mix-Headset.wav"
        progress = f"{index+1:2d}/{len(meetings)}"
        description = f"{progress} {meeting}.Mix-Headset.wav"
        download(url, filename, description)


async def create_meetings(base_path: str):
    tqdm_params = {
        'desc': "Creating meetings",
        'total': 4,
        'dynamic_ncols': True,
        'miniters': 1,
    }
    with tqdm.tqdm(**tqdm_params) as progress_bar:
        with DockerManager(stop_when_done=False) as m:
            m.full_setup()
            progress_bar.update(1)

            await DB_Manager.full_setup()
            progress_bar.update(1)

            t = Manager()
            p = Path(base_path)
            tag_names = set()
            meetings = []
            for file in sorted(p.glob("*")):
                name = file.stem[:7]
                date = datetime.datetime.now()
                file_recording = str(file)
                file_transcript = ""
                summary = ""
                meeting = await t.create_meeting(name, date, file_recording,
                                                 file_transcript, summary)
                meetings.append(meeting)
                tag_names.add(file.stem[:6])
            progress_bar.update(1)

            for tag_name in sorted(tag_names):
                tag_meetings = []
                for meeting in meetings:
                    if meeting.name[:6] == tag_name:
                        tag_meetings.append(meeting)
                await t.create_tag(tag_name, tag_meetings)

            progress_bar.update(1)


def setup_meetings(base_path: str) -> bool:
    dl_meetings_prompt = "Download ten sample meetings? (Y, N, default Y): "
    dl_meetings = input(dl_meetings_prompt).strip().upper() or "Y"
    if dl_meetings == "Y":
        try:
            os.makedirs(base_path)
        except FileExistsError:
            print("Recordings directory already exists, exiting setup")
            return False

        download_meetings(base_path)

    elif not dl_meetings == "N":
        print("Invalid input, exiting setup")
        return False

    cr_meetings_prompt = "Create meetings in DB? (Y, N, default Y): "
    cr_meetings = input(cr_meetings_prompt).strip().upper() or "Y"
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

    hostname_prompt = "Enter database hostname (default localhost): "
    hostname = input(hostname_prompt).strip() or "localhost"
    if not len(hostname) > 0:
        print("Invalid hostname, exiting setup")
        return False

    port = input("Enter database port (default 5432): ").strip() or "5432"
    if not len(port) > 0:
        print("Invalid port, exiting setup")
        return False

    name_prompt = "Enter database name (default deco3801): "
    name = input(name_prompt).strip() or "deco3801"
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

    container_name_prompt = "Enter docker container name (default deco3801): "
    container_name = input(container_name_prompt).strip() or "deco3801"
    if not len(container_name) > 0:
        print("Invalid container name, exiting setup")
        return False

    volume_name_prompt = "Enter docker volume name (default deco3801): "
    volume_name = input(volume_name_prompt).strip() or "deco3801"
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
    ollama_prompt = "Pull nomic embedding using ollama? (Y, N, default Y): "
    ollama = input(ollama_prompt).strip().upper() or "Y"
    if ollama == "Y":
        try:
            subprocess.call(["ollama", "pull", "nomic-embed-text"])
        except FileNotFoundError:
            print("ollama not found, exiting setup")
            return False

    return True


def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.WARNING)

    print("==========================")
    print("Minutes in Seconds - Setup")
    print("==========================")

    if not setup_env():
        return

    load_dotenv()

    base_path = "data/recordings/"
    if not setup_meetings(base_path):
        return

    if not setup_ollama():
        return


if __name__ == "__main__":
    main()
