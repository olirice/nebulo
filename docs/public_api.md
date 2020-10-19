# Public API

Nebulo is a young project. It exposes a minimal public API to allow the internals to change freely. The public API is defined as anything documented on this page.

## API

```python
from nebulo.server.routes import GRAPHIQL_STATIC_FILES, get_graphql_route, graphiql_route
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
```



