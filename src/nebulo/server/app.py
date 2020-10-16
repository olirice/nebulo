from nebulo.config import Config
from nebulo.server.starlette import create_app

APP = create_app(
    schema=Config.SCHEMA,
    connection=Config.CONNECTION,
    jwt_identifier=Config.JWT_IDENTIFIER,
    jwt_secret=Config.JWT_SECRET,
    default_role=Config.DEFAULT_ROLE,
)
