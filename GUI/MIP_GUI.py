#for serial comms
import threading
import serial.tools.list_ports
import serial
import sys
from time import sleep
from util import *
from math import ceil
#for UI
from PyQt5 import QtWidgets, QtGui, QtCore
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

        #initialize combo box
        self.getCOMList()

        if self.ui.targetComCB.currentText()=='':
            self.serialCOM = None
        else:
            self.serialCOM = self.ui.targetComCB.currentText()

        #window arrangement
        self.currentSetup = None
        #module vars
        self.moduleType = None
        self.moduleL = 0 #potenciometro linear
        self.moduleE = 0 #encoder linear
        self.moduleT = 0 # ToF
        self.moduleA = 0 # acelarometro
        self.moduleE = 0 # extensometro
        self.moduleH = 0 # Hall
        #graphLists
        self.moduleLList = []
        self.moduleEList = []
        self.moduleTList = []
        self.moduleAList = []
        self.moduleEList = []
        self.moduleHList = []
        #configure serial connection
        self.serialListenerThread = serialThread(1, "SerialListener")
        self.serialConnectionParameters = list()
        self.serialConnectionParameters.append(serial.EIGHTBITS)
        self.serialConnectionParameters.append(serial.PARITY_NONE)
        self.serialConnectionParameters.append(serial.STOPBITS_ONE)
        self.serialConnectionParameters.append(57600)
        #targetComConnectButton Callback
        self.ui.targetComConnectButton.clicked.connect(self.targetConnectionCB)
        #updateCOMButton CallBack
        self.ui.updateCOMButton.clicked.connect(self.getCOMList)
        #combo box Callback
        self.ui.targetComCB.activated[str].connect(self.onTargetComCBActivated)


    #COMMUNICATION

    def getCOMList(self):
        self.ui.targetComCB.clear()
        self.ui.targetComCB.addItems([comport.device for comport in serial.tools.list_ports.comports()])

    def targetConnectionCB(self):
        if self.serialListenerThread.is_alive():
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
            self.serialListenerThread = serialThread(1, "SerialListener")
            self.serialConnectionParameters.append(self.serialCOM)
            self.serialListenerThread.setParameteres(self.serialConnectionParameters)
            self.serialListenerThread.start()
            if self.serialListenerThread.is_alive():
                self.ui.connectionStatusLabel.setText("Connection Status: Online")
                return 1
            else:
                return 0
        except Exception as err:
            print(str(err))
    def closeConnetion(self):
        #Set event flag to close thread
        self.serialListenerThread.event.set()
        print(self.serialListenerThread.is_alive())
        self.ui.connectionStatusLabel.setText("Connection Status: Offline")

    #ALTERING GUI

    def addGraphs(self, string):
        #TODO FIX/ADD this when entry selection is added
        try:
            self.moduleL = 0 #potenciometro linear
            self.moduleE = 0 #encoder linear
            self.moduleT = 0 #ToF
            self.moduleA = 0 #acelarometro
            self.moduleE = 0 #extensometro
            self.moduleH = 0 #Hall
            for vars in string.split('-'):
                print(vars)
                id = vars[0]
                n = vars[1:]
                print(id,n)
                if(id == 'M'):
                    self.moduleType = "Molas " + n
                if(id == 'G'):
                    self.moduleType = "Gerador " + n
                if(id == 'L'):
                    print(n)
                    self.moduleL = int(n)
                    positions = [(i, j) for i in range(ceil(self.moduleL / 2)) for j in range(2)]
                    names = ["Potênciometro Linear " + str(pos) for pos in positions]
                    for i in range(self.moduleL):
                        self.moduleLList.append(PlotCanvas(names[i]))
                if(id == 'E'):
                    self.moduleE = int(n)
                    for i in range(self.moduleE):
                        self.moduleEList.append(PlotCanvas())
                if(id == 'T'):
                    self.moduleT = int(n)
                    for i in range(self.moduleT):
                        self.moduleTList.append(PlotCanvas())
                if(id == 'A'):
                    self.moduleA = int(n)
                    name = "Acelarometro " + str((0,0))
                    self.moduleAList.append(PlotCanvas(name))
                if(id == 'E'):
                    self.moduleE = int(n)
                    for i in range(self.moduleE):
                        self.moduleEList.append(PlotCanvas())
                if(id == 'H'):
                    self.moduleH = int(n)
                    for i in range(self.moduleH):
                        self.moduleHList.append(PlotCanvas())
            grid = QtWidgets.QGridLayout()
            positions = [(j, i) for i in range(ceil(self.moduleL/2)) for j in range(2)]

            for i, position in enumerate(positions):

                grid.addWidget(self.moduleLList[i], *position)

            self.ui.graphFrame.setLayout(grid)
        except Exception as err:
            print(str(err))

class serialThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.threadID = threadID
        self.name = name
        self.serialConnection = serial.Serial()

    def setParameteres(self, parameters):
        self.serialConnection.bytesize = parameters[0]
        self.serialConnection.parity = parameters[1]
        self.serialConnection.stopbits = parameters[2]
        self.serialConnection.baudrate = parameters[3]
        self.serialConnection.port = parameters[4]
    def run(self):
        #TODO Serial Listener loop
        while not self.event.is_set():
            print("im up")
            sleep(2)



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
