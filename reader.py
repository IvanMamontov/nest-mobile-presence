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
logger = logging.getLogger()


def say_hello(serial, face_count):
    # assume sudo rfcomm connect hci0 00:16:53:56:43:DE
    try:
        logger.info("Going UP")
        if serial:
            s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'up', 10)
            serial.write(s)
            logger.info("Sleeping for 7 sec")
            time.sleep(7)
        logger.info("Make a noise")
        play_voice()
        logger.info("Sleeping for 1 sec")
        time.sleep(1)
        logger.info("Going down DOWN")
        if serial:
            s = EV3BT.encodeMessage(EV3BT.MessageType.Numeric, 'down', 10)
            serial.write(s)
            time.sleep(8)
    except serial.SerialException as error:
        logger.error("Unable to write to serial interface {}".format(error))


def play_voice():
    try:
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
    except BaseException as error:
        logger.error("Unable to play sound {}".format(error))


def main_loop(serial):
    while True:
        try:
            resp = requests.request("GET", config.cam_url, headers=config.headers, params=config.auth, stream=True)
            if resp.status_code == 200 and resp.headers['content-type'] == 'image/jpeg' and int(
                    resp.headers['content-length']) != 0:
                img_arr = np.asarray(bytearray(resp.content), dtype="uint8")
                img = cv.imdecode(img_arr, cv.IMREAD_COLOR)
                # img = cv.imread("./images/20_12_2018_15_45.jpg")
                height, width, channels = img.shape
                # crop the image to speedup processing and remove noise
                img = img[0:int(height * 0.833), int(width * 0.1):int(width * 0.78)]
                gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.05, 6)
                face_count = 0
                timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
                for (x, y, w, h) in faces:
                    if w * h / height * width > 0.001:  # assume 1080 * 1920 = 2073600, so more than 1%
                        cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        face_count = face_count + 1
                if face_count > 0:
                    logger.info("Detected {} faces at {}".format(face_count, timestamp))
                    say_hello(serial, face_count)
                    cv.imwrite(os.path.join("images", "{}.jpg".format(timestamp)), img)
            else:
                logger.info("Empty or incorrect response {}".format(resp.status_code))
                time.sleep(2)  # wait to
        except KeyboardInterrupt:
            # quit
            sys.exit()
        except BaseException as error:
            logger.error('An exception occurred in dispatch thread: {}'.format(error))


def init_sound():
    try:
        pygame.midi.init()
        pygame.mixer.init(44100, -16, 2, 2048)
        pygame.mixer.music.set_volume(10)
        pygame.mixer.music.load(os.path.join("data", "11days.wav"))
    except BaseException as error:
        logger.error("Unable to init sound {}".format(error))


def init_serial():
    try:
        return serial.Serial('/dev/rfcomm0')
    except serial.SerialException as error:
        logger.error("Unable to init serial interface {}".format(error))
    return None


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
    init_sound()
    serial = init_serial()
    say_hello(serial, 0)
    main_loop(serial)
