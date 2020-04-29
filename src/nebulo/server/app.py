import os

from databases import Database
from nebulo.server.starlette import create_app

NEBULO_CONNECTION = os.environ["NEBULO_CONNECTION"]
NEBULO_SCHEMA = os.environ["NEBULO_SCHEMA"]


APP = create_app(Database(NEBULO_CONNECTION, min_size=5, max_size=8))
