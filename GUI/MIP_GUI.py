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

        self.g10_w1 = self.ui.graphWindowG10.addPlot(row=0, col=0, title='Temperatura')
        self.g10_w1.showGrid(x=True, y=True, alpha=0.7)

        self.g10_w1_l = LegendItem((180,30), offset=(60,30))
        self.g10_w1_l.setParentItem(self.g10_w1)


        # Setup GraphicsLayoutWidget G14

        self.g14_w1 = self.ui.graphWindowG14.addPlot(row=0, col=0, title='Pos V')
        self.g14_w1.showGrid(x=True, y=True, alpha=0.7)

        self.g14_w1_l = LegendItem((80,30), offset=(60,30))
        self.g14_w1_l.setParentItem(self.g14_w1)

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
            m10force = True
            m10forcd = True
            
            g14_slve = True
            g14_slvd = True

            g10_tempb = True
            g10_tempt = True
            g10_tempa = True
            
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
            m10force = False
            m10forcd = False

            g14_slve = False
            g14_slvd = False

            g10_tempb = False
            g10_tempt = False
            g10_tempa = False

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
                        m10force = True
                    elif int(slaveKey) == 2 and int(sensorKey) == 35:
                        m10forcd = True

                    elif int(slaveKey) == 3 and int(sensorKey) == 17:
                        g14_slve = True
                    elif int(slaveKey) == 3 and int(sensorKey) == 19:
                        g14_slvd = True

                    elif int(slaveKey) == 4 and int(sensorKey) == 17:
                        g10_tempb = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 18:
                        g10_tempt = True
                    elif int(slaveKey) == 4 and int(sensorKey) == 19:
                        g10_tempa = True



        # UPDATE data lists

        # M10

        self.m10_acelx_x = []
        self.m10_acelx_y = []
        self.m10_acely_x = []
        self.m10_acely_y = []
        self.m10_acelz_x = []
        self.m10_acelz_y = []

        self.m10_forcae_x = []
        self.m10_forcae_y = []

        self.m10_forcad_x = []
        self.m10_forcad_y = []
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

        # m10_forcae_x
        if m10force:
            try:
                self.m10_forcae_x = self.Entries["2"]["sensors"]["33"]["time"]
                self.m10_forcae_y = self.Entries["2"]["sensors"]["33"]["dataR"]
            except Exception:
                None

        # m10_forcad_x
        if m10forcd:
            try:
                self.m10_forcad_x = self.Entries["2"]["sensors"]["35"]["time"]
                self.m10_forcad_y = self.Entries["2"]["sensors"]["35"]["dataR"]
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
        self.g10_tempb_x = []
        self.g10_tempb_y = []
        self.g10_tempt_x = []
        self.g10_tempt_y = []
        self.g10_tempa_x = []
        self.g10_tempa_y = []


        # CLEAR lists

        # g10_tempb
        if g10_tempb:
            try:
                self.g10_tempb_x = self.Entries["4"]["sensors"]["17"]["time"]
                self.g10_tempb_y = self.Entries["4"]["sensors"]["17"]["dataNR"]
            except Exception:
                None

        # g10_tempt
        if g10_tempt:
            try:
                self.g10_tempt_x = self.Entries["4"]["sensors"]["18"]["time"]
                self.g10_tempt_y = self.Entries["4"]["sensors"]["18"]["dataNR"]
            except Exception:
                None

        # g10_tempa
        if g10_tempa:
            try:
                self.g10_tempa_x = self.Entries["4"]["sensors"]["19"]["time"]
                self.g10_tempa_y = self.Entries["4"]["sensors"]["19"]["dataNR"]
            except Exception:
                None

        # G14

        # CLEAR lists
        self.g14_slve_x = []
        self.g14_slve_y = []
        self.g14_slvd_x = []
        self.g14_slvd_y = []

        # CLEAR lists

        # g14_slve
        if g14_slve:
            try:
                self.g14_slve_y = self.Entries["3"]["sensors"]["17"]["time"]
                self.g14_slve_x = self.Entries["3"]["sensors"]["17"]["dataR"]
            except Exception:
                None

        # g14_slvd
        if g14_slvd:
            try:
                self.g14_slvd_y = self.Entries["3"]["sensors"]["19"]["time"]
                self.g14_slvd_x = self.Entries["3"]["sensors"]["19"]["dataR"]
            except Exception:
                None


        if (m10acelx or m10acely or m10acelz or m10force or m10forcd):
            m10 = (m10acelx, m10acely, m10acelz, m10force, m10forcd)
        else:
            m10 = None
        if (m14_acelx or m14_acely or m14_acelz or m14_sl0 or m14_sl1 or m14_sl2 or m14_sl3 or m14_sl4 or m14_sl5):
            m14 = (m14_acelx, m14_acely, m14_acelz, m14_sl0, m14_sl1, m14_sl2, m14_sl3, m14_sl4, m14_sl5)
        else:
            m14 = None
        if (g10_tempb or g10_tempt or g10_tempa):
            g10 = (g10_tempb, g10_tempt, g10_tempa)
        else:
            g10 = None
        if (g14_slve or g14_slvd):
            g14 = (g14_slve, g14_slvd)
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
            acelx = self.m10_w1.plot(self.m10_acelx_x, self.m10_acelx_y, pen=(191, 0, 0), name="Acel X")
            self.m10_w1_l.removeItem('Acel X')
            self.m10_w1_l.addItem(acelx, 'Acel X')
        if (m10[1]):
            for item in self.m10_w1.listDataItems():
                if item.name() == "Acel Y":
                    self.m10_w1.removeItem(item)
            acely = self.m10_w1.plot(self.m10_acely_x, self.m10_acely_y, pen=(0, 191, 0), name="Acel Y")
            self.m10_w1_l.removeItem('Acel Y')
            self.m10_w1_l.addItem(acely, 'Acel Y')
        if (m10[2]):
            for item in self.m10_w1.listDataItems():
                if item.name() == "Acel Z":
                    self.m10_w1.removeItem(item)
            acelz = self.m10_w1.plot(self.m10_acelz_x, self.m10_acelz_y, pen=(0, 0, 191), name="Acel Z")
            self.m10_w1_l.removeItem('Acel Z')
            self.m10_w1_l.addItem(acelz, 'Acel Z')
        if (m10[3]):
            for item in self.m10_w2.listDataItems():
                if item.name() == "Força Esq":
                    self.m10_w2.removeItem(item)
            forcae = self.m10_w2.plot(self.m10_forcae_x, self.m10_forcae_y, pen=(191, 0, 0), name="Força Esq")
            self.m10_w2_l.removeItem('Força Esq')
            self.m10_w2_l.addItem(forcae, 'Força Esq')
        if (m10[4]):
            for item in self.m10_w2.listDataItems():
                if item.name() == "Força Dir":
                    self.m10_w2.removeItem(item)
            forcad = self.m10_w2.plot(self.m10_forcad_x, self.m10_forcad_y, pen=(0, 191, 0), name="Força Dir")
            self.m10_w2_l.removeItem('Força Dir')
            self.m10_w2_l.addItem(forcad, 'Força Dir')

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

        if (g10[0]):
            for item in self.g10_w1.listDataItems():
                if item.name() == "Temperatura Ambiente":
                    self.g10_w1.removeItem(item)
            g10_tempa = self.g10_w1.plot(self.g10_tempa_x, self.g10_tempa_y, pen=(191, 0, 0), name="Temperatura Ambiente")
            self.g10_w1_l.removeItem('Temperatura Ambiente')
            self.g10_w1_l.addItem(g10_tempa, 'Temperatura Ambiente')
        if (g10[1]):
            for item in self.g10_w1.listDataItems():
                if item.name() == "Temperatura Base":
                    self.g10_w1.removeItem(item)
            g10_tempb = self.g10_w1.plot(self.g10_tempb_x, self.g10_tempb_y, pen=(0, 191, 0), name="Temperatura Base")
            self.g10_w1_l.removeItem('Temperatura Base')
            self.g10_w1_l.addItem(g10_tempb, 'Temperatura Base')
        if (g10[2]):
            for item in self.g10_w1.listDataItems():
                if item.name() == "Temperatura Tampa":
                    self.g10_w1.removeItem(item)
            g10_tempt = self.g10_w1.plot(self.g10_tempt_x, self.g10_tempt_y, pen=(0, 0, 191), name="Temperatura Tampa")
            self.g10_w1_l.removeItem('Temperatura Tampa')
            self.g10_w1_l.addItem(g10_tempt, 'Temperatura Tampa')

    def addPlotG14(self, g14):

        # ADD PLOT PROCEDURE

        if (g14[0]):
            for item in self.g14_w1.listDataItems():
                if item.name() == "SLV E":
                    self.g14_w1.removeItem(item)
            self.g14_w1.removeItem("SLV E")
            g14_slve = self.g14_w1.plot(self.g14_slve_x, self.g14_slve_y, pen=(191, 0, 0), name="SLV E")
            self.g14_w1_l.removeItem('SLV E')
            self.g14_w1_l.addItem(g14_slve, 'SLV E')
        if (g14[1]):
            for item in self.g14_w1.listDataItems():
                if item.name() == "SLV SLV D":
                    self.g14_w1.removeItem(item)
            self.g14_w1.removeItem("SLV D")
            g14_slvd = self.g14_w1.plot(self.g14_slvd_x, self.g14_slvd_y, pen=(0, 191, 0), name="SLV D")
            self.g14_w1_l.removeItem('SLV D')
            self.g14_w1_l.addItem(g14_slvd, 'SLV D')

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
        yminmul = 0
        xmaxmul = 1.05
        ymaxmul = 1.1

        if(slave == "1"):

            if(sensor == "17" or sensor == "18" or sensor == "19" or sensor == "33" or sensor == "34" or sensor == "35"):
                self.m14_w1.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])
                self.ui.labelMinLineAM14.setText("Min: "+str(round(ymin, 2)))
                self.ui.labelMaxLineAM14.setText("Max: " + str(round(ymax, 2)))

            elif(sensor == "49" or sensor == "50" or sensor == "51"):
                self.m14_w2.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])
                self.ui.labelMinLineBM14.setText("Min: "+str(round(ymin, 2)))
                self.ui.labelMaxLineBM14.setText("Max: " + str(round(ymax, 2)))

        elif(slave == "2"):

            if(sensor == "17" or sensor == "18" or sensor == "19"):
                self.m10_w1.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])
                self.ui.labelMinLineAM10.setText("Min: "+str(round(ymin, 2)))
                self.ui.labelMaxLineAM10

            elif(sensor == "33" or sensor == "35"):
                self.m10_w2.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])
                self.ui.labelMinLineBM10.setText("Min: "+str(round(ymin, 2)))
                self.ui.labelMaxLineBM10.setText("Max: " + str(round(ymax, 2)))

        elif(slave == "3"):

            if(sensor == "17" or sensor == "19"):
                self.g14_w1.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])

        elif(slave == "4"):

            if(sensor == "17" or sensor == "18" or sensor == "19"):
                self.g10_w1.setRange(xRange=[xmin*xminmul, xmax*xmaxmul], yRange=[ymin*yminmul, ymax*ymaxmul])

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
