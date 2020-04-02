from typing import List
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from graphene import relay
import graphene

from csql.sqla import SQLDatabase
from csql.user_config import UserConfig


class GQLDatabase:
    def __init__(self, sqldb: SQLDatabase, config: UserConfig):
        self.config = config
        # GQL Tables
        self.gql_models = [self.sqla_model_to_gql_model(x) for x in sqldb.models]
        # GQL Schema
        self.query = self.gql_models_to_query(self.gql_models)
        self.schema = graphene.Schema(query=self.query)

    @staticmethod
    def sqla_model_to_gql_model(sqla_model) -> SQLAlchemyObjectType:
        """Converts a sqlalchemy model into a graphene object"""
        tablename: str = sqla_model.__table__.name
        metaclass = type("Meta", (), {"model": sqla_model, "interfaces": (relay.Node,)})
        return type(tablename, (SQLAlchemyObjectType,), {"Meta": metaclass})

    @staticmethod
    def gql_models_to_query(tables_gql: List[SQLAlchemyObjectType]):
        """Creates a base query object from available graphql objects/tables"""
        relay_attrs = {"interfaces": (relay.Node,)}

        # Create dictionary of attributes for the query object
        entity_attrs = {}
        for table in tables_gql:
            key = f"all_{table._meta.name}"
            # TODO(OR): Take options to configure queryability
            # Option: Allow Sort
            # Option: Allow only index sorts
            # Option: Computed columns
            # Option: Deprecation
            value = SQLAlchemyConnectionField(table, sort=table.sort_argument())
            entity_attrs[key] = value

        all_attrs = {**relay_attrs, **entity_attrs}

        Query = type("Query", (graphene.ObjectType,), all_attrs)

        return Query
