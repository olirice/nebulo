from .conftests import engine, sqla_db
from nebulous.sql.table_base import TableBase
import sqlalchemy as sqla
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION

__all__ = ["engine", "sqla_db"]


SQL_UP = """
CREATE TABLE public.refl_numer (
    col_0 int primary key,
    col_1 smallint, 
    col_2 integer, 
    col_3 bigint, 
    col_4 smallserial,
    col_5 bigserial,
    col_6 numeric,
    col_7 numeric(10,2),
    col_8 real,
    col_9 double precision
);
"""


def test_reflect_numeric_types(engine):
    engine.execute(SQL_UP)

    TableBase.prepare(engine, reflect=True, schema="public")
    tab = TableBase.classes['refl_numer']
    tab.col_7.type.asdecimal=True
    assert isinstance(tab.col_0.type, sqla.Integer)
    assert isinstance(tab.col_1.type, sqla.Integer)
    assert isinstance(tab.col_2.type, sqla.Integer)
    assert isinstance(tab.col_3.type, sqla.Integer)
    assert isinstance(tab.col_4.type, sqla.Integer)
    assert isinstance(tab.col_5.type, sqla.Integer)
    assert isinstance(tab.col_6.type, sqla.Numeric)
    assert isinstance(tab.col_7.type, sqla.Numeric)
    assert isinstance(tab.col_8.type, sqla.REAL)
    assert isinstance(tab.col_9.type, DOUBLE_PRECISION)
