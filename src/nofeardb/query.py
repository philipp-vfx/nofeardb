from abc import abstractmethod
from typing import List

from .exceptions import NoResultFoundException
from .orm import Document
from .expr import AbstractExpr


class Query:

    def __init__(self, original: List[Document], modified: List[Document] = None):
        self.__original = original or []
        self.__modified = modified
        if self.__modified is None:
            self.__modified = self.__original

    def where(self, expr: AbstractExpr) -> 'Query':
        """applies where condition and returns a new modified query object"""
        result = []
        for doc in self.__modified:
            if expr.evaluate(doc):
                result.append(doc)
        return Query(self.__original, result)

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
