# -*- coding: latin-1 -*-


#for plots
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtGui, QtCore
from gui.plotEditDialog import *

class PlotCanvas(FigureCanvas):

    def __init__(self, name, data, parent=None,width=5, height=4, dpi=120):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.name = name
        self.data = data
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):

        ax = self.figure.add_subplot(111)

        for nplot in self.data:
            ax.plot(nplot[2], nplot[1], label=nplot[0])

        if self.data[0][3] == 'vlin':
            ax.set_ylabel("Vertical linear sensor")
        elif self.data[0][3] == 'acelx' or self.data[0][3] == 'acely' or self.data[0][3] == 'acelz':
            ax.set_ylabel("Acelerometer")
        elif self.data[0][3] == 'curr':
            ax.set_ylabel("Current")
        elif self.data[0][3] == 'volt':
            ax.set_ylabel("Voltage")
        elif self.data[0][3] == 'default':
            ax.set_ylabel("Default")

        ax.set_xlabel("Tempo : ms")

        ax.set_title(self.name)
        ax.legend()
        self.draw()

class graphQFrame(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid = QtWidgets.QGridLayout()
        self.hasDisplay = False
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

        self.currentPlots = None

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            self.EntriesFiltered = self.parent().parent().EntriesFiltered
            self.ignoreSConfigs = self.parent().parent().ignoreSConfigs
            if(not self.ignoreSConfigs):
                self.slaveDecode = self.parent().parent().scfgs['slaves']
                self.prototypesDecode = self.parent().parent().scfgs['prototypes']
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):

        data = e.mimeData()
        #print(data.text())
        source_item = QtGui.QStandardItemModel()
        source_item.dropMimeData(data, QtCore.Qt.CopyAction, 0, 0, QtCore.QModelIndex())
        entries = []
        #check for data up to 999 entries
        try:
            for i in range(999):
                entries.append(source_item.item(i, 0).text())
        except Exception as err:
            None

        nameP, self.currentPlots = self.getData(entries)
        #Check if all have the same size
        if self.currentPlots == 0:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Entradas com dimensões diferentes", QtWidgets.QMessageBox.Ok)
            return
        elif self.currentPlots == 1:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Entradas não configuradas", QtWidgets.QMessageBox.Ok)
            return
        elif self.currentPlots == 2:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Entradas de tipos diferentes", QtWidgets.QMessageBox.Ok)
            return
        else:
            self.addGraph(nameP, self.currentPlots)

    def getData(self, entries):
        nEntries = []
        nameP = ""
        preSize = int(entries[0].split()[2])
        if entries[0].split()[0][0:2] in self.slaveDecode:
            if entries[0].split()[0][2:4] in self.prototypesDecode[self.slaveDecode[entries[0].split()[0][0:2]]]:
                preType = self.prototypesDecode[self.slaveDecode[entries[0].split()[0][0:2]]][entries[0].split()[0][2:4]]['type']
            else:
                preType = self.prototypesDecode[self.slaveDecode['Default']][entries[0].split()[0][2:4]]['type']
        else:
            preType = self.prototypesDecode[self.slaveDecode['Default']][entries[0].split()[0][2:4]]['type']


        for entry in entries:
            entry=entry.split()
            slave = entry[0][0:2]
            sensor = entry[0][2:4]
            id = int(entry[1])
            size = int(entry[2])

            if preSize != size: #Check if all entries to be displayed have the same size
                return 0, 0

            preSize = size

            if (not self.ignoreSConfigs):

                if slave in self.slaveDecode:
                    if sensor in self.prototypesDecode[self.slaveDecode[slave]]:
                        name = self.prototypesDecode[self.slaveDecode[slave]][sensor]['name']
                        type = self.prototypesDecode[self.slaveDecode[slave]][sensor]['type']
                    else:
                        continue
                else:
                    name = self.prototypesDecode[self.slaveDecode['Default']][sensor]['name']
                    type = self.prototypesDecode[self.slaveDecode['Default']][sensor]['type']

                if type[0:3] != preType[0:3]:
                    return 2,2
                preType = type
            else:
                name = entry[0]+" id: "+entry[1]
                type = 'default'
            nameP = nameP+" "+name
            for tEntry in self.EntriesFiltered[slave][sensor]:
                if tEntry['id'] == id:
                    nEntries.append((name, tEntry['data'], tEntry['time'], type))
                    break

        if(len(nEntries) == 0):
            return 1, 1
        #print(nEntries)
        return nameP, nEntries

    def addGraph(self, name, entries):

        try:
            if self.hasDisplay:
                self.clearGraph()
            self.graph = PlotCanvas(name, entries)
            self.grid.addWidget(self.graph, 0, 0)

            self.setLayout(self.grid)
            if not self.hasDisplay:
                self.hasDisplay = True

        except Exception as err:
            print(str(err))

    def clearGraph(self):
        if self.hasDisplay:
            self.grid.removeWidget(self.graph)

            self.graph.axes.clear()
            self.graph.draw()
            self.hasDisplay = False
    def openMenu(self, position):

        menu = QtWidgets.QMenu()
        if self.hasDisplay:

            editAction = QtWidgets.QAction("Edit Plots", self)
            editAction.triggered.connect(self.openPlotEdit)
            clearAction = QtWidgets.QAction("Clear Graph", self)
            clearAction.triggered.connect(self.clearGraph)
            menu.addAction(editAction)
            menu.addAction(clearAction)

        menu.exec_(self.mapToGlobal(position))


    def openPlotEdit(self):
        ped = PlotEditDialog(self.currentPlots)
        if ped.exec_():
            values = ped.getValues()
            print(values)

class PlotEditDialog(QtWidgets.QDialog, Ui_plotEditDialog):
    def __init__(self, plots,parent=None):
        QtWidgets.QDialog.__init__(self,parent)
        self.setupUi(self)

        #Fill list with current plots
        self.plots = plots
        for plot in self.plots:
            plotWidgetItem = QtWidgets.QListWidgetItem()

            plotWidgetItem.setText(plot[0])
            plotWidgetItem.setData(32, plot[1:])

            self.listWidget.addItem(plotWidgetItem)

        #Add action to selecting a plot
        self.listWidget.itemPressed.connect(self.generateInputs)
        self.lineSelected = False

        #Generate inputs for selected type
    def generateInputs(self, item):
        if self.lineSelected:
            self.lineSelected = False
            QtWidgets.QWidget().setLayout(self.frame.layout())
            #Clear grid when switching or deselecting line

        grid = QtWidgets.QGridLayout()

        itemData = item.data(32)[0]
        itemDataTime = item.data(32)[1]
        itemType = item.data(32)[2]

        gridCBoxes = []
        gridLabels = []

        deleteB = QtWidgets.QPushButton("Delete Plot")
        #TODO deleteB exit with blank array

        if(itemType == 'vlin'):
            aceCBox = QtWidgets.QCheckBox("Acceleration")
            gridCBoxes.append(aceCBox)

            velCBox = QtWidgets.QCheckBox("Velocity")
            gridCBoxes.append(velCBox)

            keepCBox = QtWidgets.QCheckBox("Position")
            keepCBox.setChecked(True)
            gridCBoxes.append(keepCBox)

            aceLabel = QtWidgets.QLabel("Add Acceleration Plot")
            gridLabels.append(aceLabel)

            velLabel = QtWidgets.QLabel("Add Velocity Plot")
            gridLabels.append(velLabel)

            keepLabel = QtWidgets.QLabel("Keep Original Plot")
            gridLabels.append(keepLabel)

        elif(itemType == 'acelx' or itemType == 'acely' or itemType == 'acelz'):

            velCBox = QtWidgets.QCheckBox("Velocity")
            gridCBoxes.append(velCBox)

            posCBox = QtWidgets.QCheckBox("Position")
            gridCBoxes.append(posCBox)

            keepCBox = QtWidgets.QCheckBox("Acceleration")
            keepCBox.setChecked(True)
            gridCBoxes.append(keepCBox)

            velLabel = QtWidgets.QLabel("Add Velocity Plot")
            gridLabels.append(velLabel)

            posLabel = QtWidgets.QLabel("Add Position Plot")
            gridLabels.append(posLabel)

            keepLabel = QtWidgets.QLabel("Keep Original Plot")
            gridLabels.append(keepLabel)

        elif(itemType == 'curr'):

            torCBox = QtWidgets.QCheckBox("Torque")
            gridCBoxes.append(torCBox)

            keepCBox = QtWidgets.QCheckBox("Current")
            keepCBox.setChecked(True)
            gridCBoxes.append(keepCBox)

            torLabel = QtWidgets.QLabel("Add Torque Plot")
            gridLabels.append(torLabel)

            keepLabel = QtWidgets.QLabel("Keep Original Plot")
            gridLabels.append(keepLabel)

        elif(itemType == 'volt'):

            rpmCBox = QtWidgets.QCheckBox("RPM")
            #gridCBoxes.append(rpmCBox)

            keepCBox = QtWidgets.QCheckBox("Voltage")
            keepCBox.setChecked(True)
            #gridCBoxes.append(keepCBox)

            rpmLabel = QtWidgets.QLabel("Add RPM Plot")
            gridLabels.append(rpmLabel)

            keepLabel = QtWidgets.QLabel("Keep Original Plot")
            gridLabels.append(keepLabel)

        else:

            aceCBox = QtWidgets.QCheckBox("Acceleration")
            gridCBoxes.append(aceCBox)

            velCBox = QtWidgets.QCheckBox("Velocity")
            gridCBoxes.append(velCBox)

            posCBox = QtWidgets.QCheckBox("Position")
            gridCBoxes.append(posCBox)

            rpmCBox = QtWidgets.QCheckBox("RPM")
            gridCBoxes.append(rpmCBox)

            torCBox = QtWidgets.QCheckBox("Torque")
            gridCBoxes.append(torCBox)

            forCBox = QtWidgets.QCheckBox("Force")
            gridCBoxes.append(forCBox)

            volCBox = QtWidgets.QCheckBox("Voltage")
            gridCBoxes.append(volCBox)

            curCBox = QtWidgets.QCheckBox("Current")
            gridCBoxes.append(curCBox)

            keepCBox = QtWidgets.QCheckBox("")
            keepCBox.setChecked(True)
            gridCBoxes.append(keepCBox)

            aceLabel = QtWidgets.QLabel("Add Acceleration Plot")
            gridLabels.append(aceLabel)

            velLabel = QtWidgets.QLabel("Add Velocity Plot")
            gridLabels.append(velLabel)

            posLabel = QtWidgets.QLabel("Add Position Plot")
            gridLabels.append(posLabel)

            rpmLabel = QtWidgets.QLabel("Add RPM Plot")
            gridLabels.append(rpmLabel)

            torLabel = QtWidgets.QLabel("Add Torque Plot")
            gridLabels.append(torLabel)

            forLabel = QtWidgets.QLabel("Add Force Plot")
            gridLabels.append(forLabel)

            volLabel = QtWidgets.QLabel("Add Voltage Plot")
            gridLabels.append(volLabel)

            curLabel = QtWidgets.QLabel("Add Current Plot")
            gridLabels.append(curLabel)

            keepLabel = QtWidgets.QLabel("Keep Original Plot")
            gridLabels.append(keepLabel)

        for counter in range(len(gridCBoxes)):
            grid.addWidget(gridCBoxes[counter], counter, 0)
            grid.addWidget(gridLabels[counter], counter, 1)

        grid.addWidget(deleteB, counter+1, 1)

        self.frame.setLayout(grid)

        if not self.lineSelected:
            self.lineSelected = True

    def getValues(self):
        #TODO exit with new array

        return "test"




