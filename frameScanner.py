import pickle
import threading
import time

import cv2
import numpy as np
import yaml
from ultralytics import YOLO

from utils import RunMode


class frameScanner:

    def __init__(self, video, mode, timestamp):
        with open("config.yaml", "r") as f:
            self.config = yaml.safe_load(f)

        with open('cameraCalibration', 'rb') as f:
            self.camcalib = pickle.load(f)

        self.stopSignal = False
        self.timestamp = timestamp

        self.cam = cv2.VideoCapture(video)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['camera']['width'])
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['camera']['height'])

        self.width = int(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.fwidth = 0
        self.fheight = 0
        self.fps = self.cam.get(cv2.CAP_PROP_FPS)

        self.frameTime = 1.0 / self.fps
        self.lastFrame = None
        self.lastDst = None
        self.hasFrame = False
        print("FPS is: ", self.fps)

        self.waitTime = 1

        self.mode = mode
        print("Size is: ", self.width, " x ", self.height)

        self.model = YOLO(self.config['camera']['model'])

        self.framePoll = threading.Thread(target=self.pollFrames)
        self.framePoll.start()

        self.startTime = None

        if self.mode is RunMode.LIVE:
            self.waitTime = 1
            self.frameBuffer = []
            self.readyToRecord = False
            self.frameWrite = threading.Thread(target=self.writeFrames)
            self.frameWrite.start()
        else:
            self.duration = int(self.cam.get(cv2.CAP_PROP_FRAME_COUNT)) / self.fps

    def shutdown(self):
        self.stopSignal = True
        self.cam.release()
        self.framePoll.join()

        if self.mode is RunMode.LIVE:
            self.frameWrite.join()
            runTime = time.time() - self.startTime
            runFps = len(self.frameBuffer) / runTime
            print("Computed FPS: ", runFps)
            size = (self.width, self.height)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(f"videos/capture_{self.timestamp}.mp4", fourcc, runFps, size)

            print("Writing Video")
            for frame in self.frameBuffer:
                writer.write(frame)
            print("All done")
            writer.release()

    def pollFrames(self):
        # setup
        lastRead = time.time()
        w = self.config['camera']['width']
        h = self.config['camera']['height']

        if self.config['camera']['useCalib']:
            mtx = self.camcalib['mtx']
            dist = self.camcalib['dist']
            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
            x, y, w, h = roi
        self.fwidth = w
        self.fheight = h

        # Get frames in loop
        while not self.stopSignal:
            ret, frame = self.cam.read()
            self.hasFrame = ret
            if ret:
                self.lastFrame = frame
                if self.config['camera']['useCalib']:
                    # undistort
                    dst = cv2.undistort(frame, mtx, dist, None, newcameramtx)

                    # crop the image
                    dst = dst[y : y + h, x : x + w]
                    self.lastDst = dst
                else:
                    self.lastDst = frame

                # Sleep until next frame
                if self.mode == RunMode.RECORDED:
                    timeDif = time.time() - lastRead
                    if timeDif < self.frameTime:
                        time.sleep(self.frameTime - timeDif)
                    lastRead = time.time()
        print("closing video stream")

    def writeFrames(self):
        lastWrite = time.time()
        while not self.stopSignal:
            if self.lastFrame is not None and self.readyToRecord:
                eTime = time.time() - lastWrite
                if eTime < self.frameTime:
                    time.sleep(self.frameTime - eTime)
                self.frameBuffer.append(self.lastFrame)
                lastWrite = time.time()

    def getFrame(self):
        return self.hasFrame, self.lastDst, self.fwidth, self.fheight

    def getIdentifiedFrame(self, frame):
        results = None
        detectionsFrame = None
        # only people and cars, can change as needed
        results = self.model.track(frame, persist=True, verbose=False, classes=self.config['analyze']['classes'])
        detectionsFrame = results[0].plot()

        return detectionsFrame, results

    def rotateFrame(self, frame, roll):
        roll_angle_degrees = roll * (180 / np.pi)

        # Get the image dimensions
        (h, w) = frame.shape[:2]

        # Get the rotation matrix for the specified angle
        rotation_matrix = cv2.getRotationMatrix2D((w / 2, h / 2), -roll_angle_degrees, 1)

        # Apply the rotation
        return cv2.warpAffine(frame, rotation_matrix, (w, h))

    def showFrame(self, frame):
        cv2.imshow('PlaneOfView', frame)
        cv2.waitKey(self.waitTime)

    def trainModel(self, data, epochs, patience, batch=-1):
        self.model.train(
            data=data,
            epochs=epochs,
            patience=patience,
            batch=batch,
        )
