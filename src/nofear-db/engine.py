from orm import Document
from filter import QueryFilter

class StorageEngine:

    def __init__(self, root: str):
        self.__root = root
    
    def create(self, doc: Document):
        pass

    def update(self, doc: Document):
        pass

    def delete(self, doc: Document):
        pass

    def read(self, doc_type: Document, filter: QueryFilter):
        pass