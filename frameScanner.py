import cv2

from ultralytics import YOLO


class frameScanner:

    def __init__(self, video, yoloModel):
        self.cam = cv2.VideoCapture(video)
        self.model = YOLO(yoloModel)

    def getIdentifiedFrame(self):
        ret, frame = self.cam.read()
        if ret:
            results = self.model(frame)
            frame = results[0].plot()

        return frame, results

    def showFrame(frame):
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
