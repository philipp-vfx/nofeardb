"""
Handles entity models
"""

from abc import ABC, abstractmethod
from typing import List
import uuid
import hashlib

from .datatypes import OrmDataType
from .enums import DocumentStatus


class Document:
    """
    Base class for all documents that should be stored in the database
    """

    __documentname__ = None
    __primary_key_attribute__ = None

    def __init__(self):
        self.__id__ = uuid.uuid4()
        self.__engine__ = None
        self.__status__ = DocumentStatus.NEW
        self.__changed_fields__ = []
        self.__added_relationships__ = {}
        self.__removed_relationships__ = {}
        self.__data_snapshot__ = {}

    @classmethod
    def get_document_name(cls):
        """
        Get the name by which the document is identified in the database

        :return: Name of the document
        :rtype: str
        """

        if cls.__documentname__ is not None:
            return cls.__documentname__

        return cls.__name__.lower()

    def set_relationship_added(self, rel_name: str, document: 'Document'):
        """
        Set a relationship in added state

        :param rel_name: Name of the relationship
        :type rel_name: str
        :param document: Document which should be related
        :type document: :class:`Document`
        """
        if rel_name in self.__removed_relationships__:
            if isinstance(self.__removed_relationships__[rel_name], list):
                if document in self.__removed_relationships__[rel_name]:
                    self.__removed_relationships__[rel_name].remove(document)

        if rel_name not in self.__added_relationships__:
            self.__added_relationships__[rel_name] = []

        if document is not None:
            if document not in self.__added_relationships__[rel_name]:
                self.__added_relationships__[rel_name].append(document)

    def set_relationship_removed(self, rel_name: str, document: 'Document'):
        """
        Set a relationsip in removed state

        :param rel_name: Name of the relationship
        :type rel_name: str
        :param document: Document which is related
        :type document: :class:`Document`
        """
        if rel_name in self.__added_relationships__:
            if isinstance(self.__added_relationships__[rel_name], list):
                if document in self.__added_relationships__[rel_name]:
                    self.__added_relationships__[rel_name].remove(document)

        if rel_name not in self.__removed_relationships__:
            self.__removed_relationships__[rel_name] = []

        if document is not None:
            if document not in self.__removed_relationships__[rel_name]:
                self.__removed_relationships__[rel_name].append(document)

    def create_snapshot(self):
        """Creates a snapshot of the data for restore purposes"""

        for name, attr in vars(self.__class__).items():
            if isinstance(attr, Field) or isinstance(attr, Relationship):
                try:
                    self.__data_snapshot__[name] = getattr(self, name).copy()
                except AttributeError:
                    self.__data_snapshot__[name] = getattr(self, name)

    def validate(self) -> List[str]:
        """
        Validates the object and returns a list of found errors

        :return: List of all found errors
        :rtype: str, list
        """
        errors = []
        for name, attr in vars(self.__class__).items():
            if isinstance(attr, Field) or isinstance(attr, Field):
                if attr.nullable is False and getattr(self, name) is None:
                    errors.append(
                        "Attribute \""
                        + name
                        + "\" of document \""
                        + self.get_document_name()
                        + "\" is not nullable, but the value is None")

        return errors

    def reset(self):
        """Restores the last snapshot"""

        for name, value in self.__data_snapshot__.items():
            setattr(self, name, value)

        self.__changed_fields__ = []

    def get_hash(self):
        """
        Calculates the hash value for the document

        :return: Hash value for all attributes
        :rtype: str
        """
        m = hashlib.md5()

        for name, attr in vars(self.__class__).items():
            if isinstance(attr, Field):
                m.update(name.encode())
                field_type: OrmDataType = getattr(
                    self, name + "__datatype")
                attr_value = getattr(self, name)
                if attr_value is not None:
                    m.update(str(field_type.serialize(
                        attr_value)).encode())
                else:
                    m.update(str(None).encode())
            if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                m.update(name.encode())
                m.update(str([str(doc.__id__)
                              for doc in getattr(self, name)]).encode())
            if isinstance(attr, ManyToOne):
                m.update(name.encode())
                if getattr(self, name) is not None:
                    m.update(str(getattr(self, name).__id__).encode())

        return str(m.hexdigest())


class Relationship(ABC):
    """
    Descriptor for a relationship between documents
    """

    def __init__(self, class_name, back_populates=None, cascade: List[str] = None):
        self._name = None
        self._rel_class_name = class_name
        self._back_populates = back_populates
        self.cascade = cascade or []

    def __set_name__(self, owner, name):
        self._name = name

    def lazy_load_documents(self, rel_docs: List[Document]):
        """loads data for all documents that are marked as lazy"""
        for rel_doc in rel_docs:
            if rel_doc is not None and isinstance(rel_doc, Document):
                if rel_doc.__status__ == DocumentStatus.LAZY:
                    engine = rel_doc.__engine__
                    if engine is None:
                        raise RuntimeError(
                            "The lazy document that should be loaded is not bound to an engine."
                            + "That could mean, "
                            + "that the document was not created by an engine initially."
                        )

                    engine.lazy_load(rel_doc)

    @abstractmethod
    def back_populate_reverse_relationship(self, instance):
        """ execute back population on related items """

    @abstractmethod
    def clear_reverse_relationship(self, instance):
        """ remove back populated properties on related items """


class OneToManyList(list):
    """customized list holding one to many relationships."""

    def __init__(self, iterable, relationsip_owner: Document, back_population, relationship_name):
        super(OneToManyList, self).__init__(iterable)
        self._relationship_owner = relationsip_owner
        self._back_populates = back_population
        self._relationship_name = relationship_name

    def __setitem__(self, key, value: Document):
        if value.__id__ in [doc.__id__ for doc in self]:
            raise RuntimeError(
                "cannot add two documents with the same ID " + str(value.__id__))

        to_replace = self[key]
        self._relationship_owner.set_relationship_removed(
            self._relationship_name, to_replace)

        if self._back_populates is not None:
            setattr(to_replace, self._back_populates + "_rel", None)
            to_replace.set_relationship_removed(
                self._back_populates, self._relationship_owner)
            setattr(value, self._back_populates +
                    "_rel", self._relationship_owner)
            value.set_relationship_added(
                self._back_populates, self._relationship_owner)

            if to_replace.__status__ == DocumentStatus.SYNC:
                to_replace.__status__ = DocumentStatus.MOD

        self._relationship_owner.set_relationship_added(
            self._relationship_name, value)

        if value.__status__ == DocumentStatus.SYNC:
            value.__status__ = DocumentStatus.MOD

        if self._relationship_owner.__status__ == DocumentStatus.SYNC:
            self._relationship_owner.__status__ = DocumentStatus.MOD

        super(OneToManyList, self).__setitem__(key, value)

    def __delitem__(self, value):
        raise RuntimeError(
            "del for relationship items no allowed. Use \'remove\' instead")

    def __add__(self, value):
        raise RuntimeError("concatenation of relationships not allowed")

    def __iadd__(self, value):
        raise RuntimeError("concatenation of relationships not allowed")

    def extend(self, value):
        raise RuntimeError("extending of relationships not allowed")

    def remove(self, related_doc: Document):
        if related_doc in self:
            if self._back_populates is not None:
                setattr(related_doc, self._back_populates + "_rel", None)
                related_doc.set_relationship_removed(
                    self._back_populates, self._relationship_owner)
                if related_doc.__status__ == DocumentStatus.SYNC:
                    related_doc.__status__ = DocumentStatus.MOD

            self._relationship_owner.set_relationship_removed(
                self._relationship_name, related_doc)
            if self._relationship_owner.__status__ == DocumentStatus.SYNC:
                self._relationship_owner.__status__ = DocumentStatus.MOD
            super(OneToManyList, self).remove(related_doc)

    def append(self, related_doc: Document):
        if related_doc not in self:
            if related_doc.__id__ in [doc.__id__ for doc in self]:
                raise RuntimeError(
                    "cannot add two documents with the same ID " + str(related_doc.__id__))

            if self._back_populates is not None:
                setattr(related_doc, self._back_populates +
                        "_rel", self._relationship_owner)
                related_doc.set_relationship_added(
                    self._back_populates, self._relationship_owner)
                if related_doc.__status__ == DocumentStatus.SYNC:
                    related_doc.__status__ = DocumentStatus.MOD

            self._relationship_owner.set_relationship_added(
                self._relationship_name, related_doc)
            if self._relationship_owner.__status__ == DocumentStatus.SYNC:
                self._relationship_owner.__status__ = DocumentStatus.MOD
            super(OneToManyList, self).append(related_doc)


class ManyToManyList(list):
    """customized list holding many to many relationships."""

    def __init__(self, iterable, relationsip_owner: Document, back_population, relationship_name):
        super(ManyToManyList, self).__init__(iterable)
        self._relationship_owner = relationsip_owner
        self._back_populates = back_population
        self._relationship_name = relationship_name

    def __setitem__(self, key, value: Document):
        if self._relationship_owner.__status__ == DocumentStatus.DEL:
            raise RuntimeError("deleted object cannot be modified")

        if value.__id__ in [doc.__id__ for doc in self]:
            raise RuntimeError(
                "cannot add two documents with the same ID " + str(value.__id__))

        to_replace = self[key]
        self._relationship_owner.set_relationship_removed(
            self._relationship_name, to_replace)

        if self._back_populates is not None:

            self.__backpopulate_remove(to_replace)
            to_replace.set_relationship_removed(
                self._back_populates, self._relationship_owner)

            self.__backpopulate_append(value)
            value.set_relationship_added(
                self._back_populates, self._relationship_owner)

        self._relationship_owner.set_relationship_added(
            self._relationship_name, value)

        if self._relationship_owner.__status__ == DocumentStatus.SYNC:
            self._relationship_owner.__status__ = DocumentStatus.MOD

        super(ManyToManyList, self).__setitem__(key, value)

    def __delitem__(self, value):
        raise RuntimeError(
            "del for relationship items no allowed. Use \'remove\' instead")

    def __add__(self, value):
        raise RuntimeError("concatenation of relationships not allowed")

    def __iadd__(self, value):
        raise RuntimeError("concatenation of relationships not allowed")

    def extend(self, value):
        raise RuntimeError("extending of relationships not allowed")

    def __backpopulate_remove(self, related_doc):
        inverse_relationship = getattr(
            related_doc, self._back_populates)

        if self._relationship_owner in inverse_relationship:
            inverse_relationship.remove_without_back_propagation(
                self._relationship_owner)

    def __backpopulate_append(self, related_doc):
        inverse_relationship = getattr(
            related_doc, self._back_populates)
        if self._relationship_owner not in inverse_relationship:
            inverse_relationship.append_without_back_propagation(
                self._relationship_owner)

    def remove_without_back_propagation(self, related_doc: Document):
        """
        Removes an entity from the relationship list without propagating it to the related entity.
        """
        if related_doc in self:
            super(ManyToManyList, self).remove(related_doc)

            self._relationship_owner.set_relationship_removed(
                self._relationship_name, related_doc)
            if self._relationship_owner.__status__ == DocumentStatus.SYNC:
                self._relationship_owner.__status__ = DocumentStatus.MOD

    def append_without_back_propagation(self, related_doc: Document):
        """
        Appends an entity to the the relationship list without propagating it to the related entity.
        """
        if related_doc.__id__ in [doc.__id__ for doc in self]:
            raise RuntimeError(
                "cannot add two documents with the same ID " + str(related_doc.__id__))

        if related_doc not in self:
            super(ManyToManyList, self).append(related_doc)

            self._relationship_owner.set_relationship_added(
                self._relationship_name, related_doc)
            if self._relationship_owner.__status__ == DocumentStatus.SYNC:
                self._relationship_owner.__status__ = DocumentStatus.MOD

    def remove(self, related_doc: Document):
        if self._relationship_owner.__status__ == DocumentStatus.DEL:
            raise RuntimeError("deleted object cannot be modified")

        if related_doc in self:
            self.remove_without_back_propagation(related_doc)

            # BACK PROPAGATION
            if self._back_populates is not None:
                self.__backpopulate_remove(related_doc)
                related_doc.set_relationship_removed(
                    self._back_populates, self._relationship_owner)

    def append(self, related_doc: Document):
        if self._relationship_owner.__status__ == DocumentStatus.DEL:
            raise RuntimeError("deleted object cannot be modified")

        if related_doc not in self:
            self.append_without_back_propagation(related_doc)

            # BACK PROPAGATION
            if self._back_populates is not None:
                self.__backpopulate_append(related_doc)
                related_doc.set_relationship_added(
                    self._back_populates, self._relationship_owner)


class OneToMany(Relationship):
    """descriptor for one to many relationships"""

    def get_relation(self, instance) -> List[Document]:
        """get the relationship from the instance"""
        try:
            return instance.__dict__[self._name + "_rel"]
        except KeyError:
            l = OneToManyList(
                [], instance, self._back_populates, self._name)
            instance.__dict__[self._name + "_rel"] = l
            return instance.__dict__[self._name + "_rel"]

    def __get__(self, instance, owner):
        rel_docs = self.get_relation(instance)
        self.lazy_load_documents(rel_docs)
        return rel_docs

    def __set__(self, instance: Document, related_docs: List[Document]):
        self.clear_reverse_relationship(instance)

        doc_ids = []
        for doc in related_docs:
            if doc.__id__ in doc_ids:
                raise RuntimeError(
                    "cannot add two documents with the same ID " + str(doc.__id__))

            doc_ids.append(doc.__id__)

        if hasattr(instance, self._name + "_rel"):
            prev_instances = getattr(instance, self._name + "_rel")
            if prev_instances is not None:
                self.set_relationships_removed(instance, prev_instances)

        l = OneToManyList(related_docs, instance,
                          self._back_populates, self._name)
        instance.__dict__[self._name + "_rel"] = l

        self.set_relationships_added(instance, related_docs)

        self.back_populate_reverse_relationship(instance)

        if instance.__status__ == DocumentStatus.SYNC:
            instance.__status__ = DocumentStatus.MOD

    def set_relationships_removed(self, instance: Document, removed_documents: List[Document]):
        """track a relationship to another document as removed"""

        for removed_document in removed_documents:
            instance.set_relationship_removed(self._name, removed_document)

    def set_relationships_added(self, instance: Document, added_documents: List[Document]):
        """track a relationship to another document as added"""

        for added_document in added_documents:
            instance.set_relationship_added(self._name, added_document)

    def clear_reverse_relationship(self, instance):
        if self._back_populates is not None:
            related_docs = self.get_relation(instance)
            for related_doc in related_docs:
                setattr(related_doc, self._back_populates + "_rel", None)
                related_doc.set_relationship_removed(
                    self._back_populates, instance)
                if related_doc.__status__ == DocumentStatus.SYNC:
                    related_doc.__status__ = DocumentStatus.MOD

    def back_populate_reverse_relationship(self, instance):
        if self._back_populates is not None:
            related_docs = self.get_relation(instance)
            for related_doc in related_docs:
                setattr(related_doc, self._back_populates + "_rel", instance)
                related_doc.set_relationship_added(
                    self._back_populates, instance)
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
        rel_doc = self.get_relation(instance)
        self.lazy_load_documents([rel_doc])
        return rel_doc

    def __set__(self, instance: Document, related_doc: Document):
        self.clear_reverse_relationship(instance)
        if hasattr(instance, self._name + "_rel"):
            prev_instance = getattr(instance, self._name + "_rel")
            if prev_instance is not None:
                instance.set_relationship_removed(self._name, prev_instance)
        instance.__dict__[self._name + "_rel"] = related_doc
        instance.set_relationship_added(self._name, related_doc)
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


class ManyToMany(Relationship):
    """descriptor for many to many relationships"""

    def get_relation(self, instance) -> List[Document]:
        """get the relationship from the instance"""
        try:
            return instance.__dict__[self._name + "_rel"]
        except KeyError:
            l = ManyToManyList(
                [], instance, self._back_populates, self._name)
            instance.__dict__[self._name + "_rel"] = l
            return instance.__dict__[self._name + "_rel"]

    def __get__(self, instance, owner):
        rel_docs = self.get_relation(instance)
        self.lazy_load_documents(rel_docs)
        return rel_docs

    def __set__(self, instance: Document, related_docs: List[Document]):
        if instance.__status__ == DocumentStatus.DEL:
            raise RuntimeError("deleted object cannot be modified")

        doc_ids = []
        for doc in related_docs:
            if doc.__id__ in doc_ids:
                raise RuntimeError(
                    "cannot add two documents with the same ID " + str(doc.__id__))

            doc_ids.append(doc.__id__)

        self.clear_reverse_relationship(instance)

        if hasattr(instance, self._name + "_rel"):
            prev_instances = getattr(instance, self._name + "_rel")
            if prev_instances is not None:
                self.set_relationships_removed(instance, prev_instances)

        l = ManyToManyList(related_docs, instance,
                           self._back_populates, self._name)
        instance.__dict__[self._name + "_rel"] = l

        self.set_relationships_added(instance, related_docs)

        self.back_populate_reverse_relationship(instance)

        if instance.__status__ == DocumentStatus.SYNC:
            instance.__status__ = DocumentStatus.MOD

    def set_relationships_removed(self, instance: Document, removed_documents: List[Document]):
        """track a relationship to another document as removed"""

        for removed_document in removed_documents:
            instance.set_relationship_removed(self._name, removed_document)

    def set_relationships_added(self, instance: Document, added_documents: List[Document]):
        """track a relationship to another document as added"""

        for added_document in added_documents:
            instance.set_relationship_added(self._name, added_document)

    def clear_reverse_relationship(self, instance):
        if self._back_populates is not None:
            related_docs = self.get_relation(instance)
            for related_doc in related_docs:
                inverse_relationship = getattr(
                    related_doc, self._back_populates)
                related_doc.set_relationship_removed(
                    self._back_populates, instance)
                inverse_relationship.remove_without_back_propagation(instance)

    def back_populate_reverse_relationship(self, instance):
        if self._back_populates is not None:
            related_docs = self.get_relation(instance)
            for related_doc in related_docs:
                inverse_relationship = getattr(
                    related_doc, self._back_populates)
                inverse_relationship.append_without_back_propagation(instance)
                related_doc.set_relationship_added(
                    self._back_populates, instance)


class Field:
    """
    Descriptor for a data field in a document
    """

    def __init__(self, datatype: OrmDataType, primary_key=False, nullable=True):
        self._name = None
        self._primary_key = primary_key
        self.nullable = nullable
        self._datatype = datatype

    def __set_name__(self, owner, name):
        self._name = name
        setattr(owner, self._name + "__datatype", self._datatype)
        if self._primary_key:
            setattr(owner, "__primary_key_attribute__", self._name)

    def __get__(self, instance: Document, owner):
        try:
            if self._primary_key:
                return instance.__id__

            return instance.__dict__[self._name]
        except KeyError:
            return None

    def __set__(self, instance: Document, value):
        if instance.__status__ == DocumentStatus.DEL:
            raise RuntimeError(
                "cannot set data on an already deleted document")

        if not self.nullable and value is None:
            raise ValueError("cannot set None on non nullable field")

        if instance.__status__ == DocumentStatus.SYNC:
            instance.__status__ = DocumentStatus.MOD

        if self._primary_key:
            key = self._datatype.cast(value)
            if not isinstance(key, uuid.UUID):
                raise ValueError("primary key must be of type UUID")
            instance.__id__ = key

        if (
            self._name not in instance.__changed_fields__
            and instance.__status__ != DocumentStatus.NEW
        ):
            instance.__changed_fields__.append(self._name)

        if value is not None:
            value = self._datatype.cast(value)

        instance.__dict__[self._name] = value
