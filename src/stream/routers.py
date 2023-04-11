from fastapi import APIRouter,Request
from src.stream.services import camera
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import cv2

router = APIRouter(
    tags=["Stream Service"],
    prefix="/stream"
)

templates = Jinja2Templates(directory="stream/templates")

# A flag to indicate whether the camera should be running

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
   return templates.TemplateResponse('index.html', {"request": request})

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@router.get('/video_feed', response_class=HTMLResponse)
async def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return  StreamingResponse(gen(camera.Camera()),
                    media_type='multipart/x-mixed-replace; boundary=frame')

@router.get("/capture_image")
async def capture_image(request: Request):
    camera = cv2.VideoCapture(0)  # Initialize the camera
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    stopped = False  # Flag to stop the generator function

    def generate():
        nonlocal stopped  # Allow access to the stopped flag in the enclosing scope
        while not stopped:
            success, image = camera.read()
            if not success:
                break
            _, img_encoded = cv2.imencode('.jpg', image)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_encoded.tobytes() + b'\r\n')

    try:
        return StreamingResponse(generate(), media_type="multipart/x-mixed-replace;boundary=frame")
    finally:
        stopped = True  # Stop the generator function when the stream is closed
        camera.release()  # Release the camera resources