import uvicorn
from databases import Database
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.server.exception import http_exception
from nebulo.server.routes import get_graphiql_route, get_graphql_route
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, create_engine
from sqlalchemy import text as sql_text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from starlette.applications import Starlette
from starlette.exceptions import HTTPException

# Config
DATABASE_URI = "postgresql://app_user:app_password@localhost:5522/nebulo_example"


#####################
# SQLAlchemy Models #
#####################

Base = declarative_base()


class Author(Base):
    __tablename__ = "author"

    id = Column(Integer, primary_key=True, comment="@exclude insert, update")
    name = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=sql_text("now()"),
        comment="@exclude insert, update",
    )

    books = relationship("Book", uselist=True)


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, primary_key=True, comment="@exclude insert, update")
    title = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("author.id"), nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        default=sql_text("now()"),
        comment="@exclude insert, update",
    )

    author = relationship("Author")


#################################
# Starlette Application Factory #
#################################


def create_app(connection_str, sqla_models) -> Starlette:
    """Create the Starlette app"""

    database = Database(connection_str)

    # Convert sqla models to graphql schema
    gql_schema = sqla_models_to_graphql_schema(sqla_models)

    # Build the Starlette GraphQL Route
    graphql_route = get_graphql_route(gql_schema=gql_schema, database=database)

    # Build the Starlette GraphiQL Route and StaticFiles
    graphiql_route = get_graphiql_route()

    # Instantiate the Starlette app
    _app = Starlette(
        routes=[graphql_route, graphiql_route],
        exception_handlers={HTTPException: http_exception},
        on_startup=[database.connect],
        on_shutdown=[database.disconnect],
    )

    return _app


# Instantiate the app
APP = create_app(connection_str=DATABASE_URI, sqla_models=[Author, Book])


if __name__ == "__main__":

    # Create Tables
    with create_engine(DATABASE_URI).connect() as sqla_engine:
        Base.metadata.create_all(bind=sqla_engine)

    uvicorn.run(
        "app:APP",
        host="0.0.0.0",
        port=5084,
        log_level="info",
        reload=False,
    )
