"""
Exceptions raised by Liquibase changelog loading.
"""


class LiquibaseReadingError(Exception):
    """
    Raised when a Liquibase changelog cannot be read or applied to the in-memory schema.
    """
