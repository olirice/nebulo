# pylint: disable=unused-argument
import re
from typing import Type

from nebulo.sql.table_base import TableBase
from nebulo.text_utils import snake_to_camel, to_plural
from sqlalchemy import Table, event


def to_camelcase(text: str) -> str:
    return str(text[0].lower() + re.sub(r"_([a-z])", lambda m: m.group(1).upper(), text[1:]))


def rename_table(base: Type[TableBase], tablename: str, table: Table) -> str:
    "Produce a 'camelized' class name, e.g. "
    "'words_and_underscores' -> 'WordsAndUnderscores'"
    return to_camelcase(tablename)


def rename_to_one_collection(base, local_cls, referred_cls, constraint) -> str:
    referred_name = referred_cls.__name__
    camel_name = to_camelcase(referred_name)
    return camel_name + "By" + "And".join(snake_to_camel(col.name) for col in constraint.columns)


def rename_to_many_collection(base, local_cls, referred_cls, constraint) -> str:
    "Produce an 'uncamelized', 'pluralized' class name, e.g. "
    "'SomeTerm' -> 'some_terms'"
    referred_name = referred_cls.__name__
    pluralized = to_plural(referred_name)
    camel_name = to_camelcase(pluralized)
    return camel_name + "By" + "And".join(snake_to_camel(col.name) for col in constraint.columns)


def rename_columns() -> None:
    @event.listens_for(Table, "column_reflect")
    def camelize_column_on_reflection(inspector, table, column_info):
        """Listen for when columns are reflected and adjust the SQLA ORM
        attribute name to camelcase"""
        column_info["key"] = to_camelcase(column_info["name"])
