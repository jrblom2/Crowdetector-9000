from mavlinkManager import mavlinkManager
from frameScanner import frameScanner
from utils import RunMode
import time
import argparse
import datetime
import numpy as np
import math

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-g",
        "--gpsDataFile",
        help="optional file containing containing mavlink data for a video",
    )
    parser.add_argument(
        "-i",
        "--inputVideo",
        help="optional file containing video matching mavlink data",
    )
    args = parser.parse_args()

    mode = RunMode.LIVE

    if (args.gpsDataFile is not None) ^ (args.inputVideo is not None):
        print("Either both optional arguments are required or neither.")
        exit()

    if args.gpsDataFile is not None and args.inputVideo is not None:
        mode = RunMode.RECORDED

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    mavlink = mavlinkManager(14445, mode, timestamp, args.gpsDataFile)

    mavlink.confirmHeartbeat()

    fsInterface = frameScanner(0, 'yolo11x', mode, timestamp)

    while 1:
        # Where are we?
        msg = mavlink.getGPI()
        if msg is None:
            print("No geo data!")
            time.sleep(0.1)
            continue
        print(msg)

        # Get camera data
        frame, results = fsInterface.getIdentifiedFrame()
        detectionData = results[0].summary()

        altitude = msg["relative_alt"]
        planeLat = msg["lat"]
        planeLon = msg["lon"]

        # Camera info
        cameraSensorW = 0.00454
        cameraSensorH = 0.00340
        cameraPixelsize = 0.00000314814  # This number might be off
        cameraFocalLength = 0.0021
        cameraTilt = np.pi / 4

        # Basic Ground sample distance, how far in M each pixel is
        nadirGSDH = (altitude * cameraSensorH) / (cameraFocalLength * fsInterface.height)
        nadirGSDW = (altitude * cameraSensorW) / (cameraFocalLength * fsInterface.width)

        cameraCenterX = fsInterface.width / 2
        cameraCenterY = fsInterface.height / 2

        for detection in detectionData:
            # Camera is at a tilt from the ground, so GSD needs to be scaled
            # by relative distance. Assuming camera is level horizontally, so
            # just need to scale tilt in camera Y direction
            box = detection["box"]
            objectX = ((box["x2"] - box["x1"]) / 2) + box["x1"]
            objectY = ((box["y2"] - box["y1"]) / 2) + box["y1"]
            tanPhi = cameraPixelsize * (math.sqrt((objectY ^ 2 - cameraCenterY) ^ 2) / cameraFocalLength)
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

        fsInterface.showFrame(frame)
