# Crowdotron-9000

This project uses aerial footage gathered live from either a drone or a plane (or an aerial platform that can transmit mavlink data) to perform object detection and crowd estimation.


## Quickstart

1. Running the main.py file will run the app in live mode, where it will look for a camera on device 2 and availalbe mavlink data. When run this way, the camera stream as well as the mavlink data will be saved to a dump file for later playack and offline analysis. 
2. The project can be run in a recorded mode by passing the timestamp of a recorded video and mav file.
3. In either case, the results are served on a local web server hosting maps at `127.0.0.1:8050`

## System Overview

The system consists of three parts. The first is the data input which normally comes from a vehicle live through both a camera feed as well as a mavlink connection. The second part takes the most recent data available from both streams in a loop and plots detections in geographic coordinates. This object detection does the best it can to keep track of the same object from one frame to the next to minimize duplicate detections. The last part takes the produced data and plots it to a constantly updating web-server displaying a map for the area of interest. 
