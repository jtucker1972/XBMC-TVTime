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
import time, threading
import datetime
import sys, re
import random
import shutil

import Globals

from xml.dom.minidom import parse, parseString
from Globals import *
from ChannelList import ChannelList
from os.path import normpath, abspath

NUMBER_CHANNEL_TYPES = Globals.NUMBER_CHANNEL_TYPES

sys.setdefaultencoding('utf-8')

class ChannelConfig(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.log("__init__")
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.setCoordinateResolution(1)
        self.showingList = True
        self.channel = 0
        self.channel_type = 9999
        self.setting1 = ''
        self.setting2 = ''
        self.setting3 = ''
        self.setting4 = ''
        self.setting5 = ''
        self.setting6 = ''
        self.setting7 = ''
        self.setting8 = ''
        self.setting9 = ''
        self.doModal()
        self.log("__init__ return")


    def onInit(self):
        self.log("onInit")

        self.createDirectories()

        self.getControl(105).setVisible(False) # Channel Listing Control Group
        self.getControl(106).setVisible(False) # Channel Settings Control Group

        for i in range(NUMBER_CHANNEL_TYPES):
            self.getControl(120 + i).setVisible(False) # Channel Settings

        #migrate()
        self.prepareConfig()
        self.log("onInit return")


    def onFocus(self, controlId):
        pass


    def onAction(self, act):
        action = act.getId()

        if action == ACTION_PREVIOUS_MENU:
            if self.showingList == False:
                self.cancelChan()
                self.hideChanDetails()
            else:
                self.close()


    def prepareConfig(self):
        self.log("prepareConfig")
        self.showList = []
        self.getControl(105).setVisible(False)
        self.getControl(106).setVisible(False)
        self.dlg = xbmcgui.DialogProgress()
        self.dlg.create("TV Time", "Preparing Channel Wizard")
        self.dlg.update(0, "Preparing Channel Wizard")
        self.chnlst = ChannelList()
        self.dlg.update(10, "Preparing Channel Wizard", "Loading TV Settings")
        self.chnlst.fillTVInfo()
        self.networkList = self.chnlst.networkList
        self.studioList = self.chnlst.studioList
        self.showGenreList = self.chnlst.showGenreList
        self.dlg.update(20, "Preparing Channel Wizard", "Loading Movie Settings")
        self.chnlst.fillMovieInfo()
        self.movieGenreList = self.chnlst.movieGenreList
        self.dlg.update(40, "Preparing Channel Wizard", "Loading Music Settings")
        self.chnlst.fillMusicInfo()
        self.musicGenreList = self.chnlst.musicGenreList        
        self.dlg.update(60, "Preparing Channel Wizard", "Loading Live Feed Settings")
        self.chnlst.fillFeedInfo()
        self.feedList = self.chnlst.feedList
        self.dlg.update(80, "Preparing Channel Wizard", "Loading Mixed Genre Settings")
        self.mixedGenreList = self.chnlst.makeMixedList(self.showGenreList, self.movieGenreList)

        for i in range(len(self.chnlst.showList)):
            self.showList.append(self.chnlst.showList[i][0])

        self.mixedGenreList.sort(key=lambda x: x.lower())

        self.log("self.networkList " + str(self.networkList))
        self.log("self.studioList " + str(self.studioList))
        self.log("self.showGenreList " + str(self.showGenreList))
        self.log("self.movieGenreList " + str(self.movieGenreList))
        self.log("self.musicGenreList " + str(self.musicGenreList))
        self.log("self.mixedGenreList " + str(self.mixedGenreList))

        self.resolutionList = []
        self.resolutionList.append('All')
        self.resolutionList.append('SD Only')
        self.resolutionList.append('720p or Higher')
        self.resolutionList.append('1080p Only')

        self.showseqList = []
        self.showseqList.append('1 Show')
        self.showseqList.append('2 Shows')
        self.showseqList.append('3 Shows')
        self.showseqList.append('4 Shows')
        self.showseqList.append('5 Shows')
        self.showseqList.append('6 Shows')
        self.showseqList.append('7 Shows')
        self.showseqList.append('8 Shows')
        self.showseqList.append('9 Shows')
        self.showseqList.append('10 Shows')

        self.movieseqList = []
        self.movieseqList.append('1 Movie')
        self.movieseqList.append('2 Movies')
        self.movieseqList.append('3 Movies')
        self.movieseqList.append('4 Movies')
        self.movieseqList.append('5 Movies')
        self.movieseqList.append('6 Movies')
        self.movieseqList.append('7 Movies')
        self.movieseqList.append('8 Movies')
        self.movieseqList.append('9 Movies')
        self.movieseqList.append('10 Movies')

        # check if settings2.xml file exists
        # read in channel playlists in video, music and mixed folders
        channelNum = 0
        for i in range(500):
            if os.path.exists(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'):
                channelNum = channelNum + 1
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", xbmc.translatePath('special://profile/playlists/video/') + 'Channel_' + str(i + 1) + '.xsp')
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", ChannelList().cleanString(ChannelList().getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp')))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_playlist", xbmc.translatePath('special://profile/playlists/video/') + 'Channel_' + str(i + 1) + '.xsp')
                #self.updateDialog(progressIndicator,"Auto Tune","Found " + str(self.channelList.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp')),"")
            elif os.path.exists(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'):
                channelNum = channelNum + 1
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", xbmc.translatePath('special://profile/playlists/mixed/') + 'Channel_' + str(i + 1) + '.xsp')
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", ChannelList().cleanString(ChannelList().getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp')))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_playlist", xbmc.translatePath('special://profile/playlists/mixed/') + 'Channel_' + str(i + 1) + '.xsp')
                #self.updateDialog(progressIndicator,"Auto Tune","Found " + str(self.channelList.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp')),"")
            elif os.path.exists(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp'):
                channelNum = channelNum + 1
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", xbmc.translatePath('special://profile/playlists/music/') + 'Channel_' + str(i + 1) + '.xsp')
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", ChannelList().cleanString(ChannelList().getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp')))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_playlist", xbmc.translatePath('special://profile/playlists/music/') + 'Channel_' + str(i + 1) + '.xsp')
                #self.updateDialog(progressIndicator,"Auto Tune","Found " + str(self.channelList.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp')),"")
        ADDON_SETTINGS.writeSettings()
                        
        """
        if not os.path.exists(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/settings2.xml')):
            # if not, load presets based on networklist and studiolist
            ChannelList().autoTune()
        else:
            if (REAL_SETTINGS.getSetting("autoFindNetworks") == "true" or 
                REAL_SETTINGS.getSetting("autoFindStudios") == "true" or 
                REAL_SETTINGS.getSetting("autoFindTVGenres") == "true" or 
                REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true" or 
                REAL_SETTINGS.getSetting("autoFindMixGenres") == "true" or 
                REAL_SETTINGS.getSetting("autoFindTVShows") == "true" or
                REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true"):
                self.log("autoTune")
                ChannelList().autoTune()
        """
        
        self.listcontrol = self.getControl(102)

        for i in range(200):
            theitem = xbmcgui.ListItem()
            theitem.setLabel(str(i + 1))
            self.listcontrol.addItem(theitem)


        self.dlg.update(90, "Preparing Channel Wizard", "Loading Channel List")
        self.updateListing()
        self.dlg.close()
        self.getControl(105).setVisible(True) # Channel List
        self.getControl(106).setVisible(False) # Channel Settings
        self.setFocusId(102)
        self.log("prepareConfig return")


    def saveSettings(self):
        chantype = 9999
        chan = str(self.channel)
        
        try:
            chantype = int(ADDON_SETTINGS.getSetting("Channel_" + chan + "_type"))
        except:
            self.log("Unable to get channel type")

        setting1 = "Channel_" + chan + "_1"
        setting2 = "Channel_" + chan + "_2"
        setting3 = "Channel_" + chan + "_3"
        setting4 = "Channel_" + chan + "_4"
        setting5 = "Channel_" + chan + "_5"
        setting6 = "Channel_" + chan + "_6"
        setting7 = "Channel_" + chan + "_7"
        setting8 = "Channel_" + chan + "_8"
        setting9 = "Channel_" + chan + "_9"
        settingtime = "Channel_" + chan + "_time"
        playlist = "Channel_" + chan + "_playlist"
        totalDuration = "Channel_" + chan + "_totalDuration"
        
        if chantype == 0:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(130).getLabel2())
            ADDON_SETTINGS.setSetting(setting2, '')
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(130).getLabel()))
            ADDON_SETTINGS.setSetting(setting4, '')
            ADDON_SETTINGS.setSetting(setting5, '')
            ADDON_SETTINGS.setSetting(setting6, '')
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(settingtime, 0)
        elif chantype == 1:
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(142).getLabel()))
            if self.getControl(349).isSelected():
                ADDON_SETTINGS.setSetting(setting2, str(MODE_SERIAL))
            else:
                ADDON_SETTINGS.setSetting(setting2, '')                
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(142).getLabel()))
            if self.getControl(346).isSelected():
                ADDON_SETTINGS.setSetting(setting4, str(MODE_UNWATCHED))
            else:
                ADDON_SETTINGS.setSetting(setting4, 0)
            if self.getControl(347).isSelected():
                ADDON_SETTINGS.setSetting(setting5, str(MODE_NOSPECIALS))
            else:
                ADDON_SETTINGS.setSetting(setting5, 0)
            ADDON_SETTINGS.setSetting(setting6, self.getControl(343).getLabel())
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            if self.getControl(348).isSelected():
                ADDON_SETTINGS.setSetting(setting9, str(MODE_RANDOM_FILELISTS))
            else:
                ADDON_SETTINGS.setSetting(setting9, 0)
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        elif chantype == 2:
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(152).getLabel()))
            ADDON_SETTINGS.setSetting(setting2, '')
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(152).getLabel()))
            if self.getControl(356).isSelected():
                ADDON_SETTINGS.setSetting(setting4, str(MODE_UNWATCHED))
            else:
                ADDON_SETTINGS.setSetting(setting4, 0)
            ADDON_SETTINGS.setSetting(setting5, '')
            ADDON_SETTINGS.setSetting(setting6, self.getControl(353).getLabel())
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        elif chantype == 3:
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(162).getLabel()))
            if self.getControl(369).isSelected():
                ADDON_SETTINGS.setSetting(setting2, str(MODE_SERIAL))
            else:
                ADDON_SETTINGS.setSetting(setting2, '')                
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(162).getLabel()))
            if self.getControl(366).isSelected():
                ADDON_SETTINGS.setSetting(setting4, str(MODE_UNWATCHED))
            else:
                ADDON_SETTINGS.setSetting(setting4, 0)
            if self.getControl(367).isSelected():
                ADDON_SETTINGS.setSetting(setting5, str(MODE_NOSPECIALS))
            else:
                ADDON_SETTINGS.setSetting(setting5, 0)
            ADDON_SETTINGS.setSetting(setting6, self.getControl(363).getLabel())
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        elif chantype == 4:
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(172).getLabel()))
            ADDON_SETTINGS.setSetting(setting2, '')
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(172).getLabel()))
            if self.getControl(376).isSelected():
                ADDON_SETTINGS.setSetting(setting4, str(MODE_UNWATCHED))
            else:
                ADDON_SETTINGS.setSetting(setting4, 0)
            ADDON_SETTINGS.setSetting(setting5, self.getControl(373).getLabel())
            ADDON_SETTINGS.setSetting(setting6, '')
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        elif chantype == 5:
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(182).getLabel()))
            if self.getControl(389).isSelected():
                ADDON_SETTINGS.setSetting(setting2, str(MODE_SERIAL))
            else:
                ADDON_SETTINGS.setSetting(setting2, '')                
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(182).getLabel()))
            if self.getControl(386).isSelected():
                ADDON_SETTINGS.setSetting(setting4, str(MODE_UNWATCHED))
            else:
                ADDON_SETTINGS.setSetting(setting4, 0)
            if self.getControl(387).isSelected():
                ADDON_SETTINGS.setSetting(setting5, str(MODE_NOSPECIALS))
            else:
                ADDON_SETTINGS.setSetting(setting5, 0)
            ADDON_SETTINGS.setSetting(setting6, self.getControl(383).getLabel())
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        elif chantype == 6:
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(192).getLabel()))
            if self.getControl(194).isSelected():
                ADDON_SETTINGS.setSetting(setting2, str(MODE_SERIAL))
            else:
                ADDON_SETTINGS.setSetting(setting2, '')                
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(192).getLabel()))
            if self.getControl(396).isSelected():
                ADDON_SETTINGS.setSetting(setting4, str(MODE_UNWATCHED))
            else:
                ADDON_SETTINGS.setSetting(setting4, 0)
            if self.getControl(397).isSelected():
                ADDON_SETTINGS.setSetting(setting5, str(MODE_NOSPECIALS))
            else:
                ADDON_SETTINGS.setSetting(setting5, 0)
            ADDON_SETTINGS.setSetting(setting6, self.getControl(393).getLabel())
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        if chantype == 7: # folder
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(200).getLabel2()))
            ADDON_SETTINGS.setSetting(setting2, '')
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(200).getLabel()))
            ADDON_SETTINGS.setSetting(setting4, '')
            ADDON_SETTINGS.setSetting(setting5, '')
            ADDON_SETTINGS.setSetting(setting6, '')
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        if chantype == 8: # music
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(212).getLabel()))
            ADDON_SETTINGS.setSetting(setting2, '')
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(212).getLabel()))
            ADDON_SETTINGS.setSetting(setting4, '')
            ADDON_SETTINGS.setSetting(setting5, '')
            ADDON_SETTINGS.setSetting(setting6, '')
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        if chantype == 9: # live
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, self.chnlst.cleanString(self.getControl(222).getLabel()))
            ADDON_SETTINGS.setSetting(setting2, '')
            ADDON_SETTINGS.setSetting(setting3, self.chnlst.cleanString(self.getControl(222).getLabel()))
            ADDON_SETTINGS.setSetting(setting4, '')
            ADDON_SETTINGS.setSetting(setting5, '')
            ADDON_SETTINGS.setSetting(setting6, '')
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')
        elif chantype == 9999:
            ADDON_SETTINGS.setSetting(settingtime, 0)
            ADDON_SETTINGS.setSetting(setting1, '')
            ADDON_SETTINGS.setSetting(setting2, '')
            ADDON_SETTINGS.setSetting(setting3, '')
            ADDON_SETTINGS.setSetting(setting4, '')
            ADDON_SETTINGS.setSetting(setting5, '')
            ADDON_SETTINGS.setSetting(setting6, '')
            ADDON_SETTINGS.setSetting(setting7, '')
            ADDON_SETTINGS.setSetting(setting8, '')
            ADDON_SETTINGS.setSetting(setting9, '')
            ADDON_SETTINGS.setSetting(playlist, '')
            ADDON_SETTINGS.setSetting(totalDuration, '')

        # Check to see if the user changed anything
        set1 = ''
        set2 = ''
        set3 = ''
        set4 = ''
        set5 = ''
        set6 = ''
        set7 = ''
        set8 = ''
        set9 = ''

        try:
            set1 = ADDON_SETTINGS.getSetting(setting1)
            set2 = ADDON_SETTINGS.getSetting(setting2)
            set3 = ADDON_SETTINGS.getSetting(setting3)
            set4 = ADDON_SETTINGS.getSetting(setting4)
            set5 = ADDON_SETTINGS.getSetting(setting5)
            set6 = ADDON_SETTINGS.getSetting(setting6)
            set7 = ADDON_SETTINGS.getSetting(setting7)
            set8 = ADDON_SETTINGS.getSetting(setting8)
            set9 = ADDON_SETTINGS.getSetting(setting9)
        except:
            pass

        if chantype != self.channel_type or set1 != self.setting1 or set2 != self.setting2 or set3 != self.setting3 or set4 != self.setting4 or set5 != self.setting5 or set6 != self.setting6 or set7 != self.setting7 or set8 != self.setting8 or set9 != self.setting9:
            ADDON_SETTINGS.setSetting('Channel_' + chan + '_changed', 'true')

        ADDON_SETTINGS.writeSettings()
        # save total number of channels to settings.xml so we don't have to keep looping
        # through settings2.xml
        self.chnlst.setMaxChannels()
        
        self.log("saveSettings return")


    def cancelChan(self):
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_type", str(self.channel_type))
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_1", self.setting1)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_2", self.setting2)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_3", self.setting3)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_4", self.setting4)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_5", self.setting5)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_6", self.setting6)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_7", self.setting7)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_8", self.setting8)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_9", self.setting9)


    def hideChanDetails(self):
        self.getControl(106).setVisible(False)

        for i in range(NUMBER_CHANNEL_TYPES):
            self.getControl(120 + i).setVisible(False)

        self.setFocusId(102)
        self.getControl(105).setVisible(True)
        self.showingList = True
        self.updateListing(self.channel)
        self.listcontrol.selectItem(self.channel - 1)


    def onClick(self, controlId):
        self.log("onClick " + str(controlId))

        if controlId == 102:
            self.getControl(105).setVisible(False)
            self.getControl(106).setVisible(True)
            self.channel = self.listcontrol.getSelectedPosition() + 1
            self.changeChanType(self.channel, 0)
            
            self.setFocusId(110)
            self.showingList = False
        elif controlId == 110:
            self.changeChanType(self.channel, -1)
        elif controlId == 111:
            self.changeChanType(self.channel, 1)
        elif controlId == 112:
            self.saveSettings()
            self.hideChanDetails()
        elif controlId == 113:
            self.cancelChan()
            self.hideChanDetails()
        elif controlId == 130:
            dlg = xbmcgui.Dialog()
            retval = dlg.browse(1, "Channel " + str(self.channel) + " Playlist", "files", ".xsp", False, False, "special://videoplaylists/")

            if retval != "special://videoplaylists/":
                self.getControl(130).setLabel(self.chnlst.getSmartPlaylistName(retval), label2=retval)
        elif controlId == 140:
            self.changeListData(self.networkList, 142, -1)
        elif controlId == 141:
            self.changeListData(self.networkList, 142, 1)
        elif controlId == 150:
            self.changeListData(self.studioList, 152, -1)
        elif controlId == 151:
            self.changeListData(self.studioList, 152, 1)
        elif controlId == 160:
            self.changeListData(self.showGenreList, 162, -1)
        elif controlId == 161:
            self.changeListData(self.showGenreList, 162, 1)
        elif controlId == 170:
            self.changeListData(self.movieGenreList, 172, -1)
        elif controlId == 171:
            self.changeListData(self.movieGenreList, 172, 1)
        elif controlId == 180:
            self.changeListData(self.mixedGenreList, 182, -1)
        elif controlId == 181:
            self.changeListData(self.mixedGenreList, 182, 1)
        elif controlId == 190:
            self.changeListData(self.showList, 192, -1)
        elif controlId == 191:
            self.changeListData(self.showList, 192, 1)        
        elif controlId == 200: # Folder Channel
            dlg = xbmcgui.Dialog()
            # need to replace this with folder instead of file
            retval = dlg.browse(0, "Channel " + str(self.channel) + " Folder", "files", "*.*", False, False, "")
            if retval != "":
                # smb isn't supported at this time but it is here
                # as a placeholder if a solution can be found
                # for connecting to smb shares from python
                if retval.find("smb://") == -1:
                    ps = retval.split(os.sep)
                else:
                    ps = retval.split('/')
                chanName = ""
                for i in range(len(ps)-1):
                    chanName = ps[i]
                self.getControl(200).setLabel(chanName, label2=retval)        
        elif controlId == 210: # Music Based Channel
            self.changeListData(self.musicGenreList, 212, -1)
        elif controlId == 211:
            self.changeListData(self.musicGenreList, 212, 1)
        elif controlId == 220: # Live Channel
            self.changeListData(self.feedList, 222, -1)
        elif controlId == 221:
            self.changeListData(self.feedList, 222, 1)
        elif controlId == 344:
            self.changeListData(self.resolutionList, 343, -1)
        elif controlId == 345:
            self.changeListData(self.resolutionList, 343, 1)
        elif controlId == 354:
            self.changeListData(self.resolutionList, 353, -1)
        elif controlId == 355:
            self.changeListData(self.resolutionList, 353, 1)
        elif controlId == 364:
            self.changeListData(self.resolutionList, 363, -1)
        elif controlId == 365:
            self.changeListData(self.resolutionList, 363, 1)
        elif controlId == 374:
            self.changeListData(self.resolutionList, 373, -1)
        elif controlId == 375:
            self.changeListData(self.resolutionList, 373, 1)
        elif controlId == 384:
            self.changeListData(self.resolutionList, 383, -1)
        elif controlId == 385:
            self.changeListData(self.resolutionList, 383, 1)
        elif controlId == 394:
            self.changeListData(self.resolutionList, 393, -1)
        elif controlId == 395:
            self.changeListData(self.resolutionList, 393, 1)
        elif controlId == 489:
            self.changeListData(self.showseqList, 488, -1)
        elif controlId == 490:
            self.changeListData(self.showseqList, 488, 1)
        elif controlId == 492:
            self.changeListData(self.movieseqList, 491, -1)
        elif controlId == 493:
            self.changeListData(self.movieseqList, 491, 1)
            
        self.log("onClick return")



    def changeListData(self, thelist, controlid, val):
        self.log("changeListData " + str(controlid) + ", " + str(val))
        curval = self.getControl(controlid).getLabel()
        found = False
        index = 0

        if len(thelist) == 0:
            self.getControl(controlid).setLabel('')
            self.log("changeListData return Empty list")
            return

        for item in thelist:
            if item == curval:
                found = True
                break

            index += 1

        if found == True:
            index += val

        while index < 0:
            index += len(thelist)

        while index >= len(thelist):
            index -= len(thelist)

        self.getControl(controlid).setLabel(self.chnlst.uncleanString(thelist[index]))
        self.log("changeListData return")


    def changeChanType(self, channel, val):
        self.log("changeChanType " + str(channel) + ", " + str(val))
        chantype = 9999

        try:
            chantype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
        except:
            self.log("Unable to get channel type")

        if val != 0:
            chantype += val

            if chantype < 0:
                chantype = 9999
            elif chantype == 10000:
                chantype = 0
            elif chantype == 9998:
                chantype = NUMBER_CHANNEL_TYPES - 1
            elif chantype == NUMBER_CHANNEL_TYPES:
                chantype = 9999

            ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", str(chantype))
        else:
            self.channel_type = chantype
            self.setting1 = ''
            self.setting2 = ''
            self.setting3 = ''
            self.setting4 = ''
            self.setting5 = ''
            self.setting6 = ''
            self.setting7 = ''
            self.setting8 = ''
            self.setting9 = ''

            try:
                self.setting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
                self.setting2 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_2")
                self.setting3 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
                self.setting4 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_4")
                self.setting5 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_5")
                self.setting6 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_6")
                self.setting7 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_7")
                self.setting8 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_8")
                self.setting9 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_9")
            except:
                pass

        for i in range(NUMBER_CHANNEL_TYPES):
            if i == chantype:
                self.getControl(120 + i).setVisible(True) # show settings
                self.getControl(110).controlDown(self.getControl(120 + ((i + 1) * 10)))

                try:
                    self.getControl(111).controlDown(self.getControl(120 + ((i + 1) * 10 + 1)))
                except:
                    self.getControl(111).controlDown(self.getControl(120 + ((i + 1) * 10)))
            else:
                self.getControl(120 + i).setVisible(False) # hide settings

        self.fillInDetails(channel)
        self.log("changeChanType return")


    def fillInDetails(self, channel):
        self.getControl(104).setLabel("Channel " + str(channel))
        chantype = 9999
        chansetting1 = ''
        chansetting2 = ''
        chansetting3 = ''
        chansetting4 = ''
        chansetting5 = ''
        chansetting6 = ''
        chansetting7 = ''
        chansetting8 = ''

        try:
            chantype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
            chansetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
            chansetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_2")
            chansetting3 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
            chansetting4 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_4")
            chansetting5 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_5")
            chansetting6 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_6")
            chansetting7 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_7")
            chansetting8 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_8")
            chansetting9 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_9")
        except:
            self.log("Unable to get some setting")

        self.getControl(109).setLabel(self.getChanTypeLabel(chantype))

        if chantype == 0:
            plname = self.chnlst.getSmartPlaylistName(chansetting1)

            if len(plname) == 0:
                chansetting1 = ''

            self.getControl(130).setLabel(self.chnlst.getSmartPlaylistName(chansetting1), label2=chansetting1)
        elif chantype == 1:
            self.getControl(142).setLabel(self.findItemInList(self.networkList, chansetting1))
            self.getControl(343).setLabel(self.findItemInList(self.resolutionList, chansetting6))
            if chansetting2 <> "":
                self.getControl(349).setSelected(int(chansetting2) == int(MODE_SERIAL))
            if chansetting4 <> "":
                self.getControl(346).setSelected(int(chansetting4) == int(MODE_UNWATCHED))
            if chansetting5 <> "":
                self.getControl(347).setSelected(int(chansetting5) == int(MODE_NOSPECIALS))
            if chansetting9 <> "":
                self.getControl(348).setSelected(int(chansetting9) == int(MODE_RANDOM_FILELISTS))
        elif chantype == 2:
            self.getControl(152).setLabel(self.findItemInList(self.studioList, chansetting1))
            self.getControl(353).setLabel(self.findItemInList(self.resolutionList, chansetting6))
            if chansetting4 <> "":
                self.getControl(356).setSelected(int(chansetting4) == int(MODE_UNWATCHED))
        elif chantype == 3:
            self.getControl(162).setLabel(self.findItemInList(self.showGenreList, chansetting1))
            self.getControl(363).setLabel(self.findItemInList(self.resolutionList, chansetting6))
            if chansetting2 <> "":
                self.getControl(369).setSelected(int(chansetting2) == int(MODE_SERIAL))
            if chansetting4 <> "":
                self.getControl(366).setSelected(int(chansetting4) == int(MODE_UNWATCHED))
            if chansetting5 <> "":
                self.getControl(367).setSelected(int(chansetting5) == int(MODE_NOSPECIALS))
        elif chantype == 4:
            self.getControl(172).setLabel(self.findItemInList(self.movieGenreList, chansetting1))
            self.getControl(373).setLabel(self.findItemInList(self.resolutionList, chansetting6))
            if chansetting4 <> "":
                self.getControl(376).setSelected(int(chansetting4) == int(MODE_UNWATCHED))
        elif chantype == 5:
            self.getControl(182).setLabel(self.findItemInList(self.mixedGenreList, chansetting1))
            self.getControl(383).setLabel(self.findItemInList(self.resolutionList, chansetting6))
            if chansetting2 <> "":
                self.getControl(389).setSelected(int(chansetting2) == int(MODE_SERIAL))
            if chansetting4 <> "":
                self.getControl(386).setSelected(int(chansetting4) == int(MODE_UNWATCHED))
            if chansetting5 <> "":
                self.getControl(387).setSelected(int(chansetting5) == int(MODE_NOSPECIALS))
            self.getControl(488).setLabel(self.findItemInList(self.showseqList, chansetting7))
            self.getControl(491).setLabel(self.findItemInList(self.movieseqList, chansetting8))
        elif chantype == 6:
            self.getControl(192).setLabel(self.findItemInList(self.showList, chansetting1))
            self.getControl(393).setLabel(self.findItemInList(self.resolutionList, chansetting6))
            if chansetting4 <> "":
                self.getControl(396).setSelected(int(chansetting4) == int(MODE_UNWATCHED))
            if chansetting5 <> "":
                self.getControl(397).setSelected(int(chansetting5) == int(MODE_NOSPECIALS))
            self.getControl(194).setSelected(chansetting2 == str(MODE_SERIAL))
        elif chantype == 7: # folder
            fldname = chansetting3
            if len(fldname) == 0:
                chansetting1 = ''
            self.getControl(200).setLabel(fldname, label2=self.chnlst.uncleanString(chansetting1))
        elif chantype == 8: # music
            self.getControl(212).setLabel(self.findItemInList(self.musicGenreList, chansetting1))
        #elif chantype == 9: # live
        #    self.getControl(222).setLabel(self.findItemInList(self.feedList, chansetting1))

        self.log("fillInDetails return")


    def findItemInList(self, thelist, item):
        loitem = item.lower()

        for i in thelist:
            if loitem == i.lower():
                return item
                
        if len(thelist) > 0:
            return thelist[0]
            
        return ''


    def getChanTypeLabel(self, chantype):
        if chantype == 0:
            return "Custom Playlist"
        elif chantype == 1:
            return "TV Network"
        elif chantype == 2:
            return "Movie Studio"
        elif chantype == 3:
            return "TV Genre"
        elif chantype == 4:
            return "Movie Genre"
        elif chantype == 5:
            return "Mixed Genre"
        elif chantype == 6:
            return "TV Show"
        elif chantype == 7:
            return "Folder"
        elif chantype == 8:
            return "Music Genre"
        elif chantype == 9:
            return "Live"
        elif chantype == 9999:
            return "None"

        return ''


    def updateListing(self, channel = -1):
        self.log("updateListing")
        start = 0
        end = 200

        if channel > -1:
            start = channel - 1
            end = channel

        for i in range(start, end):
            theitem = self.listcontrol.getListItem(i)
            chantype = 9999
            chansetting1 = ''
            chansetting2 = ''
            chansetting3 = ''
            newlabel = ''

            try:
                chantype = int(ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_type"))
                chansetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_1")
                chansetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_2")
                chansetting3 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_3")
            except:
                pass

            if chantype == 0:
                newlabel = self.chnlst.getSmartPlaylistName(chansetting1)
            elif chantype == 1 or chantype == 2 or chantype == 5 or chantype == 6:
                newlabel = chansetting3
            elif chantype == 3:
                newlabel = chansetting3
            elif chantype == 4:
                newlabel = chansetting3
            elif chantype == 7:
                newlabel = self.chnlst.uncleanString(chansetting3)
            elif chantype == 8:
                newlabel = chansetting3
            elif chantype == 9:
                newlabel = self.chnlst.uncleanString(chansetting3)

            theitem.setLabel2(newlabel)

        self.log("updateListing return")


#####################################################
#####################################################
#
# Utility Functions
#
#####################################################
#####################################################

    def log(self, msg, level = xbmc.LOGDEBUG):
        xbmc.log('TV Time-' + msg, level)


    def createDirectories(self):
        self.log("createDirectories")
        # setup directories
        self.createDirectory(CHANNELS_LOC)
        self.createDirectory(GEN_CHAN_LOC)
        self.createDirectory(PRESTAGE_LOC)
        self.createDirectory(TEMP_LOC)
        self.createDirectory(META_LOC)
        self.createDirectory(FEED_LOC)
        

    def createDirectory(self, directory):
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except:
                self.Error('Unable to create the directory - ' + str(directory))
                return


__cwd__ = REAL_SETTINGS.getAddonInfo('path')


mydialog = ChannelConfig("script.pseudotv.ChannelConfig.xml", __cwd__, "default")
del mydialog
