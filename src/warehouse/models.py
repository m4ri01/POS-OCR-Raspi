from sqlalchemy import Table, Column, Integer, String, MetaData, Text, Date, DateTime
from sqlalchemy.sql import func

metadata = MetaData()

msWarehouse = Table(
    'warehouse',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('product_name', Text, nullable=False),
    Column("expired_date",Date,nullable=False),
    Column("stock",Integer,nullable=False),
    Column("created_at",DateTime(timezone=True),server_default=func.now()),
    Column("updated_at",DateTime(timezone=True),server_default=func.now(),onupdate=func.now())
)