"""ORM Datatypes"""

import uuid
import typing
from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class OrmDataType(ABC):
    """Abstract ORM Datatype"""

    @classmethod
    @abstractmethod
    def cast(cls, value):
        """tries to cast the given value to the expected datatype"""

    @classmethod
    @abstractmethod
    def serialize(cls, value) -> str:
        """serializes the given value to a string based on the datatype"""

    @classmethod
    @abstractmethod
    def deserialize(cls, value: str):
        """deserializes a string to the expected datatype"""


class UUID(OrmDataType):
    """ORM UUID Datatype"""

    @classmethod
    def cast(cls, value) -> typing.Optional[uuid.UUID]:
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return value

        if isinstance(value, str):
            return uuid.UUID(value)

        raise AttributeError("Argument must be of type str of uuid.UUID")

    @classmethod
    def serialize(cls, value: typing.Optional[uuid.UUID]) -> typing.Optional[str]:
        if value is None:
            return None

        if not isinstance(value, uuid.UUID):
            raise AttributeError("Argument must be of type uuid.UUID")

        return str(value)

    @classmethod
    def deserialize(cls, value: str) -> typing.Optional[uuid.UUID]:
        return cls.cast(value)


class Boolean(OrmDataType):
    """ORM Integer Datatype"""

    @classmethod
    def cast(cls, value) -> typing.Optional[bool]:
        if value is None:
            return None

        if isinstance(value, str):
            if value.lower() in ["none", "null"]:
                return None

            return value in ["True", "true", "1"]

        return bool(value)

    @classmethod
    def serialize(cls, value: typing.Optional[bool]) -> typing.Optional[str]:
        if value is None:
            return None

        if not isinstance(value, bool) and not isinstance(value, int):
            raise AttributeError("Argument must be of type boolean")

        return str(bool(value))

    @classmethod
    def deserialize(cls, value: str) -> typing.Optional[bool]:
        return cls.cast(value)


class Integer(OrmDataType):
    """ORM Integer Datatype"""

    @classmethod
    def cast(cls, value) -> typing.Optional[int]:
        if value is None:
            return None

        if isinstance(value, str) and "." in value:
            return int(float(value))

        if isinstance(value, str) and "x" in value:
            return int(value, base=16)

        return int(value)

    @classmethod
    def serialize(cls, value: typing.Optional[int]) -> typing.Optional[str]:
        if value is None:
            return None

        if not isinstance(value, int) and not isinstance(value, float):
            raise AttributeError("Argument must be of type int or float")

        return int(value)

    @classmethod
    def deserialize(cls, value: str) -> typing.Optional[int]:
        return cls.cast(value)


class Float(OrmDataType):
    """ORM Float Datatype"""

    @classmethod
    def cast(cls, value) -> typing.Optional[float]:
        if value is None:
            return None

        if isinstance(value, str) and "x" in value:
            return float(int(value, base=16))

        return float(value)

    @classmethod
    def serialize(cls, value: typing.Optional[float]) -> typing.Optional[str]:
        if value is None:
            return None

        if not isinstance(value, int) and not isinstance(value, float):
            raise AttributeError("Argument must be of type int or float")

        return float(value)

    @classmethod
    def deserialize(cls, value: str) -> typing.Optional[float]:
        return cls.cast(value)


class String(OrmDataType):
    """ORM String Datatype"""

    @classmethod
    def cast(cls, value) -> str:
        if value is None:
            return None

        return str(value)

    @classmethod
    def serialize(cls, value: typing.Optional[str]) -> typing.Optional[str]:
        if value is None:
            return None

        if not isinstance(value, str):
            raise AttributeError("Argument must be of type int or float")

        return str(value)

    @classmethod
    def deserialize(cls, value: str) -> typing.Optional[str]:
        return cls.cast(value)


class DateTime(OrmDataType):
    """ORM Datetime Datatype"""

    @classmethod
    def cast(cls, value) -> typing.Optional[datetime]:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            dt, _, us = value.partition(".")
            dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
            us = int(us.rstrip("Z"), 10)
            return dt + timedelta(microseconds=us)

        raise AttributeError("Argument must be of type datetime or str")

    @classmethod
    def serialize(cls, value: typing.Optional[datetime]) -> typing.Optional[str]:
        if value is None:
            return None

        return str(value.isoformat())

    @classmethod
    def deserialize(cls, value: str) -> typing.Optional[datetime]:
        return cls.cast(value)
