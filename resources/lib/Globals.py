#   Copyright (C) 2011 James A. Tucker
#
#
# This file is part of TV Time.
#
# TV Time is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TV Time is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TV Time.  If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import xbmcaddon, xbmc
import Settings

#
# Shared Settings Across Modules
#
ADDON_ID = 'script.tvtime'
ADDON_SETTINGS = Settings.Settings()
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_INFO = REAL_SETTINGS.getAddonInfo('path')

VERSION = "2.0.1"
REAL_SETTINGS.setSetting("Version",VERSION)

TIMEOUT = 15 * 1000
TOTAL_FILL_CHANNELS = 20

MODE_RESUME = 1
MODE_ALWAYSPAUSE = 2
MODE_ORDERAIRDATE = 4
MODE_RANDOM = 8
MODE_REALTIME = 16
MODE_SERIAL = MODE_RESUME | MODE_ALWAYSPAUSE | MODE_ORDERAIRDATE
MODE_STARTMODES = MODE_RANDOM | MODE_REALTIME | MODE_RESUME
MODE_UNWATCHED = 1
MODE_NOSPECIALS = 1
MODE_RANDOM_FILELISTS = 1

NUMBER_CHANNEL_TYPES = 10

IMAGES_LOC = xbmc.translatePath(os.path.join(ADDON_INFO, 'resources', 'images')) + '/'
PRESETS_LOC = xbmc.translatePath(os.path.join(ADDON_INFO, 'resources', 'presets')) + '/'
CHANNELS_LOC = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache/')
GEN_CHAN_LOC = os.path.join(CHANNELS_LOC, 'generated') + '/'
PRESTAGE_LOC = os.path.join(CHANNELS_LOC, 'prestaged') + '/'
TEMP_LOC = os.path.join(CHANNELS_LOC, 'temp') + '/'
META_LOC = os.path.join(CHANNELS_LOC, 'meta') + '/'
FEED_LOC = os.path.join(CHANNELS_LOC, 'feeds') + '/'
#FEED_LOC = os.path.join(ADDON_INFO, 'feeds') + '/'

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
ACTION_OSD = 122
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

#
# used for program control
#
prestageThreadExit = 0
savingSettings = 0
exitingTVTime = 0
autoResetChannelActive = 0
forceChannelResetActive = 0
userExit = 0
channelsReset = 0
resetSettings2 = 0
resetPrestage = 0


################################################################
################################################################
#
# Migration Code
#
################################################################
################################################################

def migrate():
    log("migration")
    curver = "0.0.0"
    
    try:
        curver = REAL_SETTINGS.getSetting("Version")
    except:
        pass

    if curver == "":
        # migrate 1.0 to 2.0
        # delete channels.xml
        channelSettingsFile = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/channels.xml')
        if os.path.exists(channelSettingsFile):
            try:
                os.remove(channelSettingsFile)
            except:
                self.log("Unable to delete " + str(channelSettingsFile))
        # delete presets directory
        presetsFolder = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets/')
        if os.path.exists(presetsFolder):
            try:
                shutil.rmtree(presetsFolder)
            except:
                self.log("Unable to delete " + str(presetsFolder))
                
        # delete cache directory
        cacheFolder = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache/')
        if os.path.exists(cacheFolder):
            try:
                shutil.rmtree(cacheFolder)
            except:
                self.log("Unable to delete " + str(cacheFolder))

        # migrate settings
        # version 1.0 Settings
        AutoOff = REAL_SETTINGS.getSetting("AutoOff")
        ChannelLogoFolder = REAL_SETTINGS.getSetting("ChannelLogoFolder")
        ChannelResetSetting = REAL_SETTINGS.getSetting("ChannelResetSetting")
        ChannelResetSettingTime = REAL_SETTINGS.getSetting("ChannelResetSettingTime")
        CurrentChannel = REAL_SETTINGS.getSetting("CurrentChannel")
        ForceChannelReset = REAL_SETTINGS.getSetting("ForceChannelReset")
        InfoOnChange = REAL_SETTINGS.getSetting("InfoOnChange")
        LastResetTime = REAL_SETTINGS.getSetting("LastResetTime")
        ShowChannelBug = REAL_SETTINGS.getSetting("ShowChannelBug")
        maxbumpers = REAL_SETTINGS.getSetting("maxbumpers")
        maxcommercials = REAL_SETTINGS.getSetting("maxcommercials")
        maxtrailers = REAL_SETTINGS.getSetting("maxtrailers")
        numbumpers = REAL_SETTINGS.getSetting("numbumpers")
        numcommercials = REAL_SETTINGS.getSetting("numcommercials")
        numtrailers = REAL_SETTINGS.getSetting("numtrailers")
        trailers = REAL_SETTINGS.getSetting("trailers")
        trailersfolder = REAL_SETTINGS.getSetting("trailersfolder")
        commercials = REAL_SETTINGS.getSetting("commercials")
        commercialsfolder = REAL_SETTINGS.getSetting("commercialsfolder")
        bumpers = REAL_SETTINGS.getSetting("bumpers")
        bumpersfolder = REAL_SETTINGS.getSetting("bumpersfolder")

        # delete settings.xml
        settingsFile = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/settings.xml')
        if os.path.exists(settingsFile):
            try:
                os.remove(settingsFile)
            except:
                self.log("Unable to delete " + str(settingsFile))

        # create version 2.0 settings.xml
        REAL_SETTINGS.setSetting("AutoOff",AutoOff)
        REAL_SETTINGS.setSetting("ChannelLogoFolder",ChannelLogoFolder)
        REAL_SETTINGS.setSetting("CurrentChannel",CurrentChannel)
        REAL_SETTINGS.setSetting("ForceChannelReset",ForceChannelReset)
        REAL_SETTINGS.setSetting("InfoOnChange",InfoOnChange)
        REAL_SETTINGS.setSetting("LastResetTime",LastResetTime)
        REAL_SETTINGS.setSetting("ShowChannelBug",ShowChannelBug)
        REAL_SETTINGS.setSetting("Version",VERSION)
        REAL_SETTINGS.setSetting("XBMC-Version",0)

        REAL_SETTINGS.setSetting("autoChannelReset","false")

        if ChannelResetSetting > 0 and ChannelResetSetting < 4:
            # autoChannelResetSetting = 4
            REAL_SETTINGS.setSetting("autoChannelResetSetting","4") # Scheduled
            if ChannelResetSetting == 1: # Every Day
                REAL_SETTINGS.setSetting("autoChannelResetInterval","0") # Daily
            if ChannelResetSetting == 2: # Every Week
                REAL_SETTINGS.setSetting("autoChannelResetInterval","0") # Weekly
            if ChannelResetSetting == 3: # Every Month
                REAL_SETTINGS.setSetting("autoChannelResetInterval","0") # Monthly
        REAL_SETTINGS.setSetting("autoChannelResetTime",ChannelResetSettingTime)           
        REAL_SETTINGS.setSetting("autoChannelResetShutdown","false")

        REAL_SETTINGS.setSetting("autoFindNetworks","false")
        REAL_SETTINGS.setSetting("autoFindStudios","false")
        REAL_SETTINGS.setSetting("autoFindTVGenres","false")
        REAL_SETTINGS.setSetting("autoFindMovieGenres","false")
        REAL_SETTINGS.setSetting("autoFindMusicGenres","false")
        REAL_SETTINGS.setSetting("autoFindLive","false")
        REAL_SETTINGS.setSetting("limit","0")

        REAL_SETTINGS.setSetting("offair","false")
        REAL_SETTINGS.setSetting("offairfile","")

        REAL_SETTINGS.setSetting("bumpers",bumpers)
        REAL_SETTINGS.setSetting("bumpersfolder",bumpersfolder)
        REAL_SETTINGS.setSetting("numbumpers",numbumpers)
        REAL_SETTINGS.setSetting("maxbumpers",maxbumpers)

        REAL_SETTINGS.setSetting("commercials",commercials)
        REAL_SETTINGS.setSetting("commercialsfolder",commercialsfolder)
        REAL_SETTINGS.setSetting("numcommercials",numcommercials)
        REAL_SETTINGS.setSetting("maxcommercials",maxcommercials)

        REAL_SETTINGS.setSetting("trailers",trailers)
        REAL_SETTINGS.setSetting("trailersfolder",trailersfolder)
        REAL_SETTINGS.setSetting("numtrailers",numtrailers)
        REAL_SETTINGS.setSetting("maxtrailers",maxtrailers)
        
    REAL_SETTINGS.setSetting("Version", VERSION)
    

def log(msg, level = xbmc.LOGDEBUG):
    xbmc.log(ADDON_ID + '-' + msg, level)


