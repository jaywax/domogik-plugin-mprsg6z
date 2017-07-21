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

PZONE_DEFAULT = {
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

VZONE_DEFAULT = {
  "Status":"locked",
  "MU":"00",
  "DT":"00",
  "VO":"00",
  "TR":"07",
  "BS":"07",
  "BL":"10",
  "CH":"01"
}

PZONE_TO_VZONE = {
  'MU',
  'DT',
  'VO',
  'TR',
  'BS',
  'BL',
  'CH'
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
    def __init__(self, log, channels, device='/dev/ttyUSB0'):
        """
        Construct the instance virtual amp

        Keyword arguments:
        log -- log instance
        channels -- dict with descrption of the 6 input channel 
        device -- rs232 device (default /dev/ttyUSB0)
        """

        self.log = log 
        self.channels = channels
        self.device = device
	self._vzones = {}
	self._vzones_old = {}

        # initialize 2D dict to store running p_params
        self.p_params = {}
        for i in range(1, 4):
            for j in range(1, 7):
                zone = str(i) + str(j)
                self.p_params[zone] = {}
                for cle, valeur in PZONE_DEFAULT.items(): 
                    self.p_params[zone][cle] = valeur
                self.p_params[zone]['slaveof'] = []
                self.p_params[zone]['lockedby'] = ""
	self.log.info(u"==> Mprsg6z Amp created : channels : {0}, device : {1}".format(self.channels, self.device))

    # -------------------------------------------------------------------------------------------------
    def open(self):
        """
        Method used to open the rs232 device with serial.Serial
        """
        try:
            self._ser = serial.Serial(self.device, 9600, timeout=1)
	    self.log.info(u"==> Mprsg6z Amp open() : OK".format(self.channels, self.device))
        except:
            error = "Error while opening device : {}".format(self.device)
            raise Mprsg6zException(error)


    def close(self):
        """
        Method used to close the rs232 device with serial.Serial
        """
        try:
            self._ser.close()
        except:
            error = "Error while closing device : {}".format(self.device)
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
        #return(p_zone, self.p_params[p_zone])


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
	#return(var)

    def getVampAll(self):
        """
        Return all the param of all zone of all amp
        Update the dict p_params{} with it
        """
        for i in range(1, 4):
            self.getAllZoneAllParam(str(i))
	#return(self.p_params)

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
	command = '<' + str(p_zone) + str(param) + str(value) + '\r\n'
        try:
            #self._ser.write('<' + p_zone + param + value + '\r\n')
            self._ser.write(command)
            self.log.info(u"=> command {0} sent to the amp".format(command))
        except:
            error = "Error while polling device : {}".format(self.device)
            raise Mprsg6zException(error)

        # Finally, we update the params{} and return the updated data
	self.p_params[p_zone][param] = value 
        #return self.getOneZoneOneParam(p_zone, param)


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
            error = "Error while polling device : {}".format(self.device)
            raise Mprsg6zException(error)

        # Finally, we update the params{} and return the updated data
        return self.getAllZoneOneParam(p_amp, param)

    # -------------------------------------------------------------------------------------------------
    def add_vzone(self, deviceid, zone_name, zone_childs):
        """"
	Add a vzone to _vzones list 
	"""
	self._vzones[deviceid] = {}
        for cle, valeur in VZONE_DEFAULT.items():
            self._vzones[deviceid][cle] = valeur
	self._vzones[deviceid]['childs'] = []
	self._vzones[deviceid]['childs'] = zone_childs.split(",")
	self._vzones[deviceid]['name'] = zone_name
	flag = ''
        for child in self._vzones[deviceid]['childs']:
            self.p_params[child]['slaveof'].append(zone_name)
            flag = flag + self.p_params[child]['lockedby']
            if not flag:
		self._vzones[deviceid]['Status'] = 'off'
        # copy of the interesting parameter of the first child of the _vzone
       	for cle in PZONE_TO_VZONE:
            self._vzones[deviceid][cle] = self.p_params[self._vzones[deviceid]['childs'][0]][cle]
	#self._vzones[deviceid]['PO'] = '00'
        # update of all the param of the vamp
        #self.getVampAll()
	self.getOneZoneAllParam(self._vzones[deviceid]['childs'][0])
	# copy current param of _vzones for comparaison
        self._vzones_old[deviceid] = self._vzones[deviceid].copy()
        self.log.info(u"=> vzone {0} created : {1}".format(deviceid, zone_name))
        self.log.debug(u"==> vzone {0} {1}".format(zone_name,self._vzones[deviceid]))

    # ------------------------------------------------------------------------------------------------- 
    
    def update_vzone_status(self, send):
        for zone in self._vzones:
            childs_lockedby = []
            # used to set status of a _vzone
            for child in self._vzones[zone]['childs']:
                childs_lockedby.append(self.p_params[child]['lockedby'])
                # if the len of the set of childs_lockedby is stricly superior to 1, the v_zone must be locked
                # because another vzone is already up
                if len(set(childs_lockedby)) > 2:
                    self._vzones[zone]['Status'] = "locked"
                else:
                    # if one or minus than one child zone is locked, the status can be on or off
                    # to know, we take the first p_zone child as model
                    first_pzone = self._vzones[zone]['childs'][0]
                    if self.p_params[first_pzone]['lockedby'] == self._vzones[zone]['name']:
                        self._vzones[zone]['Status'] = "on"
                    # if the p_zone model isn't locked and the len of the set of childs_lockedby is equal to 1
                    elif self.p_params[first_pzone]['lockedby'] == '' and len(set(childs_lockedby)) == 1:
                        self._vzones[zone]['Status'] = "off"
                    # if the child is locked by another v_zone, the actual _vzone must be locked
                    else:
                        self._vzones[zone]['Status'] = "locked"
            val = ("Status", self._vzones[zone]['Status'])
	    send(zone,val)


    def loop_read_vzones(self, send, stop, interval):
        """
        """
	calculated_interval = int(interval)/len(self._vzones)
        self.log.info(u"=>Internal loop for vzones reading started for {0} registered zones each {1} seconds.".format(len(self._vzones),calculated_interval))
        while not stop.isSet():
            for zone in self._vzones:
	        childs_lockedby = []
		self.log.info(u"=>{0} is been  polled".format(self._vzones[zone]['name']))
		# used to set status of a _vzone
	    	for child in self._vzones[zone]['childs']:
	            childs_lockedby.append(self.p_params[child]['lockedby'])   
		# if the len of the set of childs_lockedby is stricly superior to 1, the v_zone must be locked
		# because another vzone is already up
	    	if len(set(childs_lockedby)) > 2:
	            self._vzones[zone]['Status'] = "locked"
		else:
		    # if one or minus than one child zone is locked, the status can be on or off
		    # to know, we take the first p_zone child as model
                    first_pzone = self._vzones[zone]['childs'][0]
               	    if self.p_params[first_pzone]['lockedby'] == self._vzones[zone]['name']:
                        self._vzones[zone]['Status'] = "on"
		    # if the p_zone model isn't locked and the len of the set of childs_lockedby is equal to 1
                    elif self.p_params[first_pzone]['lockedby'] == '' and len(set(childs_lockedby)) == 1:
                        self._vzones[zone]['Status'] = "off"
		    # if the child is locked by another v_zone, the actual _vzone must be locked
               	    else:
                        self._vzones[zone]['Status'] = "locked"
		val = ("Status", self._vzones[zone]['Status'])
		self.log.info(u"=>{0} is {1}".format(self._vzones[zone]['name'], self._vzones[zone]['Status']))
                send(zone, val)

		# if the _vzone is on or off, we update the others params
		if self._vzones[zone]['Status'] == 'on' or self._vzones[zone]['Status'] == 'off':
		    self.log.info(u"=>{0} is {1}. We could update its parameters.".format(self._vzones[zone]['name'],self._vzones[zone]['Status']))
		    for cle in PZONE_TO_VZONE:
                        self._vzones[zone][cle] = self.p_params[self._vzones[zone]["childs"][0]][cle]
            	    diffparams = [param for param in self._vzones[zone] if self._vzones[zone][param] != self._vzones_old[zone][param]]
            	    self._vzones_old[zone] = self._vzones[zone].copy()
                    if diffparams:
		        for i,elt in enumerate(diffparams):
		            val = elt, self._vzones[zone][elt]
                            self.log.info(u"=> '{0}' : {1} update of {2} with value {3}".format(zone,self._vzones[zone]['name'],elt,self._vzones[zone][elt]))
                            send(zone, val)
			    
                stop.wait(calculated_interval)

    # -------------------------------------------------------------------------------------------------
    def VzoneOneCommand(self, device_id, command, value):
        """
        Set a param's value of the v_zone 

        """
        # if the v_zones is not locked (on or off)
        if not self._vzones[device_id]['Status'] == "locked":
            # in case of PO trigger
            if command == 'PO': 
            # if we want to stand up a v_zone, we update the lockedby of each p_zone child
	        if self._vzones[device_id]['Status'] == "off":
                    for child in self._vzones[device_id]['childs']:
                        self.setOneZoneOneParam(child,'PR','01')
                        self.p_params[child]['lockedby'] = self._vzones[device_id]['name']
		    self._vzones[device_id]['Status'] = "on"
                # if we want to shut down a v_zone, we update the lockedby of each p_zone child
		# and release them.
		elif self._vzones[device_id]['Status'] == "on":
                    for child in self._vzones[device_id]['childs']:
                        self.setOneZoneOneParam(child,'PR','00')
                        self.p_params[child]['lockedby'] = ''
		    self._vzones[device_id]['Status'] = "off"
	    # For the others params, a p_zone must be "on"
	    else:
	        if self._vzones[device_id]['Status'] == "on":
                    for child in self._vzones[device_id]['childs']:
                        self.setOneZoneOneParam(child,command,value)
		        self._vzones[device_id][command] = value
		    
	    # We lauch an update thread
	    #print(self.threadVzone())
	    #return(self.zname, param, value)
        return True, None

    # -------------------------------------------------------------------------------------------------

        def getVzoneOneParam(self, param):
            """ 
            Return one param of the first p_zone of childs v_zone

            Keyword arguments:
            param -- param to pull
            """

            # return only the param of the first p_zone of the v_zone
	    # if we want to know th CH parameter, we use the channels dict of
	    # the v_amp object
	    if param == "CH":
	        return(param, self.v_amp_obj.channels[self.v_amp_obj.p_params[self.v_params["childs"][0]][param]])
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
