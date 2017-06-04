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

    def open(self):
        """
        Open (opens the device once)
        @ldev : the device string to open
        """
        try:
            #self._log.info(u"Try to open MPR6ZMAUT: %s" % ldev)
            self._ser = serial.Serial(self.ldev, 9600, timeout=1)
            #self._log.info("MPR6ZMAUT: %s opened" % ldev)
        except:
            error = "Error while opening Mpr6zmaut : %s. Check if it is the good device or if you have the good permissions on it." % ldev
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
            self._ser.write(command)
        except:
            error = "Error while writing to mpr6zhmaut device"
            raise Mpr6zhmautException(error)

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
