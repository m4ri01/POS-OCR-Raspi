from fastapi import APIRouter,Request,File,UploadFile, status, Body, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from src.product.schema import ProductIn,ProductOut, ProductOutItem
from src.product.services import OCR
from fastapi.templating import Jinja2Templates
from src.product.models import msProduct
from pyfa_converter import FormDepends, PyFaDepends
from src.database import db
from src.exceptions import no_content
import logging
from rpi_lcd import LCD
import numpy as np
import logging
import cv2
import threading
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
# A flag to indicate whether the camera should be running
camera_running = None
video = None
message = []
lcd = LCD() 
#set GPIO Pins
GPIO_TRIGGER = 15
GPIO_ECHO = 14
GPIO_BUZZER =  17
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(GPIO_BUZZER,GPIO.OUT)
logging.basicConfig(level=logging.DEBUG)
router = APIRouter(
    tags=["Product Service"],
    prefix="/product"
)
templates = Jinja2Templates(directory="src/static")
def distance():
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance

def buzzer():
    GPIO.output(GPIO_BUZZER,True)
    time.sleep(0.1)
    GPIO.output(GPIO_BUZZER,False)
    time.sleep(0.2)
    GPIO.output(GPIO_BUZZER,True)
    time.sleep(0.1)
    GPIO.output(GPIO_BUZZER,False)
    time.sleep(0.2)

def gen():
    """Video streaming generator function."""
    global camera_running
    global video
    while camera_running.is_set():
        success, image = video.read()
        if not success:
            break
        dist = distance()/100
        if dist >= 0.2:
            cv2.putText(image,'jarak: {}m'.format(np.round(dist,2)),(5,20),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),1,cv2.LINE_AA)
        else:
            cv2.putText(image,'jarak: {}m'.format(np.round(dist,2)),(5,20),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),1,cv2.LINE_AA)
        ret, jpeg = cv2.imencode('.jpg', image)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    print("stopped")

@router.get("/", response_class=HTMLResponse,response_model=ProductOut)
async def read_item(request: Request):
    global message
    query = msProduct.select()
    result = await db.fetch_all(query)
    results = []
    for r in result:
        r_dict = r._asdict()
        # logging.debug(r_dict)
        try:
            expired_date = r.expired
            expired_date_time = datetime.strptime(expired_date, '%d%m%y')
            now = datetime.now()
            time_left = expired_date_time - now
            if time_left > timedelta(days=90):
                r_dict['status'] = 3
            elif time_left > timedelta(days=30):
                r_dict['status'] = 2
            else:
                r_dict['status'] = 1
        except:
            r_dict['status'] = 1
        results.append(r_dict)
    return templates.TemplateResponse("product/list_product.html", {"request":request,"result": results,"message":message})

@router.get('/edit/{id}',response_class=HTMLResponse)
async def edit_item_view(request: Request,id:int):
    query = msProduct.select().where(msProduct.c.id == id)
    result = await db.fetch_one(query)
    return templates.TemplateResponse("product/edit_product.html",{"request":request,"result":result})

@router.post('/edit/{id}',response_class=HTMLResponse)
async def edit_item(request: Request,id:int,product = PyFaDepends(model=ProductIn,_type=Form)):
    query = msProduct.update().where(msProduct.c.id == id).values(product_name=product.product_name,expired=product.expired,stock=product.stock)
    await db.execute(query)
    response = RedirectResponse(request.url_for("read_item"))
    response.status_code = status.HTTP_303_SEE_OTHER
    return response

@router.get("/insert",response_class=HTMLResponse)
async def insert_item_view(request: Request):
    global video
    global camera_running
    if video is None:
        camera_running = threading.Event()
        camera_running.set()
        video = cv2.VideoCapture(0)
    return templates.TemplateResponse("product/input_product.html",{"request":request})

@router.post("/insert")
async def insert_item(request: Request,product = PyFaDepends(model=ProductIn,_type=Form)):
    global camera_running
    global video
    global message
    message = []
    camera_running.clear()
    video.release()
    video = None
    try:
        expired_date_time = datetime.strptime(product.expired, '%d%m%y')
        query = msProduct.insert().values(product_name=product.product_name,expired=product.expired,stock=product.stock)
        await db.execute(query)
        buzzer()
        lcd.text(productParam.product_name, 1)
        lcd.text(productParam.expired, 2)
    except :
        message.append({"msg": "Wrong Date Format, the format should (DDMMYY)"})
    response = RedirectResponse(request.url_for("read_item"))
    response.status_code = status.HTTP_303_SEE_OTHER
    return response

@router.get("/out")
async def out_item_view(request: Request,response_class=HTMLResponse):
    global video
    global camera_running
    if video is None:
        camera_running = threading.Event()
        camera_running.set()
        video = cv2.VideoCapture(0)
    return templates.TemplateResponse("product/out_product.html",{"request":request})

@router.post("/out")
async def out_item(request: Request,product = PyFaDepends(model=ProductOutItem,_type=Form)):
    global message
    message =[]
    query = msProduct.select().where(msProduct.c.product_name == product.product_name)
    result = await db.fetch_one(query)
    logging.debug(result)
    if not result:
        message.append({"msg": "Product not found"})
    elif result.stock < product.stock:
        message.append({"msg": "Stock is Insufficient"})
    else:
        query = msProduct.update().where(msProduct.c.product_name == product.product_name).values(stock=result.stock - product.stock)
        await db.execute(query)
    response = RedirectResponse(request.url_for("read_item"))
    response.status_code = status.HTTP_303_SEE_OTHER
    return response

@router.delete("/{id}")
async def delete_item(id:int):
    query = msProduct.delete().where(msProduct.c.id == id)
    await db.execute(query)
    response = RedirectResponse(request.url_for("read_item"))
    response.status_code = status.HTTP_303_SEE_OTHER
    return response

@router.get('/camera', response_class=HTMLResponse)
async def camera_feed():
    return  StreamingResponse(gen(),media_type='multipart/x-mixed-replace; boundary=frame')

@router.post("/capture")
async def capture_image(image: UploadFile = File(...)):
    contents = await image.read()
    np_data = np.fromstring(contents, np.uint8)
    img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    cv2.imwrite('src/static/uploads/gambar.jpg', img)
    text = OCR.detect_text(img)
    return {"message": text}