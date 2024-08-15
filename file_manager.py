import faiss, json

class FileManager:

    def __init__(self):

        self.vector_db_path = vector_db_path
        self.link_db_path = link_db_path

        pass

    def save_db(self):
        assert self.vdb_index is not None, "Vector database is not setup"
        faiss.write_index(self.vdb_index, self.vector_db_path)

    def load_db(self):
        assert self.vdb_index is None, "Vector database is already setup"
        self.vdb_index = faiss.read_index(self.vector_db_path)

    def save_link(self):
        assert self.vdb_index is not None, "Vector database is not setup"
        with open(self.link_db_path, 'w') as file:
            json.dump(dict(self.link_db), file)

    def load_link(self):
        assert self.vdb_index is None, "Vector database is already setup"
        with open(self.link_db_path) as f:
            self.link_db = bidict(json.load(f))