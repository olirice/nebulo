from sqlalchemy.ext.automap import automap_base
from .meta import Meta


Base = automap_base(metadata=Meta)

