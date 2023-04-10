from sqlalchemy import String,Integer,Column,Table,MetaData,DateTime
from sqlalchemy.sql import func

metadata = MetaData()
login = Table(
    'login',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(255), nullable=False),
    Column('password', String(255), nullable=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    Column('updated_at', DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
)