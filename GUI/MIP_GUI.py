import sys
import threading
from serialListener import *
from time import sleep
from util import *
from math import ceil
#for UI
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from gui.MI_GUI_02 import Ui_MainWindow

#for plots
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

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

        #Add entries to list
        self.addEntries()

        #targetComConnectButton Callback
        self.ui.targetComConnectButton.clicked.connect(self.targetConnectionCB)
        #updateCOMButton CallBack
        self.ui.updateCOMButton.clicked.connect(self.getCOMList)
        #combo box Callback
        self.ui.targetComCB.activated[str].connect(self.onTargetComCBActivated)






    def startThread(self):
        self.serialListenerThread = serialThread(1, "SerialListener", self.d_lock)

        #Signal from Thread
        self.serialListenerThread.addEntrySignal.connect(self.addEntry)

        self.serialConnectionParameters.append(self.serialCOM)
        self.serialListenerThread.setParameteres(self.serialConnectionParameters)
        self.serialListenerThread.start()

    #COMMUNICATION

    def getCOMList(self):
        self.ui.targetComCB.clear()
        self.ui.targetComCB.addItems([comport.device for comport in serial.tools.list_ports.comports()])

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

    #ALTERING GUI

    # def addGraphs(self, string):
    #
    #     try:
    #         self.moduleL = 0 #potenciometro linear
    #         self.moduleE = 0 #encoder linear
    #         self.moduleT = 0 #ToF
    #         self.moduleA = 0 #acelarometro
    #         self.moduleE = 0 #extensometro
    #         self.moduleH = 0 #Hall
    #         for vars in string.split('-'):
    #             print(vars)
    #             id = vars[0]
    #             n = vars[1:]
    #             print(id,n)
    #             if(id == 'M'):
    #                 self.moduleType = "Molas " + n
    #             if(id == 'G'):
    #                 self.moduleType = "Gerador " + n
    #             if(id == 'L'):
    #                 print(n)
    #                 self.moduleL = int(n)
    #                 positions = [(i, j) for i in range(ceil(self.moduleL / 2)) for j in range(2)]
    #                 names = ["Potênciometro Linear " + str(pos) for pos in positions]
    #                 for i in range(self.moduleL):
    #                     self.moduleLList.append(PlotCanvas(names[i]))
    #             if(id == 'E'):
    #                 self.moduleE = int(n)
    #                 for i in range(self.moduleE):
    #                     self.moduleEList.append(PlotCanvas())
    #             if(id == 'T'):
    #                 self.moduleT = int(n)
    #                 for i in range(self.moduleT):
    #                     self.moduleTList.append(PlotCanvas())
    #             if(id == 'A'):
    #                 self.moduleA = int(n)
    #                 name = "Acelarometro " + str((0,0))
    #                 self.moduleAList.append(PlotCanvas(name))
    #             if(id == 'E'):
    #                 self.moduleE = int(n)
    #                 for i in range(self.moduleE):
    #                     self.moduleEList.append(PlotCanvas())
    #             if(id == 'H'):
    #                 self.moduleH = int(n)
    #                 for i in range(self.moduleH):
    #                     self.moduleHList.append(PlotCanvas())
    #         grid = QtWidgets.QGridLayout()
    #         positions = [(j, i) for i in range(ceil(self.moduleL/2)) for j in range(2)]
    #
    #         for i, position in enumerate(positions):
    #
    #             grid.addWidget(self.moduleLList[i], *position)
    #
    #         self.ui.graphFrame.setLayout(grid)
    #     except Exception as err:
    #         print(str(err))

    def addEntry(self):
        #Used on trigger by thread signal
        self.d_lock.acquire()

        try:
            with open('newData.json') as json_file:
                self.Entries = json.load(json_file)
        except FileNotFoundError:
            #if no file is found no entries are added
            return

        self.d_lock.release()

        self.ui.sensorEntryListWidget.clear()

        for key1, value1 in self.Entries.items():
            for key2, value2 in value1.items():
                for entry in value2:
                    title=key1+key2+"\t"+str(entry['size'])
                    self.ui.sensorEntryListWidget.addItem(title)


    def addEntries(self):
        #Used on startup to fill in data
        self.d_lock.acquire()

        try:
            with open('newData.json') as json_file:
                self.Entries = json.load(json_file)
        except FileNotFoundError:
            #if no file is found no entries are added
            return

        self.d_lock.release()
        for key1, value1 in self.Entries.items():
            for key2, value2 in value1.items():
                for entry in value2:
                    title=key1+key2+"\t"+str(entry['size'])
                    self.ui.sensorEntryListWidget.addItem(title)


class PlotCanvas(FigureCanvas):

    def __init__(self, name, parent=None,width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.name = name
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        data = [random.random() for i in range(25)]
        ax = self.figure.add_subplot(111)
        ax.plot(data, 'r-')
        ax.set_title(self.name)
        self.draw()


def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
