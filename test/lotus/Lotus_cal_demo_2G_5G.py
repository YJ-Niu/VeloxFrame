import lotus_control as ctrl  # HW control of Lotus P0
import lotus_functions as lotus  # tools for Lotus
import zva  # Setup for R&S ZVA67 VNA
import datetime
import os
import time  # 新增，用于可能的调试或延时
import serial
import serial.tools.list_ports


def find_ftdi_serial_port(vendor_id=0x0403, product_id=0x6010):
    matched_ports = []
    for port in serial.tools.list_ports.comports():
        if getattr(port, "vid", None) == vendor_id and getattr(port, "pid", None) == product_id:
            matched_ports.append(port)
    return matched_ports


start_time = time.time()
#########################################
# Find connected Lotus (FTDI) devices
#########################################
# Copy addresses (serial numbers) of connected Lotuses as input parameters to the configuration function below
ftdi_ports = find_ftdi_serial_port()
lotus2_sn = []
if ftdi_ports:
    print("Detected Lotus serial ports matching VID 0x0403 / PID 0x6010:")
    for port in ftdi_ports:
        if port.device.endswith("0"):
            lotus2_sn.append(getattr(port, 'serial_number', 'N/A'))
            print(f"  - {port.device} | VID: 0x{port.vid:04x} PID: 0x{port.pid:04x} SN: {getattr(port, 'serial_number', 'N/A')}")
else:
    print("No FTDI serial port matched VID 0x0403 / PID 0x6010.")

# ctrl.list_units()

if len(lotus2_sn) != 2:
    print("需要连接2个lotus2")
    import sys
    sys.exit(0)
if lotus2_sn[0] < lotus2_sn[1]:
    serial_num_2g, serial_num_5g = lotus2_sn
else:
    serial_num_5g, serial_num_2g = lotus2_sn
#########################################
# Setup - programming/configuration of all Lotus peripherals (run once after Lotus unit is connected)
#########################################
# Note: Example of how multiple devices connected to the same host can be addressed is below

# serial_num = 'P0_00056'
# lotus_address = ctrl.setup_unit('ftdi://ftdi:2232:P0_00056/1', serial_num)
lotus_address_2g = ctrl.setup_unit(f'ftdi://ftdi:2232:{serial_num_2g}/1', serial_num_2g)
lotus_address_5g = ctrl.setup_unit(f'ftdi://ftdi:2232:{serial_num_5g}/1', serial_num_5g)


#########################################
# Initialise VNA - CH1, continuous sweep, polar plot display
#########################################
# 初始化频率，但主循环会覆盖此值
init_freq = 3.5

rm, ZVA67 = zva.zva_connect("TCPIP0::192.168.100.251::inst0::INSTR")
# zva.preset(ZVA67)
zva.zva_cw_sweep(ZVA67, init_freq, 1, 1, 0, 10)  # added power: 0 dBm and average of 10 sweeps
zva.zva_create_trace(ZVA67, '\'T1\'', 2, '\'S11\'', 'POL', 1)
# zva.zva_delete_default_trace(ZVA67)

#########################################
# EXAMPLE - Create calibrated calibrated loads and store to cal file
#########################################
now = datetime.date.today()
cal_file = "PathLoss_" + serial_num_2g + "_" + str(now)
file = 0
while 1:
    if os.path.exists(cal_file):
        # os.remove(cal_file)  # delete old cal file
        file += 1
        cal_file = "PathLoss_" + serial_num_2g + "_" + str(now) + "_" + str(file)
    else:
        break

#freq_list = [2.350, 2.375, 2.441, 2.505, 2.530, 2.402, 2.420, 2.440, 2.460, 2.480, 5.150, 5.175, 5.200, 5.225, 5.250,
#             5.725, 5.755, 5.785, 5.820, 5.850, 5.945, 5.965, 5.985,
#             6.010, 6.030, 6.055, 6.080, 6.110, 6.135, 6.160, 6.190, 6.215, 6.240, 6.265, 6.295, 6.320, 6.345, 6.370,
#             6.400, 6.425]  # frequencies in GHz

freq_list = [2.350, 2.375, 2.402, 2.420, 2.440, 2.460, 2.480, 2.505, 2.530, 5.000, 5.050, 5.100, 5.150, 5.175, 5.200, 5.225, 5.250, 5.300, 5.350, 5.400, 5.725, 5.755, 5.785, 5.820, 5.850, 5.945, 5.985, 6.025, 6.075, 6.135, 6.190, 6.240, 6.295, 6.345, 6.385, 6.425]

mag_list = [0.05, 0.1, 0.33, 0.5, 0.636]  # magnitude
ang_list = [0, 45, 90, 135, 180, 225, 270, 315]  # angle in degrees

for freq in freq_list:
    if freq < 5:
        lotus_address = lotus_address_2g
    else:
        lotus_address = lotus_address_5g
    print(f"\n--- Starting calibration for frequency: {freq} GHz ---")
    zva.zva_cw_sweep(ZVA67, freq, 1, 1, 0, 10)  # 为每个新频率设置VNA
    target_mag = 0  # start with center of smith chart
    target_ang = 0  # start with center of smith chart
    print(f"  Generating center point (0, 0)...")
    temp, mkr_mag, mkr_phase, EVM, DSA = lotus.generate_cal_load(lotus_address, freq, target_mag, target_ang, ZVA67)
    lotus.store_cal_load(freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, DSA, cal_file)
    print(freq, "GHz,", temp, "C,", target_mag, "mag,", target_ang, "ang,", EVM, "EVM,", DSA)

    for target_ang in ang_list:
        for target_mag in mag_list:
            print(f"    Generating point: Mag={target_mag}, Ang={target_ang}...")
            temp, mkr_mag, mkr_phase, EVM, DSA = lotus.generate_cal_load(lotus_address, freq, target_mag, target_ang,
                                                                         ZVA67)
            print(freq, "GHz,", temp, "C,", target_mag, "mag,", target_ang, "ang,", EVM, "EVM,", DSA)
            lotus.store_cal_load(freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, DSA, cal_file)
print("Calibration complete. Cal_file:", cal_file)
end_time = time.time()
print("APL TT: ", end_time - start_time)