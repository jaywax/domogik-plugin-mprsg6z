#!/usr/bin/python
# -*- coding: utf-8 -*-


""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Plugin for monoprice mpr-6zhmaut amp

Implements
==========

@author: jaywax  (jaywax dt 2 dt bourbon at gmail dt com)
@copyright: (C) 2007-2017 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import serial
import traceback
import time
import re

PARAM_TYPE = {
  1: {"param" :"PA", "value" : "00"},
  2: {"param" :"PR", "value" : "00"},
  3: {"param" :"MU", "value" : "00"}, 
  4: {"param" :"DT", "value" : "00"}, 
  5: {"param" :"VO", "value" : "00"}, 
  6: {"param" :"TR", "value" : "07"}, 
  7: {"param" :"BS", "value" : "07"}, 
  8: {"param" :"BL", "value" : "10"}, 
  9: {"param" :"CH", "value" : "01"}, 
  10: {"param" :"LS", "value" : "00"}, 
}

# -------------------------------------------------------------------------------------------------
class Mpr6zhmautException(Exception):
    """
    MPR6ZHMAUT exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

# -------------------------------------------------------------------------------------------------
class Mpr6zhmautLine:
    """ 
    Construct the mpr6zhmaut line instance
    """
    def __init__(self, lid, ldev='/dev/ttyUSB0', lnumamp='1'):
        """
        Create mpr6zhmaut line instance, allowing to use amp and zone
        Create a dict with all params for all amps and zones of the line
        @lid : unique identifier of this line
        @ldev : device where the interface is connected to
        default '/dev/ttyUSB0'
        @lnumamp : number of amp to handle on this line
        default '1'
        """

        self.lid = lid
        self.ldev = ldev
        self.lnumamp = lnumamp

    def __str__(self):
        """
        Method used to print the ojbect class
        """
        return "lid:{0}\nldev:{1}\nlnumamp:{2}".format(self.lid,self.ldev,self.lnumamp)

    def open(self, device):
        """
        Open (opens the device once)
        """
        try:
            #self._log.info(u"Try to open MPR6ZMAUT: %s" % device)
            self._ser = serial.Serial(device, 9600, timeout=1)
            #self._log.info("MPR6ZMAUT: %s opened" % device)
        except:
            error = "Error while opening Mpr6zmaut : %s. Check if it is the good device or if you have the good permissions on it." % device
            raise Mpr6zhmautException(error)

    def close(self):
        """
        Close the open device
        """
        #self._log.info(u"Close MRP6ZMAUT")
        try:
            self._ser.close()
        except:
            error = "Error while closing device"
            raise Mpr6zhmautException(error)

    def write(self, command):
        """
        Write command to the line
        @param command : command to send to the line
        """
        #self._log.debug(u"==> Write command '%s' to the line" % (command))
        try:
            self._ser.write(command + '\r\n')
        except:
            error = "Error while writing to mpr6zhmaut device"
            raise Mpr6zhmautException(error)

    def _readline(self, a_serial, eol=b'\r\r\n'):
        """
        Special method used to format the data return by Serial.serial
        @param a_serial : the Serial.serial line
        """
        leneol = len(eol)
        line = bytearray()
        while True:
            c = a_serial.read(1)
            if c:
                line += c
                if line[-leneol:] == eol:
                    break
            else:
                break
        return bytes(line)

    def get_zone(self, amp, zone):
        """
        Return a dict with the full params of an zone's amp
        @param amp : the number of the amp to pull
        @param zone : the number of the zone to pull
        """
        #self._log.debug(u"==> Write command '%s' to the line" % (command))
        self._ser.write('?' + amp + zone + '\r\n')
        rcv = self._readline(self._ser)
	regex = '>' + amp + zone + '(.+?)\\r\\r\\n'
        reponse = re.search(regex, rcv).group(1)
        return rcv, reponse

    def get_param(self, amp, zone, param):
        """
        Return the value of a parameter of a submitted zone
        @param amp : amp to use
        @param zone : zone to use
        @param param : param to pull
        """
        self._ser.write('?' + amp + zone + param + '\r\n')
        rcv = self._readline(self._ser)
	regex = '>' + amp + zone + param + '(.+?)\\r\\r\\n'
        reponse = re.search(regex, rcv).group(1)
        return reponse

# -------------------------------------------------------------------------------------------------
class Mpr6zhmautAmp:
    """
    Construct the mpr6zhmaut amp from an object issued from the Mpr6zhmautLine class
    """
    def __init__(self, line, aid):
        """
        Create mpr6zhmaut amp instance, allowing to use zone and general parameters
        @line : the serial line used for this amp
        @aid : unique identifier of the amp
        """

        self.line = line
        self.lid = line.lid
        self.aid = aid

    def __str__(self):
        """
        Method used to print the ojbect class
        """
        return "the_line.lid:{0}\naid:{1}".format(self.lid,self.aid)
