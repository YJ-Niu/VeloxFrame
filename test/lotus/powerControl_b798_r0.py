import os
import sys
import serial
import time

class powerControl():
        def __init__(self, PortName, BaudRate=921600, TimeOut=3):
                super(powerControl, self).__init__()
                try:
                    self.port = serial.Serial(PortName, baudrate=BaudRate,timeout=TimeOut)
                    self.port.flush()
                except:
                    raise RuntimeError("Open serial port error: %s", PortName)


        ######### DUT power off ##############
        def DUTPowerOff(self, slotID):
                if self.port.isOpen():
                    cmd = f'CONFIG:SLOT{slotID}:UART:STATUS OFF\r\n'.encode()
                    self.port.write(cmd)
                    time.sleep(0.2)
                    cmd = f'CONFIG:SLOT{slotID}:USB:STATUS OFF\r\n'.encode()
                    self.port.write(cmd)
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:DIO:PORT0:LEVEL OUT,L \r\n '.format(slotID).encode())
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:DIO:PORT1:LEVEL OUT,L \r\n'.format(slotID).encode())
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:DIO:PORT2:LEVEL OUT,L \r\n'.format(slotID).encode())
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:DIO:PORT3:LEVEL OUT,L \r\n'.format(slotID).encode())
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:DIO:PORT4:LEVEL OUT,L \r\n'.format(slotID).encode())
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:DIO:PORT5:LEVEL OUT,L \r\n'.format(slotID).encode())
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:DIO:PORT6:LEVEL OUT,L\r\n'.format(slotID).encode())
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:DIO:PORT7:LEVEL OUT,L\r\n'.format(slotID).encode())
                    time.sleep(0.2)
                    self.port.write('CONFIG:SLOT{}:VCC:STATUS OFF\r\n'.format(slotID).encode())
                    print(self.port.read_all())
                else:
                    raise ValueError('fixture serial port not opened!')

        ######### DUT power ON ##############
        def DUTPowerON(self, slotID):
                '''
                Description: set up DUT power off, after test
                '''
                pwr_ow_sequences = [f'CONFIG:SLOT{slotID}:VCC:STATUS OFF \r\n',
                                    f'CONFIG:SLOT{slotID}:VCC:STATUS OFF \r\n',
                                    f'CONFIG:SLOT{slotID}:UART:STATUS OFF \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT0:LEVEL OUT,L \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT1:LEVEL OUT,L \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT2:LEVEL OUT,L \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT3:LEVEL OUT,L \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT4:LEVEL OUT,L \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT5:LEVEL OUT,L \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT6:LEVEL OUT,L \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT7:LEVEL OUT,L \r\n',
                                    f'CONFIG:SLOT{slotID}:VCC:VOLT 4.100000V \r\n',
                                    f'CONFIG:SLOT{slotID}:RAIL:VOLT 3.300000V \r\n',
                                    f'CONFIG:SLOT{slotID}:VCC:STATUS ON \r\n',
                                    f'CONFIG:SLOT{slotID}:UART:STATUS ON \r\n',
                                    f'CONFIG:SLOT{slotID}:USB:STATUS ON \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT1:LEVEL OUT,H \r\n',
                                    f'CONFIG:SLOT{slotID}:DIO:PORT3:LEVEL OUT,H \r\n',
                                    ]
                if self.port.isOpen():
                    print('slotID : ', slotID, "Power On start")
                    for pwr_on_i in pwr_ow_sequences:
                        self.port.write(pwr_on_i.encode())
                        time.sleep(0.1)
                        print(pwr_on_i)
                    print("Debug -> will be sleep 10s, please waiting...")
                    time.sleep(10.2)
                    self.port.write(f'CONFIG:SLOT{slotID}:DIO:PORT0:LEVEL OUT,H \r\n'.encode())
                    time.sleep(2)
                    print('slotID : ', slotID, "Power On END")
                else:
                    raise ValueError('fixture serial port not opened!')

        def stopFixturePort(self):
                if self.port.isOpen():
                        self.port.close()


if __name__ == '__main__':
    slotList = [0]
    portName = '/dev/cu.usbmodem123456781'
    pctl = powerControl(portName)
    pctl.DUTPowerON(0)






