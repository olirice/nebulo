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
<!DOCTYPE html>
<html>
  <head>
    <style>
      body {
        height: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
      }
      #graphiql {
        height: 100vh;
      }
      .jwt-token {
        background: linear-gradient(#f7f7f7, #e2e2e2);
        border-bottom: 1px solid #d0d0d0;
        font-family: system, -apple-system, 'San Francisco', '.SFNSDisplay-Regular', 'Segoe UI', Segoe, 'Segoe WP', 'Helvetica Neue', helvetica, 'Lucida Grande', arial, sans-serif;
        padding: 7px 14px 6px;
        font-size: 14px;
      }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/graphiql/0.10.2/graphiql.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fetch/2.0.3/fetch.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.5.4/react.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.5.4/react-dom.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/graphiql/0.10.2/graphiql.js"></script>
  </head>
  <body>
    <div class="jwt-token">JWT Token <input id="jwt-token" placeholder="JWT Token goes here"></div>
    <div id="graphiql">Loading...</div>
    <script>
    var search = window.location.search;
    var parameters = {};
    document.getElementById('jwt-token').value = localStorage.getItem('graphiql:jwtToken');
    function graphQLFetcher(graphQLParams) {
      const jwtToken = document.getElementById('jwt-token').value;
      let headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      };
      if (jwtToken) {
        localStorage.setItem('graphiql:jwtToken', jwtToken);
        headers = {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': jwtToken ? `Bearer ${jwtToken}` : null
        };
      }
      return fetch({{REQUEST_PATH}}, {
        method: 'post',
        headers,
        body: JSON.stringify(graphQLParams),
        credentials: 'include',
      }).then(function (response) {
        return response.text();
      }).then(function (responseBody) {
        try {
          return JSON.parse(responseBody);
        } catch (error) {
          return responseBody;
        }
      });
    }
    // Render <GraphiQL /> into the body.
    // See the README in the top level of this module to learn more about
    // how you can customize GraphiQL by providing different values or
    // additional child elements.
    ReactDOM.render(
      React.createElement(GraphiQL, {
        fetcher: graphQLFetcher,
      }),
      document.getElementById('graphiql')
    );
    </script>
  </body>
</html>
"""
