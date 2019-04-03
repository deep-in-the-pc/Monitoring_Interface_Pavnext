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
from gui.MI_GUI_02 import Ui_MainWindow


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #Configs
        with open("config.cfg") as cfg:
            self.cfgs = json.load(cfg)
        self.saveFile = self.cfgs['SaveFile']
        self.saveFileBackup = self.cfgs['SaveFileBU']

        #configure serial connection
        self.d_lock = threading.Lock()

        self.serialListenerThread = serialThread(1, "SerialListener", self.d_lock)

        self.serialConnectionParameters = list()
        self.serialConnectionParameters.append(serial.EIGHTBITS)
        self.serialConnectionParameters.append(serial.PARITY_NONE)
        self.serialConnectionParameters.append(serial.STOPBITS_ONE)
        self.serialConnectionParameters.append(57600)


        #initialize combo box
        self.getCOMList()

        if self.ui.targetComCB.currentText()=='':
            self.serialCOM = None
        else:
            self.serialCOM = self.ui.targetComCB.currentText()


        #Filters
        self.slaves = {}

        self.ui.slavesComboBox.addItem("All")
        self.ui.sensorsComboBox.addItem("All")
        self.currentSlaveFilter = "All"
        self.currentSensorFilter = "All"

        #Add entries to list
        self.addEntries()

        #targetComConnectButton Callback
        self.ui.targetComConnectButton.clicked.connect(self.targetConnectionCB)
        #updateCOMButton CallBack
        self.ui.updateCOMButton.clicked.connect(self.getCOMList)
        #combo box Callback
        self.ui.targetComCB.activated[str].connect(self.onTargetComCBActivated)
        self.ui.slavesComboBox.activated[str].connect(self.slavesComboBoxCB)
        self.ui.sensorsComboBox.activated[str].connect(self.sensorsComboBoxCB)
        #Group box Callback
        self.ui.toolsFiltersGroupBox.toggled.connect(self.updateFilterComboBoxes)

        #MenuBar Callback
        self.ui.actionClear_Graph.triggered.connect(self.actionClearGraphCB)
        self.ui.actionSave_File.triggered.connect(self.actionSave_FileCB)
        self.ui.actionOpen_File.triggered.connect(self.actionOpen_FileCB)



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
        self.ui.targetComCB.clear()
        self.ui.targetComCB.addItems([comport.device for comport in serial.tools.list_ports.comports()])
        self.serialCOM = self.ui.targetComCB.currentText()

    def targetConnectionCB(self):
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

    def updateFilterComboBoxes(self):

        if self.ui.toolsFiltersGroupBox.isChecked():
            if(self.ui.slavesComboBox.currentText() == "All"):
                self.ui.sensorsComboBox.setEnabled(False)
        else:
            self.currentSensorFilter = "All"
            self.currentSlaveFilter = "All"

        self.ui.slavesComboBox.clear()
        self.ui.slavesComboBox.addItem("All")
        self.ui.slavesComboBox.addItems(self.slaves.keys())
        self.ui.slavesComboBox.setCurrentIndex(self.ui.slavesComboBox.findText(self.currentSlaveFilter)) #Keep same filter as before
        self.ui.sensorsComboBox.clear()
        self.ui.sensorsComboBox.addItem("All")
        if self.currentSlaveFilter != "All":
            self.ui.sensorsComboBox.addItems(self.slaves[self.currentSlaveFilter])
            self.ui.sensorsComboBox.setCurrentIndex(self.ui.sensorsComboBox.findText(self.currentSensorFilter)) #Keep same filter as before
        self.filterEntries()

    def slavesComboBoxCB(self, text):
        self.currentSlaveFilter = text
        if text != "All":
            self.ui.sensorsComboBox.setEnabled(True)
            self.currentSensorFilter = "All"
        else:
            self.ui.sensorsComboBox.setEnabled(False)

        self.updateFilterComboBoxes()
        self.filterEntries()

    def sensorsComboBoxCB(self, text):
        self.currentSensorFilter = text
        self.filterEntries()

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




    def actionClearGraphCB(self):
        print("ping")
        self.ui.graphFrame.clearGraph()

    def actionSave_FileCB(self):
        self.getSavefiles()
        self.addEntries()

    def actionOpen_FileCB(self):
        self.getOpenfiles()
        self.addEntries()


def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
