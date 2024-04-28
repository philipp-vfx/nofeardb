from enum import Enum


class DocumentStatus(Enum):
    NEW = 1
    SYNC = 2
    MOD = 3
    DEL = 4


class RelationshipType(Enum):
    MANY_TO_MANY = 1
    MANY_TO_ONE = 2
    ONE_TO_MANY = 3
    ONE_TO_ONE = 4
