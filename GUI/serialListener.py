
#for serial comms
import threading
import serial.tools.list_ports
import serial
import re
#for storage
import json
import time

from PyQt5.QtCore import QThread, pyqtSignal



class serialThread (QThread):

    addEntrySignal = pyqtSignal()
    closedSignal = pyqtSignal()

    def __init__(self, threadID, name, c_lock):
        QThread.__init__(self)
        self.closeEvent = threading.Event()
        self.threadID = threadID
        self.name = name
        self.serialConnection = serial.Serial()
        #TODO Add config lock to main
        self.c_lock = c_lock
        self.saveFile = None
        self.saveFileBU = None

    def setParameteres(self, parameters):
        self.serialConnection.bytesize = parameters[0]
        self.serialConnection.parity = parameters[1]
        self.serialConnection.stopbits = parameters[2]
        self.serialConnection.baudrate = parameters[3]
        self.serialConnection.port = parameters[4]
    #TODO Change d_lock for c_lock in here and main
    def getJson(self):
        self.d_lock.acquire()
        try:
            with open(self.saveFile) as json_file:
                self.config = json.load(json_file)
        except FileNotFoundError:
            self.config = {}
        self.d_lock.release()
    def setJson(self):
        self.d_lock.acquire()
        #Data is initially written to newData to avoid loss of values if program is closed unexpectedly
        with open(self.saveFile, 'w') as outfile:
            json.dump(self.config, outfile, indent=4)
        with open(self.saveFileBU, 'w') as outfile:
            json.dump(self.config, outfile, indent=4)
        self.d_lock.release()

    def getHeader(self):
        #TODO Convert byte to string with tables
        self.config = {}

        startline = self.serialConnection.readline()
        print(startline)
        if(startline != b"start\n"):
            return 1
        nSlaves = self.serialConnection.read(1)[0]
        print(nSlaves)
        for n1 in range(nSlaves):
            slave = "Slave"+str(n1)
            self.config[slave] = {}
            address = self.serialConnection.read(1)[0]
            print(address, "address")
            self.config[slave]['address'] = address
            microprocessor = self.serialConnection.read(1)[0]
            print(microprocessor, "microprocessor")
            self.config[slave]['microprocessor'] = microprocessor
            status = self.serialConnection.read(1)[0]
            print(status, "status")
            self.config[slave]['status'] = status
            position = self.serialConnection.read(1)[0]
            print(position, "position")
            self.config[slave]['position'] = position
            unit = self.serialConnection.read(1)[0]
            print(unit, "unit")
            self.config[slave]['unit'] = unit
            self.config[slave]['sensors'] = {}
            nSensors = self.serialConnection.read(1)[0]
            print(nSensors, "nSensors")
            for n2 in range(nSensors):
                sensor = "Sensor"+str(n2)
                self.config[slave]['sensors'][sensor] = {}
                id = self.serialConnection.read(1)[0]
                print(id, "id nSensors")
                self.config[slave]['sensors'][sensor]["id"] = id
                status = self.serialConnection.read(1)[0]
                print(status, "status nSensors")
                self.config[slave]['sensors'][sensor]["status"] = status
                restval_byte = self.serialConnection.read(2)
                restval = restval_byte[0] + restval_byte[1]*256
                print(restval, "restval nSensors")
                self.config[slave]['sensors'][sensor]["restval"] = restval
        endline = self.serialConnection.readline()
        print(endline)
        if(endline != b"end\n"):
            return 1

        self.setJson()

        return 0

    def getEntry(self):
        line = self.serialConnection.readline()
        x = re.findall("S[0-9]S[0-9]D]*", str(line))
        if (x):
            slave = x[0][0:2]
            sensor = x[0][2:4]
            sizeD = self.serialConnection.read(1)
            nBytes = sizeD[0]
            data = self.serialConnection.read(nBytes)
            timeHeader = self.serialConnection.read(6)

            # print(line)
            # print(sizeD[0])
            # print(data)
            # print(timeHeader)

            reString = slave + sensor + "T*"
            x = re.findall(reString, str(timeHeader))
            if (x):  # checks if time array has same info as data
                sizeT = self.serialConnection.read(1)
                nBytes = sizeT[0]
                timeData = self.serialConnection.read(nBytes)
            else:
                print("Skipped because D == T not true")
                return 1
        else:
            print("Skipped because x not true")
            return  1
        if (nBytes == 0):
            print("No data in package")
            return 1
        print(line)
        print(sizeD[0])
        print(data)
        print(timeHeader)
        print(sizeT[0])
        print(timeData)
        sData = []
        tData = []
        # convert data from byte array to int list
        for c in range(0, len(data), 2):
            # int.from_bytes(data[c]+data[c+1], "little")
            print(data[c] + data[c + 1] * 256)
            sData.append(data[c] + data[c + 1] * 256)
        for c in timeData:
            tData.append(c)
        return (slave, sensor, sData, tData)

    def run(self):
        self.getJson()
        self.serialConnection.open()
        tries = 0
        if(self.serialConnection.is_open):
            while self.getHeader():
                tries += 1
                self.serialConnection.close()
                self.serialConnection.open()
                if(tries>5):
                    print("Failed to read header after",tries,"times.")
                    self.closeEvent.set()
                    self.closedSignal.emit()
                    break

            if not self.closeEvent.is_set():
                print("Succeeded to read header after", tries, "times.")

            while not self.closeEvent.is_set():

                entry = self.getEntry()

                if not entry == 1:
                    slave = entry[0]
                    sensor = entry[1]
                    sData = entry[2]
                    tData = entry[3]

                    #Check if Slave exists in DB
                    if slave not in self.config:
                        print("Skipped because slave doesnt exist in setup")
                        continue #Skip if slave doesnt exist in setup
                    #Check if Sensor exists in DB
                    if sensor not in self.config[slave]:
                        print("Skipped because sensor doesnt exist in setup")
                        continue  # Skip if sensor doesnt exist in setup
                    if 'entries' not in self.config[slave][sensor]:
                        self.config[slave][sensor]['entries'] = []

                    currentid = len(self.config[slave][sensor]['entries'])

                    newEntry = {'id': currentid, 'size': len(sData), 'data': sData, 'time': tData}

                    self.config[slave][sensor]['entries'].append(newEntry)

                    self.setJson()

                    self.addEntrySignal.emit()


        self.serialConnection.close()