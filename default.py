#   Copyright (C) 2011 Jason Anderson
#
#
# This file is part of PseudoTV.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Modified by James A. Tucker for TVTime
#
#

import sys
import os
import xbmc
import xbmcaddon


# Script constants
__scriptname__ = "TVTime"
__author__     = "jtucker1972"
__url__        = "http://github.com/jtucker1972/XBMC-TVTime"
__version__    = "1.0.14"
__settings__   = xbmcaddon.Addon(id='script.tvtime')
__language__   = __settings__.getLocalizedString
__cwd__        = __settings__.getAddonInfo('path')


import resources.lib.Overlay as Overlay


MyOverlayWindow = Overlay.TVOverlay("script.pseudotv.TVOverlay.xml", __cwd__, "default")
del MyOverlayWindow
