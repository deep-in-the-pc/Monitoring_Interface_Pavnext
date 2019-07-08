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
import math
# for UI
from PyQt5 import QtWidgets, QtGui, QtCore

try:
    from QtCore import QString
except ImportError:
    QString = str
from PyQt5.QtCore import QThread, pyqtSignal
from gui.MI_GUI_04 import Ui_MainWindow
from pyqtgraph import *

class Sensor():
    def __init__(self, id, parameters):
        self.sensor = id
        self.function = parameters['function']
        self.status = parameters['status']
        self.restval = parameters['restval']
        self.position = parameters['position']
        self.setup()




    def setup(self):
        lookup = {0: "Deslocamento linear vertical", 1: "Deslocamento linear horizontal", 2: "Acelerómetro  Eixo X", 3: "Acelerómetro Eixo Y", 4: "Acelerómetro Eixo Z", 5: "Extensômetro", 6: "Encoder Linear", 7: "temperatura", 8: "humidade", 9: "luminosidade", 10: "tensão", 11: "corrente", 12: "rotações pulsos", 13: "rotações hall", 14: "time of flight"}
        self.type = lookup[self.function]

    def getType(self):
        return self.type

    def getPosition(self):
        return self.position

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

    def getUnit(self):

        lookup = {0:"M100", 1:"G100", 2:"M140", 3:"G140"}

        return lookup[self.unit]

    def getSensors_GFX(self):
        sensors = {}
        for sensor in self.sensors_list:
            type = sensor.getType()
            if type not in sensors:
                sensors[type] = []
            sensors[type].append(sensor.getPosition())
        return sensors

    def sensorToType(self, sensor):

        for s in self.sensors_list:
            if s.id == sensor:
                return s.getType()

        return None

    def typeToUnits(self, type):

        lookup = {"Deslocamento linear vertical" : "mm", "Deslocamento linear horizontal" : "mm", "Acelerómetro  Eixo X" : "g", "Acelerómetro Eixo Y" : "g", "Acelerómetro Eixo Z" : "g", "Extensômetro" : "N", "Encoder Linear" : "mm", "temperatura" : "ºC", "humidade" : "HA", "luminosidade" : "lx", "tensão" : "V", "corrente" : "A", "rotações pulsos" : "RPM", "rotações hall" : "RPM", "time of flight" : "mm"}

        return lookup[type]
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

        # LOCKED UNTIL IMPLEMENTED

        self.ui.savePushButton.setEnabled(False)
        self.ui.openPushButton.setEnabled(False)




    def setupVariables(self):
        #DATA
        self.headerInfo = None
        self.rawEntries = list()

        #Serial thread
        self.serialListenerThread = serialThread(1, "SerialListener")
        self.serialListenerThread.addRawEntrySignal[list].connect(self.addRawEntry)
        self.serialListenerThread.closedSignal.connect(self.serialThreadClosed)
        self.serialListenerThread.gotHeaderSignal[dict].connect(self.serialThreadGotHeader)
        self.tabContainer = {}
        self.graphsContainer = {}

        self._isConnected = False

        #Process thread
        self.processQueue = queue.Queue()


    def setupCallbacks(self):
        self.ui.targetComConnectButton.clicked.connect(self.establishConnection)
        self.ui.targetComCB.currentIndexChanged.connect(self.changeCOMCB)

    def setupTimers(self):
        self.comlist_qtimer = QtCore.QTimer(self)
        self.comlist_qtimer.timeout.connect(self.getCOMList)
        self.comlist_qtimer_interval = round(1000/10) #10hz
        self.comlist_qtimer.start(self.comlist_qtimer_interval)
        self.guiupdate_qtimer = QtCore.QTimer(self)
        self.guiupdate_qtimer.timeout.connect(self.updatePlots)
        self.guiupdate_qtimer_interval = round(1000/60) #60hz

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

    def changeCOMCB(self):
        self.serialCOM = self.ui.targetComCB.currentText()

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
        #Stop Plot update timer
        #self.guiupdate_qtimer.stop()

    def serialThreadGotHeader(self, header):
        #Setup tabs
        self.headerInfo = header
        self.setupGraphTabs()
        #Update connection states
        self._isConnected = True
        self.ui.targetComConnectButton.setEnabled(True)
        self.ui.targetComConnectButton.setText("Disconnect")
        #Start Plot update timer
        self.guiupdate_qtimer.start()

    def addRawEntry(self, data):
        module = data[0]
        sensor = data[1]
        rawData = np.array(data[2])
        time = np.array(data[3])
        self.rawEntries.append(data)

        for mod in self.modules_list:
            if mod.module == module:
                unit = mod.getUnit()
                for sen in mod.sensors_list:
                    if sen.sensor == sensor:
                        type = sen.getType()
        for idx, inst in enumerate(time):

            self.graphsContainer[unit][type]['sensors'][sensor]['time'][inst] = inst

            if type == "Deslocamento linear vertical" or type == "Deslocamento linear horizontal":
                self.graphsContainer[unit][type]['sensors'][sensor]['data'][inst] = (rawData[idx]/1024.0)*30.0
            elif type == "Acelerómetro  Eixo X" or type == "Acelerómetro Eixo Y" or type == "Acelerómetro Eixo Z":
                self.graphsContainer[unit][type]['sensors'][sensor]['data'][inst] = (((rawData[idx] / 1024.0) * 3.3)-1.65)/0.0065
            elif type == "tensão":
                self.graphsContainer[unit][type]['sensors'][sensor]['data'][inst] = (rawData[idx] / 1024.0) * 33.0
            elif type == "corrente":
                self.graphsContainer[unit][type]['sensors'][sensor]['data'][inst] = (rawData[idx] / 1024.0) * 3.3
            elif type == "rotações pulsos" or "rotações hall":
                self.graphsContainer[unit][type]['sensors'][sensor]['data'][inst] = rawData[idx]
            else:
                self.graphsContainer[unit][type]['sensors'][sensor]['data'][inst] = rawData[idx]

        self.graphsContainer[unit][type]['sensors'][sensor]['pos'] = inst

    def setupGraphTabs(self):
        self.modules_list = []
        if not self.headerInfo == None:
            for n_slave in self.headerInfo:
                self.modules_list.append(Module(n_slave, self.headerInfo[n_slave]))
        for module in self.modules_list:

            #Setup Tab

            print(module)
            unit = module.getUnit()
            self.tabContainer[unit] = {}
            self.tabContainer[unit]['widget'] = QtGui.QWidget()
            index = self.ui.slaveTabWidget.addTab(self.tabContainer[unit]['widget'], unit)
            self.ui.slaveTabWidget.setCurrentIndex(index)
            self.tabContainer[unit]['tablayout'] = QtGui.QGridLayout()
            self.tabContainer[unit]['groupboxlayout'] = QtWidgets.QHBoxLayout()
            sensor_list = module.getSensors_GFX()
            for type in sensor_list:
                cb_groupbox = QtWidgets.QGroupBox(type)
                cb_h_layout = QtWidgets.QHBoxLayout()
                for sensor in sensor_list[type]:
                    self.tabContainer[unit][sensor] = QtWidgets.QCheckBox(str(hex(sensor)))
                    self.tabContainer[unit][sensor].setCheckState(2)
                    self.tabContainer[unit][sensor].stateChanged[int].connect(self.moduleTypeSensorCheckboxCB)
                    cb_h_layout.addWidget(self.tabContainer[unit][sensor])
                cb_groupbox.setLayout(cb_h_layout)
                self.tabContainer[unit]['groupboxlayout'].addWidget(cb_groupbox)

            self.tabContainer[unit]['tablayout'].addLayout(self.tabContainer[unit]['groupboxlayout'], 9, 0, 1, -1)

            self.tabContainer[unit]['graphicsview'] = GraphicsLayoutWidget(self)

            self.tabContainer[unit]['tablayout'].addWidget(self.tabContainer[unit]['graphicsview'], 0, 0, 9, -1)

            self.tabContainer[unit]['widget'].setLayout(self.tabContainer[unit]['tablayout'])

            #Setup Plots
            self.graphsContainer[unit] = {}
            for type in sensor_list:
                self.graphsContainer[unit][type] = {}
                self.graphsContainer[unit][type]['sensors'] = {}
                self.graphsContainer[unit][type]['units'] = module.typeToUnits(type)
                for sensor in sensor_list[type]:

                    self.graphsContainer[unit][type]['sensors'][sensor] = {}
                    self.graphsContainer[unit][type]['sensors'][sensor]['display'] = True
                    self.graphsContainer[unit][type]['sensors'][sensor]['time'] = np.empty(60000, dtype=np.single)
                    self.graphsContainer[unit][type]['sensors'][sensor]['time'].fill(np.nan)
                    self.graphsContainer[unit][type]['sensors'][sensor]['data'] = np.empty(60000, dtype=np.single)
                    self.graphsContainer[unit][type]['sensors'][sensor]['data'].fill(np.nan)
                    self.graphsContainer[unit][type]['sensors'][sensor]['pos'] = 0
                    self.graphsContainer[unit][type]['sensors'][sensor]['plot'] = None

            self.graphViewSetup(unit)

    def moduleTypeSensorCheckboxCB(self, state):
        ch = self.sender()
        gb = ch.parent()
        tab = gb.parent().parent().parent()
        unit = tab.tabText(tab.currentIndex())
        type = ch.parent().title()
        sensor = int(ch.text(), 16)
        if state == 2:

            self.graphsContainer[unit][type]['sensors'][sensor]['display'] = True

        if state == 0:
            self.graphsContainer[unit][type]['sensors'][sensor]['display'] = False

        self.graphViewSetup(unit)
        print(state, ch.text(), ch.parent().title(), tab.tabText(tab.currentIndex()))

    def graphViewSetup(self, unit):
        self.tabContainer[unit]['graphicsview'].clear()
        row = 0
        for type in self.graphsContainer[unit]:
            for sensor in self.graphsContainer[unit][type]['sensors']:
                plot = False
                if self.graphsContainer[unit][type]['sensors'][sensor]['display'] == True:
                    plot = True
                    break
            for sensor in self.graphsContainer[unit][type]['sensors']:
                self.graphsContainer[unit][type]['sensors'][sensor]['plot'] = None
            if plot:
                self.graphsContainer[unit][type]['plot'] = PlotItem(title=type, labels={'left': self.modules_list[0].typeToUnits(type) + " / unit", 'bottom': "ms / unit"})
                self.graphsContainer[unit][type]['plot'].showGrid(x=True, y=True, alpha=0.8)
                self.graphsContainer[unit][type]['plot'].addLegend()
                self.tabContainer[unit]['graphicsview'].addItem(self.graphsContainer[unit][type]['plot'], row=row, col=0, rowspan=1, colspan=1)
                row = row + 1
            else:
                self.graphsContainer[unit][type]['plot'] = None



    def updatePlots(self):
        #Run on timer when connected

        for unit in self.graphsContainer:
            for type in self.graphsContainer[unit]:
                color = 0
                for sensor in self.graphsContainer[unit][type]['sensors']:

                    QtWidgets.QApplication.processEvents()
                    if self.graphsContainer[unit][type]['sensors'][sensor]['display'] == True:
                        pos = self.graphsContainer[unit][type]['sensors'][sensor]['pos']
                        if self.graphsContainer[unit][type]['sensors'][sensor]['plot'] == None:
                            self.graphsContainer[unit][type]['sensors'][sensor]['plot'] = self.graphsContainer[unit][type]['plot'].plot(name=str(sensor), pen=intColor(color, maxValue=255, minValue=128))
                        self.graphsContainer[unit][type]['sensors'][sensor]['plot'].setData(self.graphsContainer[unit][type]['sensors'][sensor]['time'][:pos], self.graphsContainer[unit][type]['sensors'][sensor]['data'][:pos])
                        color = color + 1
                    else:
                        continue


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
            for i in range(len(container[e][0])):
                container[e][0][i] = container[e][0][i]
                container[e][1][i] = container[e][1][i]

        name = self.ui.veiculoLineEdit.text() + "_" + self.ui.velocidadeLineEdit.text() + "_" + self.ui.superficieLineEdit.text() + "_" + self.ui.notaLineEdit.text() + ".txt"
        with open(name, 'w') as file:
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
