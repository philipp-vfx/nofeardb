# pylint: skip-file

import uuid
import pytest
from src.nofeardb.enums import DocumentStatus, RelationshipType
from src.nofeardb.orm import Document, Field, Relationship


class TestDoc(Document):
    __documentname__ = "test_doc"

    testfield_1 = Field()
    testfield_2 = Field()


def test_get_document_name_set():

    class NameTestDoc(Document):
        __documentname__ = "hello_world"

    doc = NameTestDoc()
    assert doc.get_document_name() == "hello_world"


def test_get_document_name_not_set():

    class NameTestDoc(Document):
        pass

    doc = NameTestDoc()
    assert doc.get_document_name() == "nametestdoc"
    
def test_generated_document_id():
    
    class IdTestDoc(Document):
        pass
    
    doc = IdTestDoc()
    assert isinstance(doc.__id__, uuid.UUID)
    
def test_setting_document_id_correct_type():
    
    generated_id = uuid.uuid4()
    
    class IdTestDoc(Document):
        id = Field(primary_key=True)
    
    doc = IdTestDoc()
    doc.id = generated_id
    
    assert isinstance(doc.__id__, uuid.UUID)
    assert doc.__id__ == generated_id
    assert doc.id == generated_id
    
def test_setting_document_id_incorrect_type():
    
    generated_id = "helloworld"
    
    class IdTestDoc(Document):
        id = Field(primary_key=True)
    
    doc = IdTestDoc()
    
    with pytest.raises(ValueError):
        doc.id = generated_id
        
def test_reset_object():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.MOD

    doc.testfield_1 = "hello"
    doc.testfield_2 = 2
    doc.__changed_fields__ = []
    
    doc.create_snapshot()
    
    doc.testfield_1 = "world"
    doc.testfield_2 = 3
    
    assert doc.testfield_1 == "world"
    assert doc.testfield_2 == 3
    
    doc.reset()
    
    assert doc.testfield_1 == "hello"
    assert doc.testfield_2 == 2


def test_changed_data_fields_modified_model():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.MOD

    doc.testfield_1 = "hello"
    doc.testfield_2 = 2
    doc.__changed_fields__ = []

    assert doc.__changed_fields__ == []
    assert doc.testfield_1 == "hello"
    assert doc.testfield_2 == 2

    doc.testfield_1 = "world"

    assert doc.__changed_fields__ == ["testfield_1"]
    assert doc.testfield_1 == "world"
    assert doc.testfield_2 == 2

    doc.testfield_2 = 3

    assert doc.__changed_fields__ == ["testfield_1", "testfield_2"]
    assert doc.testfield_1 == "world"
    assert doc.testfield_2 == 3
    
    assert doc.__status__ == DocumentStatus.MOD


def test_changed_data_fields_new_model():
    doc = TestDoc()
    assert doc.__status__ == DocumentStatus.NEW

    doc.testfield_1 = "hello"
    doc.testfield_2 = 2
    doc.__changed_fields__ = []

    assert doc.__changed_fields__ == []
    assert doc.testfield_1 == "hello"
    assert doc.testfield_2 == 2

    doc.testfield_1 = "world"

    assert doc.__changed_fields__ == []
    assert doc.testfield_1 == "world"
    assert doc.testfield_2 == 2

    doc.testfield_2 = 3

    assert doc.__changed_fields__ == []
    assert doc.testfield_1 == "world"
    assert doc.testfield_2 == 3
    
    assert doc.__status__ == DocumentStatus.NEW


def test_changed_data_fields_deleted_model():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.DEL
    
    with pytest.raises(RuntimeError):
        doc.testfield_1 = "hello"
        
    assert doc.__status__ == DocumentStatus.DEL
    
def test_changed_data_fields_sync_model():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.SYNC

    doc.testfield_1 = "hello"
    doc.testfield_2 = 2
    doc.__changed_fields__ = []

    assert doc.__changed_fields__ == []
    assert doc.testfield_1 == "hello"
    assert doc.testfield_2 == 2

    doc.testfield_1 = "world"

    assert doc.__changed_fields__ == ["testfield_1"]
    assert doc.testfield_1 == "world"
    assert doc.testfield_2 == 2

    doc.testfield_2 = 3

    assert doc.__changed_fields__ == ["testfield_1", "testfield_2"]
    assert doc.testfield_1 == "world"
    assert doc.testfield_2 == 3
    
    assert doc.__status__ == DocumentStatus.MOD
    
def test_setfield_not_nullable():
    class NullableTestDoc(Document):
        nullable_field = Field()
        not_nullable_field = Field(nullable=False)
        
    doc = NullableTestDoc()
    with pytest.raises(ValueError):
        doc.not_nullable_field = None
        
    doc.nullable_field = None
    
    assert doc.nullable_field == None


# def test_changed_relationship_fields_new_model():
#     assert False


# def test_changed_relationship_fields_deleted_model():
#     assert False
