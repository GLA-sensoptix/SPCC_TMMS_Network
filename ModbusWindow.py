# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ModbusWindow.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ModbusWindow(object):
    def setupUi(self, ModbusWindow):
        ModbusWindow.setObjectName("ModbusWindow")
        ModbusWindow.resize(522, 721)
        self.centralwidget = QtWidgets.QWidget(ModbusWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(10, 10, 501, 661))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tableView_1 = QtWidgets.QTableView(self.tab)
        self.tableView_1.setGeometry(QtCore.QRect(0, 0, 491, 631))
        self.tableView_1.setObjectName("tableView_1")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tableView_2 = QtWidgets.QTableView(self.tab_2)
        self.tableView_2.setGeometry(QtCore.QRect(0, 0, 491, 631))
        self.tableView_2.setObjectName("tableView_2")
        self.tabWidget.addTab(self.tab_2, "")
        ModbusWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(ModbusWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 522, 22))
        self.menubar.setObjectName("menubar")
        ModbusWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(ModbusWindow)
        self.statusbar.setObjectName("statusbar")
        ModbusWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ModbusWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(ModbusWindow)

    def retranslateUi(self, ModbusWindow):
        _translate = QtCore.QCoreApplication.translate
        ModbusWindow.setWindowTitle(_translate("ModbusWindow", "Modbus Registry Display"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("ModbusWindow", "TMMS Cabinet"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("ModbusWindow", "TMMS Network Cabinet"))
