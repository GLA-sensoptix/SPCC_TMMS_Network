# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 16:09:38 2021

@author: GLA
"""

from PyQt5.QtCore import *
# from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ModbusWindow import Ui_ModbusWindow
from TMMSNetwork_modbus import TMMSClientSerial, TMMSClientEthernet, TMMSServerEthernet
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

import logging
# FORMAT = '%(asctime)s %(message)s'
# DATE = '%d-%b-%Y %I:%M:%S'
# logging.basicConfig(filename="modbus.log",level=logging.DEBUG,format=FORMAT,datefmt=DATE)
# logging.basicConfig(level=logging.DEBUG,format=FORMAT,datefmt=DATE)
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

class Struct:
    pass

class FileManager:
    def __init__(self):
        self.max_capacity = 2**16
        self.history_length = 4 * 24 * 7 * 3600 # seconds
        self.dt_rec_history = self.max_capacity / self.history_length
        # self.max_capacity = 1000
        self.nof_sensors = 84
        self.run_path = os.getcwd()
        self.folder = os.path.realpath(os.path.join(self.run_path, './data'))
        self.filename_live = os.path.realpath(os.path.join(self.run_path, './data/DeltaLuxCryo_measurements_live.dat'))
        self.filename_history = os.path.realpath(os.path.join(self.run_path, './data/DeltaLuxCryo_measurements_history.dat'))
        if not os.path.exists(self.filename_history):
            self.file_creation(self.filename_history)
      
    def read(self, filename):
        if not os.path.exists(filename):
            return([])
        data = pd.read_csv(filename, delimiter=',', header=1, skiprows=[2,3])
        return(data)
    
    def file_creation(self, filename):
        try:
            if os.path.exists(filename):
                os.remove(filename)
            with open(filename, 'w+') as f:
                f.write(self.header())
        except:
            pass
        
    def header(self):
        Tanks = ['702-', '703-']
        Locations = [str(i+1) for i in range(7)]
        Axis = ['H', 'V', 'R']
        Red = ['p', 's']
        head = '"TOA5","TBM2a-STA1","CR300","20544","CR300.Std.09.02","CPU:TBM2a-STA1_V05.CR300","29960","RawData"'
        head += '\n"TIMESTAMP","RECORD"'
        for r in Red:
            for tank in Tanks:
                for loc in Locations:
                    for ax in Axis:
                        head += ',"0100-XE-' + tank + ax + loc + r + ' Movement"'
        for r in Red:
            for tank in Tanks:
                for loc in Locations:
                    for ax in Axis:
                        head += ',"0100-XE-' + tank + ax + loc + r + ' Status"'
        head += '\n"TS","RN"'
        for k in range(self.nof_sensors):
            head += ',"mm","-"'
        head +='\n"",""'
        for k in range(2, self.nof_sensors+2):
            head += ',"Smp","Smp"'
        head += '\n'
        return(head)
      
    def append(self, filename, dat_str):
        with open(filename, 'a') as file:
            file.write(dat_str)
      
    def data_to_str(self, data, rec_nb, NaN_type='0.0'):
        
        def shunt(data, NaN_type):
            string = ""
            for k in range(self.nof_sensors):
                if type(data[k]) == type(None):
                    # string += ',"NaN"'
                    string += ',' + NaN_type
                else:
                    string += "," + str(data[k])
            return(string)
        
        line = '"' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '"'
        line += ',' + str(rec_nb)
        line += shunt(data.loc[:, 'movement'], NaN_type)
        line += shunt(data.loc[:, 'status'], NaN_type)
        line += "\n"
        return(line)

    def update_live(self, data, rec_nb):
        # Update live file (latest record only)
        self.file_creation(self.filename_live)
        dat_str_live = self.data_to_str(data, rec_nb, NaN_type='0.0')
        self.append(self.filename_live, dat_str_live)
        
    def update_history(self, data, rec_nb):
        # Updage history file, length depends of:
        #  - Capacity max
        #  - Number of seconds of history
        dat_str_history = self.data_to_str(data, rec_nb, NaN_type='"NaN"')
        # Set Faulty sensors values as NaN
        dat_str_history.replace('0.0', '"NaN"', inplace=True)
        self.append(self.filename_history, dat_str_history)
        # Check History file size
        data_history = self.read(self.filename_history)
        if len(data_history) > self.max_capacity:
            # Re-sample History data
            data_history = data_history.iloc[100:,:]
            for i in range(len(data_history)):
                try:
                    data_history.iloc[i,0] = '"' + data_history.iloc[i,0] + '"'
                except:
                    if i > 0:
                        data_history.iloc[i,0] = data_history.iloc[i-1,0]
                    else:
                        data_history.iloc[i,0] = ""
            # Deal with NaN values
            data_history.replace('0.0', '"NaN"', inplace=True)
            data_history.fillna('"NaN"', inplace=True)
            # Re-create file
            self.file_creation(self.filename_history)
            data_history.to_csv(self.filename_history, mode='a', sep=',', 
                                index=False, quotechar="'", header=False)
        t = time.strftime('[%y-%m-%d %H-%M-%S]')
        print(t + ' Data history updated')

class ModbusCommunication:
    def __init__(self, circuit, red, debug=False):
        self.circuit = circuit
        self.slave = {'p': 1, 's': 2}[self.circuit]
        self.nof_sensors = 84
        self._type_dict = {'int': int,
                           'str': str}
        adresses = self.load('parameters/matching_table_modbus_default.xml')
        self.sensor_adresses = pd.DataFrame([['', 0, 0, 0, '']] * self.nof_sensors,
                                    columns=['name', 'movement', 'status', 'bit', 'circuit'])
        self.sensor_data = pd.DataFrame([['', 0, 0, '']] * self.nof_sensors,
                                    columns=['name', 'movement', 'status', 'circuit'])
        self.adress_list = pd.DataFrame([[0, '', '', '']],
                                        columns=['adress', 'slave', 'datatype', 'circuit'])
        self.adress_data = pd.DataFrame([[0, '', '', '']],
                                        columns=['adress', 'value', 'datatype', 'circuit'])
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
        if debug:
            if self.circuit == "p":
                self.main_client = TMMSClientEthernet('localhost', 502)
            else:
                self.main_client = TMMSClientEthernet('localhost', 504)
            if red: # "red" : redundancy
                if self.circuit == "p":
                    self.red_server = TMMSServerEthernet('localhost', 506)
                    self.red_client = TMMSClientEthernet('localhost', 505)
                else:
                    self.red_server = TMMSServerEthernet('localhost', 505)
                    self.red_client = TMMSClientEthernet('localhost', 506)
        else:
            self.main_client = TMMSClientSerial('COM1')
            if red:
                if self.circuit == "p":
                    self.red_server = TMMSServerEthernet('172.201.8.3', 502)
                    self.red_client = TMMSClientEthernet('172.201.8.4', 503)
                else:
                    self.red_server = TMMSServerEthernet('172.201.8.4', 503)
                    self.red_client = TMMSClientEthernet('172.201.8.3', 502)
        threading.Thread(target=self.red_server.run).start()

    def run_requests(self, red):
        if self.circuit == 'p':
            main_circuit = 'Primary'
            red_circuit = 'Secondary'
        else:
            main_circuit = 'Secondary'
            red_circuit = 'Primary'
        # te = time.time()
        status = False
        try:
            t = time.strftime('[%y-%m-%d %H-%M-%S]')
            self.main_client.connect()
            self.query(self.main_client, circuit)
            status = True
            # print(t + '[INFO] Main Modbus Client data updated ({})'.format(main_circuit))
            print(t + '[INFO] Updating {} \t OK'.format(main_circuit))
            # self.sensor_data.to_csv('test.csv')
        except Exception:
            self.sensor_data.loc[self.sensor_data.loc[:, 'circuit'] == self.circuit, 'movement'] = [None] * (self.nof_sensors // 2)
            self.sensor_data.loc[self.sensor_data.loc[:, 'circuit'] == self.circuit, 'status'] = [None] * (self.nof_sensors // 2)
            # print(t + '[WARNING] Main Modbus Client ({}) not connected'.format(main_circuit))
            print(t + '[INFO] Updating {} \t FAILED -> Check Serial Link'.format(main_circuit))
        if red:
            try:
                t = time.strftime('[%y-%m-%d %H-%M-%S]')
                self.red_client.connect()
                if self.circuit == "p":
                    self.query(self.red_client, 's')
                else:
                    self.query(self.red_client, 'p')
                status = True
                # print(t + '[INFO] Redundant Modbus Client data updated ({})'.format(red_circuit))
                print(t + '[INFO] Updating {} \t OK'.format(red_circuit))
            except Exception:
                self.sensor_data.loc[self.sensor_data.loc[:, 'circuit'] != self.circuit, 'movement'] = [None] * (self.nof_sensors // 2)
                self.sensor_data.loc[self.sensor_data.loc[:, 'circuit'] != self.circuit, 'status'] = [None] * (self.nof_sensors // 2)
                # print(t + '[WARNING] Redundant Modbus Client ({}) not connected'.format(red_circuit))
                print(t + '[INFO] Updating {} \t FAILED -> Check Ethernet Link'.format(red_circuit))
        # print(self.sensor_data.to_string())
        # te -= time.time()
        # print('Modbus queries elapsed time: ' + str(-te))
        return(status)

    def query(self, socket, circuit):
        for i, row in enumerate(self.adress_list.iterrows()):
            if row[1].loc['circuit'] == circuit:
                adress = row[1].loc['adress']
                datatype = row[1].loc['datatype']
                if datatype == 'float32':
                    value, status = socket.read(adress, datatype, slave=self.slave)
                    name = self.sensor_adresses.loc[self.sensor_adresses.loc[:, 'movement'] == adress, 'name'].iloc[0]
                    if status and value[adress] != None:
                        val = value[adress]
                    else:
                        raise('Modbus request status error')
                        val = 0
                    self.sensor_data.loc[self.sensor_data.loc[:, 'name'] == name, 'movement'] = val
                    self.adress_data.loc[self.adress_data.loc[:, 'adress'] == adress, 'value'] = str(val)
                else:
                    value, status = socket.read(adress, datatype, slave=self.slave)
                    names = self.sensor_adresses.loc[self.sensor_adresses.loc[:, 'status'] == adress, 'name']
                    for name in names:
                        bit = int(self.sensor_adresses.loc[self.sensor_adresses.loc[:, 'name'] == name, 'bit'])
                        if status and value[adress] != None:
                            val = value[adress][bit]
                        else:
                            raise('Modbus request status error')
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
    def __init__(self, circuit, thm=True, display=False, red=True, debug=False, parent=None):
        super().__init__(parent)
        self.red = red
        self.circuit = circuit
        self.display = display
        self.rec_nb = 0
        self.setupUi(self)
        # self.modbus = ModbusCommunication(self.circuit, self.red, debug=debug)
        self.modbus.run_requests(self.red)
        self.file_manager = FileManager()
        adress_data = self.modbus.adress_data
        if self.red:
            self.modbus.red_server.update_database(self.modbus.adress_data)
        self.file_manager.update(self.modbus.sensor_data, self.rec_nb, self.circuit)
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
        # t = time.strftime('[%y-%m-%d %H-%M-%S]')
        # Set Internal timer interval
        self.timer_time = 1000 # ms
        # Set looping rec_point interval
        self.rec_nb_history = round(self.file_manager.dt_rec_history / self.timer_time * 1000)
        # Start insternal timer
        self.on_timer_callback_finished = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(self.timer_time)
    
    def on_timer(self):
        if self.on_timer_callback_finished:
            self.rec_nb += 1
            # Update modbus databases
            status = self.modbus.run_requests(self.red)
            adress_data = self.modbus.adress_data
            if self.red:
                self.modbus.red_server.update_database(self.modbus.adress_data)
            # Update data files
            self.file_manager.update_live(self.modbus.sensor_data, self.rec_nb)
            if self.rec_nb > self.rec_nb_history:
                self.rec_nb = 0
                self.file_manager.update_history(self.modbus.sensor_data, self.rec_nb)
            # ETL routine (THM database update)
            if self.refresh_thm:
                ETL(self.file_manager.folder)
            # Modbus Table display
            if self.display:
                self.refresh()
            # Watcher conf update
            with open('tmp/time.txt', 'w') as f:
                f.write(str(time.time()))

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
    # display = True
    # thm = False
    # debug = False
    # red = True
    app = QApplication([])
    win = MainWindow(circuit, thm=thm, display=display, red=red, debug=debug)
    if display:
        win.show()
    app.exec_()
