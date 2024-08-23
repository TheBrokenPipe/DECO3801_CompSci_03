import os
import json
from bidict import bidict
from faiss import IndexFlatL2, write_index, read_index
from typing import Union


class FileManager:

    def __init__(self, vector_db_path, link_db_path):
        self.vector_db_path = vector_db_path
        self.link_db_path = link_db_path

    def save(self, vector_index: IndexFlatL2, link_db: bidict):
        return self.save_db(vector_index), self.save_link(link_db)

    def save_db(self, vector_index: IndexFlatL2):
        return write_index(vector_index, self.vector_db_path)

    def save_link(self, link_db: bidict):
        with open(self.link_db_path, 'w') as file:
            json.dump(dict(link_db), file)
        return True

    def load(self) -> Union[tuple[IndexFlatL2, bidict], tuple[None, None]]:
        return self.load_db(), self.load_link()

    def load_db(self) -> Union[IndexFlatL2, None]:
        if os.path.isfile(self.vector_db_path):
            vdb_index: IndexFlatL2 = read_index(self.vector_db_path)
            return vdb_index
        else:
            return None

    def load_link(self) -> Union[bidict, None]:
        if os.path.isfile(self.link_db_path):
            with open(self.link_db_path) as f:
                link_db = bidict(json.load(f))
            return link_db
        else:
            return None

    def save_text_file(self, text: str) -> str:
        file_path = "data/saved_docs/file_test.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return file_path
