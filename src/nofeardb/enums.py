from enum import Enum


class DocumentStatus(Enum):
    NEW = 1
    SYNC = 2
    MOD = 3
    DEL = 4
    LAZY = 5
