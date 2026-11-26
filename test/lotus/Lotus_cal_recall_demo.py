import lotus_control as ctrl # HW control of Lotus P0
import lotus_functions as lotus # Control,calculation and visualisation tools for Lotus
import datetime
import time
import zva           # Setup for R&S ZVA67 VNA
import os

#########################################
# Find connected Lotus (FTDI) devices 
#########################################
# Copy addresses (serial numbers) of connected Lotuses as input parameters to the configuration function below
ctrl.list_units()

#########################################
# Setup - programming/configuration of all Lotus peripherals (run once after Lotus unit is connected)
#########################################
# Note: Example of how multiple devices connected to the same host can be addressed is below
serial_num = 'P0_00026'
lotus_address = ctrl.setup_unit('ftdi://ftdi:2232:P0_00026/1',serial_num)

#########################################
# Initialise VNA - CH1, continuous sweep, polar plot display
#########################################
freq = 3.5
rm, ZVA67 = zva.zva_connect("TCPIP0::192.168.100.251::inst0::INSTR")
# zva.preset(ZVA67)
zva.zva_cw_sweep(ZVA67, freq, 1, 1, 0, 10) # added power: 0 dBm and average of 10 sweeps
zva.zva_create_trace(ZVA67, '\'T1\'', 2, '\'S11\'', 'POL', 1)
# zva.zva_delete_default_trace(ZVA67)

#########################################
# EXAMPLE - Recall calibrated load demo
#########################################
now = datetime.date.today()
cal_file = serial_num + " " + str(now)

freq_list = [2.3, 5.5, 5.9, 7.0] #frequencies in GHz
mag_list = [0.2, 0.4, 0.6, 0.8, 1.0] #magnitude
ang_list = [-135, -90, -45, 0, 45, 90, 135, 180] #angle in degrees

for freq in freq_list:
    zva.zva_cw_sweep(ZVA67, freq, 1, 1, 0, 10) # new line added in, forgot to set VNA in previous code
    target_mag = 0 #start with center of smith chart
    target_ang = 0 #start with center of smith chart
    lotus.recall_cal_load(lotus_address, freq, target_mag, target_ang, cal_file)
    time.sleep(0.1)
    for target_ang in ang_list:
        for target_mag in mag_list:
            lotus.recall_cal_load(lotus_address, freq, target_mag, target_ang, cal_file)
            time.sleep(0.1)

