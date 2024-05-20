# pylint: skip-file

from src.nofeardb.enums import DocumentStatus
import pytest
from src.nofeardb.orm import Document, ManyToOne, OneToMany, ManyToMany


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


def test_bidirectional_many_to_many():
    doc = TestDoc()
    doc2 = TestDoc()
    relDoc = TestRelDoc()
    relDoc2 = TestRelDoc()

    doc.test_rel_docs = [relDoc, relDoc2]
    assert doc.test_rel_docs[0] == relDoc
    assert relDoc.test_docs == [doc]
    assert relDoc2.test_docs == [doc]

    doc2.test_rel_docs = [relDoc]
    assert doc2.test_rel_docs[0] == relDoc
    assert relDoc.test_docs == [doc, doc2]
    assert relDoc2.test_docs == [doc]

    relDoc2.test_docs = [doc, doc2]
    assert relDoc.test_docs == [doc, doc2]
    assert relDoc2.test_docs == [doc, doc2]
    assert doc2.test_rel_docs == [relDoc, relDoc2]
    assert doc.test_rel_docs == [relDoc, relDoc2]

    doc.test_rel_docs = []
    assert relDoc.test_docs == [doc2]
    assert relDoc2.test_docs == [doc2]
    assert doc2.test_rel_docs == [relDoc, relDoc2]


def test_bidirectional_many_to_many_list_operations():
    doc = TestDoc()
    doc2 = TestDoc()
    relDoc = TestRelDoc()
    relDoc2 = TestRelDoc()

    doc.test_rel_docs.append(relDoc)
    assert doc.test_rel_docs[0] == relDoc
    assert relDoc.test_docs == [doc]

    relDoc2.test_docs.append(doc)
    assert doc.test_rel_docs == [relDoc, relDoc2]
    assert relDoc2.test_docs == [doc]

    doc2.test_rel_docs.append(relDoc)
    assert doc2.test_rel_docs[0] == relDoc
    assert relDoc2.test_docs == [doc]
    assert relDoc.test_docs == [doc, doc2]

    relDoc2.test_docs.append(doc2)
    assert doc2.test_rel_docs == [relDoc, relDoc2]
    assert doc.test_rel_docs == [relDoc, relDoc2]
    assert relDoc2.test_docs == [doc, doc2]
    assert relDoc.test_docs == [doc, doc2]

    doc.test_rel_docs.remove(relDoc)
    assert doc2.test_rel_docs == [relDoc, relDoc2]
    assert doc.test_rel_docs == [relDoc2]
    assert relDoc2.test_docs == [doc, doc2]
    assert relDoc.test_docs == [doc2]

    doc.test_rel_docs.remove(relDoc2)
    assert doc2.test_rel_docs == [relDoc, relDoc2]
    assert doc.test_rel_docs == []
    assert relDoc2.test_docs == [doc2]
    assert relDoc.test_docs == [doc2]

    doc.test_rel_docs.append(relDoc)
    doc.test_rel_docs[0] = relDoc2
    assert doc2.test_rel_docs == [relDoc, relDoc2]
    assert doc.test_rel_docs == [relDoc2]
    assert relDoc2.test_docs == [doc2, doc]
    assert relDoc.test_docs == [doc2]


def test_bidirectional_many_to_many_unallowed_operations():
    doc = TestDoc()
    relDoc = TestRelDoc()
    relDoc2 = TestRelDoc()

    doc.test_rel_docs.append(relDoc)
    with pytest.raises(RuntimeError):
        doc.test_rel_docs += [relDoc2]

    with pytest.raises(RuntimeError):
        doc.test_rel_docs = doc.test_rel_docs + [relDoc2]

    with pytest.raises(RuntimeError):
        del doc.test_rel_docs[0]

    with pytest.raises(RuntimeError):
        doc.test_rel_docs.extend([relDoc2])


def test_synced_status_update():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.SYNC
    relDoc = TestRelDoc()
    relDoc.__status__ = DocumentStatus.SYNC

    doc.test_rel_docs = [relDoc]
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD


def test_synced_status_update_list_operations():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.SYNC
    relDoc = TestRelDoc()
    relDoc.__status__ = DocumentStatus.SYNC
    relDoc2 = TestRelDoc()
    relDoc2.__status__ = DocumentStatus.SYNC

    doc.test_rel_docs.append(relDoc)
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD

    doc.__status__ = DocumentStatus.SYNC
    relDoc.__status__ = DocumentStatus.SYNC

    doc.test_rel_docs.remove(relDoc)
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD

    doc.test_rel_docs = [relDoc]
    doc.__status__ = DocumentStatus.SYNC
    relDoc.__status__ = DocumentStatus.SYNC
    relDoc2.__status__ = DocumentStatus.SYNC

    doc.test_rel_docs[0] = relDoc2
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD
    assert relDoc2.__status__ == DocumentStatus.MOD


def test_new_status_update():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.NEW
    relDoc = TestRelDoc()
    relDoc.__status__ = DocumentStatus.NEW

    doc.test_rel_docs = [relDoc]
    assert doc.__status__ == DocumentStatus.NEW
    assert relDoc.__status__ == DocumentStatus.NEW


def test_mod_status_update():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.MOD
    relDoc = TestRelDoc()
    relDoc.__status__ = DocumentStatus.MOD

    doc.test_rel_docs = [relDoc]
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD


def test_deleted_status_update():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.DEL
    relDoc = TestRelDoc()
    relDoc.__status__ = DocumentStatus.NEW
    relDoc2 = TestRelDoc()

    with pytest.raises(RuntimeError):
        doc.test_rel_docs = [relDoc]

    with pytest.raises(RuntimeError):
        doc.test_rel_docs.append(relDoc)

    doc.__status__ = DocumentStatus.NEW
    doc.test_rel_docs = [relDoc]
    doc.__status__ = DocumentStatus.DEL

    with pytest.raises(RuntimeError):
        doc.test_rel_docs.remove(relDoc)

    with pytest.raises(RuntimeError):
        doc.test_rel_docs[0] = relDoc2


def test_many_to_many_added_removed_tracking_bidirectional():

    doc = TestDoc()
    doc2 = TestDoc()
    relDoc = TestRelDoc()

    assert relDoc.__added_relationships__ == {}
    assert relDoc.__removed_relationships__ == {}

    relDoc.test_docs = [doc]

    assert relDoc.__added_relationships__ == {'test_docs': [doc]}
    assert relDoc.__removed_relationships__ == {}
    assert doc.__added_relationships__ == {'test_rel_docs': [relDoc]}
    assert doc.__removed_relationships__ == {}

    relDoc.test_docs = []

    assert relDoc.__added_relationships__ == {'test_docs': []}
    assert relDoc.__removed_relationships__ == {'test_docs': [doc]}
    assert doc.__added_relationships__ == {'test_rel_docs': []}
    assert doc.__removed_relationships__ == {'test_rel_docs': [relDoc]}

    doc2.test_rel_docs = [relDoc]

    assert relDoc.__added_relationships__ == {'test_docs': [doc2]}
    assert relDoc.__removed_relationships__ == {'test_docs': [doc]}
    assert doc2.__added_relationships__ == {'test_rel_docs': [relDoc]}
    assert doc2.__removed_relationships__ == {}

    doc2.test_rel_docs = []

    assert relDoc.__added_relationships__ == {'test_docs': []}
    assert relDoc.__removed_relationships__ == {'test_docs': [doc, doc2]}
    assert doc2.__added_relationships__ == {'test_rel_docs': []}
    assert doc2.__removed_relationships__ == {'test_rel_docs': [relDoc]}


def test_many_to_many_added_removed_tracking_bidirectional_list_ops():

    doc = TestDoc()
    doc2 = TestDoc()
    relDoc = TestRelDoc()

    assert relDoc.__added_relationships__ == {}
    assert relDoc.__removed_relationships__ == {}

    relDoc.test_docs.append(doc)

    assert relDoc.__added_relationships__ == {'test_docs': [doc]}
    assert relDoc.__removed_relationships__ == {}
    assert doc.__added_relationships__ == {'test_rel_docs': [relDoc]}
    assert doc.__removed_relationships__ == {}

    relDoc.test_docs.remove(doc)

    assert relDoc.__added_relationships__ == {'test_docs': []}
    assert relDoc.__removed_relationships__ == {'test_docs': [doc]}
    assert doc.__added_relationships__ == {'test_rel_docs': []}
    assert doc.__removed_relationships__ == {'test_rel_docs': [relDoc]}

    doc2.test_rel_docs.append(relDoc)

    assert relDoc.__added_relationships__ == {'test_docs': [doc2]}
    assert relDoc.__removed_relationships__ == {'test_docs': [doc]}
    assert doc2.__added_relationships__ == {'test_rel_docs': [relDoc]}
    assert doc2.__removed_relationships__ == {}

    doc2.test_rel_docs.remove(relDoc)

    assert relDoc.__added_relationships__ == {'test_docs': []}
    assert relDoc.__removed_relationships__ == {'test_docs': [doc, doc2]}
    assert doc2.__added_relationships__ == {'test_rel_docs': []}
    assert doc2.__removed_relationships__ == {'test_rel_docs': [relDoc]}

    relDoc.test_docs.append(doc)
    relDoc.test_docs[0] = doc2

    assert relDoc.__added_relationships__ == {'test_docs': [doc2]}
    assert relDoc.__removed_relationships__ == {'test_docs': [doc]}
    assert doc.__added_relationships__ == {'test_rel_docs': []}
    assert doc.__removed_relationships__ == {'test_rel_docs': [relDoc]}
    assert doc2.__added_relationships__ == {'test_rel_docs': [relDoc]}
    assert doc2.__removed_relationships__ == {'test_rel_docs': []}


def test_adding_document_with_same_id_twice():
    doc = TestDoc()
    relDoc1 = TestRelDoc()
    relDoc2 = TestRelDoc()
    relDoc3 = TestRelDoc()
    relDoc2.__id__ = relDoc1.__id__

    with pytest.raises(RuntimeError):
        doc.test_rel_docs = [relDoc1, relDoc2]

    doc.test_rel_docs.append(relDoc1)
    with pytest.raises(RuntimeError):
        doc.test_rel_docs.append(relDoc2)

    doc.test_rel_docs.append(relDoc3)
    with pytest.raises(RuntimeError):
        doc.test_rel_docs[1] = relDoc2
