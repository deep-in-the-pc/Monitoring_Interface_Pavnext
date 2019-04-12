
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

    def __init__(self, threadID, name, d_lock, c_lock):
        QThread.__init__(self)
        self.closeEvent = threading.Event()
        self.threadID = threadID
        self.name = name
        self.serialConnection = serial.Serial()
        self.d_lock = d_lock
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

    def getJson(self):
        self.d_lock.acquire()
        try:
            with open(self.saveFile) as json_file:
                self.Entries = json.load(json_file)
        except FileNotFoundError:
            self.Entries = {}
        self.d_lock.release()
    def setJson(self):
        self.d_lock.acquire()
        #Data is initially written to newData to avoid loss of values if program is closed unexpectedly
        with open(self.saveFile, 'w') as outfile:
            json.dump(self.Entries, outfile, indent=4)
        with open(self.saveFileBU, 'w') as outfile:
            json.dump(self.Entries, outfile, indent=4)
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

        self.c_lock.acquire()
        #Data is initially written to newData to avoid loss of values if program is closed unexpectedly
        with open("C:/Users/deman/PycharmProjects/Monitoring_Interface_Pavnext/GUI/headerconfig.json", 'w') as outfile:
            json.dump(self.config, outfile, indent=4)

        self.c_lock.release()
        return 0


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

                #TODO Get entries from master
                None
                # sData = []
                # tData = []
                # #convert data from byte array to int list
                # for c in range(0, len(data), 2):
                #     #int.from_bytes(data[c]+data[c+1], "little")
                #     print(data[c] + data[c+1]*256)
                #     sData.append(data[c] + data[c+1]*256)
                # for c in timeData:
                #     tData.append(c)
                #
                # #Check if Slave exists in DB
                # if slave not in self.Entries:
                #     self.Entries[slave] = {}
                # #Check if Sensor exists in DB
                # if sensor not in self.Entries[slave]:
                #     self.Entries[slave][sensor] = []
                #
                # currentid = len(self.Entries[slave][sensor])
                #
                # newEntry = {'id': currentid, 'size': nBytes,'data': sData, 'time': tData}
                #
                # self.Entries[slave][sensor].append(newEntry)
                #
                # #print(self.Entries)
                #
                # self.setJson()
                #
                # self.addEntrySignal.emit()


        self.serialConnection.close()