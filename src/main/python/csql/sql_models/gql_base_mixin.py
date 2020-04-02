from __future__ import annotations

from functools import lru_cache

from csql.gql import GraphQLModel


class GQLBaseMixin:
    """SQL Alchemy Mixin to generate graphene graphql models"""

    @classmethod
    @lru_cache(9999)
    def to_graphql(cls) -> GraphQLModel:
        """Converts a sqlalchemy model into a graphene object"""
        return GraphQLModel(cls)

