from enum import StrEnum


class OrmEventListenerFlagKey(StrEnum):
    META_APPLIED = "meta_applied"


class SqlAlchemyExecutionOptionKey(StrEnum):
    META = "_cmeta"
