from collections import namedtuple

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import _CreateDropBase
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import SchemaType, to_instance, TypeDecorator, UserDefinedType, TypeEngine
from nebulo.text_utils import snake_to_camel

psycopg2 = None
CompositeCaster = None
adapt = None
AsIs = None
register_adapter = None
try:
    import psycopg2
    from psycopg2.extras import CompositeCaster
    from psycopg2.extensions import adapt, AsIs, register_adapter
except ImportError:
    pass

class CompositeElement(FunctionElement):
    """
    Instances of this class wrap a Postgres composite type.
    """

    def __init__(self, base, field, type_):
        self.name = field
        self.type = to_instance(type_)

        super(CompositeElement, self).__init__(base)


@compiles(CompositeElement)
def _compile_pgelem(expr, compiler, **kw):
    return "(%s).%s" % (compiler.process(expr.clauses, **kw), expr.name)


class CompositeArray(ARRAY):
    def _proc_array(self, arr, itemproc, dim, collection):
        if dim is None:
            if isinstance(self.item_type, CompositeType):
                arr = [itemproc(a) for a in arr]
                return arr
        return ARRAY._proc_array(self, arr, itemproc, dim, collection)


# TODO: Make the registration work on connection level instead of global level
registered_composites = {}


from typing import List, Type
from sqlalchemy import Column

def composite_type_factory(name, columns):

    
    #if name in registered_composites:
    #    self.type_cls = registered_composites[name].type_cls
    #else:
    #registered_composites[name] = self

    for column in columns:
        column.key = snake_to_camel(column.name)

    class Caster(CompositeCaster):
        def make(self, values):
            return self.type_cls(*values)

    def init(self, *args, **kwargs):
        pass


    composite = type(name, (CompositeType,), {
        'name': name,
        'columns': columns,
        'type_cls': namedtuple(name, [c.name for c in columns]),
        '__init__': init
        }) 
    return composite


class CompositeType(UserDefinedType):
    """
    Represents a PostgreSQL composite type.

    :param name:
        Name of the composite type.
    :param columns:
        List of columns that this composite type consists of
    """

    python_type = tuple

    name: str
    columns: List[Column] = []
    type_cls: Type = None


    class comparator_factory(UserDefinedType.Comparator):
        def __getattr__(self, key):
            try:
                type_ = self.type.typemap[key]
            except KeyError:
                raise KeyError(
                    "Type '%s' doesn't have an attribute: '%s'" % (self.name, key)
                )

            return CompositeElement(self.expr, key, type_)


    def get_col_spec(self):
        return self.name

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            processed_value = []
            for i, column in enumerate(self.columns):
                if isinstance(column.type, TypeDecorator):
                    processed_value.append(
                        column.type.process_bind_param(value[i], dialect)
                    )
                else:
                    processed_value.append(value[i])
            return self.type_cls(*processed_value)

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            cls = value.__class__
            kwargs = {}
            for column in self.columns:
                if isinstance(column.type, TypeDecorator):
                    kwargs[column.name] = column.type.process_result_value(
                        getattr(value, column.name), dialect
                    )
                else:
                    kwargs[column.name] = getattr(value, column.name)
            return cls(**kwargs)

        return process

@compiles(CompositeElement)
def _compile_pgelem(expr, compiler, **kw):
    return '(%s).%s' % (compiler.process(expr.clauses, **kw), expr.name)
