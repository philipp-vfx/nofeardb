from src.nofeardb.datatypes import Boolean, Integer
import src.nofeardb.expr as expr
from src.nofeardb.orm import Document, Field

def test_eq():
    
    class Test(Document):
        a = Field(Integer)
    
    t = Test()
    t.a = 1
    
    assert expr.eq("a", 1).evaluate(t) is True
    assert expr.eq("a", 2).evaluate(t) is False
    assert expr.neq("a", 2).evaluate(t) is True
    assert expr.neq("a", 1).evaluate(t) is False
    
def test_lt():
    
    class Test(Document):
        a = Field(Integer)
    
    t = Test()
    t.a = 1
    
    assert expr.lt("a", 2).evaluate(t) is True
    assert expr.lt("a", 1).evaluate(t) is False
    assert expr.lte("a", 1).evaluate(t) is True
    assert expr.lte("a", 0).evaluate(t) is False
    
def test_gt():
    
    class Test(Document):
        a = Field(Integer)
    
    t = Test()
    t.a = 2
    
    assert expr.gt("a", 1).evaluate(t) is True
    assert expr.gt("a", 2).evaluate(t) is False
    assert expr.gte("a", 2).evaluate(t) is True
    assert expr.gte("a", 3).evaluate(t) is False
    
def test_is_in():
    
    class Test(Document):
        a = Field(Integer)
    
    t = Test()
    t.a = 2
    
    assert expr.is_in("a", [1,2,3]).evaluate(t) is True
    assert expr.is_in("a", [4,5,6]).evaluate(t) is False
    
def test_is():
    
    class Test(Document):
        a = Field(Boolean)
    
    t = Test()
    t.a = True
    
    assert expr.is_("a", True).evaluate(t) is True
    assert expr.is_("a", None).evaluate(t) is False
    assert expr.is_not("a", None).evaluate(t) is True
    assert expr.is_not("a", True).evaluate(t) is False
    
def test_and():
    
    class Test(Document):
        a = Field(Integer)
        b = Field(Integer)
    
    t = Test()
    t.a = 1
    t.b = 2
    
    assert expr.and_(expr.eq("a", 1), expr.eq("b", 2)).evaluate(t) is True
    assert expr.and_(expr.eq("a", 1), expr.eq("b", 3)).evaluate(t) is False
    
    assert (
        expr.and_(
            expr.and_(
                expr.eq("a", 1), expr.eq("b", 2)
            ),
            expr.and_(
                expr.eq("a", 1), expr.eq("b", 2)
            )
        ).evaluate(t)
    ) is True
    
def test_or():
    
    class Test(Document):
        a = Field(Integer)
        b = Field(Integer)
    
    t = Test()
    t.a = 1
    t.b = 2
    
    assert expr.or_(expr.eq("a", 1), expr.eq("b", 2)).evaluate(t) is True
    assert expr.or_(expr.eq("a", 1), expr.eq("b", 3)).evaluate(t) is True
    assert expr.or_(expr.eq("a", 3), expr.eq("b", 2)).evaluate(t) is True
    assert expr.or_(expr.eq("a", 3), expr.eq("b", 4)).evaluate(t) is False
    
    assert (
        expr.or_(
            expr.and_(
                expr.eq("a", 1), expr.eq("b", 2)
            ),
            expr.and_(
                expr.eq("a", 1), expr.eq("b", 3)
            )
        ).evaluate(t)
    ) is True