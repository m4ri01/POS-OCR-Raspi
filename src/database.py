from sqlalchemy import create_engine
from src.config import SQL_URL
from databases import Database

db = Database(SQL_URL)
engine = create_engine(SQL_URL)
