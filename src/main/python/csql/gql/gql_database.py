from __future__ import annotations

from typing import List, TYPE_CHECKING, Type
from functools import lru_cache
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from graphene import relay
from graphql_relay import from_global_id
import graphene

if TYPE_CHECKING:
    from csql.sql_models.sqla import SQLDatabase
    from csql.user_config import UserConfig
    from csql.sql.table_base import TableBase
    from csql.gql.gql_model import GQLModel


class GQLDatabase:
    def __init__(self, sqldb: SQLDatabase, config: UserConfig):
        self.config = config
        # GQL Tables
        self.gql_models: List[GQLModel] = [x.to_graphql() for x in sqldb.models]
        # GQL Schema
        self.schema = graphene.Schema(query=self.query_class, mutation=self.mutation_class)

    @property
    @lru_cache()
    def query_class(self):
        """Creates a base query object from available graphql objects/tables"""
        relay_attrs = {"interfaces": (relay.Node,)}

        # Create dictionary of attributes for the query object
        entity_attrs = {}
        for table in self.gql_models:
            graphene_table = table.graphene_model
            # List All
            key = f"all_{graphene_table._meta.name}"
            value = SQLAlchemyConnectionField(graphene_table, sort=graphene_table.sort_argument())
            entity_attrs[key] = value

            # Single Entity by Relay ID
            key = f"{graphene_table._meta.name}"
            value = graphene.relay.Node.Field(graphene_table)
            entity_attrs[key] = value

        all_attrs = {**relay_attrs, **entity_attrs}

        Query = type("Query", (graphene.ObjectType,), all_attrs)
        return Query

    @property
    @lru_cache()
    def mutation_class(self):
        """Creates a base mutation object from available graphql objects/tables"""
        relay_attrs = {"interfaces": (relay.Node,)}

        # Create dictionary of attributes for the query object
        entity_attrs = {}
        for table in self.gql_models:
            graphene_table = table.graphene_model
            # Creation method
            key = f"create_{graphene_table._meta.name}"
            value = table.creation_class.Field()
            entity_attrs[key] = value

            # Update existing entity by Relay ID
            key = f"update_{graphene_table._meta.name}"
            value = table.update_class.Field()
            entity_attrs[key] = value

        all_attrs = {**relay_attrs, **entity_attrs}

        Mutation = type("Mutation", (graphene.ObjectType,), all_attrs)
        return Mutation

