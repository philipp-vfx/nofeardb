"""
Handles entity models
"""

from .enums import DocumentStatus


class Document:
    """
    Base class for all documents that should be stored in the database
    """

    __documentname__ = None

    def __init__(self):
        self.__status__ = DocumentStatus.NEW
        self.__changed_fields__ = []

    def get_document_name(self):
        if self.__documentname__ is not None:
            return self.__documentname__

        return self.__class__.__name__.lower()


class Relationship:
    """
    Descriptor for a relationship between documents
    """

    def __init__(self):
        self._name = None

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner):
        return instance.__dict__[self._name]

    def __set__(self, instance, value):
        instance.__dict__[self._name] = value


class Field:
    """
    Descriptor for a data field in a document
    """

    def __init__(self):
        self._name = None

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner):
        return instance.__dict__[self._name]

    def __set__(self, instance: Document, value):
        if self._name not in instance.__changed_fields__:
            instance.__changed_fields__.append(self._name)

        instance.__dict__[self._name] = value
