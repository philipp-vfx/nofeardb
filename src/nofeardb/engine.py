"""
Engine Classes
"""

# pylint: disable=dangerous-default-value

import os
import json
import uuid
from typing import List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .exceptions import DocumentLockException, NotCreateableException

from .datatypes import OrmDataType, UUID
from .enums import DocumentStatus
from .orm import Document, Field, ManyToMany, ManyToOne, OneToMany, Relationship
from .query import Query


class StorageEngine:
    """Storage Engine Class"""

    def __init__(self, root: str):
        self._root = os.path.normpath(root)
        self._models = []
        self._data_cache = {}

    def register_models(self, models: List[type]):
        """
        Register the model classes to the storage engine. 
        Needed to recosntruct the models from json.
        """
        for model in models:
            if not issubclass(model, Document):
                raise ValueError(str(model) + " is not of type \'Document\'")

        for model in models:
            if model not in self._models:
                self._models.append(model)

    def create_json(self, doc: Document) -> dict:
        """creates the json that should be stored for a new object"""

        doc_json = {}

        for name, attr in vars(doc.__class__).items():
            doc_json["id"] = str(doc.__id__)
            if isinstance(attr, Field):
                if name != doc.__primary_key_attribute__:
                    field_type: OrmDataType = getattr(doc, name + "__datatype")
                    doc_json[name] = field_type.serialize(getattr(doc, name))

            if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                doc_json[name] = [str(rel.__id__)
                                  for rel in getattr(doc, name)]

            if isinstance(attr, ManyToOne):
                if getattr(doc, name) is not None:
                    doc_json[name] = [str(getattr(doc, name).__id__)]
                else:
                    doc_json[name] = [None]

        return doc_json

    def update_json(self, json_to_update: dict, doc: Document) -> dict:
        """updates the json by modified fields of an object"""

        for name, attr in vars(doc.__class__).items():
            if name in doc.__changed_fields__:
                if isinstance(attr, Field):
                    field_type: OrmDataType = getattr(doc, name + "__datatype")
                    json_to_update[name] = field_type.serialize(
                        getattr(doc, name))

            if name in doc.__added_relationships__:
                if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                    if doc.__added_relationships__[name] is not None:
                        for rel in doc.__added_relationships__[name]:
                            if name in json_to_update.keys():
                                if str(rel.__id__) not in json_to_update[name]:
                                    json_to_update[name].append(
                                        str(rel.__id__))
                            else:
                                json_to_update[name] = [str(rel.__id__)]

                if isinstance(attr, ManyToOne):
                    if doc.__added_relationships__[name] is not None:
                        for rel in doc.__added_relationships__[name]:
                            json_to_update[name] = str(rel.__id__)

            if name in doc.__removed_relationships__:
                if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                    if doc.__removed_relationships__[name] is not None:
                        for rel in doc.__removed_relationships__[name]:
                            if name in json_to_update.keys():
                                if str(rel.__id__) in json_to_update[name]:
                                    json_to_update[name].remove(
                                        str(rel.__id__))

                if isinstance(attr, ManyToOne):
                    if doc.__removed_relationships__[name] is not None:
                        for rel in doc.__removed_relationships__[name]:
                            if json_to_update[name] == str(rel.__id__):
                                json_to_update[name] = None

        return json_to_update

    def resolve_dependencies(
        self, doc: Document, scope: str = None
    ) -> List[Document]:
        """creates a stack with depending documents"""

        dependencies = []

        children = [doc]

        while len(children) > 0:
            child = children.pop()
            if child not in dependencies:
                dependencies.append(child)

            for name, attr in vars(child.__class__).items():
                if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                    if scope is None or scope in attr.cascade:
                        for rel in getattr(child, name):
                            if rel not in children and rel not in dependencies:
                                children.append(rel)

                if isinstance(attr, ManyToOne):
                    if scope is None or scope in attr.cascade:
                        if getattr(child, name) is not None:
                            if (
                                getattr(child, name) not in children
                                and getattr(child, name) not in dependencies
                            ):
                                children.append(getattr(child, name))

        return dependencies

    def _remove_dependencies(self, doc: Document):
        """
        clears all direct relationships on the document
        """

        for name, attr in vars(doc.__class__).items():
            if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                setattr(doc, name, [])

            if isinstance(attr, ManyToOne):
                setattr(doc, name, None)

    def get_doc_basepath(self, doc: Document):
        """get the base file path for the document type"""
        return os.path.join(self._root, doc.get_document_name())

    def _get_document_with_id_existing(self, doc: Document):
        """Checks wether a document with the same ID already exists."""
        doc_base_path = self.get_doc_basepath(doc)
        if os.path.exists(doc_base_path):
            existing_ids = [doc_name.split("__")[0]
                            for doc_name in os.listdir(doc_base_path)]
            return str(doc.__id__) in existing_ids

        return False

    def _check_all_documents_can_be_written(self, docs: List[Document]):
        """
        Checks wether all documents can be created or updated (no id collision etc.).
        If one document fails the check, a RuntimeError is raised.
        """
        for doc in docs:
            if doc.__status__ == DocumentStatus.NEW:
                if self._get_document_with_id_existing(doc):
                    raise RuntimeError(
                        "Document "
                        + str(doc)
                        + " is marked as new, but an document with the same ID is already existing."
                    )
            if doc.__status__ == DocumentStatus.MOD:
                if not self._get_document_with_id_existing(doc):
                    raise RuntimeError(
                        "The document "
                        + str(doc)
                        + " is marked as modified, but no document with the id "
                        + str(doc.__id__) + " exists.")

        return True

    def _lock_docs(self, docs: List[Document]) -> List['DocumentLock']:
        locks: List['DocumentLock'] = []
        try:
            for doc in docs:
                if doc.__status__ != DocumentStatus.SYNC:
                    lock = DocumentLock(self, doc, expiration=10)
                    lock.lock()
                    locks.append(lock)
        except DocumentLockException as e:
            self._unlock_docs(locks)
            raise DocumentLockException from e

        return locks

    def _unlock_docs(self, locks: List['DocumentLock']):
        for lock in locks:
            try:
                lock.release()
            except DocumentLockException:
                pass

    def _get_existing_document_file_name(self, doc: Document):
        """get the filename of the document if it is already persisted to disk"""
        doc_base_path = self.get_doc_basepath(doc)
        for file in os.listdir(doc_base_path):
            if "__" in file:
                if file.split("__")[0] == str(doc.__id__) and os.path.splitext(file)[1] != '.tmp':
                    return os.path.join(doc_base_path, file)

        return None

    def _extract_id_and_hash_from_filename(self, doc_path):
        try:
            filename, _ = os.path.splitext(os.path.basename(doc_path))
            doc_id, doc_hash = filename.split("__")
            return (doc_id, doc_hash)
        except (ValueError, TypeError):
            return (None, None)

    def _read_document_bytes(self, doc_path: str, size=-1) -> bytes:
        fd = os.open(doc_path, os.O_RDONLY)
        try:
            if size == -1:
                size = os.fstat(fd).st_size
            return os.read(fd, size)
        finally:
            os.close(fd)

    def _read_document_from_disk(self, doc_path) -> dict:
        if doc_path is not None:
            doc_id, doc_hash = self._extract_id_and_hash_from_filename(
                doc_path)
            try:
                data = json.loads(self._read_document_bytes(doc_path))
                if doc_id is not None and doc_hash is not None:
                    # update data cache
                    data["__doc_hash__"] = doc_hash
                    self._data_cache[doc_id] = data
            except (PermissionError, IOError):
                data = None

            return data

        return None

    def _read_document_from_cache(self, doc_path) -> dict:
        doc_id, doc_hash = self._extract_id_and_hash_from_filename(doc_path)
        if doc_id is not None and doc_hash is not None:
            try:
                cache_data = dict(self._data_cache[doc_id])
                cache_hash = cache_data['__doc_hash__']
                if cache_hash == doc_hash:
                    del cache_data['__doc_hash__']
                    return cache_data
            except KeyError:
                return None

        return None

    def _get_document_data(self, doc_path):
        data = self._read_document_from_cache(doc_path)
        if data is None:
            data = self._read_document_from_disk(doc_path)

        return data

    def write_json(self, doc: Document):
        """writes the document data to disk"""
        if doc.__status__ != DocumentStatus.SYNC and doc.__status__ != DocumentStatus.DEL:
            previous_file = self._get_existing_document_file_name(doc)
            previous_data = self._get_document_data(previous_file)
            data_to_write = None
            if previous_data is not None:
                data_to_write = self.update_json(previous_data, doc)
            else:
                data_to_write = self.create_json(doc)

            doc_path = os.path.join(self.get_doc_basepath(
                doc), str(doc.__id__) + "__" + doc.get_hash() + ".json")
            doc_temp_path = doc_path + ".tmp"

            with open(doc_temp_path, 'w', encoding="utf-8") as f:
                json.dump(data_to_write, f)

            if previous_file is not None:
                os.remove(previous_file)

            os.rename(doc_temp_path, doc_path)

    def delete_json(self, doc: Document):
        """
        deletes document data from disk
        """

        if doc.__status__ != DocumentStatus.DEL:
            base_path = self.get_doc_basepath(doc)
            doc_name = self._get_existing_document_file_name(doc)
            doc_path = os.path.join(base_path, doc_name)
            os.remove(doc_path)

    def _create_base_pathes(self):
        for doc in self._models:
            base_path = self.get_doc_basepath(doc)
            if not os.path.exists(base_path):
                os.makedirs(base_path)

    def create(self, doc: Document):
        """
        create the document (and persist changes to all related documents)

        :param doc: document to create.
        :type doc: :class:`nofeardb.orm.Document`
        :raise nofeardb.exceptions.NotCreateableException: If the document can not be created.
        """
        if doc.__status__ is not DocumentStatus.NEW:
            raise RuntimeError(
                "The document is not new. Only new documents can be created")

        errors = doc.validate()
        if len(errors) > 0:
            raise NotCreateableException(errors[0])

        self._create_base_pathes()

        dependencies = self.resolve_dependencies(doc)
        if self._check_all_documents_can_be_written(dependencies):
            locks = self._lock_docs(dependencies)
            for dep in dependencies:
                if (
                    dep.__status__ == DocumentStatus.NEW
                    or dep.__status__ == DocumentStatus.MOD
                ):
                    self.write_json(dep)
                    dep.__status__ = DocumentStatus.SYNC

            self._unlock_docs(locks)

    def update(self, doc: Document):
        """update the document"""
        if doc.__status__ is DocumentStatus.NEW:
            raise RuntimeError(
                "The document is not persisted. Please run \'create\' before.")

        if doc.__status__ is DocumentStatus.DEL:
            raise RuntimeError("Deleted documents cannot be updated")

        self._create_base_pathes()

        dependencies = self.resolve_dependencies(doc)
        if self._check_all_documents_can_be_written(dependencies):
            locks = self._lock_docs(dependencies)
            for dep in dependencies:
                if (
                    dep.__status__ == DocumentStatus.NEW
                    or dep.__status__ == DocumentStatus.MOD
                ):
                    self.write_json(dep)
                    dep.__status__ = DocumentStatus.SYNC

            self._unlock_docs(locks)

    def delete(self, doc: Document):
        """delete the document"""

        if doc.__status__ is DocumentStatus.NEW:
            raise RuntimeError(
                "The document is not persisted. Please run \'create\' before.")

        if doc.__status__ is DocumentStatus.DEL:
            raise RuntimeError("Deleted documents cannot be deleted again")

        to_delete = self.resolve_dependencies(doc, scope="delete")
        all_dependencies = self.resolve_dependencies(doc)
        if self._check_all_documents_can_be_written(all_dependencies):
            locks = self._lock_docs(all_dependencies)

            for dep in to_delete:
                if (
                    dep.__status__ != DocumentStatus.NEW
                ):
                    self.delete_json(dep)

                self._remove_dependencies(dep)
                dep.__status__ = DocumentStatus.DEL

            for dep in all_dependencies:
                if (
                    dep not in to_delete
                ):
                    self.write_json(dep)

            self._unlock_docs(locks)

    def _get_doc_class_by_name(self, name) -> type:
        for model in self._models:
            if model.__name__ == name:
                return model

        raise RuntimeError("Document class " + str(name) +
                           "not registered in engine.")

    def _fill_document_with_data(self, doc: Document, data: dict):
        for name, attr in vars(doc.__class__).items():
            value = None
            try:
                value = data[name]
            except KeyError:
                pass
            if isinstance(attr, Field):
                if value is not None:
                    setattr(doc, name, value)

            elif isinstance(attr, Relationship):
                rel_class = self._get_doc_class_by_name(attr._rel_class_name)
                rel_docs = []
                if value is not None:
                    for rel_id in value:
                        rel_doc = rel_class()
                        rel_doc.__id__ = UUID.cast(rel_id)
                        rel_docs.append(rel_doc)

                    if len(rel_docs) > 0:
                        loaded_relationship = getattr(doc, name)
                        if isinstance(attr, ManyToMany) or isinstance(attr, OneToMany):
                            if loaded_relationship is not None:
                                for rel_doc in rel_docs:
                                    if (
                                        rel_doc.__id__ not in [
                                            doc.__id__ for doc in loaded_relationship]
                                    ):
                                        loaded_relationship.append(rel_doc)
                        elif isinstance(attr, ManyToOne):
                            if (
                                loaded_relationship is None
                                or rel_docs[0].__id__ != loaded_relationship.__id__
                            ):
                                setattr(doc, name, rel_docs[0])

                for rel_doc in rel_docs:
                    rel_doc.__status__ = DocumentStatus.LAZY
                    rel_doc.__added_relationships__ = {}
                    rel_doc.__removed_relationships__ = {}
                    rel_doc.__engine__ = self

        doc.__added_relationships__ = {}
        doc.__removed_relationships__ = {}
        doc.__status__ = DocumentStatus.SYNC

    def lazy_load(self, doc: Document):
        """executes lazy loading for docs that are marked as LAZY"""
        if doc.__status__ == DocumentStatus.LAZY:
            doc_path = self._get_existing_document_file_name(doc)
            data = self._get_document_data(doc_path)
            self._fill_document_with_data(doc, data)

    def _concurrent_read_helper(self, doc_type: type, document_path: str):
        data = self._get_document_data(document_path)
        doc = doc_type()

        try:
            value = UUID.cast(data["id"])
            setattr(doc, "__id__", value)
        except KeyError:
            pass

        self._fill_document_with_data(doc, data)

        doc.__engine__ = self

        return doc

    def read(self, doc_type: type) -> Query:
        """read the documents of the specified type"""
        base_path = self.get_doc_basepath(doc_type)
        document_jsons = os.listdir(base_path)

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            # Submit tasks for each JSON file
            futures = [
                executor.submit(
                    self._concurrent_read_helper, doc_type, os.path.join(
                        base_path, document)
                )
                for document in document_jsons]

            # Wait for all tasks to complete
            documents = [future.result() for future in futures]

        return Query(documents)


class DocumentLock:
    """A Lock for a specific document"""

    def __init__(self, storage_engine: StorageEngine, document: Document, expiration: int = 60):
        self._lock_id = uuid.uuid4()
        self.__document = document
        self.__engine = storage_engine
        self.__lock_path = os.path.join(
            self.__engine.get_doc_basepath(self.__document),
            str(self.__document.__id__) + ".lock"
        )
        self.__dateformat = '%Y-%m-%d %H:%M:%S'
        self.__expiration = expiration

    def _is_lock_expired(self):
        try:
            with open(self.__lock_path, "r", encoding="utf-8") as lock_file:
                lines = lock_file.readlines()
                creation_date = datetime.strptime(lines[1], self.__dateformat)
                return (datetime.now()-creation_date).total_seconds() > self.__expiration
        except IndexError:
            return True
        except ValueError:
            return True

    def _is_owner(self):
        try:
            with open(self.__lock_path, "r", encoding="utf-8") as lock_file:
                lines = lock_file.readlines()
                lock_id = lines[0].strip()
                return lock_id == str(self._lock_id)
        except IndexError:
            return False

    def _cleanup_old_lock(self):
        if os.path.exists(self.__lock_path):
            os.remove(self.__lock_path)

    def lock(self):
        """locks a document"""
        if self.is_locked():
            raise DocumentLockException("Document is already locked.")

        self._cleanup_old_lock()

        with open(self.__lock_path, "a", encoding="utf-8") as lock_file:
            lock_file.writelines(
                [str(self._lock_id),
                 datetime.now().strftime(self.__dateformat)]
            )

    def release(self):
        """releases a document lock"""
        if os.path.exists(self.__lock_path):
            if self._is_owner() or self._is_lock_expired():
                os.remove(self.__lock_path)
            else:
                raise DocumentLockException(
                    "Cannot release a lock that is hold by someone else.")

    def is_locked(self) -> bool:
        """returns wether a document is currently locked"""
        if os.path.exists(self.__lock_path):
            if not self._is_lock_expired():
                return True

        return False
