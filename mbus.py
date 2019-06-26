import serial
import numpy as np
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import time


PORT = 'COM3' # Port Selection

start_reg = 4096# Start Holding Reg
start_val = 1 # Start Value
stop_reg = 4096
stop_val = 0#Stop Value
m1_reg = 4097
m2_reg = 4098
spool_reg = 4099
auto_man_reg = 4100
auto_val = 0
manual_val = 1
idel_state = 0
plc_flag = False
try:
    # Connect to the slave
    master = modbus_rtu.RtuMaster(
        serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
    master.set_timeout(5.0)
    master.set_verbose(True)
    plc_flag = True
except Exception as e:
    print(e)
def start_plc():
    try:
        if not plc_flag:
            return
        master.execute(1,cst.WRITE_SINGLE_REGISTER, start_reg, output_value= start_val)
        print("Plc Started")
    except Exception as e:
        print(e)

def stop_plc():
      try:
            if not plc_flag:
                return
            master.execute(1, cst.WRITE_SINGLE_REGISTER, start_reg, output_value=stop_val)
            print("Plc Stopped")
      except Exception as e:
            print(e)


def m1_current():
    try:
        if not plc_flag:
            return
        else:
            return (master.execute(1, cst.READ_HOLDING_REGISTERS, m1_reg, 1))[0]
    except Exception as e:
        print(e)

def m2_current():
    try:
        if not plc_flag:
            return
        else:
            return (master.execute(1, cst.READ_HOLDING_REGISTERS, m2_reg, 1))[0]
    except Exception as e:
        print(e)

def spool():
    try:
        if not plc_flag:
            return
        else:
            return (master.execute(1, cst.READ_HOLDING_REGISTERS, spool_reg, 1))[0]

    except Exception as e:
        print(e)

def auto_mode():
    try:
        if not plc_flag:
            return
        else:
            return (master.execute(1, cst.WRITE_SINGLE_REGISTER, auto_man_reg, output_value= auto_val))

    except Exception as e:
        print(e)

def manual_mode():
    try:
        if not plc_flag:
            return
        else:
            return (master.execute(1, cst.WRITE_SINGLE_REGISTER, auto_man_reg, output_value= manual_val))

    except Exception as e:
        print(e)


def main():
    """main"""

    start_plc()
    time.sleep(5)
    # stop_plc()
    # time.sleep(5)
    m1 = m1_current()
    time.sleep(0.5)
    print(m1)
    m2 = m2_current()
    time.sleep(0.5)
    print(m2)

    s = spool()
    time.sleep(0.5)
    print(s)



if __name__ == "__main__":
    main()