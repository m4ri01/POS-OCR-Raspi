from pydantic import BaseModel

class UserSchemaIn(BaseModel):
    username: str
    password: str

class UserSchemaOut(BaseModel):
    id: int
    username: str

class LoginSchema(BaseModel):
    username: str
    password: str