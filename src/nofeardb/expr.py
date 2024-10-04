"""
NofearDB expression builder
"""

import operator

from abc import ABC, abstractmethod

from .orm import Document


class AbstractExpr(ABC):

    @abstractmethod
    def evaluate(self, instance: Document) -> bool:
        """
        evaluate the expression for the given document instance
        """


class Expr(AbstractExpr):

    def __init__(self, attr_name: str, value, op):
        self.__attr_name = attr_name
        self.__value = value
        self.__operator = op

    def evaluate(self, instance: Document) -> bool:
        attr_value = getattr(instance, self.__attr_name)

        if self.__operator == operator.contains:
            return self.__operator(self.__value, attr_value)

        return self.__operator(attr_value, self.__value)


class AndExpr(AbstractExpr):

    def __init__(self, expr1: 'AbstractExpr', expr2: 'AbstractExpr'):
        self.__expr1 = expr1
        self.__expr2 = expr2

    def evaluate(self, instance: Document) -> bool:
        return (
            self.__expr1.evaluate(instance)
            and self.__expr2.evaluate(instance)
        )


class OrExpr(AbstractExpr):

    def __init__(self, expr1: 'AbstractExpr', expr2: 'AbstractExpr'):
        self.__expr1 = expr1
        self.__expr2 = expr2

    def evaluate(self, instance: Document) -> bool:
        return (
            self.__expr1.evaluate(instance)
            or self.__expr2.evaluate(instance)
        )


def eq(attr_name, value) -> Expr:
    """
    Equals operator (==)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.eq)


def neq(attr_name, value) -> Expr:
    """
    Not equals operator (!=)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.ne)


def lt(attr_name, value) -> Expr:
    """
    Lower than operator (<)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.lt)


def lte(attr_name, value) -> Expr:
    """
    Lower than equals operator (<=)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.le)


def gt(attr_name, value) -> Expr:
    """
    Greater than operator (>)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.gt)


def gte(attr_name, value) -> Expr:
    """
    Greater than equals operator (>=)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.ge)


def is_in(attr_name, value) -> Expr:
    """
    Is in operator (in)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.contains)


def is_(attr_name, value) -> Expr:
    """
    Is operator (is)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.is_)


def is_not(attr_name, value) -> Expr:
    """
    Is not operator (is not)

    :param attr_name: Name of the document attribute to evaluate.
    :type attr_name: str
    :param value: Value to evaluate attribute against.

    :return: Expression.
    :rtype: :class:`nofeardb.expr.AbstractExpr`
    """
    return Expr(attr_name, value, operator.is_not)


def and_(expr1: AbstractExpr, expr2: AbstractExpr) -> AndExpr:
    """
    Logical AND operator (and)

    :param expr1: First expression.
    :type expr1: :class:`nofeardb.expr.Expr`
    :param expr2: Second expression.
    :type expr2: :class:`nofeardb.expr.Expr`

    :return: And Expression.
    :rtype: :class:`nofeardb.expr.AndExpr`
    """
    return AndExpr(expr1, expr2)


def or_(expr1: AbstractExpr, expr2: AbstractExpr) -> OrExpr:
    """
    Logical OR operator (or)

    :param expr1: First expression.
    :type expr1: :class:`nofeardb.expr.Expr`
    :param expr2: Second expression.
    :type expr2: :class:`nofeardb.expr.Expr`

    :return: Or Expression.
    :rtype: :class:`nofeardb.expr.OrExpr`
    """
    return OrExpr(expr1, expr2)
