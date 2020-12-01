# pylint: disable=unused-argument
from __future__ import annotations

from nebulo.text_utils import camel_to_snake, snake_to_camel, to_plural
from sqlalchemy import Table


def rename_table(base, tablename: str, table: Table) -> str:
    """Produce a 'camelized' class name, e.g. 'words_and_underscores' -> 'WordsAndUnderscores'"""
    return snake_to_camel(tablename, upper=True)


def rename_to_one_collection(base, local_cls, referred_cls, constraint) -> str:
    referred_name = camel_to_snake(referred_cls.__name__).lower()

    return referred_name + "_by_" + "_and".join(col.name for col in constraint.columns)


def rename_to_many_collection(base, local_cls, referred_cls, constraint) -> str:
    "Produce an 'uncamelized', 'pluralized' class name, e.g. "
    "'SomeTerm' -> 'some_terms'"
    referred_name = camel_to_snake(referred_cls.__name__).lower()
    pluralized = to_plural(referred_name)
    return pluralized + "_by_" + "_and".join(col.name for col in constraint.columns)
