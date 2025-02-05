import cv2

import numpy as np
import time

# import pyrealsense2 as rs

from ultralytics import YOLO

# pipeline = rs.pipeline()
# config = rs.config()

# config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
# profile = pipeline.start(config)

model = YOLO('yolo11x')
# model.train(
#     data="datasets/aerialData2/data.yaml",
#     epochs=100,
#     patience=5,
#     batch=-1,
# )

cam = cv2.VideoCapture("./bikeCut.mp4")
while True:
    # frames = pipeline.wait_for_frames()
    # color_frame = frames.get_color_frame()

    # if not color_frame:
    #     continue

    # color_image = np.asanyarray(color_frame.get_data())
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
