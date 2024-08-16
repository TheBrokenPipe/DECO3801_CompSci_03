import faiss
import numpy as np
import os
from file_manager import FileManager
from bidict import bidict


class RAG:

    def __init__(self, file_manager: FileManager, n_dimensions: int = 400):
        self.n_dimensions = n_dimensions

        self.vdb_index: faiss.IndexFlatL2
        self.link_db: bidict

        self.file_manager = file_manager

        self.vdb_index, self.link_db = self.file_manager.load()
        if self.vdb_index is None or self.link_db is None:
            self.init_db()

    @property
    def size(self):
        return self.vdb_index.ntotal

    def init_db(self):
        assert self.vdb_index is None, "Vector database is already setup"
        self.vdb_index = faiss.IndexFlatL2(self.n_dimensions)  # L2 distance (Euclidean distance)

    def add_to_db(self, embedding: np.ndarray, file_path: str):
        # TODO verify / ensure size
        next_index = self.size
        self.vdb_index.add(np.atleast_2d(embedding))
        self.link_db[next_index] = file_path

    def get_closest_indexes(self, embedding: np.ndarray, k=5) -> tuple[list[float], list[int]]:
        """returns distances, indexes"""
        # TODO verify / ensure size
        return self.vdb_index.search(np.atleast_2d(embedding), k=k)

