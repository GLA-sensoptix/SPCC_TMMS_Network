# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 16:09:38 2021

@author: GLA
"""


from PyQt5.QtCore import *
# from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ModbusWindow import Ui_ModbusWindow
from TMMSNetwork_modbus import TMMSClientSerial, TMMSClientEthernet
from handler import ETL

from lxml import etree, objectify
from io import BytesIO
import xml.etree.ElementTree as ET

import os
import sys
import threading
import numpy as np
import pandas as pd
import time


class Struct:
    pass

class FileManager:
    def __init__(self):
        self.nof_sensors = 84
        self.run_path = os.getcwd()
        self.folder = os.path.realpath(os.path.join(self.run_path, './data'))
        self.filename = os.path.realpath(os.path.join(self.run_path, './data/DeltaLuxCryo_measurements.dat'))
        self.create_file()
        
    def create_file(self):
        Tanks = ['702-', '703-']
        Locations = [str(i+1) for i in range(7)]
        Axis = ['H', 'V', 'R']
        Red = ['p', 's']
        if os.path.exists(self.filename):
            os.remove(self.filename)
        with open(self.filename, 'w+') as f:
            f.write(
                '"TOA5","TBM2a-STA1","CR300","20544","CR300.Std.09.02","CPU:TBM2a-STA1_V05.CR300","29960","RawData"\n')
            f.write('"TIMESTAMP","RECORD"')
            for r in Red:
                for tank in Tanks:
                    for loc in Locations:
                        for ax in Axis:
                            f.write(',"0100-XE-' + tank + ax +
                                    loc + r + ' Movement"')
            for r in Red:
                for tank in Tanks:
                    for loc in Locations:
                        for ax in Axis:
                            f.write(',"0100-XE-' + tank +
                                    ax + loc + r + ' Status"')
            f.write('\n"TS","RN"')
            for k in range(self.nof_sensors):
                f.write(',"mm","-"')
            f.write('\n')
            f.write('"",""')
            for k in range(2, self.nof_sensors+2):
                f.write(',"Smp","Smp"')
      
    def update_file(self, data, rec_nb, circuit):
        with open(self.filename, 'a') as f:
            f.write('\n"' + time.strftime("%Y-%m-%d %H:%M:%S",
                    time.localtime()) + '"')
            f.write(',' + str(rec_nb))
            if circuit == 'p':
                self.write(data.loc[:, 'movement'], f)
                self.write(None, f)
                self.write(data.loc[:, 'status'], f)
                self.write(None, f)
            else:
                self.write(None, f)
                self.write(data.loc[:, 'movement'], f)
                self.write(None, f)
                self.write(data.loc[:, 'status'], f)
                
    def write(self, data, f):
        for k in range(self.nof_sensors//2):
            if type(data) == type(None):
                f.write(",")
            else:
                f.write("," + str(data[k]))
        # for k in range(self.nof_sensors/2):
        #     if data == None:
        #         status = data.iloc[k,2]
        #         f.write("," + str(int(status)))
        #     else:

class ModbusCommunication:
    def __init__(self, circuit):
        self.circuit = circuit
        self.nof_sensors = 84
        self._type_dict = {'int': int,
                           'str': str}
        adresses = self.load('parameters/matching_table_modbus_default.xml')
        self.sensor_adresses = pd.DataFrame([['', 0, 0, 0, '']] * self.nof_sensors,
                                    index=[str(i) for i in range(1,self.nof_sensors+1)],
                                    columns=['name', 'movement', 'status', 'bit', 'circuit'])
        self.sensor_data = pd.DataFrame([['', 0, 0, '']] * self.nof_sensors,
                                    index=[str(i) for i in range(1,self.nof_sensors+1)],
                                    columns=['name', 'movement', 'status', 'circuit'])
        self.adress_list = pd.DataFrame([[0, '', '', '']],
                                        columns=['adress', 'slave', 'datatype', 'circuit'])
        self.adress_data = pd.DataFrame([[0, '', '', '']],
                                        columns=['adress', 'value', 'databyte', 'circuit'])
        i = 0
        for attr, value in adresses.__dict__.items():
            if not 'b' in attr.split('_')[1]:
                adress = int(attr.split('_')[1])
                self.adress_list.loc[i] = [adress, value.slave, value.datatype, value.tag[-1]]
                self.adress_data.loc[i] = [adress, 0, value.datatype, value.tag[-1]]
                self.sensor_adresses.loc[i] = [value.tag, adress, 0, 0, value.tag[-1]]
                self.sensor_data.loc[i] = [value.tag, 0, 0, value.tag[-1]]
                i += 1
            else:
                adress = int(attr.split('_')[1].split('b')[0])
                bit = attr.split('_')[1].split('b')[1]
                if not self.adress_list.isin([adress]).any().any():
                    self.adress_list.loc[i] = [adress, value.slave, value.datatype, value.tag.split('_Status')[0][-1]]
                    self.adress_data.loc[i] = [adress, 0, value.datatype, value.tag.split('_Status')[0][-1]]
                    i += 1
                name = value.tag.split('_')[0]
                self.sensor_adresses.loc[self.sensor_adresses.loc[:, 'name'] == name, 'status'] = adress                  
                self.sensor_adresses.loc[self.sensor_adresses.loc[:, 'name'] == name, 'bit'] = bit
        self.socket = TMMSClientSerial('COM1')

    def run_requests(self):
        # adress = 40207
        # datatype = "byte"
        # value, status = self.socket.read(adress, datatype)
        # print(value)
        for i, row in enumerate(self.adress_list.iterrows()):
            if row[1].loc['circuit'] == self.circuit:
                adress = row[1].loc['adress']
                datatype = row[1].loc['datatype']
                if datatype == 'float32':
                    value, status = self.socket.read(adress, datatype)
                    name = self.sensor_adresses.loc[self.sensor_adresses.loc[:, 'movement'] == adress, 'name'].iloc[0]
                    if status:
                        val = value[adress]
                    else:
                        val = 0
                    self.sensor_data.loc[self.sensor_data.loc[:, 'name'] == name, 'movement'] = val
                    self.adress_data.loc[self.adress_data.loc[:, 'adress'] == adress, 'value'] = str(val)
                else:
                    value, status = self.socket.read(adress, datatype)
                    names = self.sensor_adresses.loc[self.sensor_adresses.loc[:, 'status'] == adress, 'name']
                    for name in names:
                        bit = int(self.sensor_adresses.loc[self.sensor_adresses.loc[:, 'name'] == name, 'bit'])
                        if status:
                            val = value[adress][bit]
                        else:
                            val = 0
                        self.sensor_data.loc[self.sensor_data.loc[:, 'name'] == name, 'status'] = val
                    self.adress_data.loc[self.adress_data.loc[:, 'adress'] == adress, 'value'] = str(value[adress])

    def load(self, xmlFile):
        with open(xmlFile) as fobj:
            xml = fobj.read()
        root = etree.fromstring(xml)
        addess_list = Struct()
        for elem in root.getchildren():
            [name, Elem] = self.get_child(elem)
            setattr(addess_list, name, Elem)
        return(addess_list)

    def get_child(self, elem, types=False, dictionary=False):
        if len(elem.getchildren()) == 0:
            return elem.tag, self._type_dict[elem.get('type')](elem.get('value'))
        else:
            Elem_struct = Struct()
            for el in elem.getchildren():
                [name, Elem] = self.get_child(el)
                setattr(Elem_struct, name, Elem)
            return elem.get('name'), Elem_struct

class MainWindow(QMainWindow, Ui_ModbusWindow):
    def __init__(self, circuit, thm=True, display=False, parent=None):
        super().__init__(parent)
        self.circuit = circuit
        self.display = display
        self.rec_nb = 0
        self.setupUi(self)
        self.modbus = ModbusCommunication(self.circuit)
        self.modbus.run_requests()
        self.file_manager = FileManager()
        data = self.modbus.sensor_data.loc[self.modbus.sensor_data['circuit'] == self.circuit]
        self.file_manager.update_file(data, self.rec_nb, self.circuit)
        self.refresh_thm = thm
        # Init tables
        header_1 = ['Sensor', 'Movement', 'Status']
        data_1 = self.modbus.sensor_data.loc[self.modbus.sensor_data['circuit'] == self.circuit].iloc[:,0:3]
        header_2 = ['Adress', 'Value', 'Datatype']
        data_2 = self.modbus.adress_data.loc[self.modbus.adress_data['circuit'] == self.circuit].iloc[:,0:3]
        self.tableView_1.model = TableModel(np.array(data_1), header_1)
        self.tableView_2.model = TableModel(np.array(data_2), header_2)
        # self.tableView.reset() # commented 05/11: usefull ?
        self.tableView_1.setModel(self.tableView_1.model)
        self.tableView_2.setModel(self.tableView_2.model)
        t = time.strftime('[%y-%m-%d %H-%M-%S]')
        print(t + ' TMMS Network Started')
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(5000)
        
    def on_timer(self):
        self.rec_nb += 1
        # threading.Thread(target=self.modbus.run_requests).start()
        self.modbus.run_requests()
        data = self.modbus.sensor_data.loc[self.modbus.sensor_data['circuit'] == self.circuit]
        self.file_manager.update_file(data, self.rec_nb, self.circuit)
        if self.refresh_thm:
            # threading.Thread(target=ETL, args=(self.file_manager.folder, )).start()
            ETL(self.file_manager.folder)
        if self.display:
            self.refresh()
        t = time.strftime('[%y-%m-%d %H-%M-%S]')
        print(t + ' Data updated')

    def refresh(self):
        # Refresh Tables
        data_1 = self.modbus.sensor_data.loc[self.modbus.sensor_data['circuit'] == self.circuit].iloc[:,0:3]
        data_2 = self.modbus.adress_data.loc[self.modbus.adress_data['circuit'] == self.circuit].iloc[:,0:3]
        self.tableView_1.model.update(np.array(data_1))
        self.tableView_1.reset()
        self.tableView_2.model.update(np.array(data_2))
        self.tableView_2.reset()

class TableModel(QAbstractTableModel):
    def __init__(self, arraydata, header):
        super(TableModel, self).__init__()
        self.arraydata = arraydata
        self.header = header

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            if len(self.arraydata[index.row()]) > index.column():
                return self.arraydata[index.row()][index.column()]
            else:
                return

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def update(self, new_data):
        self.arraydata = new_data
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(
            self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

    def rowCount(self, index):
        # The length of the outer list.
        return len(self.arraydata)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        if len(self.arraydata) != 0:
            return len(self.arraydata[0])
        else:
            return(0)


if __name__ == "__main__":
    display = False
    thm = False
    circuit = 'p'
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == 'display':
                display = True
            if arg == 'thm':
                thm = True
            if arg == "secondary":
                circuit = 's'
    display = True
    thm = True
    app = QApplication([])
    win = MainWindow(circuit, thm=thm, display=display)
    if display:
        win.show()
    app.exec_()
