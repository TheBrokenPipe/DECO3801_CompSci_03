import asyncio
import sys
import os
from dotenv import load_dotenv
from backend.docker_manager import DockerManager
from backend.database_manager import DB_Manager
import logging
from models import *
from access import *
from backend.RAG_local import RAG
from backend.ASR import ASR

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Ingestion:
    def __init__(self):
        self.rag = RAG()
        self.asr = ASR(os.environ['HF_TOKEN'])
        self.logger = logging.getLogger(__name__)

    async def ingest_next_meeting(self):
        meetings = await select_ingestion_meeting(Meeting,(""),("summary"))
        if len(meetings) > 0:
            meeting = meetings[0]
            with open(meeting.file_transcript, 'r', encoding="utf-8") as file:
                transcript = file.read()

            full_summary = self.rag.summarise_meeting(transcript)
            self.logger.debug(full_summary)

            meeting.summary = full_summary['abstract_summary']
            await update_table(meeting)

            for action_item in full_summary['action_items'].action_items:
                await self.create_action_item(action_item, meeting)

            for key_point in full_summary['key_points'].key_points:
                await self.create_key_point(key_point, meeting)
            
            # TODO: RAG chunking and embedding goes here
            
    async def transcribe_next_meeting(self):
        meetings = await select_many_from_table(Meeting,(""),("file_transcript"))
        if len(meetings) > 0:
            meeting = meetings[0]
            recording = meeting.file_recording
            meeting.file_transcript = self.asr.transcribe_audio_file(recording)
            await update_table(meeting)
    

async def main():
    with DockerManager(stop_when_done=False) as m:
        m.full_setup()
        await DB_Manager.full_setup()
        ingestion = Ingestion()
        while True:
            await ingestion.transcribe_next_meeting()
            await ingestion.ingest_next_meeting()
        
        
asyncio.run(main())
