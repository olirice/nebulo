import os
from functools import lru_cache

from databases import Database
from nebulo.server.starlette import create_app


@lru_cache()
def get_env(key, default=None):
    return os.environ.get(key, default)


NEBULO_JWT_IDENTIFIER = get_env("NEBULO_JWT_TOKEN_IDENTIFIER")
NEBULO_JWT_SECRET = get_env("NEBULO_JWT_SECRET")
NEBULO_CONNECTION = get_env("NEBULO_CONNECTION")
NEBULO_SCHEMA = get_env("NEBULO_SCHEMA")


APP = create_app(
    database=Database(NEBULO_CONNECTION, min_size=5, max_size=8),
    jwt_identifier=NEBULO_JWT_IDENTIFIER,
    jwt_secret=NEBULO_JWT_SECRET,
)
