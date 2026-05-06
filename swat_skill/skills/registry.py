"""Skill registry initialization.

Imports all skill modules to register them.
"""

from .base import Skill, SkillRegistry, SkillResult, QuerySkill, register_skill

# Import skill modules to trigger registration
# (skills will be added as they are implemented)
from .health import HealthSkill
from .dbtop import DbtopSkill
from .sessions import SessionsSkill, ActiveSessionsSkill
from .waits import WaitsSkill
from .locks import LocksSkill, BlockedLocksSkill, BlockTreeSkill
from .space import SpaceSkill, TableSizesSkill, IndexSizesSkill
from .vacuum import VacuumSkill
from .wal import WalSkill
from .replication import ReplicationSkill, SlotsSkill
from .longtx import LongTxSkill, IdleTxSkill
from .bloat import BloatSkill
from .xid import XidAgeSkill
from .buffer import BufferStatsSkill
from .slowsql import SlowSqlSkill
from .topsql import TopSqlTimeSkill, TopSqlCallsSkill
from .params import ParamsSkill, MemoryParamsSkill
from .users import UsersSkill
from .tableinfo import TableInfoSkill, TableIndexesSkill
from .indexhealth import UnusedIndexesSkill
from .sql import SqlSkill
from .explain import ExplainSkill
from .kill import KillSkill
from .help import HelpSkill
from .exit import ExitSkill
from .model import ModelSkill
from .llm import LlmSkill

__all__ = [
    "Skill",
    "SkillRegistry",
    "SkillResult",
    "QuerySkill",
    "register_skill",
    "HealthSkill",
    "DbtopSkill",
    "SessionsSkill",
    "ActiveSessionsSkill",
    "WaitsSkill",
    "LocksSkill",
    "BlockedLocksSkill",
    "BlockTreeSkill",
    "SpaceSkill",
    "TableSizesSkill",
    "IndexSizesSkill",
    "VacuumSkill",
    "WalSkill",
    "ReplicationSkill",
    "SlotsSkill",
    "LongTxSkill",
    "IdleTxSkill",
    "BloatSkill",
    "XidAgeSkill",
    "BufferStatsSkill",
    "SlowSqlSkill",
    "TopSqlTimeSkill",
    "TopSqlCallsSkill",
    "ParamsSkill",
    "MemoryParamsSkill",
    "UsersSkill",
    "TableInfoSkill",
    "TableIndexesSkill",
    "UnusedIndexesSkill",
    "SqlSkill",
    "ExplainSkill",
    "KillSkill",
    "HelpSkill",
    "ExitSkill",
    "ModelSkill",
    "LlmSkill",
]