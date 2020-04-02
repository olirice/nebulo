from __future__ import annotations

from functools import lru_cache

from csql.gql.gql_model import reflection_factory


class GQLBaseMixin:
    """SQL Alchemy Mixin to generate graphene graphql models"""

    @classmethod
    @lru_cache()
    def to_graphql(cls) -> GQLModel:
        """Converts a sqlalchemy model into a graphene object"""
        return reflection_factory(cls)

