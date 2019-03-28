#for plots
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtGui, QtCore

class PlotCanvas(FigureCanvas):

    def __init__(self, name, data, parent=None,width=5, height=4, dpi=100):
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

        ax.legend()
        ax.set_title(self.name)
        self.draw()

class graphQFrame(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid = QtWidgets.QGridLayout()
        self.hasDisplay = False
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            self.EntriesFiltered = self.parent().parent().EntriesFiltered
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):

        data = e.mimeData()
        #print(data.text())
        source_item = QtGui.QStandardItemModel()
        source_item.dropMimeData(data, QtCore.Qt.CopyAction, 0, 0, QtCore.QModelIndex())
        entries = []
        try:
            for i in range(999):
                entries.append(source_item.item(i, 0).text())
        except Exception as err:
            None

        nameP, entries = self.getData(entries)
        self.addGraph(nameP, entries)

    def getData(self, entries):
        nEntries = []
        nameP = ""
        for entry in entries:
            entry=entry.split()
            slave = entry[0][0:2]
            sensor = entry[0][2:4]
            id = int(entry[1])
            size = int(entry[2])
            name = entry[0]+" id: "+entry[1]
            nameP = nameP+" "+name
            for tEntry in self.EntriesFiltered[slave][sensor]:
                if tEntry['id'] == id:
                    nEntries.append((name, tEntry['data'], tEntry['time']))
                    break
        #print(nEntries)
        return nameP, nEntries
    def addGraph(self, name, entries):

        try:
            if self.hasDisplay:
                self.grid.removeWidget(self.graph)

            print(name)
            self.graph = PlotCanvas(name, entries)

            self.grid.addWidget(self.graph, 0, 0)

            self.setLayout(self.grid)
            if not self.hasDisplay:
                self.hasDisplay = True

        except Exception as err:
            print(str(err))