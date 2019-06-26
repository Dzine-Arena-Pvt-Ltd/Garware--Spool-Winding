import serial
import numpy as np
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import time
import json

PORT = 'COM3'
start_reg = 4096
start_val = 600
class ModbusHandler:

       def __init__(self):

            # with open("resources/config/config_plc.json", "r") as file:
            #     self.config_js_data = json.load(file)

            self.plc_flag = False
            try:
                   self.plc = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='O', stopbits=1, xonxoff=0))
                   self.plc.set_timeout(0.5)
                   # for keys in self.config_js_data.items():
                   #     setattr(self, keys[0], keys[1])
                   self.plc_flag = True
                   print(self.plc_flag)
            except Exception as e:
                   print(e)

       def start_plc(self):
           try:

               self.plc.execute(1, cst.WRITE_SINGLE_REGISTER, start_reg, output_value=start_val)
               print("Start")
           except Exception as e:
               print(e)

       def stop_plc(self):
           try:

               self.plc.execute(1, cst.WRITE_SINGLE_REGISTER, start_reg, output_value=0)
               print("Stop")
           except Exception as e:
               print(e)

       def m1_current(self):
           try:
               if not self.plc_flag:
                   return

               self.plc.execute(self.dev_id, cst.READ_HOLDING_REGISTERS, self.m1_current_reg, 1)
               time.sleep(0.05)
           except Exception as e:
               print(e)


       def m2_current(self):
           try:
               if not self.plc_flag:
                   return

               self.plc.execute(1, cst.READ_HOLDING_REGISTERS, self.m1_current_reg, 1)
               time.sleep(0.05)
           except Exception as e:
               print(e)


       def spool_check(self):
           try:
               if not self.plc_flag:
                   return

               self.plc.execute(self.dev_id, cst.READ_HOLDING_REGISTERS, self.spool_reg, 1)
               time.sleep(0.05)
           except Exception as e:
               print(e)

plc=ModbusHandler()
plc.start_plc()# print(plc.m1_current())
# print(plc.m2_current())
# print(plc.spool_check())

# time.sleep(3)
# plc.stop_plc()
