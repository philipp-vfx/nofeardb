"""
Engine Classes
"""

from typing import List

from .datatypes import OrmDataType
from .enums import DocumentStatus
from .orm import Document, Field, ManyToMany, ManyToOne, OneToMany
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
            if not issubclass(model, Document):
                raise ValueError(str(model) + " is not of type \'Document\'")

        for model in models:
            if model not in self._models:
                self._models.append(model)

    def create_json(self, doc: Document) -> dict:
        """creates the json that should be stored for a new object"""
        
        json = {}
        
        for name, attr in vars(doc.__class__).items():
            json["id"] = str(doc.__id__)
            if isinstance(attr, Field):
                if name != doc.__primary_key_attribute__:
                    field_type: OrmDataType = getattr(doc, name + "__datatype")
                    json[name] = field_type.serialize(getattr(doc, name))
                    
            if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                json[name] = [str(rel.__id__) for rel in getattr(doc, name)]
            
            if isinstance(attr, ManyToOne):
                if getattr(doc, name) is not None:
                    json[name] = str(getattr(doc, name).__id__)
                else:
                    json[name] = None
        
        return json

    def update_json(self, json: dict, doc: Document) -> dict:
        """updates a the json by modified fields of an object"""
        
        for name, attr in vars(doc.__class__).items():
            if name in doc.__changed_fields__:
                if isinstance(attr, Field):
                    field_type: OrmDataType = getattr(doc, name + "__datatype")
                    json[name] = field_type.serialize(getattr(doc, name))
                    
            if name in doc.__added_relationships__:
                if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                    if doc.__added_relationships__[name] is not None:
                        for rel in doc.__added_relationships__[name]:
                            if name in json.keys():
                                if str(rel.__id__) not in json[name]:
                                    json[name].append(str(rel.__id__))
                            else:
                                json[name] = [str(rel.__id__)]
                
                if isinstance(attr, ManyToOne):
                    if doc.__added_relationships__[name] is not None:
                        for rel in doc.__added_relationships__[name]:
                            json[name] = str(rel.__id__)
            
            if name in doc.__removed_relationships__:
                if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                    if doc.__removed_relationships__[name] is not None:
                        for rel in doc.__removed_relationships__[name]:
                            if name in json.keys():
                                if str(rel.__id__) in json[name]:
                                    json[name].remove(str(rel.__id__))
                
                if isinstance(attr, ManyToOne):
                    if doc.__removed_relationships__[name] is not None:
                        for rel in doc.__removed_relationships__[name]:
                            if json[name] == str(rel.__id__):
                                json[name] = None
                
        return json

    def create(self, doc: Document):
        """create the document"""
        if doc.__status__ is not DocumentStatus.NEW:
            raise RuntimeError("The document is not new. Only new documents can be created")

    def update(self, doc: Document):
        """update the document"""
        if doc.__status__ is DocumentStatus.NEW:
            raise RuntimeError("The document is not persisted. Please run \'create\' before.")
        
        if doc.__status__ is DocumentStatus.DEL:
            raise RuntimeError("Deleted documents cannot be updated")

    def delete(self, doc: Document):
        """delete the document"""

    def read(self, doc_type: Document, query_filter: QueryFilter = None):
        """read the document"""
