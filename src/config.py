import dotenv
import os

dotenv.load_dotenv()
SQL_URL = os.getenv("SQL_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")