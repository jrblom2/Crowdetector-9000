from mavlinkManager import mavlinkManager
from utils import RunMode
import time
import argparse

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

    mavlink = mavlinkManager(14445, mode, args.gpsDataFile)
    mavlink.confirmHeartbeat()

    while 1:
        msg = mavlink.readGPI()
        if msg is None:
            break
        print(msg)
