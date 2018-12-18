import datetime
import logging
import os
import sys
import pygame

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
logger = logging.getLogger()


def say_hello():
    # assume sudo rfcomm connect hci0 00:16:53:56:43:DE
    EV3 = serial.Serial('/dev/rfcomm0')
    try:
        logger.info("Going UP")
        s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'up', 10)
        EV3.write(s)
        pygame.mixer.init()
        pygame.mixer.music.load("./data/6days.wav")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
        time.sleep(15)
        logger.info("Going down DOWN")
        s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'down', 10)
        EV3.write(s)
    except BaseException as error:
        logger.error("Unable to open serial port {}".format(error))
    EV3.close()
    logger.info("Done! Connection Close")


def main_loop():
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
                                logger.info("Detected face with {}".format(w * h / 2073600))
                        if contains_big_face:
                            cv.imwrite(
                                os.path.join("images",
                                             "{}.jpg".format(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M"))),
                                img)
                            say_hello()
                            time.sleep(15)  # let him go
        except KeyboardInterrupt:
            # quit
            sys.exit()
        except BaseException as error:
            logger.error('An exception occurred in dispatch thread: {}'.format(error))


if __name__ == "__main__":
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logFormatter)
    rootLogger.addHandler(console_handler)
    fileHandler = logging.FileHandler("{0}/{1}.log".format("logs", "out"))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    # ..  ######..##....##..#######..##......##.##.....##....###....##....##
    # .  ##....##.###...##.##.....##.##..##..##.###...###...##.##...###...##
    # .  ##.......####..##.##.....##.##..##..##.####.####..##...##..####..##
    # ..  ######..##.##.##.##.....##.##..##..##.##.###.##.##.....##.##.##.##
    # .......  ##.##..####.##.....##.##..##..##.##.....##.#########.##..####
    # .  ##....##.##...###.##.....##.##..##..##.##.....##.##.....##.##...###
    # ..  ######..##....##..#######...###..###..##.....##.##.....##.##....##
    logger.info("Snowman is starting")
    main_loop()
