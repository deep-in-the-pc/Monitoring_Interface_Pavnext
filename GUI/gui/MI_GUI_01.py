# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'monitoring_interface_01.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.setEnabled(True)
        MainWindow.resize(1280, 720)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setAnimated(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.connectionFrame = QtWidgets.QFrame(self.centralwidget)
        self.connectionFrame.setGeometry(QtCore.QRect(20, 20, 191, 91))
        self.connectionFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.connectionFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.connectionFrame.setObjectName("connectionFrame")
        self.formLayout_2 = QtWidgets.QFormLayout(self.connectionFrame)
        self.formLayout_2.setObjectName("formLayout_2")
        self.targetComLabel = QtWidgets.QLabel(self.connectionFrame)
        self.targetComLabel.setObjectName("targetComLabel")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.targetComLabel)
        self.targetComConnectButton = QtWidgets.QPushButton(self.connectionFrame)
        self.targetComConnectButton.setObjectName("targetComConnectButton")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.targetComConnectButton)
        self.targetComCB = QtWidgets.QComboBox(self.connectionFrame)
        self.targetComCB.setObjectName("targetComCB")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.targetComCB)
        self.connectionStatusLabel = QtWidgets.QLabel(self.connectionFrame)
        self.connectionStatusLabel.setObjectName("connectionStatusLabel")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.connectionStatusLabel)
        self.toolsFrame = QtWidgets.QFrame(self.centralwidget)
        self.toolsFrame.setGeometry(QtCore.QRect(20, 130, 191, 541))
        self.toolsFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.toolsFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.toolsFrame.setObjectName("toolsFrame")
        self.graphFrame = QtWidgets.QFrame(self.centralwidget)
        self.graphFrame.setGeometry(QtCore.QRect(230, 20, 1021, 651))
        self.graphFrame.setObjectName("graphFrame")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Monitoring Interface V0.1 - Pavnext"))
        self.targetComLabel.setText(_translate("MainWindow", "Target COM:"))
        self.targetComConnectButton.setText(_translate("MainWindow", "Connect"))
        self.connectionStatusLabel.setText(_translate("MainWindow", "Connection Status: Offline"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

