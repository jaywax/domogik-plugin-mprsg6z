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
    Mprsg6z exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

# -------------------------------------------------------------------------------------------------
class Mprsg6zVamp:
    """
    Create python object and methods to interact with rs232 amps
    """
    def __init__(self, log, name, sources, dev='/dev/ttyUSB0'):
        """
        Construct the instance virtual amp

        Keyword arguments:
        log -- log instance ??
        name -- technical device name present in domogik
        sources -- dict with descrption of the 6 input channel 
        dev -- rs232 device (default /dev/ttyUSB0)
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

        # initialize 2D dict to store running p_params
        self.p_params = {}
        for i in range(1, 4):
            for j in range(1, 7):
                zone = str(i) + str(j)
                self.p_params[zone] = {}
                for cle, valeur in PARAM_DEFAULT.items(): 
                    self.p_params[zone][cle] = valeur
                self.p_params[zone]['slaveof'] = []
                self.p_params[zone]['lockedby'] = ""

    # -------------------------------------------------------------------------------------------------
    def open(self):
        """
        Method used to open the rs232 device with serial.Serial
        """
        try:
            self._ser = serial.Serial(self.dev, 9600, timeout=1)
        except:
            error = "Error while opening device : {}".format(self.dev)
            raise Mprsg6zException(error)


    def close(self):
        """
        Method used to close the rs232 device with serial.Serial
        """
        try:
            self._ser.close()
        except:
            error = "Error while closing device : {}".format(self.dev)
            raise Mprsg6zException(error)


    def _readline(self, a_serial, eol=b'\r\r\n'):
        """
        Format the data return by the amp during status query

        Keyword arguments:
        a_serial -- the Serial.serial line
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
        Return one param of one p_zone
        Update the dict p_params{} with it

        Keyword arguments:
        p_zone -- p_zone to pull
        param -- param to pull
        """
        try:
            self._ser.write('?' + p_zone + param + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        rcv = self._readline(self._ser)
	regexp = '>' + p_zone + param + '(.+?)\\r\\r\\n'
        reponse = re.search(regexp, rcv).group(1)
        self.p_params[p_zone][param] = reponse
        return self.p_params[p_zone][param]


    def getOneZoneAllParam(self, p_zone):
        """
        Return all the params of one p_zone
        Update the dict p_params{} with it

        Keyword arguments:
        p_zone -- zone to pull
        """
        try:
        	self._ser.write('?' + p_zone + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)
            
        rcv = self._readline(self._ser)
	regexp = '>' + p_zone + '(.+?)\\r\\r\\n'
        reponse = re.search(regexp, rcv).group(1)
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
        Return one param for all zone of an amp
        Update the dict p_params{} with it

        Keyword arguments:
        p_amp -- amp to pull
        param -- param to pull
        """
        try:
            self._ser.write('?' + p_amp + '0' + param + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        rcv = self._readline(self._ser, eol=b'\r\r\n\n')
	regexp = '>' + p_amp + '[1-6]{1}[A-Z]{2}(.+?)\\r\\r\\n'
        reponse = re.findall(regexp, rcv)
        i = 1
        for elt in reponse:
            zone = p_amp + str(i) 
            self.p_params[zone][str(param)] = elt
            print(zone, param, elt)
            i += 1


    def getAllZoneAllParam(self, p_amp):
        """
        Return all zone's param on an amp
        Update the dict p_params{} with it

        Keyword arguments:
        p_amp -- amp to pull
        """
        try:
            self._ser.write('?' + p_amp + '0\r\n\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        rcv = self._readline(self._ser, eol=b'\r\r\n\n')
	regexp = '>' + p_amp + '[1-6]{1}(.+?)\\r\\r\\n'
        # Return a list with all params of each zone in
        # the right order
        reponse = re.findall(regexp, rcv)
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
            i += 1


    def getVampAll(self):
        """
        Return all the param of all zone of all amp
        Update the dict p_params{} with it
        """
        for i in range(1, 4):
            self.getAllZoneAllParam(str(i))

    # -------------------------------------------------------------------------------------------------
    def setOneZoneOneParam(self, p_zone, param, value):
        """
        Set a param's value of a zone's amp 
        Update the dict p_params{} via getOneZoneOneParam method

        Keyword arguments:
        p_zone -- the physical zone to set
        Gparam -- the param to set
        value -- the value to set
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
        Update the dict p_params{} via getAllZoneOneParam method

        Keyword arguments:
        p_amp -- the physical amp where all zone will be set
        param -- the param to set
        value -- value to set
        """
        try:
            self._ser.write('<' + p_amp + '0' + param + value + '\r\n')
        except:
            error = "Error while polling device : {}".format(self.dev)
            raise Mprsg6zException(error)

        # Finally, we update the params{} and return the updated data
        return self.getAllZoneOneParam(p_amp, param)

# -------------------------------------------------------------------------------------------------
class Mprsg6zVzone():
    """
    Create python object and methods to interact with virtual zones

    instances -- Variable of class to store created instances
    """

    instances = []

    def __init__(self, log, name, v_amp_obj, childs):
        """
        Create an instance of v_zone to store parameters

        Keyword arguments:
        log -- log instance ??
        name -- technical device name of the v_zone
        v_amp_obj -- instance of the class Mpr6zVamp to use
        childs -- list with p_zones to control
        """

        self._log = log 
        self.name = name
        self.v_amp_obj = v_amp_obj
        self.childs = childs
	Mprsg6zVzone.instances.append(self)
        # initialize the dict to store running v_params
        self.v_params = {}
        self.v_params['childs'] = childs
        # at creation time, the v_zone is locked
        self.v_params['status'] = "locked"
        # update the param slaveof for all p_zone childs
	# 
	self.flag = ''
        for child in self.v_params['childs']:
            self.v_amp_obj.p_params[child]['slaveof'].append(self.name)
	    self.flag = self.flag + self.v_amp_obj.p_params[child]['lockedby']
        if not self.flag:
            self.v_params['status'] = "available"
            
# -------------------------------------------------------------------------------------------------
    def getVzoneOneParam(self, param):
        """ 
        Return one param of the first p_zone of childs v_zone

        Keyword arguments:
        param -- param to pull
        """

        # return only the param of the first p_zone of the v_zone
        value = self.v_amp_obj.p_params[self.v_params["childs"][0]][param]
        return (param, value)

    def getVzoneAllParam(self):
        """ 
        Return all param of the first p_zone of childs v_zone
        """

        # return only the params of the first p_zone of the v_zone
        return(self.v_amp_obj.p_params[self.v_params["childs"][0]])
# -------------------------------------------------------------------------------------------------
    def setVzoneOneParam(self, param, value):
        """
        Set a param's value of the v_zone 

        Keyword arguments:
        param -- the param to set
        value -- the value to set
        """
        
        # if the v_zones is not locked (so on or available)
        if not self.v_params['status'] == "locked" :
            # in case of PR arg
            if param == 'PR': 
                # if we want to stand up a v_zone, we update the lockedby of each p_zone child
                if value == '01':
		    # if alredy on we do nothing
		    if self.v_params['status'] == "available":
                    	for child in self.v_params['childs']:
                            self.v_amp_obj.setOneZoneOneParam(child,'PR','01')
                            self.v_amp_obj.p_params[child]['lockedby'] = self.name
		        self.v_params['status'] = "on"
                # if we want to shut down a v_zone, we update the lockedby of each p_zone child
		# and release them.
		else:
		    if self.v_params['status'] == "on":
                        for child in self.v_params['childs']:
                            self.v_amp_obj.setOneZoneOneParam(child,'PR','00')
                            self.v_amp_obj.p_params[child]['lockedby'] = ''
		        self.v_params['status'] = "available"
	print("setVzoneOneParam :" + self.name + param + value)

# -------------------------------------------------------------------------------------------------
def threadVzone():
    """
    Thread function to update status of v_zone
    """

    # for all v_zones created
    for instance in Mprsg6zVzone.instances:
	# the first p_zone of v_zone is used as model
        first_pzone = instance.v_params['childs'][0]
	# if this model is locked by this v_zone, the v_zone should be on
        if instance.v_amp_obj.p_params[first_pzone]['lockedby'] == instance.name:
	    instance.v_params['status'] = "on"
	# if this model is not locked, th v_zone should be available
        elif instance.v_amp_obj.p_params[zone_temoin]['lockedby'] == '':
	    instance.v_params['status'] = "available"
	# else, the v_zone should be locked
	else:
	    instance.v_params['status'] = "locked"
	print("treadVzone() :" + instance.name + " is " + instance.v_params['status'])




if __name__ == "__main__":
    sources = {'input1':'jay','input2':'sof','input3':'ylan','input4':'leny','input5':'fibre1','input6':'fibre2'}
    myamp = Mprsg6zVamp('log', '1er ampli monoprice', sources)
    myamp.open()
    myamp.getVampAll()
    childs = ['11']
    myvzone1 = Mprsg6zVzone('log', 'Cuisine', myamp, childs)
    threadVzone()
    myvzone1.setVzoneOneParam("PR","01")
    threadVzone()
    print(myamp.getAllZoneAllParam('1'))
    childs = ['11','12','13']
    myvzone2 = Mprsg6zVzone('log', 'Cuisine|Salle à manger|Salon', myamp, childs)
    threadVzone()
    print(myamp.getAllZoneAllParam('1'))
    myvzone2.setVzoneOneParam("PR","01")
    threadVzone()
    print(myamp.getAllZoneAllParam('1'))
    myvzone1.setVzoneOneParam("PR","00")
    threadVzone()
    print(myamp.getAllZoneAllParam('1'))
    myvzone2.setVzoneOneParam("PR","01")
    threadVzone()
    print(myamp.getAllZoneAllParam('1'))
    myvzone2.setVzoneOneParam("PR","00")
    threadVzone()
    print(myamp.getAllZoneAllParam('1'))
    myamp.close()
