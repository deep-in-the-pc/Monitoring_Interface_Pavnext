
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

    def __init__(self, threadID, name, d_lock):
        QThread.__init__(self)
        self.event = threading.Event()
        self.threadID = threadID
        self.name = name
        self.serialConnection = serial.Serial()
        self.d_lock = d_lock
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
    def run(self):
        self.getJson()
        self.serialConnection.open()
        if(self.serialConnection.is_open):
            while not self.event.is_set():
                line = self.serialConnection.readline()
                x = re.findall("S[0-9]S[0-9]D]*", str(line))
                slave = x[0][0:2]
                sensor = x[0][2:4]
                #print(line)
                if(x):
                    #print(x[0])
                    nBytes = self.serialConnection.read(2)[0]
                    data = self.serialConnection.read(nBytes)

                    timeHeader = self.serialConnection.read(6)

                    reString = slave+sensor+"T*"
                    x = re.findall(reString, str(timeHeader))
                    if(x): #checks if time array has same info as data array
                        nBytes = self.serialConnection.read(2)[0]
                        timeData = self.serialConnection.read(nBytes)
                    else:
                        print("skipped because D == T not true")
                        continue
                else:
                    print("skipped because x not true")
                    continue

                sData = []
                tData = []
                #convert data from byte array to int list
                for c in data:
                    sData.append(c)
                for c in timeData:
                    tData.append(c)

                #Check if Slave exists in DB
                if slave not in self.Entries:
                    self.Entries[slave] = {}
                #Check if Sensor exists in DB
                if sensor not in self.Entries[slave]:
                    self.Entries[slave][sensor] = []

                currentid = len(self.Entries[slave][sensor])

                newEntry = {'id': currentid, 'size': nBytes,'data': sData, 'time': tData}

                self.Entries[slave][sensor].append(newEntry)

                print(self.Entries)

                self.setJson()

                self.addEntrySignal.emit()

        self.serialConnection.close()