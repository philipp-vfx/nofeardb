"""
Engine Classes
"""

import os
import json
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
        """updates the json by modified fields of an object"""
        
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
    
    def resolve_dependencies(self, doc: Document, dependencies: List[Document] = []) -> List[Document]:
        """creates a stack with depending documents"""
        
        dependencies = []
            
        children = [doc]
        
        while len(children) > 0:
            child = children.pop()
            if child not in dependencies:
                dependencies.append(child)
                
            for name, attr in vars(child.__class__).items():                  
                if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                    for rel in getattr(child, name):
                        if rel not in children and rel not in dependencies:
                            children.append(rel)
                
                if isinstance(attr, ManyToOne):
                    if getattr(child, name) is not None:
                        if getattr(child, name) not in children and getattr(child, name) not in dependencies:
                            children.append(getattr(child, name))
            
        return dependencies
    
    def get_doc_basepath(self, doc: Document):
        """get the base file path for the document type"""
        return os.path.join(self._root, doc.get_document_name())
    
    def _get_document_with_id_existing(self, doc: Document):
        """Checks wether a document with the same ID already exists."""
        doc_base_path = self.get_doc_basepath(doc)
        existing_ids = [doc_name.split("__")[0] for doc_name in os.listdir(doc_base_path)]
        return str(doc.__id__) in existing_ids
    
    def _check_all_documents_valid(self, docs: List[Document]):
        """
        Checks wether all documents can be created or updated (no id collision, no locking etc.).
        If one document fails the check, a RuntimeError is raised.
        """
        for doc in docs:
            if doc.__status__ == DocumentStatus.NEW:
                if self._get_document_with_id_existing(doc):
                    raise RuntimeError(
                        "Document " 
                        + str(doc) 
                        + " is marked as new, but an document with the same ID is already existing.")
            if doc.__status__ == DocumentStatus.MOD:
                if not self._get_document_with_id_existing(doc):
                    raise RuntimeError(
                        "The document " 
                        + str(doc) 
                        + " is marked as modified, but no document with the id "
                        + str(doc.__id__) + " exists.")
            
        return True
    
    def create_write_json(self, doc: Document):
        """write the json file initially to the disk"""

        doc_path = os.path.join(self.get_doc_basepath(doc), doc.__id__ + "__" + doc.get_hash() + ".json")
        
        json_object = json.dumps(self.create_json(doc), indent=4)
        with open(doc_path, "w") as outfile:
            outfile.write(json_object)
            
    def update_write_json(self, doc: Document):
        """updates an existing json file"""

    def create(self, doc: Document):
        """create the document"""
        if doc.__status__ is not DocumentStatus.NEW:
            raise RuntimeError("The document is not new. Only new documents can be created")
        
        dependencies = self.resolve_dependencies(doc)
        if self._check_all_documents_valid(dependencies):
            for dep in dependencies:
                if dep.__status__ == DocumentStatus.NEW:
                    self.create_write_json(dep)
                    
                if dep.__status__ == DocumentStatus.MOD:
                    self.update_write_json(dep)
         
    def update(self, doc: Document):
        """update the document"""
        if doc.__status__ is DocumentStatus.NEW:
            raise RuntimeError("The document is not persisted. Please run \'create\' before.")
        
        if doc.__status__ is DocumentStatus.DEL:
            raise RuntimeError("Deleted documents cannot be updated")
        
        #TODO: implement locking strategy to avoid concurrent writes
        
        dependencies = self.resolve_dependencies(doc)
        if self._check_all_documents_valid(dependencies):
            for dep in dependencies:
                if dep.__status__ == DocumentStatus.NEW:
                    self.create_write_json(dep)
                    
                if dep.__status__ == DocumentStatus.MOD:
                    self.update_write_json(dep)

    def delete(self, doc: Document):
        """delete the document"""

    def read(self, doc_type: Document, query_filter: QueryFilter = None):
        """read the document"""
