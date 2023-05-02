import cv2
import pytesseract
from pytesseract import Output
from imutils.object_detection import non_max_suppression
import imutils

import numpy as np
class OCR:
    @staticmethod
    def read_image(img):

        layer_names = ['feature_fusion/Conv_7/Sigmoid', 'feature_fusion/concat_3']
        net = cv2.dnn.readNet("src/stream/ai/east_text_detection.pb")
        img = img[142:338,156:484]
        orig = img.copy()
        
        orig_h,orig_w = img.shape[:2]
        blob = cv2.dnn.blobFromImage(img, 1.0, (new_w, new_h), (123.68, 116.78, 103.94), swapRB=True, crop=False)
        # Resize the image if required
        # img = cv2.resize(img, (width//2, height//2))
        
        # Convert image to grey scale
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Converting grey image to binary image by Thresholding
        thresh_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # configuring parameters for tesseract
        custom_config = r'--oem 3 --psm 3'
        
        # Get all OCR output information from pytesseract
        ocr_output_details = pytesseract.image_to_data(thresh_img, output_type = Output.DICT, config=custom_config, lang='eng')
        # Total bounding boxes
        n_boxes = len(ocr_output_details['level'])
        
        # Extract and draw rectangles for all bounding boxes
        area = []
        textFiltered = []
        for i in range(n_boxes):
            (x, y, w, h) = (ocr_output_details['left'][i], ocr_output_details['top'][i], ocr_output_details['width'][i], ocr_output_details['height'][i])
            if len(ocr_output_details['text'][i])>3:
                area.append(w*h)
                textFiltered.append(ocr_output_details['text'][i])
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # if w*h > largest:
            #     largest = w*h
            #     largestidx=i
            
        
        largestidx = np.argmax(area)

        # Print OCR Output kesys
        # print(ocr_output_details['text'][largest])
        cv2.imwrite('static/uploads/ocr.jpg', img)
        return textFiltered[largestidx]
        