import cv2
import pytesseract
from pytesseract import Output
from imutils.object_detection import non_max_suppression
import imutils
import paho.mqtt.publish as publish
import json

import numpy as np
class OCR:
    @staticmethod
    def detect_text(image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("src/static/uploads/gray.png", gray_image)
        thresh_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        cv2.imwrite("src/static/uploads/binary.png",thresh_img)
        kernel_size = 2
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        # Apply erosion
        eroded_img = cv2.erode(thresh_img, kernel, iterations=1)
        cv2.imwrite("src/static/uploads/eroded.png", eroded_img)
        # recognizing text
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(thresh_img, config=config)
        text = text.replace('\x0c','')
        return text
    
    @staticmethod
    def detect_text_exp(image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("src/static/uploads/exp_gray.png", gray_image)
        thresh_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        cv2.imwrite("src/static/uploads/exp_binary.png",thresh_img)
        kernel_size = 2
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        # Apply erosion
        eroded_img = cv2.erode(thresh_img, kernel, iterations=1)
        cv2.imwrite("src/static/uploads/exp_eroded.png", eroded_img)
        # recognizing text
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(thresh_img, config=config)
        text = text.replace('\x0c','')
        return text

    @staticmethod
    def forward_passer(net, image, layers, timing=True):
        """
        Returns results from a single pass on a Deep Neural Net for a given list of layers
        :param net: Deep Neural Net (usually a pre-loaded .pb file)
        :param image: image to do the pass on
        :param layers: layers to do the pass through
        :param timing: show detection time or not
        :return: results obtained from the forward pass
        """
        h, w = image.shape[:2]
        blob = cv2.dnn.blobFromImage(image, 1.0, (w, h), (123.68, 116.78, 103.94), swapRB=True, crop=False)
        net.setInput(blob)
        scores, geometry = net.forward(layers)

        return scores, geometry

    @staticmethod
    def box_extractor(scores, geometry, min_confidence):
        """
        Converts results from the forward pass to rectangles depicting text regions & their respective confidences
        :param scores: scores array from the model
        :param geometry: geometry array from the model
        :param min_confidence: minimum confidence required to pass the results forward
        :return: decoded rectangles & their respective confidences
        """
        num_rows, num_cols = scores.shape[2:4]
        rectangles = []
        confidences = []

        for y in range(num_rows):
            scores_data = scores[0, 0, y]
            x_data0 = geometry[0, 0, y]
            x_data1 = geometry[0, 1, y]
            x_data2 = geometry[0, 2, y]
            x_data3 = geometry[0, 3, y]
            angles_data = geometry[0, 4, y]

            for x in range(num_cols):
                if scores_data[x] < min_confidence:
                    continue

                offset_x, offset_y = x * 4.0, y * 4.0

                angle = angles_data[x]
                cos = np.cos(angle)
                sin = np.sin(angle)

                box_h = x_data0[x] + x_data2[x]
                box_w = x_data1[x] + x_data3[x]

                end_x = int(offset_x + (cos * x_data1[x]) + (sin * x_data2[x]))
                end_y = int(offset_y + (cos * x_data2[x]) - (sin * x_data1[x]))
                start_x = int(end_x - box_w)
                start_y = int(end_y - box_h)

                rectangles.append((start_x, start_y, end_x, end_y))
                confidences.append(scores_data[x])

        return rectangles, confidences


    @staticmethod
    def resize_image(image, width, height):
        """
        Re-sizes image to given width & height
        :param image: image to resize
        :param width: new width
        :param height: new height
        :return: modified image, ratio of new & old height and width
        """
        h, w = image.shape[:2]

        ratio_w = w / width
        ratio_h = h / height

        image = cv2.resize(image, (width, height))

        return image, ratio_w, ratio_h

    @staticmethod
    def read_image(img):
        layer_names = ['feature_fusion/Conv_7/Sigmoid', 'feature_fusion/concat_3']
        net = cv2.dnn.readNet("src/stream/ai/frozen_east_text_detection.pb")
        image = img
        orig_image = image.copy()
        orig_h, orig_w = orig_image.shape[:2]
        width=320
        height=320
        min_confidence=0.3
        padding = 0.2
        image, ratio_w, ratio_h = OCR.resize_image(image, width, height)
        scores,geometry = OCR.forward_passer(net, image, layer_names)
        rectangles, confidences = OCR.box_extractor(scores, geometry, min_confidence)
        boxes = non_max_suppression(np.array(rectangles), probs=confidences)
        results = []
        maximum = 0
        biggest = None
        idx = 0
        for (start_x, start_y, end_x, end_y) in boxes:
            start_x = int(start_x * ratio_w)
            start_y = int(start_y * ratio_h)
            end_x = int(end_x * ratio_w)
            end_y = int(end_y * ratio_h)

            dx = int((end_x - start_x) * padding)
            dy = int((end_y - start_y) * padding)

            start_x = max(0, start_x - dx)
            start_y = max(0, start_y - dy)
            end_x = min(orig_w, end_x + (dx*2))
            end_y = min(orig_h, end_y + (dy*2))

            # ROI to be recognized
            roi = orig_image[start_y:end_y, start_x:end_x]
            gray_image = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # blr = cv2.GaussianBlur(gray_image, (3, 3), 0)
            thresh_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            kernel_size = 2
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            # Apply erosion
            eroded_img = cv2.erode(thresh_img, kernel, iterations=1)
            cv2.imwrite("src/static/uploads/roi{}.png".format(idx), eroded_img)
            # recognizing text
            config = '--oem 3 --psm 7'
            text = pytesseract.image_to_string(eroded_img, config=config)

            # collating results
            results.append(((start_x, start_y, end_x, end_y), text))
            if ((end_x-start_x)*(end_y-start_y)) > maximum:
                maximum = ((end_x-start_x)*(end_y-start_y))
                biggest = text
            idx+=1
        return biggest
        # # Resize the image if required
        # # img = cv2.resize(img, (width//2, height//2))
        
        # # Convert image to grey scale
        # gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # # Converting grey image to binary image by Thresholding
        # thresh_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # # configuring parameters for tesseract
        # custom_config = r'--oem 3 --psm 3'
        
        # # Get all OCR output information from pytesseract
        # ocr_output_details = pytesseract.image_to_data(thresh_img, output_type = Output.DICT, config=custom_config, lang='eng')
        # # Total bounding boxes
        # n_boxes = len(ocr_output_details['level'])
        
        # # Extract and draw rectangles for all bounding boxes
        # area = []
        # textFiltered = []
        # for i in range(n_boxes):
        #     (x, y, w, h) = (ocr_output_details['left'][i], ocr_output_details['top'][i], ocr_output_details['width'][i], ocr_output_details['height'][i])
        #     if len(ocr_output_details['text'][i])>3:
        #         area.append(w*h)
        #         textFiltered.append(ocr_output_details['text'][i])
        #         cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        #     # if w*h > largest:
        #     #     largest = w*h
        #     #     largestidx=i
            
        
        # largestidx = np.argmax(area)

        # # Print OCR Output kesys
        # # print(ocr_output_details['text'][largest])
        # cv2.imwrite('static/uploads/ocr.jpg', img)
        # return textFiltered[largestidx]
        
class Email:
    @staticmethod 
    def send(product_name,expired):
        msg = """
        <h1>Peringatan!!!</h1><br>
        <h3> Barang {} akan Expired kurang dari 1 bulan</h3>
        <h3> Tanggal Expired {} </h3>
        <h2> Mohon Diperhatikan</h2>
        """
        to = "melkimariogulo@gmail.com"
        header = "Pesan Peringatan Barang Expired!"
        dict_send = {
            "header":header,
            "msg":msg.format(product_name,expired),
            "to":to
        }
        publish.single("/bimo/forwarder",json.dumps(dict_send),hostname="test.mosquitto.org")
        # print("masuk")

    