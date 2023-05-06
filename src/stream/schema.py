from pydantic import BaseModel

class Image(BaseModel):
    image_data: str

class ProductIn(BaseModel):
    product_name: str
    expired: str
    stock: int