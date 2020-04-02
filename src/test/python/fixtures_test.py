from .conftests import engine, sqla_db

__all__ = ["engine", "sqla_db"]


def test_engine(engine):
    assert True


def test_database(sqla_db):
    """Ensure that the testing database is available"""
    assert True
