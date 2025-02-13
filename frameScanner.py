import cv2

from ultralytics import YOLO
from utils import RunMode


class frameScanner:

    def __init__(self, video, yoloModel, mode, timestamp):
        self.cam = cv2.VideoCapture(video)
        self.width = 1920
        self.height = 1080

        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        self.mode = mode
        print("Size is: ", self.width, " x ", self.height)
        if self.mode is RunMode.LIVE:
            size = (self.width, self.height)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(f"videos/capture_{timestamp}.mp4", fourcc, 30, size)
            self.detectionWriter = cv2.VideoWriter(f"videos/detections_{timestamp}.mp4", fourcc, 30, size)

        self.model = YOLO(yoloModel)

    def __del__(self):
        self.cam.release()

        if self.mode is RunMode.LIVE:
            self.writer.release()
            self.detectionWriter.release()

    def getIdentifiedFrame(self):
        ret, frame = self.cam.read()
        results = None
        detectionsFrame = None
        if ret:
            results = self.model.track(frame, persist=True, verbose=False)
            detectionsFrame = results[0].plot()

        if self.mode is RunMode.LIVE:
            self.writer.write(frame)
            self.detectionWriter.write(detectionsFrame)

        return ret, detectionsFrame, results

    def showFrame(self, frame):
        cv2.namedWindow('PlaneOfView', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('PlaneOfView', frame)
        cv2.waitKey(1)

    def trainModel(self, data, epochs, patience, batch=-1):
        self.model.train(
            data=data,
            epochs=epochs,
            patience=patience,
            batch=batch,
        )
