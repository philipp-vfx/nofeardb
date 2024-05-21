import pytest
import uuid
import datetime

from src.nofeardb.enums import DocumentStatus
from src.nofeardb.engine import StorageEngine
from src.nofeardb.datatypes import UUID, DateTime, Float, Integer, String
from src.nofeardb.orm import Document, Field, ManyToMany, ManyToOne, OneToMany

def test_create_not_allowed():
    class TestDoc(Document):
        pass
    
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])
    
    doc = TestDoc()
    engine.create(doc)
    
    doc.__status__ = DocumentStatus.MOD
    
    with pytest.raises(RuntimeError):
        engine.create(doc)
        
    doc.__status__ = DocumentStatus.SYNC
    
    with pytest.raises(RuntimeError):
        engine.create(doc)
        
    doc.__status__ = DocumentStatus.DEL
    
    with pytest.raises(RuntimeError):
        engine.create(doc)
        
    
        
def test_update_not_allowed():
    class TestDoc(Document):
        pass
    
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])
    
    doc = TestDoc()
    doc.__status__ = DocumentStatus.NEW
    
    with pytest.raises(RuntimeError):
        engine.update(doc)
        
    doc.__status__ = DocumentStatus.DEL
    
    with pytest.raises(RuntimeError):
        engine.update(doc)
        
    doc.__status__ = DocumentStatus.SYNC
    engine.update(doc)
    doc.__status__ = DocumentStatus.MOD
    engine.update(doc)
    
    

def test_register_models():
    class TestDoc(Document):
        pass
    
    class TestDoc2(Document):
        pass
    
    class NoDoc:
        pass
    
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])
    assert engine._models == [TestDoc]
    
    with pytest.raises(ValueError):
        engine.register_models([NoDoc])
        
    engine.register_models([TestDoc2])
    assert engine._models == [TestDoc, TestDoc2]
    
    engine.register_models([TestDoc])
    assert engine._models == [TestDoc, TestDoc2]

def test_create_json_fields():
    class TestDoc(Document):
        uuid = Field(UUID, primary_key=True)
        int_field = Field(Integer)
        float_field = Field(Float)
        str_field = Field(String)
        date_field = Field(DateTime)
        
    doc = TestDoc()
    doc.uuid = uuid.uuid4()
    doc.int_field = 2
    doc.float_field = 2.0
    doc.str_field = "hello world"
    doc.date_field = datetime.datetime.now()
    
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])
    
    expected_json = {
        "id": str(doc.uuid),
        "int_field": doc.int_field,
        "float_field": doc.float_field,
        "str_field": doc.str_field,
        "date_field": str(doc.date_field.isoformat())
    }
    
    assert engine.create_json(doc) == expected_json
    
def test_create_json_many_to_one_bidirectional():
    class TestDoc(Document):
        __documentname__ = "test_doc"

        test_rel_docs = OneToMany(
            "TestRelDoc",
            back_populates="test_doc"
        )


    class TestRelDoc(Document):
            __documentname__ = "rel_test_doc"

            test_doc = ManyToOne(
                "TestDoc",
                back_populates="test_rel_docs")
            
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, TestRelDoc])
    
    doc = TestDoc()
    rel = TestRelDoc()
    
    expected_json = {
        'id': str(rel.__id__),
        'test_doc': None
    }
    
    assert engine.create_json(rel) == expected_json
    
    doc.test_rel_docs = [rel]
    
    expected_json = {
        'id': str(doc.__id__),
        'test_rel_docs': [str(rel.__id__)]
    }
    
    assert engine.create_json(doc) == expected_json
    
    expected_json = {
        'id': str(rel.__id__),
        'test_doc': str(doc.__id__)
    }
    
    assert engine.create_json(rel) == expected_json
    
def test_create_json_many_to_many_bidirectional():
    class TestDoc(Document):
        __documentname__ = "test_doc"

        test_rel_docs = ManyToMany(
            "TestRelDoc",
            back_populates="test_docs"
        )


    class TestRelDoc(Document):
            __documentname__ = "rel_test_doc"

            test_docs = ManyToMany(
                "TestDoc",
                back_populates="test_rel_docs")
            
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, TestRelDoc])
    
    doc = TestDoc()
    rel = TestRelDoc()
    
    expected_json = {
        'id': str(rel.__id__),
        'test_docs': []
    }
    
    assert engine.create_json(rel) == expected_json
    
    doc.test_rel_docs = [rel]
    
    expected_json = {
        'id': str(doc.__id__),
        'test_rel_docs': [str(rel.__id__)]
    }
    
    assert engine.create_json(doc) == expected_json
    
    expected_json = {
        'id': str(rel.__id__),
        'test_docs': [str(doc.__id__)]
    }
    
    assert engine.create_json(rel) == expected_json
    
def test_update_json_fields():
    class TestDoc(Document):
        uuid = Field(UUID, primary_key=True)
        int_field = Field(Integer)
        float_field = Field(Float)
        str_field = Field(String)
        date_field = Field(DateTime)
        
    doc = TestDoc()
    doc.uuid = uuid.uuid4()
    doc.int_field = 2
    doc.float_field = 2.0
    doc.str_field = "hello world"
    doc.date_field = datetime.datetime.now()
    
    expected_json = {
        "id": str(doc.uuid),
        "int_field": doc.int_field,
        "float_field": 4.0,
        "str_field": doc.str_field,
        "date_field": str(doc.date_field.isoformat())
    }
    
    doc.__status__ = DocumentStatus.MOD
    doc.__changed_fields__ = []
    
    doc.int_field = 3
    doc.str_field = "hello hello"
    
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])
    
    updated_json = engine.update_json(expected_json.copy(), doc)
    
    expected_json['int_field'] = 3
    expected_json['str_field'] = "hello hello"
    
    assert updated_json == expected_json
    
def test_update_json_many_to_one_bidirectional():
    class TestDoc(Document):
        __documentname__ = "test_doc"

        test_rel_docs = OneToMany(
            "TestRelDoc",
            back_populates="test_doc"
        )


    class TestRelDoc(Document):
            __documentname__ = "rel_test_doc"

            test_doc = ManyToOne(
                "TestDoc",
                back_populates="test_rel_docs")
            
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, TestRelDoc])
    
    doc = TestDoc()
    rel1 = TestRelDoc()
    rel2 = TestRelDoc()
    
    doc.__status__ = DocumentStatus.MOD
    rel1.__status__ = DocumentStatus.MOD
    rel2.__status__ = DocumentStatus.MOD
    
    expected_json_rel1 = {
        'id': str(rel1.__id__),
        'test_doc': None
    }
    
    expected_json_rel2 = {
        'id': str(rel2.__id__),
        'test_doc': None
    }
    
    expected_json_doc = {
        'id': str(rel1.__id__),
        'test_rel_docs': []
    }
    
    json_copy_doc = expected_json_doc.copy()
    json_copy_rel1 = expected_json_rel1.copy()
    json_copy_rel2 = expected_json_rel2.copy()
    
    assert engine.update_json(json_copy_doc, doc) == expected_json_doc
    assert engine.update_json(json_copy_rel1, rel1) == expected_json_rel1
    
    doc.test_rel_docs = [rel1]
    
    assert engine.update_json({}, doc) != {}
    assert engine.update_json({}, rel1) != {}
    
    expected_json_doc["test_rel_docs"] = [str(rel1.__id__)]
    expected_json_rel1["test_doc"] = str(doc.__id__)
    
    assert engine.update_json(json_copy_doc, doc) == expected_json_doc
    assert engine.update_json(json_copy_rel1, rel1) == expected_json_rel1
    
    rel2.test_doc = doc
    
    expected_json_doc["test_rel_docs"] = [str(rel1.__id__), str(rel2.__id__)]
    expected_json_rel2["test_doc"] = str(doc.__id__)
    
    assert engine.update_json(json_copy_doc, doc) == expected_json_doc
    assert engine.update_json(json_copy_rel2, rel2) == expected_json_rel2
    
    doc.test_rel_docs.remove(rel1)
    
    expected_json_doc["test_rel_docs"] = [str(rel2.__id__)]
    expected_json_rel1["test_doc"] = None
    
    assert engine.update_json(json_copy_doc, doc) == expected_json_doc
    assert engine.update_json(json_copy_rel1, rel1) == expected_json_rel1
    
    
    
