import pyftdi
from pyftdi.ftdi import Ftdi
from pyftdi.i2c import I2cController

def init(i2c,i2c_dev_addr):    
    MAX31760 = i2c.get_port(i2c_dev_addr)

    #CR1
    MAX31760.write_to(0x00, b'\x19')
    #CR2 
    MAX31760.write_to(0x01, b'\x30')# Overtemperature protection changed to latching (0x70 -> 0x30)
    #CR3
    MAX31760.write_to(0x02, b'\x31')
    #MASK
    MAX31760.write_to(0x04, b'\xD7')
    #IFR
    MAX31760.write_to(0x05, b'\x14')
    #RHSH (22degC TMP_ALERT activation limit) 
    MAX31760.write_to(0x06, b'\x46')
    #LHSH (70degC TMP_ALERT activation lmimit)
    MAX31760.write_to(0x0C, b'\x46')

    # LUT [address (hex)][PWM (%)]
    LUT = [[0x20,0], # T<18 degC
           [0x21,0], # 18<T<20 deg
           [0x22,0], # 20<T<22 deg
           [0x23,0],# 22<T<24 deg
           [0x24,0],# 24<T<26 deg
           [0x25,0],# 26<T<28 deg
           [0x26,0],# 28<T<30 deg
           [0x27,0],# 30<T<32 degC
           [0x28,0],# 32<T<34 deg
           [0x29,0],# 34<T<36 deg
           [0x2A,0],# 36<T<38 deg
           [0x2B,0],# 38<T<40 deg
           [0x2C,0],# 40<T<42 deg
           [0x2D,100],
           [0x2E,100],
           [0x2F,100],
           [0x30,100],
           [0x31,100],
           [0x32,100],
           [0x33,100],
           [0x34,100],
           [0x35,100],#50
           [0x36,100],
           [0x37,100],
           [0x38,100],
           [0x39,100],
           [0x3A,100],
           [0x3B,100],
           [0x3C,100],
           [0x3D,100],
           [0x3E,100],
           [0x3F,100],
           [0x40,100],
           [0x41,100],
           [0x42,100],
           [0x43,100],
           [0x44,100],
           [0x45,100],
           [0x46,100],
           [0x47,100],
           [0x48,100],
           [0x49,100],
           [0x4A,100],
           [0x4B,100],
           [0x4C,100],
           [0x4D,100],
           [0x4E,100],
           [0x4F,100]]
           
    #Program LUT
    for x in range(48):
        LUT_addr = LUT[x][0]
        LUT_data = LUT[x][1]
        
        LUT_data = int(255*(LUT_data/100))
        LUT_data_byte = LUT_data.to_bytes(1, 'big')
        
        MAX31760.write_to(LUT_addr, LUT_data_byte)

    #Store to EEPROM
    MAX31760.write_to(0x5B, b'\x1F')
           
    
def set_PWM_override(i2c,i2c_dev_addr,duty_cycle_pct):    
    MAX31760 = i2c.get_port(i2c_dev_addr)
    #CR2 
    MAX31760.write_to(0x01, b'\x71')
    
    duty_cycle = int(255*(duty_cycle_pct/100))
    PWM_byte = duty_cycle.to_bytes(1, 'big') 

    #PWMR
    MAX31760.write_to(0x50, PWM_byte)
    
    byte_val = MAX31760.read_from(0x51, 1)
    hex_val = hex(int.from_bytes(byte_val, 'big'))
    
    return hex_val    
    
def get_PWM(i2c,i2c_dev_addr):    
    MAX31760 = i2c.get_port(i2c_dev_addr)
    
    byte_val = MAX31760.read_from(0x51, 1)
    dec_val = int.from_bytes(byte_val, 'big')
    pwm_pct = 100*(dec_val/255)
        
    return pwm_pct
    
def get_RPM(i2c,i2c_dev_addr):    
    MAX31760 = i2c.get_port(i2c_dev_addr)
    
    #TC1H
    byte_val = MAX31760.read_from(0x52, 1)
    tach1_cnt_MSB = int.from_bytes(byte_val, 'big')
    
    #TC1L
    byte_val = MAX31760.read_from(0x53, 1)
    tach1_cnt_LSB = int.from_bytes(byte_val, 'big')
    
    if (tach1_cnt_MSB == 0) & (tach1_cnt_LSB < 100):
        fan_rpm = 0
    elif (tach1_cnt_MSB == 255) & (tach1_cnt_LSB == 255):
        fan_rpm = 0
    else:
        fan_rpm = 60 * (100000/(tach1_cnt_MSB*256+(tach1_cnt_LSB)))/2
    
    return fan_rpm

def get_remote_temp(i2c,i2c_dev_addr):    
    MAX31760 = i2c.get_port(i2c_dev_addr)
    
   #RTH
    byte_val = MAX31760.read_from(0x56, 1)
    remote_temp_MSB = int.from_bytes(byte_val, 'big') 

   #RTL
    byte_val = MAX31760.read_from(0x57, 1)
    remote_temp_LSB = int.from_bytes(byte_val, 'big') 
   
    remote_temp = remote_temp_MSB + (remote_temp_LSB/256)
    
    return remote_temp
    
def get_local_temp(i2c,i2c_dev_addr):    
    MAX31760 = i2c.get_port(i2c_dev_addr)
    
   #LTH
    byte_val = MAX31760.read_from(0x58, 1)
    local_temp_MSB = int.from_bytes(byte_val, 'big') 

   #LTL
    byte_val = MAX31760.read_from(0x59, 1)
    local_temp_LSB = int.from_bytes(byte_val, 'big') 
   
    local_temp = local_temp_MSB + (local_temp_LSB/256)
    
    return local_temp
    