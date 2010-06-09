from mw_greylist.settings import Settings
from mw_greylist.glcandidate import GLCandidate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

settings = Settings()
engine = create_engine(settings.connection_url)
Session = sessionmaker(bind=engine)
session = Session()
candidate = GLCandidate(settings, session)
candidate.read_headers()
print candidate.perform_action()
session.commit()
