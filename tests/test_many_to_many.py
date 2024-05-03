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
