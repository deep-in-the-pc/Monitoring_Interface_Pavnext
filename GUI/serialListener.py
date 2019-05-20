
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

    addRawEntrySignal = pyqtSignal(list)
    closedSignal = pyqtSignal()

    def __init__(self, threadID, name, c_lock):
        QThread.__init__(self)
        self.closeEvent = threading.Event()
        self.threadID = threadID
        self.name = name
        self.serialConnection = serial.Serial()
        self.c_lock = c_lock
        self.saveRawFile = None
        self.saveRawFileBU = None

    def setParameteres(self, parameters):
        self.serialConnection.bytesize = parameters[0]
        self.serialConnection.parity = parameters[1]
        self.serialConnection.stopbits = parameters[2]
        self.serialConnection.baudrate = parameters[3]
        self.serialConnection.port = parameters[4]
    def getJson(self):
        self.c_lock.acquire()
        try:
            with open(self.saveRawFile) as json_file:
                self.config = json.load(json_file)
        except json.decoder.JSONDecodeError:
            try:
                with open(self.saveRawFileBU) as json_file:
                    self.config = json.load(json_file)
            except Exception:
                None
        except FileNotFoundError:
            #if no file is found no entries are added
            None
        self.c_lock.release()
    def setJson(self):
        self.c_lock.acquire()
        #Data is written twice to avoid loss of values if program is closed unexpectedly
        with open(self.saveRawFile, 'w') as outfile:
            json.dump(self.config, outfile, indent=4)
        with open(self.saveRawFileBU, 'w') as outfile:
            json.dump(self.config, outfile, indent=4)
        self.c_lock.release()

    def getHeader(self):
        packet = bytearray()
        packet.append(0x42)
        nbyte = self.serialConnection.write(packet)
        print(nbyte)
        self.config = {}
        #print("Starting read...")
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
        #print(endline)
        if(endline != b"end\n"):
            return 1
        #print(self.config)
        self.setJson()

        return 0

    def getEntry(self):
        line = self.serialConnection.read(6)
        #print(line)
        x = re.findall("DATA", str(line[0:4]))
        if (x):
            slave_pos = line[4]
            sensor_pos = line[5]
            # print("Slave_pos", slave_pos)
            # print("Sensor_pos", sensor_pos)
            sizeD = self.serialConnection.read(2)
            # print(sizeD)
            nBytesd = (sizeD[0] + sizeD[1] * 256)*2
            #print(nBytesd)
            data = self.serialConnection.read(nBytesd)

            #print(line)
            #print("Slave_pos", slave_pos)
            #print("Sensor_pos", sensor_pos)
            #print(sizeD)
            #print(nBytesd)
            #print(data)

            line = self.serialConnection.read(4)
            x = re.findall("TIME", str(line[0:4]))
            # print(line)
            if (x):

                sizeT = self.serialConnection.read(2)

                nBytest = (sizeT[0] + sizeT[1] * 256)*2
                tempo = self.serialConnection.read(nBytest)

                # print(line)
                # print(sizeT)
                # print(nBytest)
                # print(tempo)
            else:
                print("Didn't receive time")
                return 1

                if (nBytesd == 0):
                    print("No data in package")
                    return 1
                if (nBytesd != nBytest):
                    print("Data and Time differ in size")
                    return 1

            sData = []
            sTime = []
            # convert data from byte array to int list
            #print("=================STARTED==================")
            for c in range(0, len(data), 2):
                sData.append(data[c] + data[c + 1] * 256)
            for c in range(0, len(tempo), 2):
                segundos = tempo[c+1]>>2
                milisegundos = (tempo[c+1] & 3) * 256 + tempo[c]
                sTime.append(segundos*1000+milisegundos)
            #print("=================FINISHED==================")
            return (slave_pos, sensor_pos, sData, sTime)
        return 1

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
                    slave_pos = entry[0]
                    sensor_pos = entry[1]
                    sData = entry[2]
                    sTime = entry[3]

                    #Check if Slave exists in DB
                    if slave_pos not in self.config:
                        print("Skipped because slave:", slave_pos, "doesnt exist in setup")
                        continue #Skip if slave doesnt exist in setup
                    #Check if Sensor exists in DB
                    if sensor_pos not in self.config[slave_pos]["sensors"]:
                        print("Skipped because sensor:", sensor_pos, " doesnt exist in setup")
                        continue  # Skip if sensor doesnt exist in setup
                    if 'entries' not in self.config[slave_pos]["sensors"][sensor_pos]:
                        self.config[slave_pos]["sensors"][sensor_pos]['entries'] = []

                    currentid = len(self.config[slave_pos]["sensors"][sensor_pos]['entries'])

                    newEntry = {'id': currentid, 'size': len(sData), 'data': sData, 'time': sTime}

                    self.config[slave_pos]["sensors"][sensor_pos]['entries'].append(newEntry)

                    self.setJson()
                    #print("inside serial", slave_pos, sensor_pos)
                    self.addRawEntrySignal.emit([slave_pos, sensor_pos])
                    #print("================ENTRY ADDED================")

        self.serialConnection.close()
        #print("serialListener", self.serialConnection.is_open)