# pylint: skip-file

from src.nofeardb.enums import DocumentStatus
import pytest
from src.nofeardb.orm import Document, ManyToOne, OneToMany


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
        doc.test_rel_docs = doc.test_rel_docs + [relDoc2]

    with pytest.raises(RuntimeError):
        del doc.test_rel_docs[0]

    with pytest.raises(RuntimeError):
        doc.test_rel_docs.extend([relDoc2])


def test_bidirectional_many_to_one_status_update():
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

    doc.__status__ = DocumentStatus.SYNC
    relDoc.__status__ = DocumentStatus.SYNC

    doc.test_rel_docs = [relDoc]
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD

    doc.__status__ = DocumentStatus.SYNC
    relDoc.__status__ = DocumentStatus.SYNC
    relDoc2.__status__ = DocumentStatus.SYNC

    doc.test_rel_docs[0] = relDoc2

    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD
    assert relDoc2.__status__ == DocumentStatus.MOD

    doc.__status__ = DocumentStatus.SYNC
    relDoc.__status__ = DocumentStatus.SYNC
    relDoc2.__status__ = DocumentStatus.SYNC

    assert doc.test_rel_docs[0] == relDoc2
    doc.test_rel_docs = []
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.SYNC
    assert relDoc2.__status__ == DocumentStatus.MOD


def test_bidirectional_many_to_one_reverse_status_update():
    doc = TestDoc()
    doc.__status__ = DocumentStatus.SYNC
    relDoc = TestRelDoc()
    relDoc.__status__ = DocumentStatus.SYNC

    relDoc.test_doc = doc
    assert doc.__status__ == DocumentStatus.MOD

    relDoc.__status__ = DocumentStatus.SYNC
    doc.__status__ = DocumentStatus.SYNC

    setattr(relDoc, "test_doc", None)
    assert doc.__status__ == DocumentStatus.MOD


def test_bidirectional_one_to_many_status_update():
    doc = TestDoc()
    relDoc = TestRelDoc()
    doc.__status__ = DocumentStatus.SYNC
    relDoc.__status__ = DocumentStatus.SYNC

    relDoc.test_doc = doc
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD

    doc.__status__ = DocumentStatus.SYNC
    relDoc.__status__ = DocumentStatus.SYNC

    relDoc.test_doc = None
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.MOD


def test_unidirectional_many_to_one_status_update():
    class TestDocUni(Document):
        __documentname__ = "test_doc_uni"

        test_rel_docs = OneToMany(
            "RelTestDocUni",
        )

    class RelTestDocUni(Document):
        __documentname__ = "test_doc_uni"

    doc = TestDocUni()
    doc.__status__ = DocumentStatus.SYNC
    relDoc = RelTestDocUni()
    relDoc.__status__ = DocumentStatus.SYNC

    doc.test_rel_docs.append(relDoc)
    assert doc.__status__ == DocumentStatus.MOD
    assert relDoc.__status__ == DocumentStatus.SYNC


def test_unidirectional_one_to_many_status_update():
    class TestDocUni(Document):
        __documentname__ = "test_doc_uni"

    class RelTestDocUni(Document):
        __documentname__ = "test_doc_uni"

        test_doc = ManyToOne("TestDocUni")

    doc = TestDocUni()
    doc.__status__ = DocumentStatus.SYNC
    relDoc = RelTestDocUni()
    relDoc.__status__ = DocumentStatus.SYNC

    relDoc.test_doc = doc
    assert relDoc.__status__ == DocumentStatus.MOD
    assert doc.__status__ == DocumentStatus.SYNC


def test_reset_relationships():
    doc = TestDoc()
    relDoc = TestRelDoc()

    print("SNAPSHOT")
    doc.create_snapshot()
    doc.test_rel_docs.append(relDoc)

    assert doc.test_rel_docs == [relDoc]
    assert relDoc.test_doc == doc

    print("RESET")
    doc.reset()

    assert doc.test_rel_docs == []
    assert relDoc.test_doc is None


def test_many_to_one_added_removed_tracking_unidirectional():
    class TestDocUni(Document):
        __documentname__ = "test_doc_uni"

    class RelTestDocUni(Document):
        __documentname__ = "test_doc_uni"

        test_doc = ManyToOne("TestDocUni")

    doc = TestDocUni()
    doc2 = TestDocUni()
    relDoc = RelTestDocUni()

    assert relDoc.__added_relationships__ == {}
    assert relDoc.__removed_relationships__ == {}

    relDoc.test_doc = doc

    assert relDoc.__added_relationships__ == {'test_doc': [doc]}
    assert relDoc.__removed_relationships__ == {}

    relDoc.test_doc = None

    assert relDoc.__added_relationships__ == {'test_doc': []}
    assert relDoc.__removed_relationships__ == {'test_doc': [doc]}

    relDoc.test_doc = doc

    assert relDoc.__added_relationships__ == {'test_doc': [doc]}
    assert relDoc.__removed_relationships__ == {'test_doc': []}

    relDoc.test_doc = doc2

    assert relDoc.__added_relationships__ == {'test_doc': [doc2]}
    assert relDoc.__removed_relationships__ == {'test_doc': [doc]}


def test_one_to_many_added_removed_tracking_unidirectional():
    class TestDocUni(Document):
        __documentname__ = "test_doc_uni"

        test_docs = OneToMany("RelTestDocUni")

    class RelTestDocUni(Document):
        __documentname__ = "test_doc_uni"

    doc = TestDocUni()
    relDoc = RelTestDocUni()
    relDoc2 = RelTestDocUni()

    assert doc.__added_relationships__ == {}
    assert doc.__removed_relationships__ == {}

    doc.test_docs = [relDoc, relDoc2]

    assert doc.__added_relationships__ == {'test_docs': [relDoc, relDoc2]}
    assert doc.__removed_relationships__ == {}

    doc.test_docs = []

    assert doc.__added_relationships__ == {'test_docs': []}
    assert doc.__removed_relationships__ == {'test_docs': [relDoc, relDoc2]}

    doc.test_docs = [relDoc, relDoc2]

    assert doc.__added_relationships__ == {'test_docs': [relDoc, relDoc2]}
    assert doc.__removed_relationships__ == {'test_docs': []}

    doc.test_docs = [relDoc]

    assert doc.__added_relationships__ == {'test_docs': [relDoc]}
    assert doc.__removed_relationships__ == {'test_docs': [relDoc2]}


def test_one_to_many_added_removed_tracking_unidirectional_list_operations():
    class TestDocUni(Document):
        __documentname__ = "test_doc_uni"

        test_docs = OneToMany("RelTestDocUni")

    class RelTestDocUni(Document):
        __documentname__ = "test_doc_uni"

    doc = TestDocUni()
    relDoc = RelTestDocUni()
    relDoc2 = RelTestDocUni()

    assert doc.__added_relationships__ == {}
    assert doc.__removed_relationships__ == {}

    doc.test_docs.append(relDoc)
    assert doc.__added_relationships__ == {'test_docs': [relDoc]}
    assert doc.__removed_relationships__ == {}

    doc.test_docs.append(relDoc2)
    assert doc.__added_relationships__ == {'test_docs': [relDoc, relDoc2]}
    assert doc.__removed_relationships__ == {}

    doc.test_docs.remove(relDoc)
    assert doc.__added_relationships__ == {'test_docs': [relDoc2]}
    assert doc.__removed_relationships__ == {'test_docs': [relDoc]}

    doc.test_docs[0] = relDoc
    assert doc.__added_relationships__ == {'test_docs': [relDoc]}
    assert doc.__removed_relationships__ == {'test_docs': [relDoc2]}


def test_many_to_one_added_removed_tracking_bidirectional():
    class TestDocBi(Document):
        __documentname__ = "test_doc_uni"

        test_docs = OneToMany("RelTestDocBi", back_populates="test_doc")

    class RelTestDocBi(Document):
        __documentname__ = "test_doc_uni"

        test_doc = ManyToOne("TestDocBi", back_populates="test_docs")

    doc = TestDocBi()
    relDoc = RelTestDocBi()
    relDoc2 = RelTestDocBi()

    relDoc.test_doc = doc
    assert doc.__added_relationships__ == {'test_docs': [relDoc]}
    assert doc.__removed_relationships__ == {}

    relDoc2.test_doc = doc
    assert doc.__added_relationships__ == {'test_docs': [relDoc, relDoc2]}
    assert doc.__removed_relationships__ == {}

    relDoc.test_doc = None
    assert doc.__added_relationships__ == {'test_docs': [relDoc2]}
    assert doc.__removed_relationships__ == {'test_docs': [relDoc]}


def test_one_to_many_added_removed_tracking_bidirectional():
    class TestDocBi(Document):
        __documentname__ = "test_doc_uni"

        test_docs = OneToMany("RelTestDocBi", back_populates="test_doc")

    class RelTestDocBi(Document):
        __documentname__ = "test_doc_uni"

        test_doc = ManyToOne("TestDocBi", back_populates="test_docs")

    doc = TestDocBi()
    relDoc = RelTestDocBi()
    relDoc2 = RelTestDocBi()

    doc.test_docs = [relDoc]
    assert relDoc.__added_relationships__ == {'test_doc': [doc]}
    assert doc.__removed_relationships__ == {}

    doc.test_docs = [relDoc, relDoc2]
    assert relDoc.__added_relationships__ == {'test_doc': [doc]}
    assert relDoc2.__added_relationships__ == {'test_doc': [doc]}
    assert relDoc.__removed_relationships__ == {'test_doc': []}
    assert relDoc2.__removed_relationships__ == {}

    doc.test_docs = []
    assert relDoc.__added_relationships__ == {'test_doc': []}
    assert relDoc.__removed_relationships__ == {'test_doc': [doc]}
    assert relDoc2.__added_relationships__ == {'test_doc': []}
    assert relDoc2.__removed_relationships__ == {'test_doc': [doc]}


def test_one_to_many_added_removed_tracking_bidirectional_list_operations():
    class TestDocBi(Document):
        __documentname__ = "test_doc_uni"

        test_docs = OneToMany("RelTestDocBi", back_populates="test_doc")

    class RelTestDocBi(Document):
        __documentname__ = "test_doc_uni"

        test_doc = ManyToOne("TestDocBi", back_populates="test_docs")

    doc = TestDocBi()
    relDoc = RelTestDocBi()
    relDoc2 = RelTestDocBi()

    doc.test_docs.append(relDoc)
    assert relDoc.__added_relationships__ == {'test_doc': [doc]}
    assert doc.__removed_relationships__ == {}

    doc.test_docs.append(relDoc2)
    assert relDoc.__added_relationships__ == {'test_doc': [doc]}
    assert relDoc2.__added_relationships__ == {'test_doc': [doc]}
    assert relDoc.__removed_relationships__ == {}
    assert relDoc2.__removed_relationships__ == {}

    doc.test_docs.remove(relDoc)
    assert relDoc.__added_relationships__ == {'test_doc': []}
    assert relDoc.__removed_relationships__ == {'test_doc': [doc]}
    assert relDoc2.__added_relationships__ == {'test_doc': [doc]}
    assert relDoc2.__removed_relationships__ == {}

    doc.test_docs[0] = relDoc
    assert relDoc.__added_relationships__ == {'test_doc': [doc]}
    assert relDoc.__removed_relationships__ == {'test_doc': []}
    assert relDoc2.__added_relationships__ == {'test_doc': []}
    assert relDoc2.__removed_relationships__ == {'test_doc': [doc]}


def test_adding_document_with_same_id_twice():
    class TestDocTwice(Document):
        __documentname__ = "test_doc_uni"

        test_docs = OneToMany("RelTestDocBi", back_populates="test_doc")

    class RelTestDocTwice(Document):
        __documentname__ = "test_doc_uni"

        test_doc = ManyToOne("TestDocBi", back_populates="test_docs")

    doc = TestDocTwice()
    relDoc1 = RelTestDocTwice()
    relDoc2 = RelTestDocTwice()
    relDoc3 = RelTestDocTwice()
    relDoc2.__id__ = relDoc1.__id__

    with pytest.raises(RuntimeError):
        doc.test_docs = [relDoc1, relDoc2]

    doc.test_docs.append(relDoc1)
    with pytest.raises(RuntimeError):
        doc.test_docs.append(relDoc2)

    doc.test_docs.append(relDoc3)
    with pytest.raises(RuntimeError):
        doc.test_docs[1] = relDoc2
