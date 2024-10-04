

import pytest
from src.nofeardb.exceptions import NoResultFoundException
from src.nofeardb.engine import StorageEngine
from src.nofeardb.query import Query
from src.nofeardb.datatypes import UUID, Integer
from src.nofeardb.orm import Document, Field
import src.nofeardb.expr as expr


def test_query_where(mocker):
    class TestDoc(Document):
        uuid = Field(UUID, primary_key=True)
        int_field = Field(Integer)

    docs = []
    for i in range(10):
        doc = TestDoc()
        doc.int_field = i
        docs.append(doc)

    mock_result = Query(docs)

    mocker.patch.object(
        StorageEngine, 'read', return_value=mock_result)

    engine = StorageEngine("test/path")
    result = engine.read(TestDoc).where(
        expr.and_(
            expr.lt("int_field", 5),
            expr.gt("int_field", 3)
        )
    ).all()

    assert len(result) == 1
    assert result[0].int_field == 4


def test_query_first(mocker):
    class TestDoc(Document):
        uuid = Field(UUID, primary_key=True)
        int_field = Field(Integer)

    docs = []
    for i in range(10):
        doc = TestDoc()
        doc.int_field = i
        docs.append(doc)

    mock_result = Query(docs)

    mocker.patch.object(
        StorageEngine, 'read', return_value=mock_result)

    engine = StorageEngine("test/path")
    result = engine.read(TestDoc).first()

    assert result.int_field == 0


def test_query_last(mocker):
    class TestDoc(Document):
        uuid = Field(UUID, primary_key=True)
        int_field = Field(Integer)

    docs = []
    for i in range(10):
        doc = TestDoc()
        doc.int_field = i
        docs.append(doc)

    mock_result = Query(docs)

    mocker.patch.object(
        StorageEngine, 'read', return_value=mock_result)

    engine = StorageEngine("test/path")
    result = engine.read(TestDoc).last()

    assert result.int_field == 9


def test_query_empty_result(mocker):
    class TestDoc(Document):
        uuid = Field(UUID, primary_key=True)
        int_field = Field(Integer)

    docs = []

    mock_result = Query(docs)

    mocker.patch.object(
        StorageEngine, 'read', return_value=mock_result)

    engine = StorageEngine("test/path")
    with pytest.raises(NoResultFoundException):
        engine.read(TestDoc).last()

    with pytest.raises(NoResultFoundException):
        engine.read(TestDoc).first()

    assert engine.read(TestDoc).all() == []
