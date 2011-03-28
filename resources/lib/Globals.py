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
import os
import xbmcaddon, xbmc


def log(msg, level = xbmc.LOGDEBUG):
    xbmc.log(ADDON_ID + '-' + msg, level)


ADDON_ID = 'script.tvtime'
ADDON_VERSION = '1.0.14'
ADDON_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_INFO = ADDON_SETTINGS.getAddonInfo('path')

TIMEOUT = 15 * 1000

IMAGES_LOC = xbmc.translatePath(os.path.join(ADDON_INFO, 'resources', 'images')) + '/'

if ADDON_SETTINGS.getSetting("CustomChannelLogoFolder") == "true":
    if ADDON_SETTINGS.getSetting("ChannelLogoFolder") == "":
        LOGOS_LOC = xbmc.translatePath(os.path.join(ADDON_INFO, 'resources', 'logos')) + '/'
    else:
        LOGOS_LOC = xbmc.translatePath(ADDON_SETTINGS.getSetting("ChannelLogoFolder")) + '/'
else:
    LOGOS_LOC = xbmc.translatePath(os.path.join(ADDON_INFO, 'resources', 'logos')) + '/'


CHANNELS_LOC = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache/')
PRESETS_LOC = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets/')

TIME_BAR = 'pstvTimeBar.png'
BUTTON_FOCUS = 'pstvButtonFocus.png'
BUTTON_NO_FOCUS = 'pstvButtonNoFocus.png'

ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4
ACTION_PAGEUP = 5
ACTION_PAGEDOWN = 6
ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = 10
ACTION_SHOW_INFO = 11
ACTION_PAUSE = 12
ACTION_STOP = 13
ACTION_NEXT_ITEM = 14
ACTION_PREV_ITEM = 15
ACTION_STEP_FOWARD = 17
ACTION_STEP_BACK = 18
ACTION_BIG_STEP_FORWARD = 19
ACTION_BIG_STEP_BACK = 20
ACTION_OSD = 21
ACTION_NUMBER_0 = 58
ACTION_NUMBER_1 = 59
ACTION_NUMBER_2 = 60
ACTION_NUMBER_3 = 61
ACTION_NUMBER_4 = 62
ACTION_NUMBER_5 = 63
ACTION_NUMBER_6 = 64
ACTION_NUMBER_7 = 65
ACTION_NUMBER_8 = 66
ACTION_NUMBER_9 = 67
ACTION_PLAYER_FORWARD = 73
ACTION_PLAYER_REWIND = 74
ACTION_PLAYER_PLAY = 75
ACTION_PLAYER_PLAYPAUSE = 76
#ACTION_MENU = 117
ACTION_MENU = 7
ACTION_INVALID = 999
