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
        self.sources = sources

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
        return(p_zone, param, reponse)


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
        return(p_zone, self.p_params[p_zone])


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
        var = []
        for elt in reponse:
            zone = p_amp + str(i) 
            self.p_params[zone][str(param)] = elt
            var.append(self.p_params[zone][str(param)])
            i += 1
	return(p_amp + '0',param,var)

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
	var = {}
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
	    var[zone] = self.p_params[zone]
            i += 1
	return(var)

    def getVampAll(self):
        """
        Return all the param of all zone of all amp
        Update the dict p_params{} with it
        """
        for i in range(1, 4):
            self.getAllZoneAllParam(str(i))
	return(self.p_params)

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

    instances -- Variable of class to store created instances of virtual zones
    """

    instances = []

    def __init__(self, log, name, v_amp_obj, childs):
        """
        Create an instance of v_zone

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
        # the we update the slaveof paramater of each child p_zone
	# in the mean time we check the lockedby paramater and determine 
	# the status of the v_zone
	self.flag = ''
        for child in self.v_params['childs']:
            self.v_amp_obj.p_params[child]['slaveof'].append(self.name)
	    self.flag = self.flag + self.v_amp_obj.p_params[child]['lockedby']
        if not self.flag:
            self.v_params['status'] = "available"
	# then we update the others params (sensors of p_zone) of the v_zone
	for cle, valeur in PARAM_DEFAULT.items():
            self.v_params[cle] = self.v_amp_obj.p_params[self.v_params["childs"][0]][cle]
	# we update all the p_zone params and create an old v_params
	# for MQ Usage comparaison 
        self.v_amp_obj.getVampAll()
	self.v_params_old = self.v_params.copy()
            
# -------------------------------------------------------------------------------------------------
    def getVzoneOneParam(self, param):
        """ 
        Return one param of the first p_zone of childs v_zone

        Keyword arguments:
        param -- param to pull
        """

        # return only the param of the first p_zone of the v_zone
	# if we want to know th CH parameter, we use the sources dict of
	# the v_amp object
	if param == "CH":
	    return(param, self.v_amp_obj.sources[self.v_amp_obj.p_params[self.v_params["childs"][0]][param]])
	else:
            value = self.v_amp_obj.p_params[self.v_params["childs"][0]][param]
            return(param, value)

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

        Return:
        A list with the name of v_zone, the param and its value
        """
        
        # if the v_zones is not locked (on or available)
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
	    # For the others params, a p_zone must be "on"
	    else:
	        if self.v_params['status'] == "on":
                    for child in self.v_params['childs']:
                        self.v_amp_obj.setOneZoneOneParam(child,param,value)
		    self.v_params[param] = value
		    
	# We lauch an update thread
	print(threadVzone())
	return(self.name, param, value)

# -------------------------------------------------------------------------------------------------
def threadVzone():
    """
    Thread function to update status and sensors of v_zone

    Return :
    var -- Dict with differences of all instances of v_zone
    """

    # dict created to send to MQ
    var = {}
    for instance in Mprsg6zVzone.instances:
	# check if one of a p_zone child is lockedby 
	childs_lockedby = []
	for child in instance.v_params['childs']:
	    childs_lockedby.append(instance.v_amp_obj.p_params[child]['lockedby'])   
	# if more than 1 unique lockedby is reported, the whole v_zone must be locked
	if len(set(childs_lockedby)) > 1:
	    instance.v_params['status'] = "locked"
	else:
	# if not, we use the first_pzone as model
            first_pzone = instance.v_params['childs'][0]
            if instance.v_amp_obj.p_params[first_pzone]['lockedby'] == instance.name:
	        instance.v_params['status'] = "on"
            elif instance.v_amp_obj.p_params[first_pzone]['lockedby'] == '':
	        instance.v_params['status'] = "available"
	    # else, the v_zone should be locked
	    else:
	        instance.v_params['status'] = "locked"
	# then we update the others params of the vzone (copy the sensors of the first p_zone)
	for cle, valeur in PARAM_DEFAULT.items():
            instance.v_params[cle] = instance.v_amp_obj.p_params[instance.v_params["childs"][0]][cle]
	#var[instance.name] = instance.v_params
	diffparams = [(param+':'+instance.v_params[param]) for param in instance.v_params if instance.v_params[param] != instance.v_params_old[param]]
	#for param in diffparams:
	#    print instance.name,param, ':', instance.v_params_old[param], '->', instance.v_params[param]
	instance.v_params_old = instance.v_params.copy()
	if diffparams:
	    var[instance.name] = diffparams
    return(var)

# -------------------------------------------------------------------------------------------------
# Only for test purpose
if __name__ == "__main__":
    sources = {'01':'jay','02':'sof','03':'ylan','04':'leny','05':'fibre1','06':'fibre2'}
    myamp = Mprsg6zVamp('log', '1er ampli monoprice', sources)
    myamp.open()
    childs = ['11']
    cuisine = Mprsg6zVzone('log', 'Cuisine', myamp, childs)
    childs = ['12']
    salle_a_manger = Mprsg6zVzone('log', 'Salle à manger', myamp, childs)
    childs = ['13']
    salon = Mprsg6zVzone('log', 'Salon', myamp, childs)
    childs = ['11','12','13']
    bas = Mprsg6zVzone('log', 'Cuisine|Salle à manger|Salon', myamp, childs)
    print(salon.setVzoneOneParam("PR","01"))
    print(salon.getVzoneOneParam('CH'))
    print(salon.setVzoneOneParam("VO","01"))
    print(salon.setVzoneOneParam("VO","00"))
    print(cuisine.setVzoneOneParam("PR","01"))
    print(cuisine.setVzoneOneParam("VO","01"))
    print(salon.setVzoneOneParam("PR","00"))
    print(cuisine.setVzoneOneParam("PR","00"))
    myamp.close()
