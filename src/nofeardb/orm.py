"""
Handles entity models
"""

from abc import ABC, abstractmethod
import uuid
from .enums import DocumentStatus, RelationshipType


class Document:
    """
    Base class for all documents that should be stored in the database
    """

    __documentname__ = None

    def __init__(self):
        self.__id__ = uuid.uuid4()
        self.__status__ = DocumentStatus.NEW
        self.__changed_fields__ = []
        self.__data_snapshot__ = {}

    def get_document_name(self):
        if self.__documentname__ is not None:
            return self.__documentname__

        return self.__class__.__name__.lower()
    
    def create_snapshot(self):
        self.__data_snapshot__ = self.__dict__.copy()
        
    def reset(self):
        self.__dict__ = self.__data_snapshot__


class Relationship(ABC):
    """
    Descriptor for a relationship between documents
    """

    def __init__(self, class_name, back_populates=None):
        self._name = None
        self._rel_class_name = class_name
        self._back_populates = back_populates
        
    def __set_name__(self, owner, name):
        self._name = name
        
    @abstractmethod
    def back_populate(self):
        """ execute back population on related items """
    
    @abstractmethod
    def remove_from_old_rel(self):
        """ remove back populated properties on related items """
    
class RelationshipList(list):
    
    def set_owner(self, instance):
        self._owner = instance
        
    def set_back_populate(self, back_populates):
        self._back_populates = back_populates
        
    def __setitem__(self, key, value: Document):
        to_replace = self[key]
        setattr(to_replace, self._back_populates + "_rel", None)
        setattr(value, self._back_populates + "_rel", self._owner)
        super(RelationshipList, self).__setitem__(key, value)

    def __delitem__(self, value):
        raise RuntimeError("del for relationship items no allowed. Use \'remove\' instead")

    def __add__(self, value):
        raise RuntimeError("concatenation of relationships not allowed")

    def __iadd__(self, value):
        raise RuntimeError("concatenation of relationships not allowed")
        
    def remove(self, value: Document):
        if value in self:
            setattr(value, self._back_populates + "_rel", None)
            super(RelationshipList, self).remove(value)
        
    def append(self, value: Document):
        if value not in self:
            setattr(value, self._back_populates + "_rel", self._owner)
            super(RelationshipList, self).append(value)
                    

class OneToMany(Relationship):
    
    def __init__(self, class_name, back_populates=None):
        super(OneToMany, self).__init__(class_name, back_populates)
        
    def get_relation(self, instance):
        try:
            l = instance.__dict__[self._name + "_rel"]
            l.set_owner = instance
            return l
        except KeyError:
            l = RelationshipList()
            l.set_owner(instance)
            l.set_back_populate(self._back_populates)
            instance.__dict__[self._name + "_rel"] = l
            return instance.__dict__[self._name + "_rel"]

    def __get__(self, instance, owner):
        return self.get_relation(instance)

    def __set__(self, instance, value):
        self.remove_from_old_rel(instance)
        l = RelationshipList(value)
        l.set_owner(instance)
        l.set_back_populate(self._back_populates)
        instance.__dict__[self._name + "_rel"] = l
        self.back_populate(instance)
        
    def remove_from_old_rel(self, instance):
        if self._back_populates is not None:
            for rel in self.get_relation(instance):
                setattr(rel, self._back_populates + "_rel", None)
    
    def back_populate(self, instance):
        if self._back_populates is not None:
            for rel in self.get_relation(instance):
                setattr(rel, self._back_populates + "_rel", instance)
    

class ManyToOne(Relationship):
    
    def __init__(self, class_name, back_populates=None):
        super(ManyToOne, self).__init__(class_name, back_populates)
        self._relation = None
        
    def get_relation(self, instance):
        try:
            return instance.__dict__[self._name + "_rel"]
        except KeyError:
            instance.__dict__[self._name + "_rel"] = None
            return instance.__dict__[self._name + "_rel"]

    def __get__(self, instance, owner):
        return self.get_relation(instance)

    def __set__(self, instance, value: Document):
        self.remove_from_old_rel(instance)
        instance.__dict__[self._name + "_rel"] = value
        self.back_populate(instance)
            
    def remove_from_old_rel(self, instance):
        if self._back_populates is not None:
            if self.get_relation(instance) is not None:
                owning = getattr(self.get_relation(instance), self._back_populates)
                owning.remove(instance)
    
    def back_populate(self, instance):
        if self._back_populates is not None:
            if self.get_relation(instance) is not None:
                owning = getattr(self.get_relation(instance), self._back_populates)
                owning.append(instance)


class Field:
    """
    Descriptor for a data field in a document
    """

    def __init__(self, primary_key=False, nullable=True):
        self._name = None
        self._primary_key = primary_key
        self._nullable = nullable

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance: Document, owner):
        if self._primary_key:
            return instance.__id__
        
        return instance.__dict__[self._name]

    def __set__(self, instance: Document, value):
        if instance.__status__ == DocumentStatus.DEL:
            raise RuntimeError("cannot set data on an already deleted document")
        
        if not self._nullable and value is None:
            raise ValueError("cannot set None on non nullable field")
        
        if instance.__status__ == DocumentStatus.SYNC:
            instance.__status__ = DocumentStatus.MOD
        
        if self._primary_key:
            if not isinstance(value, uuid.UUID):
                raise ValueError("primary key must be of type UUID")
            instance.__id__ = value
            
        if (
            self._name not in instance.__changed_fields__ 
            and instance.__status__ != DocumentStatus.NEW
        ):
            instance.__changed_fields__.append(self._name)

        instance.__dict__[self._name] = value
