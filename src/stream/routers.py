from fastapi import APIRouter,Request,File,UploadFile, status
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from src.stream.schema import Image,ProductIn
from src.stream.services import OCR
from fastapi.templating import Jinja2Templates
from src.stream.models import msProduct
from src.database import db
import time
from rpi_lcd import LCD
import numpy as np
import logging
import cv2
import threading
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
# A flag to indicate whether the camera should be running
camera_running = None
video = None
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
    tags=["Stream Service"],
    prefix="/stream"
)

templates = Jinja2Templates(directory="src/stream/templates")
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

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    global video
    global camera_running
    if video is None:
        camera_running = threading.Event()
        camera_running.set()
        video = cv2.VideoCapture(0)
    return templates.TemplateResponse('modalNew.html', {"request": request})

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


@router.get('/video_feed', response_class=HTMLResponse)
async def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return  StreamingResponse(gen(),
                    media_type='multipart/x-mixed-replace; boundary=frame')

@router.post("/capture_image")
async def capture_image(image: UploadFile = File(...)):
    contents = await image.read()
    np_data = np.fromstring(contents, np.uint8)
    img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    cv2.imwrite('src/static/uploads/gambar.jpg', img)
    text = OCR.detect_text(img)
    logging.debug(text)
    return {"message": text}

@router.post("/product",status_code=status.HTTP_201_CREATED)
async def product(productParam:ProductIn):
    global camera_running
    global video
    camera_running.clear()
    video.release()
    video = None
    query = msProduct.insert().values(product_name=productParam.product_name,expired=productParam.expired,stock=productParam.stock)
    last_record_id = await db.execute(query)
    lcd.clear()
    buzzer()
    lcd.text(productParam.product_name, 1)
    lcd.text(productParam.expired, 2)
    return {"message":"ok"}