from pymavlink import mavutil
from utils import RunMode
import datetime
import os
import json


class mavlinkManager:

    def __init__(self, port, mode, file=None):
        # Set up connection to vehicle
        self.connection = mavutil.mavlink_connection(f'udp:localhost:{port}')

        self.runMode = mode
        # If Live, open stream file to record. If recorded, open the data.
        if mode is RunMode.LIVE:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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

    def readGPI(self):
        if self.runMode is RunMode.LIVE:
            # while 1:
            #     try:
            #         msg = self.connection.messages['GLOBAL_POSITION_INT']
            #         break
            #     except KeyError:
            #         print("No geo message received yet.")
            #         time.sleep(0.1)
            msgReceived = False
            while not msgReceived:
                msg = self.connection.recv_match(
                    type='GLOBAL_POSITION_INT', blocking=False
                )
                if msg is not None:
                    msgReceived = True

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
            return geoDump
        else:
            line = self.readFile.readline()
            if line != "":
                msg = json.loads(line)
                return msg
            else:
                return None
