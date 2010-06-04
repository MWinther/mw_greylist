from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

Base = declarative_base()
class GLEntry(Base):
    __tablename__ = 'greylist'

    client = Column('client', String(15), primary_key=True)
    helo = Column('helo', String(256), primary_key=True)
    sender = Column('sender', String(256), primary_key=True)
    status = Column('status', String(1))
    last_activated = Column('last_activated', DateTime)
    expiry_date = Column('expiry_date', DateTime, index=True)
    count = Column('count', Integer)
    score = Column('score', Integer)

    def __init__(self, client, helo, sender):
        self.client = client
        self.helo = helo
        self.sender = sender

    def __repr__(self):
        return "<GLEntry(client='%s', helo='%s', sender='%s')>" \
            % (self.client, self.helo, self.sender)

    def get_action(self):
        if self.status == 'W':
            if self.expiry_date < datetime.now():
                return 'TEST'
            else:
                return 'ALLOW'
        elif self.status == 'G':
            if self.expiry_date < datetime.now() - timedelta(days=4):
                return 'TEST'
            if self.expiry_date < datetime.now():
                return 'ALLOW'
            else:
                return 'DENY'
        else:
            return 'TEST'
