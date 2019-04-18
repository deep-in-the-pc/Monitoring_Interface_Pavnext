# -*- coding: latin-1 -*-

import sys
import os
import threading
import datetime
from serialListener import *
from time import sleep
from util import *
from math import ceil
#for UI
from PyQt5 import QtWidgets, QtGui, QtCore
try:
    from QtCore import QString
except ImportError:
    QString = str
from PyQt5.QtCore import QThread, pyqtSignal
from gui.MI_GUI_0201 import Ui_MainWindow


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #Configs
        try:
            with open("config.cfg") as cfg:
                self.cfgs = json.load(cfg)
            self.saveFile = self.cfgs['SaveFile']
            self.saveFileBackup = self.cfgs['SaveFileBU']
        except FileNotFoundError:
            self.saveFile = None
            self.saveFileBackup = None

        try:
            with open("slaveconfigs.json") as scfg:
                self.scfgs = json.load(scfg)
            self.ignoreSConfigs = False
            self.slaveDecode = self.scfgs['slaves']
            self.prototypesDecode = self.scfgs['prototypes']
        except FileNotFoundError:
            self.ignoreSConfigs = True
        #self.ignoreSConfigs = True

        #TODO Add Edit and Add option to Slave config file

        #configure serial connection
        self.d_lock = threading.Lock()

        self.serialListenerThread = serialThread(1, "SerialListener", self.d_lock)

        self.serialConnectionParameters = list()
        self.serialConnectionParameters.append(serial.EIGHTBITS)
        self.serialConnectionParameters.append(serial.PARITY_NONE)
        self.serialConnectionParameters.append(serial.STOPBITS_ONE)
        self.serialConnectionParameters.append(57600)


        #Add check boxes for each COM
        self.addAvailableCOMs()

        #targetComConnectButton Callback
        self.ui.targetComConnectButton.clicked.connect(self.targetConnectionCB)
        #updateCOMButton CallBack
        self.ui.updateCOMButton.clicked.connect(self.addAvailableCOMs)

    def startThread(self):
        self.serialListenerThread = serialThread(1, "SerialListener", self.d_lock)

        #Signal from Thread
        self.serialListenerThread.addEntrySignal.connect(self.addEntry)

        self.serialConnectionParameters.append(self.serialCOM)
        self.serialListenerThread.setParameteres(self.serialConnectionParameters)
        self.serialListenerThread.saveFile = self.saveFile
        self.serialListenerThread.saveFileBU = self.saveFileBackup
        self.serialListenerThread.start()

    #COMMUNICATION

    def getCOMList(self):
        return [comport.device for comport in serial.tools.list_ports.comports()]

    def addAvailableCOMs(self):
        self.COMList = self.getCOMList()
        if(self.ui.groupBoxCOM.layout()):
            while self.ui.groupBoxCOM.grid.count()-1:
                child = self.ui.groupBoxCOM.grid.takeAt(1)
                if child.widget():
                    child.widget().deleteLater()
                print(self.ui.groupBoxCOM.grid.count())
        else:
            self.ui.groupBoxCOM.grid = QtWidgets.QGridLayout()
            self.ui.groupBoxCOM.grid.addWidget(QtWidgets.QLabel("Status"), 0, 1)
            self.ui.groupBoxCOM.setLayout(self.ui.groupBoxCOM.grid)

        if (self.COMList):
            for count, COM in enumerate(self.COMList):
                print(count, COM)
                try:
                    self.ui.groupBoxCOM.grid.addWidget(QtWidgets.QCheckBox(COM), count+1, 0)
                    self.ui.groupBoxCOM.grid.addWidget(QtWidgets.QLabel("Offline"), count+1, 1)
                except Exception as err:
                    print(err)


    def targetConnectionCB(self):
        if self.saveFileBackup == None or self.saveFile == None:
            self.getSavefiles()
            return
        if self.serialListenerThread.isRunning():
            self.closeConnetion()
            self.ui.targetComConnectButton.setText("Connect")
        elif(self.serialCOM != None):
            if(self.establishConnection()):
                # If connection is established set text as disconnect
                self.ui.targetComConnectButton.setText("Disconnect")

    def onTargetComCBActivated(self, text):
        if text != None:
            self.serialCOM = text

    def establishConnection(self):
        try:
            self.startThread()
            if self.serialListenerThread.isRunning():
                self.ui.connectionStatusLabel.setText("Connection Status: Online")
                return 1
            else:
                return 0
        except Exception as err:
            print(str(err))

    def closeConnetion(self):
        #Set event flag to close thread
        self.serialListenerThread.event.set()
        print(self.serialListenerThread.isRunning())
        self.ui.connectionStatusLabel.setText("Connection Status: Offline")


    def filterEntries(self):
        self.EntriesFiltered = {}
        if not self.ui.toolsFiltersGroupBox.isChecked():
            self.EntriesFiltered = self.Entries
        else:
            if self.currentSlaveFilter == "All":
                self.EntriesFiltered = self.Entries
            elif self.currentSensorFilter == "All":
                self.EntriesFiltered["S"+self.currentSlaveFilter[-1]] = self.Entries["S"+self.currentSlaveFilter[-1]]
            else:
                self.EntriesFiltered["S"+self.currentSlaveFilter[-1]] = {}
                self.EntriesFiltered["S"+self.currentSlaveFilter[-1]]["S"+self.currentSensorFilter[-1]] = self.Entries["S"+self.currentSlaveFilter[-1]]["S"+self.currentSensorFilter[-1]]

        self.ui.sensorEntryListWidget.clear()

        for key1, value1 in self.EntriesFiltered.items():
            for key2, value2 in value1.items():
                for entry in value2:
                    title=key1+key2+" "*(26-2*len(key1+key2))+str(entry['id'])+" "*(22-2*len(str(entry['id'])))+str(entry['size'])
                    self.ui.sensorEntryListWidget.addItem(title)

    def addEntry(self):
        #Used on trigger by thread signal
        self.d_lock.acquire()

        try:
            with open(self.saveFile) as json_file:
                self.Entries = json.load(json_file)
        except FileNotFoundError:
            #if no file is found no entries are added
            self.d_lock.release()
            return

        self.d_lock.release()

        self.slaves = {}
        for key1, value1 in self.Entries.items():
            self.slaves["Slave "+key1[-1]] = []
            for key2, value2 in value1.items():
                self.slaves["Slave "+key1[-1]].append("Sensor " + key2[-1])

        self.updateFilterComboBoxes()

        self.filterEntries()

    def addEntries(self):
        #Used on startup to fill in data
        self.d_lock.acquire()
        try:
            with open(self.saveFile) as json_file:
                self.Entries = json.load(json_file)
            print("got entries")
        except FileNotFoundError:
            #if no file is found no entries are added
            self.slaves = {}
            self.Entries = {}
            self.d_lock.release()
            self.updateFilterComboBoxes()

            self.filterEntries()
            return

        self.d_lock.release()

        self.slaves = {}
        for key1, value1 in self.Entries.items():
            self.slaves["Slave "+key1[-1]] = []
            for key2, value2 in value1.items():
                self.slaves["Slave "+key1[-1]].append("Sensor " + key2[-1])



        self.updateFilterComboBoxes()

        self.filterEntries()

    def getOpenfiles(self):
        dlg = QtWidgets.QFileDialog()
        filenames = dlg.getOpenFileName(parent=self, caption="Open File",filter="Json files (*.json)", directory='..\\Data\\')
        self.saveFile = filenames[0]

        self.saveFileBackup = self.saveFile[:-5]+"_BU.json"

        self.cfgs['SaveFile'] = self.saveFile
        self.cfgs['SaveFileBU'] = self.saveFileBackup

        with open("config.cfg", 'w') as cfg:
            json.dump(self.cfgs, cfg, indent=4)

    def getSavefiles(self):
        dlg = QtWidgets.QFileDialog()
        filenames = dlg.getSaveFileName(parent=self, caption="Save File",filter="Json files (*.json)",directory=datetime.datetime.now().strftime("..\\Data\\%Y-%m-%d_%H%M"))
        self.saveFile = filenames[0]
        self.saveFileBackup = self.saveFile[:-5]+"_BU.json"

        self.cfgs['SaveFile'] = self.saveFile
        self.cfgs['SaveFileBU'] = self.saveFileBackup

        with open("config.cfg", 'w') as cfg:
            json.dump(self.cfgs, cfg, indent=4)


def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
