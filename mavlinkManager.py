from pymavlink import mavutil
from utils import RunMode
import os
import json
import time
import threading


class mavlinkManager:

    def __init__(self, port, mode, timestamp, file=None):
        # Set up connection to vehicle
        self.connection = mavutil.mavlink_connection(f'udp:localhost:{port}')

        self.runMode = mode

        self.lastMessage = None
        self.mavPoll = threading.Thread(target=self.pollGPI)
        self.mavPoll.start()

        # If Live, open stream file to record. If recorded, open the data.
        if mode is RunMode.LIVE:
            self.writeFile = open(f"mavdumps/mavlink_{timestamp}.json", "w")
        else:
            self.readFile = open(file, "r")

    def __del__(self):
        if hasattr(self, 'writeFile'):
            self.writeFile.close()
        if hasattr(self, 'readFile'):
            self.readFile.close()

    def confirmHeartbeat(self):
        if self.runMode is RunMode.LIVE:
            self.connection.wait_heartbeat()

    def pollGPI(self):
        while True:
            if self.runMode is RunMode.LIVE:
                msg = self.connection.recv_match(
                    type='GLOBAL_POSITION_INT', blocking=True
                )

                # Get nice format for the dump, drop headers and such.
                jsonKeys = [
                    'time_boot_ms',
                    'lat',
                    'lon',
                    'alt',
                    'relative_alt',
                    'vx',
                    'vy',
                    'vz',
                    'hdg',
                    '_timestamp',
                ]
                geoDump = {
                    key: msg.__dict__[key]
                    for key in jsonKeys
                    if key in msg.__dict__
                }
                self.writeFile.write(json.dumps(geoDump))
                self.writeFile.write('\n')
                self.writeFile.flush()
                self.lastMessage = geoDump
            else:
                line = self.readFile.readline()
                if line != "":
                    msg = json.loads(line)
                    time.sleep(0.3)
                    self.lastMessage = msg

    def getGPI(self):
        if self.lastMessage["lat"] == 0 and self.lastMessage["lon"] == 0:
            defualt = json.loads(
                "{\"time_boot_ms\": 223087, \"lat\": 42.062252, \"lon\": -87.678276, \"alt\": 930, \"relative_alt\": 30, \"vx\": 0, \"vy\": 0, \"vz\": 0, \"hdg\": 0, \"_timestamp\": 1739383911.5852737}"
            )
            defualt["_timestamp"] = self.lastMessage["_timestamp"]
            return defualt
        return self.lastMessage
