import pytest
from src.nofeardb.orm import Document, Field, ManyToOne, OneToMany


class TestDoc(Document):
    __documentname__ = "test_doc"

    test_rel_docs = OneToMany(
        "TestRelDoc",
        back_populates="test_doc"
    )
    
    test_rel_docs2 = OneToMany(
        "TestRelDoc2",
        back_populates="test_doc"
    )
    
class TestRelDoc(Document):
    __documentname__ = "rel_test_doc"

    test_doc = ManyToOne(
        "TestDoc",
        back_populates="test_rel_docs")
    
class TestRelDoc2(Document):
    __documentname__ = "rel_test_docs"

    test_doc = ManyToOne(
        "TestDoc",
        back_populates="test_rel_docs2")
    
def test_bidirectional_many_to_one():
    doc = TestDoc()
    relDoc = TestRelDoc()
    relDoc2 = TestRelDoc2()
    
    doc.test_rel_docs.append(relDoc)
    assert doc.test_rel_docs[0] == relDoc
    assert relDoc.test_doc == doc
    assert len(doc.test_rel_docs2) == 0
    assert relDoc2.test_doc == None
    
    doc.test_rel_docs2.append(relDoc2)
    assert doc.test_rel_docs[0] == relDoc
    assert relDoc.test_doc == doc
    assert doc.test_rel_docs2[0] == relDoc2
    assert relDoc2.test_doc == doc
    
    doc.test_rel_docs.remove(relDoc)
    assert len(doc.test_rel_docs) == 0
    assert relDoc.test_doc == None
    assert doc.test_rel_docs2[0] == relDoc2
    assert relDoc2.test_doc == doc
    
    doc.test_rel_docs2.remove(relDoc2)
    assert len(doc.test_rel_docs) == 0
    assert relDoc.test_doc == None
    assert len(doc.test_rel_docs2) == 0
    assert relDoc2.test_doc == None
    
def test_bidirectional_one_to_many():
    doc = TestDoc()
    relDoc = TestRelDoc()
    relDoc2 = TestRelDoc2()
    
    relDoc.test_doc = doc
    assert doc.test_rel_docs[0] == relDoc
    assert relDoc.test_doc == doc
    assert len(doc.test_rel_docs2) == 0
    assert relDoc2.test_doc == None
    
    relDoc2.test_doc = doc
    assert doc.test_rel_docs[0] == relDoc
    assert relDoc.test_doc == doc
    assert doc.test_rel_docs2[0] == relDoc2
    assert relDoc2.test_doc == doc
    
    relDoc.test_doc = None
    assert len(doc.test_rel_docs) == 0
    assert relDoc.test_doc == None
    assert len(doc.test_rel_docs2) == 1
    assert relDoc2.test_doc == doc
    
    relDoc2.test_doc = None
    assert len(doc.test_rel_docs) == 0
    assert relDoc.test_doc == None
    assert len(doc.test_rel_docs2) == 0
    assert relDoc2.test_doc == None
    
def test_bidirectional_many_to_one_replace_item():
    doc = TestDoc()
    relDoc = TestRelDoc()
    relDoc2 = TestRelDoc()
    
    doc.test_rel_docs.append(relDoc)
    assert doc.test_rel_docs == [relDoc]
    assert relDoc.test_doc == doc
    assert relDoc2.test_doc == None
    
    doc.test_rel_docs[0] = relDoc2
    assert doc.test_rel_docs == [relDoc2]
    assert relDoc.test_doc == None
    assert relDoc2.test_doc == doc
    
def test_bidirectional_many_to_one_set_all_items_at_once():
    doc = TestDoc()
    relDoc = TestRelDoc()
    relDoc2 = TestRelDoc()
    
    doc.test_rel_docs = [relDoc, relDoc2]
    assert doc.test_rel_docs == [relDoc, relDoc2]
    assert relDoc.test_doc == doc
    assert relDoc2.test_doc == doc
    
    doc.test_rel_docs.remove(relDoc)
    assert doc.test_rel_docs == [relDoc2]
    assert relDoc.test_doc == None
    assert relDoc2.test_doc == doc
    
    doc.test_rel_docs = []
    assert doc.test_rel_docs == []
    assert relDoc.test_doc == None
    assert relDoc2.test_doc == None
    
def test_bidirectional_many_to_one_unallowed_operations():
    doc = TestDoc()
    relDoc = TestRelDoc()
    relDoc2 = TestRelDoc()
    
    doc.test_rel_docs.append(relDoc)
    with pytest.raises(RuntimeError):
        doc.test_rel_docs += [relDoc2]
        
    with pytest.raises(RuntimeError):
        doc.test_rel_docs = doc.test_rel_docs +[relDoc2]
        
    with pytest.raises(RuntimeError):
        del doc.test_rel_docs[0]