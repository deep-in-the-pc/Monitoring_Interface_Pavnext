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
from gui.MI_GUI_0301 import Ui_MainWindow
from pyqtgraph import *

#TODO add graphWindow to G10 & G14

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

        #TODO Add Save and Open to config file

        #configure serial connection

        self.d_lock = threading.Lock()

        self.serialListenerThread = serialThread(1, "SerialListener", self.d_lock)

        self.serialConnectionParameters = list()
        self.serialConnectionParameters.append(serial.EIGHTBITS)
        self.serialConnectionParameters.append(serial.PARITY_NONE)
        self.serialConnectionParameters.append(serial.STOPBITS_ONE)
        self.serialConnectionParameters.append(500000)


        #Setup GraphicsLayoutWidget M10

        self.m10_w1 = self.ui.graphWindowM10.addPlot(row=0, col=0, title='Acel')
        self.m10_w2 = self.ui.graphWindowM10.addPlot(row=1, col=0, title='Força')

        self.m10_w1_l = LegendItem((80,30), offset=(60,30))  # args are (size, offset)
        self.m10_w1_l.setParentItem(self.m10_w1)   # Note we do NOT call plt.addItem in this case

        self.m10_w2_l = LegendItem((80,30), offset=(60,30))  # args are (size, offset)
        self.m10_w2_l.setParentItem(self.m10_w2)   # Note we do NOT call plt.addItem in this case

        #Setup GraphicsLayoutWidget M14

        self.m14_w1 = self.ui.graphWindowM14.addPlot(row=0, col=0, title='Pos V')
        self.m14_w2 = self.ui.graphWindowM14.addPlot(row=1, col=0, title='Acel')

        self.m14_w1_l = LegendItem((80,30), offset=(60,30))
        self.m14_w1_l.setParentItem(self.m14_w1)

        self.m14_w2_l = LegendItem((80,30), offset=(60,30))
        self.m14_w2_l.setParentItem(self.m14_w2)

        self.addEntry()

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
        # if self.saveFileBackup == None or self.saveFile == None:
        #     self.getSavefiles()
        #     return
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
        self.serialListenerThread.closeEvent.set()
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
            #self.d_lock.release()
            None
        self.d_lock.release()

        #UPDATE data lists

        #M10

        self.m10_acelx_x = []
        self.m10_acelx_y = []
        self.m10_acely_x = []
        self.m10_acely_y = []
        self.m10_acelz_x = []
        self.m10_acelz_y = []

        self.m10_forca_x = []
        self.m10_forca_y = []





        #m10_acelx
        try:
            for data in self.Entries["0"]["sensors"]["17"]["entries"]:
                self.m10_acelx_y = self.m10_acelx_y + data["data"]
            self.m10_acelx_x = [i for i in range(len(self.m10_acelx_y))]
            m10acelx = True
        except Exception:
            m10acelx = False
        #m10_acely
        try:
            for data in self.Entries["0"]["sensors"]["18"]["entries"]:
                self.m10_acelz_y = self.m10_acely_y + data["data"]
            self.m10_acely_x = [i for i in range(len(self.m10_acely_y))]
            m10acely = True
        except Exception:
            m10acely = False
        #m10_acelz
        try:
            for data in self.Entries["0"]["sensors"]["19"]["entries"]:
                self.m10_acelz_y = self.m10_acelz_y + data["data"]
            self.m10_acelz_x = [i for i in range(len(self.m10_acelz_y))]
            m10acelz = True
        except Exception:
            m10acelz = False
        #m10_forca_x
        try:
            for data in self.Entries["0"]["sensors"]["33"]["entries"]:
                self.m10_forca_y = self.m10_forca_y + data["data"]
            self.m10_forca_x = [i for i in range(len(self.m10_forca_y))]
            m10forc = True
        except Exception:
            m10forc = False


        #M14

        #CLEAR lists
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
        try:
            for data in self.Entries["1"]["sensors"]["33"]["entries"]:
                self.m14_acelx_y = self.m14_acelx_y + data["data"]
            self.m14_acelx_x = [i for i in range(len(self.m14_acelx_y))]
            m14_acelx = True
        except Exception:
            m14_acelx = False

        #m14_acely
        try:
            for data in self.Entries["1"]["sensors"]["34"]["entries"]:
                self.m14_acely_y = self.m14_acely_y + data["data"]
            self.m14_acely_x = [i for i in range(len(self.m14_acely_y))]
            m14_acely = True
        except Exception:
            m14_acely = False

        #m14_acelz
        try:
            for data in self.Entries["1"]["sensors"]["35"]["entries"]:
                self.m14_acelz_y = self.m14_acelz_y + data["data"]
            self.m14_acelz_x = [i for i in range(len(self.m14_acelz_y))]
            m14_acelz = True
        except Exception:
            m14_acelz = False
        #m14_sl0
        try:
            for data in self.Entries["1"]["sensors"]["17"]["entries"]:
                self.m14_sl0_y = self.m14_sl0_y + data["data"]
            self.m14_sl0_x = [i for i in range(len(self.m14_sl0_y))]
            m14_sl0 = True
        except Exception:
            m14_sl0 = False
        #m14_sl1
        try:
            for data in self.Entries["1"]["sensors"]["18"]["entries"]:
                self.m14_sl1_y = self.m14_sl1_y + data["data"]
            self.m14_sl1_x = [i for i in range(len(self.m14_sl1_y))]
            m14_sl1 = True
        except Exception:
            m14_sl1 = False
        #m14_sl2
        try:
            for data in self.Entries["1"]["sensors"]["19"]["entries"]:
                self.m14_sl2_y = self.m14_sl2_y + data["data"]
            self.m14_sl2_x = [i for i in range(len(self.m14_sl2_y))]
            m14_sl2 = True
        except Exception:
            m14_sl2 = False
        #m14_sl3
        try:
            for data in self.Entries["1"]["sensors"]["49"]["entries"]:
                self.m14_sl3_y = self.m14_sl3_y + data["data"]
            self.m14_sl3_x = [i for i in range(len(self.m14_sl3_y))]
            m14_sl3 = True
        except Exception:
            m14_sl3 = False
        #m14_sl4
        try:
            for data in self.Entries["1"]["sensors"]["50"]["entries"]:
                self.m14_sl4_y = self.m14_sl4_y + data["data"]
            self.m14_sl4_x = [i for i in range(len(self.m14_sl4_y))]
            m14_sl4 = True
        except Exception:
            m14_sl4 = False
        #m14_sl5
        try:
            for data in self.Entries["1"]["sensors"]["51"]["entries"]:
                self.m14_sl5_y = self.m14_sl5_y + data["data"]
            self.m14_sl5_x = [i for i in range(len(self.m14_sl5_y))]
            m14_sl5 = True
        except Exception:
            m14_sl5 = False
        m10 = (m10acelx, m10acely, m10acelz, m10forc)
        m14 = (m14_acelx, m14_acely, m14_acelz, m14_sl0, m14_sl1, m14_sl2, m14_sl3, m14_sl4, m14_sl5)
        self.updatePlots(m10=m10, m14=m14)


    def updatePlots(self, m10=None, m14=None, g10=None, g14=None):
        print(m10)
        print(m14)
        if(m10):
            print("m10")
            self.addPlotM10(m10)
        if(m14):
            print("m14")
            self.addPlotM14(m14)


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

    def addPlotM10(self, m10):
        # ADD PLOT PROCEDURE
        self.m10_w1.clear()

        if (m10[0]):
            acelx = self.m10_w1.plot(self.m10_acelx_x, self.m10_acelx_y, pen='r')
            self.m10_w1_l.removeItem('Acel X')
            self.m10_w1_l.addItem(acelx, 'Acel X')
        if (m10[1]):
            acely = self.m10_w1.plot(self.m10_acely_x, self.m10_acely_y, pen='g')
            self.m10_w1_l.removeItem('Acel Y')
            self.m10_w1_l.addItem(acely, 'Acel Y')
        if (m10[2]):
            acelz = self.m10_w1.plot(self.m10_acelz_x, self.m10_acelz_y, pen='b')
            self.m10_w1_l.removeItem('Acel Z')
            self.m10_w1_l.addItem(acelz, 'Acel Z')
        if (m10[3]):
            forca = self.m10_w2.plot(self.m10_forca_x, self.m10_forca_y, pen='r')
            self.m10_w2_l.removeItem('Força')
            self.m10_w2_l.addItem(forca, 'Força')











    def addPlotM14(self, m14):
        # ADD PLOT PROCEDURE

        if (m14[3]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl0":
                    self.m14_w1.removeItem(item)
            sl0 = self.m14_w1.plot(self.m14_sl0_x, self.m14_sl0_y, pen='r', name="sl0")
            self.m14_w1_l.removeItem('sl0')
            self.m14_w1_l.addItem(sl0, 'sl0')
        if (m14[4]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl1":
                    self.m14_w1.removeItem(item)
            sl1 = self.m14_w1.plot(self.m14_sl1_x, self.m14_sl1_y, pen='g', name="sl1")
            self.m14_w1_l.removeItem('sl1')
            self.m14_w1_l.addItem(sl1, 'sl1')
        if (m14[5]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl2":
                    self.m14_w1.removeItem(item)
            sl2 = self.m14_w1.plot(self.m14_sl2_x, self.m14_sl2_y, pen='b', name="sl2")
            self.m14_w1_l.removeItem('sl2')
            self.m14_w1_l.addItem(sl2, 'sl2')
        if (m14[6]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl3":
                    self.m14_w1.removeItem(item)
            sl3 = self.m14_w1.plot(self.m14_sl3_x, self.m14_sl3_y, pen=(255, 255, 0), name="sl3")
            self.m14_w1_l.removeItem('sl3')
            self.m14_w1_l.addItem(sl3, 'sl3')
        if (m14[7]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl4":
                    self.m14_w1.removeItem(item)
            sl4 = self.m14_w1.plot(self.m14_sl4_x, self.m14_sl4_y, pen=(0, 255, 255), name="sl4")
            self.m14_w1_l.removeItem('sl4')
            self.m14_w1_l.addItem(sl4, 'sl4')
        if (m14[8]):
            for item in self.m14_w1.listDataItems():
                if item.name() == "sl5":
                    self.m14_w1.removeItem(item)
            sl5 = self.m14_w1.plot(self.m14_sl5_x, self.m14_sl5_y, pen=(255, 0, 255), name="sl5")
            self.m14_w1_l.removeItem('sl5')
            self.m14_w1_l.addItem(sl5, 'sl5')


        if(m14[0]):
            for item in self.m14_w2.listDataItems():
                if item.name() == "acelx":
                    self.m14_w2.removeItem(item)
            acelx = self.m14_w2.plot(self.m14_acelx_x, self.m14_acelx_y, pen='r', name="acelx")
            self.m14_w2_l.removeItem('Acel X')
            self.m14_w2_l.addItem(acelx, 'Acel X')
        if (m14[1]):
            for item in self.m14_w2.listDataItems():
                if item.name() == "acely":
                    self.m14_w2.removeItem(item)
            self.m14_w2.removeItem("acely")
            acely = self.m14_w2.plot(self.m14_acely_x, self.m14_acely_y, pen='g', name="acely")
            self.m14_w2_l.removeItem('Acel Y')
            self.m14_w2_l.addItem(acely, 'Acel Y')
        if (m14[2]):
            for item in self.m14_w2.listDataItems():
                if item.name() == "acelz":
                    self.m14_w2.removeItem(item)
            self.m14_w2.removeItem("acelz")
            acelz = self.m14_w2.plot(self.m14_acelz_x, self.m14_acelz_y, pen='b', name="acelz")
            self.m14_w2_l.removeItem('Acel Z')
            self.m14_w2_l.addItem(acelz, 'Acel Z')


        print(len(self.m14_sl0_x), len(self.m14_sl1_x), len(self.m14_sl2_x), len(self.m14_sl3_x), len(self.m14_sl4_x), len(self.m14_sl5_x))
        print(len(self.m14_sl0_y), len(self.m14_sl1_y), len(self.m14_sl2_y), len(self.m14_sl3_y), len(self.m14_sl4_y), len(self.m14_sl5_y))
        print(len(self.m14_acelx_x), len(self.m14_acely_x), len(self.m14_acelz_x))
        print(len(self.m14_acelx_y), len(self.m14_acely_y), len(self.m14_acelz_y))
def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
