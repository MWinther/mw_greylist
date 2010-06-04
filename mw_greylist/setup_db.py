from mw_greylist.glentry import GLEntry
from sqlalchemy import create_engine
from mw_greylist.settings import Settings

settings = Settings()
engine = create_engine(settings.connection_url)
GLEntry.metadata.create_all(engine)

