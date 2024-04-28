# pylint: skip-file

from src.nofeardb.enums import DocumentStatus
from src.nofeardb.orm import Document, Field, Relationship


class TestDoc(Document):
    __documentname__ = "test_doc"

    testfield_1 = Field()
    testfield_2 = Field()
    testRel_1 = Relationship()


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


# def test_changed_data_fields_new_model():
#     assert False


# def test_changed_data_fields_deleted_model():
#     assert False


# def test_changed_relationship_fields_modified_model():
#     assert False


# def test_changed_relationship_fields_new_model():
#     assert False


# def test_changed_relationship_fields_deleted_model():
#     assert False
