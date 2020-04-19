#!/usr/bin/python3

import serial

# Assumes the following settings for the DCS M9 RS-232 Interface
# Baud-rate = 19200
# Hardware Flow Control = None

class sorensenPower(object):
    DEFAULT_TIMEOUT = 0.125

    # List of commands
    COMMAND_IDN                     = "*IDN?\r"

    COMMAND_MEASURE_CURRENT         = ":MEAS:CURR?\r"
    COMMAND_MEASURE_VOLTAGE         = ":MEAS:VOLT?\r"
    COMMAND_SET_VOLTAGE             = ":SOUR:VOLT {:1.03f}\r"
    COMMAND_SET_VOLTAGE_RAMP        = ":SOUR:VOLT:RAMP {:1.03f} {:1.01f}\r"
    COMMAND_SET_CURRENT             = ":SOUR:CURR {:1.03f}\r"
    COMMAND_GET_STATUS              = ":SOUR:STAT:BLOC?\r"
    COMMAND_RETURN_LOCAL            = ":SYST:LOCAL ON\r"

    def __init__(self, portName="/dev/ttyUSB0", baudrate=19200, debug=False):
        self.portName = portName
        self.baudrate = baudrate

        self.port = serial.Serial()
        self.port.baudrate = self.baudrate
        self.port.port = self.portName
        self.port.timeout = self.DEFAULT_TIMEOUT
        self.port.rts = True
        self.port.dtr = True

        self.debug = debug

        self.model = None
        self.serialNumber = None
        self.maxVoltage = None
        self.maxCurrent = None

        self.connect()

    def __del__(self):
        # Make sure we return control to local.
        self.disconnect()

    def _writeCommand(self, command):
        result = None

        if (self.port.isOpen()):
            if (self.debug is True):
                print(command.encode())

            self.port.write(command.encode())
            result = self.port.readline().decode(encoding='UTF-8')

            if (self.debug is True):
                print("> " + result)

        return result

    def connect(self):
        success = False

        if (self.port.isOpen() == False):
            self.port.open()

        self.getStatus()

        success = self.port.isOpen()

        return success

    def disconnect(self, returnToLocal=True):
        if (returnToLocal == True):
            self._writeCommand(self.COMMAND_RETURN_LOCAL)

        success = False

        if (self.port.isOpen() == True):
            self.port.close()
            success = True

        return success

    def getModel(self, forceUpdate=False):
        if ((self.model is None) or forceUpdate):
            self.getStatus()

        return self.model

    def getSerialNumber(self, forceUpdate=False):
        if ((self.serialNumber is None) or forceUpdate):
            self.getStatus()

        return self.serialNumber

    def getMaxVoltage(self, forceUpdate=False):
        if ((self.maxVoltage is None) or forceUpdate):
            self.getStatus()

        return self.maxVoltage

    def getMaxCurrent(self, forceUpdate=False):
        if ((self.maxCurrent is None) or forceUpdate):
            self.getStatus()

        return self.maxCurrent

    def getIdentification(self):
        identification = self._writeCommand(self.COMMAND_IDN)
        return identification.strip()

    def getOutputVoltage(self):
        voltageASCII = self._writeCommand(self.COMMAND_MEASURE_VOLTAGE)
        voltage = float(voltageASCII.strip())

        return voltage

    def getOutputCurrent(self):
        currentASCII = self._writeCommand(self.COMMAND_MEASURE_CURRENT)
        current = float(currentASCII.strip())

        return current

    def setOutputVoltage(self, voltage):
        success = False

        if ((voltage >= 0.0) and (voltage <= self.maxVoltage)):
            self._writeCommand(self.COMMAND_SET_VOLTAGE.format(voltage))
            success = True

        return success

    def setOutputVoltageRamp(self, endVoltage, rampTimeSec):
        success = False
        if ((endVoltage >= 0.0) and (endVoltage <= self.maxVoltage) and (rampTimeSec >= 0.0) and (rampTimeSec < 99.0)):
            self._writeCommand(self.COMMAND_SET_VOLTAGE_RAMP.format(endVoltage, rampTimeSec))
            success = True

        return success

    def setOutputCurrent(self, current):
        success = False

        if ((current >= 0) and (current <= self.maxCurrent)):
            self._writeCommand(self.COMMAND_SET_CURRENT.format(current))
            success = True

        return success

    def getStatus(self):
        status = None

        statusASCII = self._writeCommand(self.COMMAND_GET_STATUS).strip().split(',')

        # Doesn't seem to follow the interface spec
        if (len(statusASCII) == 23):
            statusRegister = int(statusASCII[3])
            overTemperature = bool((statusRegister >> 4) & 0x01)
            overVoltage     = bool((statusRegister >> 3) & 0x01)
            constantCurrent = bool((statusRegister >> 1) & 0x01)
            constantVoltage = bool((statusRegister >> 0) & 0x01)

            status = {
                'channelNumber'     : int(statusASCII[0]),
                'onlineStatus'      : int(statusASCII[1]),
                'statusFlags'       : int(statusASCII[2]),
                'statusRegister'    : statusRegister,
                'accumulatedStatus' : int(statusASCII[4]),
                'faultMask'         : int(statusASCII[5]),
                'faultRegister'     : int(statusASCII[6]),
                'errorRegister'     : int(statusASCII[7]),
                'overTemperature'   : overTemperature,
                'overVoltage'       : overVoltage,
                'constantCurrent'   : constantCurrent,
                'constantVoltage'   : constantVoltage,
                'serialNumber'      : statusASCII[8],
                'voltageCapability' : float(statusASCII[9]),
                'currentCapability' : float(statusASCII[10]),
                'overVoltage'       : float(statusASCII[11]),
                'voltageDacGain'    : float(statusASCII[12]),
                'voltageDacOffset'  : float(statusASCII[13]),
                'currentDacGain'    : float(statusASCII[14]),
                'currentDacOffset'  : float(statusASCII[15]),
                'protectionDacGain' : float(statusASCII[16]),
                'protectionDacOffset': float(statusASCII[17]),
                'voltageAdcGain'    : float(statusASCII[18]),
                'voltageAdcOffset'  : float(statusASCII[19]),
                'currentAdcGain'    : float(statusASCII[20]),
                'currentAcOffset'   : float(statusASCII[21]),
                'model'             : statusASCII[22]
            }

            self.model = status['model']
            self.serialNumber = status['serialNumber']
            self.maxCurrent = status['currentCapability']
            self.maxVoltage = status['voltageCapability']

        return status
