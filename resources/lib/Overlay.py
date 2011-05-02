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

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading, thread
import datetime
import sys, re
import random

from operator import itemgetter
from time import time, localtime, strftime, strptime, mktime, sleep
from datetime import datetime, date, timedelta
from decimal import *

import Globals

from xml.dom.minidom import parse, parseString

from Playlist import Playlist
from Globals import *
from Channel import Channel
from EPGWindow import EPGWindow
from ChannelList import ChannelList
from PrestageThread import *


class MyPlayer(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self, xbmc.PLAYER_CORE_AUTO)
        self.stopped = False

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Player: ' + msg, level)

        
    def onPlayBackStopped(self):
        if self.stopped == False:
            self.log('Playback stopped')

            if self.overlay.sleepTimeValue == 0:
                self.overlay.sleepTimer = threading.Timer(1, self.overlay.sleepAction)
    
            self.overlay.sleepTimeValue = 1
            self.overlay.startSleepTimer()
            self.stopped = True


# overlay window to catch events and change channels
class TVOverlay(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.log('Overlay: __init__')
        # initialize all variables
        self.channels = []
        self.Player = MyPlayer()
        self.Player.overlay = self
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
        random.seed()

        for i in range(3):
            self.channelLabel.append(xbmcgui.ControlImage(50 + (50 * i), 50, 50, 50, IMAGES_LOC + 'solid.png', colorDiffuse='0xAA00ff00'))
            self.addControl(self.channelLabel[i])
            self.channelLabel[i].setVisible(False)

        self.doModal()
        self.log('Overlay: __init__ return')


    def resetChannelTimes(self):
        curtime = time.time()

        for i in range(self.maxChannels):
            self.channels[i].setAccessTime(curtime - self.channels[i].totalTimePlayed)


    def onFocus(self, controlId):
        pass


    # override the doModal function so we can setup everything first
    def onInit(self):
        self.log('Overlay: onInit')
        migrate()
        
        self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)
        self.infoTimer = threading.Timer(5.0, self.hideInfo)
        self.background = self.getControl(101)
        self.getControl(102).setVisible(False)
        self.channelList = ChannelList()
        # need to reset for scheduled auto channel reset
        Globals.prestageThreadExit = 0

        # setup directories
        self.createDirectories()

        # Copy feeds xml if it doesn't exist yet.
        #if not os.path.exists(FEED_LOC,"feeds.xml"):
        #    self.copyFeedsXML()
        
        self.myEPG = EPGWindow("script.pseudotv.EPG.xml", ADDON_INFO, "default")
        self.myEPG.MyOverlayWindow = self
        # Don't allow any actions during initialization
        self.actionSemaphore.acquire()

        self.log('Overlay: Read Config')
        if self.readConfig() == False:
            return

        # build meta files if first time loading
        if (
            REAL_SETTINGS.getSetting("bumpers") == "true" or 
            REAL_SETTINGS.getSetting("commercials") == "true" or  
            REAL_SETTINGS.getSetting("trailers") == "true"
            ):
            self.buildMetaFiles()

        # add a step to check settings2.xml exists
        if not os.path.exists(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/settings2.xml')):
            # if not, load presets
            self.log("Overlay: onInit - settings2.xml not found")
            self.channelList.autoTune()
        else:
            self.log("Overlay: onInit - settings2.xml found")

            autoFindMixGenres = REAL_SETTINGS.getSetting("autoFindMixGenres")        
            autoFindMovieGenres = REAL_SETTINGS.getSetting("autoFindMovieGenres")        
            autoFindNetworks = REAL_SETTINGS.getSetting("autoFindNetworks")        
            autoFindStudios = REAL_SETTINGS.getSetting("autoFindStudios")        
            autoFindTVGenres = REAL_SETTINGS.getSetting("autoFindTVGenres")        
            autoFindTVShows = REAL_SETTINGS.getSetting("autoFindTVShows")
            autoFindMusicGenres = REAL_SETTINGS.getSetting("autoFindMusicGenres")        

            self.log("autoFindMixGenres " + str(autoFindMixGenres)) 
            self.log("autoFindMovieGenres " + str(autoFindMovieGenres)) 
            self.log("autoFindNetworks " + str(autoFindNetworks)) 
            self.log("autoFindStudios " + str(autoFindStudios)) 
            self.log("autoFindTVGenres " + str(autoFindTVGenres)) 
            self.log("autoFindTVShows " + str(autoFindTVShows)) 
            self.log("autoFindMusicGenres " + str(autoFindMusicGenres)) 
            
            if (autoFindMixGenres == "true" or       
                autoFindMovieGenres == "true" or        
                autoFindNetworks == "true" or        
                autoFindStudios == "true" or   
                autoFindTVGenres == "true" or       
                autoFindTVShows == "true" or
                autoFindMusicGenres == "true"):
                Globals.resetSettings2 = 1
                Globals.resetPrestage = 1
                self.channelList.autoTune()

        # There are two types of force resets
        # 1. Force All Channels Reset (Addon Setting)
        # 2. Force a changed channel to reset (Channel Config Change) 
        forceReset = int(REAL_SETTINGS.getSetting("ForceChannelReset"))

        # Loop through each channel and determine if channel setting has changed
        self.dlg = xbmcgui.DialogProgress()
        self.dlg.create("TV Time", "Channel Check")
        progressIndicator = 0

        self.log("setMaxChannels")
        self.channelList.setMaxChannels()
        maxChannels = int(REAL_SETTINGS.getSetting("maxChannels"))

        for i in range(maxChannels):
            progressIndicator = progressIndicator + (100/maxChannels)
            self.dlg.update(progressIndicator,"Channel Check","Checking if Channel " + str(i+1) + " needs to be reset")
            channelChanged = ADDON_SETTINGS.getSetting("Channel_" + str(i+1) + "_changed")
            if channelChanged == "true":
                self.log("Channel Configuration Changed")
                self.log("Resetting Channel Playlist " + str(i+1))
                # rebuild playlist
                self.channelList.resetPlaylist(i+1)

                # force channel reset does not use pre-staged file lists
                # this will only reset the channel that changed
                # it will not reset channels which have not changed
                # only want to force channel reset once, so if force reset
                # is on then skip since we will force reset the channel later
                if forceReset == 0:
                    self.log("Force Channel " + str(i+1) + " Reset")
                    # reset only the specified channel
                    self.forceChannelReset(i+1)
                    Globals.resetPrestage = 1
                    
        self.dlg.close()

        # update settings2.xml file
        ADDON_SETTINGS.writeSettings()

        # pause while settings file is being written to
        while int(Globals.savingSettings) == 1:
            pass            

        # Check if a force reset is required for all channels
        # This will force rebuilding of ALL channel file lists
        if forceReset > 0:
            self.log("Force All Channels Reset")
            # reset all channels
            self.forceChannelReset("all")
            Globals.resetPrestage = 1
     
        # check auto reset
        if self.checkAutoChannelReset() == True:
            self.log("Auto Reset Channels")
            # auto channel reset copies over pre-staged file lists to speed up loading
            self.autoChannelReset()

        # time to load in the channels
        if self.loadChannels() == False:
            return

        self.myEPG.channelLogos = self.channelLogos
        self.maxChannels = len(self.channels)
        if self.maxChannels == 0:
            self.Error('Overlay: Unable to find any channels. Please configure the addon.')
            return

        found = False

        for i in range(self.maxChannels):
            if self.channels[i].isValid:
                self.log("Channel " + str(i) + " isValid")
                found = True
                break

        if found == False:
            self.Error("Overlay: No valid channel data found")
            return

        if self.sleepTimeValue > 0:
            self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

        # start thread to build prestage channel files in the background
        self.prestageThread = PrestageThread()
        self.prestageThread.start()

        # shutdown check timer
        self.shutdownTimer = threading.Timer(1, self.checkShutdownFlag)
        self.shutdownTimer.start()

        try:
            if self.forceReset == False:
                self.currentChannel = self.fixChannel(int(REAL_SETTINGS.getSetting("CurrentChannel")))
            else:
                self.currentChannel = self.fixChannel(1)
        except:
            self.currentChannel = self.fixChannel(1)

        self.resetChannelTimes()
        self.setChannel(self.currentChannel)
        self.timeStarted = time.time()
        
        if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.currentChannel) + "_type")) == 8:
            self.background.setVisible(False)
            xbmc.executebuiltin("ActivateWindow(12006)")
            
        else:
            self.background.setVisible(False)

        self.log("onInit: startSleepTimer")
        self.startSleepTimer()

        self.log("onInit: releasing semaphore")        
        self.actionSemaphore.release()

        self.log('Overlay: onInit return')


    def checkShutdownFlag(self):
        self.log("checkShutdownFlag")
        if Globals.userExit == 1:
            self.log("Calling TV Time Exit")
            self.shutdownTimer.cancel()
            self.end()
        else:
            self.log("Resetting checkShutdownFlag")
            self.shutdownTimer = threading.Timer(1, self.checkShutdownFlag)
            self.shutdownTimer.start()
        

    def createDirectories(self):
        self.log("createDirectories")
        # setup directories
        self.createDirectory(CHANNELS_LOC)
        self.createDirectory(GEN_CHAN_LOC)
        self.createDirectory(PRESTAGE_LOC)
        self.createDirectory(TEMP_LOC)
        self.createDirectory(META_LOC)
        self.createDirectory(FEED_LOC)
        

    def copyFeedsXML(self):
        self.log("createFeedXML")
        if not os.path.exists(FEED_LOC,"feeds.xml"):
            # copy default feeds.xml file
            self.channelList.copyFiles(os.path.join(os.path.join(ADDON_INFO, 'resources', 'feeds')), FEED_LOC)
            

    def buildMetaFiles(self):
        self.dlg = xbmcgui.DialogProgress()
        self.dlg.create("TV Time", "Initializing")
        progressIndicator = 0
        if REAL_SETTINGS.getSetting("bumpers"):
            if not os.path.exists(META_LOC + "bumpers.meta"):
                # prompt user that we need to build this meta file
                self.dlg.update(progressIndicator,"Initializing","Creating Bumper File List")
                bumpersfolder = REAL_SETTINGS.getSetting("bumpersfolder")
                if len(bumpersfolder) > 0:
                    self.buildMetaFile("bumpers",bumpersfolder)

        if REAL_SETTINGS.getSetting("commercials"):
            if not os.path.exists(META_LOC + "commercials.meta"):
                # prompt user that we need to build this meta file
                self.dlg.update(progressIndicator,"Initializing","Creating Commercial File List")
                commercialsfolder = REAL_SETTINGS.getSetting("commercialsfolder")
                if len(commercialsfolder) > 0:
                    self.buildMetaFile("commercials",commercialsfolder)

        if REAL_SETTINGS.getSetting("trailers"):
            if not os.path.exists(META_LOC + "trailers.meta"):
                # prompt user that we need to build this meta file
                self.dlg.update(progressIndicator,"Initializing","Creating Trailer File List")
                trailersfolder = REAL_SETTINGS.getSetting("trailersfolder")
                if len(trailersfolder) > 0:
                    self.buildMetaFile("trailers",trailersfolder)

        self.dlg.close()


    def buildMetaFile(self, type, folder):
        if (Globals.prestageThreadExit == 0):
            self.log("buildMetaFile")
            self.videoParser = VideoParser()
            flext = [".avi",".mp4",".m4v",".3gp",".3g2",".f4v",".flv",".mkv",".flv"]
            metaFileList = []

            if os.path.exists(folder):
                # get a list of valid filenames from the folder
                fnlist = []
                for root, subFolders, files in os.walk(folder):
                    for filename in files:
                        if (Globals.prestageThreadExit == 0): # pseudo break point to exit thread
                            # get file extension
                            basename, extension = os.path.splitext(filename)
                            if extension in flext: # passed first test
                                if (Globals.prestageThreadExit == 0):
                                    # get file duration
                                    filepath = os.path.join(root, filename)
                                    dur = self.videoParser.getVideoLength(filepath)
                                    if (dur > 0): # passed second test
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
                                        metastr = str(filepath) + '|' + str(dur) + '|' + str(title) + '|' + str(showtitle) + '|' + str(description)
                                        metaFileList.append(metastr)
                                else:
                                    self.abort()
                        else:
                            self.abort()
            self.writeMetaFile(type, metaFileList)
        else:
            self.abort()


    def writeMetaFile(self, type, metaFileList):
        if (Globals.prestageThreadExit == 0):
            try:
                metafile = open(META_LOC + str(type) + ".meta", "w")
            except:
                self.Error('Unable to open the meta file ' + META_LOC + str(type) + '.meta', xbmc.LOGERROR)
                return False

            for file in metaFileList:
                metafile.write(file + "\n")

            metafile.close()
        else:
            self.abort()
        

    # setup all basic configuration parameters, including creating the playlists that
    # will be used to actually run this thing
    def readConfig(self):
        self.log('readConfig')
        # Sleep setting is in 30 minute incriments...so multiply by 30, and then 60 (min to sec)
        self.sleepTimeValue = int(REAL_SETTINGS.getSetting('AutoOff')) * 1800
        self.log('readConfig: Auto off is ' + str(self.sleepTimeValue))
        self.infoOnChange = REAL_SETTINGS.getSetting("InfoOnChange") == "true"
        self.log('readConfig: Show info label on channel change is ' + str(self.infoOnChange))
        self.showChannelBug = REAL_SETTINGS.getSetting("ShowChannelBug") == "true"
        self.log('readConfig: Show channel bug - ' + str(self.showChannelBug))
        self.forceReset = REAL_SETTINGS.getSetting('ForceChannelReset') == "true"
        self.channelLogos = xbmc.translatePath(REAL_SETTINGS.getSetting('ChannelLogoFolder'))
        if self.channelLogos == "":
            self.channelLogos = xbmc.translatePath("special://home/addons/script.tvtime/resources/images/")

        if os.path.exists(self.channelLogos) == False:
            self.channelLogos = IMAGES_LOC

        self.log('readConfig: Channel logo folder - ' + self.channelLogos)
        self.startupTime = time.time()

        try:
            self.lastResetTime = int(REAL_SETTINGS.getSetting("LastResetTime"))
        except:
            self.lastResetTime = 0

        self.log('readConfig return')
        return True


    def loadChannels(self):
        self.log('loadChannels')    
        self.background.setVisible(True)
        self.channels = self.channelList.setupList()

        if self.channels is None:
            self.log('loadChannels: No channel list returned')
            self.log("loadChannels: calling end")
            self.end()
            return False

        self.Player.stop()
        return True


    def channelDown(self):
        self.log('channelDown')

        if self.maxChannels == 1:
            return

        self.background.setVisible(True)
        channel = self.fixChannel(self.currentChannel - 1, False)
        self.setChannel(channel)

        if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.currentChannel) + "_type")) == 8:
            self.background.setVisible(False)
            xbmc.executebuiltin("ActivateWindow(12006)")
        else:
            self.background.setVisible(False)

        self.log('channelDown return')


    def channelUp(self):
        self.log('channelUp')

        if self.maxChannels == 1:
            return

        self.background.setVisible(True)
        channel = self.fixChannel(self.currentChannel + 1)
        self.setChannel(channel)

        if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.currentChannel) + "_type")) == 8:
            self.background.setVisible(False)
            xbmc.executebuiltin("ActivateWindow(12006)")
        else:
            self.background.setVisible(False)

        self.log('channelUp return')


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
        self.getControl(102).setVisible(False)
        self.showingInfo = False

        # first of all, save playing state, time, and playlist offset for
        # the currently playing channel
        if self.Player.isPlaying():
            if channel != self.currentChannel:
                self.channels[self.currentChannel - 1].setPaused(xbmc.getCondVisibility('Player.Paused'))

                # Automatically pause in serial mode
                if self.channels[self.currentChannel - 1].mode & MODE_ALWAYSPAUSE > 0:
                    self.channels[self.currentChannel - 1].setPaused(True)

                self.channels[self.currentChannel - 1].setShowTime(self.Player.getTime())
                self.channels[self.currentChannel - 1].setShowPosition(xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition())
                self.channels[self.currentChannel - 1].setAccessTime(time.time())

        self.currentChannel = channel
        # now load the proper channel playlist
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        if xbmc.PlayList(xbmc.PLAYLIST_MUSIC).load(self.channels[channel - 1].fileName) == False:
            self.log("Error loading playlist")
            self.InvalidateChannel(channel)
            return

        # Disable auto playlist shuffling if it's on
        if xbmc.getInfoLabel('Playlist.Random').lower() == 'random':
            self.log('Random on.  Disabling.')
            xbmc.PlayList(xbmc.PLAYLIST_MUSIC).unshuffle()

        xbmc.executebuiltin("self.PlayerControl(repeatall)")

        timedif += (time.time() - self.channels[self.currentChannel - 1].lastAccessTime)

        # adjust the show and time offsets to properly position inside the playlist
        while self.channels[self.currentChannel - 1].showTimeOffset + timedif > self.channels[self.currentChannel - 1].getCurrentDuration():
            timedif -= self.channels[self.currentChannel - 1].getCurrentDuration() - self.channels[self.currentChannel - 1].showTimeOffset
            self.channels[self.currentChannel - 1].addShowPosition(1)
            self.channels[self.currentChannel - 1].setShowTime(0)

        # set the show offset
        self.Player.playselected(self.channels[self.currentChannel - 1].playlistPosition)
        # set the time offset
        self.channels[self.currentChannel - 1].setAccessTime(time.time())

        if self.channels[self.currentChannel - 1].isPaused:
            self.channels[self.currentChannel - 1].setPaused(False)

            try:
                self.Player.seekTime(self.channels[self.currentChannel - 1].showTimeOffset)
                
                if self.channels[self.currentChannel - 1].mode & MODE_ALWAYSPAUSE == 0:
                    self.Player.pause()
    
                    if self.waitForVideoPaused() == False:
                        return
            except:
                self.log('Exception during seek on paused channel', xbmc.LOGERROR)
        else:
            seektime = self.channels[self.currentChannel - 1].showTimeOffset + timedif

            try:
                self.Player.seekTime(seektime)
            except:
                self.log('Exception during seek', xbmc.LOGERROR)

        self.showChannelLabel(self.currentChannel)
        self.lastActionTime = time.time()
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

            if self.Player.isPlaying():
                if xbmc.getCondVisibility('Player.Paused'):
                    break

            sleeptime += 100
        else:
            self.log('Timeout waiting for pause', xbmc.LOGERROR)
            return False

        self.log('waitForVideoPaused return')
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
        self.getControl(506).setImage(self.channelLogos + self.channels[self.currentChannel - 1].name + '.png')
        self.log('setShowInfo return')


    # Display the current channel based on self.currentChannel.
    # Start the timer to hide it.
    def showChannelLabel(self, channel):
        self.log('showChannelLabel ' + str(channel))

        if self.channelLabelTimer.isAlive():
            self.channelLabelTimer.cancel()
            self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)

        tmp = self.inputChannel
        #self.hideChannelLabel()
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
            if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.currentChannel) + "_type")) == 8:
                self.background.setVisible(False)
                xbmc.executebuiltin("ActivateWindow(12006)")
            else:
                self.infoOffset = 0
                self.showInfo(5.0)

        if self.showChannelBug == True:
            try:
                self.getControl(103).setImage(self.channelLogos + self.channels[self.currentChannel - 1].name + '.png')
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
        self.log("acquiring semaphore")
        if self.actionSemaphore.acquire(False) == False:
            self.log('onAction: Unable to get semaphore')
            return
        else:
            lastaction = time.time() - self.lastActionTime

            # during certain times we just want to discard all input
            if lastaction < 2:
                # unless it is an exit action
                if action == ACTION_STOP:
                    Globals.userExit = 1                    
                    self.log("Exiting because user pressed exit")
                    #self.end()
                else:
                    self.log('Not allowing actions')
                    action = ACTION_INVALID

            self.log("onAction: startSleepTimer")
            self.startSleepTimer()

            if action == ACTION_SELECT_ITEM:
                # If we're manually typing the channel, set it now
                if self.inputChannel > 0:
                    if self.inputChannel != self.currentChannel:
                        self.setChannel(self.inputChannel)

                    if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.inputChannel) + "_type")) == 8:
                        self.background.setVisible(False)
                        xbmc.executebuiltin("ActivateWindow(12006)")
                    else:
                        self.background.setVisible(False)

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

                        if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.currentChannel) + "_type")) == 8:
                            self.background.setVisible(False)
                            xbmc.executebuiltin("ActivateWindow(12006)")
                        else:
                            self.background.setVisible(False)

            elif action == ACTION_MOVE_UP or action == ACTION_PAGEUP:
                self.channelUp()
            elif action == ACTION_MOVE_DOWN or action == ACTION_PAGEDOWN:
                self.channelDown()
            elif action == ACTION_MOVE_LEFT:
                if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.currentChannel) + "_type")) == 8:
                    self.background.setVisible(False)
                    xbmc.executebuiltin("ActivateWindow(12006)")
                else:
                    if self.showingInfo:
                        self.infoOffset -= 1
                        self.showInfo(10.0)
            elif action == ACTION_MOVE_RIGHT:
                if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.currentChannel) + "_type")) == 8:
                    self.background.setVisible(False)
                    xbmc.executebuiltin("ActivateWindow(12006)")
                else:
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

                    if dlg.yesno("Exit?", "Are you sure you want to exit TV Time?"):
                        Globals.userExit = 1
                        self.log("Exiting because user selected yes")
                        #self.end()
                    else:
                        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)
                        self.startSleepTimer()

                    del dlg
            elif action == ACTION_SHOW_INFO:
                if int(ADDON_SETTINGS.getSetting("Channel_" + str(self.currentChannel) + "_type")) == 8:
                    self.background.setVisible(False)
                    xbmc.executebuiltin("ActivateWindow(12006)")
                else:
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
            elif action == ACTION_OSD:
                xbmc.executebuiltin("ActivateWindow(12901)")
            elif action == ACTION_STOP:
                Globals.userExit = 1
                self.log("Exiting because user pressed exit")
                #self.end()

            self.log("onAction: releasing semaphore")
            self.actionSemaphore.release()
            self.log('onAction return')


    # Reset the sleep timer
    def startSleepTimer(self):
        if self.sleepTimeValue == 0:
            return

        # Cancel the timer if it is still running
        if self.sleepTimer.isAlive():
            self.sleepTimer.cancel()            
            # resetting sleep time value
            self.sleepTimeValue = int(REAL_SETTINGS.getSetting('AutoOff')) * 1800
            self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)
            self.sleepTimer.start()


    # This is called when the sleep timer expires
    def sleepAction(self):
        self.log("sleepAction: acquiring semaphore")
        # TODO: show some dialog, allow the user to cancel the sleep
        # perhaps modify the sleep time based on the current show
        self.log("sleepAction: calling end")
        self.end()


    # cleanup and end
    def end(self):
        self.log("end")
        self.background.setVisible(True)
        # add a control to block script from calling end twice
        # unsure why it does sometimes
        if Globals.exitingTVTime == 0:
            Globals.exitingTVTime = 1
            self.log('EXITING TV TIME')

            # trigger prestage thread to exit
            self.log("end: triggering prestage thread to exit")
            Globals.prestageThreadExit = 1

            # wait a few seconds to allow script to exit threads, etc.
            self.dlg = xbmcgui.DialogProgress()
            self.dlg.create("TV Time", "Exiting")
            self.dlg.update(0,"Exiting TV Time","Please wait...")
            time.sleep(3)

            # shutdown check timer
            self.shutdownTimer = threading.Timer(1, self.checkShutdownFlag)
            self.shutdownTimer.start()

            try:
                if self.shutdownTimer.isAlive():
                    self.log("shutdownTimer is still alive")
                    self.shutdownTimer.cancel()
                    self.log("channelLabelTimer is cancelled")
            except:
                self.log("error cancelling shutdownTimer")
                pass

            try:
                if self.channelLabelTimer.isAlive():
                    self.log("channelLabelTimer is still alive")
                    self.channelLabelTimer.cancel()
                    self.log("channelLabelTimer is cancelled")
            except:
                self.log("error cancelling channelLabelTimer")
                pass

            try:
                if self.infoTimer.isAlive():
                    self.log("infoTimer is still alive")
                    self.infoTimer.cancel()
                    self.log("infoTimer is cancelled")
            except:
                self.log("error cancelling infoTimer")
                pass
                
            try:
                if self.sleepTimeValue > 0:
                    if self.sleepTimer.isAlive():
                        self.log("sleepTimer is still alive")
                        self.sleepTimer.cancel()
                        self.log("sleepTimer is cancelled")
            except:
                self.log("error cancelling sleepTimer")
                pass

            #if self.autoResetTimer > 0:
            try:
                if self.autoResetTimer.isAlive():
                    self.log("autoResetTimer is still alive")
                    self.autoResetTimer.cancel()
                    self.log("autoResetTimer is cancelled")                 
            except:
                self.log("error cancelling autoResetTimer")
                pass

            if self.Player.isPlaying():
                self.Player.stop()

            if self.timeStarted > 0 and int(Globals.channelsReset) == 0:
#                for i in range(self.maxChannels):
                for i in range(int(REAL_SETTINGS.getSetting("maxChannels"))):
                    if self.channels[i].isValid:
                        if self.channels[i].mode & MODE_RESUME == 0:
                            ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(int(time.time() - self.timeStarted + self.channels[i].totalTimePlayed)))
                        else:
                            tottime = 0

                            for j in range(self.channels[i].playlistPosition):
                                tottime += self.channels[i].getItemDuration(j)

                            tottime += self.channels[i].showTimeOffset

                            if i == self.currentChannel - 1:
                                tottime += (time.time() - self.channels[i].lastAccessTime)

                            ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(int(tottime)))
                ADDON_SETTINGS.writeSettings()

            try:
                REAL_SETTINGS.setSetting('CurrentChannel', str(self.currentChannel))
            except:
                pass

            # wait while settings file is being written to
            # settings2.xml wasn't being completely written to
            # before script would end
            while int(Globals.savingSettings) == 1:
                self.dlg.update(25,"Exiting TV Time","Waiting on settings to be saved...")
                pass

            self.dlg.update(50,"Exiting TV Time","Please wait...")
            time.sleep(3)
            self.dlg.close()
                                
            self.background.setVisible(False)

            # need to distinguish between user eXits and auto shutdown
            if int(Globals.userExit) == 0 and REAL_SETTINGS.getSetting("autoChannelResetShutdown") == "true":
                #print xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "JSONRPC.Introspect", "id": 1}')
                #XBMC.Quit
                self.log("Exiting XBMC")             
                json_query = '{"jsonrpc": "2.0", "method": "XBMC.Quit", "id": 1}'
                xbmc.executeJSONRPC(json_query)
                #self.close()
            else:
                self.close()

            self.log("Threads - " + str(threading.enumerate()))

        else:
            self.log("TVTime already triggered end")


#####################################################
#####################################################
#
# Channel Reset Functions
#
#####################################################
#####################################################

    # rebuild filelists
    def forceChannelReset(self, channel):
        self.log('forceChannelReset: Channel ' + str(channel))
        self.channels = []

        if channel == "all":
            # reset all channels
            # we only want one reset occuring at a time so let's put a check in
            if Globals.forceChannelResetActive == 0:
                Globals.forceChannelResetActive = 1
                REAL_SETTINGS.setSetting('LastResetTime', str( int ( time.time() ) ) )
                # if force reset, delete all cache files 
                self.channelList.deleteFiles(CHANNELS_LOC)
                # if force reset, delete all prestage files
                self.channelList.deleteFiles(PRESTAGE_LOC)
                # call function to rebuild all channel file lists
                self.channelList.buildChannelFileList(CHANNELS_LOC, "all")
                # reset finished
                Globals.channelsReset = 1
                Globals.forceChannelResetActive = 0
            else:
                pass
        else:
            # only reset the channel passed
            if Globals.forceChannelResetActive == 0:
                Globals.forceChannelResetActive = 1
                filename = "Channel_" + str(channel) + ".m3u"
                REAL_SETTINGS.setSetting('LastResetTime', str(int(time.time())))
                # delete cache file 
                if os.path.exists(os.path.join(CHANNELS_LOC, filename)):
                    os.remove(os.path.join(CHANNELS_LOC, filename))
                # delete prestage files
                if os.path.exists(os.path.join(PRESTAGE_LOC, filename)):
                    os.remove(os.path.join(PRESTAGE_LOC, filename))
                # call function to rebuild channel file lists
                self.channelList.buildChannelFileList(CHANNELS_LOC, channel)
                # reset finished
                Globals.channelsReset = 1
                Globals.forceChannelResetActive = 0
            
    
    # check if auto reset times have expired
    def checkAutoChannelReset(self):
        needsreset = False
        """
        autoChannelResetSetting
          values:
            0 = automatic
            1 = each day
            2 = each week
            3 = each month
            4 = scheduled
        """
        autoChannelResetSetting = int(REAL_SETTINGS.getSetting("autoChannelResetSetting"))
        if autoChannelResetSetting == "":
            autoChannelResetSetting = 0
        """
        if autoChannelResetSetting is set to automatic
          loop through all channels to get their totalduration and time values
          if total time played for the channel is greater than total duration
          watched since last auto reset, then set needsreset flag to true
        """
        if autoChannelResetSetting == 0:
            # need to get channel settings
            self.channels = []
            needsreset = False
            # loop through channel settings to get
            #   totalTimePlayed
            #   totalDuration
            for i in range(int(REAL_SETTINGS.getSetting("maxChannels"))):                
                if not ADDON_SETTINGS.getSetting("Channel_" + str(i+1) + "_offair") == "1":
                    # need to figure out how to store 
                    totalTimePlayed = ADDON_SETTINGS.getSetting("Channel_" + str(i+1) + "_time")
                    if totalTimePlayed == "":
                        totalTimePlayed = 0

                    totalDuration =  ADDON_SETTINGS.getSetting("Channel_" + str(i+1) + "_totalDuration")
                    if totalDuration == "":
                        totalDuration = 0

                    if totalTimePlayed > totalDuration:
                        needsreset = True
        
            if needsreset:
                REAL_SETTINGS.setSetting('LastResetTime', str(int(time.time())))

        elif autoChannelResetSetting > 0 and autoChannelResetSetting < 4: # each day, each week, each month
            try:
                self.lastResetTime = int(REAL_SETTINGS.getSetting("LastResetTime"))
            except:
                self.lastResetTime = 0
            
            timedif = time.time() - self.lastResetTime

            if autoChannelResetSetting == 1 and timedif > (60 * 60 * 24):
                needsreset = True

            if autoChannelResetSetting == 2 and timedif > (60 * 60 * 24 * 7):
                needsreset = True

            if autoChannelResetSetting == 3 and timedif > (60 * 60 * 24 * 30):
                needsreset = True

            if timedif < 0:
                needsreset = True

            if needsreset:
                REAL_SETTINGS.setSetting('LastResetTime', str(int(time.time())))

        elif autoChannelResetSetting == 4: # scheduled
            """
            if autoChannelResetSetting = 4, 
              set next reset date/time, 
              set timer until next reset date/time, 
              start auto reset timer
            """
            if REAL_SETTINGS.getSetting('nextAutoResetDateTime') == "":
                self.setNextAutoResetTime()
            elif REAL_SETTINGS.getSetting('nextAutoResetDateTimeInterval') <> REAL_SETTINGS.getSetting('ChannelResetSetting'):
                self.setNextAutoResetTime()
            elif REAL_SETTINGS.getSetting('nextAutoResetDateTimeResetTime') <> REAL_SETTINGS.getSetting('ChannelResetSettingTime'):
                self.setNextAutoResetTime()
            # set auto reset timer
            self.setAutoResetTimer()
            # start auto reset timer
            self.startAutoResetTimer()

        return needsreset

    
    def setNextAutoResetTime(self):
        # set next auto resetChannel time
        # need to get current datetime in local time
        currentDateTimeTuple = localtime()
        # parse out year, month and day so we can computer resetDate
        cd = datetime.datetime(*(currentDateTimeTuple[0:6]))
        year = cd.strftime('%Y')
        month = cd.strftime('%m')
        day = cd.strftime('%d')
        hour = cd.strftime('%H')
        minutes = cd.strftime('%M')
        seconds = cd.strftime('%S')
        # convert to date object so we can add timedelta in the next step
        currentDateTime = year + "-" + month + "-" + day + " " + hour + ":" + minutes + ":" + seconds
        currentDateTimeTuple = strptime(currentDateTime,"%Y-%m-%d %H:%M:%S")
        currentDate = date(int(year), int(month), int(day))
        # need to get setting of when to auto reset
        # Daily|Weekly|Monthly
        # 0 = Daily
        # 1 = Weekly
        # 2 = Monthly
        # Daily = Current Date + 1 Day
        # Weekly = CUrrent Date + 1 Week
        # Monthly = CUrrent Date + 1 Month
        resetInterval = REAL_SETTINGS.getSetting("autoChannelResetInterval")
        # Time to Reset: 12:00am, 1:00am, 2:00am, etc.
        # get resetTime setting
        resetTime = REAL_SETTINGS.getSetting("autoChannelResetTime")

        if resetInterval == "0":
            # Daily
            interval = timedelta(days=1)
        elif resetInterval == "1":
            # Weekly
            interval = timedelta(days=7)
        elif resetInterval == "2":
            # Monthly
            interval = timedelta(days=30)

        # determine resetDate based on current date and interval
        if resetTime > hour and resetInterval == "0":
            resetDate = currentDate
        else:
            resetDate = currentDate + interval        
        
        # need to convert to tuple to be able to parse out components
        resetDateTuple = strptime(str(resetDate), "%Y-%m-%d")
        # parse out year, month, and day
        rd = datetime.datetime(*(resetDateTuple[0:3]))
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
        REAL_SETTINGS.setSetting('nextAutoResetDateTime', str(resetDateTime))        
        REAL_SETTINGS.setSetting('nextAutoResetDateTimeInterval', str(resetInterval))        
        REAL_SETTINGS.setSetting('nextAutoResetDateTimeResetTime', str(resetTime))        
        

    def setAutoResetTimer(self):
        # set next auto resetChannel time
        # need to get current datetime in local time
        currentDateTimeTuple = localtime()       
        nextAutoResetDateTime = REAL_SETTINGS.getSetting('nextAutoResetDateTime')
        nextAutoResetDateTimeTuple = strptime(nextAutoResetDateTime,"%Y-%m-%d %H:%M:%S")       
        # need to get difference between the two
        self.autoResetTimeValue = mktime(nextAutoResetDateTimeTuple) - mktime(currentDateTimeTuple)
        # set timer
        self.autoResetTimer = threading.Timer(self.autoResetTimeValue, self.autoChannelReset)


    # Reset the sleep timer
    def startAutoResetTimer(self):
        if self.autoResetTimeValue == 0:
            return
        # Cancel the auto reset timer if it is still running
        if self.autoResetTimer.isAlive():
            self.autoResetTimer.cancel()
            self.autoResetTimer = threading.Timer(self.resetTimerValue, self.autoChannelReset)
        self.autoResetTimer.start()


    def autoChannelReset(self):
        self.log("autoChannelReset")
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
            if Globals.autoResetChannelActive == 0:
                # trigger prestage thread to exit
                Globals.prestageThreadExit = 1
                # block any attempt to run concurrent auto channel resets
                Globals.autoResetChannelActive = 1
                self.log("autoChannelReset: reset started")
                # reset started
                REAL_SETTINGS.setSetting('LastResetTime', str( int ( time.time() ) ) )
                # delete previous files in the cache
                self.log("autoChannelReset: delete previous files in the cache")
                self.channelList.deleteFiles(CHANNELS_LOC)        
                # copy pre-staged channel file lists to cache
                self.log("autoChannelReset: copying prestaged files to the cache")
                self.channelList.copyFiles(PRESTAGE_LOC, CHANNELS_LOC)
                # reset next auto reset time
                self.setNextAutoResetTime()
                try:
                    if self.channelLabelTimer.isAlive():
                        self.channelLabelTimer.cancel()
                    if self.infoTimer.isAlive():
                        self.infoTimer.cancel()
                    if self.sleepTimer.isAlive():
                        self.sleepTimer.cancel()
                    if self.autoResetTimer.isAlive():
                        self.autoResetTimer.cancel()
                except:
                    pass

                if xbmc.Player().isPlaying():
                    xbmc.Player().stop()
                
                # reset channel times
                if self.timeStarted > 0:
                    for i in range(int(REAL_SETTINGS.getSetting("maxChannels"))):
                        if self.channels[i].isValid:
                            #ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(int(time() - self.timeStarted + self.channels[i].totalTimePlayed)))
                            channel = i + 1
                            ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_time","0")
                            totalDuration = self.channelList.getTotalDuration(channel,CHANNELS_LOC)
                            ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_totalDuration",str(totalDuration))

                try:
                    ADDON_SETTINGS.setSetting('CurrentChannel', str(self.currentChannel))
                except:
                    pass        

                ADDON_SETTINGS.writeSettings()

                Globals.channelsReset = 1
                Globals.autoResetChannelActive = 0

                # need to find right way to re initialize the script
                # reload channels
                # update EPC and restart
                autoChannelResetSetting = int(REAL_SETTINGS.getSetting("autoChannelResetSetting"))
                if autoChannelResetSetting > 0 and autoChannelResetSetting < 5:
                    if REAL_SETTINGS.getSetting("autoChannelResetShutdown") == "false":
                        self.log("Restarting TV Time")
                        self.__init__()
                    else:
                        self.log("Exiting because auto channel reset shutdown")
                        self.end()
                    

#####################################################
#####################################################
#
# Utility Functions
#
#####################################################
#####################################################

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('TVOverlay: ' + msg, level)


    def createDirectory(self, directory):
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except:
                self.Error('Unable to create the directory - ' + str(directory))
                return


    # handle fatal errors: log it, show the dialog, and exit
    def Error(self, message):
        self.log('FATAL ERROR: ' + message, xbmc.LOGFATAL)
        dlg = xbmcgui.Dialog()
        dlg.ok('Error', message)
        del dlg
        self.log("Error: calling end")
        self.end()


    def message(self, data):
        log('Dialog message: ' + data)
        dlg = xbmcgui.Dialog()
        dlg.ok('Info', data)
        del dlg


    def countdown(self, secs, interval=1): 
        while secs > 0: 
            yield secs 
            secs = secs - 1 
            sleep(interval) 

