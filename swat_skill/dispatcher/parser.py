"""Input parser for distinguishing input types."""

from ..skills.base import Skill, SkillResult, register_skill

SQL_KEYWORDS = [
    "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER",
    "DROP", "TRUNCATE", "WITH", "EXPLAIN", "BEGIN", "COMMIT",
]


def is_sql_statement(input: str) -> bool:
    """Check if input is a SQL statement.

    Args:
        input: User input string.

    Returns:
        True if input appears to be a SQL statement.
    """
    stripped = input.strip().upper()
    for keyword in SQL_KEYWORDS:
        if stripped.startswith(keyword):
            return True
    return False


@register_skill
class ParserSkill(Skill):
    """Parse user input."""

    name = "parse"
    description = "解析用户输入"

    def execute(self, conn, args, formatter):
        """Parse input."""
        pass