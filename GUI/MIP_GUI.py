# -*- coding: latin-1 -*-

import sys
import os
import threading
import datetime
from serialListener import *
from dataProcess import *
from util import *
from math import ceil
#for UI
from PyQt5 import QtWidgets, QtGui, QtCore
try:
    from QtCore import QString
except ImportError:
    QString = str
from PyQt5.QtCore import QThread, pyqtSignal
from gui.MI_GUI_0301 import Ui_MainWindow
from pyqtgraph import *

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        #PyQtGraph config
        setConfigOption('background', 'w')
        setConfigOption('foreground', 'k')

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #Configs
        self.DataFolderPath = "C:/Users/deman/PycharmProjects/Monitoring_Interface_Pavnext/Data"
        try:
            with open("config.cfg") as cfg:
                self.cfgs = json.load(cfg)
            self.saveRawFile = self.cfgs['tempRawFile']
            self.saveRawFileBackup = self.cfgs['tempRawFileBU']
            self.saveDataFile = self.cfgs['tempFile']
            self.saveDataFileBU = self.cfgs['tempFileBU']
        except FileNotFoundError:
            self.saveRawFile = None
            self.saveRawFileBackup = None
            self.saveDataFile = None
            self.saveDataFileBU = None
        try:
            with open("slaveconfigs.json") as scfg:
                self.scfgs = json.load(scfg)
            self.ignoreSConfigs = False
            self.slaveDecode = self.scfgs['slaves']
            self.prototypesDecode = self.scfgs['prototypes']
        except FileNotFoundError:
            self.ignoreSConfigs = True
        #self.ignoreSConfigs = True

        self.ten_second_timer_flag = False
        self.toBeUpdated_count = 0
        self.graph_qtimer = QtCore.QTimer(self)
        self.graph_qtimer.timeout.connect(self.update_graph_timer_timeout)
        self.graph_qtimer.start(10000)

        self.total_toBeUpdated = {}
        #configure serial connection

        self.d_lock = threading.Lock()
        self.c_lock = threading.Lock()



        self.serialListenerThread = serialThread(1, "SerialListener", self.c_lock)
        self.processThread = processThread(2, "Process", self.d_lock, self.c_lock)

        self.serialConnectionParameters = list()
        self.serialConnectionParameters.append(serial.EIGHTBITS)
        self.serialConnectionParameters.append(serial.PARITY_NONE)
        self.serialConnectionParameters.append(serial.STOPBITS_ONE)
        #self.serialConnectionParameters.append(115200)
        self.serialConnectionParameters.append(500000)

        self.serialListenerThread.closeEvent.set()
        self.serialListenerThread.addRawEntrySignal[list].connect(self.addRawEntry)
        #Setup GraphicsLayoutWidget M10

        self.m10_w1 = self.ui.graphWindowM10.addPlot(row=0, col=0, title='Acel')
        self.m10_w1.showGrid(x=True, y=True, alpha=0.7)
        self.m10_w2 = self.ui.graphWindowM10.addPlot(row=1, col=0, title='Força')
        self.m10_w2.showGrid(x=True, y=True, alpha=0.7)
        self.m10_w1_l = LegendItem((80,30), offset=(60,30))  # args are (size, offset)
        self.m10_w1_l.setParentItem(self.m10_w1)   # Note we do NOT call plt.addItem in this case

        self.m10_w2_l = LegendItem((80,30), offset=(60,30))  # args are (size, offset)
        self.m10_w2_l.setParentItem(self.m10_w2)   # Note we do NOT call plt.addItem in this case

        #Setup GraphicsLayoutWidget M14

        self.m14_w1 = self.ui.graphWindowM14.addPlot(row=0, col=0, title='Pos V')
        self.m14_w1.showGrid(x=True, y=True, alpha=0.7)
        self.m14_w2 = self.ui.graphWindowM14.addPlot(row=1, col=0, title='Acel')
        self.m14_w2.showGrid(x=True, y=True, alpha=0.7)

        self.m14_w1_l = LegendItem((80,30), offset=(60,30))
        self.m14_w1_l.setParentItem(self.m14_w1)

        self.m14_w2_l = LegendItem((80,30), offset=(60,30))
        self.m14_w2_l.setParentItem(self.m14_w2)

        #Setup GraphicsLayoutWidget G10

        self.g10_w1 = self.ui.graphWindowG10.addPlot(row=0, col=0, colspan=3, title='Gerador')
        self.g10_w1.showGrid(x=True, y=True, alpha=0.7)
        self.g10_w4 = self.ui.graphWindowG10.addPlot(row=0, col=3, colspan=1, title='Potência')
        self.g10_w4.showGrid(x=True, y=True, alpha=0.7)
        self.g10_w2 = self.ui.graphWindowG10.addPlot(row=1, col=0, colspan=4, title='Rotações')
        self.g10_w2.showGrid(x=True, y=True, alpha=0.7)
        self.g10_w3 = self.ui.graphWindowG10.addPlot(row=2, col=0, colspan=4, title='ToF')
        self.g10_w3.showGrid(x=True, y=True, alpha=0.7)

        self.g10_w1_l = LegendItem((80,30), offset=(60,30))
        self.g10_w1_l.setParentItem(self.g10_w1)

        self.g10_w2_l = LegendItem((80,30), offset=(60,30))
        self.g10_w2_l.setParentItem(self.g10_w2)

        self.g10_w3_l = LegendItem((80,30), offset=(60,30))
        self.g10_w3_l.setParentItem(self.g10_w3)

        self.g10_w4_l = LegendItem((80,30), offset=(60,30))
        self.g10_w4_l.setParentItem(self.g10_w4)

        # Setup GraphicsLayoutWidget G14

        self.g14_w1 = self.ui.graphWindowG14.addPlot(row=0, col=0, colspan=3, title='Gerador')
        self.g14_w1.setRange(xRange=[0, 101])
        self.g14_w1.showGrid(x=True, y=True, alpha=0.7)
        self.g14_w4 = self.ui.graphWindowG14.addPlot(row=0, col=3, colspan=1, title='Potência')
        self.g14_w4.setRange(xRange=[0, 101])
        self.g14_w4.showGrid(x=True, y=True, alpha=0.7)
        self.g14_w2 = self.ui.graphWindowG14.addPlot(row=1, col=0, colspan=4, title='Rotações')
        self.g14_w2.setRange(xRange=[0, 101])
        self.g14_w2.showGrid(x=True, y=True, alpha=0.7)
        self.g14_w3 = self.ui.graphWindowG14.addPlot(row=2, col=0, colspan=4, title='Pos V + Pos H')
        self.g14_w3.setRange(xRange=[0, 101])
        self.g14_w3.showGrid(x=True, y=True, alpha=0.7)

        self.g14_w1_l = LegendItem((80, 30), offset=(60, 30))
        self.g14_w1_l.setParentItem(self.g14_w1)

        self.g14_w2_l = LegendItem((80, 30), offset=(60, 30))
        self.g14_w2_l.setParentItem(self.g14_w2)

        self.g14_w3_l = LegendItem((80, 30), offset=(60, 30))
        self.g14_w3_l.setParentItem(self.g14_w3)

        self.g14_w4_l = LegendItem((80, 30), offset=(60, 30))
        self.g14_w4_l.setParentItem(self.g14_w4)

        self.currentTabName = self.ui.tabWidgetGraphs.tabText(self.ui.tabWidgetGraphs.currentIndex()).split()[0]

        self.M10Entries = []
        self.M14Entries = []
        self.G10Entries = []
        self.G14Entries = []

        self.addEntry("All")

        #initialize combo box
        self.getCOMList()

        if self.ui.targetComCB.currentText()=='':
            self.serialCOM = None
        else:
            self.serialCOM = self.ui.targetComCB.currentText()

        #combo box Callback
        self.ui.targetComCB.activated[str].connect(self.onTargetComCBActivated)

        #targetComConnectButton Callback
        self.ui.targetComConnectButton.clicked.connect(self.targetConnectionCB)
        #updateCOMButton CallBack
        self.ui.updateCOMButton.clicked.connect(self.getCOMList)
        #saveDataButton Callback
        self.ui.saveDataButton.clicked.connect(self.getSaveFiles)
        #openDataButton Callback
        self.ui.openDataButton.clicked.connect(self.getOpenfiles)
        #clearGraphButton Callback
        self.ui.clearGraphButton.clicked.connect(self.clearGraph)
        #tabWidget tab change
        self.ui.tabWidgetGraphs.currentChanged.connect(self.tabChangedCB)
        #sensorEntryListWidget item selected
        self.ui.sensorEntryListWidget.itemClicked.connect(self.sensorEntryListICCB)
    def startSerialThread(self):
        #self.serialListenerThread = serialThread(1, "SerialListener", self.d_lock)

        #Signal from Thread

        self.serialConnectionParameters.append(self.serialCOM)
        self.serialListenerThread.setParameteres(self.serialConnectionParameters)
        self.serialListenerThread.saveRawFile = self.saveRawFile
        self.serialListenerThread.saveRawFileBU = self.saveRawFileBackup
        self.serialListenerThread.start()

    def startProcessThread(self):
        #self.processThread = processThread(2, "Process", self.d_lock, self.c_lock)

        #Signal from Thread
        self.processThread.addEntrySignal[dict].connect(self.newData)

        self.processThread.rawConfigFile = self.saveRawFile
        self.processThread.rawConfigFileBU = self.saveRawFileBackup
        self.processThread.dataFile = self.saveDataFile
        self.processThread.dataFileBU = self.saveDataFileBU
        self.processThread.start()

    #COMMUNICATION
    def getCOMList(self):
        self.ui.targetComCB.clear()
        self.ui.targetComCB.addItems([comport.device for comport in serial.tools.list_ports.comports()])
        self.serialCOM = self.ui.targetComCB.currentText()

    def targetConnectionCB(self):

        if not self.serialListenerThread.closeEvent.is_set():
            self.closeSerialConnetion()
            self.ui.targetComConnectButton.setText("Connect")
            self.addEntry("All")
        elif(self.serialCOM != None):
            self.serialListenerThread.closeEvent.clear()
            self.processThread.closeEvent.clear()
            if(self.establishConnection()):
                # If connection is established set text as disconnect
                self.ui.targetComConnectButton.setText("Disconnect")

    def onTargetComCBActivated(self, text):
        if text != None:
            self.serialCOM = text

    def establishConnection(self):
        try:
            self.startSerialThread()
            #print("serialListenerThread isRunning", self.serialListenerThread.isRunning())
            if self.serialListenerThread.isRunning():
                self.startProcessThread()
                #print("processThread isRunning", self.processThread.isRunning())
                self.ui.connectionStatusLabel.setText("Connection Status: Online")
                return 1
            else:
                return 0
        except Exception as err:
            print(str(err))

    def closeSerialConnetion(self):
        #Set event flag to close thread
        self.serialListenerThread.closeEvent.set()
        self.processThread.closeEvent.set()
        self.ui.connectionStatusLabel.setText("Connection Status: Offline")

    def newData(self, toBeUpdated):

        for key in toBeUpdated:
            if key not in self.total_toBeUpdated:
                self.total_toBeUpdated[key] = []
            for val in toBeUpdated[key]:
                if val not in self.total_toBeUpdated[key]:
                    self.total_toBeUpdated[key].append(val)
                self.toBeUpdated_count = self.toBeUpdated_count + 1
        if self.toBeUpdated_count > 10 or self.ten_second_timer_flag and self.toBeUpdated_count > 0:
            print("Displaying", self.total_toBeUpdated, self.toBeUpdated_count)
            self.toBeUpdated_count = 0
            self.ten_second_timer_flag = False
            self.addEntry(self.total_toBeUpdated)
            self.total_toBeUpdated = {}

    def addEntry(self, toBeUpdated):

        if toBeUpdated == "All":
            updateAll = True

            m14_sl0 = True
            m14_sl1 = True
            m14_sl2 = True
            m14_acelx = True
            m14_acely = True
            m14_acelz = True
            m14_sl3 = True
            m14_sl4 = True
            m14_sl5 = True

            m10acelx = True
            m10acely = True
            m10acelz = True
            m10forc = True

            g14_hall1 = True
            g14_hall2 = True
            g14_curr1 = True
            g14_curr2 = True
            g14_volt1 = True
            g14_volt2 = True
            g14_pulse1 = True
            g14_pulse2 = True
            g14_slhe = True
            g14_slhd = True
            g14_slve = True
            g14_slvd = True

            g10_tof = True
            g10_EL1 = True
            g10_EL2 = True
            g10_hall1 = True
            g10_hall2 = True
            g10_volt1 = True
            g10_volt2 = True
            g10_curr1 = True
            g10_curr2 = True
            g10_pulse1 = True
            g10_pulse2 = True
            
        else:
            updateAll = False

            m14_sl0 = False
            m14_sl1 = False
            m14_sl2 = False
            m14_acelx = False
            m14_acely = False
            m14_acelz = False
            m14_sl3 = False
            m14_sl4 = False
            m14_sl5 = False

            m10acelx = False
            m10acely = False
            m10acelz = False
            m10forc = False

            g14_hall1 = False
            g14_hall2 = False
            g14_curr1 = False
            g14_curr2 = False
            g14_volt1 = False
            g14_volt2 = False
            g14_pulse1 = False
            g14_pulse2 = False
            g14_slhe = False
            g14_slhd = False
            g14_slve = False
            g14_slvd = False

            g10_tof = False
            g10_EL1 = False
            g10_EL2 = False
            g10_hall1 = False
            g10_hall2 = False
            g10_volt1 = False
            g10_volt2 = False
            g10_curr1 = False
            g10_curr2 = False
            g10_pulse1 = False
            g10_pulse2 = False

        # Used on trigger by thread signal
        self.d_lock.acquire()

        try:
            with open(self.saveDataFile) as json_file:
                self.Entries = json.load(json_file)
        except json.decoder.JSONDecodeError:
            try:
                with open(self.saveDataFileBU) as json_file:
                    self.Entries = json.load(json_file)
            except Exception:
                # if no file is found no entries are added
                None
        except FileNotFoundError:
            # if no file is found no entries are added
            None
        self.d_lock.release()

        #print("toBeUpdates", toBeUpdated)
        if not updateAll:
            for slaveKey in toBeUpdated:
                for sensorKey in toBeUpdated[slaveKey]:
                    
                    if int(slaveKey) == 1 and int(sensorKey) == 17:
                        m14_sl0 = True
                    elif int(slaveKey) == 1 and int(sensorKey) == 18:
                        m14_sl1 = True
                    elif int(slaveKey) == 1 and int(sensorKey) == 19:
                        m14_sl2 = True
                    elif int(slaveKey) == 1 and int(sensorKey) == 33:
                        m14_sl3 = True
                    elif int(slaveKey) == 1 and int(sensorKey) == 34:
                        m14_sl4 = True
                    elif int(slaveKey) == 1 and int(sensorKey) == 35:
                        m14_sl5 = True
                    elif int(slaveKey) == 1 and int(sensorKey) == 49:
                        m14_acelx = True
                    elif int(slaveKey) == 1 and int(sensorKey) == 50:
                        m14_acely = True
                    elif int(slaveKey) == 1 and int(sensorKey) == 51:
                        m14_acelz = True

                    elif int(slaveKey) == 2 and int(sensorKey) == 17:
                        m10acelx = True
                    elif int(slaveKey) == 2 and int(sensorKey) == 18:
                        m10acely = True
                    elif int(slaveKey) == 2 and int(sensorKey) == 19:
                        m10acelz = True
                    elif int(slaveKey) == 2 and int(sensorKey) == 33:
                        m10forc = True

                    elif int(slaveKey) == 3 and int(sensorKey) == 11:
                        g14_hall1 = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 12:
                        g14_hall2 = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 21:
                        g14_curr1 = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 22:
                        g14_curr2 = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 31:
                        g14_volt1 = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 32:
                        g14_volt2 = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 41:
                        g14_pulse1 = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 42:
                        g14_pulse2 = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 51:
                        g14_slhe = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 52:
                        g14_slhd = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 61:
                        g14_slve = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 62:
                        g14_slvd = True

                    elif int(slaveKey) == 4 and int(sensorKey) == 11:
                        g10_tof = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 21:
                        g10_EL1 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 22:
                        g10_EL2 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 31:
                        g10_hall1 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 32:
                        g10_hall2 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 41:
                        g10_volt1 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 42:
                        g10_volt2 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 51:
                        g10_curr1 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 52:
                        g10_curr2 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 61:
                        g10_pulse1 = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 62:
                        g10_pulse2 = True


        # UPDATE data lists

        # M10

        self.m10_acelx_x = []
        self.m10_acelx_y = []
        self.m10_acely_x = []
        self.m10_acely_y = []
        self.m10_acelz_x = []
        self.m10_acelz_y = []

        self.m10_forca_x = []
        self.m10_forca_y = []

        # m10_acelx
        if m10acelx:
            try:
                self.m10_acelx_x = self.Entries["2"]["sensors"]["17"]["time"]
                self.m10_acelx_y = self.Entries["2"]["sensors"]["17"]["dataNR"]
            except Exception:
                None

        # m10_acely
        if m10acely:
            try:
                self.m10_acely_x = self.Entries["2"]["sensors"]["18"]["time"]
                self.m10_acely_y = self.Entries["2"]["sensors"]["18"]["dataNR"]
            except Exception:
                None

        # m10_acelz
        if m10acelz:
            try:
                self.m10_acelz_x = self.Entries["2"]["sensors"]["19"]["time"]
                self.m10_acelz_y = self.Entries["2"]["sensors"]["19"]["dataNR"]
            except Exception:
                None

        # m10_forca_x
        if m10forc:
            try:
                self.m10_forca_x = self.Entries["2"]["sensors"]["33"]["time"]
                self.m10_forca_y = self.Entries["2"]["sensors"]["33"]["dataR"]
            except Exception:
                None


        # M14

        # CLEAR lists
        self.m14_acelx_x = []
        self.m14_acelx_y = []
        self.m14_acely_x = []
        self.m14_acely_y = []
        self.m14_acelz_x = []
        self.m14_acelz_y = []

        self.m14_sl0_x = []
        self.m14_sl0_y = []
        self.m14_sl1_x = []
        self.m14_sl1_y = []
        self.m14_sl2_x = []
        self.m14_sl2_y = []
        self.m14_sl3_x = []
        self.m14_sl3_y = []
        self.m14_sl4_x = []
        self.m14_sl4_y = []
        self.m14_sl5_x = []
        self.m14_sl5_y = []
        # CLEAR lists

        # m14_acelx
        if m14_acelx:
            try:
                self.m14_acelx_x = self.Entries["1"]["sensors"]["49"]["time"]
                self.m14_acelx_y = self.Entries["1"]["sensors"]["49"]["dataNR"]
            except Exception:
                None

        # m14_acely
        if m14_acely:
            try:
                self.m14_acely_x = self.Entries["1"]["sensors"]["50"]["time"]
                self.m14_acely_y = self.Entries["1"]["sensors"]["50"]["dataNR"]
            except Exception:
                None

        # m14_acelz
        if m14_acelz:
            try:
                self.m14_acelz_x = self.Entries["1"]["sensors"]["51"]["time"]
                self.m14_acelz_y = self.Entries["1"]["sensors"]["51"]["dataNR"]
            except Exception:
                None

        # m14_sl0
        if m14_sl0:
            try:
                self.m14_sl0_x = self.Entries["1"]["sensors"]["17"]["time"]
                self.m14_sl0_y = self.Entries["1"]["sensors"]["17"]["dataR"]
            except Exception:
                None

        # m14_sl1
        if m14_sl1:
            try:
                self.m14_sl1_x = self.Entries["1"]["sensors"]["18"]["time"]
                self.m14_sl1_y = self.Entries["1"]["sensors"]["18"]["dataR"]
            except Exception:
                None

        # m14_sl2
        if m14_sl2:
            try:
                self.m14_sl2_x = self.Entries["1"]["sensors"]["19"]["time"]
                self.m14_sl2_y = self.Entries["1"]["sensors"]["19"]["dataR"]
            except Exception:
                None

        # m14_sl3
        if m14_sl3:
            try:
                self.m14_sl3_x = self.Entries["1"]["sensors"]["33"]["time"]
                self.m14_sl3_y = self.Entries["1"]["sensors"]["33"]["dataR"]
            except Exception:
                None

        # m14_sl4
        if m14_sl4:
            try:
                self.m14_sl4_x = self.Entries["1"]["sensors"]["34"]["time"]
                self.m14_sl4_y = self.Entries["1"]["sensors"]["34"]["dataR"]
            except Exception:
                None

        # m14_sl5
        if m14_sl5:
            try:
                self.m14_sl5_x = self.Entries["1"]["sensors"]["35"]["time"]
                self.m14_sl5_y = self.Entries["1"]["sensors"]["35"]["dataR"]
            except Exception:
                None

        # G10

        # CLEAR lists
        self.g10_volt1_x = []
        self.g10_volt1_y = []
        self.g10_volt2_x = []
        self.g10_volt2_y = []
        self.g10_curr1_x = []
        self.g10_curr1_y = []
        self.g10_curr2_x = []
        self.g10_curr2_y = []

        self.g10_hall1_x = []
        self.g10_hall1_y = []
        self.g10_hall2_x = []
        self.g10_hall2_y = []
        self.g10_pulse1_x = []
        self.g10_pulse1_y = []
        self.g10_pulse2_x = []
        self.g10_pulse2_y = []

        self.g10_tof_x = []
        self.g10_tof_y = []
        self.g10_EL1_x = []
        self.g10_EL1_y = []
        self.g10_EL2_x = []
        self.g10_EL2_y = []

        self.g10_pot1_x = []
        self.g10_pot1_y = []
        self.g10_pot2_x = []
        self.g10_pot2_y = []

        # CLEAR lists

        # g10_volt1
        if g10_volt1:
            try:
                self.g10_volt1_x = self.Entries["4"]["sensors"]["41"]["time"]
                self.g10_volt1_y = self.Entries["4"]["sensors"]["41"]["dataR"]
            except Exception:
                None

        # g10_volt2
        if g10_volt2:
            try:
                self.g10_volt2_x = self.Entries["4"]["sensors"]["42"]["time"]
                self.g10_volt2_y = self.Entries["4"]["sensors"]["42"]["dataR"]
            except Exception:
                None

        # g10_curr1
        if g10_curr1:
            try:
                self.g10_curr1_x = self.Entries["4"]["sensors"]["51"]["time"]
                self.g10_curr1_y = self.Entries["4"]["sensors"]["51"]["dataR"]
            except Exception:
                None

        # g10_curr2
        if g10_curr2:
            try:
                self.g10_curr2_x = self.Entries["4"]["sensors"]["52"]["time"]
                self.g10_curr2_y = self.Entries["4"]["sensors"]["52"]["dataR"]
            except Exception:
                None

        # g10_hall1
        if g10_hall1:
            try:
                self.g10_hall1_x = self.Entries["4"]["sensors"]["31"]["time"]
                self.g10_hall1_y = self.Entries["4"]["sensors"]["31"]["dataR"]
            except Exception:
                None

        # g10_hall2
        if g10_hall2:
            try:
                self.g10_hall2_x = self.Entries["4"]["sensors"]["32"]["time"]
                self.g10_hall2_y = self.Entries["4"]["sensors"]["32"]["dataR"]
            except Exception:
                None

        # g10_pulse1
        if g10_pulse1:
            try:
                self.g10_pulse1_x = self.Entries["4"]["sensors"]["61"]["time"]
                self.g10_pulse1_y = self.Entries["4"]["sensors"]["61"]["dataR"]
            except Exception:
                None

        # g10_pulse2
        if g10_pulse2:
            try:
                self.g10_pulse2_x = self.Entries["4"]["sensors"]["62"]["time"]
                self.g10_pulse2_y = self.Entries["4"]["sensors"]["62"]["dataR"]
            except Exception:
                None

        # g10_tof
        if g10_tof:
            try:
                self.g10_tof_x = self.Entries["4"]["sensors"]["11"]["time"]
                self.g10_tof_y = self.Entries["4"]["sensors"]["11"]["dataR"]
            except Exception:
                None

        # g10_EL1
        if g10_EL1:
            try:
                self.g10_EL1_x = self.Entries["4"]["sensors"]["21"]["time"]
                self.g10_EL1_y = self.Entries["4"]["sensors"]["21"]["dataR"]
            except Exception:
                None

        # g10_EL2
        if g10_EL2:
            try:
                self.g10_EL2_x = self.Entries["4"]["sensors"]["22"]["time"]
                self.g10_EL2_y = self.Entries["4"]["sensors"]["22"]["dataR"]
            except Exception:
                None

        # TODO add potencia

        # G14

        # CLEAR lists
        self.g14_volt1_x = []
        self.g14_volt1_y = []
        self.g14_volt2_x = []
        self.g14_volt2_y = []
        self.g14_curr1_x = []
        self.g14_curr1_y = []
        self.g14_curr2_x = []
        self.g14_curr2_y = []

        self.g14_hall1_x = []
        self.g14_hall1_y = []
        self.g14_hall2_x = []
        self.g14_hall2_y = []
        self.g14_pulse1_x = []
        self.g14_pulse1_y = []
        self.g14_pulse2_x = []
        self.g14_pulse2_y = []

        self.g14_slhe_x = []
        self.g14_slhe_y = []
        self.g14_slhd_x = []
        self.g14_slhd_y = []
        self.g14_slve_x = []
        self.g14_slve_y = []
        self.g14_slvd_x = []
        self.g14_slvd_y = []

        self.g14_pot1_x = []
        self.g14_pot1_y = []
        self.g14_pot2_x = []
        self.g14_pot2_y = []

        # CLEAR lists

        # g14_volt1
        if g14_volt1:
            try:
                self.g14_volt1_y = self.Entries["3"]["sensors"]["31"]["time"]
                self.g14_volt1_x = self.Entries["3"]["sensors"]["31"]["dataR"]
            except Exception:
                None

        # g14_volt2
        if g14_volt2:
            try:
                self.g14_volt2_y = self.Entries["3"]["sensors"]["32"]["time"]
                self.g14_volt2_x = self.Entries["3"]["sensors"]["32"]["dataR"]
            except Exception:
                None

        # g14_curr1
        if g14_curr1:
            try:
                self.g14_curr1_y = self.Entries["3"]["sensors"]["21"]["time"]
                self.g14_curr1_x = self.Entries["3"]["sensors"]["21"]["dataR"]
            except Exception:
                None

        # g14_curr2
        if g14_curr2:
            try:
                self.g14_curr2_y = self.Entries["3"]["sensors"]["22"]["time"]
                self.g14_curr2_x = self.Entries["3"]["sensors"]["22"]["dataR"]
            except Exception:
                None

        # g14_hall1
        if g14_hall1:
            try:
                self.g14_hall1_y = self.Entries["3"]["sensors"]["11"]["time"]
                self.g14_hall1_x = self.Entries["3"]["sensors"]["11"]["dataR"]
            except Exception:
                None

        # g14_hall2
        if g14_hall2:
            try:
                self.g14_hall2_y = self.Entries["3"]["sensors"]["12"]["time"]
                self.g14_hall2_x = self.Entries["3"]["sensors"]["12"]["dataR"]
            except Exception:
                None

        # g14_pulse1
        if g14_pulse1:
            try:
                self.g14_pulse1_y = self.Entries["3"]["sensors"]["71"]["time"]
                self.g14_pulse1_x = self.Entries["3"]["sensors"]["71"]["dataR"]
            except Exception:
                None

        # g14_pulse2
        if g14_pulse2:
            try:
                self.g14_pulse2_y = self.Entries["3"]["sensors"]["72"]["time"]
                self.g14_pulse2_x = self.Entries["3"]["sensors"]["72"]["dataR"]
            except Exception:
                None

            # g14_slhe
        if g14_slhe:
            try:
                self.g14_slhe_y = self.Entries["3"]["sensors"]["51"]["time"]
                self.g14_slhe_x = self.Entries["3"]["sensors"]["51"]["dataR"]
            except Exception:
                None

        # g14_slhd
        if g14_slhd:
            try:
                self.g14_slhd_y = self.Entries["3"]["sensors"]["52"]["time"]
                self.g14_slhd_x = self.Entries["3"]["sensors"]["52"]["dataR"]
            except Exception:
                None

        # g14_slve
        if g14_slve:
            try:
                self.g14_slve_y = self.Entries["3"]["sensors"]["61"]["time"]
                self.g14_slve_x = self.Entries["3"]["sensors"]["61"]["dataR"]
            except Exception:
                None

        # g14_slvd
        if g14_slvd:
            try:
                self.g14_slvd_y = self.Entries["3"]["sensors"]["62"]["time"]
                self.g14_slvd_x = self.Entries["3"]["sensors"]["62"]["dataR"]
            except Exception:
                None

        if (m10acelx or m10acely or m10acelz or m10forc):
            m10 = (m10acelx, m10acely, m10acelz, m10forc)
        else:
            m10 = None
        if (m14_acelx or m14_acely or m14_acelz or m14_sl0 or m14_sl1 or m14_sl2 or m14_sl3 or m14_sl4 or m14_sl5):
            m14 = (m14_acelx, m14_acely, m14_acelz, m14_sl0, m14_sl1, m14_sl2, m14_sl3, m14_sl4, m14_sl5)
        else:
            m14 = None
        if (g10_volt1 or g10_volt2 or g10_curr1 or g10_curr2 or g10_hall1 or g10_hall2 or g10_pulse1 or g10_pulse2 or g10_tof or g10_EL1 or g10_EL2):
            g10 = (g10_volt1, g10_volt2, g10_curr1, g10_curr2, g10_hall1, g10_hall2, g10_pulse1, g10_pulse2, g10_tof, g10_EL1, g10_EL2)
        else:
            g10 = None
        if (g14_volt1 or g14_volt2 or g14_curr1 or g14_curr2 or g14_hall1 or g14_hall2 or g14_pulse1 or g14_pulse2 or g14_slhe or g14_slhd or g14_slve or g14_slvd):
            g14 = (g14_volt1, g14_volt2, g14_curr1, g14_curr2, g14_hall1, g14_hall2, g14_pulse1, g14_pulse2, g14_slhe, g14_slhd, g14_slve, g14_slvd)
        else:
            g14 = None

        self.updatePlots(m10=m10, m14=m14, g10=g10, g14=g14)

        #Filters
        self.M14Entries = []
        self.M10Entries = []
        self.G14Entries = []
        self.G10Entries = []

        for module in self.Entries:
            for sensor in self.Entries[module]['sensors']:
                try:
                    if module == '1':
                        self.M14Entries.append((sensor, self.Entries[module]['sensors'][sensor]['dataList']))
                    elif module == '2':
                        self.M10Entries.append((sensor, self.Entries[module]['sensors'][sensor]['dataList']))
                    elif module == '3':
                        self.G14Entries.append((sensor, self.Entries[module]['sensors'][sensor]['dataList']))
                    elif module == '4':
                        self.G10Entries.append((sensor, self.Entries[module]['sensors'][sensor]['dataList']))
                except Exception:
                    None

        self.currentEntriesFilter = {'M10': {'key':'2', 'entries': self.M10Entries}, 'M14': {'key':'1', 'entries': self.M14Entries}, 'G10': {'key':'4', 'entries': self.G10Entries}, 'G14': {'key':'3', 'entries': self.G14Entries}}
        self.updateSensorEntryListWidget()



    def updatePlots(self, m10=None, m14=None, g10=None, g14=None):
        #print("M10", m10)
        #print("M14", m14)
        #print("G10", g10)
        #print("G14", g14)

        if (m10):
            self.addPlotM10(m10)
        if (m14):
            self.addPlotM14(m14)
        if (g10):
            self.addPlotG10(g10)
        if (g14):
            self.addPlotG14(g14)

    def addRawEntry(self, data):
        print("Got new raw data", data)
        self.processThread.newRawEvent.set()

    def addPlotM10(self, m10):
        # ADD PLOT PROCEDURE

        if (m10[0]):
            for item in self.m10_w1.listDataItems():
                if item.name() == "Acel X":
                    self.m10_w1.removeItem(item)
            acelx = self.m10_w1.plot(self.m10_acelx_x, self.m10_acelx_y, pen=(128, 0, 0))
            self.m10_w1_l.removeItem('Acel X')
            self.m10_w1_l.addItem(acelx, 'Acel X')
        if (m10[1]):
            for item in self.m10_w1.listDataItems():
                if item.name() == "Acel Y":
                    self.m10_w1.removeItem(item)
            acely = self.m10_w1.plot(self.m10_acely_x, self.m10_acely_y, pen=(0, 128, 0))
            self.m10_w1_l.removeItem('Acel Y')
            self.m10_w1_l.addItem(acely, 'Acel Y')
        if (m10[2]):
            for item in self.m10_w1.listDataItems():
                if item.name() == "Acel Z":
                    self.m10_w1.removeItem(item)
            acelz = self.m10_w1.plot(self.m10_acelz_x, self.m10_acelz_y, pen=(0, 0, 128))
            self.m10_w1_l.removeItem('Acel Z')
            self.m10_w1_l.addItem(acelz, 'Acel Z')
        if (m10[3]):
            for item in self.m10_w1.listDataItems():
                if item.name() == "Força":
                    self.m10_w2.removeItem(item)
            forca = self.m10_w2.plot(self.m10_forca_x, self.m10_forca_y, pen=(128, 0, 0))
            self.m10_w2_l.removeItem('Força')
            self.m10_w2_l.addItem(forca, 'Força')

    def addPlotM14(self, m14):
        # ADD PLOT PROCEDURE
        if (m14[3]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl0":
                    self.m14_w1.removeItem(item)
            sl0 = self.m14_w1.plot(self.m14_sl0_x, self.m14_sl0_y, pen=(191, 0, 0), name="sl0")
            self.m14_w1_l.removeItem('sl0')
            self.m14_w1_l.addItem(sl0, 'sl0')
        if (m14[4]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl1":
                    self.m14_w1.removeItem(item)
            sl1 = self.m14_w1.plot(self.m14_sl1_x, self.m14_sl1_y, pen=(0, 191, 0), name="sl1")
            self.m14_w1_l.removeItem('sl1')
            self.m14_w1_l.addItem(sl1, 'sl1')
        if (m14[5]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl2":
                    self.m14_w1.removeItem(item)
            sl2 = self.m14_w1.plot(self.m14_sl2_x, self.m14_sl2_y, pen=(0, 0, 191), name="sl2")
            self.m14_w1_l.removeItem('sl2')
            self.m14_w1_l.addItem(sl2, 'sl2')
        if (m14[6]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl3":
                    self.m14_w1.removeItem(item)
            sl3 = self.m14_w1.plot(self.m14_sl3_x, self.m14_sl3_y, pen=(128, 128, 0), name="sl3")
            self.m14_w1_l.removeItem('sl3')
            self.m14_w1_l.addItem(sl3, 'sl3')
        if (m14[7]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl4":
                    self.m14_w1.removeItem(item)
            sl4 = self.m14_w1.plot(self.m14_sl4_x, self.m14_sl4_y, pen=(0, 128, 128), name="sl4")
            self.m14_w1_l.removeItem('sl4')
            self.m14_w1_l.addItem(sl4, 'sl4')
        if (m14[8]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl5":
                    self.m14_w1.removeItem(item)
            sl5 = self.m14_w1.plot(self.m14_sl5_x, self.m14_sl5_y, pen=(128, 0, 128), name="sl5")
            self.m14_w1_l.removeItem('sl5')
            self.m14_w1_l.addItem(sl5, 'sl5')


        if(m14[0]):
            for item in self.m14_w2.listDataItems():
                if item.name() == "acelx":
                    self.m14_w2.removeItem(item)
            acelx = self.m14_w2.plot(self.m14_acelx_x, self.m14_acelx_y, pen=(191, 0, 0), name="acelx")
            self.m14_w2_l.removeItem('Acel X')
            self.m14_w2_l.addItem(acelx, 'Acel X')
        if (m14[1]):
            for item in self.m14_w2.listDataItems():
                if item.name() == "acely":
                    self.m14_w2.removeItem(item)
            self.m14_w2.removeItem("acely")
            acely = self.m14_w2.plot(self.m14_acely_x, self.m14_acely_y, pen=(0, 191, 0), name="acely")
            self.m14_w2_l.removeItem('Acel Y')
            self.m14_w2_l.addItem(acely, 'Acel Y')
        if (m14[2]):
            for item in self.m14_w2.listDataItems():
                if item.name() == "acelz":
                    self.m14_w2.removeItem(item)
            self.m14_w2.removeItem("acelz")
            acelz = self.m14_w2.plot(self.m14_acelz_x, self.m14_acelz_y, pen=(0, 0, 191), name="acelz")
            self.m14_w2_l.removeItem('Acel Z')
            self.m14_w2_l.addItem(acelz, 'Acel Z')

    def addPlotG10(self, g10):
        # ADD PLOT PROCEDURE
        
        #TODO add potencia

        if (g10[0]):
            for item in self.g10_w1.listDataItems():
                if item.name() == "g10_volt1":
                    self.g10_w1.removeItem(item)
            g10_volt1 = self.g10_w1.plot(self.g10_volt1_x, self.g10_volt1_y, pen=(191, 0, 0), name="Volt 1")
            self.g10_w1_l.removeItem('g10_volt1')
            self.g10_w1_l.addItem(g10_volt1, 'g10_volt1')
        if (g10[1]):
            for item in self.g10_w1.listDataItems():
                if item.name() == "g10_volt2":
                    self.g10_w1.removeItem(item)
            g10_volt2 = self.g10_w1.plot(self.g10_volt2_x, self.g10_volt2_y, pen=(0, 191, 0), name="Volt 2")
            self.g10_w1_l.removeItem('g10_volt2')
            self.g10_w1_l.addItem(g10_volt2, 'g10_volt2')
        if (g10[2]):
            for item in self.g10_w1.listDataItems():
                if item.name() == "g10_curr1":
                    self.g10_w1.removeItem(item)
            g10_curr1 = self.g10_w1.plot(self.g10_curr1_x, self.g10_curr1_y, pen=(0, 0, 191), name="Curr 1")
            self.g10_w1_l.removeItem('g10_curr1')
            self.g10_w1_l.addItem(g10_curr1, 'g10_curr1')
        if (g10[3]):
            for item in self.g10_w1.listDataItems():
                if item.name() == "g10_curr2":
                    self.g10_w1.removeItem(item)
            g10_curr2 = self.g10_w1.plot(self.g10_curr2_x, self.g10_curr2_y, pen=(128, 128, 0), name="Curr 2")
            self.g10_w1_l.removeItem('g10_curr2')
            self.g10_w1_l.addItem(g10_curr2, 'g10_curr2')
            
            
        if (g10[4]):
            for item in self.g10_w2.listDataItems():
                if item.name() == "g10_hall1":
                    self.g10_w2.removeItem(item)
            g10_hall1 = self.g10_w2.plot(self.g10_hall1_x, self.g10_hall1_y, pen=(191, 0, 0), name="Hall 1")
            self.g10_w2_l.removeItem('g10_hall1')
            self.g10_w2_l.addItem(g10_hall1, 'g10_hall1')
        if (g10[5]):
            for item in self.g10_w2.listDataItems():
                if item.name() == "g10_hall2":
                    self.g10_w2.removeItem(item)
            g10_hall2 = self.g10_w2.plot(self.g10_hall2_x, self.g10_hall2_y, pen=(0, 191, 0), name="Hall 2")
            self.g10_w2_l.removeItem('g10_hall2')
            self.g10_w2_l.addItem(g10_hall2, 'g10_hall2')
        if(g10[6]):
            for item in self.g10_w2.listDataItems():
                if item.name() == "g10_pulse1":
                    self.g10_w2.removeItem(item)
            g10_pulse1 = self.g10_w2.plot(self.g10_pulse1_x, self.g10_pulse1_y, pen=(0, 0, 191), name="Pulse 1")
            self.g10_w2_l.removeItem('g10_pulse1')
            self.g10_w2_l.addItem(g10_pulse1, 'g10_pulse1')
        if (g10[7]):
            for item in self.g10_w2.listDataItems():
                if item.name() == "g10_pulse2":
                    self.g10_w2.removeItem(item)
            self.g10_w2.removeItem("g10_pulse2")
            g10_pulse2 = self.g10_w2.plot(self.g10_pulse2_x, self.g10_pulse2_y, pen=(128, 128, 0), name="Pulse 2")
            self.g10_w2_l.removeItem('g10_pulse2')
            self.g10_w2_l.addItem(g10_pulse2, 'g10_pulse2')

        if (g10[8]):
            for item in self.g10_w3.listDataItems():
                if item.name() == "g10_tof":
                    self.g10_w3.removeItem(item)
            self.g10_w3.removeItem("g10_tof")
            g10_tof = self.g10_w3.plot(self.g10_tof_x, self.g10_tof_y, pen=(191, 0, 0), name="ToF")
            self.g10_w3_l.removeItem('g10_tof')
            self.g10_w3_l.addItem(g10_tof, 'g10_tof')
        if (g10[9]):
            for item in self.g10_w3.listDataItems():
                if item.name() == "g10_EL1":
                    self.g10_w3.removeItem(item)
            self.g10_w3.removeItem("g10_EL1")
            g10_EL1 = self.g10_w3.plot(self.g10_EL1_x, self.g10_EL1_y, pen=(0, 191, 0), name="EL 1")
            self.g10_w3_l.removeItem('g10_EL1')
            self.g10_w3_l.addItem(g10_EL1, 'g10_EL1')
        if (g10[10]):
            for item in self.g10_w3.listDataItems():
                if item.name() == "g10_EL2":
                    self.g10_w3.removeItem(item)
            self.g10_w3.removeItem("g10_EL2")
            g10_EL2 = self.g10_w3.plot(self.g10_EL2_x, self.g10_EL2_y, pen=(0, 0, 191), name="EL 2")
            self.g10_w3_l.removeItem('g10_EL2')
            self.g10_w3_l.addItem(g10_EL2, 'g10_EL2')

    def addPlotG14(self, g14):

        # ADD PLOT PROCEDURE

        # TODO add potencia

        if (g14[0]):
            for item in self.g14_w1.listDataItems():
                if item.name() == "g14_volt1":
                    self.g14_w1.removeItem(item)
            g14_volt1 = self.g14_w1.plot(self.g14_volt1_x, self.g14_volt1_y, pen=(191, 0, 0), name="Volt 1")
            self.g14_w1_l.removeItem('g14_volt1')
            self.g14_w1_l.addItem(g14_volt1, 'g14_volt1')
        if (g14[1]):
            for item in self.g14_w1.listDataItems():
                if item.name() == "g14_volt2":
                    self.g14_w1.removeItem(item)
            g14_volt2 = self.g14_w1.plot(self.g14_volt2_x, self.g14_volt2_y, pen=(0, 191, 0), name="Volt 2")
            self.g14_w1_l.removeItem('g14_volt2')
            self.g14_w1_l.addItem(g14_volt2, 'g14_volt2')
        if (g14[2]):
            for item in self.g14_w1.listDataItems():
                if item.name() == "g14_curr1":
                    self.g14_w1.removeItem(item)
            g14_curr1 = self.g14_w1.plot(self.g14_curr1_x, self.g14_curr1_y, pen=(0, 0, 191), name="Curr 1")
            self.g14_w1_l.removeItem('g14_curr1')
            self.g14_w1_l.addItem(g14_curr1, 'g14_curr1')
        if (g14[3]):
            for item in self.g14_w1.listDataItems():
                if item.name() == "g14_curr2":
                    self.g14_w1.removeItem(item)
            g14_curr2 = self.g14_w1.plot(self.g14_curr2_x, self.g14_curr2_y, pen=(128, 128, 0), name="Curr 2")
            self.g14_w1_l.removeItem('g14_curr2')
            self.g14_w1_l.addItem(g14_curr2, 'g14_curr2')

        if (g14[4]):
            for item in self.g14_w2.listDataItems():
                if item.name() == "g14_hall1":
                    self.g14_w2.removeItem(item)
            g14_hall1 = self.g14_w2.plot(self.g14_hall1_x, self.g14_hall1_y, pen=(191, 0, 0), name="Hall 1")
            self.g14_w2_l.removeItem('g14_hall1')
            self.g14_w2_l.addItem(g14_hall1, 'g14_hall1')
        if (g14[5]):
            for item in self.g14_w2.listDataItems():
                if item.name() == "g14_hall2":
                    self.g14_w2.removeItem(item)
            g14_hall2 = self.g14_w2.plot(self.g14_hall2_x, self.g14_hall2_y, pen=(0, 191, 0), name="Hall 2")
            self.g14_w2_l.removeItem('g14_hall2')
            self.g14_w2_l.addItem(g14_hall2, 'g14_hall2')
        if (g14[6]):
            for item in self.g14_w2.listDataItems():
                if item.name() == "g14_pulse1":
                    self.g14_w2.removeItem(item)
            g14_pulse1 = self.g14_w2.plot(self.g14_pulse1_x, self.g14_pulse1_y, pen=(0, 0, 191), name="Pulse 1")
            self.g14_w2_l.removeItem('g14_pulse1')
            self.g14_w2_l.addItem(g14_pulse1, 'g14_pulse1')
        if (g14[7]):
            for item in self.g14_w2.listDataItems():
                if item.name() == "g14_pulse2":
                    self.g14_w2.removeItem(item)
            self.g14_w2.removeItem("g14_pulse2")
            g14_pulse2 = self.g14_w2.plot(self.g14_pulse2_x, self.g14_pulse2_y, pen=(128, 128, 0), name="Pulse 2")
            self.g14_w2_l.removeItem('g14_pulse2')
            self.g14_w2_l.addItem(g14_pulse2, 'g14_pulse2')

        if (g14[8]):
            for item in self.g14_w3.listDataItems():
                if item.name() == "g14_slhe":
                    self.g14_w3.removeItem(item)
            self.g14_w3.removeItem("g14_slhe")
            g14_slhe = self.g14_w3.plot(self.g14_slhe_x, self.g14_slhe_y, pen=(191, 0, 0), name="SLH E")
            self.g14_w3_l.removeItem('g14_slhe')
            self.g14_w3_l.addItem(g14_slhe, 'g14_slhe')
        if (g14[9]):
            for item in self.g14_w3.listDataItems():
                if item.name() == "g14_slhd":
                    self.g14_w3.removeItem(item)
            self.g14_w3.removeItem("g14_slhd")
            g14_slhd = self.g14_w3.plot(self.g14_slhd_x, self.g14_slhd_y, pen=(0, 191, 0), name="SLH D")
            self.g14_w3_l.removeItem('g14_slhd')
            self.g14_w3_l.addItem(g14_slhd, 'g14_slhd')
        if (g14[10]):
            for item in self.g14_w3.listDataItems():
                if item.name() == "g14_slve":
                    self.g14_w3.removeItem(item)
            self.g14_w3.removeItem("g14_slve")
            g14_slve = self.g14_w3.plot(self.g14_slve_x, self.g14_slve_y, pen=(0, 0, 191), name="SLV E")
            self.g14_w3_l.removeItem('g14_slve')
            self.g14_w3_l.addItem(g14_slve, 'g14_slve')
        if (g14[11]):
            for item in self.g14_w3.listDataItems():
                if item.name() == "g14_slvd":
                    self.g14_w3.removeItem(item)
            self.g14_w3.removeItem("g14_slvd")
            g14_slvd = self.g14_w3.plot(self.g14_slvd_x, self.g14_slvd_y, pen=(0, 0, 191), name="SLV D")
            self.g14_w3_l.removeItem('g14_slvd')
            self.g14_w3_l.addItem(g14_slvd, 'g14_slvd')

    def clearGraph(self):

        processedData = {}
        rawData = {}
        self.c_lock.acquire()
        self.d_lock.acquire()

        with open(self.saveDataFile, 'w') as outfile:
            json.dump(processedData, outfile, indent=4)
        with open(self.saveDataFileBU, 'w') as outfile:
            json.dump(processedData, outfile, indent=4)
        with open(self.saveRawFile, 'w') as outfile:
            json.dump(rawData, outfile, indent=4)
        with open(self.saveRawFileBackup, 'w') as outfile:
            json.dump(rawData, outfile, indent=4)

        self.c_lock.release()
        self.d_lock.release()

        self.ui.vehSaveEdit.setText('')
        self.ui.velSaveEdit.setText('')
        self.ui.surSaveEdit.setText('')
        self.ui.noteSaveEdit.setText('')


        self.addEntry("All")
        self.updateSensorEntryListWidget()

    def tabChangedCB(self):

        self.currentTabName = self.ui.tabWidgetGraphs.tabText(self.ui.tabWidgetGraphs.currentIndex()).split()[0]
        self.updateSensorEntryListWidget()

    def sensorEntryListICCB(self, item):
        slave, sensor, coords = item.data(32)
        xmin, xmax, ymin, ymax = coords
        xminmul = 0.95
        yminmul = 0.9
        xmaxmul = 1.05
        ymaxmul = 1.1
        if(slave == "1"):
            if(sensor == "17" or sensor == "18" or sensor == "19" or sensor == "33" or sensor == "34" or sensor == "35"):
                self.m14_w1.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])
            elif(sensor == "49" or sensor == "50" or sensor == "51"):
                self.m14_w2.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])
        elif(slave == "2"):
            if(sensor == "17" or sensor == "18" or sensor == "19"):
                self.m10_w1.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])
            elif(sensor == "33"):
                self.m10_w2.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])
        elif(slave == "3"):
            print("not implemented yet")
        elif(slave == "4"):
            print("not implemented yet")
    def updateSensorEntryListWidget(self):

        self.ui.sensorEntryListWidget.clear()
        slave = self.currentEntriesFilter[self.currentTabName]['key']

        for ef in self.currentEntriesFilter[self.currentTabName]['entries']:
            for entry in ef[1]:
                try:
                    dataListWin = slave, ef[0], self.Entries[slave]['sensors'][ef[0]]['dataListWin'][str(entry)]

                    listEntry = QtWidgets.QListWidgetItem()
                    listEntry.setText(str(ef[0])+"                        "+str(dataListWin[2][0]))
                    listEntry.setData(32, dataListWin)
                    self.ui.sensorEntryListWidget.addItem(listEntry)

                except KeyError:
                    print("Key not found")

    def getOpenfiles(self):

        items = os.listdir(self.DataFolderPath)
        items.remove('temp')

        folder, ok = QtWidgets.QInputDialog.getItem(self, 'Open Folder Name Dialog',
                                        "Open Data Folder:", items, 0, False)

        if ok and folder:

            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("Unsaved Data will be lost!")
            msg.setInformativeText("Are you sure you want to open?")
            msg.setWindowTitle("Conflict warning!")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            retval = msg.exec_()
            if retval == 0x4000:
                self.openFiles(folder)

    def getSaveFiles(self):

        if self.ui.noteSaveEdit.text() == '':
            preName = "V" + self.ui.vehSaveEdit.text() + "_" + self.ui.velSaveEdit.text() + "_" + self.ui.surSaveEdit.text()
        else:
            preName = "V" + self.ui.vehSaveEdit.text() + "_" + self.ui.velSaveEdit.text() + "_" + self.ui.surSaveEdit.text() + "_" + self.ui.noteSaveEdit.text()

        preName = preName + "_" + datetime.datetime.now().strftime("%Y-%m-%d")
        text, ok = QtWidgets.QInputDialog.getText(self, 'Save Folder Name Dialog', 'Save Data Folder to:', text=preName)
        folder = str(text)
        if ok:
            if folder in os.listdir(self.DataFolderPath):
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText("Data Folder already exists with the same name!")
                msg.setInformativeText("Are you sure you want to overwrite it?")
                msg.setWindowTitle("Conflict warning!")
                msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                retval = msg.exec_()
                if retval == 0x4000:
                    self.saveFiles(folder)
                    return
                elif retval == 0x10000:
                    self.getSaveFiles()
            else:
                os.mkdir(self.DataFolderPath + "/" + folder)
                self.saveFiles(folder)

    def saveFiles(self, folder):
        self.c_lock.acquire()
        self.d_lock.acquire()

        try:
            with open(self.saveDataFile) as json_file:
                processedData = json.load(json_file)
        except json.decoder.JSONDecodeError:
            try:
                with open(self.saveDataFileBU) as json_file:
                    processedData = json.load(json_file)
            except Exception:

                # if no file is found no entries are added
                processedData = {}
        except FileNotFoundError:

            # if no file is found no entries are added
            processedData = {}

        try:
            with open(self.saveRawFile) as json_file:
                rawData = json.load(json_file)
        except json.decoder.JSONDecodeError:
            try:
                with open(self.saveRawFileBackup) as json_file:
                    rawData = json.load(json_file)
            except FileNotFoundError:
                rawData = {}
        except FileNotFoundError:
            rawData = {}

        self.c_lock.release()
        self.d_lock.release()
        datapath = self.DataFolderPath + "/" + folder + "/processedData.json"
        datapathBU = self.DataFolderPath + "/" + folder + "/processedDataBU.json"
        datarawpath = self.DataFolderPath + "/" + folder + "/rawData.json"
        datarawpathBU = self.DataFolderPath + "/" + folder + "/rawDataBU.json"

        with open(datapath, 'w') as outfile:
            json.dump(processedData, outfile, indent=4)
        with open(datapathBU, 'w') as outfile:
            json.dump(processedData, outfile, indent=4)
        with open(datarawpath, 'w') as outfile:
            json.dump(rawData, outfile, indent=4)
        with open(datarawpathBU, 'w') as outfile:
            json.dump(rawData, outfile, indent=4)

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("File save successfully!")
        msg.setWindowTitle("File Saved")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def openFiles(self, folder):

        datapath = self.DataFolderPath + "/" + folder + "/processedData.json"
        datapathBU = self.DataFolderPath + "/" + folder + "/processedDataBU.json"
        datarawpath = self.DataFolderPath + "/" + folder + "/rawData.json"
        datarawpathBU = self.DataFolderPath + "/" + folder + "/rawDataBU.json"

        try:
            with open(datapath) as json_file:
                processedData = json.load(json_file)
        except Exception:
            try:
                with open(datapathBU) as json_file:
                    processedData = json.load(json_file)
            except Exception:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setText("Failed to Opened successfully!")
                msg.setWindowTitle("File not opened")
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg.exec_()
                return

        try:
            with open(datarawpath) as json_file:
                rawData = json.load(json_file)
        except Exception:
            try:
                with open(datarawpathBU) as json_file:
                    rawData = json.load(json_file)
            except Exception:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setText("Failed to Opened successfully!")
                msg.setWindowTitle("File not opened")
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg.exec_()
                return

        self.c_lock.acquire()
        self.d_lock.acquire()

        with open(self.saveDataFile, 'w') as outfile:
            json.dump(processedData, outfile, indent=4)
        with open(self.saveDataFileBU, 'w') as outfile:
            json.dump(processedData, outfile, indent=4)
        with open(self.saveRawFile, 'w') as outfile:
            json.dump(rawData, outfile, indent=4)
        with open(self.saveRawFileBackup, 'w') as outfile:
            json.dump(rawData, outfile, indent=4)

        self.c_lock.release()
        self.d_lock.release()

        self.addEntry("All")

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("File Opened successfully!")
        msg.setWindowTitle("File Opened")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def update_graph_timer_timeout(self):
        self.ten_second_timer_flag = True
        #print(self.ui.tabWidgetGraphs.tabText(self.ui.tabWidgetGraphs.currentIndex()).split()[0])
def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
