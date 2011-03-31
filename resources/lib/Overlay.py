#   Copyright (C) 2011 James A. Tucker
#
# This file is part of TV Time
#
#   Original Code: Copyright (C) 2011 Jason Anderson
#   Modified by James A. Tucker for TVTime
#
# TVTime is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TVTime is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading
import datetime
import sys, re
import random

from xml.dom.minidom import parse, parseString

from Playlist import Playlist
from Globals import *
from Channel import Channel
from EPGWindow import EPGWindow

from operator import itemgetter
from time import time, localtime, strftime, strptime, mktime, sleep
from datetime import datetime, date, timedelta
from VideoParser import VideoParser
from decimal import *
from PresetChannels import *

import glob

# overlay window to catch events and change channels
class TVOverlay(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.log('__init__')
        # initialize all variables
        self.channels = []
        self.inputChannel = -1
        self.channelLabel = []
        self.lastActionTime = 0
        self.actionSemaphore = threading.BoundedSemaphore()
        self.setCoordinateResolution(1)
        self.timeStarted = 0
        self.infoOnChange = True
        self.infoOffset = 0
        self.invalidatedChannelCount = 0
        self.showingInfo = False
        self.showChannelBug = False
        self.nextM3uChannelNum = 0
        self.getFileTries = 0
        self.getfile = ""
        random.seed()
        
        for i in range(3):
            self.channelLabel.append(xbmcgui.ControlImage(50 + (50 * i), 50, 50, 50, IMAGES_LOC + 'solid.png', colorDiffuse='0xAA00ff00'))
            self.addControl(self.channelLabel[i])
            self.channelLabel[i].setVisible(False)

        self.doModal()
        self.log('__init__ return')


    # override the doModal function so we can setup everything first
    def onInit(self):
        self.log('onInit')
        self.log('Version: ' + str(ADDON_VERSION))
        self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)
        self.infoTimer = threading.Timer(5.0, self.hideInfo)
        self.background = self.getControl(101)
        self.getControl(102).setVisible(False)
        self.resetChannelActive = False

        self.createChannelsDir()
        self.createPresetsDir()

        self.myEPG = EPGWindow("script.pseudotv.EPG.xml", ADDON_INFO, "default")
        self.videoParser = VideoParser()
        self.myEPG.MyOverlayWindow = self
        
        # Don't allow any actions during initialization
        self.actionSemaphore.acquire()

        # Read in general settings
        if self.readConfig() == False:
            return

        #
        #self.LiveChannels =LiveChannels()
        #self.LiveChannels.buildFoxNewsLive('87249')

        # set auto reset timer if enabled        
        if self.autoChannelReset:
            self.log("onInit: self.channelResetSetting = " + str(self.channelResetSetting))
            self.autoResetTimeValue = 0
            if self.channelResetSetting > 0 and self.channelResetSetting < 4:
                if ADDON_SETTINGS.getSetting('nextAutoResetDateTime') == "":
                    self.log("onInit: set next auto reset time")
                    self.setNextAutoResetTime()
                elif ADDON_SETTINGS.getSetting('nextAutoResetDateTimeInterval') <> ADDON_SETTINGS.getSetting('ChannelResetSetting'):
                    self.log("onInit: reset interval changed. update next auto reset time.")
                    self.setNextAutoResetTime()
                elif ADDON_SETTINGS.getSetting('nextAutoResetDateTimeResetTime') <> ADDON_SETTINGS.getSetting('ChannelResetSettingTime'):
                    self.log("onInit: reset time changed. update next auto reset time.")
                    self.setNextAutoResetTime()
                else:
                    self.log("onInit: no change in auto reset time.")            
                self.log("onInit: setting auto reset time")
                # set auto reset timer
                self.setAutoResetTimer()
                # start auto reset timer
                self.startAutoResetTimer()
        
        # check for force reset
        self.log("onInit: self.forceReset = " + str(self.forceReset))
        if self.forceReset == "1" or self.forceReset == "2":
            self.log("onInit: resetChannels")
            self.resetChannels()
        
        # store maximun number of channels created
        self.maxChannels = self.findMaxM3us()
        if self.maxChannels == 0:
            self.Error('Unable to find any channels.')
            return
        else:
            self.log('onInit: self.maxChannels = ' + str(self.maxChannels))

        # Load channel m3u files
        self.log("onInit: loadChannels ")
        self.loadChannels()

        # check for at least one valid channel
        if self.validateChannels() == False:
            self.Error("No valid channel data found")
        
        if self.sleepTimeValue > 0:
            self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

        try:
            if self.forceReset == False:
                self.currentChannel = self.fixChannel(int(ADDON_SETTINGS.getSetting("CurrentChannel")))
            else:
                self.currentChannel = self.fixChannel(1)
        except:
            self.currentChannel = self.fixChannel(1)

        self.resetChannelTimes()
        self.setChannel(self.currentChannel)
        self.timeStarted = time()
        self.background.setVisible(False)
        self.startSleepTimer()
        self.actionSemaphore.release()        
        self.log('onInit return')


    # setup all basic configuration parameters, including creating the playlists that
    # will be used to actually run this thing
    def readConfig(self):
        self.log("readConfig: Started")
        self.updateDialog = xbmcgui.DialogProgress()
        # Sleep setting is in 30 minute incriments...so multiply by 30, and then 60 (min to sec)
        self.sleepTimeValue = int(ADDON_SETTINGS.getSetting('AutoOff')) * 1800
        self.log('Auto off is ' + str(self.sleepTimeValue))
        self.forceReset = ADDON_SETTINGS.getSetting('ForceChannelReset')
        self.log('Force Reset is ' + str(self.forceReset))
        self.autoChannelReset = ADDON_SETTINGS.getSetting("autoChannelReset") == "true"
        self.log('Auto Channel Reset is ' + str(self.autoChannelReset))
        self.infoOnChange = ADDON_SETTINGS.getSetting("InfoOnChange") == "true"
        self.log('Show info label on channel change is ' + str(self.infoOnChange))
        self.channelResetSetting = int(ADDON_SETTINGS.getSetting("ChannelResetSetting"))
        self.log('Channel Reset Setting is ' + str(self.channelResetSetting))
        self.channelResetSettingTime = int(ADDON_SETTINGS.getSetting("ChannelResetSettingTime"))
        self.log('Channel Reset Setting Time is ' + str(self.channelResetSettingTime))
        self.showChannelBug = ADDON_SETTINGS.getSetting("ShowChannelBug") == "true"
        self.log('Show channel bug - ' + str(self.showChannelBug))
        try:
            self.lastResetTime = int(ADDON_SETTINGS.getSetting("LastResetTime"))
        except:
            self.lastResetTime = 0

        self.commercials = ADDON_SETTINGS.getSetting("commercials") == "true"
        self.log('TV Commercials Enabled - ' + str(self.commercials))
        self.numCommercials = ADDON_SETTINGS.getSetting("numcommercials") 
        self.log('Number of Commercials Between TV Files - ' + str(self.numCommercials))
        self.maxCommercials = int(ADDON_SETTINGS.getSetting("maxcommercials")) + 1
        self.log('Max Number of Commercials Between TV Files - ' + str(self.maxCommercials))
        self.commercialsFolder = ADDON_SETTINGS.getSetting("commercialsfolder")
        self.log('TV Commercials Folder - ' + str(self.commercialsFolder))

        self.bumpers = ADDON_SETTINGS.getSetting("bumpers") == "true"
        self.log('TV Bumpers Enabled - ' + str(self.bumpers))
        self.numBumpers = ADDON_SETTINGS.getSetting("numbumpers")
        self.log('Number of Bumpers Between TV Files - ' + str(self.numBumpers))
        self.maxBumpers = int(ADDON_SETTINGS.getSetting("maxbumpers")) + 1
        self.log('Max Number of Bumpers Between TV Files - ' + str(self.maxBumpers))
        self.bumpersFolder = ADDON_SETTINGS.getSetting("bumpersfolder")
        self.log('TV Bumpers Folder - ' + str(self.bumpersFolder))

        self.trailers = ADDON_SETTINGS.getSetting("trailers") == "true"
        self.log('Movie Trailers Enabled - ' + str(self.trailers))
        self.numTrailers = ADDON_SETTINGS.getSetting("numtrailers")
        self.log('Number of Trailers Between Movie Files - ' + str(self.numTrailers))
        self.maxTrailers = int(ADDON_SETTINGS.getSetting("maxtrailers")) + 1
        self.log('Max Number of Trailers Between Movie Files - ' + str(self.maxTrailers))
        self.trailersFolder = ADDON_SETTINGS.getSetting("trailersfolder")
        self.log('Trailers Folder - ' + str(self.trailersFolder))

        self.log("readConfig: Completed")


    def setNextAutoResetTime(self):
        # set next auto resetChannel time
        # need to get current datetime in local time
        currentDateTimeTuple = localtime()
        # parse out year, month and day so we can computer resetDate
        cd = datetime(*(currentDateTimeTuple[0:6]))
        year = cd.strftime('%Y')
        month = cd.strftime('%m')
        day = cd.strftime('%d')
        hour = cd.strftime('%H')
        minutes = cd.strftime('%M')
        seconds = cd.strftime('%S')
        # convert to date object so we can add timedelta in the next step
        currentDateTime = year + "-" + month + "-" + day + " " + hour + ":" + minutes + ":" + seconds
        self.log("setNextAutoResetTime: currentDateTime=" + str(currentDateTime))
        currentDateTimeTuple = strptime(currentDateTime,"%Y-%m-%d %H:%M:%S")
        self.log("setNextAutoResetTime: currentDateTimeTuple=" + str(currentDateTimeTuple))
        currentDate = date(int(year), int(month), int(day))
        self.log("setNextAutoResetTime: currentDate=" + str(currentDate))
        # need to get setting of when to auto reset
        # Automatic|Every Day|Every Week|Every Month|Never
        # 0 = Automatic
        # 1 = Daily
        # 2 = Weekly
        # 3 = Monthly
        # 4 = Never
        # Daily = Current Date + 1 Day
        # Weekly = CUrrent Date + 1 Week
        # Monthly = CUrrent Date + 1 Month
        resetInterval = ADDON_SETTINGS.getSetting("ChannelResetSetting")
        # Time to Reset: 12:00am, 1:00am, 2:00am, etc.
        # get resetTime setting
        resetTime = ADDON_SETTINGS.getSetting("ChannelResetSettingTime")
        self.log("setNextAutoResetTime: resetInterval=" + str(resetInterval))
        self.log("setNextAutoResetTime: resetTime=" + str(resetTime))

        if resetInterval == "1":
            # Daily
            interval = timedelta(days=1)
        elif resetInterval == "2":
            # Weekly
            interval = timedelta(days=7)
        elif resetInterval == "3":
            # Monthly
            interval = timedelta(days=30)

        # determine resetDate based on current date and interval
        if resetTime > hour and resetInterval == "1":
            resetDate = currentDate
        else:
            resetDate = currentDate + interval        
        
        # need to convert to tuple to be able to parse out components
        resetDateTuple = strptime(str(resetDate), "%Y-%m-%d")
        # parse out year, month, and day
        rd = datetime(*(resetDateTuple[0:3]))
        year = rd.strftime('%Y')
        month = rd.strftime('%m')
        day = rd.strftime('%d')
        # set hour, minutes and seconds
        hour = resetTime
        minutes = 0
        seconds = 0
        # join components together to form reset date and time
        resetDateTime = str(year) + "-" + str(month) + "-" + str(day) + " " + str(hour) + ":" + str(minutes) + ":" + str(seconds)
        # save next resetDateTime to settings
        self.log("setNextAutoResetTime: nextAutoResetDateTime: " + str(resetDateTime))
        ADDON_SETTINGS.setSetting('nextAutoResetDateTime', str(resetDateTime))        
        ADDON_SETTINGS.setSetting('nextAutoResetDateTimeInterval', str(resetInterval))        
        ADDON_SETTINGS.setSetting('nextAutoResetDateTimeResetTime', str(resetTime))        
        

    def setAutoResetTimer(self):
        # set next auto resetChannel time
        # need to get current datetime in local time
        currentDateTimeTuple = localtime()       
        nextAutoResetDateTime = ADDON_SETTINGS.getSetting('nextAutoResetDateTime')
        nextAutoResetDateTimeTuple = strptime(nextAutoResetDateTime,"%Y-%m-%d %H:%M:%S")
        self.log("setResetTimer: currentDateTimeTuple: " + str(currentDateTimeTuple))
        self.log("setResetTimer: nextAutoResetDateTimeTuple: " + str(nextAutoResetDateTimeTuple))
        
        # need to get difference between the two
        self.autoResetTimeValue = mktime(nextAutoResetDateTimeTuple) - mktime(currentDateTimeTuple)
        self.log("setResetTimer: resetTimerDiff: " + str(self.autoResetTimeValue))
        
        # set timer
        self.log("setResetTimer: Setting Timer for " + str(self.autoResetTimeValue) + " seconds")
        self.autoResetTimer = threading.Timer(self.autoResetTimeValue, self.autoResetChannels)


    def buildPlaylists(self):
        self.log("buildPlaylists: Started")
        # Give some feedback to the user
        self.loadDialog = xbmcgui.DialogProgress()
        self.loadDialog.create("TV Time", "Preparing for Playlist Creation")
        self.loadDialog.update(25, "Preparing for Playlist Creation")        
        # Setup Preset Channel Object
        self.presetChannels = presetChannels()
        # Auto Fill Custom Config channels
        if ADDON_SETTINGS.getSetting("autoFillCustom") == "true":
            self.loadDialog.update(50, "Auto Filling Custom Channels")
            self.log("buildPlaylists: Auto Filling Custom Channels")
            self.presetChannels.fillCustomChannels()        
        # Load Preset Channels from configuration settings
        self.loadDialog.update(75, "Reading Channel Management Settings")
        self.log("buildPlaylists: Reading Channel Management Settings")
        self.presetChannels.readPresetChannelConfig()
        # Delete Previous Channels
        self.presetChannels.deletePresetChannels()
        # Get total number of Preset Channels (maxChannels)
        self.numPresetChannels = self.presetChannels.findMaxPresetChannels()
        self.loadDialog.update(100, "Playlist Creation Prep Complete")
        self.log("buildPlaylists: Playlist Creation Prep Complete")
        # If the user pressed cancel, stop everything and exit
        if self.loadDialog.iscanceled():
            self.log("buildPlaylists: Playlist Creation Cancelled")
            self.loadDialog.close()
            self.end()
            return False
        self.loadDialog.close()        
        # Build the Preset Channel Playlists
        self.log("buildPlaylists: Build Preset Channel Playlists")
        self.presetChannels.buildPresetChannels(self.numPresetChannels)
        self.log("buildPlaylists: Completed")

#
# on forceReset, load new playlists and call buildChannel to create m3u
#
    def loadPlaylists(self):
        self.log("loadPlaylists: Started")
        self.startupTime = time()
        self.updateDialog.create("TV Time", "Building Channels")
        self.updateDialog.update(0, "Building Channels","","")
        self.log("loadPlaylists: Building Channels")
        self.background.setVisible(True)
        self.channelList = []
        getcontext().prec = 4
        progressIncrement = Decimal(100) / Decimal(self.numPresetChannels)
        self.updateProgressPercentage = 0
        # Go through all channels, create their arrays, and setup the new playlist
        playlistNum = 0
        for playlistNum in range(self.numPresetChannels):
            if not self.updateDialog.iscanceled():
                playlistNum = playlistNum + 1
                channelName = str(self.getSmartPlaylistName(self.getSmartPlaylistFilename(playlistNum)))
                self.updateProgressPlaylistNum = playlistNum # referenced when updating the dialog window in other functions
                self.updateProgressPercentage = Decimal(self.updateProgressPercentage) + Decimal(progressIncrement)
                self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(playlistNum) + ": " + str(channelName),"","")
                self.log("loadPlaylists: Building Channel " + str(playlistNum))
                self.channels.append(Channel())
                self.buildChannel(playlistNum)

        # If the user pressed cancel, stop everything and exit
        if self.updateDialog.iscanceled():
            self.log('loadPlaylists: Build Channels Cancelled')
            self.updateDialog.close()
            self.end()
            return False

        # write channelList settings to xml file for reference when rebuilding a channel
        self.log("loadPlaylists: length of channelList: " + str(len(self.channelList)))
        self.buildChannelsXML(self.channelList)

        self.updateDialog.update(100, "Build complete","","")
        self.log("loadPlaylists: Build complete")
        xbmc.Player().stop()
        self.updateDialog.close()
        self.log("loadPlaylists: Completed")
        return True


#
# loops through all the created m3u's and calls loadChannel
#
    def loadChannels(self):
        self.log("loadChannels: Started")
        self.startupTime = time()
        self.updateDialog.create("TV Time", "Loading channel list")
        self.updateDialog.update(0, "Loading channel list","","")
        self.log("loadChannels: Loading channel list")
        self.background.setVisible(True)
        # Go through all channels, create their arrays, and setup the new playlist
        getcontext().prec = 4
        progressIncrement = Decimal(100) / Decimal(self.maxChannels)
        progressPercentage = 0
        for m3uNum in range(self.maxChannels):
            self.log("loadChannels: Loading channel " + str(m3uNum))
            channelName = str(self.getSmartPlaylistName(self.getSmartPlaylistFilename(self.getChannelPlaylistNum(m3uNum))))
            self.log("loadChannels: channelName=" + str(channelName))
            progressPercentage = Decimal(progressPercentage) + Decimal(progressIncrement)
            self.updateDialog.update(progressPercentage, "Loading channel " + str(m3uNum), channelName,"")
            # create new channel
            self.channels.append(Channel())
            self.log("loadChannel: channel=" + str(m3uNum))
            self.loadChannel(m3uNum)
            # If the user pressed cancel, stop everything and exit
            if self.updateDialog.iscanceled():
                self.log('loadChannel: Update channels cancelled')
                self.updateDialog.close()
                self.end()
                return False
        self.forceReset = False

        self.updateDialog.update(100, "Load complete","","")
        self.log("loadChannel: Load complete")
        xbmc.Player().stop()
        self.updateDialog.close()
        self.log("loadChannels: Completed")
        return True

#
# load existing playlist for the channel, but check to see if reset is required
# if reset required call buildChannel
#
    def loadChannel(self, m3uNum):
        self.log("loadChannel: Started")
        returnval = False
        resetChannel = False
        channel = int(m3uNum - 1)
        self.log("loadChannel: m3uNum=" + str(m3uNum))
        self.log("loadChannel: channel=" + str(channel))
        self.log("loadChannel: channel file=" + CHANNELS_LOC + "channel_" + str(m3uNum) + ".m3u")
        # If possible, use an existing playlist
        if os.path.exists(CHANNELS_LOC + "channel_" + str(m3uNum) + ".m3u"):
            self.log("loadChannel: File Found")
            try:
                self.channels[channel].totalTimePlayed = int(ADDON_SETTINGS.getSetting('Channel_' + str(m3uNum) + '_time'))
                self.log("loadChannel: totalTimePlayed=" + str(self.channels[channel].totalTimePlayed))
                if self.channels[channel].setPlaylist(CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u') == True:
                    self.channels[channel].isValid = True
                    self.log("loadChannel: isValid=True")
                    self.channels[channel].fileName = CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u'
                    self.log("loadChannel: fileName=" + str(self.channels[channel].fileName))                    
                    self.log("loadChannel: playlistNum:" + str(self.getChannelPlaylistNum(m3uNum-1)))
                    self.log("loadChannel: playlistFilename: " + str(self.getSmartPlaylistFilename(self.getChannelPlaylistNum(m3uNum-1))))
                    self.log("loadChannel: channelName: " + str(self.getSmartPlaylistName(self.getSmartPlaylistFilename(self.getChannelPlaylistNum(m3uNum-1)))))
                    self.channels[channel].name = self.getSmartPlaylistName(self.getSmartPlaylistFilename(self.getChannelPlaylistNum(m3uNum-1)))
                    self.log("loadChannel: name=" + str(self.channels[channel].name))
                    returnval = True
                    # channelResetSetting:
                    # 0 = Automatic
                    # 1 = Every Day
                    # 2 = Every Week
                    # 3 = Every Month
                    # 4 = Never                    
                    if self.channelResetSetting == 0 and self.channels[channel].totalTimePlayed > self.channels[channel].getTotalDuration():
                        resetChannel = True
                        self.log("loadChannel: resetChannel=True")
            except:
                pass

        self.log("loadChannel: resetChannel=" + str(resetChannel))
        if resetChannel:
            self.log("loadChannel: Resetting Channels")
            self.resetChannels()
        self.log("loadChannel: Completed")


    # create new m3u for channel and initialize channel
    def buildChannel(self, playlistNum):
        self.log("buildChannel: Started")
        self.log("buildChannel: playlistNum=" + str(playlistNum))
        self.log("buildChannel: self.nextM3uChannelNum=" + str(self.nextM3uChannelNum))
        channelName = str(self.getSmartPlaylistName(self.getSmartPlaylistFilename(playlistNum)))
        self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Starting","")
        # now let's create new channels
        if self.makeChannelList(playlistNum) == True:
            self.log("buildChannel: makeChannelList=True")
            # the m3u channel number may not be the same as the playlist channel number            
            channelNum = self.nextM3uChannelNum
            self.log("buildChannel: channelNum=" + str(channelNum))            
            # keep a list of which playlists are associated with which channels
            self.channelList.append(playlistNum)
            # add new channel to EPG
            self.log("buildChannel: Add channel to EPG")
            self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Adding Channel to EPG","")
            self.log("buildChannel: self.channels[" + str(channelNum - 1) + "].setPlaylist" + str(CHANNELS_LOC) + "channel_" + str(channelNum) + ".m3u")
            if self.channels[channelNum - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channelNum) + '.m3u') == True:
                self.channels[channelNum - 1].totalTimePlayed = 0
                self.log("buildChannel: totalTimePlayed=0")          
                self.channels[channelNum - 1].isValid = True
                self.log("buildChannel: isValid=True")          
                self.channels[channelNum - 1].fileName = CHANNELS_LOC + 'channel_' + str(channelNum) + '.m3u'
                self.log("buildChannel: fileName=" + CHANNELS_LOC + "channel_" + str(channelNum) + ".m3u")
                returnval = True
                ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_time', '0')
            else:
                returnval = False
            self.channels[channelNum - 1].name = self.getSmartPlaylistName(self.getSmartPlaylistFilename(playlistNum))
            self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Adding Channel to EPG",self.channels[channelNum - 1].name)
            self.log("buildChannel: name=" + str(self.channels[channelNum - 1].name))
            return returnval
            # load new channel
            self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Completed","")
            self.log("buildChannel: Loading new channel")
        else:
            pass
        self.log("buildChannel: Completed")


    # rebuild m3u for channel and initialize channel
    def rebuildChannel(self, m3uNum):
        self.log("rebuildChannel: Started")
        self.log("rebuildChannel: m3uNum=" + str(m3uNum))
        playlistNum = ""
        # lookup playlistNum for channel in channels.xml
        playlistNum = self.getChannelPlaylistNum(m3uNum-1)
        self.log("rebuildChannel: playlistNum=" + str(playlistNum))
        if playlistNum <> "":
            # now let's create new channels
            if self.makeChannelList(playlistNum, m3uNum) == True:
                self.log("rebuildChannel: makeChannelList=True")
                self.log("rebuildChannel: Refreshing channel in EPG")
                if self.channels[m3uNum - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u') == True:
                    self.channels[m3uNum - 1].totalTimePlayed = 0
                    self.log("rebuildChannel: totalTimePlayed=" + str(self.channels[m3uNum - 1].totalTimePlayed))
                    self.channels[m3uNum - 1].isValid = True
                    self.log("rebuildChannel: isValid=" + str(self.channels[m3uNum - 1].isValid))
                    self.channels[m3uNum - 1].fileName = CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u'
                    self.log("rebuildChannel: fileName=" + str(self.channels[m3uNum - 1].fileName))
                    returnval = True
                    ADDON_SETTINGS.setSetting('Channel_' + str(m3uNum) + '_time', '0')
                self.channels[m3uNum - 1].name = self.getSmartPlaylistName(self.getSmartPlaylistFilename(playlistNum))
                self.log("rebuildChannel: name=" + str(self.channels[m3uNum - 1].name))
                return returnval
                # load new channel
                self.log("rebuildChannel: Reloading channel")
                self.loadChannel(m3uNum)
            else:
                pass
        else:
            self.log("No channel found in channels.xml for channel_" + str(m3uNum) + ".m3u")
            return False
        self.log("rebuildChannel: Completed")


    def getChannelPlaylistNum(self, channelNum):
        self.log("getChannelPlaylistNum: Started")
        # check if channels.xml file exists
        filename = 'channels.xml'
        self.log("getChannelPlaylistNum: fle=" + str(os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/'), filename)))        
        if os.path.exists(os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/'), filename)):
            fle = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/'), filename)
            self.log("getChannelPlaylistNum: found channels.xml")
        else:
            self.log("getChannelPlaylistNum: no channels.xml file found")
            return False        
        # read in channels.xml file
        dom = self.getChannelsXML(fle)
        # lookup channel node matching id = channelNum
        channelList = dom.getElementsByTagName('channel')
        for i in range(len(channelList)):
            channel = channelList[i]
            channelNum2 = channel.attributes["channelNum"]
            playlistNum = channel.attributes["playlistNum"]
            self.log("getChannelPlaylistNum: channelNum=" + str(channelNum))
            self.log("getChannelPlaylistNum: channelNum2=" + str(channelNum2))
            self.log("getChannelPlaylistNum: playlistNum=" + str(playlistNum))
            if int(channelNum2.value) == int(channelNum):
                self.log("getChannelPlaylistNum: Found channel playlist: " + str(playlistNum.value))
                return playlistNum.value
        self.log("getChannelPlaylistNum: Completed")

    
    def buildChannelsXML(self, channelList):
        self.log("buildChannelsXML: Started")
        # create xml doc
        channelsXML = self.createChannelsXML()
        # add channels element
        channels = self.addChannels(channelsXML)
        # add channel elements
        for channelNum in range(len(channelList)):
            playlistNum = channelList[channelNum]
            self.addChannel(channelsXML, channels, channelNum, playlistNum)
            self.log("buildChannelsXML: channeNum=" + str(channelNum))
            self.log("buildChannelsXML: playlistNum=" + str(playlistNum))
            channelNum = channelNum + 1        
        # write xml to file
        self.writeChannelsXML(channelsXML)
        self.log("buildChannelsXML: Completed")


    def createChannelsXML(self):
        channelsXML = Document()
        return channelsXML


    def addChannels(self, channelsXML):
        channelsNode = channelsXML.createElement("channels")
        channelsXML.appendChild(channelsNode)
        return channelsNode


    def addChannel(self, channelsXML, channelsNode, channelNum, playlistNum):
        channelElement = channelsXML.createElement("channel")
        channelElement.setAttribute("channelNum", str(channelNum))
        channelElement.setAttribute("playlistNum", str(playlistNum))
        channelsNode.appendChild(channelElement)


    def writeChannelsXML(self, channelsXML):
        # get path to write to
        fle = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/'), 'channels.xml')
        # write xml file
        f = open(fle, "w")
        channelsXML.toprettyxml(indent='  ')
        channelsXML.writexml(f)
        f.close()


    def deleteChannelsXML(self):
        fle = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/'), 'channels.xml')
        if os.path.exists(fle):
            try:
                if os.path.isfile(fle):
                    self.log('deleteChannelsXML: deleting file: ' + fle)
                    os.unlink(fle)
            except Exception, e:
                self.log(e)
        else:
            self.log('deleteChannelsXML: ' + str(fle) + ' does not exist')
                    

    def getChannelsXML(self, fle):
        self.log("getChannelsXML: Started")
        if os.path.exists(fle):
            try:
                xml = open(fle, "r")
            except:
                self.log("getChannelsXML Unable to open the xml file " + fle, xbmc.LOGERROR)
                return ''
            try:
                dom = parse(xml)
            except:
                self.log('getChannelsXML Problem parsing xml file ' + fle, xbmc.LOGERROR)
                xml.close()
                return ''
            xml.close()
            return dom
        else:
            self.log(str(fle) + ' not found')
            dom = ""
            return dom
        self.log("getChannelsXML: Completed")


    # Based on a smart playlist, create a normal playlist that can actually be used by us
    # make m3u file
    def makeChannelList(self, playlistNum, m3uNum=None):
        self.log("makeChannelList: Started")
        self.log('makeChannelList ' + str(playlistNum))        
        fle = self.getSmartPlaylistFilename(playlistNum)
        filename = os.path.basename(fle)
        channelName = str(self.getSmartPlaylistName(self.getSmartPlaylistFilename(playlistNum)))
        self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Getting SmartPlaylist",str(filename))
        self.log("makeChannelList: fle=" + str(fle))
        if len(fle) == 0:
            self.log("makeChannelList: Unable to locate the playlist for channel " + str(playlistNum), xbmc.LOGERROR)
            return False
        try:
            xml = open(fle, "r")
        except:
            self.log("makeChannelList: Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return False
        try:
            dom = parse(xml)
        except:
            self.log("makeChannelList: Problem parsing playlist " + fle, xbmc.LOGERROR)
            xml.close()
            return False
        xml.close()
        pltype = self.getSmartPlaylistType(dom)

        try:
            limitNode = dom.getElementsByTagName('limit')
        except:
            # if no limit node in smartplaylist, force max limit
            limit = 250
            xml.close()
   
        if limitNode:
            limit = limitNode[0].firstChild.nodeValue
            # force a max limit of 250 for performance reason
            if int(limit) > 250:
                limit = 250
        else:
            # force a max limit of 250 for performance reason
            limit = 250
        
        if pltype == 'mixed':
            self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Found Mixed SmartPlaylist","")
            self.fileLists = []
            self.level = 0
            self.fileLists = self.buildMixedFileLists(fle)            
            if not "movies" in self.fileLists and not "episodes" in self.fileLists:
                self.log("makeChannelList: mix tvshow channel")
                self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Found Mixed SmartPlaylist","Building Mixed TV Show Channel")
                fileList = self.buildMixedTVShowFileList(self.fileLists, limit)
            else:
                self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Found Mixed SmartPlaylist","Building Mixed Episode & Movie Channel")
                fileList = self.buildMixedFileList(self.fileLists, limit)
        else:
            self.channelType = pltype
            self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Found SmartPlaylist","")
            fileList = self.buildFileList(fle)

        try:
            order = dom.getElementsByTagName('order')
            if order[0].childNodes[0].nodeValue.lower() == 'random':
                self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Randomizing Channel Files","")
                random.shuffle(fileList)
        except:
            pass
        
        # check if fileList contains files
        if len(fileList) == 0:
            self.updateDialog.update(self.updateProgressPercentage, "Building Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"No Files Found for Channel...Skipping","")
            self.log("makeChannelList: Playlist returned no files", xbmc.LOGERROR)
            return False
        else:
            self.log("makeChannelList: self.channelType=" + str(self.channelType))
            if self.channelType == "movies":
                if (self.trailers == True and os.path.exists(self.trailersFolder)):
                    fileList = self.addTrailers(fileList, channelName)
            else:
                if (self.commercials == True and os.path.exists(self.commercialsFolder)) or (self.bumpers == True and os.path.exists(self.bumpersFolder)):
                    fileList = self.addCommercialsAndBumpers(fileList, channelName)

        # valid channel
        if m3uNum == None:
            self.nextM3uChannelNum = self.nextM3uChannelNum + 1
            m3uNum = self.nextM3uChannelNum
            self.log("makeChannelList: m3uNum=" + str(m3uNum))
            self.log("makeChannelList: self.nextM3uChannelNum: " + str(self.nextM3uChannelNum))
        
        if self.writeM3u(m3uNum, fileList) == True:
            return True
        else:
            return False
        self.log("makeChannelList: Completed")


    def getFile(self, folder):
        self.log("getFile: Started")
        tmpstr = ""
        self.getFileTries = self.getFileTries + 1
        self.log("getFile: self.getFileTries=" + str(self.getFileTries))
        if os.path.exists(folder):
            if self.getFileTries < 100:
                # get directory contents
                try:
                    self.log("getFile: folder=" + str(folder))
                    filename = random.choice(os.listdir(folder))
                    self.log("getFile: filename=" + str(filename))
                    if len(filename) > 0:
                        # get duration of file
                        dur = self.videoParser.getVideoLength(os.path.join(folder, filename))
                        self.log("getFile: dur=" + str(dur))
                        if dur == 0:
                            # try again
                            self.getFile(folder)
                        else:
                            # let's parse out some file information
                            filename_base = []
                            filename_parts = []
                            filename_parts2 = []
                            filename_base = filename.split(".")
                            filename_parts = filename_base[0].split("_")
                            filename_parts2 = filename_base[0].split("-")
                            if len(filename_parts) > len(filename_parts2):
                                # use filename_parts
                                title = filename_parts[0]
                                if len(filename_parts) > 1:
                                    showtitle = filename_parts[1]
                                else:
                                    showtitle = ""
                                if len(filename_parts) > 2:
                                    description = filename_parts[2]
                                else:
                                    description = ""
                            else:
                                # use filename_parts2
                                title = filename_parts2[0]
                                if len(filename_parts2) > 1:
                                    showtitle = filename_parts2[1]
                                else:
                                    showtitle = ""
                                if len(filename_parts2) > 2:
                                    description = filename_parts2[2]
                                else:
                                    description = ""
                            self.log("getFile: title=" + str(title))                     
                            self.log("getFile: showtitle=" + str(showtitle))                     
                            self.log("getFile: description=" + str(description))                     
                            tmpstr = str(dur) + ',' + str(title) + '//' + str(showtitle) + '//' + str(description)
                            tmpstr = tmpstr + '\n' + os.path.join(folder, filename)
                            self.getfile = tmpstr
                            self.getFileTries = 0
                    else:
                        # try again
                        self.getFile(folder)
                except:
                    # try again
                    self.getFile(folder)
            else:
                self.log("getFile: File: Failed to find a valid file after 100 attempts")
        else:
            self.log("getFile: Folder does not exist " + str(folder))

        self.log("getFile: Completed")
        self.log("getFile: File=" + str(tmpstr))
        self.getFileTries = 0
        return str(self.getfile)


    def addTrailers(self, fileList, channelName):
        newFileList = []
        # check if we need to add commercials
        if self.trailers == True and os.path.exists(self.trailersFolder):
            # check for channel specific trailers
            if os.path.exists(self.trailersFolder):
                if os.path.exists(os.path.join(self.trailersFolder, channelName)):
                    trailersFolder = os.path.join(self.trailersFolder, channelName)
                else:
                    trailersFolder = self.trailersFolder                
                if self.numTrailers == "0":
                    # need to determine how many commercials are available compared with number of files in tv channel to get a ratio
                    numTotalTrailers = len(glob.glob(os.path.join(trailersFolder, '*.*')))
                    if numTotalTrailers > 0:
                        trailerInterval = len(fileList) / numTotalTrailers
                        # if there are more commercials than files in the channel, set interval to 1
                        if trailerInterval < 1:
                            trailerInterval = 1
                        # need to determine number of bumpers to play during interval
                        numTrailers = numTotalTrailers / len(fileList)
                        if numTrailers < 1:
                            numTrailers = 1
                        if numTrailers > self.maxTrailers:
                            numTrailers = self.maxTrailers
                    else:
                        trailerInterval = 0
                        numTrailers = 0
                else:
                    trailerInterval = 1
                    numTrailers = self.numTrailers
            else:
                trailerInterval = 0
                numTrailers = 0

            # insert commercials and/or bumpers into fileList
            for i in range(len(fileList)):
                self.log('makeChannelList: Inserting file')
                newFileList.append(fileList[i])
                # mix in trailers                                               
                if self.trailers == True and not trailerInterval == 0:
                    if (i+1) % trailerInterval == 0:
                        self.log("makeChannelList: Add Trailer")
                        for n in range(int(numTrailers)):
                            trailerFile = self.getFile(trailersFolder)
                            self.log("makeChannelList: trailerFile=" + str(trailerFile))
                            if len(trailerFile) > 0:
                                self.log('makeChannelList: Inserting Trailer')
                                newFileList.append(trailerFile)
                            else:
                                self.log('makeChannelList: Unable to get trailer')                                        
                            n = n + 1
                i = i + 1
        fileList = newFileList    
        return fileList


    def addCommercialsAndBumpers(self, fileList, channelName):
        newFileList = []
        # check if we need to add commercials
        if self.commercials == True and os.path.exists(self.commercialsFolder):
            # check for channel specific commercials
            if os.path.exists(os.path.join(self.commercialsFolder, channelName)):
                commercialsFolder = os.path.join(self.commercialsFolder, channelName)
            else:
                commercialsFolder = self.commercialsFolder                
            # check if number of commercials set to auto
            if self.numCommercials == "0":
                # need to determine how many commercials are available compared with number of files in tv channel to get a ratio
                numTotalCommercials = len(glob.glob(os.path.join(commercialsFolder, '*.*')))
                if numTotalCommercials > 0:
                    commercialInterval = len(fileList) / numTotalCommercials
                    # if there are more commercials than files in the channel, set interval to 1
                    if commercialInterval < 1:
                        commercialInterval = 1
                    # need to determine number of commercials to play during interval
                    numCommercials = numTotalCommercials / len(fileList)
                    if numCommercials < 1:
                        numCommercials = 1
                    if numCommercials > self.maxCommercials:
                        numCommercials = self.maxCommercials
                else:
                    commercialInterval = 0
                    numCommercials = 0
            else:
                commercialInterval = 1
                numCommercials = self.numCommercials
        else:
            commercialInterval = 0
            numCommercials = 0

        # check if we need to add bumpers                    
        if self.bumpers == True and os.path.exists(self.bumpersFolder):
            # check if number of commercials set to auto
            if self.numBumpers == "0":
                # need to determine how many bumpers are available compared with number of files in tv channel to get a ratio
                numTotalBumpers = len(glob.glob(os.path.join(self.bumpersFolder, channelName, '*.*')))
                if numTotalBumpers > 0:
                    bumperInterval = len(fileList) / numTotalBumpers
                    # if there are more bumpers than files in the channel, set interval to 1
                    if bumperInterval < 1:
                        bumperInterval = 1
                    # need to determine number of bumpers to play during interval
                    numBumpers = numTotalBumpers / len(fileList)
                    if numBumpers < 1:
                        numBumpers = 1
                    if numBumpers > self.maxBumpers:
                        numBumpers = self.maxBumpers
                else:
                    bumperInterval = 0
                    numBumpers = 0
            else:
                bumperInterval = 1                
                numBumpers = self.numBumpers
        else:
            bumperInterval = 0
            numBumpers = 0
            
        # insert commercials and/or bumpers into fileList
        for i in range(len(fileList)):
            self.log('makeChannelList: Inserting file')
            newFileList.append(fileList[i])
            # mix in bumpers                                                
            if self.bumpers == True and not bumperInterval == 0:
                if (i+1) % bumperInterval == 0:
                    self.log("makeChannelList: Add Bumper")
                    for n in range(int(numBumpers)):
                        bumperFile = self.getFile(os.path.join(self.bumpersFolder, channelName))
                        self.log("makeChannelList: bumperFile=" + str(bumperFile))
                        if len(bumperFile) > 0:
                            self.log('makeChannelList: Inserting Bumper')
                            newFileList.append(bumperFile)
                        else:
                            self.log('makeChannelList: Unable to get bumper')
                        n = n + 1
            # mix in commercials                                                
            if self.commercials == True and not commercialInterval == 0:
                self.log("makeChannelList: Begin Inserting Commercials")
                if (i+1) % commercialInterval == 0:
                    self.log("makeChannelList: Add Commercial")
                    for n in range(int(numCommercials)):
                        commercialFile = self.getFile(commercialsFolder)
                        self.log("makeChannelList: commercialFile=" + str(commercialFile))
                        if len(commercialFile) > 0:
                            self.log('makeChannelList: Inserting Commercial')
                            newFileList.append(commercialFile)
                        else:
                            self.log('makeChannelList: Unable to get commercial')                                        
                        n = n + 1
            i = i + 1
        fileList = newFileList
        return fileList


    def writeM3u(self, channelNum, fileList):
        self.log("writeM3u: Started")
        try:
           channelplaylist = open(CHANNELS_LOC + "channel_" + str(channelNum) + ".m3u", "w")
        except:
            self.Error('writeM3u: Unable to open the cache file ' + CHANNELS_LOC + 'channel_' + str(channelNum) + '.m3u', xbmc.LOGERROR)
            return False        
        channelName = str(self.getSmartPlaylistName(self.getSmartPlaylistFilename(self.updateProgressPlaylistNum)))
        self.updateDialog.update(self.updateProgressPercentage, "Creating Channel " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Writing Channel File to Cache","")            
        self.log("writeM3u: created m3u file " + CHANNELS_LOC + "channel_" + str(channelNum) + ".m3u successfully") 
        channelplaylist.write("#EXTM3U\n")
        fileList = fileList[:250]
        # Write each entry into the new playlist
        for string in fileList:
            channelplaylist.write("#EXTINF:" + string + "\n")
        channelplaylist.close()
        self.log("writeM3u: Completed")
        return True


    def getM3uFilename(self, channel):
        self.log("getM3uFilename: Started")
        self.log("getM3uFilename: channel=" + str(channel))
        self.log(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache') + '/channel_' + str(channel) + '.m3u')
        if os.path.exists(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache') + '/channel_' + str(channel) + '.m3u'):
            self.log("getM3uFilename: File found")
            self.log("getM3uFilename: Completed")
            return xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache') + '/channel_' + str(channel) + '.m3u'
        else:
            self.log("getM3uFilename: File not found")
            self.log("getM3uFilename: Completed")
            return ""

    
    def getSmartPlaylistFilename(self, playlistNum):
        self.log("getSmartPlaylistFilename: Started")
        self.log("getSmartPlaylistFilename: " + str(playlistNum))
        self.log(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets') + '/channel_' + str(playlistNum) + '.xsp')
        if os.path.exists(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets') + '/channel_' + str(playlistNum) + '.xsp'):
            self.log("getSmartPlaylistFilename: File found")
            self.log("getSmartPlaylistFilename: Completed")
            return xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets') + '/channel_' + str(playlistNum) + '.xsp'
        else:
            self.log("getSmartPlaylistFilename: File not found")
            self.log("getSmartPlaylistFilename: Completed")
            return ""


    # Open the smart playlist and read the name out of it...this is the channel name
    def getSmartPlaylistName(self, fle):
        self.log("getSmartPlaylistName: Started")
        try:
            xml = open(fle, "r")
        except:
            self.log("getSmartPlaylistName Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return ''
        try:
            dom = parse(xml)
        except:
            self.log('getSmartPlaylistName: Problem parsing playlist ' + fle, xbmc.LOGERROR)
            xml.close()
            return ''
        xml.close()
        try:
            plname = dom.getElementsByTagName('name')
            self.log("getSmartPlaylistName: plname=" + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except:
            self.log("getSmartPlaylistName: Unable to get the playlist name.", xbmc.LOGERROR)
            return ''
        self.log("getSmartPlaylistName: Completed")


    # handle fatal errors: log it, show the dialog, and exit
    def Error(self, message):
        self.log('FATAL ERROR: ' + message, xbmc.LOGFATAL)
        dlg = xbmcgui.Dialog()
        dlg.ok('Error', message)
        del dlg
        self.end()


    def getSmartPlaylistType(self, dom):
        self.log("getSmartPlaylistType: Started")
        try:
            pltype = dom.getElementsByTagName('smartplaylist')
            self.log("getSmartPlaylistType: pltype=" + str(pltype))
            self.log("getSmartPlaylistType: Completed")
            return pltype[0].attributes['type'].value
        except:
            self.log("Unable to get the playlist type.", xbmc.LOGERROR)
            self.log("getSmartPlaylistType: Completed")
            return ''


    def buildFileList(self, dir_name, media_type="video", recursive="TRUE"):
        self.log("buildFileList: Started")
        channelName = self.getSmartPlaylistName(self.getSmartPlaylistFilename(self.updateProgressPlaylistNum))
        playlistName = self.getSmartPlaylistName(dir_name)
        self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Querying XBMC Database...please wait",str(playlistName))
        fileList = []
        json_query = '{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "recursive": "%s", "fields":["duration","tagline","showtitle","album","artist","plot"]}, "id": 1}' % ( self.escapeDirJSON( dir_name ), media_type, recursive )
        json_folder_detail = xbmc.executeJSONRPC(json_query)
        self.log(json_folder_detail)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Processing Results",str(playlistName))
        numFiles = len(file_detail)
        progressIncrement = 100/numFiles
        progressPercentage = 0
        fileNum = 1
        for f in file_detail:
            progressPercentage = progressPercentage + progressIncrement
            self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Analyzing File " + str(fileNum),"")
            match = re.search('"file" *: *"(.*?)",', f)
            if match:
                if(match.group(1).endswith("/") or match.group(1).endswith("\\")):
                    if(recursive == "TRUE"):
                        fileList.extend(self.buildFileList(match.group(1), media_type, recursive))
                else:
                    duration = re.search('"duration" *: *([0-9]*?),', f)

                    try:
                        dur = int(duration.group(1))
                    except:
                        dur = 0

                    if dur == 0:
                        self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Analyzing File " + str(fileNum),"Getting Video Duration")
                        self.log("buildFileList: Getting Video Durations")
                        dur = self.videoParser.getVideoLength(match.group(1).replace("\\\\", "\\"))
                        self.log("buildFileList: dur=" + str(dur))
                        
                    try:
                        if dur > 0:
                            title = re.search('"label" *: *"(.*?)"', f)
                            tmpstr = str(dur) + ','
                            showtitle = re.search('"showtitle" *: *"(.*?)"', f)
                            plot = re.search('"plot" *: *"(.*?)",', f)
                            if plot == None:
                                theplot = ""
                            else:
                                theplot = plot.group(1)
                            # This is a TV show
                            if showtitle != None:
                                tmpstr += showtitle.group(1) + "//" + title.group(1) + "//" + theplot
                            else:
                                tmpstr += title.group(1) + "//"
                                album = re.search('"album" *: *"(.*?)"', f)
                                # This is a movie
                                if album == None:
                                    tagline = re.search('"tagline" *: *"(.*?)"', f)
                                    if tagline != None:
                                        tmpstr += tagline.group(1)
                                    tmpstr += "//" + theplot
                                else:
                                    artist = re.search('"artist" *: *"(.*?)"', f)
                                    tmpstr += album.group(1) + "//" + artist.group(1)
                            tmpstr = tmpstr[:600]
                            tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                            tmpstr = tmpstr + '\n' + match.group(1).replace("\\\\", "\\")
                            fileList.append(tmpstr)
                            self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Adding File " + str(fileNum),"")
                    except:
                        pass
            else:
                continue
            fileNum = fileNum + 1
        self.log("buildFileList: Completed")
        return fileList


    def buildMixedTVShowFileList(self, fileLists, limit):
        self.log("buildMixedTVShowFileList: Started")
        self.channelType = "mixedtvshows"
        channelName = str(self.getSmartPlaylistName(self.getSmartPlaylistFilename(self.updateProgressPlaylistNum)))
        tvshowList = []        
        fileList = []
        maxFileListItems = 0
        numTotalItems = 0
        # neeed to grab one episode from each list until we reach channel limit
        self.log("buildMixedTVShowFileList: fileLists Length=" + str(len(fileLists)))
        self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Found Mixed SmartPlaylist","Processing " + str(len(fileLists)) + " Playlists")
        # get fileList sizes
        fl = 0 
        for fl in range(len(fileLists)):
            numTotalItems = numTotalItems + len(fileLists[fl].list)            
            if len(fileLists[fl].list) > maxFileListItems:
                maxFileListItems = len(fileLists[fl].list)
            fl = fl + 1

        # make sure we have files in the lists
        if maxFileListItems > 0:
            # loop through filelists for each item using maxFileList Items
            i = 0
            for i in range(maxFileListItems):
                # loop through each filelist in fileLists
                fl = 0 
                for fl in range(len(fileLists)):
                    # if i is less than number items in filelist then get next item
                    if i < len(fileLists[fl].list):
                        fileList.append(fileLists[fl].list[i])
                    fl = fl + 1                
                i = i + 1
        f = 0
        for f in range(len(fileList)):
            self.log("buildMixedTVShowFileList: fileList item: " + str(fileList[f]))
            self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Found Mixed SmartPlaylist","Adding " + str(fileList[f]) + " to channel file list")
            f = f + 1

        # limit filelist
        self.log("buildMixedTVShowFileList: limit=" + str(limit))
        fileList = fileList[0:int(limit)]

        self.log("buildMixedTVShowFileList: fileList contains " + str(len(fileList)) + " items")
        self.log("buildMixedTVShowFileList: Completed")
        return fileList


    def buildMixedFileList(self, fileLists, limit):
        self.log("buildMixedFileList: Started")
        self.channelType = "mixedtvandmovies"
        channelName = str(self.getSmartPlaylistName(self.getSmartPlaylistFilename(self.updateProgressPlaylistNum)))
        i = 0
        numMovieItems = 0
        numEpisodeItems = 0
        numTVShowItems = 0
        ratioMovies = 0
        ratioEpisodes = 0
        ratioTVShows = 0
        itemMultiplier = 0
        movieIndex = 999
        episodeIndex = 999
        tvshowIndex = 999
        movieList = []
        episodeList = []
        tvshowList = []
        fileList = []

        # create seperate lists for each type
        for i in range(len(fileLists)):
            self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Found Mixed SmartPlaylist","Sorting files by type")
            if fileLists[i].type == "movies":
                self.log("buildMixedFileList: movie list found: " + str(i))
                if int(movieIndex) == 999:
                    movieIndex = i
                numMovieItems = numMovieItems + len(fileLists[i].list)
                movieList.extend(fileLists[i].list)
            elif fileLists[i].type == "episodes":
                self.log("buildMixedFileList: episode list found: " + str(i))
                if int(episodeIndex) == 999:
                    episodeIndex = i
                numEpisodeItems = numEpisodeItems + len(fileLists[i].list)
                episodeList.extend(fileLists[i].list)
            elif fileLists[i].type == "tvshows":
                self.log("buildMixedFileList: tvshow list found: " + str(i))
                if int(tvshowIndex) == 999:
                    tvshowIndex = i
                numTVShowItems = numTVShowItems + len(fileLists[i].list)
                tvshowList.extend(fileLists[i].list)
            i = i + 1

        # randomize if playlist order set to random
        if self.mixOrder == 'random':
            random.shuffle(movieList)
            random.shuffle(episodeList)
            random.shuffle(tvshowList)
            
        self.log("buildMixedFileList: movieIndex: " + str(movieIndex))
        self.log("buildMixedFileList: episodeIndex: " + str(episodeIndex))
        self.log("buildMixedFileList: tvshowIndex: " + str(tvshowIndex))

        self.log("buildMixedFileList: numMovieItems: " + str(numMovieItems))
        self.log("buildMixedFileList: numEpisodeItems: " + str(numEpisodeItems))
        self.log("buildMixedFileList: numTVShowItems: " + str(numTVShowItems))
        
        numTotalItems = numMovieItems + numEpisodeItems + numTVShowItems
        self.log("buildMixedFileList: numTotalItems: " + str(numTotalItems))
        
        if numMovieItems > 0:
            ratioMovies = int(round(numTotalItems / numMovieItems))
            self.log("buildMixedFileList: ratioMovies: " + str(ratioMovies))

        if numEpisodeItems > 0:
            ratioEpisodes = int(round(numTotalItems / numEpisodeItems))
            self.log("buildMixedFileList: ratioEpisodes: " + str(ratioEpisodes))

        if numTVShowItems > 0:
            ratioTVShows = int(round(numTotalItems / numTVShowItems))
            self.log("buildMixedFileList: ratioTVShows: " + str(ratioTVShows))

        if int(ratioMovies) > 0 or int(ratioEpisodes) > 0 or int(ratioTVShows):
            itemMultiplier = int(round(int(self.mixLimit)/(int(ratioMovies) + int(ratioEpisodes) + int(ratioTVShows))))
        else:
            itemMultiplier = 0

        self.log("buildMixedFileList: itemMultiplier: " + str(itemMultiplier))

        numMovies = itemMultiplier * ratioMovies
        numEpisodes = itemMultiplier * ratioEpisodes
        numTVShows = itemMultiplier * ratioTVShows

        self.log("buildMixedFileList: numMovies: " + str(numMovies))
        self.log("buildMixedFileList: numEpisodes: " + str(numEpisodes))
        self.log("buildMixedFileList: numTVShows: " + str(numTVShows))

        # get a subset of items based on the number required
        movieSeq = []
        episodeSeq = []
        tvshowSeq = []

        movieSeq = movieList[0:numMovies]
        episodeSeq = episodeList[0:numEpisodes]
        tvshowSeq = tvshowList[0:numTVShows]

        self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum) + ": " + str(channelName),"Found Mixed SmartPlaylist","Creating channel file list")
        # build the final fileList for the channel
        if int(movieIndex) < int(episodeIndex) and int(movieIndex) < tvshowIndex:
            # add movie files first
            fileList.extend(movieSeq)

            if int(episodeIndex) < int(tvshowIndex):
                # add episode files second
                fileList.extend(episodeSeq)

                if int(tvshowIndex) > int(episodeIndex):
                    #add tvshow files third
                    fileList.extend(tvshowSeq)
            
            elif int(tvshowIndex) < int(episodeIndex):
                # add tvshow files second
                fileList.extend(tvShowSeq)
            
                if int(episodeIndex) > int(tvshowIndex):
                    #add episodes files third
                    fileList.extend(episodeSeq)
        
        elif int(episodeIndex) < int(movieIndex) and int(episodeIndex) < int(tvshowIndex):
            # add episde files first
            fileList.extend(episodeSeq)
        
            if int(movieIndex) < int(tvshowIndex):
                # add movie files second
                fileList.extend(movieSeq)
        
                if int(tvshowIndex) > int(movieIndex):
                    #add tvshow files third
                    fileList.extend(tvshowSeq)
        
            elif int(tvshowIndex) < int(movieIndex):
                # add tvshow files second
                fileList.extend(tvshowSeq)
        
                if int(movieIndex) > int(tvshowIndex):
                    #add movie files third
                    fileList.extend(movieSeq)
        
        elif int(tvshowIndex) < int(movieIndex) and int(tvshowIndex) < int(episodeIndex):
            # add tvshow files first
            fileList.extend(tvshowSeq)
        
            if int(movieIndex) < int(episodeIndex):
                # add movie files second
                fileList.extend(movieSeq)
        
                if int(episodeIndex) > int(movieIndex):
                    #add episode files third
                    fileList.extend(episodeSeq)
        
            elif int(episodeIndex) < int(movieIndex):
                # add episode files second
                fileList.extend(episodeSeq)
        
                if int(movieIndex) > int(episodeIndex):
                    #add movie files third
                    fileList.extend(movieSeq)

        self.log("buildMixedFileList: fileList contains " + str(len(fileList)) + " items")
        self.log("buildMixedFileList: Completed")
        
        # limit filelist
        self.log("buildMixedFileList: limit=" + str(limit))
        fileList = fileList[0:int(limit)]

        return fileList


    def buildMixedFileLists(self, src):
        self.log("buildMixedFileLists: Started")
        self.log("buildMixedFileLists: src=" + str(src))
        self.updateDialog.update(self.updateProgressPercentage, "Building File List " + str(self.updateProgressPlaylistNum),"Mixed Channel","")
        dom1 = self.presetChannels.getPlaylist(src)
        pltype = self.getSmartPlaylistType(dom1)

        try:
            rulesNode = dom1.getElementsByTagName('rule')
            orderNode = dom1.getElementsByTagName('order')
            limitNode = dom1.getElementsByTagName('limit')
        except:
            self.log('buildMixedFileList Problem parsing playlist ' + filename, xbmc.LOGERROR)
            xml.close()
            return fileList
   
        if limitNode:
            limit = limitNode[0].firstChild.nodeValue
            # force a max limit of 250 for performance reason
            if int(limit) > 250:
                limit = "250"
        else:
            # force a max limit of 250 for performance reason
            limit = "250"

        # get order to determine whether fileList should be randomized
        if orderNode:
            order = orderNode[0].firstChild.nodeValue
        else:
            order = ""

        # used to capture limit for the mixed channel
        self.level = self.level + 1        
        if self.level == 1:
            # get limit of first playlist to determine how items should be in the final Mixed fileList
            self.mixLimit = limit
            self.log("buildMixedFileLists: mixLimit=" + str(self.mixLimit))
            # get order of first playlist to determine whether final Mix fileList should be randomized
            self.mixOrder = order
            self.log("buildMixedFileLists: mixOrder=" + str(self.mixOrder))
            
        for rule in rulesNode:
            i = 0                        
            fileList = []
            rulename = rule.childNodes[i].nodeValue
            self.log("buildMixedFileLists: rulename: " + str(rulename))
            if os.path.exists(os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets'), rulename)):
                src1 = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets'), rulename)
                self.log("buildMixedFileLists: found video playlist at:" + src1)
            else:
                src1 = ""
                self.log("buildMixedFileLists: Problem finding source file: " + os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets'), rulename))
            dom1 = self.presetChannels.getPlaylist(src1)
            pltype1 = self.getSmartPlaylistType(dom1)
            if pltype1 == 'movies' or pltype1 == 'episodes' or pltype1 == 'tvshows':
                tmpList = []
                tmpList = self.buildFileList(src1)
                if len(tmpList) > 0:
                    if order == 'random':
                        self.log("buildMixedFileLists: Randomize")
                        random.shuffle(tmpList)
                    fileList.extend(tmpList)
                    self.fileLists.append(presetChannelFileList(pltype1, limit, fileList))
            elif pltype1 == 'mixed':
                if os.path.exists(src1):
                    self.buildMixedFileLists(src1)
                else:
                    self.log("buildMixedFileLists: Problem finding source file: " + src1)
            i = i + 1
        self.log("buildMixedFileLists: Completed")
        return self.fileLists


    # Determine the maximum number of channels by opening consecutive
    # m3u until we don't find one
    def findMaxM3us(self):
        self.log("findMaxM3us: Started")
        notfound = False
        channelNum = 1
        while notfound == False:
            self.log("findMaxM3us: " + str(channelNum) )
            self.log("findMaxM3us: getM3uFilename: " + self.getM3uFilename(channelNum))
            if len(self.getM3uFilename(channelNum)) == 0:
                break
            channelNum += 1
        findMaxM3us = channelNum - 1
        self.log("findMaxM3us: findMaxM3us=" + str(findMaxM3us))
        self.log("findMaxM3us: Completed")
        return findMaxM3us


    def createChannelsDir(self):
        if not os.path.exists(CHANNELS_LOC):
            try:
                os.makedirs(CHANNELS_LOC)
            except:
                self.Error('Unable to create the cache directory')
                return


    def createPresetsDir(self):
        if not os.path.exists(PRESETS_LOC):
            try:
                os.makedirs(PRESETS_LOC)
            except:
                self.Error('Unable to create the presets directory')
                return
    

    def deleteCache(self):
        self.log("deleteCache: Started")
        dir = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache/')       
        self.log('deletePresetChannels: Started')
        for filename in os.listdir(dir):
            fle = os.path.join(dir, filename)
            self.log('deletePresetChannels: deleting file: ' + fle)
            try:
                if os.path.isfile(fle):
                    os.unlink(fle)
            except Exception, e:
                self.log(e)
        self.log("deleteCache: Completed")


    def countdown(self, secs, interval=1): 
        while secs > 0: 
            yield secs 
            secs = secs - 1 
            sleep(interval) 


    def autoResetChannels(self):
        # need to allow user to abort the channel reset
        self.resetDialog = xbmcgui.DialogProgress()
        self.resetDialog.create("TV Time", "Preparing for Auto Channel Reset")
        self.resetDialog.update(0, "Preparing for Auto Channel Reset")     
        if self.resetDialog.iscanceled():
            self.log("autoResetChannels: auto channel reset Cancelled")
            self.resetDialog.close()
            return False
        progressPercentage = 0
        for count in self.countdown(10):
            progressPercentage = progressPercentage + 10
            self.resetDialog.update(progressPercentage, "Preparing for Auto Channel Reset")     
        self.resetDialog.close()        
        if not self.resetDialog.iscanceled():
            # cleanly shut down TV Time
            try:
                if self.autoResetTimer > 0:
                    if self.autoResetTimer.isAlive():
                        self.autoResetTimer.cancel()
            except:
                pass
            if xbmc.Player().isPlaying():
                xbmc.Player().stop()
            try:
                ADDON_SETTINGS.setSetting('CurrentChannel', str(self.currentChannel))
            except:
                pass
            # if force reset, delete old cache 
            self.deleteCache()        
            # call creatChannels function to rebuild playlists
            self.buildPlaylists()
            # load in new playlists to create new m3u files
            self.loadPlaylists()
            # reset next auto reset time
            self.setNextAutoResetTime()
            # shut everything down
            try:
                if self.channelLabelTimer.isAlive():
                    self.channelLabelTimer.cancel()
                if self.infoTimer.isAlive():
                    self.infoTimer.cancel()
                if self.sleepTimeValue > 0:
                    if self.sleepTimer.isAlive():
                        self.sleepTimer.cancel()
                if self.autoResetTimer > 0:
                    if self.autoResetTimer.isAlive():
                        self.autoResetTimer.cancel()
            except:
                pass
            if xbmc.Player().isPlaying():
                xbmc.Player().stop()
            if self.timeStarted > 0:
                for i in range(self.maxChannels):
                    if self.channels[i].isValid:
                        ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(int(time() - self.timeStarted + self.channels[i].totalTimePlayed)))
            try:
                ADDON_SETTINGS.setSetting('CurrentChannel', str(self.currentChannel))
            except:
                pass        
            # reinitialize script
            self.__init__()


    def resetChannels(self):
        # we only want one reset occuring at a time so let's put a check in
        if self.resetChannelActive == False:
            self.log("resetChannels: Started")
            ADDON_SETTINGS.setSetting('LastResetTime', str(int(time())))
            self.log("resetChannels: LastResetTime=" + str(int(time())))
            # reset nextM3uChannelNum back to 0
            self.nextM3uChannelNum = 0
            # reset started
            self.resetChannelActive == True
            # if force reset, delete old cache 
            self.deleteCache()        
            # call creatChannels function to rebuild playlists
            self.buildPlaylists()
            # load in new playlists to create new m3u files
            self.loadPlaylists()
            # reset the force setting to Never if it was set to Once
            if self.forceReset == "1":
                ADDON_SETTINGS.setSetting("ForceChannelReset", "0")
            # reset finished
            self.resetChannelActive == False
            self.log("resetChannels: Completed")
        else:
            self.log("resetChannels: Reset Channels Already Running")
            
    
    def validateChannels(self):
        found = False
        for m3uNum in range(self.maxChannels):
            if self.channels[m3uNum].isValid:
                self.log("Channel: " + str(m3uNum) + " is valid")
                found = True
                return True
        if found == False:
            return False


    def resetChannelTimes(self):
        curtime = time()
        for i in range(self.maxChannels):
            self.channels[i].setAccessTime(curtime - self.channels[i].totalTimePlayed)


    def onFocus(self, controlId):
        pass


    def escapeDirJSON(self, dir_name):
        if (dir_name.find(":")):
            dir_name = dir_name.replace("\\", "\\\\")

        return dir_name


    def channelDown(self):
        self.log('channelDown')

        if self.maxChannels == 1:
            return

        self.background.setVisible(True)
        channel = self.fixChannel(self.currentChannel - 1, False)
        self.setChannel(channel)
        self.background.setVisible(False)
        self.log('channelDown return')


    def channelUp(self):
        self.log('channelUp')

        if self.maxChannels == 1:
            return

        self.background.setVisible(True)
        channel = self.fixChannel(self.currentChannel + 1)
        self.setChannel(channel)
        self.background.setVisible(False)
        self.log('channelUp return')


    def message(self, data):
        self.log('Dialog message: ' + data)
        dlg = xbmcgui.Dialog()
        dlg.ok('Info', data)
        del dlg


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('TVOverlay: ' + msg, level)


    # set the channel, the proper show offset, and time offset
    def setChannel(self, channel):
        self.log('setChannel ' + str(channel))

        if channel < 1 or channel > self.maxChannels:
            self.log('setChannel invalid channel ' + str(channel), xbmc.LOGERROR)
            return

        if self.channels[channel - 1].isValid == False:
            self.log('setChannel channel not valid ' + str(channel), xbmc.LOGERROR)
            return

        self.lastActionTime = 0
        timedif = 0
        forcestart = True
        samechannel = False
        self.getControl(102).setVisible(False)
        self.showingInfo = False

        # first of all, save playing state, time, and playlist offset for
        # the currently playing channel
        if xbmc.Player().isPlaying():
            if channel != self.currentChannel:
                self.channels[self.currentChannel - 1].setPaused(xbmc.getCondVisibility('Player.Paused'))
                self.channels[self.currentChannel - 1].setShowTime(xbmc.Player().getTime())
                self.channels[self.currentChannel - 1].setShowPosition(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                self.channels[self.currentChannel - 1].setAccessTime(time())
            else:
                samechannel = True

            forcestart = False

        if self.currentChannel != channel or forcestart:
            self.currentChannel = channel
            # now load the proper channel playlist
            xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
            self.log('starting video')
            self.log('filename is ' + self.channels[channel - 1].fileName)

            if self.startPlaylist('XBMC.PlayMedia(' + self.channels[channel - 1].fileName + ')') == False:
                self.log("Unable to set channel " + str(channel) + ". Invalidating.", xbmc.LOGERROR)
                self.InvalidateChannel(channel)
                return

            # Disable auto playlist shuffling if it's on
            if xbmc.getInfoLabel('Playlist.Random').lower() == 'random':
                self.log('Random on.  Disabling.')
                xbmc.PlayList(0).unshuffle()
                xbmc.PlayList(1).unshuffle()
                xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
                self.log('starting video')

                if self.startPlaylist('XBMC.PlayMedia(' + self.channels[channel - 1].fileName + ')') == False:
                    self.log("Unable to set channel " + str(channel) + ". Invalidating.", xbmc.LOGERROR)
                    self.InvalidateChannel(channel)
                    return

            xbmc.executebuiltin("XBMC.PlayerControl(repeatall)")

        timedif += (time() - self.channels[self.currentChannel - 1].lastAccessTime)

        # adjust the show and time offsets to properly position inside the playlist
        while self.channels[self.currentChannel - 1].showTimeOffset + timedif > self.channels[self.currentChannel - 1].getCurrentDuration():
            self.channels[self.currentChannel - 1].addShowPosition(1)
            timedif -= self.channels[self.currentChannel - 1].getCurrentDuration() - self.channels[self.currentChannel - 1].showTimeOffset
            self.channels[self.currentChannel - 1].setShowTime(0)

        # if needed, set the show offset
        if self.channels[self.currentChannel - 1].playlistPosition != xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition():
            if samechannel == False:
                if self.startPlaylist('XBMC.Playlist.PlayOffset(' + str(self.channels[self.currentChannel - 1].playlistPosition) + ')') == False:
                    self.log('Unable to set offset for channel ' + str(channel) + ". Invalidating.", xbmc.LOGERROR)
                    self.InvalidateChannel(channel)
                    return
            else:
                if self.startPlaylist('XBMC.Playlist.PlayOffset(' + str(self.channels[self.currentChannel - 1].playlistPosition - xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition()) + ')') == False:
                    self.log('Unable to set offset for channel ' + str(channel) + ". Invalidating.", xbmc.LOGERROR)
                    self.InvalidateChannel(channel)
                    return

        # set the time offset
        self.channels[self.currentChannel - 1].setAccessTime(time())

        if self.channels[self.currentChannel - 1].isPaused:
            try:
                xbmc.Player().seekTime(self.channels[self.currentChannel - 1].showTimeOffset)
                xbmc.Player().pause()

                if self.waitForVideoPaused() == False:
                    return
            except:
                self.log('Exception during seek on paused channel', xbmc.LOGERROR)
        else:
            seektime = self.channels[self.currentChannel - 1].showTimeOffset + timedif

            try:
                xbmc.Player().seekTime(seektime)
            except:
                self.log('Exception during seek', xbmc.LOGERROR)

        self.showChannelLabel(self.currentChannel)
        self.lastActionTime = time()
        self.log('setChannel return')


    def InvalidateChannel(self, channel):
        self.log("InvalidateChannel" + str(channel))

        if channel < 1 or channel > self.maxChannels:
            self.log("InvalidateChannel invalid channel " + str(channel))
            return

        self.channels[channel - 1].isValid = False
        self.invalidatedChannelCount += 1

        if self.invalidatedChannelCount > 3:
            self.Error("Exceeded 3 invalidated channels. Exiting.")
            return

        remaining = 0

        for i in range(self.maxChannels):
            if self.channels[i].isValid:
                remaining += 1

        if remaining == 0:
            self.Error("No channels available. Exiting.")
            return

        self.setChannel(self.fixChannel(channel))


    def waitForVideoPaused(self):
        self.log('waitForVideoPaused')
        sleeptime = 0

        while sleeptime < TIMEOUT:
            xbmc.sleep(100)

            if xbmc.Player().isPlaying():
                if xbmc.getCondVisibility('Player.Paused'):
                    break

            sleeptime += 100
        else:
            self.log('Timeout waiting for pause', xbmc.LOGERROR)
            return False

        self.log('waitForVideoPaused return')
        return True


    def waitForVideoStop(self):
        self.log('waitForVideoStop')
        sleeptime = 0

        while sleeptime < TIMEOUT:
            xbmc.sleep(100)

            if xbmc.Player().isPlaying() == False:
                break

            sleeptime += 100
        else:
            self.log('Timeout waiting for video to stop', xbmc.LOGERROR)
            return False

        self.log('waitForVideoStop return')
        return True


    # run a built-in command and wait for it to take effect
    def startPlaylist(self, command):
        self.log('startPlaylist ' + command)

        if xbmc.Player().isPlaying():
            if xbmc.getCondVisibility('Player.Paused') == False:
                self.log('Pausing')
                xbmc.Player().pause()

                if self.waitForVideoPaused() == False:
                    return False

        self.log('Executing command')
        xbmc.executebuiltin(command)
        sleeptime = 0
        self.log('Waiting for video')

        while sleeptime < TIMEOUT:
            xbmc.sleep(100)

            if xbmc.Player().isPlaying():
                try:
                    if xbmc.getCondVisibility('!Player.Paused') and xbmc.Player().getTime() > 0.0:
                        break
                except:
                    self.log('Exception waiting for video to start')
                    pass

            sleeptime += 100

        if sleeptime >= TIMEOUT:
            self.log('Timeout waiting for video to start', xbmc.LOGERROR)
            return False

        self.log('startPlaylist return')
        return True


    def setShowInfo(self):
        self.log('setShowInfo')

        if self.infoOffset > 0:
            self.getControl(502).setLabel('COMING UP:')
        elif self.infoOffset < 0:
            self.getControl(502).setLabel('ALREADY SEEN:')
        elif self.infoOffset == 0:
            self.getControl(502).setLabel('NOW WATCHING:')

        position = xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition() + self.infoOffset
        self.getControl(503).setLabel(self.channels[self.currentChannel - 1].getItemTitle(position))
        self.getControl(504).setLabel(self.channels[self.currentChannel - 1].getItemEpisodeTitle(position))
        self.getControl(505).setLabel(self.channels[self.currentChannel - 1].getItemDescription(position))
        self.getControl(506).setImage(LOGOS_LOC + self.channels[self.currentChannel - 1].name + '.png')
        self.log('setShowInfo return')


    # Display the current channel based on self.currentChannel.
    # Start the timer to hide it.
    def showChannelLabel(self, channel):
        self.log('showChannelLabel ' + str(channel))

        if self.channelLabelTimer.isAlive():
            self.channelLabelTimer.cancel()
            self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)

        tmp = self.inputChannel
        self.hideChannelLabel()
        self.inputChannel = tmp
        curlabel = 0

        if channel > 99:
            self.channelLabel[curlabel].setImage(IMAGES_LOC + 'label_' + str(channel // 100) + '.png')
            self.channelLabel[curlabel].setVisible(True)
            curlabel += 1

        if channel > 9:
            self.channelLabel[curlabel].setImage(IMAGES_LOC + 'label_' + str((channel % 100) // 10) + '.png')
            self.channelLabel[curlabel].setVisible(True)
            curlabel += 1

        self.channelLabel[curlabel].setImage(IMAGES_LOC + 'label_' + str(channel % 10) + '.png')
        self.channelLabel[curlabel].setVisible(True)

        ##ADDED BY SRANSHAFT: USED TO SHOW NEW INFO WINDOW WHEN CHANGING CHANNELS
        if self.inputChannel == -1 and self.infoOnChange == True:
            self.infoOffset = 0
            self.showInfo(5.0)

        if self.showChannelBug == True:
            try:
                self.getControl(103).setImage(LOGOS_LOC + self.channels[self.currentChannel - 1].name + '.png')
            except:
                pass
        ##

        self.channelLabelTimer.start()
        self.log('showChannelLabel return')


    # Called from the timer to hide the channel label.
    def hideChannelLabel(self):
        self.log('hideChannelLabel')
        self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)

        for i in range(3):
            self.channelLabel[i].setVisible(False)

        self.inputChannel = -1
        self.log('hideChannelLabel return')


    def hideInfo(self):
        self.getControl(102).setVisible(False)
        self.infoOffset = 0
        self.showingInfo = False

        if self.infoTimer.isAlive():
            self.infoTimer.cancel()

        self.infoTimer = threading.Timer(5.0, self.hideInfo)


    def showInfo(self, timer):
        self.getControl(102).setVisible(True)
        self.showingInfo = True
        self.setShowInfo()

        if self.infoTimer.isAlive():
            self.infoTimer.cancel()

        self.infoTimer = threading.Timer(timer, self.hideInfo)
        self.infoTimer.start()

    # return a valid channel in the proper range
    def fixChannel(self, channel, increasing = True):
        while channel < 1 or channel > self.maxChannels:
            if channel < 1: channel = self.maxChannels + channel
            if channel > self.maxChannels: channel -= self.maxChannels

        if increasing:
            direction = 1
        else:
            direction = -1

        if self.channels[channel - 1].isValid == False:
            return self.fixChannel(channel + direction, increasing)

        return channel


    # Handle all input while videos are playing
    def onAction(self, act):
        action = act.getId()
        self.log('onAction ' + str(action))

        # Since onAction isnt always called from the same thread (weird),
        # ignore all actions if we're in the middle of processing one
        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return

        # Don't force the 2 second rule on the stop command since it will
        # be done anyway.
        if action == ACTION_STOP:
            self.end()
            self.actionSemaphore.release()
            self.log('onAction return')
            return

        lastaction = time() - self.lastActionTime

        # during certain times we just want to discard all input
        if lastaction < 2:
            self.log('Not allowing actions')
            action = ACTION_INVALID

        self.startSleepTimer()

        if action == ACTION_SELECT_ITEM:
            # If we're manually typing the channel, set it now
            if self.inputChannel > 0:
                if self.inputChannel != self.currentChannel:
                    self.setChannel(self.inputChannel)

                self.inputChannel = -1
            else:
                # Otherwise, show the EPG
                if self.sleepTimeValue > 0:
                    if self.sleepTimer.isAlive():
                        self.sleepTimer.cancel()
                        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

                self.hideInfo()
                self.newChannel = 0
                self.myEPG.doModal()

                if self.newChannel != 0:
                    self.background.setVisible(True)
                    self.setChannel(self.newChannel)
                    self.background.setVisible(False)
        elif action == ACTION_MOVE_UP or action == ACTION_PAGEUP:
            self.channelUp()
        elif action == ACTION_MOVE_DOWN or action == ACTION_PAGEDOWN:
            self.channelDown()
        elif action == ACTION_MOVE_LEFT:
            if self.showingInfo:
                self.infoOffset -= 1
                self.showInfo(10.0)
        elif action == ACTION_MOVE_RIGHT:
            if self.showingInfo:
                self.infoOffset += 1
                self.showInfo(10.0)
        elif action == ACTION_PREVIOUS_MENU:
            if self.showingInfo:
                self.hideInfo()
            else:
                dlg = xbmcgui.Dialog()

                if self.sleepTimeValue > 0:
                    if self.sleepTimer.isAlive():
                        self.sleepTimer.cancel()
                        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

                if dlg.yesno("Exit?", "Are you sure you want to exit TV Time?"):
                    self.end()
                else:
                    self.startSleepTimer()

                del dlg
        elif action == ACTION_SHOW_INFO:
            if self.showingInfo:
                self.hideInfo()
            else:
                self.showInfo(10.0)
        elif action >= ACTION_NUMBER_0 and action <= ACTION_NUMBER_9:
            if self.inputChannel < 0:
                self.inputChannel = action - ACTION_NUMBER_0
            else:
                if self.inputChannel < 100:
                    self.inputChannel = self.inputChannel * 10 + action - ACTION_NUMBER_0

            self.showChannelLabel(self.inputChannel)

        self.actionSemaphore.release()
        self.log('onAction return')


    # Reset the sleep timer
    def startSleepTimer(self):
        if self.sleepTimeValue == 0:
            return

        # Cancel the timer if itbis still running
        if self.sleepTimer.isAlive():
            self.sleepTimer.cancel()
            self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

        self.sleepTimer.start()


    # Reset the sleep timer
    def startAutoResetTimer(self):
        self.log("startAutoResetTimer: Started")
        self.log("startAutoResetTimer: self.autoResetTimeValue=" + str(self.autoResetTimeValue))
        if self.autoResetTimeValue == 0:
            return

        # Cancel the timer if it is still running
        if self.autoResetTimer.isAlive():
            self.autoResetTimer.cancel()
            self.autoResetTimer = threading.Timer(self.resetTimerValue, self.autoResetChannels)

        self.autoResetTimer.start()
        self.log("startAutoResetTimer: Completed")


    # This is called when the sleep timer expires
    def sleepAction(self):
        self.log("sleepAction")
        self.actionSemaphore.acquire()
#        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)
        # TODO: show some dialog, allow the user to cancel the sleep
        # perhaps modify the sleep time based on the current show
        self.end()
        self.actionSemaphore.release()


    # cleanup and end
    def end(self):
        self.log('end')
        
        try:
            if self.channelLabelTimer.isAlive():
                self.channelLabelTimer.cancel()

            if self.infoTimer.isAlive():
                self.infoTimer.cancel()

            if self.sleepTimeValue > 0:
                if self.sleepTimer.isAlive():
                    self.sleepTimer.cancel()

            if self.autoResetTimer > 0:
                if self.autoResetTimer.isAlive():
                    self.autoResetTimer.cancel()
        except:
            pass

        if xbmc.Player().isPlaying():
            xbmc.Player().stop()

        if self.timeStarted > 0:
            for i in range(self.maxChannels):
                if self.channels[i].isValid:
                    ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(int(time() - self.timeStarted + self.channels[i].totalTimePlayed)))

        try:
            ADDON_SETTINGS.setSetting('CurrentChannel', str(self.currentChannel))
        except:
            pass

        self.background.setVisible(False)
        self.close()
