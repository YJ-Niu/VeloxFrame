import rsnumpy as np
import lotus_control as ctrl
import zva
import os
import rspandas as pd


def cdot(a, b):  # dot product of vectors
    return (a.real * b.real + a.imag * b.imag)


def generate_cal_load(lotus_address, frequency, target_mag, target_angle, VNA_instrument):
    import math
    MAX_ITERATIONS = 100  # 新增：防止无限循环的最大迭代次数
    # convert target to complex format
    T0_complex = target_mag * math.cos((math.pi / 180) * target_angle) + target_mag * math.sin(
        (math.pi / 180) * target_angle) * 1j

    DSA = [63, 63, 63, 63]  # initialize DSA settings
    dotProduct = [0, 0, 0, 0]  # initialize dot products
    BaseVector = [0, 0, 0, 0]  # initialize base vectors

    # measure base vectors IP, IN, QP, QN and Z0
    ctrl.set_DSAs(lotus_address, 0, DSA[1], DSA[2], DSA[3])  # IP measurement
    mkr_mag, mkr_phase, IP_complex = zva.zva_read_polar_marker(VNA_instrument, 1, '\'T1\'')
    ctrl.set_DSAs(lotus_address, DSA[0], 0, DSA[2], DSA[3])  # IN measurement
    mkr_mag, mkr_phase, IN_complex = zva.zva_read_polar_marker(VNA_instrument, 1, '\'T1\'')
    ctrl.set_DSAs(lotus_address, DSA[0], DSA[1], 0, DSA[3])  # QP measurement
    mkr_mag, mkr_phase, QP_complex = zva.zva_read_polar_marker(VNA_instrument, 1, '\'T1\'')
    ctrl.set_DSAs(lotus_address, DSA[0], DSA[1], DSA[2], 0)  # QN measurement
    mkr_mag, mkr_phase, QN_complex = zva.zva_read_polar_marker(VNA_instrument, 1, '\'T1\'')
    ctrl.set_DSAs(lotus_address, DSA[0], DSA[1], DSA[2], DSA[3])  # Z0 measurement
    mkr_mag, mkr_phase, Z0_complex = zva.zva_read_polar_marker(VNA_instrument, 1, '\'T1\'')

    # reference base vectors from Z0
    BaseVector[0] = IP_complex - Z0_complex
    BaseVector[1] = IN_complex - Z0_complex
    BaseVector[2] = QP_complex - Z0_complex
    BaseVector[3] = QN_complex - Z0_complex

    # calculate dot products to see what base vector we need the most
    for x in range(0, 4):
        dotProduct[x] = cdot(BaseVector[x], T0_complex - Z0_complex)
    # First Loop uses the attenuator that has most impact (highest dot product) to get close to target
    T1_complex = Z0_complex  # starting search at Z0
    iteration_count = 0
    # 修正循环条件：加入迭代次数保护，并确保在距离不再减小时退出
    break_mark = 0
    while True:
        if break_mark == 1:
            break
        iteration_count += 1
        prev_distance = abs(T0_complex - T1_complex)
        for x in range(0, 4):
            if (dotProduct[x] == max(dotProduct)):  # use the base vector that is strongest contributor
                # 修改内部while循环，加入DSA下限和变化检测
                while (dotProduct[x] == max(dotProduct) and DSA[x] > 1 and iteration_count < MAX_ITERATIONS):
                    DSA_prev = DSA[x]
                    if DSA_prev >= 45:
                        ss = 5
                    elif 30 < DSA_prev < 45:
                        ss = 3
                    elif 20 < DSA_prev < 30:
                        ss = 2
                    else:
                        ss = 1
                    DSA[x] = DSA[x] - ss  # reduce attenuation to home in on target vector
                    ctrl.set_DSAs(lotus_address, DSA[0], DSA[1], DSA[2], DSA[3])  # new DSA setting
                    mkr_mag, mkr_phase, T1_complex = zva.zva_read_polar_marker(VNA_instrument, 1, '\'T1\'')  # read VNA
                    dotProduct[x] = cdot(T0_complex - T1_complex, BaseVector[x])  # recalculate dot product
                    iteration_count += 1
                    # 如果DSA调整没有改变状态，强制退出内层while循环
                    # print("--------------------- x:", x)
                    # print("DSA\t", DSA)
                    
                    # print("Target mag\t", target_mag, "\tTarget angle\t", target_angle, "\t", ss)
                    # print("Test mag\t", round(mkr_mag, 3), "\tTest phase\t", round(mkr_phase, 2), "\tTest mag\t", mkr_mag, "\tTest phase\t", mkr_phase)
                    # print("---------------------")
                    # if DSA[x] == DSA_prev:
                    #     break
                    if (abs(round(mkr_mag, 3) - target_mag) < max(target_mag * 0.02, 0.005)) and (abs(round(mkr_phase, 3) - target_angle) < 50):
                        # print(333, round(mkr_mag, 3), target_mag, (round(mkr_mag, 3) - target_mag), mkr_phase, round(mkr_phase, 3) - target_angle, DSA)
                        break_mark = 1
                        break

        # 重新计算所有点的点积，为下一次外循环准备
        for x in range(0, 4):
            dotProduct[x] = cdot(BaseVector[x], T0_complex - T1_complex)
        # 如果距离没有改善，提前退出
        current_distance = abs(T0_complex - T1_complex)
        if current_distance >= prev_distance:
            break

    if iteration_count >= MAX_ITERATIONS:
        print(
            f"  Warning: First loop reached max iterations ({MAX_ITERATIONS}) for target ({target_mag}, {target_angle}).")

    # find 2 biggest contributors (they have lowest DSA settings) and make sure they overshot
    min2 = 0
    min1 = 0
    for x in range(0, 4):
        if (DSA[x] < DSA[min1]):
            min2 = min1
            min1 = x
        elif (DSA[x] < DSA[min2]):
            min2 = x
    if (DSA[min1] > 0):
        DSA[min1] = DSA[min1] - 1  # decrement biggest contributor one more time to make sure it overshot
    if (DSA[min2] > 0):
        DSA[min2] = DSA[min2] - 1  # decrement 2nd biggest contributor one more time to make sure it overshot

    ctrl.set_DSAs(lotus_address, DSA[0], DSA[1], DSA[2], DSA[3])  # new DSA setting
    mkr_value_mag, mkr_value_phase, T1_complex = zva.zva_read_polar_marker(VNA_instrument, 1, '\'T1\'')  # read VNA
    EVM = abs(T0_complex - T1_complex)  # calculate EVM

    break_mark = 0
    # 2nd Loop decrements any DSAs that help reduce EVM
    for iter in range(2):  # run 2 iterations of this, may not be necessary
        if break_mark == 1:
            break
        delta = [0, 0, 0, 0]  # this stores the size of DSA decrement
        EVM_improve = [1, 1, 1, 1]  # this stores whether or not decrementing [DSA1,2,3,4] helped
        for x in range(0, 4):
            # 为内层while循环添加保护，防止无限循环
            if break_mark == 1:
                break
            inner_iter = 0
            MAX_INNER_ITER = 20
            while (EVM_improve[x] != 0 and DSA[x] > 1 and inner_iter < MAX_INNER_ITER):
                inner_iter += 1
                # 修正delta计算，防止除零错误
                if DSA[1] > 0:
                    delta[0] = max(1, math.ceil(DSA[0] / DSA[1] / 2.5))
                else:
                    delta[0] = 1
                if DSA[0] > 0:
                    delta[1] = max(1, math.ceil(DSA[1] / DSA[0] / 2.5))
                else:
                    delta[1] = 1
                if DSA[3] > 0:
                    delta[2] = max(1, math.ceil(DSA[2] / DSA[3] / 2.5))
                else:
                    delta[2] = 1
                if DSA[2] > 0:
                    delta[3] = max(1, math.ceil(DSA[3] / DSA[2] / 2.5))
                else:
                    delta[3] = 1

                DSA_prev = DSA[x]
                DSA[x] = max(1, DSA[x] - delta[x])  # 确保DSA不小于1
                ctrl.set_DSAs(lotus_address, DSA[0], DSA[1], DSA[2], DSA[3])  # new DSA setting
                mkr_mag, mkr_phase, T1_complex = zva.zva_read_polar_marker(VNA_instrument, 1, '\'T1\'')  # read VNA
                # print(111, mkr_mag, mkr_phase, round(mkr_mag, 3), round(mkr_phase, 3))
                if (abs(round(mkr_mag, 3) - target_mag) < max(target_mag * 0.02, 0.005)) and (abs(round(mkr_phase, 3) - target_angle) < 50):
                    # print(44444, mkr_phase, round(mkr_phase, 3) - target_angle)
                    break_mark = 1
                    break

                EVMx = abs(T0_complex - T1_complex)
                if (EVMx < EVM):
                    EVM = EVMx  # improved so keep new EVM
                    EVM_improve[x] = 1
                else:
                    DSA[x] = DSA_prev  # degraded so go back
                    ctrl.set_DSAs(lotus_address, DSA[0], DSA[1], DSA[2], DSA[3])  # restore DSA setting
                    EVM_improve[x] = 0  # degraded so set flag
                # print(f"Iteration {iter}: DSA settings: {DSA}, EVM: {EVM}, EVMxL: {EVMx}, EVM_improve: {EVM_improve}")
    print(DSA)
    ctrl.set_DSAs(lotus_address, DSA[0], DSA[1], DSA[2], DSA[3])  # set DSA to final value
    mkr_mag, mkr_phase, T1_complex = zva.zva_read_polar_marker(VNA_instrument, 1,
                                                               '\'T1\'')  # read VNA again for final value
    temp = ctrl.get_remote_temp(lotus_address)

    # 修复：安全地计算EVM的对数值
    try:
        if EVM <= 0:
            evm_db = -100.0  # 当EVM为0或负数时，设置为-100dB
        else:
            evm_db = round(20 * math.log10(EVM), 2)
    except (ValueError, ZeroDivisionError):
        evm_db = -100.0
    return round(temp, 3), round(mkr_mag, 4), round(mkr_phase, 2), evm_db, DSA


def store_cal_load(freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, DSA, cal_file):
    if os.path.exists(cal_file):
        # print('Cal file found!')
        new_entry = np.array(
            [[freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, str(DSA[0]), str(DSA[1]), str(DSA[2]),
              str(DSA[3])]])
        new_entry_df = pd.DataFrame(new_entry)
        new_entry_df.to_csv(cal_file, header=False, mode='a', index=False)
    else:
        new_entry = np.array(
            [['Freq(GHz)', 'Temp', 'TargetMag', 'TargetAng', 'MeasMag', 'MeasAng', 'EVM', 'DSA1', 'DSA2', 'DSA3',
              'DSA4']])
        new_entry_df = pd.DataFrame(new_entry)
        new_entry_df.to_csv(cal_file, header=False, mode='a', index=False)
        new_entry = np.array(
            [[freq, temp, target_mag, target_ang, mkr_mag, mkr_phase, EVM, str(DSA[0]), str(DSA[1]), str(DSA[2]),
              str(DSA[3])]])
        new_entry_df = pd.DataFrame(new_entry)
        new_entry_df.to_csv(cal_file, header=False, mode='a', index=False)
    return


def recall_cal_load(lotus_address, freq, target_mag, target_ang, cal_file):
    cal_table_df = pd.read_csv(cal_file)
    print(cal_table_df)

    idx = cal_table_df.index[(cal_table_df['Freq(GHz)'] == freq) & (cal_table_df['TargetMag'] == target_mag) & (cal_table_df['TargetAng'] == target_ang)]

    if idx.size > 0:
        message = 'Calibrated load: Magnitude: ' + str(target_mag) + ' Angle: ' + str(
            target_ang) + ' found and recalled!'
        DSA1 = cal_table_df.at[idx[0], 'DSA1']
        DSA2 = cal_table_df.at[idx[0], 'DSA2']
        DSA3 = cal_table_df.at[idx[0], 'DSA3']
        DSA4 = cal_table_df.at[idx[0], 'DSA4']
        ctrl.set_DSAs(lotus_address, DSA1, DSA2, DSA3, DSA4)
    else:
        message = 'Calibrated load NOT found!'

    return message


def show_cal_loads(cal_file):
    cal_table_df = pd.read_csv(cal_file)

    return cal_table_df
