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
from collections import defaultdict

PARAM_DEFAULT = {
  "PA":"00",
  "PR":"00",
  "MU":"00",
  "DT":"00",
  "VO":"00",
  "TR":"07",
  "BS":"07",
  "BL":"10",
  "CH":"01",
  "LS":"00"
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
    def __init__(self, id, dev='/dev/ttyUSB0', numamp='1'):
        """
        Create mpr6zhmaut line instance, allowing to use amp and zone
        Create a dict with all params for all amps and zones of the line
        @id : unique identifier of this line
        @dev : device where the interface is connected to
        default '/dev/ttyUSB0'
        @lnumamp : number of amp to handle on this line
        default '1'
        """

        self.id = id
        self.dev = dev
        self.numamp = int(numamp)

        # Create the 3d dict [amp][zone][param] to store runing params
        # https://stackoverflow.com/questions/12167192/pythonic-way-to-create-3d-dict
        self.params = defaultdict(lambda: defaultdict(dict))
        i = 1
        j = 1
        while i <= self.numamp:
            while j <= 6:
                for cle, valeur in PARAM_DEFAULT.items(): 
                    self.params[i][j][cle] = valeur
                j += 1
            i += 1
            j = 1


    def __str__(self):
        """
        Method used to print the ojbect class
        """
        return "id:{0}\ndev:{1}\nnumamp:{2}".format(self.id,self.dev,self.numamp)


    def open(self, device):
        """
        Open with serial.Serial the dev device
        """
        try:
            self._ser = serial.Serial(device, 9600, timeout=1)
        except:
            error = "Error while opening device : %s." % device
            raise Mpr6zhmautException(error)


    def close(self):
        """
        Close the open device
        """
        #self._log.info(u"Close MRP6ZMAUT")
        try:
            self._ser.close()
        except:
            error = "Error while closing device : %s." % device
            raise Mpr6zhmautException(error)


    def _readline(self, a_serial, eol=b'\r\r\n'):
        """
        Method used to format the data return by Serial.serial
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


    def get_zone_all(self, amp, zone):
        """
        Pull all the parameters of an zone's amp and
        update the dict params{}
        @param amp : amp to pull
        @param zone : zone to pull
        """
        try:
        	self._ser.write('?' + amp + zone + '\r\n')
        except:
            error = "Error while closing device : %s." % device
            raise Mpr6zhmautException(error)
            
        rcv = self._readline(self._ser)
	regex = '>' + amp + zone + '(.+?)\\r\\r\\n'
        reponse = re.search(regex, rcv).group(1)
        amp, zone = int(amp), int(zone)
        self.params[amp][zone]['PA'] = reponse[0:2]
        self.params[amp][zone]['PR'] = reponse[2:4]
        self.params[amp][zone]['MU'] = reponse[4:6]
        self.params[amp][zone]['DT'] = reponse[6:8]
        self.params[amp][zone]['VO'] = reponse[8:10]
        self.params[amp][zone]['TR'] = reponse[10:12]
        self.params[amp][zone]['BS'] = reponse[12:14]
        self.params[amp][zone]['BL'] = reponse[14:16]
        self.params[amp][zone]['CH'] = reponse[16:18]
        self.params[amp][zone]['LS'] = reponse[18:20]
        return self.params[amp][zone]


    def get_zone_param(self, amp, zone, param):
        """
        Pull one parameter of an zone's amp and 
        update the dict params{}
        @param amp : amp to pull
        @param zone : zone to pull
        @param param : param to pull
        """
        try:
            self._ser.write('?' + amp + zone + param + '\r\n')
        except:
            error = "Error while closing device : %s." % device
            raise Mpr6zhmautException(error)

        rcv = self._readline(self._ser)
	regex = '>' + amp + zone + param + '(.+?)\\r\\r\\n'
        reponse = re.search(regex, rcv).group(1)
        amp, zone = int(amp), int(zone)
        self.params[amp][zone][param] = reponse
        return self.params[amp][zone][param]


    def get_amp_all(self, amp):
        """
        Update the dict params{} with all the param of an amp
        @param amp : amp to pull
        """
        try:
            self._ser.write('?' + amp + '0\r\n\n')
        except:
            error = "Error while closing device : %s." % device
            raise Mpr6zhmautException(error)

        rcv = self._readline(self._ser, eol=b'\r\r\n\n')
	regex = '>' + amp + '[1-6]{1}(.+?)\\r\\r\\n'
        # Return a list with all params of each zone in
        # the right order
        reponse = re.findall(regex, rcv)
        i = 1
        amp = int(amp)
        for elt in reponse:
            self.params[amp][i]['PA'] = elt[0:2]
            self.params[amp][i]['PR'] = elt[2:4]
            self.params[amp][i]['MU'] = elt[4:6]
            self.params[amp][i]['DT'] = elt[6:8]
            self.params[amp][i]['VO'] = elt[8:10]
            self.params[amp][i]['TR'] = elt[10:12]
            self.params[amp][i]['BS'] = elt[12:14]
            self.params[amp][i]['BL'] = elt[14:16]
            self.params[amp][i]['CH'] = elt[16:18]
            self.params[amp][i]['LS'] = elt[18:20]
            print(self.params[amp][i])
            i += 1


    def set_zone_param(self, amp, zone, param, value):
        """
        Set a param's value of and zone's amp and 
        update the dict params{} with method get_zone_param
        """
        try:
            self._ser.write('<' + amp + zone + param + value + '\r\n')
        except:
            error = "Error while closing device : %s." % device
            raise Mpr6zhmautException(error)

        # Finally, we update the params{} and return the updated data
        return self.get_zone_param(amp, zone, param)

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
        self.id = line.id
        self.aid = aid

    def __str__(self):
        """
        Method used to print the ojbect class
        """
        return "the_line.id:{0}\naid:{1}".format(self.id,self.aid)
