from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, List, Type

import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType
from graphene_sqlalchemy.types import ORMField
from graphql_relay import from_global_id

from csql.sql.utils import cachedclassproperty, classproperty

if TYPE_CHECKING:
    from csql.sql.sql_database import SQLDatabase
    from csql.user_config import UserConfig
    from csql.sql.table_base import TableBase


def reflection_factory(table: TableBase) -> ReflectedGQLModel:
    tablename: str = table.table_name
    metaclass = type("Meta", (), {"model": table, "interfaces": (relay.Node,)})

    # Alter Types, Add Descriptions, Change Required flag,
    extra_attrs = {}
    if hasattr(table, "team_name"):
        extra_attrs["team_name"] = ORMField(description="name o da thing")

    return type(tablename, (ReflectedGQLModel,), dict(**{"Meta": metaclass}, **extra_attrs))


class ReflectedGQLModel(SQLAlchemyObjectType):
    class Meta:
        abstract = True

    @cachedclassproperty
    def sql_table_name(cls) -> str:
        return cls._meta.model.table_name

    @cachedclassproperty
    def _mutation_attributes_class(cls) -> Type:
        """Returns a class defining the attributes
        that the user can provide for creates and updates

        Example

        class postAttributes:
            title = graphene.String()
            body = graphene.String() 
        """
        # Class name is not used externally
        class_name = cls.sql_table_name + "Attributes"
        # Copy fields from the graphene model excluding 'id' which can not be user defined
        attrs = {
            k: v for k, v in cls._meta.fields.items() if k != "id" and isinstance(v, graphene.Field)
        }
        return type(class_name, (), attrs)

    @cachedclassproperty
    def _creation_input_class(cls) -> Type:
        """Returns a class defining what a user can send
        when creating a new instance of this model

        Example:

        class postCreateInput(graphene.InputObjectType, postAttributes):
            pass
        """
        class_name = cls.sql_table_name + "CreateInput"
        return type(class_name, (graphene.InputObjectType, cls._mutation_attributes_class), {})

    @cachedclassproperty
    def creation_class(cls) -> Type:
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
            arguments_key, (), {"input": cls._creation_input_class(required=True)}
        )

        create_cls = type(
            f"baseCreate{cls.sql_table_name}",
            (graphene.Mutation,),
            {
                cls.sql_table_name: graphene.Field(lambda: cls, description=""),
                arguments_key: inner_argument_cls,
                # Graphene requires a mutate method is defined
                # on every graphene.Mutation. We will patch it in a sec
                mutate_key: lambda x: "This is a placeholder",
            },
        )
        # Graphene requires using reserved word input....
        def mutate(_, info, input):
            data = cls.input_to_dictionary(input)
            db_session = info.context["session"]

            sql_row = cls._meta.model(**data)
            db_session.add(sql_row)
            db_session.commit()
            return create_cls(**{cls.sql_table_name: sql_row})

        return type(f"{cls.sql_table_name}Create", (create_cls,), {"mutate": mutate})

    @cachedclassproperty
    def _update_input_class(cls):
        """Returns class defining user input to uniquely identify a database object

        Example:

        class postUpdateInput(graphene.InputObjectType):
            id = graphene.Field(lambda: self.graphene_model)
        """
        return type(
            f"{cls.sql_table_name}UpdateInput",
            (graphene.InputObjectType, cls._mutation_attributes_class),
            {"id": graphene.ID(required=True, description="GraphQL relay identifier")},
        )

    @cachedclassproperty
    def update_class(cls):
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
            arguments_key, (), {"input": cls._update_input_class(required=True)}
        )

        update_cls = type(
            f"baseUpdate{cls.sql_table_name}",
            (graphene.Mutation,),
            {
                cls.sql_table_name: graphene.Field(lambda: cls, description=""),
                arguments_key: inner_argument_cls,
                # Graphene requires a mutate method is defined
                # on every graphene.Mutation. We will patch it in a sec
                mutate_key: lambda x: "This is a placeholder",
            },
        )

        # Graphene requires using reserved word input....
        def mutate(_, info, input):
            data = cls.input_to_dictionary(input)
            db_session = info.context["session"]

            # TODO(OR): More assuming that the id field for the table is name "id"
            existing_row = db_session.query(cls._meta.model).filter_by(id=data["id"]).one()
            existing_row.update(**data)
            db_session.commit()
            db_session.refresh(existing_row)
            return update_cls(**{cls.sql_table_name: existing_row})

        return type(f"{cls.sql_table_name}Update", (update_cls,), {"mutate": mutate})

    @staticmethod
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
