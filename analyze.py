from mavlinkManager import mavlinkManager
from frameScanner import frameScanner
from utils import RunMode
import time
import argparse
import datetime

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

    fsInterface = frameScanner(0, 'yolo11x')

    while 1:
        msg = mavlink.getGPI()
        if msg is None:
            print("No geo data!")
            time.sleep(0.1)
            continue
        print(msg)
        frame, results = fsInterface.getIdentifiedFrame()
        fsInterface.showFrame(frame)
