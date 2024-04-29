"""
Handles entity models
"""

from abc import ABC, abstractmethod
from typing import List
import uuid
from .enums import DocumentStatus


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
        """get the name by which the document is identified in the database"""

        if self.__documentname__ is not None:
            return self.__documentname__

        return self.__class__.__name__.lower()

    def create_snapshot(self):
        """creates a snapshot of the data for restore purposes"""

        for name, attr in vars(self.__class__).items():
            if isinstance(attr, Field) or isinstance(attr, Relationship):
                try:
                    self.__data_snapshot__[name] = getattr(self, name).copy()
                except AttributeError:
                    self.__data_snapshot__[name] = getattr(self, name)

    def reset(self):
        """restores the last snapshot"""

        for name, value in self.__data_snapshot__.items():
            setattr(self, name, value)

        self.__changed_fields__ = []


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
    def back_populate_reverse_relationship(self, instance):
        """ execute back population on related items """

    @abstractmethod
    def clear_reverse_relationship(self, instance):
        """ remove back populated properties on related items """


class RelationshipList(list):
    """customized list holding one to many relationships."""

    def __init__(self, iterable, relationsip_owner, back_population):
        super(RelationshipList, self).__init__(iterable)
        self._relationship_owner = relationsip_owner
        self._back_populates = back_population

    def __setitem__(self, key, value: Document):
        to_replace = self[key]
        setattr(to_replace, self._back_populates + "_rel", None)
        setattr(value, self._back_populates + "_rel", self._relationship_owner)
        super(RelationshipList, self).__setitem__(key, value)

    def __delitem__(self, value):
        raise RuntimeError(
            "del for relationship items no allowed. Use \'remove\' instead")

    def __add__(self, value):
        raise RuntimeError("concatenation of relationships not allowed")

    def __iadd__(self, value):
        raise RuntimeError("concatenation of relationships not allowed")

    def remove(self, related_doc: Document):
        if related_doc in self:
            if self._back_populates is not None:
                setattr(related_doc, self._back_populates + "_rel", None)
                if related_doc.__status__ == DocumentStatus.SYNC:
                    related_doc.__status__ = DocumentStatus.MOD

            if self._relationship_owner.__status__ == DocumentStatus.SYNC:
                self._relationship_owner.__status__ = DocumentStatus.MOD
            super(RelationshipList, self).remove(related_doc)

    def append(self, related_doc: Document):
        if related_doc not in self:
            if self._back_populates is not None:
                setattr(related_doc, self._back_populates +
                        "_rel", self._relationship_owner)
                if related_doc.__status__ == DocumentStatus.SYNC:
                    related_doc.__status__ = DocumentStatus.MOD

            if self._relationship_owner.__status__ == DocumentStatus.SYNC:
                self._relationship_owner.__status__ = DocumentStatus.MOD
            super(RelationshipList, self).append(related_doc)


class OneToMany(Relationship):
    """descriptor for one to many relationships"""

    def get_relation(self, instance):
        """get the relationship from the instance"""
        try:
            return instance.__dict__[self._name + "_rel"]
        except KeyError:
            l = RelationshipList([], instance, self._back_populates)
            instance.__dict__[self._name + "_rel"] = l
            return instance.__dict__[self._name + "_rel"]

    def __get__(self, instance, owner):
        return self.get_relation(instance)

    def __set__(self, instance: Document, related_docs: List[Document]):
        print(related_docs)
        self.clear_reverse_relationship(instance)
        l = RelationshipList(related_docs, instance, self._back_populates)
        instance.__dict__[self._name + "_rel"] = l
        self.back_populate_reverse_relationship(instance)

        if instance.__status__ == DocumentStatus.SYNC:
            instance.__status__ = DocumentStatus.MOD

    def clear_reverse_relationship(self, instance):
        if self._back_populates is not None:
            related_docs = self.get_relation(instance)
            for related_doc in related_docs:
                setattr(related_doc, self._back_populates + "_rel", None)

    def back_populate_reverse_relationship(self, instance):
        if self._back_populates is not None:
            related_docs = self.get_relation(instance)
            for related_doc in related_docs:
                setattr(related_doc, self._back_populates + "_rel", instance)
                if related_doc.__status__ == DocumentStatus.SYNC:
                    related_doc.__status__ = DocumentStatus.MOD


class ManyToOne(Relationship):
    """descriptor for many to one relationships"""

    def get_relation(self, instance):
        """get the relationship from the instance"""
        try:
            return instance.__dict__[self._name + "_rel"]
        except KeyError:
            instance.__dict__[self._name + "_rel"] = None
            return instance.__dict__[self._name + "_rel"]

    def __get__(self, instance, owner):
        return self.get_relation(instance)

    def __set__(self, instance, related_doc: Document):
        self.clear_reverse_relationship(instance)
        instance.__dict__[self._name + "_rel"] = related_doc
        self.back_populate_reverse_relationship(instance)

        if instance.__status__ == DocumentStatus.SYNC:
            instance.__status__ = DocumentStatus.MOD

    def clear_reverse_relationship(self, instance):
        if self._back_populates is not None:
            related_doc = self.get_relation(instance)
            if related_doc is not None:
                owning_relationship = getattr(
                    related_doc, self._back_populates)
                owning_relationship.remove(instance)

    def back_populate_reverse_relationship(self, instance):
        if self._back_populates is not None:
            related_doc = self.get_relation(instance)
            if related_doc is not None:
                owning_relationship = getattr(
                    related_doc, self._back_populates)
                owning_relationship.append(instance)


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
            raise RuntimeError(
                "cannot set data on an already deleted document")

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
