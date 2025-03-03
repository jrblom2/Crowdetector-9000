from analyze import analyzer
from dataManager import dataVisualizer
from utils import RunMode
import argparse
import signal
import sys
import time
import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--timestamp",
        help="optional timestamp signaling that we should play back from files",
    )
    args = parser.parse_args()

    mode = RunMode.LIVE
    videoStream = 2  # set to 2/3 depending on which stream camera is coming in on
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if args.timestamp is not None:
        mode = RunMode.RECORDED
        videoStream = f"videos/capture_{args.timestamp}.mp4"
        timestamp = args.timestamp

    anz = analyzer(timestamp, mode, videoStream)

    def stopper(signal, frame):
        print()
        print(f"Sending stop signal at {time.time()}")
        anz.mavlink.shutdown()
        anz.shutdown()
        anz.fsInterface.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, stopper)

    dataVis = dataVisualizer(anz)
