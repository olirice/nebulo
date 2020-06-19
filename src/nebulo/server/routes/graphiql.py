from functools import lru_cache

from starlette.requests import Request
from starlette.responses import HTMLResponse


async def graphiql_endpoint(request: Request, graphql_url_path: str = '"/"') -> HTMLResponse:
    """Return the HTMLResponse for GraphiQL GraphQL explorer configured to hit the correct endpoint"""

    html_text = build_graphiql_html(graphql_url_path)
    return HTMLResponse(html_text)


@lru_cache()
def build_graphiql_html(url_path: str) -> str:
    """Return the raw HTML for GraphiQL GraphQL explorer"""

    text = GRAPHIQL.replace("{{REQUEST_PATH}}", url_path)
    return text


GRAPHIQL = """
<html>
  <head>
    <title>Nebulo GraphiQL</title>
    <link href="static/graphiql.min.css" rel="stylesheet" />
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
      src="static/graphiql.min.js"
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
