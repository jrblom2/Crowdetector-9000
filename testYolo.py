import cv2

import numpy as np
import time

from ultralytics import YOLO

model = YOLO('yolo11x')
# model.train(
#     data="datasets/aerialData2/data.yaml",
#     epochs=100,
#     patience=5,
#     batch=-1,
# )

cam = cv2.VideoCapture("./bikeCut.mp4")
while True:
    ret, frame = cam.read()
    if ret:
        results = model(frame)

        frame = results[0].plot()

        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', frame)
        cv2.waitKey(1)
        time.sleep(1.0 / 60.0)
    else:
        break
