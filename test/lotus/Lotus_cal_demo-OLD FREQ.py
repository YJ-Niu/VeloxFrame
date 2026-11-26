import lotus_control as ctrl # HW control of Lotus P0
import lotus_functions as lotus     # tools for Lotus
import zva           # Setup for R&S ZVA67 VNA
import datetime
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
serial_num = 'P0_00031'
lotus_address = ctrl.setup_unit('ftdi://ftdi:2232:P0_00031/1',serial_num)

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
# EXAMPLE - Create calibrated calibrated loads and store to cal file
#########################################
now = datetime.date.today()
cal_file = serial_num + " " + str(now)
if os.path.exists(cal_file):
    os.remove(cal_file) #delete old cal file

freq_list = [2402, 2440, 2460, 2480, 5150, 5175, 5200, 5228, 5250, 5725, 5755, 5795, 5823, 5945, 5975, 5987,6015, 6029, 6051, 6075, 6115, 6131, 6176, 6200, 6216, 6240, 6264, 6325, 6341, 6365, 6405, 6413] #frequencies in GHz
mag_list = [0.1, 0.5, 0.5, 0.5, .636, 0.636, 0.1, 0.33, 0.5, 0.6, 0.636] #magnitude
ang_list = [ 270, 45, 270, 315, 180, 225, 90, 135, 270, 270, 315] #angle in degrees

for freq in freq_list:
    zva.zva_cw_sweep(ZVA67, freq, 1, 1, 0, 10) # new line added in, forgot to set VNA in previous code
    target_mag = 0 #start with center of smith chart
    target_ang = 0 #start with center of smith chart
    temp, mkr_mag, mkr_phase, EVM, DSA = lotus.generate_cal_load(lotus_address, freq, target_mag, target_ang, ZVA67)
    lotus.store_cal_load(freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, DSA, cal_file)
    print(freq,"GHz,",temp,"C,",target_mag,"mag,",target_ang,"ang,",EVM,"EVM,",DSA)
    for target_ang in ang_list:
        for target_mag in mag_list:
            temp, mkr_mag, mkr_phase, EVM, DSA = lotus.generate_cal_load(lotus_address, freq, target_mag, target_ang, ZVA67)
            print(freq,"GHz,",temp,"C,",target_mag,"mag,",target_ang,"ang,",EVM,"EVM,",DSA)
            lotus.store_cal_load(freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, DSA, cal_file)
print("cal_file:", cal_file)