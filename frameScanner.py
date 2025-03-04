import cv2

from ultralytics import YOLO
from utils import RunMode
import time
import threading
import numpy as np


class frameScanner:

    def __init__(self, video, yoloModel, mode, timestamp):
        self.stopSignal = False
        self.timestamp = timestamp

        self.cam = cv2.VideoCapture(video)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        self.width = int(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cam.get(cv2.CAP_PROP_FPS)

        self.frameTime = 1.0 / self.fps
        self.lastFrame = None
        self.hasFrame = False
        print("FPS is: ", self.fps)

        self.waitTime = 1

        self.mode = mode
        print("Size is: ", self.width, " x ", self.height)

        self.model = YOLO(yoloModel)

        self.framePoll = threading.Thread(target=self.pollFrames)
        self.framePoll.start()

        self.startTime = None

        if self.mode is RunMode.LIVE:
            self.waitTime = 1
            # self.detectionWriter = cv2.VideoWriter(f"videos/detections_{timestamp}.mp4", fourcc, self.fps, size)
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
            # self.detectionWriter.release()

    def pollFrames(self):
        lastRead = time.time()
        while not self.stopSignal:
            ret, frame = self.cam.read()
            self.hasFrame = ret
            if ret:
                self.lastFrame = frame
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
        return self.hasFrame, self.lastFrame

    def getIdentifiedFrame(self, frame):
        results = None
        detectionsFrame = None
        # only people and cars, can change as needed
        results = self.model.track(frame, persist=True, verbose=False, classes=[0, 2])
        detectionsFrame = results[0].plot()

        # if self.mode is RunMode.LIVE:
        #     self.detectionWriter.write(detectionsFrame)

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
