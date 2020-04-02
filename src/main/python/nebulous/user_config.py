class UserConfig:
    def __init__(
        self,
        connection: str,
        schema: str,
        echo_queries: bool,
        graphql_route: str,
        graphiql: bool,
        port: int,
        demo: bool,
    ):
        self.connection = connection
        self.schema = schema
        self.echo_queries = echo_queries
        self.graphiql = graphiql
        self.graphql_route = graphql_route
        self.port = port
        self.demo = demo

    def __str__(self):
        return f"UserConfig(**{self.__dict__})"
