from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, List, Type

import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType
from graphene_sqlalchemy.types import ORMField
from graphql_relay import from_global_id

from graphene_sqlalchemy.converter import convert_sqlalchemy_type
from graphene_sqlalchemy.registry import get_global_registry
from csql.sql.utils import cachedclassproperty, classproperty
from sqlalchemy import Column
from sqlalchemy import select, func, literal, type_coerce

if TYPE_CHECKING:
    from csql.sql.sql_database import SQLDatabase
    from csql.user_config import UserConfig
    from csql.sql.table_base import TableBase
    from csql.sql.reflection.functions import SQLFunction


def sqla_type_to_graphene_type(_type, name: str):
    gql_registry = get_global_registry()
    return convert_sqlalchemy_type(_type, Column(name, None), gql_registry)


def function_reflection_factory(sql_function: SQLFunction) -> ReflectedGQLFunction:
    """Reflect SQLFunction into a GQL object that has methods that produce
    its mutation objects"""

    object_name = sql_function.func_name + "FuncModel"
    extra_attrs = {"sql_function": sql_function}
    output = type(object_name, (ReflectedGQLFunction,), extra_attrs)
    return output


class ReflectedGQLFunction:
    """
    Generate graphene models required for calling
    a sql function via a mutation

    Note:
        In the example below, "AuthenticationResult" is the object we're currently in
        the <>Input, and  Call<> class will be accessible as method on the <>Result
        class


    class AuthenticateResult(graphene.ObjectType):
        result = graphene.JSONString()


    class AuthenticateInput(graphene.InputObjectType):
        username = graphene.String(description='an account\'s username')
        password = graphene.String(description="an account\'s password")

    class CallAuthenticate(graphene.Mutation):
        "Mutation to create a person."
        authenticate_res = graphene.Field(lambda: AuthenticateResult, description="mut result")

        class Arguments:
            input = AuthenticateInput(required=True)

        def mutate(self, info, input):
            data = ReflectedGQLModel.input_to_dictionary(input)
            db_session = info.context["session"]
            sql = select([func.authenticate(*data.values())])
            py_result = db_session.execute(sql).first()[0]
            return CallAuthenticate(authenticate_res={'res': py_result}) #str(py_result))

    # The mutation class's creation is delegated to GQLDatabase
    class Mutate(graphene.ObjectType):
        interfaces = relay.Node
        authenticate = CallAuthenticate.Field()

    """

    @cachedclassproperty
    def sql_function_name(cls) -> str:
        return cls.sql_function.func_name

    @cachedclassproperty
    def result_class(cls) -> graphene.ObjectType:
        object_name = cls.sql_function.func_name + "Result1"
        gql_return_type = sqla_type_to_graphene_type(
            cls.sql_function.return_type, "result"
        )
        extra_attrs = {"result": gql_return_type()}
        return type(object_name, (graphene.ObjectType,), extra_attrs)

    @cachedclassproperty
    def _mutation_input_class(cls) -> Type:
        """Returns a class defining the attributes
        that the user can provide for creates and updates

        Example

        class AuthenticateInput(graphene.InputObjectType):
            username = graphene.String(description='an account\'s username')
            password = graphene.String(description="an account\'s password")

        """
        # Class name is not used externally
        class_name = cls.sql_function_name + "Input"
        # Copy fields from the graphene model excluding 'id' which can not be user defined
        attrs = {}
        for arg_type, arg_name in zip(
            cls.sql_function.arg_types, cls.sql_function.arg_names
        ):
            attrs[arg_name] = sqla_type_to_graphene_type(arg_type, arg_name)()
        return type(class_name, (graphene.InputObjectType,), attrs)

    @cachedclassproperty
    def call_class(cls) -> Type:
        """Returns a graphene mutation object that can be used to call the sql function"""

        class_name = "Call_" + cls.sql_function_name

        arguments_key = "Arguments"
        argument_class_name = cls.sql_function_name + "_result"
        argument_attrs = {"input": cls._mutation_input_class(required=True)}
        inner_argument_cls = type(arguments_key, (), argument_attrs)

        mutate_key = "mutate"

        call_base_cls = type(
            f"baseCall{cls.sql_function_name}",
            (graphene.Mutation,),
            {
                cls.sql_function_name
                + "_result": graphene.Field(lambda: cls.result_class, description=""),
                arguments_key: inner_argument_cls,
                # Graphene requires a mutate method is defined
                # on every graphene.Mutation. We will patch it in a sec
                mutate_key: lambda x: "This is a placeholder",
            },
        )

        def mutate(self, info, input):
            data = cls.input_to_dictionary(input)
            print(data)
            db_session = info.context["session"]
            sql = select([getattr(func, cls.sql_function_name)(*data.values())])
            py_result = db_session.execute(sql).first()[0]
            print(py_result)
            return call_base_cls(**{cls.sql_function_name + "_result": {'result': py_result}})

        return type(
            f"Call{cls.sql_function_name}", (call_base_cls,), {"mutate": mutate}
        )

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
