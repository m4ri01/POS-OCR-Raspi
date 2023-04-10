from fastapi import APIRouter, Depends
from src.exceptions import invalid_username_or_password, invalid_credential
from src.config import SECRET_KEY, ALGORITHM
from passlib.hash import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.database import db
from src.models import login
from src.login.schema import TokenData

router = APIRouter(
    tags=["Login"]
)

oauth2scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token:str=Depends(oauth2scheme)):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str = payload.get("sub")
        if username is None:
            raise invalid_credential
        token_data = TokenData(username=username)
    except JWTError:
        raise invalid_credential

def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login")
async def login(userLogin:OAuth2PasswordRequestForm=Depends()):
    query = login.select().where(login.c.username == userLogin.username)
    result = await db.fetch_one(query)
    if not result:
        raise invalid_username_or_password
    if not bcrypt.verify(userLogin.password,result.password):
        raise invalid_username_or_password
    access_token = create_access_token(data={"sub":userLogin.username})
    return {"access_token":access_token,"token_type":"bearer"}
