import uvicorn
from fastapi import FastAPI
import os,sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from src.user.routers import router as user_router
from src.login.routers import router as login_router
from src.warehouse.routers import router as warehouse_router
from src.stream.routers import router as stream_router
from fastapi.staticfiles import StaticFiles
from src.database import db
app = FastAPI()
app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

app.include_router(router=user_router)
app.include_router(router=login_router)
app.include_router(router=warehouse_router)
app.include_router(router=stream_router)

if __name__ == "__main__":
    uvicorn.run("main:app",port=8181,log_level="info",reload=True)
    