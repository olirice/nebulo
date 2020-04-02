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
    from .sql_models.table_base import TableBase


class GraphQLModel:
    def __init__(self, table: TableBase):
        self.table = table

    @property
    @lru_cache()
    def graphene_model(self) -> SQLAlchemyObjectType:
        tablename: str = self.table.table_name
        metaclass = type("Meta", (), {"model": self.table, "interfaces": (relay.Node,)})
        return type(tablename, (SQLAlchemyObjectType,), {"Meta": metaclass})

    @property
    @lru_cache()
    def mutation_attributes_class(self) -> Type:
        """Returns a class defining the attributes
        that the user can provide for creates and updates

        Example

        class postAttributes:
            title = graphene.String()
            body = graphene.String() 
        """
        # Class name is not used externally
        class_name = self.table.table_name + "Attributes"
        # Copy fields from the graphene model excluding 'id' which can not be user defined
        # TODO(OR): Do any other fields need to be excluded?
        attrs = {k: v for k, v in self.graphene_model._meta.fields.items() if k != "id"}
        return type(class_name, (), attrs)

    @property
    @lru_cache()
    def creation_input_class(self) -> Type:
        """Returns a class defining what a user can send
        when creating a new instance of this model

        Example:

        class postCreateInput(graphene.InputObjectType, postAttributes):
            pass
        """
        class_name = self.table.table_name + "CreateInput"
        return type(class_name, (graphene.InputObjectType, self.mutation_attributes_class), {})

    @property
    @lru_cache()
    def creation_class(self) -> Type:
        """Returns a class that handles creating new objects

        Example:

        class createPost(graphene.Mutation):
            post = graphene.Field(lambda: self.graphene_model, description='')

            class Arguments:
                input = postCreateInput(required=True)
            
            def mutate(inner_self, info, input: postCreateInput]):
                data = input_to_dictionary(input)
                # sqlalchemy model
                sqla_row = self.table(**data)
                db_session = info.context['session']
                db_session.add(sqla_row)
                db_session.commit(sqla_row)
                return createPost(post=sqla_row)
        """
        arguments_key = "Arguments"
        mutate_key = "mutate"
        inner_argument_cls = type(
            arguments_key, (), {"input": self.creation_input_class(required=True)}
        )

        create_cls = type(
            f"create{self.table.table_name}",
            (graphene.Mutation,),
            {
                self.table.table_name: graphene.Field(lambda: self.graphene_model, description=""),
                arguments_key: inner_argument_cls,
                # Graphene requires a mutate method is defined
                # on every graphene.Mutation. We will patch it in a sec
                mutate_key: lambda x: "This is a placeholder",
            },
        )

        class Patched(create_cls):
            # Graphene requires using reserved word input....
            def mutate(_, info, input):
                data = input_to_dictionary(input)
                db_session = info.context["session"]

                sql_row = self.table(**data)
                db_session.add(sql_row)
                db_session.commit()
                return create_cls(**{self.table.table_name: sql_row})

        return Patched


def input_to_dictionary(graphene_input):
    """Converts a graphene input to a sqlalchemy friendly dict"""
    as_dict = {}
    for key in graphene_input:
        # Convert relay id to sql id
        # TODO(OR): Lookup the field type and confirm its a relay id
        if key[-2:] == "id":
            graphene_input[key] = from_global_id(graphene_input[key])[1]
        as_dict[key] = graphene_input[key]
    return as_dict


class GQLDatabase:
    def __init__(self, sqldb: SQLDatabase, config: UserConfig):
        self.config = config
        # GQL Tables
        self.gql_models = [x.to_graphql().graphene_model for x in sqldb.models]
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
            # List All
            key = f"all_{table._meta.name}"
            value = SQLAlchemyConnectionField(table, sort=table.sort_argument())
            entity_attrs[key] = value

            # Single Entity by Relay ID
            key = f"{table._meta.name}"
            value = graphene.relay.Node.Field(table)
            entity_attrs[key] = value

        all_attrs = {**relay_attrs, **entity_attrs}

        Query = type("Query", (graphene.ObjectType,), all_attrs)

        return Query
