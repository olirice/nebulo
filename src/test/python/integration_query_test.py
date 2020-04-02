def test_engine(engine):
    assert True


def test_connection(sqla_db):
    """Ensure that the testing database is available"""
    session = sqla_db.session
    result = session.execute("select 1").fetchone()
    assert result == (1,)


def test_reflection(sqla_db):
    database = sqla_db
    assert len(database.models) > 0
