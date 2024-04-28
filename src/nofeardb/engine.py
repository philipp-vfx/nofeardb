"""
Engine Classes
"""

from .orm import Document
from .filter import QueryFilter


class StorageEngine:
    """Storage Engine Class"""

    def __init__(self, root: str):
        self.__root = root

    def create(self, doc: Document):
        """create the document"""
        pass

    def update(self, doc: Document):
        """update the document"""
        pass

    def delete(self, doc: Document):
        """delete the document"""
        pass

    def read(self, doc_type: Document, query_filter: QueryFilter):
        """read the document"""
        pass
