import pyftdi
from pyftdi.ftdi import Ftdi
from pyftdi.i2c import I2cController

def init(i2c,i2c_dev_addr):    
    INA3221 = i2c.get_port(i2c_dev_addr)

    #Configuration
    INA3221.write_to(0x00, b'\x77\x27')
    
    
def read_ch(i2c, i2c_dev_addr, CH, shuntR):
    INA3221 = i2c.get_port(i2c_dev_addr)

    if CH == 1:
        voltage_raw = INA3221.read_from(0x02, 2)
        voltage_raw = int.from_bytes(voltage_raw, 'big')
        current_raw = INA3221.read_from(0x01, 2)
        current_raw = int.from_bytes(current_raw, 'big')
    elif CH == 2:
        voltage_raw = INA3221.read_from(0x04, 2)
        voltage_raw = int.from_bytes(voltage_raw, 'big')
        current_raw = INA3221.read_from(0x03, 2)
        current_raw = int.from_bytes(current_raw, 'big')
        
    elif CH == 3:
        voltage_raw = INA3221.read_from(0x06, 2)
        voltage_raw = int.from_bytes(voltage_raw, 'big')
        current_raw = INA3221.read_from(0x05, 2)
        current_raw = int.from_bytes(current_raw, 'big')
    
    voltage = (voltage_raw/8)*0.008
    current = ((current_raw/8)*0.00004)/shuntR
        
    return voltage, current
