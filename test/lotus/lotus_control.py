import pyftdi
from pyftdi.ftdi import Ftdi
from pyftdi.i2c import I2cController
from pyftdi.spi import SpiController
import max31760
import lotus_gpio
import ina3221
import spi_flash
import time

def list_units():
    Ftdi.show_devices()
    
def setup_unit(FTDI_chA,familiar_name):
    
    ###########################################
    # Lotus P0 configuration (required after power-up)
    ###########################################

    # Address of Channel A (I2C + GPIO)
    #FTDI_chA = 'ftdi://ftdi:2232:P0_00003/1'
    # Address of Channel B (SPI + GPIO)
    FTDI_chB = FTDI_chA.replace('/1', '/2')

    # ChannelA: I2C + GPIO
    ###########################################
    # I2C Controller and devices
    i2c = I2cController()
    i2c.configure(FTDI_chA, frequency=100000,clockstretching=False)

    # MAX31760 - Fan controller configuration
    MAX31760_I2C_addr = 0x50
    max31760.init(i2c, MAX31760_I2C_addr)
    time.sleep(1)

    # INA3221 - Power monitor configuration
    INA3221_I2C_addr = 0x40
    ina3221.init(i2c, INA3221_I2C_addr)

    # Channel A GPIOs [ACBUS7 ... ADBUS0]
    chA_pins = 0xFFF0 # configure all pins except I2C
    chA_direction = 0x3FF0  # configure all pins as outputs except FTDI_SPARE0 and FTDI_SPARE1
    chA_gpio_out = 0x0000  # all outputs set to 0

    chA_gpio = i2c.get_gpio()
    chA_gpio.set_direction(chA_pins, chA_direction)
    chA_gpio.write(chA_gpio_out)

    # ChannelB: SPI + GPIO
    ###########################################
    # SPI Controller
    spi = SpiController()
    spi.configure(FTDI_chB)

    # Channel B GPIOs [BCBUS7 ... BDBUS0]
    chB_pins = 0xFFF0 # configure all pins except SPI
    chB_direction = 0x0F00  # configure all pins as inputs except RGB_LED[_R,_G,_B] and PA_PWR_DIS
    chB_gpio_out = 0x0300  # Blue LED ON = low, others OFF; PA ON = PA_PWR_DIS low 

    chB_gpio = spi.get_gpio()
    chB_gpio.set_direction(chB_pins, chB_direction)
    chB_gpio.write(chB_gpio_out)

    # Reset DSAs to minimum reflection
    lotus_gpio.set_DSA(chA_gpio,[63,63,63,63])   


    # Set fan at fixed higher speed 
    # MAX31760 Set PWM (%) manually; overrides LUT configuration
    #max31760.set_PWM_override(i2c, MAX31760_I2C_addr,70)
    
    print('Lotus setup complete:',FTDI_chA,' + ',FTDI_chB,'ready for use as: ',familiar_name)
    
    return [i2c, spi, chB_gpio_out, str(familiar_name)]


def dump_sensors(lotus_address):
    
    i2c = lotus_address[0]
    spi = lotus_address[1]
    
    MAX31760_I2C_addr = 0x50

    INA3221_I2C_addr = 0x40
    
    # I2C Controller and devices
    #i2c = I2cController()
    #i2c.configure(FTDI_chA, frequency=100000,clockstretching=False)
    
    # SPI Controller
    #spi = SpiController()
    #spi.configure(FTDI_chB)
    
    #chB_pins = 0xFFF0 # configure all pins except SPI
    #chB_direction = 0x0F00  # configure all pins as inputs except RGB_LED[_R,_G,_B] and PA_PWR_DIS
    #chB_gpio_out = 0x0300  # Blue LED ON = low, others OFF; PA ON = PA_PWR_DIS low
    
    chB_gpio = spi.get_gpio()
    #chB_gpio.set_direction(chB_pins, chB_direction)
    #chB_gpio.write(chB_gpio_out)
    
    
    # MAX31760 Read PWM (%)
    fan_PWM = max31760.get_PWM(i2c, MAX31760_I2C_addr)
    print("Fan PWM duty-cycle (%): ",fan_PWM)

    # MAX31760 Read FAN speed (RPM)
    fan_RPM = max31760.get_RPM(i2c, MAX31760_I2C_addr)
    print("Fan speed (RPM):        ", fan_RPM)

    # MAX31760 Read REMOTE temperature (degC)
    remote_temp = max31760.get_remote_temp(i2c, MAX31760_I2C_addr)
    print("Temperature remote - PA (degC):      ",remote_temp)

    # MAX31760 Read LOCAL temperature (degC)
    local_temp = max31760.get_local_temp(i2c, MAX31760_I2C_addr)
    print("Temperature local - MAX31760 (degC): ",local_temp)
    print("\n")
    
    # INA3221 Read channel [1,2,3], configure shunt resistor (0.25 or 0.1 Ohm)
    print("PA LDO:")
    voltage, current = ina3221.read_ch(i2c, INA3221_I2C_addr, 1, 0.25)
    print(voltage,"V", current, "A\n")

    print("LNA 6V DC-DC:")
    voltage, current = ina3221.read_ch(i2c, INA3221_I2C_addr, 2, 0.1)
    print(voltage,"V",current, "A\n")

    print("5V DC-DC:")
    voltage, current = ina3221.read_ch(i2c, INA3221_I2C_addr, 3, 0.1)
    print(voltage,"V",current, "A\n")
    
    print("GPIO:")
    # Get REV_ID (dec)
    rev_ID = lotus_gpio.get_REV_ID(chB_gpio)
    print(rev_ID, "rev_ID")

    # Get TMP_ALERT status
    temp_alert = lotus_gpio.get_TMP_ALERT(chB_gpio)
    print(temp_alert, "pin TMP_ALERT")

    # Get INA_WARNING status (INA3221 limits not configured yet)
    INA_WARNING = lotus_gpio.get_INA_WARNING(chB_gpio)
    print(INA_WARNING, "pin INA_WARNING")

    # Get INA_CRITICAL status (INA3221 limits not configured yet)
    INA_CRITICAL = lotus_gpio.get_INA_CRITICAL(chB_gpio)
    print(INA_CRITICAL, "pin INA_CRITICAL")

    # Get INA_PV status (INA3221 limits not configured yet)
    INA_PV = lotus_gpio.get_INA_PV(chB_gpio)
    print(INA_PV, "pin INA_PV")


def set_DSAs(lotus_address,DSA1, DSA2, DSA3, DSA4):
    
    i2c = lotus_address[0]
    #i2c.configure(FTDI_chA, frequency=100000,clockstretching=False)
    
    # Channel A GPIOs [ACBUS7 ... ADBUS0]
    chA_pins = 0xFFF0 # configure all pins except I2C
    chA_direction = 0x3FF0  # configure all pins as outputs except FTDI_SPARE0 and FTDI_SPARE1
    chA_gpio_out = 0x0000  # all outputs set to 0

    chA_gpio = i2c.get_gpio()
    chA_gpio.set_direction(chA_pins, chA_direction)
    chA_gpio.write(chA_gpio_out)

    lotus_gpio.set_DSA(chA_gpio,[DSA1,DSA2,DSA3,DSA4])   
    
    
def get_remote_temp(lotus_address):
    i2c = lotus_address[0]
    MAX31760_I2C_addr = 0x50
    remote_temp = max31760.get_remote_temp(i2c, MAX31760_I2C_addr)
    return remote_temp
    
def get_local_temp(lotus_address):
    i2c = lotus_address[0]
    MAX31760_I2C_addr = 0x50
    local_temp = max31760.get_local_temp(i2c, MAX31760_I2C_addr)
    return local_temp

def set_PWM_override(lotus_address,pwm):
    i2c = lotus_address[0]
    MAX31760_I2C_addr = 0x50
    max31760.set_PWM_override(i2c, MAX31760_I2C_addr,pwm)

def set_LED_colour(lotus_address,chB_gpio_out,color):
    spi = lotus_address[1]
    chB_gpio = spi.get_gpio()

    if color == 'red':
                red   = 1
                green = 0
                blue  = 0
    elif color == 'green':
                red   = 0
                green = 1
                blue  = 0    
    elif color == 'blue':
                red   = 0
                green = 0
                blue  = 1
    elif color == 'magenta':
                red   = 1
                green = 0
                blue  = 1
    elif color == 'cyan':
                red   = 0
                green = 1
                blue  = 1
    elif color == 'yellow':
                red   = 1
                green = 1
                blue  = 0
    else:
                red   = 0
                green = 0
                blue  = 0
    
    chB_gpio_out = lotus_gpio.set_RGB_LED(chB_gpio,chB_gpio_out,red,green,blue)
    
    return chB_gpio_out