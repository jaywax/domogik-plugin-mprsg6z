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
class Mprsg6zException(Exception):
    """
    MPR6ZHMAUT exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

# -------------------------------------------------------------------------------------------------
class Mprsg6zVamp:
    """ 
    Construct the Mprsg6z Virtual Amp instance (all the physical amp on a single rs232 bus)
    """
    def __init__(self, log, name, sources, dev='/dev/ttyUSB0'):
        """
        @log : log instance
        @name : technical device name
        input channel of a virtual amp
        @dev : device where the interface is connected to
        default '/dev/ttyUSB0'
        @sources : dict with descrption of the 6 input channel 
        """

        self._log = log 
        self.name = name
        self.dev = dev
        self.input1 = sources.get('input1')
        self.input2 = sources.get('input2')
        self.input3 = sources.get('input3')
        self.input4 = sources.get('input4')
        self.input5 = sources.get('input5')
        self.input6 = sources.get('input6')

        # initialize 2D dict to store running params
        self.p_params = {}
        i = 1
        j = 1
        while i <= 3:
            while j <= 6:
                zone = str(i) + str(j)
                self.p_params[zone] = {}
                i, j = int(i), int(j)
                for cle, valeur in PARAM_DEFAULT.items(): 
                    self.p_params[zone][cle] = valeur
                j += 1
            i += 1
            j = 1

    # -------------------------------------------------------------------------------------------------
    def open(self):
        """
        Open with serial.Serial the dev device
        """
        try:
            self._ser = serial.Serial(self.dev, 9600, timeout=1)
        except:
            error = "Error while opening device : {}".format(self.dev)
            raise Mprsg6zException(error)


    def close(self):
        """
        Close the open device
        """
        try:
            self._ser.close()
        except:
            error = "Error while closing device : {}".format(self.dev)
            raise Mprsg6zException(error)


    def _readline(self, a_serial, eol=b'\r\r\n'):
        """
        Method used to format the data return by the amp 
        during status query
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


    # -------------------------------------------------------------------------------------------------
    def getOneZoneOneParam(self, p_zone, param):
        """
        Pull one parameter of a zone's amp
        Update the dict p_params{} with it
        @param p_zone : zone to pull
        @param param : param to pull
        """
        try:
            self._ser.write('?' + p_zone + param + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        rcv = self._readline(self._ser)
	regex = '>' + p_zone + param + '(.+?)\\r\\r\\n'
        reponse = re.search(regex, rcv).group(1)
        self.p_params[p_zone][param] = reponse
        return self.p_params[p_zone][param]


    def getOneZoneAllParam(self, p_zone):
        """
        Pull all the parameters of an zone's amp
        Update the dict p_params{} with it
        @param p_zone : zone to pull
        """
        try:
        	self._ser.write('?' + p_zone + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)
            
        rcv = self._readline(self._ser)
	regex = '>' + p_zone + '(.+?)\\r\\r\\n'
        reponse = re.search(regex, rcv).group(1)
        self.p_params[p_zone]['PA'] = reponse[0:2]
        self.p_params[p_zone]['PR'] = reponse[2:4]
        self.p_params[p_zone]['MU'] = reponse[4:6]
        self.p_params[p_zone]['DT'] = reponse[6:8]
        self.p_params[p_zone]['VO'] = reponse[8:10]
        self.p_params[p_zone]['TR'] = reponse[10:12]
        self.p_params[p_zone]['BS'] = reponse[12:14]
        self.p_params[p_zone]['BL'] = reponse[14:16]
        self.p_params[p_zone]['CH'] = reponse[16:18]
        self.p_params[p_zone]['LS'] = reponse[18:20]
        return self.p_params[p_zone]


    def getAllZoneOneParam(self, p_amp, param):
        """
        Pull the parameter on all zones of an amp
        Update the dict p_params{} with it
        @param p_amp : amp to pull
        @param param : param to pull
        """
        try:
            self._ser.write('?' + p_amp + '0' + param + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        rcv = self._readline(self._ser, eol=b'\r\r\n\n')
	regex = '>' + p_amp + '[1-6]{1}[A-Z]{2}(.+?)\\r\\r\\n'
        reponse = re.findall(regex, rcv)
        i = 1
        for elt in reponse:
            zone = p_amp + str(i) 
            self.p_params[zone][str(param)] = elt
            print(zone, param, elt)
            i += 1


    def getAllZoneAllParam(self, p_amp):
        """
        Pull all the amp's params
        Update the dict p_params{} with it
        @param p_amp : amp to pull
        """
        try:
            self._ser.write('?' + p_amp + '0\r\n\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        rcv = self._readline(self._ser, eol=b'\r\r\n\n')
	regex = '>' + p_amp + '[1-6]{1}(.+?)\\r\\r\\n'
        # Return a list with all params of each zone in
        # the right order
        reponse = re.findall(regex, rcv)
        i = 1
        for elt in reponse:
            zone = p_amp + str(i) 
            self.p_params[zone]['PA'] = elt[0:2]
            self.p_params[zone]['PR'] = elt[2:4]
            self.p_params[zone]['MU'] = elt[4:6]
            self.p_params[zone]['DT'] = elt[6:8]
            self.p_params[zone]['VO'] = elt[8:10]
            self.p_params[zone]['TR'] = elt[10:12]
            self.p_params[zone]['BS'] = elt[12:14]
            self.p_params[zone]['BL'] = elt[14:16]
            self.p_params[zone]['CH'] = elt[16:18]
            self.p_params[zone]['LS'] = elt[18:20]
            print(self.p_params[zone])
            i += 1


    def getLineParam(self):
        """
        Pull all the params of the line
        Update the dict p_params{} with it
        """
        i = 1
        while i <= 3:
            self.getAllZoneAllParam(str(i))
            i += 1
    # -------------------------------------------------------------------------------------------------
    def setOneZoneOneParam(self, p_zone, param, value):
        """
        Set a param's value of a zone's amp 
        Update the dict p_params{} with method get_zone_param
        """
        try:
            self._ser.write('<' + p_zone + param + value + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        # Finally, we update the params{} and return the updated data
        return self.getOneZoneOneParam(p_zone, param)


    def setAllZoneOneParam(self, p_amp, param, value):
        """
        Set a param's value on all zone of one amp
        """
        try:
            self._ser.write('<' + p_amp + '0' + param + value + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        # Finally, we update the params{} and return the updated data
        return self.getAllZoneOneParam(p_amp, param)

