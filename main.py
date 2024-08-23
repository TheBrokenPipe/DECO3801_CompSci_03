import os
from dotenv import load_dotenv
import faiss
from openai import OpenAI
from typing import Union
import numpy as np
from bidict import bidict

from file_manager import FileManager
from RAG import RAG
from ASR import ASR

load_dotenv()


class Thingo:

    def __init__(
        self, n_dimensions: int = 400,
        vector_db_path: str = "data/databases/index_file.index",
        link_db_path: str = "data/databases/link.json"
    ):
        self.open_ai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        self.vdb_index: Union[faiss.IndexFlatL2, None] = None

        self.file_manager = FileManager(
            vector_db_path,
            link_db_path
        )
        self.rag = RAG(self.file_manager, self.open_ai_client)
        self.asr = ASR(self.open_ai_client)

    def add_audio_meeting_transcript_document(self, file_path: str):
        """from path"""
        # assert False  # TODO save transcript as a txt file
        transcription = self.asr.transcribe_audio_file(file_path)
        summary = self.rag.summarise_meeting(transcription)['abstract_summary']  # TODO just using the abstract for now
        save_transcript_file_path = self.file_manager.save_text_file(summary)
        self.rag.add_document(summary, save_transcript_file_path)
        self.file_manager.save(self.rag.vdb_index, self.rag.link_db)

    def add_text_document(self, file_path: str):
        """from path"""
        with open(file_path, "r") as file:
            text = str(file.read())
        self.rag.add_document(text, file_path)
        self.file_manager.save(self.rag.vdb_index, self.rag.link_db)

    def query(self, query_text: str):
        return self.rag.query(query_text)



t = Thingo(10)  # need a metadatafile
print("Transcribing:")
# t.add_audio_meeting_transcript_document("data/audio_recordings/en-US_AntiBERTa_for_word_boosting_testing.wav")
# t.add_to_db(t.embed_text("Pizza hut"))
# t.save_db()

transcription = t.asr.transcribe_audio_file("data/audio_recordings/en-US_AntiBERTa_for_word_boosting_testing.wav")
print(transcription)


# em = t.embed_text(transcription)

# print()
# print("Num embeddings saved: ", t.rag.vdb_index.ntotal)
# print()

print(t.query("What does the llm do?"))


exit()
exit()

for i in ["pizza is tasty", "chatgpt is an llm used to design proteins", "protein"]:
    print(t.query(i))
    # em = t.rag.embed_text(i)
    # print(t.rag.get_closest_indexes(em, 1))

# t.file_manager.save(t.rag.vdb_index, t.rag.link_db)

# ids = t.vdb_index.reconstruct_n(0, t.vdb_index.ntotal)
# print("All IDs:", ids)
# print(t.transcribe_audio_file("en-US_AntiBERTa_for_word_boosting_testing.wav"))

