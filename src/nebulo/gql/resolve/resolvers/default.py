import typing

from graphql.pyutils import Path
from nebulo.gql.alias import ResolveInfo


def default_resolver(_, info: ResolveInfo, **kwargs) -> typing.Any:
    """Expects the final, complete result to exist in context['result']
    and uses the current path to retrieve and return the expected result for
    the current location in the query

    Why TF would you do this?
    - To avoid writing a custom executor
    - To keep the resolver tree extensible for end users
    - To keep everything as default as possible
    """
    path: Path = info.path
    context = info.context
    final_result = context["result"]

    remain_result = final_result
    for elem in path.as_list():
        remain_result = remain_result[elem]

    return remain_result
