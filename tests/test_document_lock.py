# pylint: skip-file

import pytest
import uuid
import os
import time
from datetime import datetime, timedelta

from src.nofeardb.exceptions import DocumentLockException
from src.nofeardb.orm import Document
from src.nofeardb.engine import DocumentLock, StorageEngine

DATEFORMAT = '%Y-%m-%d %H:%M:%S'


def test_document_locked(mocker):
    lock_creation_date = datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)
    assert lock.is_locked() is True


def test_document_not_locked(mocker):
    lock_creation_date = datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)
    assert lock.is_locked() is False


def test_document_lock_expired(mocker):
    lock_creation_date = datetime.now()
    lock_creation_date = lock_creation_date - timedelta(0, 60)
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)
    assert lock.is_locked() is False


def test_document_lock_missing_date(mocker):
    lock_content = str(uuid.uuid4())
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)
    assert lock.is_locked() is False


def test_document_lock_wrong_date_format(mocker):
    lock_content = str(uuid.uuid4()) + "\nHelloWorld"
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)
    assert lock.is_locked() is False


def test_is_owner(mocker):

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)

    lock_creation_date = datetime.now()
    lock_content = str(lock._lock_id) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    assert lock._is_owner() is True


def test_is_not_owner(mocker):

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)

    lock_creation_date = datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    assert lock._is_owner() is False


def test_is_not_owner_missing_id(mocker):

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)

    mocked_fileread_data = mocker.mock_open(read_data="")
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    assert lock._is_owner() is False


def test_is_not_owner_wrong_id(mocker):

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)

    lock_creation_date = datetime.now()
    lock_content = str("HelloWorld") + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    assert lock._is_owner() is False


def test_try_to_lock_when_already_locked(mocker):
    lock_creation_date = datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_fileread_data = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_fileread_data)
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)
    with pytest.raises(DocumentLockException):
        lock.lock()


def test_lock_when_expired_lock_exists(mocker):
    lock_creation_date = datetime.now()
    lock_creation_date = lock_creation_date - timedelta(0, 60)
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_open)
    mocker.patch('os.makedirs')
    mocked_remove = mocker.patch('os.remove')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)
    original_cleanup = lock._cleanup_old_lock
    mocked_cleanup_lock = mocker.patch.object(
        DocumentLock, '_cleanup_old_lock', side_effect=original_cleanup)
    mocked_start_heartbeat = mocker.patch.object(
        DocumentLock, '_start_heartbeat')

    lock.lock()
    mocked_open.assert_called_with(os.path.normpath(
        "test/path/testdoc/" + str(doc.__id__) + ".lock"), "a", encoding="utf-8")
    mocked_cleanup_lock.assert_called_once()
    mocked_remove.assert_called_once()
    mocked_start_heartbeat.assert_called_once()


def test_lock_no_lock_exists(mocker):
    lock_creation_date = datetime.now()
    lock_creation_date = lock_creation_date - timedelta(0, 60)
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mocked_open)
    mocked_remove = mocker.patch('os.remove')
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)
    original_cleanup = lock._cleanup_old_lock
    mocked_cleanup_lock = mocker.patch.object(
        DocumentLock, '_cleanup_old_lock', side_effect=original_cleanup)
    mocked_start_heartbeat = mocker.patch.object(
        DocumentLock, '_start_heartbeat')

    lock.lock()
    mocked_open.assert_called_with(
        os.path.normpath("test/path/testdoc/" + str(doc.__id__) + ".lock"), "a", encoding="utf-8")
    mocked_cleanup_lock.assert_called_once()
    mocked_remove.assert_not_called()
    mocked_start_heartbeat.assert_called_once()


def test_release_owned_existing_lock(mocker):
    lock_creation_date = datetime.now()

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)

    lock_content = str(str(lock._lock_id)) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_open)
    mocked_remove = mocker.patch('os.remove')
    mocker.patch('os.makedirs')

    mocked_stop_heartbeat = mocker.patch.object(
        DocumentLock, '_stop_heartbeat')

    lock.release()
    mocked_open.assert_called_with(
        os.path.normpath("test/path/testdoc/" + str(doc.__id__) + ".lock"), "r", encoding="utf-8")
    mocked_remove.assert_called_once()
    mocked_stop_heartbeat.assert_called_once()


def test_try_releasing_not_owned_existing_lock(mocker):
    lock_creation_date = datetime.now()

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)

    lock_content = str(str(uuid.uuid4())) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_open)
    mocked_remove = mocker.patch('os.remove')
    mocker.patch('os.makedirs')

    with pytest.raises(DocumentLockException):
        lock.release()

    mocked_open.assert_called_with(
        os.path.normpath("test/path/testdoc/" + str(doc.__id__) + ".lock"), "r", encoding="utf-8")
    mocked_remove.assert_not_called()


def test_release_not_owned_existing_expired_lock(mocker):
    lock_creation_date = datetime.now()
    lock_creation_date = lock_creation_date - timedelta(0, 60)

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)

    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_open)
    mocked_remove = mocker.patch('os.remove')
    mocker.patch('os.makedirs')

    mocked_stop_heartbeat = mocker.patch.object(
        DocumentLock, '_stop_heartbeat')

    lock.release()
    mocked_open.assert_called_with(
        os.path.normpath("test/path/testdoc/" + str(doc.__id__) + ".lock"), "r", encoding="utf-8")
    mocked_remove.assert_called_once()
    mocked_stop_heartbeat.assert_called_once()


def test_try_releasing_not_existing_lock(mocker):
    lock_creation_date = datetime.now()

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=60)

    lock_content = str(str(uuid.uuid4())) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mocked_open)
    mocked_remove = mocker.patch('os.remove')
    mocker.patch('os.makedirs')

    mocked_stop_heartbeat = mocker.patch.object(
        DocumentLock, '_stop_heartbeat')

    lock.release()

    mocked_open.assert_not_called()
    mocked_remove.assert_not_called()
    mocked_stop_heartbeat.assert_not_called()


def test_heartbeat_start_and_stop_owned_lock(mocker):
    lock_creation_date = datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', side_effect=[
                 False, True, True, False, True, True])
    mocker.patch('builtins.open', mocked_open)
    mocker.patch('os.remove')
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=2)
    mocker.patch.object(
        DocumentLock, '_cleanup_old_lock')
    mocker.patch.object(
        DocumentLock, '_is_owner', return_value=True)
    mocked_heartbeat_update = mocker.patch.object(
        DocumentLock, '_update_lock_timestamp')

    lock.lock()
    heartbeat_thread = lock._heartbeat_thread
    lock.release()

    mocked_heartbeat_update.assert_called_once()
    assert heartbeat_thread.is_alive() is False

    lock.lock()
    heartbeat_thread = lock._heartbeat_thread
    lock.release()

    assert mocked_heartbeat_update.call_count == 2
    assert heartbeat_thread.is_alive() is False


def test_heartbeat_start_and_stop_not_owned_lock(mocker):
    lock_creation_date = datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', side_effect=[True, True])
    mocker.patch('builtins.open', mocked_open)
    mocker.patch('os.remove')
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    lock = DocumentLock(engine, doc, expiration=2)
    mocker.patch.object(
        DocumentLock, '_cleanup_old_lock')
    mocker.patch.object(
        DocumentLock, '_is_owner', return_value=False)
    mocked_heartbeat_update = mocker.patch.object(
        DocumentLock, '_update_lock_timestamp')

    with pytest.raises(DocumentLockException):
        lock.lock()
        lock.release()

    mocked_heartbeat_update.assert_not_called()


def test_update_lock(mocker):
    lock_creation_date = datetime.now()
    lock_content = str(uuid.uuid4()) + "\n" + \
        lock_creation_date.strftime(DATEFORMAT)
    mocked_open = mocker.mock_open(read_data=lock_content)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mocked_open)
    mocker.patch('os.remove')
    mocked_replace = mocker.patch('os.replace')
    mocker.patch('os.makedirs')

    class TestDoc(Document):
        pass

    engine = StorageEngine("test/path")
    engine.register_models([TestDoc])

    doc = TestDoc()

    mocker.patch.object(
        DocumentLock, '_is_owner', return_value=True)
    mocker.patch.object(
        DocumentLock, '_is_lock_expired', return_value=False)

    lock = DocumentLock(engine, doc, expiration=1)
    lock._start_heartbeat()
    time.sleep(2)
    lock._stop_heartbeat()
    time.sleep(1)

    assert mocked_replace.call_count == 4
