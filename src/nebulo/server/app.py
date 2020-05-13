from nebulo.config import Config
from nebulo.server.starlette import create_app

APP = create_app(connection=Config.CONNECTION, jwt_identifier=Config.JWT_IDENTIFIER, jwt_secret=Config.JWT_SECRET)
