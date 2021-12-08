# -*- coding: utf-8 -*-
"""
Created on Fri Oct 15 10:44:47 2021

@author: GLA
"""

from pymodbus.server.asynchronous import StartTcpServer, StartSerialServer, StopServer
from pymodbus.client.sync import ModbusTcpClient, ModbusSerialClient
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from twisted.internet.serialport import SerialPort

import time
import sys
import struct

class Struct:
    pass

class TMMSModbus:
    def __init__(self):
        self._type_dict = Struct()
        self._type_dict.encode = {'float32': self.float32toBin, 'boolean':self.BooltoBin}
        self._type_dict.decode = {'float32': self.Bintofloat32, 'boolean':self.BintoBool}
        
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
        # return(struct.unpack('b', value))
    
    def BintoBool(self, value):
        if type(value[0]) == bytes:
            return(bool(struct.unpack('b', value[0])[0]))
        else:
            return(bool(value[0]))
    
class TMMSModbusClient(TMMSModbus):
    def __init__(self):
        TMMSModbus.__init__(self)
        self.dataframe = []
        self.nof_words = {'float32':2, 'boolean':1}

    # def connect(self):
    #     self.socket.connet()
    
    # def close(self):
    #     self.socket.close()
    
    def request(self, address, datatype):
        try:
            req = self.socket.read_holding_registers(address, self.nof_words[datatype])
            if not req.isError():
                value = self.decode(req.registers, datatype)
                status = True
            else:
                print('error')
                print(address)
                value = 0
                status = False
        except:
            value = 0
            status = False
        return(value, status)


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
        self.socket = ModbusSerialClient(port=self.port, defer_reactor_run=True, stopbits=1, bytesize=8, baudrate=9600, timeout=1)
        self.socket.connect()
        
    def close(self):
        self.socket.close()

