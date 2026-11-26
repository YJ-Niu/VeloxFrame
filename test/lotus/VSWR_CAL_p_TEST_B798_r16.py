import os
import sys
import serial
import time
from datetime import datetime
import serial.tools.list_ports

import os.path
import pyvisa
from ctypes import *
import ctypes
from numpy import exp, abs, angle, pi
import pandas as pd
import cmath
import sys
import numpy as np
import matplotlib
import math
import time
from lotus_control import *
#from lotus_functions import *
import lotus_functions
from usb.backend import libusb1
import zva
# from datetime import datetime
import lotus_control
from powerControl_b798_r0 import *

def timeStart():
    return time.time()


def timeStop():
    return time.time()


def testDone(timeBegin, timeEnd):
    sys_print("\nTotal test time %fs" %(timeEnd - timeBegin))


#### Instructions ###### 
# Update Line 55 with serial port address
# Update Line 75 with Address of your Lotus Tuner
# Ensure your Lotus tuner is calibrated at mag/angles listed in lines 79/80 at the following frequencies:
# 2402, 2440, 2460, 2480, 5150, 5175, 5200, 5228, 5250, 5725, 5755, 5795, 5823, 5945, 5975, 5987, 
# 6015, 6029, 6051, 6075, 6115, 6131, 6176, 6200, 6216, 6240, 6264, 6325, 6341, 6365, 6405, 6413 






######### log file ##############

timeBegin = timeStart()

portName = '/dev/cu.usbmodem123456781'
pctl = powerControl(portName)

file_path = '/Users/gdlocal/Documents/VSWR-CAL'

now = datetime.now()
dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")

log_date = time_ = datetime.now().strftime('%Y-%m-%d')
if not os.path.isdir(f"{file_path}/{log_date}"):
    os.mkdir(f"{file_path}/{log_date}")
filename = file_path + "/" + log_date + '/' + 'vswr_cal_plus_test_' + dt_string + '.csv'

def sys_print(*args):
    ss = [str(i) for i in args]
    time_ = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(filename, "a+") as file:
        file.write("\n".join(ss) + "\n")
    print(time_, "->", "\n".join(ss))

sys_print(filename)
# sys.stdout = open(filename, 'w')
pctl.DUTPowerON(0)

######### LOTUS ##############

sys_print(libusb1.get_backend())

sys_print(lotus_control.list_units())

P0_00001 = lotus_control.setup_unit('ftdi://ftdi:2232:P0_00026/1','P0_00026')

cal_file = sys.path[0] + '/cal_table.txt'

target_mag = [0.1, 0.5, 0.5, 0.5, .636, 0.636, 0.1, 0.33, 0.5, 0.6, 0.636]
target_angle = [ 270, 45, 270, 315, 180, 225, 90, 135, 270, 270, 315]

######### B798 SIP ###########

ports = serial.tools.list_ports.comports()
for p in ports:
    sys_print(p.device)
# sys_print(len(ports), 'ports found')



# connect to sip 
sys_print(ports[3].device)
sys_print(serial.VERSION)
ser = serial.Serial("/dev/cu.kis-14333100-ch-2", 921600, timeout=1)
sys_print(ser.isOpen())
time.sleep(2)


# # init device
import re
# 2 rls
line = b''
ser.write((b'syscfg print MLB#\n '))
line = ser.readline()
sys_print(line)
while "syscfg:ok" not in line.decode():
    line = ser.readline()
    print(line)
content = re.search(r'"(.*?)"', line.decode())
if content:
    mlb_number = content.group(1)  
else:
    print("Error: No MLB SN")
    sys.exit()
    
# while
line = b''
# time.sleep(2)
ser.write(b'bt send bcal\n')
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    sys_print(line)
    if "Timeout" in line.decode():
        print("=="*20)
        sys_print("END test Fail")
        print("=="*20)
        sys.exit()


# 2 rls

ser.write((b'syscfg print CFG#\n '))
line = ser.readline()
sys_print(line)
line = ser.readline()
sys_print(line)

## triangle switch

line = b''
ser.write((b'bt init\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


line = b''
ser.write((b'bt set output hex\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line) 


line = b''
ser.write((b'bt send cmd 011AFD1000000100000803000D00040000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)





line = b''
ser.write((b'bt send cmd 011AFD1000000100000804000D00040000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)




line = b''
ser.write((b'bt trgl_mode cond\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)





# resets
line = b''
ser.write((b'bt send cmd 01030C00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


# resets
line = b''
ser.write((b'bt send cmd 01F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)



# resets
line = b''
ser.write((b'bt send cmd 011A0C0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


# reset
line = b''
ser.write((b'bt send cmd 01030C00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


# phy level reset 
line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)



# exit bt bridge 
line = b''
ser.write((b'bt send cmd 01F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)



######################################################################################
#################################### vswr cal commands ##############################
######################################################################################



#### 2402MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 2402MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))
    
    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,2402, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,2402, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)
        

    line = b''
    ser.write((b'bt send cmd 01F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01F9FF0100\n '))
            line = ser.readline()
            sys_print(line)

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
    line = str(ser.readline())
    #line.strip()
    
    #line = ser.readline()
    #line.strip()
    #while 'bt:ok' not in line.decode():
    while 'bt:ok' not in line:
        line = str(ser.readline())
        #line.strip()
        sys_print(line)
        sys_print(type(line))
        if 'bad params' in line:
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
            line = str(ser.readline())
            line.strp()
            sys_print(line) 

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000620962090000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000620962090000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
            line = ser.readline()
            sys_print(line) 

# 2420MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 2420MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))
    
    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,2420, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,2420, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
    line = str(ser.readline()).strip()
    sys_print(line)
    while 'bt:ok' not in line:
        sys_print("[sf]", line)
        line = str(ser.readline())
        sys_print(line)
        if 'bad params' in line:
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
            line = str(ser.readline())
            sys_print(line) 

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000740974090000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000740974090000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
            line = ser.readline()
            sys_print(line)   

# 2440MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 2440MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))


    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360


    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,2440, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,2440, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
    line = ser.readline()
    if(type(line) is str):
        sys_print("[SF2] string type")
        line  = line.encode()
    sys_print(repr(line))
    while 'bt:ok' not in line.decode():
        sys_print("[sf1]", line)
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
            line = ser.readline()
            sys_print(line) 

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000880988090000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000880988090000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
            line = ser.readline()
            sys_print(line)  


# 2460MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 2460MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))


    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360


    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,2460, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,2460, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
    line = ser.readline()
    if(type(line) is str):
        line = line.encode()
    sys_print(line)
    sys_print(type(line))
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        if not line:
            sys_print("[sf4] empty line")
            break
        sys_print("[sf3]", type(line))
        if(type(line) is str):
            line = line.encode()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
            line = ser.readline()
            sys_print(line) 

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd16010000009C099C090000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd16010000009C099C090000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
            line = ser.readline()
            sys_print(line) 


# 2480MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 2480MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,2480, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,2480, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        if not line:
            break
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
            line = ser.readline()
            sys_print(line) 

    # set tx power         

        line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000B009B0090000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000B009B0090000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
            line = ser.readline()
            sys_print(line)  

# 5150MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5150MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5150, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5150, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        if not line:
            break
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
            line = ser.readline()
            sys_print(line) 

    # set tx power         

        line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd16010000001E141E140000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd16010000001E141E140000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
            line = ser.readline()
            sys_print(line)         


# 5175MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5175MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5175, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5175, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)
    
    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
            line = ser.readline()
            sys_print(line)       

   # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000371437140000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000371437140000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
            line = ser.readline()
            sys_print(line)         


# 5200MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5200MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5200, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5200, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        if not line:
            break
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
            line = ser.readline()
            sys_print(line)        

   # set tx power         

        line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000501450140000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000501450140000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
            line = ser.readline()
            sys_print(line)   

# 5228MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5225MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5225, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5225, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)



    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
            line = ser.readline()
            sys_print(line) 

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd16010000006C146C140000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd16010000006C146C140000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
            line = ser.readline()
            sys_print(line)  


# 5725MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5725MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5725, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5725, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)


    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000020000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000020000000000000000\n '))
            line = ser.readline()
            sys_print(line)     

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd16010000005D165D160000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd16010000005D165D160000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000020000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000020000000000000000\n '))
            line = ser.readline()
            sys_print(line)  


# 5795MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5785MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5785, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5785, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)


    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000020000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000020000000000000000\n '))
            line = ser.readline()
            sys_print(line)       

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000A316A3160000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000A316A3160000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000020000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000020000000000000000\n '))
            line = ser.readline()
            sys_print(line)  


# 5823MHz -d
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5820MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5820, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5820, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)  


    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000020000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000020000000000000000\n '))
            line = ser.readline()
            sys_print(line)        

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000BF16BF160000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000BF16BF160000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000020000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000020000000000000000\n '))
            line = ser.readline()
            sys_print(line)   



# 5945MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5945MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5945, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5945, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)  

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)        

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000391739170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000391739170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)     


# 5975MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5965MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360


    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5965, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5965, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)   

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000571757170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000571757170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)        

# 5987MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 5985MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5985, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5985, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)   

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000631763170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000631763170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)       


# 6015MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6010MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,5985, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,5985, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)   


    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)     

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd16010000007F177F170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd16010000007F177F170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)       


# 6029MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6030MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6030, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6030, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)   

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd16010000008D178D170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd16010000008D178D170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
            line = ser.readline()
            sys_print(line)    
     



# 6051MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6055MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6055, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6055, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)  

    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
            line = ser.readline()
            sys_print(line)        

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000A317A3170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000A317A3170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
            line = ser.readline()
            sys_print(line)      

# 6075MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6080MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6080, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6080, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    

     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
            line = ser.readline()
            sys_print(line)       


    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000BB17BB170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000BB17BB170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
            line = ser.readline()
            sys_print(line)      

# 6115MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6110MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6110, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6110, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
            line = ser.readline()
            sys_print(line)       
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000E317E3170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000E317E3170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
            line = ser.readline()
            sys_print(line)    


# 6131MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6135MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6135, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6135, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


    # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
            line = ser.readline()
            sys_print(line)     
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000F317F3170000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000F317F3170000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
            line = ser.readline()
            sys_print(line)    


# 6176MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6160MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6160, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6160, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)

    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)      
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000201820180000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000201820180000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)     


# 6200MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6190MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6190, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6190, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)         
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000381838180000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000381838180000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)    

# 6216MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6215MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6215, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6215, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)        
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000481848180000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000481848180000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)    

# 6240MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6240MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))


    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360


    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6240, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6240, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)         
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000601860180000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000601860180000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)     

# 6264MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6265MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))


    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6265, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6265, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)
                

     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)       
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000781878180000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000781878180000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)    


# 6325MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6320MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6320, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6320, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)



    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)        
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000B518B5180000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000B518B5180000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)     


# 6341MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6345MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6345, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6345, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)      
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000C518C5180000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000C518C5180000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)     

# 6365MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6370MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6370, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6370, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)



    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)       
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000DD18DD180000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000DD18DD180000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)    

# 6405MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6400MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6400, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6400, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)         
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd1601000000051905190000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd1601000000051905190000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

    # stop vswr         
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)    

# 6413MHz
for i in range(0,len(target_mag),1):
    sys_print('Frequency: 6425MHz: Load Index %d: Target Mag: %0.4f: Target Angle: %0.4f' % (i,target_mag[i],target_angle[i]))

    # if target_angle[i] > 180:
    #     target_angle[i] = target_angle[i] - 360

    # if target_mag[i] == 0.25:

    recall_status = lotus_functions.recall_cal_load(P0_00001,6425, target_mag[i], target_angle[i], cal_file)
    sys_print(recall_status)
    time.sleep(0.2)

    # else:

    #     recall_status = lotus_functions.recall_cal_load(P0_00001,6425, target_mag[i], target_angle[i], cal_file)
    #     sys_print(recall_status)
    #     time.sleep(0.2)


    line = b''
    ser.write((b'bt send cmd 0188FD00\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 0188FD00\n '))
            line = ser.readline()
            sys_print(line)

    line = b''
    ser.write((b'bt send cmd F9FF0100\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd F9FF0100\n '))
            line = ser.readline()
            sys_print(line)    


     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)        
    

    # set tx power         

    line = b''
    ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
            line = ser.readline()
            sys_print(line) 
    
    # set band                    
    line = b''
    ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
            line = ser.readline()
            sys_print(line) 

    # set ch/freq        
    line = b''
    ser.write((b'bt send cmd 01cdfd16010000000D190D190000050553010a01ff010a000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 01cdfd16010000000D190D190000050553010a01ff010a000000\n '))
            line = ser.readline()
            sys_print(line)         

    # get results         
    line = b''
    ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)   
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
            line = ser.readline()
            sys_print(line)   

     # enable vswr 
    line = b''
    ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
    line = ser.readline()
    sys_print(line)
    while 'bt:ok' not in line.decode():
        line = ser.readline()
        sys_print(line)
        if 'bad params' in line.decode():
            ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
            line = ser.readline()
            sys_print(line)        
        
######################################################################################
#################################### vswr test commands ##############################
######################################################################################

pctl.DUTPowerOff(0)

pctl.DUTPowerON(0)

# 2 rls
ser.write((b'syscfg print MLB#\n '))
line = ser.readline()
sys_print(line)
line = ser.readline()
sys_print(line)




# while
line = b''
# time.sleep(2)
ser.write(b' bt send bcal\n ')
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


# 2 rls

ser.write((b'syscfg print CFG#\n '))
line = ser.readline()
sys_print(line)
line = ser.readline()
sys_print(line)



line = b''
ser.write((b'bt init\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


line = b''
ser.write((b'bt set output hex\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line) 




# resets
line = b''
ser.write((b'bt send cmd 01030C00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


# resets
line = b''
ser.write((b'bt send cmd 01F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)



# resets
line = b''
ser.write((b'bt send cmd 011A0C0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


# reset
line = b''
ser.write((b'bt send cmd 01030C00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)


# phy level reset 
line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)



# exit bt bridge 
line = b''
ser.write((b'bt send cmd 01F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)



#### 2402MHz


#### 2402MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)

# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f0010000112000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line) 

# set tx power         

    line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000620962090000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000620962090000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f0010000012000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line)   

# 2420MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line) 

# set tx power         

    line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000740974090000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000740974090000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line)   

# 2440MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line) 

# set tx power         

    line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000880988090000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000880988090000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line)  


# 2460MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line) 

# set tx power         

    line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd16010000009C099C090000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd16010000009C099C090000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line) 


# 2480MHz -d



line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line) 

# set tx power         

    line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700000028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000B009B0090000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000B009B0090000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000000000000000000000\n '))
        line = ser.readline()
        sys_print(line)  

# 5150MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
        line = ser.readline()
        sys_print(line) 

# set tx power         

    line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd16010000001E141E140000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd16010000001E141E140000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
        line = ser.readline()
        sys_print(line)         


# 5175MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
        line = ser.readline()
        sys_print(line)       

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000371437140000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000371437140000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
        line = ser.readline()
        sys_print(line)         


# 5200MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)

# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
        line = ser.readline()
        sys_print(line)        

# set tx power         

    line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000501450140000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000501450140000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
        line = ser.readline()
        sys_print(line)   

# 5228MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000010000000000000000\n '))
        line = ser.readline()
        sys_print(line) 

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700010028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd16010000006C146C140000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd16010000006C146C140000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000010000000000000000\n '))
        line = ser.readline()
        sys_print(line)  


# 5725MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000020000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100001120000000000020000000000000000\n '))
        line = ser.readline()
        sys_print(line)     

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd16010000005D165D160000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd16010000005D165D160000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000020000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001404000f00100000120000000000020000000000000000\n '))
        line = ser.readline()
        sys_print(line)  


# 5795MHz -d

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000020000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000020000000000000000\n '))
        line = ser.readline()
        sys_print(line)       

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000A316A3160000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000A316A3160000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000020000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000020000000000000000\n '))
        line = ser.readline()
        sys_print(line)  


# 5823MHz -d


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000020000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000020000000000000000\n '))
        line = ser.readline()
        sys_print(line)        

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700020028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000BF16BF160000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000BF16BF160000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000020000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000020000000000000000\n '))
        line = ser.readline()
        sys_print(line)   



# 5945MHz


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)        

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000391739170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000391739170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)     


# 5975MHz


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)    

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000571757170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000571757170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)        

# 5987MHz


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)    

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000631763170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000631763170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)       


# 6015MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)     

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd16010000007F177F170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd16010000007F177F170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)       


# 6029MHz


line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)    

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700040028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd16010000008D178D170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd16010000008D178D170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000040000000000000000\n '))
        line = ser.readline()
        sys_print(line)    
 



# 6051MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
        line = ser.readline()
        sys_print(line)        

# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600040000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000A317A3170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000A317A3170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
        line = ser.readline()
        sys_print(line)      

# 6075MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
        line = ser.readline()
        sys_print(line)       


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000BB17BB170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000BB17BB170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
        line = ser.readline()
        sys_print(line)      

# 6115MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
        line = ser.readline()
        sys_print(line)       


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000E317E3170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000E317E3170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
        line = ser.readline()
        sys_print(line)    


# 6131MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




# enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000050000000000000000\n '))
        line = ser.readline()
        sys_print(line)     


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000F317F3170000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000F317F3170000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000050000000000000000\n '))
        line = ser.readline()
        sys_print(line)    


# 6176MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)      


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700050028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000201820180000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000201820180000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)     


# 6200MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)         


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000381838180000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000381838180000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)    

# 6216MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)        


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000481848180000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000481848180000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)    

# 6240MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)         


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000601860180000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000601860180000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)     

# 6264MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)       


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700060028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000781878180000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000781878180000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)    


# 6325MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)        


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000B518B5180000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000B518B5180000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)     


# 6341MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)



 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)      


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000C518C5180000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000C518C5180000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)     

# 6365MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)


 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)       


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000DD18DD180000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000DD18DD180000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)    

# 6405MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)         


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd1601000000051905190000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd1601000000051905190000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

# stop vswr         
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)    

# 6413MHz

line = b''
ser.write((b'bt send cmd 0188FD00\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 0188FD00\n '))
        line = ser.readline()
        sys_print(line)

line = b''
ser.write((b'bt send cmd F9FF0100\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd F9FF0100\n '))
        line = ser.readline()
        sys_print(line)




 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100001120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)        


# set tx power         

line = b''
ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011AFD1200000100000A030013000600050000000016\n '))
        line = ser.readline()
        sys_print(line) 

# set band                    
line = b''
ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01B4FF0700070028002800\n '))
        line = ser.readline()
        sys_print(line) 

# set ch/freq        
line = b''
ser.write((b'bt send cmd 01cdfd16010000000D190D190000050553010a01ff010a000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 01cdfd16010000000D190D190000050553010a01ff010a000000\n '))
        line = ser.readline()
        sys_print(line)         

# get results         
line = b''
ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)   
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd0c000001000004030010000000\n '))
        line = ser.readline()
        sys_print(line)   

 # enable vswr 
line = b''
ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
line = ser.readline()
sys_print(line)
while 'bt:ok' not in line.decode():
    line = ser.readline()
    if not line:
        break
    sys_print(line)
    if 'bad params' in line.decode():
        ser.write((b'bt send cmd 011afd1c00000100001403000f00100000120000000000060000000000000000\n '))
        line = ser.readline()
        sys_print(line)      

pctl.DUTPowerOff(0)

timeEnd = timeStop()
testDone(timeBegin, timeEnd)