# -*- coding: utf-8 -*-
"""
Created on Fri Oct 15 10:44:47 2021

@author: GLA
"""

# import logging
# logging.basicConfig()
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

from pymodbus.server.asynchronous import StartTcpServer, StartSerialServer, StopServer
from pymodbus.client.sync import ModbusTcpClient, ModbusSerialClient
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
# from twisted.internet.serialport import SerialPort

import time
import sys
import struct

class Struct:
    pass

class TMMSModbus:
    def __init__(self):
        self._type_dict = Struct()
        self._type_dict.encode = {'float32': self.float32toBin, 'boolean':self.BooltoBin, 'byte':self.BintoByte, 'uint32':int}
        self._type_dict.decode = {'float32': self.Bintofloat32, 'boolean':self.BintoBool, 'byte':self.BytetoBin, 'uint32':self.BintoInt}
        
    def encode(self, value, datatype):
        return(self._type_dict.encode[datatype](value))
        
    def decode(self, value, datatype):
        return(self._type_dict.decode[datatype](value))
    
    def float32toBin(self, value):
        val = struct.pack('>f', value)
        return([val[0] * 2**8 + val[1], val[2] * 2**8 + val[3]])
    
    def Bintofloat32(self, values):
        MSB = struct.pack('>H', values[0])
        LSB = struct.pack('>H', values[1])
        val = MSB + LSB
        return(struct.unpack('>f', val)[0])
    
    def BooltoBin(self, value):
        return(int(value))
        # return(struct.pack('b', value))
    
    def BintoBool(self, value):
        if type(value[0]) == bytes:
            return(bool(struct.unpack('b', value[0])[0]))
        else:
            return(bool(value[0]))
        
    def BytetoBin(self, value):
        value = value[0]
        retValue = []
        for i in range(16):
            retValue.insert(0, value & 0x01)
            value = value >> 1
        return(retValue)
    
    def BintoByte(self, values):
        retValue = 0
        for i, val in enumerate(values):
            retValue += val << (16-(i+1))
        return(retValue)
    
    def BintoInt(self, value):
        return(value[0])
           
class TMMSModbusClient(TMMSModbus):
    def __init__(self):
        TMMSModbus.__init__(self)
        self.dataframe = []
        self.nof_words = {'float32':2, 'boolean':1, 'uint32':1, 'byte':1}
        self.connected = True

    def connect(self):
        self.socket.connect()
    
    def close(self):
        self.socket.close()
    
    def read(self, adresses, datatype, slave=0):
        if type(adresses) != list:
                adresses = [adresses]
        requests = {}
        status = {}
        for address in adresses:
            request = self.socket.read_holding_registers(address, self.nof_words[datatype], unit=slave)
            if not request.isError():
                requests[address] = self.decode(request.registers, datatype)
                status[address] = True
            else:
                requests[address] = None
                status[address] = True
        return(requests, status)
    
    def write(self, address, value, slave=0):
        request = self.socket.write_register(address, value, unit=slave)
        status = not request.isError()
        return(request, status)

class TMMSModbusEthernet(TMMSModbus):
    def __init__(self, IPaddress, port):
        TMMSModbus.__init__(self)
        self.IPaddress = IPaddress
        self.port = port

class TMMSModbusSerial(TMMSModbus):
    def __init__(self, port):
        TMMSModbus.__init__(self)
        self.port = port

class TMMSClientEthernet(TMMSModbusEthernet, TMMSModbusClient):
    def __init__(self, IPaddress, port):
        TMMSModbusEthernet.__init__(self, IPaddress, port)
        TMMSModbusClient.__init__(self)
        self.socket = ModbusTcpClient(self.IPaddress, self.port)
        self.socket.connect()
        
    def close(self):
        self.socket.close()
        
class TMMSClientSerial(TMMSModbusSerial, TMMSModbusClient):
    def __init__(self, port):
        TMMSModbusSerial.__init__(self, port)
        TMMSModbusClient.__init__(self)
        self.socket = ModbusSerialClient(port=self.port, stopbits=1, bytesize=8, baudrate=9600, timeout=1)
        self.socket.connect()
        
    def close(self):
        self.socket.close()
        
class TMMSModbusServer(TMMSModbus):
    def __init__(self, identity):
        TMMSModbus.__init__(self)
        self.identity = identity
        self.block = ModbusSparseDataBlock({40001: 0})
        self.slave = ModbusSlaveContext(co=None, di=None, hr=self.block, ir=None, zero_mode=True)
        self.context = ModbusServerContext(slaves=self.slave, single=True)
        
    def update_database(self, adress_data):
            for k in range(len(adress_data)):
                adress = adress_data.loc[k,'adress']
                datatype = adress_data.loc[k,'datatype']
                if datatype == 'float32':
                    try:
                        if adress_data.loc[k,'value'] != 'None':
                            value = float(adress_data.loc[k,'value'])
                        else:
                            value = 0
                    except:
                        value = 0
                elif datatype == 'byte':
                    try:
                        if adress_data.loc[k,'value'] != str([None] * 16) and type(adress_data.loc[k,'value']) == str:
                            value = [int(s) for s in adress_data.loc[k,'value'].split('[')[1].split(']')[0].split(',')]
                            if type(value) != list:
                                value = [0] * 16
                        else:
                            value = [0] * 16
                    except:
                        value = [0] * 16
                self.block.setValues(adress, self.encode(value, datatype))

class TMMSServerEthernet(TMMSModbusEthernet, TMMSModbusServer):
    def __init__(self, IPaddress, port, identity=0):
        TMMSModbusEthernet.__init__(self, IPaddress, port)
        TMMSModbusServer.__init__(self, identity)
        
    def run(self):
        StartTcpServer(self.context, defer_reactor_run=False, identity=1, address=(self.IPaddress, self.port))
        

