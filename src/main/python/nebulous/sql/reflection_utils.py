# pylint: disable=unused-argument
import re
import inflect
import typing
from sqlalchemy import Table, event
from functools import lru_cache


from inflect import engine
from nebulous.sql.table_base import TableBase
from sqlalchemy.sql.schema import Table
from typing import Type
@lru_cache()
def get_pluralizer() -> engine:
    """Return an instance of inflection library's engine.
    This is wrapped in a function to reduce import side effects"""
    return inflect.engine()


def to_camelcase(text: str) -> str:
    return str(
        text[0].lower() + re.sub(r"_([a-z])", lambda m: m.group(1).upper(), text[1:])
    )


def camelize_classname(base: Type[TableBase], tablename: str, table: Table) -> str:
    "Produce a 'camelized' class name, e.g. "
    "'words_and_underscores' -> 'WordsAndUnderscores'"
    return to_camelcase(tablename)


def pluralize_collection(base, local_cls, referred_cls, constraint):
    "Produce an 'uncamelized', 'pluralized' class name, e.g. "
    "'SomeTerm' -> 'some_terms'"
    pluralizer = get_pluralizer()
    referred_name = referred_cls.__name__
    pluralized = pluralizer.plural(referred_name)
    return pluralized


def camelize_collection(base, local_cls, referred_cls, constraint):
    referred_name = referred_cls.__name__
    camel_name = to_camelcase(referred_name)
    return camel_name


def pluralize_and_camelize_collection(base, local_cls, referred_cls, constraint):
    "Produce an 'uncamelized', 'pluralized' class name, e.g. "
    "'SomeTerm' -> 'some_terms'"
    pluralizer = get_pluralizer()
    referred_name = referred_cls.__name__
    pluralized = pluralizer.plural(referred_name)
    camel_name = to_camelcase(pluralized)
    return camel_name


def camelize_columns() -> typing.NoReturn:
    @event.listens_for(Table, "column_reflect")
    def camelize_column_on_reflection(inspector, table, column_info):
        """Listen for when columns are reflected and adjust the SQLA ORM
        attribute name to camelcase"""
        column_info["key"] = to_camelcase(column_info["name"])
