from fastapi import APIRouter, Depends,status
from src.database import db
from src.login.models import login
from src.user.schema import UserSchemaIn
from passlib.hash import bcrypt

router = APIRouter(
    tags=["User"],
    prefix="/user"
)

@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_user(user:UserSchemaIn):
    query = login.insert().values(username=user.username,password=bcrypt.hash(user.password))
    await db.execute(query)
    return {"message":"User created successfully"}