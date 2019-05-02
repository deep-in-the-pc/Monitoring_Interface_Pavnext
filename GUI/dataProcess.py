
#for serial comms
import threading
import serial.tools.list_ports
#for storage
import json
import time

from PyQt5.QtCore import QThread, pyqtSignal



class processThread (QThread):

    addEntrySignal = pyqtSignal()
    closedSignal = pyqtSignal()

    def __init__(self, threadID, name, d_lock, c_lock):
        QThread.__init__(self)
        self.closeEvent = threading.Event()
        self.threadID = threadID
        self.name = name
        self.serialConnection = serial.Serial()
        self.d_lock = d_lock
        self.c_lock = c_lock
        self.configFile = None
        self.dataFile = None
        self.dataFileBU = None

    def getJson(self):
        self.c_lock.acquire()
        try:
            with open(self.configFile) as json_file:
                self.config = json.load(json_file)
        except FileNotFoundError:
            self.config = None
            #TODO Stop process
        self.c_lock.release()
    def setJson(self):
        self.d_lock.acquire()
        #Data is initially written to newData to avoid loss of values if program is closed unexpectedly
        with open(self.dataFile, 'w') as outfile:
            json.dump(self.data, outfile, indent=4)
        with open(self.dataFileBU, 'w') as outfile:
            json.dump(self.data, outfile, indent=4)
        self.d_lock.release()


    def run(self):
        self.getJson()
        if(self.config != None):
            while not self.closeEvent.is_set():
                    #TODO add interate entries
                    #for entry in config
                        #TODO Check type of entry
                        #TODO Process for type of entry
                        #TODO Save processed data

                    self.setJson()

                    self.addEntrySignal.emit()


        self.serialConnection.close()