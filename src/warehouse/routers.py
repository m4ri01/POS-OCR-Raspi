from fastapi import APIRouter, Depends, status
from src.database import db
from src.login.routers import get_current_user
from src.warehouse.schema import WarehouseSchemaIn, WarehouseSchemaOut, StockSchemaIn
from src.warehouse.models import msWarehouse
from src.user.schema import UserSchemaOut
import dateutil.parser as dparser
from src.exceptions import no_content, no_stock

router = APIRouter(
    tags=["Warehouse"],
    prefix="/warehouse"
)

@router.get("/",response_model=list[WarehouseSchemaOut])
async def get_all_record(current_user:UserSchemaOut=Depends(get_current_user)):
    query = msWarehouse.select()
    return await db.fetch_all(query)

@router.get("/{id}",response_model=WarehouseSchemaOut)
async def get_record(id:int,current_user:UserSchemaOut=Depends(get_current_user)):
    query = msWarehouse.select().where(msWarehouse.c.id == id)
    return await db.fetch_one(query)

@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_record(warehouse:WarehouseSchemaIn, current_user:UserSchemaOut=Depends(get_current_user)):
    warehouse.expired_date = dparser.parse(warehouse.expired_date,fuzzy=True,dayfirst=True)
    query = msWarehouse.insert().values(product_name=warehouse.product_name,expired_date=warehouse.expired_date,stock=warehouse.stock)
    last_record_id = await db.execute(query)
    return {"message":"Record created successfully","id":last_record_id}

@router.put("/{id}",status_code=status.HTTP_202_ACCEPTED)
async def update_record(id:int,warehouse:WarehouseSchemaIn,current_user:UserSchemaOut=Depends(get_current_user)):
    warehouse.expired_date = dparser.parse(warehouse.expired_date,fuzzy=True,dayfirst=True)
    query = msWarehouse.update().where(msWarehouse.c.id == id).values(product_name=warehouse.product_name,expired_date=warehouse.expired_date,stock=warehouse.stock)
    await db.execute(query)
    return {"message":"Record updated successfully"}

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(id:int,current_user:UserSchemaOut=Depends(get_current_user)):
    query = msWarehouse.delete().where(msWarehouse.c.id == id)
    await db.execute(query)
    return {"message":"Record deleted successfully"}

@router.post("/stock/{id}",status_code=status.HTTP_202_ACCEPTED,response_model=WarehouseSchemaOut)
async def update_stock(id:int,stock_update:StockSchemaIn,current_user:UserSchemaOut=Depends(get_current_user)):
    query = msWarehouse.select().where(msWarehouse.c.id == id)
    result = await db.fetch_one(query)
    if not result:
        raise no_content
    if stock_update.is_add:
        query = msWarehouse.update().where(msWarehouse.c.id == id).values(stock=result.stock + stock_update.stock_delta)
    else:
        if result.stock < stock_update.stock_delta:
            raise no_stock
        else:
            query = msWarehouse.update().where(msWarehouse.c.id == id).values(stock=result.stock - stock_update.stock_delta)
    await db.execute(query)
    query = msWarehouse.select().where(msWarehouse.c.id == id)
    return await db.fetch_one(query)

    