import os
import json
from bidict import bidict
from faiss import IndexFlatL2, write_index, read_index
from typing import Union


class FileManager:

    def save_text_file(self, text: str, time_tag) -> str:
        file_path = f"./data/saved_docs/file_test.txt"
        audio_file_path = f"./data/saved_docs/transcripts_{time_tag}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return file_path
