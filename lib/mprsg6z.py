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
    Construct the mpr6zhmaut line
    """
    def __init__(self, log, laddress, dev='/dev/ttyUSB0', nb_amp='1'):
        """
        Create mpr6zhmaut line instance, allowing to use amp and zone
        @laddress : unique identifier of the line
        @param dev : device where the interface is connected to
        default '/dev/ttyUSB0'
        @nb_amp : number of amp to handle on this line
        default '1'
        """

        self.log = log
        self.laddress = laddress
        self._dev = dev
        self.nb_amp = nb_amp

class Mpr6zhmautAmp(Mpr6zhmautLine):
    """
    Construct the mpr6zhmaut amp from the class Mpr6zhmautLine
    """
    def __init__(self, aaddress, params):
        """
        Create mpr6zhmaut amp instance
        """

        self.aaddress = Mpr6zhmautLine.laddress + "toto"
        
