
import datetime
import logging
import os
import sys
import pygame
import pygame.midi

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
        logger.info("Sleeping for 7 sec")
        time.sleep(7)
        logger.info("Make a noise")
        play_voice()
        logger.info("Sleeping for 1 sec")
        time.sleep(1)
        logger.info("Going down DOWN")
        s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'down', 10)
        EV3.write(s)
        time.sleep(7)
        logger.info("Done! Going to close connection")
    except BaseException as error:
        logger.error("Unable to open serial port {}".format(error))
    EV3.close()


def play_voice():
    try:
        pygame.midi.init()
        pygame.mixer.init(44100, -16, 2, 2048)
        pygame.mixer.music.set_volume(10)
        pygame.mixer.music.load(os.path.join("data", "12days.wav"))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
    except BaseException as error:
        logger.error("Unable to play sound {}".format(error))


def find_the_face(faces):
    the_face = (0, 0, 0, 0)
    for (x, y, w, h) in faces:
        if w * h > the_face[2] * the_face[3]:
            the_face = (x, y, w, h)
    return the_face


def main_loop():
    while True:
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
                        (x, y, w, h) = find_the_face(faces)
                        contains_big_face = False
                        timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M")
                        if w * h / 2073600 > 0.001:
                            if 400 < x < 1200 and y < 800:  # assume 1080 * 1920 = 2073600, so more than 10%
                                cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                                logger.info("Detected big enough({}) face at {}".format(w * h / 2073600, timestamp))
                                cv.imwrite(
                                    os.path.join("images", "{}.jpg".format(timestamp)), img)
                                say_hello()
                                time.sleep(15)  # let him go
                                logger.info("Ready to Go!")
                            else:
                                logger.info("Detected face out of zone({}x{}) at {}".format(x, y, timestamp))
                        else:
                            logger.info("Detected face too small({}) at {}".format(w * h / 2073600, timestamp))
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
    say_hello()
    main_loop()
