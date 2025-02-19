from analyze import analyzer
from dataManager import dataVisualizer
from utils import RunMode
import argparse
import datetime
import pandas as pd

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
    videoStream = 0  # set to 2/3 depending on which stream camera is coming in on
    gpsFile = ""

    if (args.gpsDataFile is not None) ^ (args.inputVideo is not None):
        print("Either both optional arguments are required or neither.")
        exit()

    if args.gpsDataFile is not None and args.inputVideo is not None:
        mode = RunMode.RECORDED
        videoStream = args.inputVideo
        gpsFile = args.gpsDataFile

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    anz = analyzer(timestamp, mode, gpsFile, videoStream)

    dataVis = dataVisualizer(anz)
