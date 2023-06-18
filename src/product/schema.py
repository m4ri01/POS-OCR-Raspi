from pydantic import BaseModel

class ProductIn(BaseModel):
    product_name: str
    expired: str
    stock: int

class ProductOutItem(BaseModel):
    product_name: str
    stock: int

class ProductOut(BaseModel):
    id: int
    product_name: str
    expired: str
    stock: int