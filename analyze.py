from mavlinkManager import mavlinkManager
from frameScanner import frameScanner
import time
import numpy as np
import math
import threading
import pandas as pd


class analyzer:
    def __init__(self, timestamp, mode, gpsDataFile, videoStream):
        self.positions = pd.DataFrame({'id': [], 'lat': [], 'lon': [], 'alt': [], 'time': [], 'color': []})
        self.mavlink = mavlinkManager(14445, mode, timestamp, gpsDataFile)

        print("Run mode is: ", mode.name)
        self.mavlink.confirmHeartbeat()

        print("Found heartbeat.")

        self.fsInterface = frameScanner(videoStream, 'yolo11x', mode, timestamp)

        self.analyzeThread = threading.Thread(target=self.analyzeLoop)
        self.analyzeThread.start()

    def updatePositions(self, row):
        if row['id'] in self.positions['id'].values:
            self.positions.loc[self.positions['id'] == row['id'], ['lat', 'lon', 'alt', 'time']] = (
                row['lat'],
                row['lon'],
                row['alt'],
                row['time'],
            )
        else:
            self.positions = pd.concat([self.positions, pd.DataFrame([row])], ignore_index=True)

    def analyzeLoop(self):
        dataTimeout = 0
        while dataTimeout < 5:
            # Get camera data
            ret, frame = self.fsInterface.getFrame()

            # Where are we?
            msg = self.mavlink.getGPI()

            if not ret or msg is None:
                print("No data in either frames or geo data!")
                dataTimeout += 1
                time.sleep(1)
                continue

            trimX1 = 250
            trimX2 = 250
            trimY1 = 100
            trimY2 = 0

            frame = frame[trimY1 : self.fsInterface.height - trimY2, trimX1 : self.fsInterface.width - trimX2]
            frame, results = self.fsInterface.getIdentifiedFrame(frame)
            detectionData = results[0].summary()

            altitude = msg["relative_alt"] / 1000
            planeLat = msg["lat"] / 10000000
            planeLon = msg["lon"] / 10000000

            # Remove detections older than 2 sec and update plane coords
            self.positions = self.positions[self.positions['time'] > time.time() - 2]
            planeUpdate = {
                "id": "Plane",
                "lat": planeLat,
                "lon": planeLon,
                "alt": altitude,
                "time": time.time(),
                'color': 'blue',
            }
            self.updatePositions(planeUpdate)

            # Camera info
            cameraSensorW = 0.00454
            cameraSensorH = 0.00340
            cameraPixelsize = 0.00000314814  # This number might be off
            cameraFocalLength = 0.0021
            cameraTilt = np.pi / 4

            # Basic Ground sample distance, how far in M each pixel is
            nadirGSDH = (altitude * cameraSensorH) / (cameraFocalLength * self.fsInterface.height)
            nadirGSDW = (altitude * cameraSensorW) / (cameraFocalLength * self.fsInterface.width)

            cameraCenterX = self.fsInterface.width / 2
            cameraCenterY = self.fsInterface.height / 2

            for detection in detectionData:
                # Camera is at a tilt from the ground, so GSD needs to be scaled
                # by relative distance. Assuming camera is level horizontally, so
                # just need to scale tilt in camera Y direction
                if detection["name"] == "person":
                    box = detection["box"]
                    objectX = ((box["x2"] - box["x1"]) / 2) + box["x1"] + trimX1
                    objectY = ((box["y2"] - box["y1"]) / 2) + box["y1"] + trimY1
                    tanPhi = cameraPixelsize * (math.sqrt((objectY**2 - cameraCenterY) ** 2) / cameraFocalLength)
                    verticalPhi = math.atan(tanPhi)
                    adjustedGSDH = nadirGSDH * (1 / math.cos(cameraTilt - verticalPhi))

                    # Distance camera center is projected forward
                    offsetCenterY = math.tan(cameraTilt) * altitude

                    # Positive value means shift left from camera POV
                    offsetXinM = (cameraCenterX - objectX) * nadirGSDW

                    # Positive value means shift down in camera POV
                    offsetYinM = ((cameraCenterY - objectY) * adjustedGSDH) + offsetCenterY

                    rotation = msg["hdg"] * math.pi / 180

                    # At heading 0, camera Y is straight Longitude while X is latitude. Need to convert.
                    newXinMeters = offsetXinM * math.cos(rotation) - offsetYinM * math.sin(rotation)
                    newYinMeters = offsetXinM * math.sin(rotation) + offsetYinM * math.cos(rotation)

                    # Simple meters to lat/lon, can be improved. 1 degree is about 111111 meters
                    objectLon = planeLon + (newXinMeters * (1 / 111111 * math.cos(planeLat * math.pi / 180)))
                    objectLat = planeLat + (newYinMeters * (1 / 111111.0))

                    # update
                    if 'track_id' in detection:
                        name = detection['name'] + str(detection['track_id'])
                    else:
                        name = detection['name']

                    if detection['name'] == 'person':
                        color = 'red'
                    if detection['name'] == 'car':
                        color = 'green'
                    detectionUpdate = {
                        "id": name,
                        "lat": objectLat,
                        "lon": objectLon,
                        "alt": 0.0,
                        "time": time.time(),
                        "color": color,
                    }
                    self.updatePositions(detectionUpdate)

            self.fsInterface.showFrame(frame)
            dataTimeout = 0
