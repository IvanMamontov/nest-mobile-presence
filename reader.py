import requests
import numpy as np
import cv2 as cv
import config
import serial
import time
import EV3BT
from timeit import default_timer as timer

face_cascade = cv.CascadeClassifier(config.face_cascade)

#response = requests.request("GET", config.api_url, headers=config.headers)
#response.raise_for_status()
#data = response.json()

# assume sudo rfcomm connect hci0 00:16:53:56:43:DE
EV3 = serial.Serial('/dev/rfcomm0')
print("Listening for EV3 Bluetooth messages, press CTRL C to quit.")
left = 10
right = 10
s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'up', 10)
EV3.write(s)
s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'down', 10)
EV3.write(s)
EV3.close()

for _ in range(1000):
    resp = requests.request("GET", config.cam_url, headers=config.headers, params=config.auth, stream=True)
    if resp.status_code == 200 and resp.headers['content-type'] == 'image/jpeg':
        img = np.asarray(bytearray(resp.content), dtype="uint8")
        img = cv.imdecode(img, cv.IMREAD_COLOR)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        start = timer()
        faces = face_cascade.detectMultiScale(gray, 1.05, 6)
        end = timer()
        print(end - start)  # Time in seconds, e.g. 5.38091952400282
        for (x, y, w, h) in faces:
            cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv.imwrite("face.jpg", img)

        print(len(faces))
