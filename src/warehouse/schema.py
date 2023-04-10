from pydantic import BaseModel

class WarehouseSchemaIn(BaseModel):
    product_name: str
    expired_date: str
    stock: int

class WarehouseSchemaOut(BaseModel):
    id: int
    product_name: str
    expired_date: str
    stock: int