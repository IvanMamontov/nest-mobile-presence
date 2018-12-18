import datetime
import os
import sys

import requests
import numpy as np
import cv2 as cv
import config
import serial
import time
import EV3BT

face_cascade = cv.CascadeClassifier(config.face_cascade)


# response = requests.request("GET", config.api_url,  data=payload,  headers=config.headers)
# response.raise_for_status()
# data = response.json()

def say_hello():
    # assume sudo rfcomm connect hci0 00:16:53:56:43:DE
    EV3 = serial.Serial('/dev/rfcomm0')
    print("Sending UP")
    s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'up', 10)
    EV3.write(s)
    time.sleep(15)
    print("Done. Sending DOWN")
    s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'down', 10)
    EV3.write(s)
    print("Done!")
    EV3.close()


for _ in range(100000):
    try:
        resp = requests.request("GET", config.cam_url, headers=config.headers, params=config.auth, stream=True)
        if resp.status_code == 200 and resp.headers['content-type'] == 'image/jpeg':
            img = np.asarray(bytearray(resp.content), dtype="uint8")
            img = cv.imdecode(img, cv.IMREAD_COLOR)
            height, width, channels = img.shape
            if height == 1080 and width == 1920:
                gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.05, 6)
                if len(faces) > 0:
                    contains_big_face = False
                    for (x, y, w, h) in faces:
                        if w * h / 2073600 > 0.10:  # assume 1080 * 1920 = 2073600, so more than 10%
                            cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            contains_big_face = True
                            print("size {}".format(w * h / 2073600))
                    if contains_big_face:
                        cv.imwrite(
                            os.path.join("images", "{}.jpg".format(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M"))),
                            img)
                        say_hello()
    except KeyboardInterrupt:
        # quit
        sys.exit()
    except BaseException as error:
        print('An exception occurred in dispatch thread: {}'.format(error))
