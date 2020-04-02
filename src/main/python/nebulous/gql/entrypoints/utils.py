import json

import sqlparse


class Encoder(json.JSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        return str(o)


def print_query(query):
    compiled_query = query.compile(compile_kwargs={"literal_binds": True})
    print(sqlparse.format(str(compiled_query), reindent=True, keyword_case="upper"))
    return


def print_json(result):
    pretty_result = json.dumps(result, indent=2, cls=Encoder)
    print(pretty_result)
