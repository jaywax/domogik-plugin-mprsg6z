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


        # get the devices list
        self.devices = self.get_device_list(quit_if_no_device=True)
	self.sensors = self.get_sensors(self.devices)
	self.commands = self.get_commands(self.devices)
        self.log.info(u"==> device:   %s" % format(self.devices))
        self.log.info(u"==> sensors:   %s" % format(self.sensors))
        self.log.info(u"==> commands:   %s" % format(self.commands))

	# ### get all config keys
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

	# for each vzone
        self.device_list = {}
        thread_sensors = None
        for a_device in self.devices:
            device_name = a_device["name"]
            device_id = a_device["id"]
            device_type = a_device["device_type_id"]
            device_childs = self.get_parameter(a_device, "childs")
            self.device_list.update({device_id : {'name': device_name, 'childs': device_childs}})
	    self.mprsg6zvamp.add_vzone(device_id,device_name,device_childs)
	thread_sensors = threading.Thread(None,
        				self.mprsg6zvamp.loop_read_vzones,
        				'Main_reading_vzones',
        				(self.send_pub_data, self.get_stop()),
        				{})
        thread_sensors.start()
        self.register_thread(thread_sensors)
        self.ready()

    # -------------------------------------------------------------------------------------------------

    def send_pub_data(self, device_id, value):
        """ Send the sensors values over MQ
        """
        data = {}
	sensor = value[0]
	valeur = value[1]
	if sensor == 'PR':
	    sensor = 'STATUS'
        data[self.sensors[device_id][sensor]] = valeur       # sensor = sensor name in info.json file
        self.log.debug(u"==> Update Sensor {0}:{1} for device id {2} ({3})".format(sensor,valeur,device_id,self.device_list[device_id]["name"]))    # {u'id': u'value'}

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
	    z = ["device_id","command_id"]
	    param = list(set(data)-set(z))[0]
            if device_id not in self.device_list:
                self.log.error(u"### MQ REQ command, Device ID '%s' unknown, Have you restarted the plugin after device creation ?" % device_id)
                status = False
                reason = u"Plugin onewired: Unknown device ID %d" % device_id
                self.send_rep_ack(status, reason, command_id, "unknown") ;                      # Reply MQ REP (acq) to REQ command
                return

            device_name = self.device_list[device_id]["name"]
            self.log.info(u"==> Received for device '%s' MQ REQ command message: %s" % (device_name, format(data)))         # {u'command_id': 70, u'value': u'1', u'device_id': 169}

            status, reason = self.mprsg6zvamp.setVzoneOneParam(device_id, param, data[param])
            if status:
                self.send_pub_data(device_id, (param,data[param]))    # Update sensor command.

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
