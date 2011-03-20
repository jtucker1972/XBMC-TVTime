#   Copyright (C) 2011 James A. Tucker
#
# This file is part of TVTime
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
#

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading
import datetime
import sys, re
import random
from operator import itemgetter

from xml.dom.minidom import parse, parseString

from Playlist import Playlist
from Globals import *
from Channel import Channel
from EPGWindow import EPGWindow
from VideoParser import VideoParser

from PresetChannels import *


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
        random.seed()

        for i in range(3):
            self.channelLabel.append(xbmcgui.ControlImage(50 + (50 * i), 50, 50, 50, IMAGES_LOC + 'solid.png', colorDiffuse='0xAA00ff00'))
            self.addControl(self.channelLabel[i])
            self.channelLabel[i].setVisible(False)

        self.doModal()
        self.log('__init__ return')


    def resetChannelTimes(self):
        curtime = time.time()

        for i in range(self.maxChannels):
            self.channels[i].setAccessTime(curtime - self.channels[i].totalTimePlayed)


    def onFocus(self, controlId):
        pass


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
    

    # override the doModal function so we can setup everything first
    def onInit(self):
        self.log('onInit')
        self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)
        self.infoTimer = threading.Timer(5.0, self.hideInfo)
        self.background = self.getControl(101)
        self.getControl(102).setVisible(False)

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

        if self.forceReset == True:
            self.resetChannels()
            
        # Get Maximum Number of M3u's after all channels have been built from playlists
        # maxM3uNum = self.findMaxM3us()
        
        self.maxChannels = self.findMaxM3us()

        if self.maxChannels == 0:
            self.Error('Unable to find any channels. Create smart\nplaylists with file names Channel_1, Chanbel_2, etc.')
            return
        else:
            self.log('onInit: self.maxChannels = ' + str(self.maxChannels))

        # Load channel m3u files
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
        self.timeStarted = time.time()
        self.background.setVisible(False)
        self.startSleepTimer()
        self.actionSemaphore.release()
        self.log('onInit return')


    def resetChannels(self):
        # if force reset, delete old cache 
        self.deleteCache()        
        # call creatChannels function to rebuild playlists
        self.buildPlaylists()
        # load in new playlists to create new m3u files
        self.loadPlaylists()
    

    def validateChannels(self):
        found = False
        for m3uNum in range(self.maxChannels):
            if self.channels[m3uNum].isValid:
                self.log("Channel: " + str(m3uNum) + " is valid")
                found = True
                return True
        if found == False:
            return False


    # Determine the maximum number of channels by opening consecutive
    # m3u until we don't find one
    def findMaxM3us(self):
        self.log('findMaxChannels')
        notfound = False
        channelNum = 1

        while notfound == False:
            self.log("findMaxM3us: " + str(channelNum) )
            self.log("findMaxM3us: getM3uFilename: " + self.getM3uFilename(channelNum))
            if len(self.getM3uFilename(channelNum)) == 0:
                break
            channelNum += 1

        findMaxM3us = channelNum - 1
        self.log('findMaxM3us return ' + str(findMaxM3us))
        return findMaxM3us


    # setup all basic configuration parameters, including creating the playlists that
    # will be used to actually run this thing
    def readConfig(self):
        self.log('readConfig')
        self.updateDialog = xbmcgui.DialogProgress()
        # Sleep setting is in 30 minute incriments...so multiply by 30, and then 60 (min to sec)
        self.sleepTimeValue = int(ADDON_SETTINGS.getSetting('AutoOff')) * 1800
        self.log('Auto off is ' + str(self.sleepTimeValue))
        self.forceReset = ADDON_SETTINGS.getSetting('ForceChannelReset') == "true"
        self.log('Force Reset is ' + str(self.forceReset))
        self.infoOnChange = ADDON_SETTINGS.getSetting("InfoOnChange") == "true"
        self.log('Show info label on channel change is ' + str(self.infoOnChange))
        self.channelResetSetting = int(ADDON_SETTINGS.getSetting("ChannelResetSetting"))
        self.log('Channel Reset Setting is ' + str(self.channelResetSetting))
        self.showChannelBug = ADDON_SETTINGS.getSetting("ShowChannelBug") == "true"
        self.log('Show channel bug - ' + str(self.showChannelBug))

        try:
            self.lastResetTime = int(ADDON_SETTINGS.getSetting("LastResetTime"))
        except:
            self.lastResetTime = 0


    def buildPlaylists(self):
        # Give some feedback to the user
        self.loadDialog = xbmcgui.DialogProgress()
        self.loadDialog.create("XBTV", "Preparing for Playlist Creation")
        self.loadDialog.update(0, "Preparing for Playlist Creation")        

        # Setup Preset Channel Object
        self.presetChannels = presetChannels()
        # Auto Fill Custom Config channels
        if ADDON_SETTINGS.getSetting("autoFillCustom") == "true":
            self.loadDialog.update(25, "Auto Filling Custom Channels")
            self.presetChannels.fillCustomChannels()        
        # Load Preset Channels from configuration settings
        self.loadDialog.update(50, "Reading Channel Management Settings")
        self.presetChannels.readPresetChannelConfig()
        # Get total number of Preset Channels (maxChannels)
        self.numPresetChannels = self.presetChannels.findMaxPresetChannels()
        self.loadDialog.update(75, "Creating " + str(self.numPresetChannels) + " Channel Playlists")
        # Delete Previous Channels
        self.presetChannels.deletePresetChannels()
        self.loadDialog.update(100, "Playlist Creation Prep Complete")

        # If the user pressed cancel, stop everything and exit
        if self.loadDialog.iscanceled():
            self.log('Playlist Creation Cancelled')
            self.loadDialog.close()
            self.end()
            return False
        self.loadDialog.close()        

        # Build the Preset Channel Playlists
        self.presetChannels.buildPresetChannels(self.numPresetChannels)

#
# on forceReset, load new playlists and call buildChannel to create m3u
#
    def loadPlaylists(self):
        self.log("loadPlaylists")
        self.startupTime = time.time()
        self.updateDialog.create("XBTV", "Building channel list")
        self.updateDialog.update(0, "Building channel list")
        self.background.setVisible(True)

        self.channelList = []
        playlistNum = 0

        # Go through all channels, create their arrays, and setup the new playlist
        for playlistNum in range(self.numPresetChannels):
            playlistNum = playlistNum + 1
            self.updateDialog.update(playlistNum * 100 // self.numPresetChannels, "Building channel " + str(playlistNum))
            self.channels.append(Channel())
            # If the user pressed cancel, stop everything and exit
            if self.updateDialog.iscanceled():
                self.log('Update channels cancelled')
                self.updateDialog.close()
                self.end()
                return False
            # 
            self.buildChannel(playlistNum)

        # write channelList settings to xml file for reference when rebuilding a channel
        self.log("length of channelList: " + str(len(self.channelList)))
        self.buildChannelsXML(self.channelList)

        self.updateDialog.update(100, "Build complete")
        xbmc.Player().stop()
        self.updateDialog.close()
        ADDON_SETTINGS.setSetting('ForceChannelReset', 'false')
        return True


#
# loops through all the created m3u's and calls loadChannel
#
    def loadChannels(self):
        self.startupTime = time.time()
        self.updateDialog.create("XBTV", "Loading channel list")
        self.updateDialog.update(0, "Loading channel list")
        self.background.setVisible(True)
        self.log("self.maxChannels: " + str(self.maxChannels))
        # Go through all channels, create their arrays, and setup the new playlist
        for m3uNum in range(self.maxChannels):
            self.updateDialog.update(self.maxChannels * 100 // self.maxChannels, "Loading channel " + str(m3uNum + 1))
            # create new channel
            self.channels.append(Channel())
            # If the user pressed cancel, stop everything and exit
            if self.updateDialog.iscanceled():
                self.log('Update channels cancelled')
                self.updateDialog.close()
                self.end()
                return False
            # 
            self.log("loadChannel: " + str(m3uNum + 1))
            self.loadChannel(m3uNum + 1)

        ADDON_SETTINGS.setSetting('ForceChannelReset', 'false')
        self.forceReset = False

        self.updateDialog.update(100, "Load complete")
        xbmc.Player().stop()
        self.updateDialog.close()
        self.log('readConfig return')
        return True

#
# load existing playlist for the channel, but check to see if reset is required
# if reset required call buildChannel
#
    def loadChannel(self, m3uNum):
        returnval = False
        resetChannel = False
        channel = int(m3uNum - 1)
        self.log("loadChannel: " + str(m3uNum))
        # If possible, use an existing playlist
        if os.path.exists(CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u'):
            try:
                self.channels[channel].totalTimePlayed = int(ADDON_SETTINGS.getSetting('Channel_' + str(m3uNum) + '_time'))

                if self.channels[channel].setPlaylist(CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u') == True:
                    self.channels[channel].isValid = True
                    self.channels[channel].fileName = CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u'
                    returnval = True

                    # channelResetSetting:
                    # 0 = Automatic
                    # 1 = Every Day
                    # 2 = Every Week
                    # 3 = Every Month
                    # 4 = Never
                    
                    if self.channelResetSetting == 0 and self.channels[channel].totalTimePlayed > self.channels[channel].getTotalDuration():
                        resetChannel = True

                    if self.channelResetSetting > 0 and self.channelResetSetting < 4:
                        timedif = time.time() - self.lastResetTime

                        if self.channelResetSetting == 1 and timedif > (60 * 60 * 24): # 1 day
                            resetChannel = True

                        if self.channelResetSetting == 2 and timedif > (60 * 60 * 24 * 7): # 7 days
                            resetChannel = True

                        if self.channelResetSetting == 3 and timedif > (60 * 60 * 24 * 30): # 30 days
                            resetChannel = True

                        if timedif < 0:
                            resetChannel = True

# don't reset time until after successful resetting
#                        if resetChannel:
#                            ADDON_SETTINGS.setSetting('LastResetTime', str(int(time.time())))

            except:
                pass

        if resetChannel:
#            self.rebuildChannel(m3uNum)
            self.resetChannels()

    # create new m3u for channel and initialize channel
    def buildChannel(self, playlistNum):
        self.log("buildChannel: " + str(playlistNum))
        # now let's create new channels
        if self.makeChannelList(playlistNum) == True:
            # the m3u channel number may not be the same as the playlist channel number            
            channelNum = self.nextM3uChannelNum
            
            # keep a list of which playlists are associated with which channels
            self.channelList.append(playlistNum)
            
            self.log(CHANNELS_LOC + 'channel_' + str(channelNum) + '.m3u created successfully.  Add channel to EPG')
            if self.channels[channelNum - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channelNum) + '.m3u') == True:
                self.channels[channelNum - 1].totalTimePlayed = 0
                self.channels[channelNum - 1].isValid = True
                self.channels[channelNum - 1].fileName = CHANNELS_LOC + 'channel_' + str(channelNum) + '.m3u'
                returnval = True
                ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_time', '0')
            self.channels[channelNum - 1].name = self.getSmartPlaylistName(self.getSmartPlaylistFilename(playlistNum))
            return returnval
            # load new channel
            self.log("buildChannel: Loading new channel")
            self.loadChannel(channelNum)
        else:
            pass


    # rebuild m3u for channel and initialize channel
    def rebuildChannel(self, m3uNum):
        self.log("rebuildChannel: " + str(m3uNum))

        playlistNum = ""
        
        # lookup playlistNum for channel in channels.xml
        playlistNum = self.getChannelPlaylistNum(m3uNum-1)
        if playlistNum <> "":
            # now let's create new channels
            if self.makeChannelList(playlistNum, m3uNum) == True:
                self.log(CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u rebuilt successfully.  Refreshing channel in EPG')
                if self.channels[m3uNum - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u') == True:
                    self.channels[m3uNum - 1].totalTimePlayed = 0
                    self.channels[m3uNum - 1].isValid = True
                    self.channels[m3uNum - 1].fileName = CHANNELS_LOC + 'channel_' + str(m3uNum) + '.m3u'
                    returnval = True
                    ADDON_SETTINGS.setSetting('Channel_' + str(m3uNum) + '_time', '0')
                self.channels[m3uNum - 1].name = self.getSmartPlaylistName(self.getSmartPlaylistFilename(playlistNum))
                return returnval
                # load new channel
                self.log("rebuildChannel: Reloading channel")
                self.loadChannel(m3uNum)
            else:
                pass
        else:
            self.log("No channel found in channels.xml for Channel_" + str(m3uNum) + ".m3u")
            return False


    def getChannelPlaylistNum(self, channelNum):
        self.log("getChannelPlaylist:")
        # check if channels.xml file exists
        filename = 'channels.xml'
        if os.path.exists(os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/'), filename)):
            fle = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/'), filename)
            self.log("found channels.xml")
        else:
            self.log("no channels.xml file found")
            return False
        
        # read in channels.xml file
        dom = self.getChannelsXML(fle)
        
        # lookup channel node matching id = channelNum
        channelList = dom.getElementsByTagName('channel')
        for i in range(len(channelList)):
            channel = channelList[i]
            channelNum2 = channel.attributes["channelNum"]
            playlistNum = channel.attributes["playlistNum"]
            if int(channelNum2.value) == int(channelNum):
                self.log("Found channel playlist: " + str(playlistNum.value))
                return playlistNum.value

    
    def buildChannelsXML(self, channelList):
        self.log("buildChannelsXML:")
        # create xml doc
        channelsXML = self.createChannelsXML()
        # add channels element
        channels = self.addChannels(channelsXML)
        # add channel elements
        for channelNum in range(len(channelList)):
            playlistNum = channelList[channelNum]
            self.addChannel(channelsXML, channels, channelNum, playlistNum)
            self.log("channeNum=" + str(channelNum))
            self.log("playlistNum=" + str(playlistNum))
            channelNum = channelNum + 1        
        # write xml to file
        self.writeChannelsXML(channelsXML)


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
        self.log('getChannelsXML:')       
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


    # Based on a smart playlist, create a normal playlist that can actually be used by us
    # make m3u file
    def makeChannelList(self, playlistNum, m3uNum=None):
        self.log('makeChannelList ' + str(playlistNum))
        
        fle = self.getSmartPlaylistFilename(playlistNum)

        if len(fle) == 0:
            self.log('Unable to locate the playlist for channel ' + str(playlistNum), xbmc.LOGERROR)
            return False

        try:
            xml = open(fle, "r")
        except:
            self.log("makeChannelList Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return False

        try:
            dom = parse(xml)
        except:
            self.log('makeChannelList Problem parsing playlist ' + fle, xbmc.LOGERROR)
            xml.close()
            return False

        xml.close()
        
        if self.getSmartPlaylistType(dom) == 'mixed':
            self.fileLists = []
            self.level = 0
            self.fileLists = self.buildMixedFileLists(fle)            
            if not "movies" in self.fileLists and not "episodes" in self.fileLists:
                self.log("mix tvshow channel")
                fileList = self.buildMixedTVShowFileList(self.fileLists)
            else:
                fileList = self.buildMixedFileList(self.fileLists)
        else:
            fileList = self.buildFileList(fle)

        try:
            order = dom.getElementsByTagName('order')
            if order[0].childNodes[0].nodeValue.lower() == 'random':
                random.shuffle(fileList)
        except:
            pass
        
        # check if fileList contains files
        if len(fileList) == 0:
#            self.log("Unable to get information about channel " + str(playlistNum), xbmc.LOGERROR)
            self.log("Playlist returned no files", xbmc.LOGERROR)
            return False
        else:
            # valid channel
            if m3uNum == None:
                self.nextM3uChannelNum = self.nextM3uChannelNum + 1
                m3uNum = self.nextM3uChannelNum
                self.log("self.nextM3uChannelNum: " + str(self.nextM3uChannelNum))
            
            if self.writeM3u(m3uNum, fileList) == True:
                return True
            else:
                return False


    def writeM3u(self, channelNum, fileList):
        try:
           channelplaylist = open(CHANNELS_LOC + "channel_" + str(channelNum) + ".m3u", "w")
        except:
            self.Error('Unable to open the cache file ' + CHANNELS_LOC + 'channel_' + str(channelNum) + '.m3u', xbmc.LOGERROR)
            return False
        
        self.log("created m3u file " + CHANNELS_LOC + "channel_" + str(channelNum) + ".m3u successfully") 

        channelplaylist.write("#EXTM3U\n")

        fileList = fileList[:250]

        # Write each entry into the new playlist
        for string in fileList:
            channelplaylist.write("#EXTINF:" + string + "\n")

        channelplaylist.close()
        self.log('makeChannelList return')

        return True


    def getM3uFilename(self, channel):
        self.log("getM3uFilename: channel=" + str(channel))
        self.log(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache') + '/Channel_' + str(channel) + '.m3u')
        if os.path.exists(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache') + '/Channel_' + str(channel) + '.m3u'):
            self.log("getM3uFilename: File found")
            return xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache') + '/Channel_' + str(channel) + '.m3u'
        else:
            self.log("getM3uFilename: File not found")
            return ""
    
    def getSmartPlaylistFilename(self, playlistNum):
        self.log("getSmartPlaylistFilename: " + str(playlistNum))
        self.log(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets') + '/Channel_' + str(playlistNum) + '.xsp')
        if os.path.exists(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets') + '/Channel_' + str(playlistNum) + '.xsp'):
            self.log("getSmartPlaylistFilename: File found")
            return xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets') + '/Channel_' + str(playlistNum) + '.xsp'
        else:
            self.log("getSmartPlaylistFilename: File not found")
            return ""


    # Open the smart playlist and read the name out of it...this is the channel name
    def getSmartPlaylistName(self, fle):
        self.log('getSmartPlaylistName')

        try:
            xml = open(fle, "r")
        except:
            self.log("getSmartPlaylistName Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return ''

        try:
            dom = parse(xml)
        except:
            self.log('getSmartPlaylistName Problem parsing playlist ' + fle, xbmc.LOGERROR)
            xml.close()
            return ''

        xml.close()

        try:
            plname = dom.getElementsByTagName('name')
            self.log('getSmartPlaylistName return ' + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except:
            self.log("Unable to get the playlist name.", xbmc.LOGERROR)
            return ''


    # handle fatal errors: log it, show the dialog, and exit
    def Error(self, message):
        self.log('FATAL ERROR: ' + message, xbmc.LOGFATAL)
        dlg = xbmcgui.Dialog()
        dlg.ok('Error', message)
        del dlg
        self.end()


    def getSmartPlaylistType(self, dom):
        self.log('getSmartPlaylistType')

        try:
            pltype = dom.getElementsByTagName('smartplaylist')
            return pltype[0].attributes['type'].value
        except:
            self.log("Unable to get the playlist type.", xbmc.LOGERROR)
            return ''


    def buildFileList(self, dir_name, media_type="video", recursive="TRUE"):
        fileList = []
        json_query = '{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "recursive": "%s", "fields":["duration","tagline","showtitle","album","artist","plot"]}, "id": 1}' % ( self.escapeDirJSON( dir_name ), media_type, recursive )
        json_folder_detail = xbmc.executeJSONRPC(json_query)
        self.log(json_folder_detail)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        numFiles = len(file_detail)
        progressIncrement = 100/numFiles
        progressPercentage = 0
        self.loadDialog.update(0, "Building Channel Filelist")
        for f in file_detail:
            fileNum = 1
            progressPercentage = progressPercentage + progressIncrement
 #           self.loadDialog.update(progressPercentage, "Adding Files")

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
                        self.loadDialog.update(progressPercentage, "Getting Video Durations...please be patient")
                        dur = self.videoParser.getVideoLength(match.group(1).replace("\\\\", "\\"))
                        
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
                    except:
                        pass
            else:
                continue
            fileNum = fileNum + 1
        return fileList


    def buildMixedTVShowFileList(self, fileLists):
        tvshowList = []        
        fileList = []
        maxFileListItems = 0
        numTotalItems = 0
        # neeed to grab one episode from each list until we reach channel limit
        self.log("fileLists Length=" + str(len(fileLists)))
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
                        #tmpFilelist = []
                        #tmpFileList = fileLists[fl].list
                        ## loop through list to get list item
                        #item = 0
                        #for item in range(len(tmpFileList)):
                        #    if item == i:
                        #        # get next item in list and add to filelist
                        #        fileList.append(tmpFileList[item])
                        #    item = item + 1
                    fl = fl + 1                
                i = i + 1
        f = 0
        for f in range(len(fileList)):
            self.log("fileList item: " + str(fileList[f]))
            f = f + 1

        self.log("fileList contains " + str(len(fileList)) + " items")
        return fileList

    def buildMixedFileList(self, fileLists):
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
            if fileLists[i].type == "movies":
                self.log("movie list found: " + str(i))
                if int(movieIndex) == 999:
                    movieIndex = i
                numMovieItems = numMovieItems + len(fileLists[i].list)
                movieList.extend(fileLists[i].list)
            elif fileLists[i].type == "episodes":
                self.log("episode list found: " + str(i))
                if int(episodeIndex) == 999:
                    episodeIndex = i
                numEpisodeItems = numEpisodeItems + len(fileLists[i].list)
                episodeList.extend(fileLists[i].list)
            elif fileLists[i].type == "tvshows":
                self.log("tvshow list found: " + str(i))
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
            
        self.log("movieIndex: " + str(movieIndex))
        self.log("episodeIndex: " + str(episodeIndex))
        self.log("tvshowIndex: " + str(tvshowIndex))

        self.log("numMovieItems: " + str(numMovieItems))
        self.log("numEpisodeItems: " + str(numEpisodeItems))
        self.log("numTVShowItems: " + str(numTVShowItems))
        
        numTotalItems = numMovieItems + numEpisodeItems + numTVShowItems
        self.log("numTotalItems: " + str(numTotalItems))
        
        if numMovieItems > 0:
            ratioMovies = int(round(numTotalItems / numMovieItems))
            self.log("ratioMovies: " + str(ratioMovies))

        if numEpisodeItems > 0:
            ratioEpisodes = int(round(numTotalItems / numEpisodeItems))
            self.log("ratioEpisodes: " + str(ratioEpisodes))

        if numTVShowItems > 0:
            ratioTVShows = int(round(numTotalItems / numTVShowItems))
            self.log("ratioTVShows: " + str(ratioTVShows))

        if int(ratioMovies) > 0 or int(ratioEpisodes) > 0 or int(ratioTVShows):
            itemMultiplier = int(round(int(self.mixLimit)/(int(ratioMovies) + int(ratioEpisodes) + int(ratioTVShows))))
        else:
            itemMultiplier = 0

        self.log("itemMultiplier: " + str(itemMultiplier))

        numMovies = itemMultiplier * ratioMovies
        numEpisodes = itemMultiplier * ratioEpisodes
        numTVShows = itemMultiplier * ratioTVShows

        self.log("numMovies: " + str(numMovies))
        self.log("numEpisodes: " + str(numEpisodes))
        self.log("numTVShows: " + str(numTVShows))

        # get a subset of items based on the number required
        movieSeq = []
        episodeSeq = []
        tvshowSeq = []

        movieSeq = movieList[0:numMovies]
        episodeSeq = episodeList[0:numEpisodes]
        tvshowSeq = tvshowList[0:numTVShows]

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

        self.log("fileList contains " + str(len(fileList)) + " items")
        return fileList


    def buildMixedFileLists(self, src):
        self.log('buildMixedFileList')
        self.log("buildMixedFileList src: " + str(src))
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
            # get order of first playlist to determine whether final Mix fileList should be randomized
            self.mixOrder = order
            
        for rule in rulesNode:
            i = 0
                        
            fileList = []
            rulename = rule.childNodes[i].nodeValue
            
            self.log("rulename: " + str(rulename))
            if os.path.exists(os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets'), rulename)):
                src1 = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets'), rulename)
                self.log("found video playlist at:" + src1)
            else:
                src1 = ""
                self.log("Problem finding source file: " + os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets'), rulename))

            dom1 = self.presetChannels.getPlaylist(src1)
            pltype1 = self.getSmartPlaylistType(dom1)

            if pltype1 == 'movies' or pltype1 == 'episodes' or pltype1 == 'tvshows':
                tmpList = []
                tmpList = self.buildFileList(src1)
                if len(tmpList) > 0:
                    if order == 'random':
                        random.shuffle(tmpList)
                    fileList.extend(tmpList)
                    self.fileLists.append(presetChannelFileList(pltype1, limit, fileList))

            elif pltype1 == 'mixed':
                if os.path.exists(src1):
                    self.buildMixedFileLists(src1)
                else:
                    self.log("Problem finding source file: " + src1)

            i = i + 1

        return self.fileLists


    def deleteCache(self):
        dir = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache/')       
        for filename in os.listdir(dir):
            fle = os.path.join(dir, filename)
            self.log('deletePresetChannels: deleting file: ' + fle)
            try:
                if os.path.isfile(fle):
                    os.unlink(fle)
            except Exception, e:
                self.log(e)


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
                self.channels[self.currentChannel - 1].setAccessTime(time.time())
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

        timedif += (time.time() - self.channels[self.currentChannel - 1].lastAccessTime)

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
        self.channels[self.currentChannel - 1].setAccessTime(time.time())

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
        self.getControl(506).setImage(IMAGES_LOC + self.channels[self.currentChannel - 1].name + '.png')
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
                self.getControl(103).setImage(IMAGES_LOC + self.channels[self.currentChannel - 1].name + '.png')
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

        lastaction = time.time() - self.lastActionTime

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

                if dlg.yesno("Exit?", "Are you sure you want to exit XBTV?"):
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
        except:
            pass

        if xbmc.Player().isPlaying():
            xbmc.Player().stop()

        if self.timeStarted > 0:
            for i in range(self.maxChannels):
                if self.channels[i].isValid:
                    ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(int(time.time() - self.timeStarted + self.channels[i].totalTimePlayed)))

        try:
            ADDON_SETTINGS.setSetting('CurrentChannel', str(self.currentChannel))
        except:
            pass

        self.background.setVisible(False)
        self.close()
