from .enums import DocumentStatus


class Document:

    __documentname__ = None

    def __init__(self):
        self.__status__ = DocumentStatus.NEW
        self.__attr_snap__ = {}

    def get_document_name(self):
        if self.__documentname__ is not None:
            return self.__documentname__

        return self.__class__.__name__.lower()

    def create_attribute_snapshot(self):
        pass


class Relationship:
    pass


class Field:
    pass
