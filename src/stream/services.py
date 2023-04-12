import cv2
import pytesseract

class OCR:
    @staticmethod
    def read_image(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        gray = img
        # Text detection
        text_detector = cv2.text.TextDetectorCNN_create("model/textbox.prototxt", "model/TextBoxes_icdar13.caffemodel")
        boxes, confidences = text_detector.detect(gray)

        # Find the largest bounding box
        largest_box = None
        largest_area = 0
        for box in boxes:
            x, y, w, h = box
            area = w * h
            if area > largest_area:
                largest_box = box
                largest_area = area

        # Extract text from the largest bounding box
        x, y, w, h = largest_box
        text_img = gray[y:y+h, x:x+w]
        text = pytesseract.image_to_string(text_img)
        print(text)
        return text