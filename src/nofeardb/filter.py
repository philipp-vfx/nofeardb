from abc import abstractmethod
from typing import List

from .exceptions import NoResultFoundException
from .orm import Document


class QueryFilter:

    def __init__(self, original: List[Document], modified: List[Document] = None):
        self.__original = original or []
        self.__modified = modified
        if modified is None:
            self.__modified = self.__original

    def where(self, condition):
        """applies where condition and returns a new modified query filter object"""
        result = []
        for doc in self.__modified:
            if condition:
                result.append(doc)
        return QueryFilter(self.__original, result)

    def all(self):
        """get all results"""
        return self.__modified

    def first(self):
        """get first result"""
        if len(self.__modified) > 0:
            return self.__modified[0]

        raise NoResultFoundException

    def last(self):
        """get last result"""
        if len(self.__modified) > 0:
            return self.__modified[-1]

        raise NoResultFoundException
