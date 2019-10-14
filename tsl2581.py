import smbus
import time


# I2C address options
ADDR_LOW = 0x29
ADDR_FLOAT = 0x39    # Default address (pin left floating)
ADDR_HIGH = 0x49

# ---------------------------------------------------
# x       xx      xxxxx
# CMD TRANSACTION ADDRESS

COMMAND_CMD = 0x80
TRANSACTION = 0x40  # read/write block protocol.
TRANSACTION_SPECIAL = 0X60
# ADDRESS
CONTROL = 0x00
TIMING = 0x01
INTERRUPT = 0X02
THLLOW = 0x03
THLHIGH = 0X04
THHLOW = 0x05
THHHIGH = 0X06
ANALOG = 0X07

ID = 0X12
DATA0LOW = 0X14  # 1 10 1 0010
DATA0HIGH = 0X15
DATA1LOW = 0X16
DATA1HIGH = 0X17
# ---------------------------------------------------

ADC_EN = 0X02
CONTROL_POWERON = 0x01
CONTROL_POWEROFF = 0x00
INTR_TEST_MODE = 0X30
INTR_INTER_MODE = 0X1F

# TRANSACTION_SPECIAL
SPECIAL_FUN_RESER1 = 0X00
SPECIAL_FUN_INTCLEAR = 0X01
SPECIAL_FUN_STOPMAN = 0X02
SPECIAL_FUN_STARTMAN = 0X03
SPECIAL_FUN_RESER2 = 0X0F

# INTERRUPT
INTEGRATIONTIME_Manual = 0x00
INTEGRATIONTIME_2Z7MS = 0xFF
INTEGRATIONTIME_5Z4MS = 0xFE
INTEGRATIONTIME_51Z3MS = 0xED
INTEGRATIONTIME_100MS = 0xDB
INTEGRATIONTIME_200MS = 0xB6
INTEGRATIONTIME_400MS = 0x6C
INTEGRATIONTIME_688MS = 0x01

# ANALOG
GAIN_1X = 0x00
GAIN_8X = 0x01
GAIN_16X = 0x02
GAIN_111X = 0x03


LUX_SCALE = 16  # scale by 2^16
RATIO_SCALE = 9  # scale ratio by 2^9
# ---------------------------------------------------
# Integration time scaling factors
# ---------------------------------------------------
CH_SCALE = 16  # scale channel values by 2^16

# Nominal 400 ms integration.
# Specifies the integration time in 2.7-ms intervals
# 400/2.7 = 148
NOM_INTEG_CYCLE = 148
# ---------------------------------------------------
# Gain scaling factors
# ---------------------------------------------------
CH0GAIN128X = 107  # 128X gain scalar for Ch0
CH1GAIN128X = 115  # 128X gain scalar for Ch1

# ---------------------------------------------------
K1C = 0x009A  # 0.30 * 2^RATIO_SCALE
B1C = 0x2148  # 0.130 * 2^LUX_SCALE
M1C = 0x3d71  # 0.240 * 2^LUX_SCALE

K2C = 0x00c3  # 0.38 * 2^RATIO_SCALE
B2C = 0x2a37  # 0.1649 * 2^LUX_SCALE
M2C = 0x5b30  # 0.3562 * 2^LUX_SCALE

K3C = 0x00e6  # 0.45 * 2^RATIO_SCALE
B3C = 0x18ef  # 0.0974 * 2^LUX_SCALE
M3C = 0x2db9  # 0.1786 * 2^LUX_SCALE

K4C = 0x0114  # 0.54 * 2^RATIO_SCALE
B4C = 0x0fdf  # 0.062 * 2^LUX_SCALE
M4C = 0x199a  # 0.10 * 2^LUX_SCALE

K5C = 0x0114  # 0.54 * 2^RATIO_SCALE
B5C = 0x0000  # 0.00000 * 2^LUX_SCALE
M5C = 0x0000  # 0.00000 * 2^LUX_SCALE
# ---------------------------------------------------


class TSL2581():
    def __init__(self, channel, I2C_addr):
        self.channel = channel
        self.I2C_addr = I2C_addr
        self.bus = smbus.SMBus(channel)

    def Write8(self, reg, value):
        self.bus.write_byte_data(self.I2C_addr, reg, value & 0xff)

    def power_on(self):
        self.Write8(COMMAND_CMD | CONTROL, CONTROL_POWERON)

    def power_off(self):
        self.Write8(COMMAND_CMD | CONTROL, CONTROL_POWEROFF)

    def config(self, gain_size=GAIN_16X):
        """gain_size参数设置倍数，越大，测量范围越小, default=GAIN_16X"""
        self.Write8(COMMAND_CMD | TIMING, INTEGRATIONTIME_400MS)
        self.Write8(COMMAND_CMD | CONTROL, ADC_EN | CONTROL_POWERON)
        self.Write8(COMMAND_CMD | INTERRUPT, INTR_INTER_MODE)
        self.Write8(COMMAND_CMD | ANALOG, gain_size)

    def read_channel(self):
        low = self.bus.read_byte_data(self.I2C_addr, COMMAND_CMD | TRANSACTION | DATA0LOW)
        high = self.bus.read_byte_data(self.I2C_addr, COMMAND_CMD | TRANSACTION | DATA0HIGH)
        self.ch0 = high * 256 + low
        # print('ch0:', self.ch0)
        low = self.bus.read_byte_data(self.I2C_addr, COMMAND_CMD | TRANSACTION | DATA1LOW)
        high = self.bus.read_byte_data(self.I2C_addr, COMMAND_CMD | TRANSACTION | DATA1HIGH)
        self.ch1 = high * 256 + low
        # print('ch1:', self.ch1)

    def calculateLux(self, iGain=2, tIntCycles=148):
        """Arguments: unsigned int iGain - gain, where 0:1X, 1:8X, 2:16X, 3:128X
        unsigned int tIntCycles - INTEG_CYCLES defined in Timing Register
        iGain参数需要与增益倍数一致
        """
        if (tIntCycles == NOM_INTEG_CYCLE):
            chScale0 = 65536
        else:
            chScale0 = int((NOM_INTEG_CYCLE << CH_SCALE) / tIntCycles)
        if iGain == 0:
            chScale1 = chScale0  # No scale. Nominal setting
        elif iGain == 1:
            chScale0 = chScale0 >> 3  # Scale/multiply value by 1/8
            chScale1 = chScale0
        elif iGain == 2:
            chScale0 = chScale0 >> 4  # Scale/multiply value by 1/16
            chScale1 = chScale0
        elif iGain == 3:
            chScale1 = int(chScale0/CH1GAIN128X)
            chScale0 = int(chScale0/CH0GAIN128X)

        channel0 = (self.ch0 * chScale0) >> CH_SCALE
        channel1 = (self.ch1 * chScale1) >> CH_SCALE
        if channel0 != 0:
            ratio1 = int((channel1 << (RATIO_SCALE + 1)) / channel0)
        # print('ratio1:', ratio1)

        ratio = (ratio1 + 1) >> 1

        if ((ratio >= 0) and (ratio <= K1C)):
            b = B1C
            m = M1C
        elif (ratio <= K2C):
            b = B2C
            m = M2C
        elif (ratio <= K3C):
            b = B3C
            m = M3C
        elif (ratio <= K4C):
            b = B4C
            m = M4C
        elif (ratio > K5C):
            b = B5C
            m = M5C
        temp = ((channel0 * b) - (channel1 * m))
        temp = temp + 32768
        lux_temp = temp >> LUX_SCALE  # strip off fractional portion
        print('lux is:', lux_temp)
        return lux_temp  # Signal I2C had no errors

    def reload_register(self):
        self.Write8(COMMAND_CMD | TRANSACTION_SPECIAL | SPECIAL_FUN_INTCLEAR, SPECIAL_FUN_INTCLEAR)
        self.Write8(COMMAND_CMD | CONTROL, ADC_EN | CONTROL_POWERON)


if __name__ == '__main__':
    sensor = TSL2581(1, 0x39)
    sensor.power_on()
    time.sleep(2)
    sensor.config(gain_size=GAIN_1X)
    for i in range(100):
        time.sleep(0.5)
        sensor.read_channel()
        sensor.calculateLux(iGain=0)
    sensor.power_off()
