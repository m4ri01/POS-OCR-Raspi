from fastapi import APIRouter, Depends, status
from src.database import db
from src.login.routers import get_current_user
from src.warehouse.schema import WarehouseSchemaIn, WarehouseSchemaOut
from src.warehouse.models import msWarehouse
from src.user.schema import UserSchemaOut
import datetutil.parser as dparser

router = APIRouter(
    tags=["Warehouse"],
    prefix="/warehouse"
)

@router.get("/",response_model=list[WarehouseSchemaOut])
async def get_record():
    query = msWarehouse.select()
    return await db.fetch_all(query)

@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_record(warehouse:WarehouseSchemaIn, current_user:UserSchemaOut=Depends(get_current_user)):
    warehouse.expired_date = dparser.parse(warehouse.expired_date,fuzzy=True)
    query = msWareHouse.insert().values(product_name=warehouse.product_name,expired_date=warehouse.expired_date,stock=warehouse.stock)
    last_record_id = await db.execute(query)
    return {"message":"Record created successfully","id":last_record_id}
