from pydantic import BaseModel
import datetime

class WarehouseSchemaIn(BaseModel):
    product_name: str
    expired_date: str
    stock: int

class WarehouseSchemaOut(BaseModel):
    id: int
    product_name: str
    expired_date: datetime.date
    stock: int

class StockSchemaIn(BaseModel):
    stock_delta: int
    is_add: bool