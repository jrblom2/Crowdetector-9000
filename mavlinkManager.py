from pymavlink import mavutil
from utils import RunMode
import json
import time
import threading


class mavlinkManager:

    def __init__(self, port, mode, timestamp, file=None):
        # Set up connection to vehicle
        self.connection = mavutil.mavlink_connection(f'udp:localhost:{port}')

        self.runMode = mode

        # If Live, open stream file to record. If recorded, open the data.
        if mode is RunMode.LIVE:
            self.writeFile = open(f"mavdumps/mavlink_{timestamp}.json", "w")
        else:
            self.readFile = open(file, "r")

        self.lastMessage = None
        self.mavPoll = threading.Thread(target=self.pollGPI)
        self.mavPoll.start()

    def __del__(self):
        if hasattr(self, 'writeFile'):
            self.writeFile.close()
        if hasattr(self, 'readFile'):
            self.readFile.close()

    def confirmHeartbeat(self):
        print("Checking heartbeat, make sure QGC is running or it is offline mode.")
        if self.runMode is RunMode.LIVE:
            self.connection.wait_heartbeat()

    def pollGPI(self):
        while True:
            if self.runMode is RunMode.LIVE:
                msg = self.connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)

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
                geoDump = {key: msg.__dict__[key] for key in jsonKeys if key in msg.__dict__}
                self.writeFile.write(json.dumps(geoDump))
                self.writeFile.write('\n')
                self.writeFile.flush()
                self.lastMessage = geoDump
            else:
                line = self.readFile.readline()
                if line != "":
                    msg = json.loads(line)

                    # Live mavlink updates messages at about 2 a second
                    if self.lastMessage is not None:
                        time.sleep(msg["_timestamp"] - self.lastMessage["_timestamp"])
                    self.lastMessage = msg
                else:
                    # Means we are at end of file
                    return

            print(self.lastMessage)

    def getGPI(self):
        return self.lastMessage
