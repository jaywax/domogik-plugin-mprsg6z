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

        # get the devices, sensors and command lists
        self.devices = self.get_device_list(quit_if_no_device=True)
	self.sensors = self.get_sensors(self.devices)
	self.commands = self.get_commands(self.devices)
        self.log.debug(u"= = = > device: {0}".format(self.devices))
        self.log.debug(u"= = = > sensors: {0}".format(self.sensors))
        self.log.debug(u"= = = > commands: {0}".format(self.commands))

	# get config keys for the vamp
        mprsg6z_device = str(self.get_config('device'))
        mprsg6z_channel1 = self.get_config('channel1')
        mprsg6z_channel2 = self.get_config('channel2')
        mprsg6z_channel3 = self.get_config('channel3')
        mprsg6z_channel4 = self.get_config('channel4')
        mprsg6z_channel5 = self.get_config('channel5')
        mprsg6z_channel6 = self.get_config('channel6')
	mprsg6z_channels = {'01' : mprsg6z_channel1, '02' : mprsg6z_channel2, '03' : mprsg6z_channel3, '04' : mprsg6z_channel4, 
	'05' : mprsg6z_channel5, '06' : mprsg6z_channel6}

        # create vamp device and open it
        try:
            self.mprsg6zvamp = Mprsg6zVamp(self.log, mprsg6z_channels, mprsg6z_device)
	    self.mprsg6zvamp.open()
        except Mprsg6zException as e:
            self.log.error(e.value)
            print(e.value)
            self.force_leave()
            return

        self.device_list = {}
        thread_sensors = None
	# for each vzone device
        for a_device in self.devices:
	    # get config keys for vzone
            device_name = a_device["name"]
            device_id = a_device["id"]
            device_type = a_device["device_type_id"]
            device_childs = self.get_parameter(a_device, "childs")
	    # next release : to_sync parameter
	    #device_tosync = {'VO' : self.get_parameter(a_device, "VO"), 'CH' : self.get_parameter(a_device, "CH"), 'BS' : self.get_parameter(a_device, "BS"), 'TR' : self.get_parameter(a_device, "TR"),
	    #'BL' : self.get_parameter(a_device, "BL"), 'MU' : self.get_parameter(a_device, "MU"), 'DT' : self.get_parameter(a_device, "DT")}
            #self.device_list.update({device_id : {'name': device_name, 'childs': device_childs, 'tosync' : device_tosync}})
            self.device_list.update({device_id : {'name': device_name, 'childs': device_childs}})
	    # next release : to_sync parameter
	    #self.mprsg6zvamp.vzone_add(device_id, device_name, device_childs, device_tosync)
	    self.mprsg6zvamp.vzone_add(device_id, device_name, device_childs)
	thread_sensors = threading.Thread(None,
        				self.mprsg6zvamp.loop_vzones_update,
        				'Main_reading_vzones',
        				(self.send_pub_data, self.get_stop()),
        				{})
        thread_sensors.start()
        self.register_thread(thread_sensors)
        self.ready()

    # -------------------------------------------------------------------------------------------------

    def send_pub_data(self, device_id, value):
        """ 
	Send the sensors values over MQ
        """
        data = {}
	# data must be split 
	sensor = value[0]
	valeur = value[1]
        data[self.sensors[device_id][sensor]] = valeur
        self.log.debug(u"= = = > Update Sensor {0}:{1} for device id {2} ({3})".format(sensor,valeur,device_id,self.device_list[device_id]["name"]))

        try:
            self._pub.send_event('client.sensor', data)
        except:
            # We ignore the message if some values are not correct
            self.log.debug(u"= = = > Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
            pass

    # -------------------------------------------------------------------------------------------------

    def on_mdp_request(self, msg):
        """ 
	Called when a MQ req/rep message is received

	Keyword arguments:
        msg -- message received from MQ
        """
        Plugin.on_mdp_request(self, msg)
        if msg.get_action() == "client.cmd":
            reason = None
            status = True
            data = msg.get_data()

            device_id = data["device_id"]
            command_id = data["command_id"]
	    z = ["device_id","command_id"]
	    param = list(set(data)-set(z))[0]
            if device_id not in self.device_list:
                self.log.error(u"# # # MQ REQ command, Device ID {0} unknown, Have you restarted the plugin after device creation ?".format(device_id))
                status = False
                reason = u"Plugin mprsg6z: Unknown device ID {0}".format(device_id)
                self.send_rep_ack(status, reason, command_id, "unknown") ;                      # Reply MQ REP (acq) to REQ command
                return

            device_name = self.device_list[device_id]["name"]
            self.log.debug(u"= = = > Received for device {0} MQ REQ command message: {1}".format(device_name, data))         # {u'command_id': 70, u'value': u'1', u'device_id': 169}

            status, reason = self.mprsg6zvamp.vzone_set_one_command(device_id, param, data[param])
            if status:
		if param not in 'PO':
                    self.send_pub_data(device_id, (param,data[param]))    # Update sensor command.
	        else:
		    self.mprsg6zvamp.vzone_update_status(self.send_pub_data) # Force Update of zones

            # Reply MQ REP (acq) to REQ command
            self.send_rep_ack(status, reason, command_id, device_name) ;


    # -------------------------------------------------------------------------------------------------

    def send_rep_ack(self, status, reason, cmd_id, dev_name):
        """ 
	Send MQ REP (acq) to command

	Keyword arguments:
	status -- The status of the ack
	reason -- The reason of the ack
	cmd_id -- The cmd_id for log use
	dev_name -- The neme of the dev for log use
        """
        self.log.info(u"= = > Reply MQ REP (acq) to REQ command id {0} for device {0}".format(cmd_id, dev_name))
        reply_msg = MQMessage()
        reply_msg.set_action('client.cmd.result')
        reply_msg.add_data('status', status)
        reply_msg.add_data('reason', reason)
        self.reply(reply_msg.get())


if __name__ == "__main__":
    Mprsg6zManager()
