# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'monitoring_interface_04.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 720)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.slaveTabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.slaveTabWidget.setObjectName("slaveTabWidget")
        self.Info = QtWidgets.QWidget()
        self.Info.setObjectName("Info")
        self.layoutWidget = QtWidgets.QWidget(self.Info)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 410, 198, 139))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtWidgets.QLabel(self.layoutWidget)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.veiculoLineEdit = QtWidgets.QLineEdit(self.layoutWidget)
        self.veiculoLineEdit.setObjectName("veiculoLineEdit")
        self.horizontalLayout_3.addWidget(self.veiculoLineEdit)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_3 = QtWidgets.QLabel(self.layoutWidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_4.addWidget(self.label_3)
        self.velocidadeLineEdit = QtWidgets.QLineEdit(self.layoutWidget)
        self.velocidadeLineEdit.setObjectName("velocidadeLineEdit")
        self.horizontalLayout_4.addWidget(self.velocidadeLineEdit)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_4 = QtWidgets.QLabel(self.layoutWidget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_5.addWidget(self.label_4)
        self.superficieLineEdit = QtWidgets.QLineEdit(self.layoutWidget)
        self.superficieLineEdit.setObjectName("superficieLineEdit")
        self.horizontalLayout_5.addWidget(self.superficieLineEdit)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_5 = QtWidgets.QLabel(self.layoutWidget)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_6.addWidget(self.label_5)
        self.notaLineEdit = QtWidgets.QLineEdit(self.layoutWidget)
        self.notaLineEdit.setObjectName("notaLineEdit")
        self.horizontalLayout_6.addWidget(self.notaLineEdit)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.savePushButton = QtWidgets.QPushButton(self.layoutWidget)
        self.savePushButton.setObjectName("savePushButton")
        self.horizontalLayout_7.addWidget(self.savePushButton)
        self.openPushButton = QtWidgets.QPushButton(self.layoutWidget)
        self.openPushButton.setObjectName("openPushButton")
        self.horizontalLayout_7.addWidget(self.openPushButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout_7)
        self.slaveTabWidget.addTab(self.Info, "")
        self.verticalLayout_2.addWidget(self.slaveTabWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.connectionStatusLabel = QtWidgets.QLabel(self.centralwidget)
        self.connectionStatusLabel.setObjectName("connectionStatusLabel")
        self.verticalLayout.addWidget(self.connectionStatusLabel)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.targetComCB = QtWidgets.QComboBox(self.centralwidget)
        self.targetComCB.setObjectName("targetComCB")
        self.horizontalLayout.addWidget(self.targetComCB)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.targetComConnectButton = QtWidgets.QPushButton(self.centralwidget)
        self.targetComConnectButton.setObjectName("targetComConnectButton")
        self.verticalLayout.addWidget(self.targetComConnectButton)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.slaveTabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Monitoring Interface V0.4 - Pavnext"))
        self.label.setText(_translate("MainWindow", "Veículo:"))
        self.label_3.setText(_translate("MainWindow", "Velocidade:"))
        self.label_4.setText(_translate("MainWindow", "Superfície:"))
        self.label_5.setText(_translate("MainWindow", "Nota:"))
        self.savePushButton.setText(_translate("MainWindow", "Save"))
        self.openPushButton.setText(_translate("MainWindow", "Open"))
        self.slaveTabWidget.setTabText(self.slaveTabWidget.indexOf(self.Info), _translate("MainWindow", "Info"))
        self.connectionStatusLabel.setText(_translate("MainWindow", "Connection Status: Offline"))
        self.label_2.setText(_translate("MainWindow", "Target COM:"))
        self.targetComConnectButton.setText(_translate("MainWindow", "Connect"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
