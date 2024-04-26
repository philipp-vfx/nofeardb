from enum import Enum

class DocumentStatus(Enum):
    NEW = 1
    SYNC = 2
    MOD = 3
    DEL = 4

class RelationshipType(Enum):
    ManyToMany = 1
    ManyToOne = 2
    OneToMany = 3
    OneToOne = 4