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

from domogik.common.plugin import Plugin
from domogikmq.message import MQMessage

from domogik_packages.plugin_mprsg6z.lib.mprsg6z import Mprsg6zVamp
from domogik_packages.plugin_mprsg6z.lib.mprsg6z import Mprsg6zVzone
from domogik_packages.plugin_mprsg6z.lib.mprsg6z import Mprsg6zException

import threading
import traceback


class Mprsg6zManager(Plugin):
  # -------------------------------------------------------------------------------------------------
    def __init__(self):
        """
            Init plugin
        """
        Plugin.__init__(self, name='mprsg6z')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():
            return


        # get the devices list
        self.devices = self.get_device_list(quit_if_no_device=True)
        self.log.info(u"==> device:   %s" % format(self.devices))

        # for this plugin, we have to find the mprsg6z.vamp devices first and loop on it
	self.liste_vamp = (a_device for a_device in self.devices if a_device["device_type_id"] == "mprsg6z.vamp")
	for a_vamp in self.liste_vamp:
	    vamp_name = a_vamp["name"]
            vamp_id = a_vamp["id"]
            vamp_type = a_vamp["device_type_id"]
	    vamp_device = self.get_parameter(a_vamp, "device")
 	    vamp_channels = {'01': self.get_parameter(a_vamp, "channel1"), '02': self.get_parameter(a_vamp, "channel2"), '03': self.get_parameter(a_vamp, "channel3"), '04': self.get_parameter(a_vamp, "channel4"),
	    '05': self.get_parameter(a_vamp, "channel5"), '06': self.get_parameter(a_vamp, "channel6")}

            # create vamp device and open it
            try:
                mprsg6zvamp = Mprsg6zVamp(self.log, vamp_name, vamp_channels, vamp_device)
		mprsg6zvamp.open()
            except Mprsg6zException as e:
                self.log.error(e.value)
                print(e.value)
                self.force_leave()
                return
	    
	    # we have to find the mprsg6z.vzone devices used by this mprsg6zvamp instance
	    self.liste_vzone = (b_device for b_device in self.devices if b_device["device_type_id"] == "mprsg6z.vzone")
	    liste_goodvzone = (c_device for c_device in self.liste_vzone if self.get_parameter(c_device, "mprsg6zvamp") == vamp_name)
	    # for each good vzone found :
	    for a_vzone in liste_goodvzone:
	        vzone_name = a_vzone["name"]
		vzone_id = a_vzone["id"]
		vzone_type = a_vzone["device_type_id"]
		vzone_childs = self.get_parameter(a_vzone, "childs")
		the_childs = vzone_childs.split(",") 
		# create vzone device
		try:
		    mprsg6zvzone = Mprsg6zVzone(self.log, vzone_name, mprsg6zvamp, the_childs)
		    mprsg6zvzone.threadVzone()
                except Mprsg6zException as e:
                    self.log.error(e.value)
                    print(e.value)
                    self.force_leave()
                    return
	       
    # -------------------------------------------------------------------------------------------------
    def send_pub_data(self, device_id, value):
        """ Send the sensors values over MQ
        """
        data = {}
        for sensor in self.sensors[device_id]:                  # "for" nécessaire pour les 2 sensors counter : '1-wire counter diff' et '1-wire counter'
            data[self.sensors[device_id][sensor]] = value       # sensor = sensor name in info.json file
        self.log.debug(u"==> Update Sensor '%s' for device id %s (%s)" % (format(data), device_id, self.device_list[device_id]["name"]))    # {u'id': u'value'}

        try:
            self._pub.send_event('client.sensor', data)
        except:
            # We ignore the message if some values are not correct
            self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
            pass


    # -------------------------------------------------------------------------------------------------
    def on_mdp_request(self, msg):
        """ Called when a MQ req/rep message is received
        """
        Plugin.on_mdp_request(self, msg)
        # self.log.info(u"==> Received 0MQ messages: %s" % format(msg))
        if msg.get_action() == "client.cmd":
            reason = None
            status = True
            data = msg.get_data()
            
            device_id = data["device_id"]
            command_id = data["command_id"]
            if device_id not in self.device_list:
                self.log.error(u"### MQ REQ command, Device ID '%s' unknown, Have you restarted the plugin after device creation ?" % device_id)
                status = False
                reason = u"Plugin onewired: Unknown device ID %d" % device_id
                self.send_rep_ack(status, reason, command_id, "unknown") ;                      # Reply MQ REP (acq) to REQ command
                return

            device_name = self.device_list[device_id]["name"]
            self.log.info(u"==> Received for device '%s' MQ REQ command message: %s" % (device_name, format(data)))         # {u'command_id': 70, u'value': u'1', u'device_id': 169}

            status, reason = self.onewire.writeSensor(self.device_list[device_id]["address"], self.device_list[device_id]["properties"], data["value"])
            if status:
                self.send_pub_data(device_id, data["value"])    # Update sensor command.
            
            # Reply MQ REP (acq) to REQ command
            self.send_rep_ack(status, reason, command_id, device_name) ;

    # -------------------------------------------------------------------------------------------------
    def send_rep_ack(self, status, reason, cmd_id, dev_name):
        """ Send MQ REP (acq) to command
        """
        self.log.info(u"==> Reply MQ REP (acq) to REQ command id '%s' for device '%s'" % (cmd_id, dev_name))
        reply_msg = MQMessage()
        reply_msg.set_action('client.cmd.result')
        reply_msg.add_data('status', status)
        reply_msg.add_data('reason', reason)
        self.reply(reply_msg.get())


if __name__ == "__main__":
    Mprsg6zManager()
