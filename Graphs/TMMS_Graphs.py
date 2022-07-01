# -*- coding: utf-8 -*-
"""
Created on Sat Jun 18 05:39:50 2022

@author: laugi
"""

print('******************************\n Loading Data, please wait...')

import sys
import os
import time
import win32gui, win32con

# hide = win32gui.GetForegroundWindow()
# win32gui.ShowWindow(hide, win32con.SW_HIDE)

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QCheckBox, QPushButton
)
from PyQt5.QtCore import (QAbstractTableModel, Qt, QModelIndex, QTimer)

from PyQt5.uic import loadUi
from TMMS_GraphsDesign import Ui_GraphsWindow

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import matplotlib.pyplot as plt
import matplotlib.dates as dates
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


import pandas as pd
pd.options.mode.chained_assignment = None

import numpy as np
from functools import partial

# import warnings
# with warnings.catch_warnings():
#     warnings.simplefilter(action='ignore', category=FutureWarning)

class GUIWindow(QMainWindow, Ui_GraphsWindow):
    def __init__(self, app, hide_cmd=True, parent=None):
        super().__init__(parent)
        self.app = app
        self.setupUi(self)
        # Axis set up
        self.A = GUIAxis(self.A_axes_layout, 'A')
        self.B = GUIAxis(self.B_axes_layout, 'B')
        # Push buttons set up
        # self.A_PB_1.clicked.connect(self.A_PB_1_callback)
        # self.A_PB_2.clicked.connect(self.A_PB_2_callback)
        # self.A_PB_3.clicked.connect(self.A_PB_3_callback)
        # self.B_PB_1.clicked.connect(self.B_PB_1_callback)
        # self.B_PB_2.clicked.connect(self.B_PB_2_callback)
        # self.B_PB_3.clicked.connect(self.B_PB_3_callback)
        self.A_PB_1.clicked.connect(partial(self.PB_1_callback, 'A'))
        self.A_PB_2.clicked.connect(partial(self.PB_2_callback, 'A'))
        self.A_PB_3.clicked.connect(partial(self.PB_3_callback, 'A'))
        self.B_PB_1.clicked.connect(partial(self.PB_1_callback, 'B'))
        self.B_PB_2.clicked.connect(partial(self.PB_2_callback, 'B'))
        self.B_PB_3.clicked.connect(partial(self.PB_3_callback, 'B'))
        # Properties
        self.sensors_prefix = '0100-XE-'
        self.tank_dict = {'T-001': '702-', 'T-002': '703-'}
        self.sensor_dict = {'Horizontal': 'H', 'Vertical': 'V', 'Rotational': 'R'}
        self.circuit_dict = {'Primary': 'p', 'Secondary': 's'}
        # Load data
        self.filepath = os.path.realpath(os.path.join(os.getcwd(), '../data/DeltaLuxCryo_measurements_history.dat'))
        self.downsampling_step_old = 100 # in seconds.
        self.downsampling_step_recent = 5
        # Refresh
        self.load()
        # Hide cmd windows
        if hide_cmd:
            hide = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hide, win32con.SW_HIDE)
        # # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.load)
        self.timer.start(1 * 10 * 1000) # ms
        
    def load(self):
        # Load data
        data = pd.read_csv(self.filepath, skiprows=[0,2,3], usecols=range(86))
        old_points = data.iloc[:-self.downsampling_step_old:self.downsampling_step_old,:]
        recent_points = data.iloc[-self.downsampling_step_old::self.downsampling_step_recent,:]
        # self.data = self.data.iloc[0:self.downsampling_step:-downsampling_step,:]
        self.data = old_points.append(recent_points)
        self.data.replace(0.0, None, inplace=True)
        # Refresh Plots
        self.refresh('A')
        self.refresh('B')
    
    def refresh(self, graph):
        A_sensors, B_sensors = self.sensor_list()
        if graph == 'A':
            self.A.refresh(A_sensors, self.data, self.A_txt)
        elif graph == 'B':
            self.B.refresh(B_sensors, self.data, self.B_txt)           
        
    def closeEvent(self, event):
        # self.app.timer.stop()
        self.app.exit()
        
    def PB_1_callback(self, graph):
        PB_clicked = self.sender()
        if PB_clicked.text() == "T-001":
            PB_clicked.setText("T-002")
        else:
            PB_clicked.setText("T-001")
        self.refresh(graph)
            
    def PB_2_callback(self, graph):
        PB_clicked = self.sender()
        if PB_clicked.text() == "Horizontal":
            PB_clicked.setText("Vertical")
        elif PB_clicked.text() == "Vertical":
            PB_clicked.setText("Rotational")
        else:
            PB_clicked.setText("Horizontal")
        self.refresh(graph)
            
    def PB_3_callback(self, graph):
        PB_clicked = self.sender()
        if PB_clicked.text() == "Primary":
            PB_clicked.setText("Secondary")
        else:
            PB_clicked.setText("Primary")
        self.refresh(graph)
        
    def sensor_list(self):
        # A list
        A_sensors = []
        for i in range(7):
            A_sensors.append(self.sensors_prefix + 
                             self.tank_dict[self.A_PB_1.text()] + 
                             self.sensor_dict[self.A_PB_2.text()] + str(i+1) + 
                             self.circuit_dict[self.A_PB_3.text()])
        # B list
        B_sensors = []
        for i in range(7):
            B_sensors.append(self.sensors_prefix + 
                             self.tank_dict[self.B_PB_1.text()] + 
                             self.sensor_dict[self.B_PB_2.text()] + str(i+1) + 
                             self.circuit_dict[self.B_PB_3.text()])
        return(A_sensors, B_sensors)

class GUIAxis(QDialog):
    def __init__(self, layout, id, parent=None):
        super(GUIAxis, self).__init__(parent)
        self.canvas = FigureCanvas(Figure())
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.canvas.figure.subplots()
        self.id = id
        layout.addWidget(self.navi_toolbar)
        layout.addWidget(self.canvas)
        
    def refresh(self, sensors, data, cursor):
        
        def mouse_move(event):
            x, y = event.xdata, event.ydata
            try:
                d = str(dates.num2date(x))[:16]
                m = round(y * 1e3) / 1e3
                cursor.setText('Date: {}\nMovement: {} mm'.format(d, m))
            except:
                cursor.setText('Date: \nMovement: ')
            
        self.ax.clear()
        # date_list = [time.strptime(d, '%Y-%m-%d %H:%M:%S') for d in data['TIMESTAMP']]
        date_list = pd.to_datetime(data['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S')
        lastest_date = dates.date2num(date_list.iloc[-1])
        one_week_date = lastest_date - 7
        for sensor in sensors:
            name = sensor + ' Movement'
            if len(data[name].dropna()) < 2:
                data[name].iloc[1] = 0.0
                data[name].iloc[-1] = 0.0
            self.ax.plot(date_list, data[name], label=sensor.split('0100-XE-')[1])
        # self.ax.xaxis.set_major_locator(dates.DayLocator(interval=1))    # every day
        self.ax.xaxis.set_major_formatter(dates.DateFormatter('\n%Y-%m-%d'))
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Movement (mm)")
        # self.ax.grid(which='minor', linestyle='--')
        self.ax.grid(which='major', linestyle='-')
        self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        self.ax.set_title("Time series ({})".format(self.id))
        self.ax.set_xlim([one_week_date, lastest_date + 0.1])
        self.canvas.mpl_connect('motion_notify_event', mouse_move)
        self.canvas.draw()
        
def check_existing_window():
    process = "TMMS Time Serie Graphs"
    PID_self = os.getpid()
    PID_others = []
    kill = False
    # os.system('tasklist /v /fi "imagename eq cmd.exe" /fi "sessionname eq console" /fo "csv" > tasklist.txt')
    os.system('tasklist /v /fi "imagename eq python.exe" /fo "csv" > tasklist.txt')
    with open('tasklist.txt', 'r') as task_file:
        for line in task_file.readlines():
            if process in line.split(',')[-1]:
                PID = line.split(',')[1]
                if PID != PID_self:
                    PID_others.append(PID)
                    kill = True
    if kill:
        for PID in PID_others:
            os.system('taskkill /PID ' + PID)

if __name__ == "__main__":
    # Search existing TMMS Graph instance and close it
    # check_existing_window()
    # Run app
    hide_cmd = False
    app = QApplication(sys.argv)
    window = GUIWindow(app, hide_cmd)
    # app.raiseW()
    app.setActiveWindow(window)
    window.show()
    app.exec()