import lotus_control as ctrl  # HW control of Lotus P0
import lotus_functions as lotus  # tools for Lotus
import zva  # Setup for R&S ZVA67 VNA
import datetime
import os
import time  # 新增，用于可能的调试或延时
import serial.tools.list_ports

start_time = time.time()
# 查找符合条件的串口设备
def find_lotus_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.pid == 0x6010 and port.vid == 0x0403:
            return port.device
    return None
    

# 使用pyserial读取PID=0x6010、 VID=0x0403的串口

serial_num = find_lotus_port().split("-")[1][:-1] if find_lotus_port() else None

#########################################
# Find connected Lotus (FTDI) devices
#########################################
# Copy addresses (serial numbers) of connected Lotuses as input parameters to the configuration function below
# ctrl.list_units()
print("Lotus devices connected:", serial_num)
#########################################
# Setup - programming/configuration of all Lotus peripherals (run once after Lotus unit is connected)
#########################################
# Note: Example of how multiple devices connected to the same host can be addressed is below
lotus_address = ctrl.setup_unit(f'ftdi://ftdi:2232:{serial_num}/1', serial_num)

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
cal_file = serial_num + " " + str(now)
if os.path.exists(cal_file):
    os.remove(cal_file)  # delete old cal file


# freq_list = [2.350, 2.375, 2.441, 2.505, 2.530, 2.402, 2.420, 2.440, 2.460, 2.480, 5.150, 5.175, 5.200, 5.225, 5.250,
#             5.725, 5.755, 5.785, 5.820, 5.850, 5.945, 5.965, 5.985,
#             6.010, 6.030, 6.055, 6.080, 6.110, 6.135, 6.160, 6.190, 6.215, 6.240, 6.265, 6.295, 6.320, 6.345, 6.370,
#             6.400, 6.425]  # frequencies in GHz

freq_list = [2.350, 2.375, 2.402, 2.420, 2.440, 2.460, 2.480, 2.505, 2.530, 5.000, 5.050, 5.100, 5.150, 5.175, 5.200, 5.225, 5.250, 5.300, 5.350, 5.400, 5.725, 5.755, 5.785, 5.820, 5.850, 5.945, 5.985, 6.025, 6.075, 6.135, 6.190, 6.240, 6.295, 6.345, 6.385, 6.425]

mag_list = [0, 0.05, 0.1, 0.33, 0.5, 0.636]  # magnitude
ang_list = [0, 45, 90, 135, 180, 225, 270, 315]  # angle in degrees

for freq in freq_list:
    print(f"\n--- Starting calibration for frequency: {freq} GHz ---")
    zva.zva_cw_sweep(ZVA67, freq, 1, 1, 0, 10)  # 为每个新频率设置VNA
    target_mag = 0  # start with center of smith chart
    target_ang = 0  # start with center of smith chart
    print("  Generating center point (0, 0)...")
    # temp, mkr_mag, mkr_phase, EVM, DSA = lotus.generate_cal_load(lotus_address, freq, target_mag, target_ang, ZVA67)
    # lotus.store_cal_load(freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, DSA, cal_file)
    # print(freq, "GHz,", temp, "C,", target_mag, "mag,", target_ang, "ang,", EVM, "EVM,", DSA)

    for target_ang in ang_list:
        for target_mag in mag_list:
            input("Press any key to continue...")
            print(f"    Generating point: Mag={target_mag}, Ang={target_ang}...")
            temp, mkr_mag, mkr_phase, EVM, DSA = lotus.generate_cal_load(lotus_address, freq, target_mag, target_ang,
                                                                         ZVA67)
            print(freq, "GHz,", temp, "C,", target_mag, "mag,", target_ang, "ang,", EVM, "EVM,", DSA)
            lotus.store_cal_load(freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, DSA, cal_file)
print("Calibration complete. Cal_file:", cal_file)

end_time = time.time()
print(f"Calibration time: {end_time - start_time:.2f} seconds")
