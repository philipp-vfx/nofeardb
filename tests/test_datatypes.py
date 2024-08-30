# pylint: skip-file

import pytest
import uuid

from src.nofeardb.datatypes import Integer, Float, String, DateTime, UUID, Boolean
from datetime import datetime


def test_integer():
    assert Integer.deserialize("2") == 2
    assert Integer.deserialize("-2") == -2
    assert Integer.deserialize("2.0") == 2
    assert Integer.deserialize("0x12F") == 303
    assert Integer.cast(2) == 2
    assert Integer.cast(2.0) == 2

    assert Integer.serialize(2) == 2
    assert Integer.serialize(-2) == -2
    assert Integer.serialize(2.0) == 2
    assert Integer.serialize(0x12F) == 303

    with pytest.raises(ValueError):
        Integer.cast("hello")

    with pytest.raises(AttributeError):
        Integer.serialize("2")


def test_bool():
    assert Boolean.deserialize("True") == True
    assert Boolean.deserialize("None") == None
    assert Boolean.deserialize("true") == True
    assert Boolean.deserialize("1") == True
    assert Boolean.deserialize("False") == False
    assert Boolean.deserialize("false") == False
    assert Boolean.deserialize("0") == False
    assert Boolean.cast(True) == True
    assert Boolean.cast(False) == False
    assert Boolean.cast(0) == False
    assert Boolean.cast(1) == True

    assert Boolean.serialize(True) == "True"
    assert Boolean.serialize(1) == "True"
    assert Boolean.serialize(False) == "False"
    assert Boolean.serialize(0) == "False"

    with pytest.raises(AttributeError):
        Boolean.serialize("hallo")


def test_Float():
    assert Float.deserialize("2") == 2.0
    assert Float.deserialize("2.0") == 2.0
    assert Float.deserialize("-2.0") == -2.0
    assert Float.deserialize("0x12F") == 303.0
    assert Float.cast(2) == 2.0
    assert Float.cast(2.0) == 2.0
    assert Float.cast(-2.0) == -2.0

    assert Float.serialize(2) == 2.0
    assert Float.serialize(2.0) == 2.0
    assert Float.serialize(0x12F) == 303.0

    with pytest.raises(ValueError):
        Float.cast("hello")

    with pytest.raises(AttributeError):
        Float.serialize("2")


def test_String():
    assert String.deserialize("2") == "2"
    assert String.deserialize("2.0") == "2.0"
    assert String.deserialize("hello") == "hello"
    assert String.serialize("hello") == "hello"
    assert String.cast(2) == "2"
    assert String.cast(2.0) == "2.0"
    assert String.cast("hello") == "hello"

    with pytest.raises(AttributeError):
        String.serialize(2)


def test_DateTime():
    now = datetime.now()
    assert DateTime.deserialize(now.isoformat()) == now
    assert DateTime.serialize(now) == now.isoformat()
    assert DateTime.cast(now) == now

    with pytest.raises(AttributeError):
        DateTime.serialize(2)

    with pytest.raises(AttributeError):
        DateTime.cast(2)


def test_UUID():
    test = uuid.uuid4()
    assert UUID.deserialize(str(test)) == test
    assert UUID.cast(test) == test
    assert UUID.serialize(test) == str(test)

    with pytest.raises(AttributeError):
        UUID.serialize(2)

    with pytest.raises(AttributeError):
        UUID.cast(2)


def test_setting_none():
    assert UUID.serialize(None) == None
    assert Integer.serialize(None) == None
    assert Float.serialize(None) == None
    assert String.serialize(None) == None
    assert Boolean.serialize(None) == None
    assert DateTime.serialize(None) == None

    assert UUID.deserialize(None) == None
    assert Integer.deserialize(None) == None
    assert Float.deserialize(None) == None
    assert String.deserialize(None) == None
    assert Boolean.deserialize(None) == None
    assert DateTime.deserialize(None) == None
