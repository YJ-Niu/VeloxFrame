import pyftdi
from pyftdi.ftdi import Ftdi
from pyftdi.gpio import (GpioAsyncController,GpioSyncController,GpioMpsseController)
from pyftdi.i2c import I2cController
from pyftdi.spi import SpiController
import time

def set_DSA(chA_gpio,att_states):   

    #write U1 (IP) -> U2 (IN) -> U3 (QP) -> U4 (QN)  

    data_bus_mask = 0x3F00
    IP_LE_mask = 0x0010
    IN_LE_mask = 0x0020
    QP_LE_mask = 0x0040
    QN_LE_mask = 0x0080
    
    IP_DATA = att_states[0]
    IN_DATA = att_states[1]
    QP_DATA = att_states[2]
    QN_DATA = att_states[3]
    
    IP_DATA = IP_DATA <<8
    IN_DATA = IN_DATA <<8
    QP_DATA = QP_DATA <<8
    QN_DATA = QN_DATA <<8    

    chA_gpio.write(IP_DATA & data_bus_mask)
    chA_gpio.write(IP_DATA | IP_LE_mask)
    time.sleep(0.0001)
    chA_gpio.write(IP_DATA & data_bus_mask)
    
    chA_gpio.write(IN_DATA & data_bus_mask)
    chA_gpio.write(IN_DATA | IN_LE_mask)
    time.sleep(0.0001)
    chA_gpio.write(IN_DATA & data_bus_mask)
    
    chA_gpio.write(QP_DATA & data_bus_mask)
    chA_gpio.write(QP_DATA | QP_LE_mask)
    time.sleep(0.0001)
    chA_gpio.write(QP_DATA & data_bus_mask)
    
    chA_gpio.write(QN_DATA & data_bus_mask)
    chA_gpio.write(QN_DATA | QN_LE_mask)
    time.sleep(0.0001)
    chA_gpio.write(QN_DATA & data_bus_mask)
    
    
def get_REV_ID(chB_gpio):
    
    rev_ID0_mask = 0x0080
    rev_ID1_mask = 0x0040
    
    port_read = chB_gpio.read()
    
    rev_ID0 = (port_read & rev_ID0_mask) >> 7
    rev_ID1 = (port_read & rev_ID1_mask) >> 6
    rev_ID = 2*rev_ID1 + rev_ID0
    
    return rev_ID 
    

def get_TMP_ALERT(chB_gpio): 
    
    temp_alert_mask = 0x0020
    port_read = chB_gpio.read()
    temp_ALERT = (port_read & temp_alert_mask) >> 5
    
    return temp_ALERT 
    
def get_INA_WARNING(chB_gpio): 
    
    INA_WARNING_mask = 0x4000
    port_read = chB_gpio.read()
    INA_WARNING = (port_read & INA_WARNING_mask) >> 14
    
    return INA_WARNING 

def get_INA_CRITICAL(chB_gpio): 
    
    INA_CRITICAL_mask = 0x2000
    port_read = chB_gpio.read()
    INA_CRITICAL = (port_read & INA_CRITICAL_mask) >> 13
    
    return INA_CRITICAL     
    
def get_INA_PV(chB_gpio): 
    
    INA_PV_mask = 0x1000
    port_read = chB_gpio.read()
    INA_PV = (port_read & INA_PV_mask) >> 12
    
    return INA_PV         
    
def set_PA_PWR_DIS(chB_gpio,chB_gpio_out,state):
    
    #disable PA 
    if state == 1:
        chB_gpio_out = chB_gpio_out | (1 << 11)
    #enable PA        
    elif state == 0:
        chB_gpio_out = chB_gpio_out & ~(1 << 11) 
        
    chB_gpio.write(chB_gpio_out)
        
    return chB_gpio_out  
    
def set_RGB_LED(chB_gpio,chB_gpio_out,red,green,blue):
    
    if red == 0:
        chB_gpio_out = chB_gpio_out | (1 << 8)
    elif red == 1:
        chB_gpio_out = chB_gpio_out & ~(1 << 8) 
        
    if green == 0:
        chB_gpio_out = chB_gpio_out | (1 << 9)
    elif green == 1:
        chB_gpio_out = chB_gpio_out & ~(1 << 9) 
        
    if blue == 0:
        chB_gpio_out = chB_gpio_out | (1 << 10)
    elif blue == 1:
        chB_gpio_out = chB_gpio_out & ~(1 << 10)
        
    chB_gpio.write(chB_gpio_out)
        
    return chB_gpio_out      