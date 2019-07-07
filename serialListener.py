import os
#for serial comms
import multiprocessing
import serial.tools.list_ports
import serial
import re
from math import ceil
#for storage
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal


def processWorker(item):
    slave_pos = item[4]
    sensor_pos = item[5]
    # print("Slave_pos", slave_pos)
    # print("Sensor_pos", sensor_pos)
    sizeD = item[6:8]
    # print("sizeD", sizeD)
    nBytesd = (sizeD[0] + sizeD[1] * 256) * 2
    # print("nBytesd",nBytesd)
    data = item[8:8+nBytesd]
    # print("data", data)
    if item[8+nBytesd:12+nBytesd] != b"TIME":
        print("TIME stamp not where expected")
        return 1

    sizeT = item[12+nBytesd:14+nBytesd]
    # print("sizeT", sizeT)
    if sizeD != sizeT:
        print("Length of data and time differs")
        return 1

    nBytest = (sizeT[0] + sizeT[1] * 256) * 2
    # print("nBytest", nBytest)
    tempo = item[14+nBytesd:14+nBytesd+nBytest]
    # print("tempo", tempo)

    sData = []
    sTime = []
    # convert data from byte array to int list
    # print("=================STARTED==================")
    for c in range(0, len(data), 2):
        sData.append(data[c] + data[c + 1] * 256)
    for c in range(0, len(tempo), 2):
        sTime.append(tempo[c] + tempo[c + 1] * 256)
    # print("=================FINISHED==================")
    return (slave_pos, sensor_pos, sData, sTime)

class serialThread (QThread):

    gotHeaderSignal = pyqtSignal(dict)
    addRawEntrySignal = pyqtSignal(list)
    closedSignal = pyqtSignal()

    def __init__(self, threadID, name):
        QThread.__init__(self)
        self._isRunning = True
        self.threadID = threadID
        self.name = name

        self.setupSerialConnection()

        self._serialincdata = bytes()
        self.reData = re.compile(b"DATA")
        self.reEnd = re.compile(b"END")
        self.reTime = re.compile(b"TIME")

        if os.cpu_count()<=8:
            self.corecount = ceil(os.cpu_count()/2)
        else:
            self.corecount = 4


    def setParameters(self, parameters):
        self.serialConnection.bytesize = parameters[0]
        self.serialConnection.parity = parameters[1]
        self.serialConnection.stopbits = parameters[2]
        self.serialConnection.baudrate = parameters[3]
        self.serialConnection.port = parameters[4]

    def setPort(self, port):
        self.serialConnection.port = port

    def setupSerialConnection(self):
        self.serialConnection = serial.Serial()
        self.serialConnection.bytesize = serial.EIGHTBITS
        self.serialConnection.parity = serial.PARITY_NONE
        self.serialConnection.stopbits = serial.STOPBITS_ONE
        self.serialConnection.baudrate = 1000000

    def getHeader(self):
        packet = bytearray()
        packet.append(0x42)
        nbyte = self.serialConnection.write(packet)
        self.config = {}
        print("Starting read...",nbyte)
        startline = self.serialConnection.readline()
        #print(startline)
        if(startline != b"start\n"):
            return 1
        nSlaves = self.serialConnection.read(1)[0]
        #print(nSlaves)
        for n1 in range(nSlaves):
            address = self.serialConnection.read(1)[0]
            print(address, "address")
            microprocessor = self.serialConnection.read(1)[0]
            print(microprocessor, "microprocessor")
            status = self.serialConnection.read(1)[0]
            print(status, "status")
            position_m = self.serialConnection.read(1)[0]
            print(position_m, "position_m")
            unit = self.serialConnection.read(1)[0]
            print(unit, "unit")

            self.config[position_m] = {}
            self.config[position_m]['address'] = address
            self.config[position_m]['microprocessor'] = microprocessor
            self.config[position_m]['status'] = status
            self.config[position_m]['position'] = position_m
            self.config[position_m]['unit'] = unit
            self.config[position_m]['sensors'] = {}
            nSensors = self.serialConnection.read(1)[0]
            print(nSensors, "nSensors")
            for n2 in range(nSensors):
                function = self.serialConnection.read(1)[0]
                print(function, "function nSensors")
                status = self.serialConnection.read(1)[0]
                print(status, "status nSensors")
                restval_byte = self.serialConnection.read(2)
                restval = restval_byte[0] + restval_byte[1]*256
                print(restval, "restval nSensors")
                position_s = self.serialConnection.read(1)[0]
                print(position_s, "position_s")
                self.config[position_m]['sensors'][position_s] = {}
                self.config[position_m]['sensors'][position_s]["function"] = function
                self.config[position_m]['sensors'][position_s]["status"] = status
                self.config[position_m]['sensors'][position_s]["restval"] = restval
                self.config[position_m]['sensors'][position_s]["position"] = position_s
        endline = self.serialConnection.readline()
        if(endline != b"end\n"):
            return 1


        return 0

    def workerFinishedCB(self, entry):
        if not entry == 1:
            slave_pos = entry[0]
            sensor_pos = entry[1]
            sData = entry[2]
            sTime = entry[3]

            # Check if Slave exists in DB
            if slave_pos not in self.config:
                print("Skipped because slave:", slave_pos, "doesnt exist in setup")
                return  # Skip if slave doesnt exist in setup
            # Check if Sensor exists in DB
            if sensor_pos not in self.config[slave_pos]["sensors"]:
                print("Skipped because sensor:", sensor_pos, " doesnt exist in setup")
                return  # Skip if sensor doesnt exist in setup
            if 'entries' not in self.config[slave_pos]["sensors"][sensor_pos]:
                self.config[slave_pos]["sensors"][sensor_pos]['entries'] = []

            currentid = len(self.config[slave_pos]["sensors"][sensor_pos]['entries'])

            newEntry = {'id': currentid, 'size': len(sData), 'data': sData, 'time': sTime}

            self.config[slave_pos]["sensors"][sensor_pos]['entries'].append(newEntry)

            self.addRawEntrySignal.emit([slave_pos, sensor_pos, sData, sTime])


    def run(self):
        self._isRunning = True
        try:
            self.serialConnection.open()
        except serial.serialutil.SerialException as e:
            print(e)
        tries = 0
        if(self.serialConnection.is_open):
            while self.getHeader():
                tries += 1
                self.serialConnection.close()
                self.serialConnection.open()
                if(tries>5):
                    print("Failed to read header after",tries,"times.")
                    self._isRunning = False
                    break

            if self._isRunning:
                self.gotHeaderSignal.emit(self.config)

                self.processPool = multiprocessing.Pool(self.corecount)
                print("Succeeded to read header after", tries, "times.")
                while self._isRunning:
                    entry = 1
                    availablebytes = self.serialConnection.in_waiting
                    if availablebytes:
                        newdata = self.serialConnection.read(availablebytes)
                        #print(newdata)
                        self._serialincdata = self._serialincdata + newdata
                    endpos = self.reEnd.search(self._serialincdata)
                    if endpos != None:
                        datapos = self.reData.search(self._serialincdata)
                        inputdata = [self._serialincdata[datapos.start():endpos.end()]]
                        self._serialincdata = self._serialincdata[endpos.end():]
                        self.processPool.apply_async(processWorker, args=inputdata, callback=self.workerFinishedCB)
                    QtWidgets.QApplication.processEvents()
                self.processPool.close()
                self.processPool.join()
            self.serialConnection.close()

        self.closedSignal.emit()


    def stop(self):
        self._isRunning = False