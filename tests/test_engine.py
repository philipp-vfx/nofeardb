# pylint: skip-file

import pytest
import uuid
import datetime
import os

from src.nofeardb.exceptions import DocumentLockException, NotCreateableException
from src.nofeardb.enums import DocumentStatus
from src.nofeardb.engine import DocumentLock, StorageEngine
from src.nofeardb.datatypes import UUID, DateTime, Float, Integer, String
from src.nofeardb.orm import Document, Field, ManyToMany, ManyToOne, OneToMany, Relationship

DATEFORMAT = '%Y-%m-%d %H:%M:%S'


def test_create_not_allowed():
    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

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


def test_createJsonAlreadyExistingId(mocker):
    import os

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc1 = TestDoc()
    doc2 = TestDoc()
    doc2.__id__ = "id2"

    mocker.patch('os.listdir', return_value=["id1__hash1", "id2__hash2"])
    mocker.patch('os.path.exists', return_value=True)

    assert engine._check_all_documents_can_be_written([doc1]) == True
    with pytest.raises(RuntimeError):
        engine._check_all_documents_can_be_written([doc1, doc2])


def test_updateJsonNotExistingId(mocker):
    import os

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc1 = TestDoc()
    doc1.__status__ = DocumentStatus.MOD
    doc2 = TestDoc()
    doc2.__id__ = "id2"
    doc2.__status__ = DocumentStatus.MOD

    mocker.patch('os.listdir', return_value=["id1__hash1", "id2__hash2"])
    mocker.patch('os.path.exists', return_value=True)

    assert engine._check_all_documents_can_be_written([doc2]) == True
    with pytest.raises(RuntimeError):
        engine._check_all_documents_can_be_written([doc1, doc2]) == False


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
        'test_doc': [None]
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
        'test_doc': [str(doc.__id__)]
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


def test_resolve_dependencies():
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

        many_docs = ManyToMany(
            "TestRelDoc2",
            back_populates="many_docs"
        )

    class TestRelDoc2(Document):
        many_docs = ManyToMany(
            "TestRelDoc",
            back_populates="many_docs"
        )

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, TestRelDoc, TestRelDoc2])

    doc1 = TestDoc()
    doc2 = TestDoc()
    reldoc1 = TestRelDoc()
    reldoc2 = TestRelDoc()
    reldoc3 = TestRelDoc2()
    reldoc4 = TestRelDoc2()
    reldoc5 = TestRelDoc()

    doc1.test_rel_docs = [reldoc1]
    reldoc1.many_docs = [reldoc3]
    reldoc2.many_docs = [reldoc4]

    assert engine.resolve_dependencies(reldoc2) == [reldoc2, reldoc4]
    assert engine.resolve_dependencies(reldoc4) == [reldoc4, reldoc2]
    assert engine.resolve_dependencies(doc1) == [doc1, reldoc1, reldoc3]
    assert engine.resolve_dependencies(reldoc1) == [reldoc1, reldoc3, doc1]
    assert engine.resolve_dependencies(reldoc3) == [reldoc3, reldoc1, doc1]
    assert engine.resolve_dependencies(reldoc5) == [reldoc5]
    assert engine.resolve_dependencies(doc2) == [doc2]


def test_resolve_dependencies_unidirectional():
    class TestDoc(Document):
        __documentname__ = "test_doc"

        test_rel_docs = OneToMany(
            "TestRelDoc",
        )

    class TestRelDoc(Document):
        __documentname__ = "rel_test_doc"

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, TestRelDoc])

    doc1 = TestDoc()
    reldoc1 = TestRelDoc()

    doc1.test_rel_docs.append(reldoc1)

    assert engine.resolve_dependencies(doc1) == [doc1, reldoc1]
    assert engine.resolve_dependencies(reldoc1) == [reldoc1]


def test_resolving_dependencies_with_scope():
    class TestDoc(Document):
        __documentname__ = "test_doc"

        test_rel_docs = OneToMany(
            "TestRelDoc",
            back_populates="test_doc",
            cascade=["delete"]
        )

    class TestRelDoc(Document):
        __documentname__ = "rel_test_doc"

        test_doc = ManyToOne(
            "TestDoc",
            back_populates="test_rel_docs")

        many_docs = ManyToMany(
            "TestRelDoc2",
            back_populates="many_docs"
        )

    class TestRelDoc2(Document):
        many_docs = ManyToMany(
            "TestRelDoc",
            back_populates="many_docs"
        )

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, TestRelDoc, TestRelDoc2])

    doc1 = TestDoc()
    reldoc1 = TestRelDoc()
    reldoc2 = TestRelDoc()
    reldoc3 = TestRelDoc2()
    reldoc4 = TestRelDoc2()

    doc1.test_rel_docs = [reldoc1, reldoc2]
    reldoc1.many_docs = [reldoc3]
    reldoc2.many_docs = [reldoc4]

    assert len(engine.resolve_dependencies(doc1)) == 5
    assert doc1 in engine.resolve_dependencies(doc1)
    assert reldoc1 in engine.resolve_dependencies(doc1)
    assert reldoc2 in engine.resolve_dependencies(doc1)
    assert reldoc3 in engine.resolve_dependencies(doc1)
    assert reldoc4 in engine.resolve_dependencies(doc1)

    assert len(engine.resolve_dependencies(doc1, scope="delete")) == 3
    assert doc1 in engine.resolve_dependencies(doc1, scope="delete")
    assert reldoc1 in engine.resolve_dependencies(doc1, scope="delete")
    assert reldoc2 in engine.resolve_dependencies(doc1, scope="delete")

    assert len(engine.resolve_dependencies(reldoc3, scope="delete")) == 1
    assert reldoc3 in engine.resolve_dependencies(reldoc3, scope="delete")

    assert len(engine.resolve_dependencies(doc1, scope="nonexisting")) == 1
    assert doc1 in engine.resolve_dependencies(doc1, scope="nonexisting")


def test_lock_before_write(mocker):
    class TestDoc(Document):
        pass

    lock_creation_date = datetime.datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mocked_fileread_data)

    mocked_lock = mocker.patch.object(
        DocumentLock, 'lock',)
    mocked_release = mocker.patch.object(
        DocumentLock, 'release',)

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc1 = TestDoc()
    doc2 = TestDoc()
    doc3 = TestDoc()

    engine._lock_docs([doc1, doc2, doc3])
    assert mocked_lock.call_count == 3
    assert mocked_release.call_count == 0


def test_lock_before_write_failure_on_locking(mocker):
    class TestDoc(Document):
        pass

    lock_creation_date = datetime.datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mocked_fileread_data)

    doc1 = TestDoc()
    doc2 = TestDoc()
    doc3 = TestDoc()

    mocked_lock = mocker.patch.object(
        DocumentLock, 'lock', side_effect=[None, None, DocumentLockException])
    mocked_release = mocker.patch.object(
        DocumentLock, 'release')

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    with pytest.raises(DocumentLockException):
        engine._lock_docs([doc1, doc2, doc3])

    assert mocked_lock.call_count == 3
    assert mocked_release.call_count == 2


def test_unlock(mocker):
    class TestDoc(Document):
        pass

    lock_creation_date = datetime.datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mocked_fileread_data)

    doc1 = TestDoc()
    doc2 = TestDoc()
    doc3 = TestDoc()

    mocked_release = mocker.patch.object(
        DocumentLock, 'release', side_effect=[None,  DocumentLockException, None])

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    lock1 = DocumentLock(engine, doc1, expiration=10)
    lock2 = DocumentLock(engine, doc2, expiration=10)
    lock3 = DocumentLock(engine, doc3, expiration=10)

    engine._unlock_docs([lock1, lock2, lock3])
    assert mocked_release.call_count == 3


def test_get_real_document_filename_existing(mocker):
    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    real_name = str(doc.__id__) + "__" + doc.get_hash() + "json"

    mocker.patch('os.listdir', return_value=[
        str(uuid.uuid4()) + "__" + doc.get_hash() + "json",
        real_name,
        str(uuid.uuid4()) + "__" + doc.get_hash() + "json",
    ])

    file_path = os.path.normpath("test/path/testdoc/" + real_name)

    assert engine._get_existing_document_file_name(doc) == file_path


def test_get_real_document_filename_not_existing(mocker):
    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    mocker.patch('os.listdir', return_value=[
        str(uuid.uuid4()) + "__" + doc.get_hash() + "json",
        str(uuid.uuid4()) + "__" + doc.get_hash() + "json",
        str(uuid.uuid4()) + "__" + doc.get_hash() + "json",
    ])

    assert engine._get_existing_document_file_name(doc) == None


def test_read_data_from_file(mocker):
    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    lock_content = str("{\"test\": \"hello\", \"test_int\":38}")
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('json.loads', return_value={"test": "hello", "test_int": 38})
    mocker.patch('os.open')
    mocker.patch('os.fstat')
    mocker.patch('os.read', return_value={"test": "hello", "test_int": 38})
    mocker.patch('os.close')
    mocker.patch.object(
        StorageEngine, '_extract_id_and_hash_from_filename', return_value=("test_id", "test_hash"))
    assert engine._read_document_from_disk(
        "test/doc/path") == {'__doc_hash__': 'test_hash', 'test': 'hello', 'test_int': 38}
    assert engine._read_document_from_disk(
        None) == None

    mocker.patch('json.loads', side_effect=PermissionError)
    assert engine._read_document_from_disk(
        "test/doc/path") == None


def test_write_json_previous_file_existing(mocker):
    class TestDoc(Document):
        pass

    doc = TestDoc()

    mocker.patch.object(
        StorageEngine, '_get_existing_document_file_name', return_value="/test/doc")
    mocker.patch.object(
        StorageEngine, '_read_document_from_disk', return_value={"hello": "world"})
    mocker.patch('builtins.open')
    mocked_remove = mocker.patch('os.remove')
    mocked_rename = mocker.patch('os.rename')

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    engine.write_json(doc)

    mocked_remove.assert_called_once()
    mocked_rename.assert_called_once()


def test_write_json_previous_file_not_existing(mocker):
    class TestDoc(Document):
        pass

    doc = TestDoc()

    mocker.patch.object(
        StorageEngine, '_get_existing_document_file_name', return_value=None)
    mocker.patch.object(
        StorageEngine, '_read_document_from_disk', return_value=None)
    mocker.patch('builtins.open')
    mocked_remove = mocker.patch('os.remove')
    mocked_rename = mocker.patch('os.rename')

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    engine.write_json(doc)

    assert mocked_remove.call_count == 0
    mocked_rename.assert_called_once()


def test_create_and_update_doc(mocker):
    class TestDoc(Document):
        pass

    doc = TestDoc()

    mocker.patch.object(
        StorageEngine, 'resolve_dependencies', return_value=[doc])
    mocker.patch.object(
        StorageEngine, '_check_all_documents_can_be_written', return_value=True)
    mocker.patch.object(
        StorageEngine, '_lock_docs')
    mocker.patch.object(
        StorageEngine, '_unlock_docs')
    patched_write = mocker.patch.object(
        StorageEngine, 'write_json')
    mocker.patch('os.makedirs')
    mocker.patch('os.path.exists', return_value=False)

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    engine.create(doc)

    assert patched_write.call_count == 1

    doc.__status__ = DocumentStatus.MOD

    engine.update(doc)

    assert patched_write.call_count == 2


def test_status_update_on_create(mocker):
    class TestDoc(Document):
        pass

    doc = TestDoc()

    mocker.patch.object(
        StorageEngine, 'resolve_dependencies', return_value=[doc])
    mocker.patch.object(
        StorageEngine, '_check_all_documents_can_be_written', return_value=True)
    mocker.patch.object(
        StorageEngine, '_lock_docs')
    mocker.patch.object(
        StorageEngine, '_unlock_docs')
    mocker.patch.object(
        StorageEngine, 'write_json')
    mocker.patch('os.makedirs')
    mocker.patch('os.path.exists', return_value=False)

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    assert doc.__status__ == DocumentStatus.NEW
    engine.create(doc)
    assert doc.__status__ == DocumentStatus.SYNC


def test_read_all_documents_of_type(mocker):
    class TestDoc(Document):

        attr1 = Field(Integer)
        attr2 = Field(String)

    doc = TestDoc()
    doc.attr1 = 38
    doc.attr2 = "hello"

    mocker.patch.object(
        StorageEngine, '_read_document_from_disk', return_value={"id": str(doc.__id__), "attr1": "38", "attr2": "hello"})
    mocker.patch('os.listdir', return_value=["first_document"])

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    docs = engine.read(TestDoc).all()
    read_doc = docs[0]
    assert read_doc.__id__ == doc.__id__
    assert read_doc.attr1 == doc.attr1
    assert read_doc.attr2 == doc.attr2
    assert read_doc != doc
    assert read_doc.__status__ == DocumentStatus.SYNC


def test_read_all_documents_of_type_custom_id(mocker):
    class TestDoc(Document):

        attr1 = Field(UUID, primary_key=True)
        attr2 = Field(String)

    doc = TestDoc()

    id = uuid.uuid4()
    doc.attr1 = id
    doc.attr2 = "hello"

    mocker.patch.object(
        StorageEngine, '_read_document_from_disk', return_value={"attr1": str(id), "attr2": "hello"})
    mocker.patch('os.listdir', return_value=["first_document"])

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    docs = engine.read(TestDoc).all()
    read_doc = docs[0]
    assert read_doc.__id__ == id
    assert read_doc.attr1 == id
    assert read_doc.attr2 == doc.attr2
    assert read_doc != doc


def test_read_all_documents_relationships(mocker):
    class TestDoc(Document):

        rel = ManyToOne("RelDoc", back_populates="rel")

    class RelDoc(Document):
        rel = OneToMany("TestDoc", back_populates="rel")

    doc = TestDoc()
    rel = RelDoc()

    doc.rel = rel

    mocker.patch.object(
        StorageEngine, '_read_document_from_disk', return_value={"rel": [str(rel.__id__)]})
    mocker.patch('os.listdir', return_value=["first_document"])

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, RelDoc])

    docs = engine.read(TestDoc).all()
    read_doc = docs[0]
    assert read_doc.__dict__['rel_rel'].__status__ == DocumentStatus.LAZY
    assert read_doc.rel.__id__ == rel.__id__
    assert read_doc.__dict__['rel_rel'].__status__ == DocumentStatus.SYNC
    assert read_doc.__status__ == DocumentStatus.SYNC
    assert read_doc.__added_relationships__ == {}

    mocker.patch.object(
        StorageEngine, '_read_document_from_disk', side_effect=[
            {"id": str(rel.__id__), "rel": [str(doc.__id__)]},
            {"id": str(doc.__id__), "rel": [str(rel.__id__)]}
        ])

    docs = engine.read(RelDoc).all()
    read_doc = docs[0]
    assert read_doc.rel[0].__id__ == doc.__id__
    assert read_doc.__status__ == DocumentStatus.SYNC
    assert read_doc.__added_relationships__ == {}


def test_load_relation_unregistered_doctype(mocker):
    class TestDoc(Document):

        rel = ManyToOne("NoneExistingDoc", back_populates="rel")

    doc = TestDoc()

    mocker.patch.object(
        StorageEngine, '_read_document_from_disk', return_value={"rel": [str(uuid.uuid4())]})
    mocker.patch('os.listdir', return_value=["first_document"])

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    with pytest.raises(RuntimeError):
        engine.read(TestDoc)


def test_read_all_documents_relationships_lazy_loading(mocker):
    class TestDoc(Document):

        rel = ManyToOne("RelDoc", back_populates="rels")

    class RelDoc(Document):
        rels = OneToMany("TestDoc", back_populates="rel")

    doc = TestDoc()
    doc2 = TestDoc()
    rel = RelDoc()

    doc.rel = rel
    doc2.rel = rel

    mocker.patch.object(
        StorageEngine,
        '_read_document_from_disk',
        side_effect=[
            {"id": str(doc.__id__), "rel": [str(rel.__id__)]},
            {"id": str(rel.__id__), "rels": [
                str(doc.__id__), str(doc2.__id__)]},
            {"id": str(doc2.__id__), "rel": [str(rel.__id__)]},
        ]
    )
    mocker.patch('os.listdir', return_value=["first_document"])

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, RelDoc])

    docs = engine.read(TestDoc).all()
    read_doc = docs[0]
    assert read_doc.rel.__id__ == rel.__id__
    assert len(read_doc.rel.rels) == 2
    assert read_doc.rel.rels[0] == read_doc


def test_read_all_documents_relationships_lazy_loading_unbound_engine(mocker):
    class TestDoc(Document):

        rel = ManyToOne("RelDoc", back_populates="rels")

    class RelDoc(Document):
        rels = OneToMany("TestDoc", back_populates="rel")

    doc = TestDoc()
    doc2 = TestDoc()
    rel = RelDoc()

    doc.rel = rel
    doc2.rel = rel

    mocker.patch.object(
        StorageEngine,
        '_read_document_from_disk',
        side_effect=[
            {"id": str(doc.__id__), "rel": [str(rel.__id__)]},
            {"id": str(rel.__id__), "rels": [
                str(doc.__id__), str(doc2.__id__)]},
            {"id": str(doc2.__id__), "rel": [str(rel.__id__)]},
        ]
    )
    mocker.patch('os.listdir', return_value=["first_document"])

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, RelDoc])

    docs = engine.read(TestDoc).all()
    read_doc = docs[0]
    read_doc.__dict__["rel_rel"].__engine__ = None

    with pytest.raises(RuntimeError):
        read_doc.rel


def test_get_document_with_id_existing_no_valid_path(mocker):
    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc1 = TestDoc()

    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('os.listdir', side_effect=OSError(
        "no file or directory found"))
    assert engine._get_document_with_id_existing(doc1) == False


def test_extract_id_and_hash_from_filename_single_name():
    engine = StorageEngine("test/path")

    doc_id, doc_hash = engine._extract_id_and_hash_from_filename(
        "test_id__test_hash.json")
    assert doc_id == "test_id"
    assert doc_hash == "test_hash"


def test_extract_id_and_hash_from_filename_path():
    engine = StorageEngine("test/path")

    doc_id, doc_hash = engine._extract_id_and_hash_from_filename(
        "/path/to/test_id__test_hash.json")
    assert doc_id == "test_id"
    assert doc_hash == "test_hash"


def test_extract_id_and_hash_invalid_filename():
    engine = StorageEngine("test/path")

    doc_id, doc_hash = engine._extract_id_and_hash_from_filename(
        "/path/to/test_id_test_hash.json")
    assert doc_id == None
    assert doc_hash == None


def test_read_from_cache_not_in_cache(mocker):
    engine = StorageEngine("test/path")

    mocker.patch.object(
        StorageEngine, '_extract_id_and_hash_from_filename', return_value=("test_id", "test_hash"))

    cache_data = {"id": "second_test_id", "attr2": "hello"}
    cache_data["__doc_hash__"] = "test_hash"
    engine._data_cache = {"second_test_id": cache_data}

    data = engine._read_document_from_cache("test/path/test")

    assert data is None

    data = engine._read_document_from_cache(None)

    assert data is None


def test_read_from_cache_if_in_cache(mocker):
    engine = StorageEngine("test/path")

    mocker.patch.object(
        StorageEngine, '_extract_id_and_hash_from_filename', return_value=("test_id", "test_hash"))

    data = engine._read_document_from_cache("test/path/test")

    data = {"id": "test_id", "attr2": "hello"}

    cache_data = dict(data)
    cache_data["__doc_hash__"] = "test_hash"
    engine._data_cache = {"test_id": cache_data}

    cached_data = engine._read_document_from_cache("test/path/test")

    assert cached_data == data


def test_fill_document_with_data_changed_fields(mocker):
    class TestDoc(Document):

        test_field1 = Field(String)
        test_field2 = Field(String)
        test_field3 = Field(String)

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()
    doc.test_field2 = "world"

    data = {"id": "test_id", "test_field1": "hello",
            "unrecognized_field": "something different"}

    engine._fill_document_with_data(doc, data)

    assert doc.test_field1 == "hello"
    assert doc.test_field2 == "world"
    assert doc.test_field3 is None


def test_create_invalid_entity(mocker):
    class TestDoc(Document):

        test_field1 = Field(String, nullable=False)

    mocker.patch('builtins.open')
    mocker.patch('os.makedirs')
    mocker.patch.object(DocumentLock, "lock")
    mocker.patch.object(DocumentLock, "release")

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()
    with pytest.raises(NotCreateableException):
        engine.create(doc)


def test_delete_document_normal(mocker):
    class TestDoc(Document):

        rel = ManyToOne("RelDoc", back_populates="rels")

    class TestDoc2(Document):

        rel = ManyToOne("RelDoc", back_populates="rels")

    class RelDoc(Document):
        rels = OneToMany("TestDoc", back_populates="rel", cascade=["delete"])
        rels2 = OneToMany("TestDoc2", back_populates="rel")

    doc1 = TestDoc()
    doc2 = TestDoc()
    doc3 = TestDoc2()
    rel = RelDoc()

    rel.rels = [doc1, doc2]
    rel.rels2 = [doc3]
    rel.__status__ = DocumentStatus.SYNC
    doc1.__status__ = DocumentStatus.SYNC
    doc2.__status__ = DocumentStatus.SYNC
    doc3.__status__ = DocumentStatus.SYNC
    rel.__status__ = DocumentStatus.SYNC

    delete_json_mock = mocker.patch.object(StorageEngine, 'delete_json')
    write_json_mock = mocker.patch.object(StorageEngine, 'write_json')
    _lock_docs_mock = mocker.patch.object(
        StorageEngine, '_lock_docs', return_value=[])
    mocker.patch.object(StorageEngine, '_unlock_docs')
    mocker.patch.object(
        StorageEngine, '_check_all_documents_can_be_written', return_value=True)

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc, RelDoc])

    assert doc3.rel == rel

    engine.delete(rel)

    assert delete_json_mock.call_count == 3
    assert _lock_docs_mock.call_count == 1
    assert write_json_mock.call_count == 1
    delete_json_mock.assert_called_with(doc1)
    write_json_mock.assert_called_with(doc3)
    assert rel.__status__ == DocumentStatus.DEL
    assert doc1.__status__ == DocumentStatus.DEL
    assert doc2.__status__ == DocumentStatus.DEL
    assert doc3.__status__ == DocumentStatus.MOD
    assert doc3.rel == None


def test_delete_document_json_data(mocker):
    class TestDoc(Document):
        pass

    doc = TestDoc()
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    test_base_path = os.path.normpath("/test/path/to/entity")
    test_name = "testid_testhash.json"

    mocker_remove = mocker.patch('os.remove')
    mocker.patch.object(
        StorageEngine, 'get_doc_basepath', return_value=test_base_path)
    mocker.patch.object(
        StorageEngine, '_get_existing_document_file_name', return_value=test_name)

    engine.delete_json(doc)
    mocker_remove.assert_called_with(
        os.path.join(test_base_path, test_name))


def test_delete_document_wrong_status(mocker):
    class TestDoc(Document):
        pass

    doc = TestDoc()
    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    with pytest.raises(RuntimeError):
        doc.__status__ = DocumentStatus.DEL
        engine.delete(doc)

    with pytest.raises(RuntimeError):
        doc.__status__ = DocumentStatus.NEW
        engine.delete(doc)
