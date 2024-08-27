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
    
    def __init__(self, attr_name: str, value, operator):
        self.__attr_name = attr_name
        self.__value = value
        self.__operator = operator
    
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
    return Expr(attr_name, value, operator.eq)

def neq(attr_name, value) -> Expr:
    return Expr(attr_name, value, operator.ne)

def lt(attr_name, value) -> Expr:
    return Expr(attr_name, value, operator.lt)

def lte(attr_name, value) -> Expr:
    return Expr(attr_name, value, operator.le)

def gt(attr_name, value) -> Expr:
    return Expr(attr_name, value, operator.gt)

def gte(attr_name, value) -> Expr:
    return Expr(attr_name, value, operator.ge)

def is_in(attr_name, value) -> Expr:
    return Expr(attr_name, value, operator.contains)

def is_(attr_name, value) -> Expr:
    return Expr(attr_name, value, operator.is_)

def is_not(attr_name, value) -> Expr:
    return Expr(attr_name, value, operator.is_not)

def and_(expr1: AbstractExpr, expr2: AbstractExpr) -> AndExpr:
    return AndExpr(expr1, expr2)

def or_(expr1: AbstractExpr, expr2: AbstractExpr) -> OrExpr:
    return OrExpr(expr1, expr2)
