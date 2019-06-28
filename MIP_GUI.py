# -*- coding: latin-1 -*-
from operator import itemgetter
import queue
import sys
import os
from pathlib import Path
import threading
import datetime
from serialListener import *
from dataProcess import *
from util import *
from math import ceil
# for UI
from PyQt5 import QtWidgets, QtGui, QtCore

try:
    from QtCore import QString
except ImportError:
    QString = str
from PyQt5.QtCore import QThread, pyqtSignal
from GUI.MI_GUI_04 import Ui_MainWindow
from pyqtgraph import *

class Sensor():
    def __init__(self, id, parameters):
        self.sensor = id
        self.function = parameters['function']
        self.status = parameters['status']
        self.restval = parameters['restval']
        self.position = parameters['position']

    def __repr__(self):
        return f"Sensor: {self.sensor}\n\t\t\tFunction: {self.function}\n\t\t\tStatus: {self.status}\n\t\t\tRestval: {self.restval}\n\t\t\tPosition: {self.position}"

    def __str__(self):
        return f"Sensor: {self.sensor}\n\t\t\tFunction: {self.function}\n\t\t\tStatus: {self.status}\n\t\t\tRestval: {self.restval}\n\t\t\tPosition: {self.position}"

class Module():
    def __init__(self, id, parameters):
        self.module = id
        self.address = parameters['address']
        self.microprocessor = parameters['microprocessor']
        self.status = parameters['status']
        self.position = parameters['position']
        self.unit = parameters['unit']
        self.sensors_list = []
        self.setupSensors(parameters['sensors'])

    def setupSensors(self, sensors):
        for sensor in sensors:
            self.sensors_list.append(Sensor(sensor, sensors[sensor]))

    def __repr__(self):
        fstr = f"Module: {self.module}\n\tAddress: {self.address}\n\tMicroprocessor: {self.microprocessor}\n\tStatus: {self.status}\n\tPosition {self.position}\n\tUnit: {self.unit}\n\tSensors:"
        for sensor in self.sensors_list:
            fstr = fstr + f"\n\t\t{sensor}"
        return fstr

    def __str__(self):
        fstr = f"Module: {self.module}\n\tAddress: {self.address}\n\tMicroprocessor: {self.microprocessor}\n\tStatus: {self.status}\n\tPosition {self.position}\n\tUnit: {self.unit}\n\tSensors:"
        for sensor in self.sensors_list:
            fstr = fstr + f"\n\t\t{sensor}"
        return fstr

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        # PyQtGraph config
        setConfigOption('background', 'w')
        setConfigOption('foreground', 'k')

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setupVariables()
        self.setupCallbacks()
        self.setupTimers()

    def setupVariables(self):
        #DATA
        self.headerInfo = None
        self.rawEntries = list()

        #Serial thread
        self.serialListenerThread = serialThread(1, "SerialListener")
        self.serialListenerThread.addRawEntrySignal[list].connect(self.addRawEntry)
        self.serialListenerThread.closedSignal.connect(self.serialThreadClosed)
        self.serialListenerThread.gotHeaderSignal[dict].connect(self.serialThreadGotHeader)

        self._isConnected = False

        #Process thread
        self.processQueue = queue.Queue()

    def setupCallbacks(self):
        self.ui.targetComConnectButton.clicked.connect(self.establishConnection)

    def setupTimers(self):
        self.comlist_qtimer = QtCore.QTimer(self)
        self.comlist_qtimer.timeout.connect(self.getCOMList)
        self.comlist_qtimer_interval = round(1000/10) #10hz
        self.comlist_qtimer.start(self.comlist_qtimer_interval)

    def getCOMList(self):

        #Searches ports for available COMs
        comlist = [comport.device for comport in serial.tools.list_ports.comports()]

        #Updates Current COM and COM selection combobox
        if len(comlist) != self.ui.targetComCB.count():
            self.ui.targetComCB.clear()
            self.ui.targetComCB.addItems(comlist)
            self.serialCOM = self.ui.targetComCB.currentText()

        if self.ui.targetComCB.count() == 0:
            self.serialCOM = None

        #Changes speed of search depending on amount of COMs available found

        if len(comlist)>0 and self.comlist_qtimer_interval == 100:
            self.comlist_qtimer_interval = round(1000/0.5) #0.5hz
            self.comlist_qtimer.stop()
            self.comlist_qtimer.start(self.comlist_qtimer_interval)
        else:
            self.comlist_qtimer_interval = round(1000/10) #10hz
            self.comlist_qtimer.stop()
            self.comlist_qtimer.start(self.comlist_qtimer_interval)


    def establishConnection(self):
        if self._isConnected:
            self.closeSerialThread()
        else:
            self.comlist_qtimer.stop()
            self.rawEntries = []
            self.startSerialThread()

    def startSerialThread(self):
        # Signal from Thread

        self.serialListenerThread.setPort(self.serialCOM)
        self.serialListenerThread.start()
        self.ui.targetComConnectButton.setEnabled(False)

    def closeSerialThread(self):
        # Set event flag to close thread
        self.serialListenerThread.stop()
        self.ui.targetComConnectButton.setEnabled(False)

    def serialThreadClosed(self):
        self._isConnected = False
        self.ui.targetComConnectButton.setEnabled(True)
        self.ui.targetComConnectButton.setText("Connect")
        self.comlist_qtimer.start(self.comlist_qtimer_interval)
        self.exportRawData()

    def serialThreadGotHeader(self, header):
        #Setup tabs
        self.headerInfo = header
        self.setupGraphTabs()
        #Update connection states
        self._isConnected = True
        self.ui.targetComConnectButton.setEnabled(True)
        self.ui.targetComConnectButton.setText("Disconnect")

    def addRawEntry(self, data):
        self.rawEntries.append(data)
        #print("rawEntries size:", sys.getsizeof(self.rawEntries))
        #Display/process data
        print(data)

    def setupGraphTabs(self):
        self.modules_list = []
        if not self.headerInfo == None:
            for n_slave in self.headerInfo:
                self.modules_list.append(Module(n_slave, self.headerInfo[n_slave]))

    def exportRawData(self):
        container = {}

        for entry in self.rawEntries:
            if entry[1] not in container:
                container[entry[1]] = [[], []]
            container[entry[1]][0] = container[entry[1]][0] + entry[2]
            container[entry[1]][1] = container[entry[1]][1] + entry[3]

        maxlen = 0
        for e in container:
            if max(len(container[e][0]), len(container[e][1])) > maxlen:
                maxlen = max(len(container[e][0]), len(container[e][1]))
        for e in container:
            if e != 50 and e != 97:
                for i in range(len(container[e][0])):
                    container[e][0][i] = round((container[e][0][i]*5)/1024,3)
                    container[e][1][i] = float(container[e][1][i])
            else:
                for i in range(len(container[e][0])):
                    container[e][0][i] = float(container[e][0][i])
                    container[e][1][i] = float(container[e][1][i])
        with open('rawdata.txt', 'w') as file:
            print(maxlen)
            header = ""
            for key in container.keys():
                header = header + "S" + str(key) + " t "
            header = header + "\n"
            file.write(header)
            for i in range(maxlen):
                line = ""
                for e in container:
                    try:
                        line = line + str(container[e][0][i]) + " " + str(container[e][1][i]) + " "
                    except Exception:
                        line = line + "- - "
                line = line[:-1] + "\n"
                file.write(line)


def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
