import pyvisa
from rsnumpy import exp, pi

# R&S ZVA Control functions - copied from Travis
def preset(inst):
    inst.write('*RST')
    
    
def zva_close(rm):
    rm.close()
    
    
def zva_connect(inst_address):
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(inst_address)
    print(inst.query("*IDN?"))
    inst.timeout = 30
    return rm, inst
 
    
def zva_cw_sweep(inst, freq, ch, pts, pwr, avg):
    inst.write(f'SENS{ch}:SWE:TYPE POIN')
    inst.write(f'SOUR{ch}:FREQ:CW {freq} GHz')
    inst.write(f'SENS{ch}:SWE:POIN {pts}')
    inst.write(f'SOUR{ch}:POW {pwr}')
    
    inst.write(f'SENS{ch}:SWE:COUNT {avg}')
    inst.write(f'SENS{ch}:AVER:COUN {avg}')
    inst.write(f'SENS{ch}:AVER:ON')
    
def zva_create_trace(inst, trace_name, trace_num, parameter, par_format, ch):
    inst.write(f'CALC{ch}:PAR:SDEF ' + trace_name + ', ' + parameter)
    inst.write(f'DISP:WIND1:TRAC{trace_num}:FEED ' + trace_name)
    inst.write(f'CALC{ch}:FORM ' + par_format)
    inst.write(f'CALC{ch}:MARK1 ON')


def zva_delete_default_trace(inst):
    inst.write('CALC1:PAR:DEL ''Trc1')


def zva_read_polar_marker(inst, ch, trace):
    inst.write('INIT1:CONT OFF')
    inst.write('INIT1')
    inst.write('*OPC?')
        
    inst.write(f'CALC{ch}:PAR:SEL ' + trace)
    mkr_value_polar = inst.query(f"CALC{ch}:MARK:Y?")
    # print(mkr_value_polar)
    x = mkr_value_polar.split(",")
    mkr_value_mag = float(x[0])
    mkr_value_phase = float(x[1])
    mkr_complex = mkr_value_mag * exp(1j * (mkr_value_phase*(pi/180)))
    
    inst.write('INIT1:CONT ON')
    return mkr_value_mag, mkr_value_phase, mkr_complex
