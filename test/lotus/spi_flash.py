import pyftdi
from pyftdi.ftdi import Ftdi
from pyftdi.spi import SpiController


def get_Jedec_ID(spi):
    
    SPI_Flash = spi.get_port(cs=0, freq=10e6, mode=0)
    byte_val = SPI_Flash.exchange([0x9f], 3)
    hex_val = hex(int.from_bytes(byte_val, 'big'))
    
    return hex_val