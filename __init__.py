# -*- coding: utf-8 -*-
"""
 Copyright 2008 Spike^ekipS <spikeekips@gmail.com>

	This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

"""
To run Django search with Lucene in Django, exactly thread environment, you sould initialize lucene(JAVA) VM, so we must connect 'request_started' and 'request_finished'.

But when the 'request_finished' was connected, some weired error occured and the entire server was corrupted.
"""

import sys

import signals

if not hasattr(sys, "SIGNAL_CONNECTED") :
    sys.SIGNAL_CONNECTED = False

if not sys.SIGNAL_CONNECTED :
    signals.Signals.connect("request_started")
    #signals.Signals.connect("request_finished")


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"
__version__=  "0.1"
__nonsense__ = ""






