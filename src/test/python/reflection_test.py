from .conftests import engine, sqla_db

__all__ = ["engine", "sqla_db"]


def test_reflection(sqla_db):
    database = sqla_db
    assert len(database.models) > 0
