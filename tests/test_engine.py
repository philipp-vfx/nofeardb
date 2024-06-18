# pylint: skip-file

import pytest
import uuid
import datetime
import os

from src.nofeardb.exceptions import DocumentLockException
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

    mocker.patch('os.listdir', return_value=["id1", "id2"])

    assert engine._check_all_documents_can_be_written([doc1]) == True
    with pytest.raises(RuntimeError):
        engine._check_all_documents_can_be_written([doc1, doc2]) == False


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

    mocker.patch('os.listdir', return_value=["id1", "id2"])

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
    assert engine._read_document_from_disk(
        "test/doc/path") == {'test': 'hello', 'test_int': 38}
    assert engine._read_document_from_disk(
        None) == None


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

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    engine.create(doc)

    assert patched_write.call_count == 1

    doc.__status__ = DocumentStatus.MOD

    engine.update(doc)

    assert patched_write.call_count == 2


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

    docs = engine.read(TestDoc)
    read_doc = docs[0]
    assert read_doc.__id__ == doc.__id__
    assert read_doc.attr1 == doc.attr1
    assert read_doc.attr2 == doc.attr2
    assert read_doc != doc


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

    docs = engine.read(TestDoc)
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

    docs = engine.read(TestDoc)
    read_doc = docs[0]
    assert read_doc.rel.__id__ == rel.__id__
    assert read_doc.__status__ == DocumentStatus.SYNC
    assert read_doc.rel.__status__ == DocumentStatus.LAZY
    assert read_doc.__added_relationships__ == {}

    mocker.patch.object(
        StorageEngine, '_read_document_from_disk', return_value={"rel": [str(doc.__id__)]})

    docs = engine.read(RelDoc)
    read_doc = docs[0]
    assert read_doc.rel[0].__id__ == doc.__id__
    assert read_doc.__status__ == DocumentStatus.SYNC
    assert read_doc.rel[0].__status__ == DocumentStatus.LAZY
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
