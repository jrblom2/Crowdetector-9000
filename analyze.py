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
            planeHeading = msg['hdg'] / 100

            # Remove detections older than 2 sec and update plane coords
            self.positions = self.positions[self.positions['time'] > time.time() - 1]
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
            cameraPixelsize = 0.00000314814
            cameraFocalLength = 0.0021
            cameraTilt = 63 * (math.pi / 180)

            # Basic Ground sample distance, how far in M each pixel is
            nadirGSDH = (altitude * cameraSensorH) / (cameraFocalLength * self.fsInterface.height)
            nadirGSDW = (altitude * cameraSensorW) / (cameraFocalLength * self.fsInterface.width)

            cameraCenterX = self.fsInterface.width / 2
            cameraCenterY = self.fsInterface.height / 2

            for i, detection in enumerate(detectionData):
                # Camera is at a tilt from the ground, so GSD needs to be scaled
                # by relative distance. Assuming camera is level horizontally, so
                # just need to scale tilt in camera Y direction
                if detection["name"] == "car" or detection["name"] == "person":
                    box = detection["box"]
                    objectX = ((box["x2"] - box["x1"]) / 2) + box["x1"] + trimX1
                    objectY = ((box["y2"] - box["y1"]) / 2) + box["y1"] + trimY1

                    tanPhi = cameraPixelsize * ((objectY - cameraCenterY) / cameraFocalLength)
                    verticalPhi = math.atan(tanPhi)

                    totalAngle = cameraTilt - verticalPhi
                    if totalAngle > 1.57:
                        totalAngle = 1.57
                    adjustedGSDH = nadirGSDH * (1 / math.cos(totalAngle))
                    adjustedGSDW = nadirGSDW * (1 / math.cos(totalAngle))

                    # Distance camera center is projected forward
                    offsetCenterY = math.tan(cameraTilt) * altitude

                    # Positive value means shift left from camera POV
                    offsetYInPlaneFrame = (cameraCenterX - objectX) * adjustedGSDW

                    # Positive value means shift up in camera POV
                    offsetXInPlaneFrame = ((cameraCenterY - objectY) * adjustedGSDH) + offsetCenterY
                    # print("offset center ", offsetCenterY, " offset y ", ((cameraCenterY - objectY) * adjustedGSDH))

                    # north is hdg value of 0/360, convert to normal radians with positive
                    # being counter clockwise
                    rotation = (90 - planeHeading) * (math.pi / 180)

                    # Plane is rotated around world frame by heading, so rotate camera detection back
                    worldXinMeters = offsetXInPlaneFrame * math.cos(rotation) - offsetYInPlaneFrame * math.sin(rotation)
                    worldYinMeters = offsetXInPlaneFrame * math.sin(rotation) + offsetYInPlaneFrame * math.cos(rotation)

                    # Simple meters to lat/lon, can be improved. 1 degree is about 111111 meters
                    objectLon = planeLon + (worldXinMeters * (1 / 111111 * math.cos(planeLat * math.pi / 180)))
                    objectLat = planeLat + (worldYinMeters * (1 / 111111.0))

                    # update
                    if 'track_id' in detection:
                        name = detection['name'] + str(detection['track_id'])
                    else:
                        name = detection['name'] + str(i)

                    print(name)
                    print("objectX ", objectX)
                    print("objectY ", objectY)
                    print("offset center ", offsetCenterY)
                    print("scaling factor ", 1 / math.cos(totalAngle))
                    print("adjustedGSDW ", adjustedGSDW)
                    print("adjustedGSDH ", adjustedGSDH)
                    print("vertical offset ", verticalPhi * 180 / math.pi)
                    print("total angle", totalAngle * 180 / math.pi)
                    print("heading ", planeHeading)
                    print("rotation ", rotation)
                    print("offset plane y ", offsetYInPlaneFrame, " offset plane x", offsetXInPlaneFrame)
                    print("offset in lon ", worldXinMeters, " offset in lat ", worldYinMeters)
                    print()
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
