from sqlalchemy import String,Integer,Column,Table,MetaData,DateTime
from sqlalchemy.sql import func

metadata = MetaData()
msProduct = Table(
    'product',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('product_name', String(255), nullable=False),
    Column('expired', String(255), nullable=False),
    Column('stock',Integer, nullable=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    Column('updated_at', DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
)