"""
swat_skill - PostgreSQL Database CLI Agent

A database CLI agent inspired by Claude Code's interactive approach.
Provides three interaction modes: /commands, SQL statements, and natural language.
"""

__version__ = "1.6.0"
__author__ = "swat_skill"

from .config import Config, load_config
from .database.connection import ConnectionManager
from .skills import SkillRegistry  # Import skills first to register them
from .dispatcher.router import Dispatcher

__all__ = ["Config", "load_config", "ConnectionManager", "Dispatcher", "SkillRegistry"]