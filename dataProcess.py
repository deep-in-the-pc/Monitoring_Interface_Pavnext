
import threading
import serial.tools.list_ports
#for storage
import json
import time
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal

#from gui.graphUtil import *


class processThread (QThread):

    addEntrySignal = pyqtSignal(dict)
    closedSignal = pyqtSignal()

    def __init__(self, threadID, name, d_lock, c_lock):
        QThread.__init__(self)
        self._isRunning = True
        self.newRawEvent = threading.Event()
        self.threadID = threadID
        self.name = name
        self.d_lock = d_lock
        self.c_lock = c_lock
        self.rawConfigFile = None
        self.rawConfigFileBU = None
        self.dataFile = None
        self.dataFileBU = None
    def getRawJson(self):
        self.c_lock.acquire()
        try:
            with open(self.rawConfigFile) as json_file:
                self.config = json.load(json_file)
        except json.decoder.JSONDecodeError:
            try:
                with open(self.rawConfigFileBU) as json_file:
                    self.config = json.load(json_file)
            except FileNotFoundError:
                self.config = None
        except FileNotFoundError:
            self.config = None

        self.c_lock.release()
    def getDataJson(self):
        self.d_lock.acquire()
        try:
            with open(self.dataFile) as json_file:
                self.entries = json.load(json_file)
        except Exception:
            try:
                with open(self.dataFileBU) as json_file:
                    self.entries = json.load(json_file)
            except Exception:
                self.entries = {}
        self.d_lock.release()

    def setJson(self):
        self.d_lock.acquire()
        #Data is initially written to newData to avoid loss of values if program is closed unexpectedly
        with open(self.dataFile, 'w') as outfile:
            json.dump(self.entries, outfile, indent=4)
        with open(self.dataFileBU, 'w') as outfile:
            json.dump(self.entries, outfile, indent=4)
        self.d_lock.release()


    def run(self):
        self.getRawJson()
        self.getDataJson()
        while self._isRunning:
            if (self.config == None):
                self.getRawJson()
            if self.newRawEvent.is_set():

                toBeUpdated = {}
                self.getRawJson()
                self.newRawEvent.clear()
                for slaveKey in self.config:
                    toBeUpdated[slaveKey]=[]
                    if slaveKey not in self.entries:
                        self.entries[slaveKey] = {"sensors":{}}
                    for sensorKey in self.config[slaveKey]['sensors']:
                        if sensorKey not in self.entries[slaveKey]['sensors']:
                            self.entries[slaveKey]['sensors'][sensorKey] = {}
                        if 'entries' not in self.config[slaveKey]['sensors'][sensorKey]:
                            self.config[slaveKey]['sensors'][sensorKey]['entries'] = []
                        for sensorDataEntry in self.config[slaveKey]['sensors'][sensorKey]['entries']:
                            if 'dataList' not in self.entries[slaveKey]['sensors'][sensorKey]:
                                self.entries[slaveKey]['sensors'][sensorKey]['dataList'] = list()
                            if 'dataListWin' not in self.entries[slaveKey]['sensors'][sensorKey]:
                                self.entries[slaveKey]['sensors'][sensorKey]['dataListWin'] = dict()
                            if sensorDataEntry['id'] in self.entries[slaveKey]['sensors'][sensorKey]['dataList']:
                                continue
                            else:
                                if sensorKey not in toBeUpdated[slaveKey]:
                                    toBeUpdated[slaveKey].append(sensorKey)
                                self.entries[slaveKey]['sensors'][sensorKey]['dataList'].append(sensorDataEntry['id'])

                                (dataR, dataNR) = dataConverter(self.config[slaveKey], sensorKey, sensorDataEntry['id'])

                                if(dataR):
                                    if 'dataR' not in self.entries[slaveKey]['sensors'][sensorKey]:
                                        self.entries[slaveKey]['sensors'][sensorKey]['dataR'] = []
                                    self.entries[slaveKey]['sensors'][sensorKey]['dataR'] = self.entries[slaveKey]['sensors'][sensorKey]['dataR'] + dataR
                                if(dataNR):
                                    if 'dataNR' not in self.entries[slaveKey]['sensors'][sensorKey]:
                                        self.entries[slaveKey]['sensors'][sensorKey]['dataNR'] = []
                                    self.entries[slaveKey]['sensors'][sensorKey]['dataNR'] = self.entries[slaveKey]['sensors'][sensorKey]['dataNR'] + dataNR
                                if('time' not in self.entries[slaveKey]['sensors'][sensorKey]):
                                    self.entries[slaveKey]['sensors'][sensorKey]['time'] = []
                                time = self.config[slaveKey]['sensors'][sensorKey]["entries"][sensorDataEntry['id']]['time']
                                self.entries[slaveKey]['sensors'][sensorKey]['time'] = self.entries[slaveKey]['sensors'][sensorKey]['time'] + time
                                self.entries[slaveKey]['sensors'][sensorKey]['dataListWin'][sensorDataEntry['id']] = (time[0], time[-1], min(dataNR), max(dataNR))
                self.setJson()

                for i in toBeUpdated:
                    if(len(toBeUpdated[i])>0):
                        self.addEntrySignal.emit(toBeUpdated)
                        break
            QtWidgets.QApplication.processEvents()
    def stop(self):
        self._isRunning = False