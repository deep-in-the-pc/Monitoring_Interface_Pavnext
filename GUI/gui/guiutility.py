# -*- coding: latin-1 -*-


#for plots
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtGui, QtCore

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
        elif self.data[0][3] == 'corr':
            ax.set_ylabel("Current")
        elif self.data[0][3] == 'tens':
            ax.set_ylabel("Voltage")
        elif self.data[0][3] == 'default':
            ax.set_ylabel("Default")

        ax.set_xlabel("Tempo : ms")


        #TODO Add ylabel depending on sensor type


        ax.set_title(self.name)
        ax.legend()
        self.draw()

class graphQFrame(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid = QtWidgets.QGridLayout()
        self.hasDisplay = False
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

        nameP, entries = self.getData(entries)
        #Check if all have the same size
        if entries == 0:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Entradas com dimensões diferentes", QtWidgets.QMessageBox.Ok)
            return
        elif entries == 1:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Entradas não configuradas", QtWidgets.QMessageBox.Ok)
            return
        elif entries == 2:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Entradas de tipos diferentes", QtWidgets.QMessageBox.Ok)
            return
        else:
            self.addGraph(nameP, entries)

    def getData(self, entries):
        nEntries = []
        nameP = ""
        preSize = int(entries[0].split()[2])
        if entries[0].split()[0][0:2] in self.slaveDecode:
            if entries[0].split()[0][2:4] in self.prototypesDecode[self.slaveDecode[entries[0].split()[0][0:2]]]:
                preType = self.prototypesDecode[self.slaveDecode[entries[0].split()[0][0:2]]][entries[0].split()[0][2:4]]['type']
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





