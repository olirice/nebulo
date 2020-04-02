from functools import lru_cache

from sqlalchemy import asc, desc

from nebulous.text_utils import snake_to_camel

from ..alias import EnumType, EnumValue, InputObjectType

__all__ = ["ordering_factory"]


@lru_cache()
def to_default_ordering(sqla_model):
    # TODO(OR): Support multi-column primary key
    pk_order = []
    for col in sqla_model.primary_key.columns:
        pk_order.append((col.key, asc))
    return pk_order


@lru_cache()
def ordering_factory(sqla_model) -> InputObjectType:
    result_name = f"{snake_to_camel(sqla_model.__table__.name)}OrderBy"

    value_dict = {}

    for col in sqla_model.columns:
        col_name = col.name.upper()
        for key, direction in [(col_name + "_ASC", asc), (col_name + "_DESC", desc)]:
            value_dict[key] = EnumValue(value=(col.name, direction))

    return EnumType(result_name, value_dict, description="")
