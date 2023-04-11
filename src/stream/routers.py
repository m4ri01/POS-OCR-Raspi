from fastapi import APIRouter,Request,File,UploadFile
from src.stream.services import camera
from fastapi.responses import HTMLResponse, StreamingResponse
from src.stream.schema import Image
from fastapi.templating import Jinja2Templates
import numpy as np
import base64
import cv2
import threading

router = APIRouter(
    tags=["Stream Service"],
    prefix="/stream"
)

templates = Jinja2Templates(directory="src/stream/templates")

# A flag to indicate whether the camera should be running
camera_running = None
video = None
@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    global video
    global camera_running
    if video is None:
        camera_running = threading.Event()
        camera_running.set()
        video = cv2.VideoCapture(0)
    return templates.TemplateResponse('index.html', {"request": request})

def gen():
    """Video streaming generator function."""
    global camera_running
    global video
    while camera_running.is_set():
        success, image = video.read()
        if not success:
            break
        cv2.rectangle(image,(156,142),(484,338),(0,255,0),2)
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
    global camera_running
    global video
    camera_running.clear()
    video.release()
    video = None
    contents = await image.read()
    np_data = np.fromstring(contents, np.uint8)
    img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    cv2.imwrite('src/static/uploads/gambar.jpg', img)
    return {"message": "Image saved successfully."}
