from analyze import analyzer
from dataManager import dataVisualizer
from utils import RunMode
import argparse
import signal
import sys
import threading
import datetime
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-mav",
        "--mavDataFile",
        help="optional file containing containing mavlink data for a video",
    )
    parser.add_argument(
        "-video",
        "--inputVideo",
        help="optional file containing video matching mavlink data",
    )
    args = parser.parse_args()

    mode = RunMode.LIVE
    videoStream = 2  # set to 2/3 depending on which stream camera is coming in on
    gpsFile = ""

    if (args.mavDataFile is not None) ^ (args.inputVideo is not None):
        print("Either both optional arguments are required or neither.")
        exit()

    if args.mavDataFile is not None and args.inputVideo is not None:
        mode = RunMode.RECORDED
        videoStream = args.inputVideo
        gpsFile = args.mavDataFile

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    anz = analyzer(timestamp, mode, gpsFile, videoStream)

    def stopper(signal, frame):
        print()
        print("Sending stop signal")
        anz.mavlink.shutdown()
        anz.fsInterface.shutdown()
        anz.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, stopper)

    dataVis = dataVisualizer(anz)
