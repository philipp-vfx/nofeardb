"""
Engine Classes
"""

from typing import List
from .orm import Document
from .filter import QueryFilter


class StorageEngine:
    """Storage Engine Class"""

    def __init__(self, root: str):
        self._root = root
        self._models = []

    def register_models(self, models: List[type]):
        """
        Register the model classes to the storage engine. 
        Needed to recosntruct the models from json.
        """
        for model in models:
            if not isinstance(model, Document):
                raise ValueError(str(model) + " is not of type \'Document\'")

        self._models = models

    def create(self, doc: Document):
        """create the document"""
        pass

    def update(self, doc: Document):
        """update the document"""
        pass

    def delete(self, doc: Document):
        """delete the document"""
        pass

    def read(self, doc_type: Document, query_filter: QueryFilter = None):
        """read the document"""
        pass
