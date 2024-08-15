import faiss
import json
from bidict import bidict


class FileManager:

    def __init__(self, vector_db_path, link_db_path):
        self.vector_db_path = vector_db_path
        self.link_db_path = link_db_path

    def save_db(self, vector_index: faiss.IndexFlatL2):
        faiss.write_index(vector_index, self.vector_db_path)

    def load_db(self) -> faiss.IndexFlatL2:
        vdb_index: faiss.IndexFlatL2 = faiss.read_index(self.vector_db_path)
        return vdb_index

    def save_link(self, link_db: bidict):
        with open(self.link_db_path, 'w') as file:
            json.dump(dict(link_db), file)

    def load_link(self) -> bidict:
        with open(self.link_db_path) as f:
            link_db = bidict(json.load(f))
        return link_db
