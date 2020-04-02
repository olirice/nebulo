from __future__ import annotations

from functools import lru_cache

from csql.gql.gql_model import ReflectedGQLModel, model_reflection_factory


class GQLBaseMixin:
    """SQL Alchemy Mixin to generate graphene graphql models"""

    @classmethod
    @lru_cache()
    def to_graphql(cls) -> ReflectedGQLModel:
        """Converts a sqlalchemy model into a graphene object"""
        return model_reflection_factory(cls)
