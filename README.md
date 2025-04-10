# Crowdetector-9000

This project uses aerial footage gathered live from either a drone or a plane (or an aerial platform that can transmit mavlink data) to perform object detection and crowd estimation.

[Portfolio Link](https://jrblom2.github.io/crowd/)


## Requirments

1. mavlink messages need to be availaible on the system through a port defined in the config file. Both `GLOBAL_POSITION_INT` and `ATTITUDE` need to be available.
2. video data needs to be be available on a camera device, the number of which is also specified through the config file.
3. Other values in the config file will need to be set as needed such as camera paramters, mount angle on the vehicle, and a proper calibration if one is desired.
   
## Quickstart

1. Running the main.py file will run the app in live mode, where it will look for a camera on device 2 and availalbe mavlink data. When run this way, the camera stream as well as the mavlink data will be saved to a dump file for later playack and offline analysis. 
2. The project can be run in a recorded mode by passing the timestamp of a recorded video and mav file.
3. In either case, the results are served on a local web server hosting maps at `127.0.0.1:8050`

## System Overview

The system consists of three parts. The first is the data input which normally comes from a vehicle live through both a camera feed as well as a mavlink connection. The second part takes the most recent data available from both streams in a loop and plots detections in geographic coordinates. This object detection does the best it can to keep track of the same object from one frame to the next to minimize duplicate detections. The last part takes the produced data and plots it to a constantly updating web-server displaying a map for the area of interest. 
![Crowd](https://github.com/user-attachments/assets/c4ba7abe-f3a9-4970-8a69-a507951c2a7b)

## Hardware

Any vehicle can be used for this project provided it mounts a camera that can trasmit to the ground station in real time. However, the image detection will not work as well with lower resolution images or with analog video.
Good results could be acheivable even in these scenarious, but the model would need to be trained with data specifically from these cameras.

The Walksnail Avatar camera system works very well for this project.
https://caddxfpv.com/products/walksnail-avatar-fpv-vrx?variant=49202408685870

![image](https://github.com/user-attachments/assets/34471c34-a94b-489d-975c-971da0f73418)


With most setups, there will be ground control software interfacing with the vehicle, and this is what will forward the mavlink messages to the application. Some examples of GCS are QGroundControl or Mission Planner.
Two basic vehicles were used for this project, with the drone providing much better results due to being more stable. A plane might be a better platform with more advanced hardware.

![droneEdited](https://github.com/user-attachments/assets/bd212d7c-bc25-49a8-aa7a-bae30c5ec9ed)
