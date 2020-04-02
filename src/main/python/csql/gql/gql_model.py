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


class GQLModel:
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
        print(self.graphene_model._meta.fields.items())
        attrs = {
            k: v
            for k, v in self.graphene_model._meta.fields.items()
            if k != "id" and isinstance(v, graphene.Field)
        }
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
            f"baseCreate{self.table.table_name}",
            (graphene.Mutation,),
            {
                self.table.table_name: graphene.Field(lambda: self.graphene_model, description=""),
                arguments_key: inner_argument_cls,
                # Graphene requires a mutate method is defined
                # on every graphene.Mutation. We will patch it in a sec
                mutate_key: lambda x: "This is a placeholder",
            },
        )
        # Graphene requires using reserved word input....
        def mutate(_, info, input):
            data = input_to_dictionary(input)
            db_session = info.context["session"]

            sql_row = self.table(**data)
            db_session.add(sql_row)
            db_session.commit()
            return create_cls(**{self.table.table_name: sql_row})

        return type(f"{self.table.table_name}Create", (create_cls,), {"mutate": mutate})

    @property
    @lru_cache()
    def update_input_class(self):
        """Returns class defining user input to uniquely identify a database object

        Example:

        class postUpdateInput(graphene.InputObjectType):
            id = graphene.Field(lambda: self.graphene_model)
        """
        return type(
            f"{self.table.table_name}UpdateInput",
            (graphene.InputObjectType, self.mutation_attributes_class),
            {"id": graphene.ID(required=True, description="")},
        )

    @property
    @lru_cache()
    def update_class(self):
        """Returns class that handles updating existing database objects

        Example:

        class Updatepost(graphene.Mutation):
            post = graphene.Field(lambda: self.graphene_model, description='')

            class Arguments:
                input = postCreateInput(required=True)
            
            def mutate(inner_self, info, input: postUpdateInput]):
                data = input_to_dictionary(input)
                db_session = info.context['session']
                # lookup by id
                existing_row = db_session.query(self.table).filter_by(id=date['id'])
                existing_row.update(data)
                db_session.commit()
                db_session.refresh(existing_row)
                return Updatepost(post=existing_row)
        """
        arguments_key = "Arguments"
        mutate_key = "mutate"
        inner_argument_cls = type(
            arguments_key, (), {"input": self.update_input_class(required=True)}
        )

        update_cls = type(
            f"baseUpdate{self.table.table_name}",
            (graphene.Mutation,),
            {
                self.table.table_name: graphene.Field(lambda: self.graphene_model, description=""),
                arguments_key: inner_argument_cls,
                # Graphene requires a mutate method is defined
                # on every graphene.Mutation. We will patch it in a sec
                mutate_key: lambda x: "This is a placeholder",
            },
        )

        # Graphene requires using reserved word input....
        def mutate(_, info, input):
            data = input_to_dictionary(input)
            db_session = info.context["session"]

            # TODO(OR): More assuming that the id field for the table is name "id"
            existing_row = db_session.query(self.table).filter_by(id=data["id"])  # .one()
            existing_row.update(data)
            db_session.commit()
            existing_row = db_session.query(self.table).filter_by(id=data["id"]).one()
            return update_cls(**{self.table.table_name: existing_row})

        return type(f"{self.table.table_name}Update", (update_cls,), {"mutate": mutate})


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
