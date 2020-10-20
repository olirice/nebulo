import os
from functools import lru_cache
from pathlib import Path

from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

GRAPHIQL_STATIC_PATH = Path(os.path.abspath(__file__)).parent.parent.parent.resolve() / "static"

GRAPHIQL_STATIC_FILES = StaticFiles(directory=GRAPHIQL_STATIC_PATH)


def get_graphiql_route(graphiql_path: str = "/graphiql", graphql_path: str = "/", name="graphiql") -> Mount:
    """Return mountable routes serving GraphiQL interactive API explorer

    **Parameters**

    * **graphiql_path**: _str_ = URL path to GraphiQL html page
    * **graphql_path**: _str_ =  URL path to the GraphQL route
    * **name**: _str_ =  Name for the mount
    """

    async def graphiql_endpoint(_: Request) -> HTMLResponse:
        """Return the HTMLResponse for GraphiQL GraphQL explorer configured to hit the correct endpoint"""
        html_text = build_graphiql_html(graphiql_path, graphql_path)
        return HTMLResponse(html_text)

    graphiql_html_route = Route("/", graphiql_endpoint, methods=["GET"])
    graphiql_statics = Mount("/static", GRAPHIQL_STATIC_FILES, name="static")

    return Mount(graphiql_path, routes=[graphiql_html_route, graphiql_statics], name=name)


@lru_cache()
def build_graphiql_html(
    graphiql_route_path: str,
    graphql_route_path: str,
) -> str:
    """Return the raw HTML for GraphiQL GraphQL explorer"""

    text = GRAPHIQL.replace("{{GRAPHIQL_PATH}}", graphiql_route_path)
    text = text.replace("{{REQUEST_PATH}}", f'"{graphql_route_path}"')
    return text


GRAPHIQL = """
<html>
  <head>
    <title>Nebulo GraphiQL</title>
    <link href="{{GRAPHIQL_PATH}}/static/graphiql.min.css" rel="stylesheet" />
  </head>
  <body style="margin: 0;">
    <div id="graphiql" style="height: 100vh;"></div>

    <script
      crossorigin
      src="https://unpkg.com/react/umd/react.production.min.js"
    ></script>
    <script
      crossorigin
      src="https://unpkg.com/react-dom/umd/react-dom.production.min.js"
    ></script>
    <script
      crossorigin
      src="{{GRAPHIQL_PATH}}/static/graphiql.min.js"
    ></script>

    <script>

        let graphQLFetcher = (graphQLParams, opts = { headers: {} }) => {
          return fetch(window.location.origin + {{REQUEST_PATH}}, {
            method: 'post',
            headers: Object.assign({ 'Content-Type': 'application/json', 'User-Agent': 'GraphiQL' }, opts.headers),
            body: JSON.stringify(graphQLParams),
          }).then(response => response.json());
        }

        ReactDOM.render(
          React.createElement(GraphiQL, {
            fetcher: graphQLFetcher,
            headerEditorEnabled: true,
          }),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
"""
