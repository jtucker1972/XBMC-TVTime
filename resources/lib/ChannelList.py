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
import glob

from operator import itemgetter
from time import time, localtime, strftime, strptime, mktime, sleep
from datetime import datetime, date, timedelta
from decimal import *

import Globals

from xml.dom.minidom import parse, parseString

from Playlist import Playlist
from Globals import *
from Channel import Channel
from VideoParser import VideoParser

NUMBER_CHANNEL_TYPES = Globals.NUMBER_CHANNEL_TYPES

class ChannelList:
    def __init__(self):
        self.networkList = []
        self.studioList = []
        self.mixedGenreList = []
        self.showGenreList = []
        self.movieGenreList = []
        self.showList = []
        self.musicGenreList = []
        self.getFileTries = 0

    def setupList(self):
        self.channels = []

        self.dlg = xbmcgui.DialogProgress()
        self.dlg.create("TV Time", "Loading Channels")
        self.progress = 0
        self.line1 = "Loading Channels"
        self.line2 = ""
        self.line3 = ""
        self.updateDialog(self.progress, self.line1, self.line2, self.line3)

        maxChannels = int(REAL_SETTINGS.getSetting("maxChannels"))

        # Go through all channels, create their arrays, and setup the new playlist
        for i in range(maxChannels):
            self.progress = int(i * (100/maxChannels))
            self.line2 = "Loading Channel " + str(i + 1)
            self.line3 = ""
            self.updateDialog(self.progress, self.line1, self.line2, self.line3)
            self.channels.append(Channel())

            # If the user pressed cancel, stop everything and exit
            if self.dlg.iscanceled():
                self.log('Loading Channels Cancelled')
                self.dlg.close()
                return None

            self.setupChannel(i + 1)

        #REAL_SETTINGS.setSetting('ForceChannelReset', 'false')
        self.updateDialog(100, "Loading Complete","","")
        self.dlg.close()

        return self.channels


    def setupChannel(self, channel):
        returnval = False
        createlist = True
        chtype = 9999
        chsetting1 = '' # criteria
        chsetting2 = '' # serial mode
        chsetting3 = '' # channel name
        chsetting4 = '' # unwatched
        chsetting5 = '' # no specials
        chsetting6 = '' # resolution
        chsetting7 = '' # setting for num episodes in mixed genre
        chsetting8 = '' # setting for num movies in mixed genre
        chsetting9 = '' # setting for mixed tv show randomizing

        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
            chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_1')
            chsetting2 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_2')
            chsetting3 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_3')
            chsetting4 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_4')
            chsetting5 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_5')
            chsetting6 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_6')
            chsetting7 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_7')
            chsetting8 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_8')
            chsetting9 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_9')
        except:
            pass

        """
        Channel Types
          0 = Custom Playlist
          1 = Network
          2 = Studio
          3 = TV Show Genre
          4 = Movie Genre
          5 = Mix Genre
          6 = TV Show
          7 = Folder
          8 = Music
        """
        if chtype == 9999:
            self.channels[channel - 1].isValid = False
            return False

        # If possible, use an existing playlist
        if os.path.exists(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u'):
            try:
                self.channels[channel - 1].totalTimePlayed = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_time'))

                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == True:
                    self.channels[channel - 1].isValid = True
                    self.channels[channel - 1].fileName = CHANNELS_LOC + 'channel_' + str(channel) + '.m3u'
                    returnval = True

            except:
                pass
        
        if chtype == 6 or chtype == 1: # TV Show or Network Channel
            if chsetting2 == str(MODE_SERIAL):
                self.channels[channel - 1].mode = MODE_SERIAL

        if self.channels[channel - 1].mode & MODE_ALWAYSPAUSE > 0:
            self.channels[channel - 1].isPaused = True

        if self.channels[channel - 1].mode & MODE_RESUME > 0:
            self.channels[channel - 1].totalTimePlayed = 0
            chantime = 0

            try:
                chantime = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_time'))
            except:
                pass

            self.channels[channel - 1].showTimeOffset = chantime

            while self.channels[channel - 1].showTimeOffset > self.channels[channel - 1].getCurrentDuration():
                self.channels[channel - 1].showTimeOffset -= self.channels[channel - 1].getCurrentDuration()
                self.channels[channel - 1].addShowPosition(1)

        self.channels[channel - 1].name = chsetting3
        return returnval



    # Based on a smart playlist, create a normal playlist that can actually be used by us
    def makeChannelList(self, channel, chtype, setting1, setting2):
        self.log('makeChannelList ' + str(channel))

        if chtype == 0:
            fle = setting1
        else:
            fle = self.makeTypePlaylist(chtype, setting1, setting2)

        fle = xbmc.translatePath(fle)

        if len(fle) == 0:
            self.log('Unable to locate the playlist for channel ' + str(channel), xbmc.LOGERROR)
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
            fileList = self.buildMixedFileList(dom)
        else:
            fileList = self.buildFileList(fle)

        try:
            channelplaylist = open(CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "w")
        except:
            self.Error('Unable to open the cache file ' + CHANNELS_LOC + 'channel_' + str(channel) + '.m3u', xbmc.LOGERROR)
            return False

        channelplaylist.write("#EXTM3U\n")

        if len(fileList) == 0:
            self.log("Unable to get information about channel " + str(channel), xbmc.LOGERROR)
            channelplaylist.close()
            return False

        try:
            order = dom.getElementsByTagName('order')

            if order[0].childNodes[0].nodeValue.lower() == 'random':
                random.shuffle(fileList)
        except:
            pass

        fileList = fileList[:250]

        # Write each entry into the new playlist
        for string in fileList:
            channelplaylist.write("#EXTINF:" + string + "\n")

        channelplaylist.close()
        self.log('makeChannelList return')
        return True


    def fillMusicInfo(self):
        #print xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "JSONRPC.Introspect", "id": 1}')
        self.log("fillMusicInfo")
        self.musicGenreList = [] 
        json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": {"fields":["genre"]}, "id": 1}'
        json_folder_detail = xbmc.executeJSONRPC(json_query)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        for f in detail:
            match = re.search('"genre" *: *"(.*?)",', f)

            if match:
                genres = match.group(1).split('/')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip()

                    for g in self.musicGenreList:
                        if curgenre == g.lower():
                            found = True
                            break

                    if found == False:
                        self.musicGenreList.append(genre.strip())

        self.musicGenreList.sort(key=lambda x: x.lower())


    def fillTVInfo(self):
        self.log("fillTVInfo")
        self.networkList = []
        self.showGenreList = []
        self.showList = []
        json_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"fields":["studio", "genre"]}, "id": 1}'
        json_folder_detail = xbmc.executeJSONRPC(json_query)
#        self.log(json_folder_detail)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in detail:
            match = re.search('"studio" *: *"(.*?)",', f)
            network = ''

            if match:
                found = False
                network = match.group(1).strip()

                for item in self.networkList:
                    if item.lower() == network.lower():
                        found = True
                        break

                if found == False and len(network) > 0:
                    self.networkList.append(network)

            match = re.search('"label" *: *"(.*?)",', f)

            if match:
                show = match.group(1).strip()
                self.showList.append([show, network])

            match = re.search('"genre" *: *"(.*?)",', f)

            if match:
                genres = match.group(1).split('/')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip()

                    for g in self.showGenreList:
                        if curgenre == g.lower():
                            found = True
                            break

                    if found == False:
                        self.showGenreList.append(genre.strip())

        self.networkList.sort(key=lambda x: x.lower())
        self.showGenreList.sort(key=lambda x: x.lower())


    def fillMovieInfo(self):
        self.log("fillMovieInfo")
        studioList = []
        json_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"fields":["studio", "genre"]}, "id": 1}'
        json_folder_detail = xbmc.executeJSONRPC(json_query)
#        self.log(json_folder_detail)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in detail:
            match = re.search('"genre" *: *"(.*?)",', f)

            if match:
                genres = match.group(1).split('/')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip()

                    for g in self.movieGenreList:
                        if curgenre == g.lower():
                            found = True
                            break

                    if found == False:
                        self.movieGenreList.append(genre.strip())

            match = re.search('"studio" *: *"(.*?)",', f)

            if match:
                studios = match.group(1).split('/')

                for studio in studios:
                    curstudio = studio.strip()
                    found = False

                    for i in range(len(studioList)):
                        if studioList[i][0].lower() == curstudio.lower():
                            studioList[i][1] += 1
                            found = True

                    if found == False and len(curstudio) > 0:
                        studioList.append([curstudio, 1])

        maxcount = 0

        for i in range(len(studioList)):
            if studioList[i][1] > maxcount:
                maxcount = studioList[i][1]

        bestmatch = 1
        lastmatch = 1000

        for i in range(maxcount, 0, -1):
            itemcount = 0

            for j in range(len(studioList)):
                if studioList[j][1] == i:
                    itemcount += 1

            if abs(itemcount - 15) < abs(lastmatch - 15):
                bestmatch = i
                lastmatch = itemcount

        for i in range(len(studioList)):
            if studioList[i][1] == bestmatch:
                self.studioList.append(studioList[i][0])

        self.studioList.sort(key=lambda x: x.lower())
        self.movieGenreList.sort(key=lambda x: x.lower())
        

    def fillMixedGenreInfo(self):
        if len(self.mixedGenreList) == 0:
            if len(self.showGenreList) == 0:
                self.fillTVInfo()
            if len(self.movieGenreList) == 0:
                self.fillMovieInfo()

            self.mixedGenreList = self.makeMixedList(self.showGenreList, self.movieGenreList)
            self.mixedGenreList.sort(key=lambda x: x.lower())


    def makeMixedList(self, list1, list2):
        self.log("makeMixedList")
        newlist = []

        for item in list1:
            curitem = item.lower()

            for a in list2:
                if curitem == a.lower():
                    newlist.append(item)
                    break

        return newlist


    def escapeDirJSON(self, dir_name):
        if (dir_name.find(":")):
            dir_name = dir_name.replace("\\", "\\\\")

        return dir_name


#####################################################
#####################################################
#
# Settings Functions
#
#####################################################
#####################################################

    def autoTune(self):
        self.log('autoTune')
        
        channelNum = 0

        self.dlg = xbmcgui.DialogProgress()
        self.dlg.create("TV Time", "Auto Tune")

        progressIndicator = 0
        # need to get number of Channel_X files in the video and mix folders
        for i in range(500):
            if os.path.exists(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'):
                channelNum = channelNum + 1
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "special://profile/playlists/video/Channel_" + str(i + 1) + ".xsp")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", self.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                self.updateDialog(progressIndicator,"Auto Tune","Found " + str(self.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp')),"")
            elif os.path.exists(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'):
                channelNum = channelNum + 1
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "special://profile/playlists/mixed/Channel_" + str(i + 1) + ".xsp")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", self.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                self.updateDialog(progressIndicator,"Auto Tune","Found " + str(self.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp')),"")
            #i = i + 1
        
        progressIndicator = 10
        if (REAL_SETTINGS.getSetting("autoFindNetworks") == "true" or REAL_SETTINGS.getSetting("autoFindTVGenres") == "true"):
            self.updateDialog(progressIndicator,"Auto Tune","Searching for TV Channels","")
            if len(self.networkList) == 0:
                self.fillTVInfo()

        # need to add check for auto find network channels
        progressIndicator = 20
        if REAL_SETTINGS.getSetting("autoFindNetworks") == "true":
            self.updateDialog(progressIndicator,"Auto Tune","Adding TV Networks","")
            for i in range(len(self.networkList)):
                channelNum = channelNum + 1
                # add network presets
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(self.networkList[i]))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(self.networkList[i]))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str("All"))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog(progressIndicator,"Auto Tune","Adding TV Network",str(self.networkList[i]))

        progressIndicator = 30
        if REAL_SETTINGS.getSetting("autoFindTVGenres") == "true":
            self.updateDialog(progressIndicator,"Auto Tune","Adding TV Genres","")
            for i in range(len(self.showGenreList)):
                channelNum = channelNum + 1
                # add network presets
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "3")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(self.showGenreList[i]))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(self.showGenreList[i]) + ' TV')
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str("All"))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog(progressIndicator,"Auto Tune","Adding TV Genres",str(self.showGenreList[i]) + " TV")
        
        progressIndicator = 40
        if (REAL_SETTINGS.getSetting("autoFindStudios") == "true" or REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true"):
            self.updateDialog(progressIndicator,"Auto Tune","Searching for Movie Channels","")
            self.fillMovieInfo()

        progressIndicator = 50
        if REAL_SETTINGS.getSetting("autoFindStudios") == "true":
            self.updateDialog(progressIndicator,"Auto Tune","Adding Movie Studios","")
            for i in range(len(self.studioList)):
                channelNum = channelNum + 1
                progressIndicator = progressIndicator + (10/len(self.studioList))
                # add network presets
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "2")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(self.studioList[i]))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(self.studioList[i]))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str("All"))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog(progressIndicator,"Auto Tune","Adding Movie Studios",str(self.studioList[i]))

        progressIndicator = 60
        if REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true":
            self.updateDialog(progressIndicator,"Auto Tune","Adding Movie Genres","")
            for i in range(len(self.movieGenreList)):
                channelNum = channelNum + 1
                progressIndicator = progressIndicator + (10/len(self.movieGenreList))
                # add network presets
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "4")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(self.movieGenreList[i]))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(self.movieGenreList[i]) + ' Movies')
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str("All"))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog(progressIndicator,"Auto Tune","Adding Movie Genres","Found " + str(self.movieGenreList[i]) + " Movies")

        progressIndicator = 65
        if REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.updateDialog(progressIndicator,"Auto Tune","Searching for Mixed Channels","")
            self.fillMixedGenreInfo()
        
        progressIndicator = 70
        if REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.updateDialog(progressIndicator,"Auto Tune","Adding Mixed Genres","")
            for i in range(len(self.mixedGenreList)):
                channelNum = channelNum + 1
                # add network presets
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "5")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(self.mixedGenreList[i]))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(self.mixedGenreList[i]) + ' Mix')
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str("All"))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str("8 Shows"))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str("2 Movies"))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog(progressIndicator,"Auto Tune","Adding Mixed Genres",str(self.mixedGenreList[i]) + " Mix")

        progressIndicator = 80
        if REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.updateDialog(progressIndicator,"Auto Tune","Searching for Music Channels","")
            if len(self.musicGenreList) == 0:
                self.fillMusicInfo()

        progressIndicator = 90
        if REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.updateDialog(progressIndicator,"Auto Tune","Adding Music Genres","")
            for i in range(len(self.musicGenreList)):
                channelNum = channelNum + 1
                # add network presets
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(self.musicGenreList[i]))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(self.musicGenreList[i]) + ' Music')
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_5", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_6", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_7", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_8", str(""))
                ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_9", str(""))
                ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog(progressIndicator,"Auto Tune","Adding Music Genres",str(self.musicGenreList[i]) + " Music")

        ADDON_SETTINGS.writeSettings()

        # set max channels
        self.setMaxChannels()

        # reset auto tune settings
        REAL_SETTINGS.setSetting("autoFindNetworks","false")
        REAL_SETTINGS.setSetting("autoFindStudios","false")
        REAL_SETTINGS.setSetting("autoFindTVGenres","false")
        REAL_SETTINGS.setSetting("autoFindMovieGenres","false")
        REAL_SETTINGS.setSetting("autoFindMixGenres","false")
        REAL_SETTINGS.setSetting("autoFindTVShows","false")
        REAL_SETTINGS.setSetting("autoFindMusicGenres","false")
        
        # force a reset
        REAL_SETTINGS.setSetting("ForceChannelReset","1")

        self.dlg.close()


    def setMaxChannels(self):
        self.log('setMaxChannels')
        maxChannels = 0

        for i in range(999):
            chtype = 9999
            chsetting1 = ''

            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
                chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_1')
            except:
                pass

            if chtype == 0:
                if os.path.exists(xbmc.translatePath(chsetting1)):
                    maxChannels = i + 1
            elif chtype < 7:
                if len(chsetting1) > 0:
                    maxChannels = i + 1
            elif chtype == 7: # Folder Based
                if os.path.exists(chsetting1):
                    maxChannels = i + 1
                else:
                    self.log("Cannot find Folder")                    
            elif chtype == 8: # Music
                if len(chsetting1) > 0:
                    maxChannels = i + 1
          
        REAL_SETTINGS.setSetting("maxChannels", str(maxChannels))

        self.log('setMaxChannels return ' + str(maxChannels))

#####################################################
#####################################################
#
# SmartPlaylist Functions
#
#####################################################
#####################################################

    def resetPlaylist(self, channel):
        # need to get the channel settings
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
            chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_1') # criteria
            chsetting2 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_2') # Serial Mode
            chsetting3 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_3') # channel name
            chsetting4 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_4') # unwatched
            chsetting5 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_5') # no specials
            chsetting6 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_6') # resolution
            chsetting7 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_7') # num shows
            chsetting8 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_8') # num movies
            chsetting9 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_9') # randomize tv shows
            # save playlist filename as a setting so we can reference it later
            playlist = self.makeTypePlaylist(chtype, chsetting1, chsetting2, chsetting3, chsetting4, chsetting5, chsetting6, chsetting7, chsetting8, chsetting9)
            if chtype == 0:
                # set playlist to selected playlist 
                ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_playlist', chsetting1)
            elif chtype < 7:
                # set playlist to generated playlist
                ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_playlist', playlist)
            elif chtype == 8: # music
                # set playlist to generated playlist
                ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_playlist', playlist)              
        except:
            pass

            
    def makeTypePlaylist(self, chtype, setting1, setting2, setting3, setting4, setting5, setting6, setting7, setting8, setting9):
        if int(chtype) == 1:
            return self.createNetworkPlaylist(setting1, setting2, setting3, setting4, setting5, setting6, setting9)
        elif int(chtype) == 2:
            return self.createStudioPlaylist(setting1, setting2, setting3, setting4, setting5, setting6)
        elif int(chtype) == 3:
            return self.createGenrePlaylist('episodes', chtype, setting1, setting2, setting3, setting4, setting5, setting6)
        elif int(chtype) == 4:
            return self.createGenrePlaylist('movies', chtype, setting1, setting2, setting3, setting4, setting5, setting6)
        elif int(chtype) == 5:
            return self.createGenreMixedPlaylist(setting1, setting2, setting3, setting4, setting5, setting6)
        elif int(chtype) == 6:
            return self.createShowPlaylist(setting1, setting2, setting3, setting4, setting5, setting6)
        elif int(chtype) == 8:
            return self.createMusicPlaylist(setting1, setting3)

        self.log('makeTypePlaylists invalid channel type: ' + str(chtype))
        return ''


    def createNetworkPlaylist(self, network, serial, channelname, unwatched, nospecials, resolution, randomtvshow):
        if len(self.networkList) == 0:
            self.fillTVInfo()        
        limit = REAL_SETTINGS.getSetting("limit")
        if limit == "0":
            limit = 50
        elif limit == "1":
            limit = 100
        elif limit == "2":
            limit = 250
        if serial == "":
            serial = 0
        if randomtvshow == "":
            randomtvshow = 0
        network_playlists = []
        network_tvshow_playlists = []

        # get number of shows matching
        numShows = 0
        for i in range(len(self.showList)):
            if self.showList[i][1].lower() == network.lower():
                numShows = numShows + 1        

        # create a seperate playlist for each tvshow
        for i in range(len(self.showList)):
            if self.showList[i][1].lower() == network.lower():
                network = network.lower()
                theshow = self.cleanString(self.showList[i][0].lower())
                flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'network_' + network + '_' + theshow + '.xsp')

                # create playlist for network tvshow
                try:
                    fle = open(flename, "w")
                except:
                    self.Error('createNetworkPlaylist: Unable to open the cache file ' + flename, xbmc.LOGERROR)
                    return ''

                network = network.lower()
                self.writeXSPHeader(fle, "episodes", 'network_' + network + '_' + theshow, 'all')
                fle.write('    <rule field="tvshow" operator="is">' + theshow + '</rule>\n')
                
                if unwatched == "1":
                    fle.write('    <rule field="playcount" operator="is">0</rule>\n')
                
                if nospecials == "1":
                    fle.write('    <rule field="season" operator="isnot">0</rule>\n')

                if len(resolution) > 0:
                    if resolution == 'SD Only':
                        fle.write('    <rule field="videoresolution" operator="lessthan">720</rule>\n')
                    if resolution == '720p or Higher':
                        fle.write('    <rule field="videoresolution" operator="greaterthan">719</rule>\n')
                    if resolution == '1080p Only':
                        fle.write('    <rule field="videoresolution" operator="greaterthan">1079</rule>\n')

                if int(serial) == MODE_SERIAL:
                    self.writeXSPFooter(fle, int(limit/numShows), "airdate")                        
                else:
                    self.writeXSPFooter(fle, int(limit/numShows), "random")

                fle.close()

                network_tvshow_playlists.append(flename)

        # build mixed playlist combining all the network tvshows
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'network_' + network + '.xsp')
        try:
            fle = open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, "mixed", channelname, 'one')
        network = network.lower()

        for i in range(len(network_tvshow_playlists)):
            playlist = self.cleanString(network_tvshow_playlists[i])
            fle.write('    <rule field="playlist" operator="is">' + playlist + '</rule>\n')

        if int(randomtvshow) > 0:
            self.writeXSPFooter(fle, limit, "random")
        else:
            self.writeXSPFooter(fle, limit, "")

        network_playlists.append(flename)
        fle.close()
        
        return flename            


    def createShowPlaylist(self, show, serial, channelname, unwatched, nospecials, resolution):
        limit = REAL_SETTINGS.getSetting("limit")
        if limit == "0":
            limit = 50
        elif limit == "1":
            limit = 100
        elif limit == "2":
            limit = 250
        show_playlists = []
        show = show.lower()
        order = 'random'

        try:
            setting = int(serial)

            if setting & MODE_ORDERAIRDATE > 0:
                order = 'airdate'
        except:
            pass

        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'show_' + show + '_' + order + '.xsp')

        try:
            fle = open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, 'episodes', channelname, 'all')
        show = self.cleanString(show)
        fle.write('    <rule field="tvshow" operator="is">' + show + '</rule>\n')
        if unwatched:
            fle.write('    <rule field="playcount" operator="is">0</rule>\n')
        if nospecials:
            fle.write('    <rule field="season" operator="isnot">0</rule>\n')
        if len(resolution)>0:
            if resolution == 'SD Only':
                fle.write('    <rule field="videoresolution" operator="lessthan">720</rule>\n')
            if resolution == '720p or Higher':
                fle.write('    <rule field="videoresolution" operator="greaterthan">719</rule>\n')
            if resolution == '1080p Only':
                fle.write('    <rule field="videoresolution" operator="greaterthan">1079</rule>\n')

        self.writeXSPFooter(fle, limit, order)
        fle.close()
        show_playlists.append(flename)
        
        return flename


    def createGenreMixedPlaylist(self, genre, serial, channelname, unwatched, nospecials, resolution):
        limit = REAL_SETTINGS.getSetting("limit")
        if limit == "0":
            limit = 50
        elif limit == "1":
            limit = 100
        elif limit == "2":
            limit = 250
        genre = genre.lower()
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'mixed_' + genre + '.xsp')

        try:
            fle = open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''

        epname = os.path.basename(self.createGenrePlaylist('episodes', 3, genre, serial, channelname + " TV", unwatched, nospecials, resolution))
        moname = os.path.basename(self.createGenrePlaylist('movies', 4, genre, serial, channelname + " Movies", unwatched, nospecials, resolution))

        self.writeXSPHeader(fle, 'mixed', channelname, 'one')
        fle.write('    <rule field="playlist" operator="is">' + epname + '</rule>\n')
        fle.write('    <rule field="playlist" operator="is">' + moname + '</rule>\n')
        self.writeXSPFooter(fle, limit, "random")
        fle.close()

        return flename


    def createGenrePlaylist(self, pltype, chtype, genre, serial, channelname, unwatched, nospecials, resolution):
        limit = REAL_SETTINGS.getSetting("limit")
        if limit == "0":
            limit = 50
        elif limit == "1":
            limit = 100
        elif limit == "2":
            limit = 250
        pltype = pltype.lower()
        genre = genre.lower()
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + pltype + '_' + genre + '.xsp')
        try:
            fle = open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''
        self.writeXSPHeader(fle, pltype, channelname, 'all')
        genre = self.cleanString(genre)
        fle.write('    <rule field="genre" operator="is">' + genre + '</rule>\n')
        if unwatched:
            fle.write('    <rule field="playcount" operator="is">0</rule>\n')
        if (pltype=="episodes" and nospecials):
            fle.write('    <rule field="season" operator="isnot">0</rule>\n')
        if (pltype=="movies" and len(resolution)>0):
            if resolution == 'SD Only':
                fle.write('    <rule field="videoresolution" operator="lessthan">720</rule>\n')
            if resolution == '720p or Higher':
                fle.write('    <rule field="videoresolution" operator="greaterthan">719</rule>\n')
            if resolution == '1080p Only':
                fle.write('    <rule field="videoresolution" operator="greaterthan">1079</rule>\n')
        if (pltype=="episodes" and serial):
            self.writeXSPFooter(fle, limit, "airdate")
        else:
            self.writeXSPFooter(fle, limit, "random")
        fle.close()
        
        return flename


    def createStudioPlaylist(self, studio, serial, channelname, unwatched, nospecials, resolution):
        limit = REAL_SETTINGS.getSetting("limit")
        if limit == "0":
            limit = 50
        elif limit == "1":
            limit = 100
        elif limit == "2":
            limit = 250
        studio = studio.lower()
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'studio_' + studio + '.xsp')
        try:
            fle = open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''                
        self.writeXSPHeader(fle, "movies", channelname, 'all')
        studio = self.cleanString(studio)
        fle.write('    <rule field="studio" operator="is">' + studio + '</rule>\n')
        if unwatched:
            fle.write('    <rule field="playcount" operator="is">0</rule>\n')
        if nospecials:
            fle.write('    <rule field="season" operator="isnot">0</rule>\n')
        if len(resolution)>0:
            if resolution == 'SD Only':
                fle.write('    <rule field="videoresolution" operator="lessthan">720</rule>\n')
            if resolution == '720p or Higher':
                fle.write('    <rule field="videoresolution" operator="greaterthan">719</rule>\n')
            if resolution == '1080p Only':
                fle.write('    <rule field="videoresolution" operator="greaterthan">1079</rule>\n')
        if serial:
            self.writeXSPFooter(fle, limit, "airdate")
        else:
            self.writeXSPFooter(fle, limit, "random")
        fle.close()

        return flename


    def createMusicPlaylist(self, genre, channelname):
        limit = 1000
        pltype = "songs"
        genre = genre.lower()
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + pltype + '_' + genre + '.xsp')
        try:
            fle = open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''
        self.writeXSPHeader(fle, pltype, channelname, 'all')
        genre = self.cleanString(genre)
        fle.write('    <rule field="genre" operator="is">' + genre + '</rule>\n')
        self.writeXSPFooter(fle, limit, "random")
        fle.close()
        
        return flename


    def writeXSPHeader(self, fle, pltype, plname, match):
        fle.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
        fle.write('<smartplaylist type="' + pltype + '">\n')
        plname = self.cleanString(plname)
        fle.write('    <name>' + plname + '</name>\n')
        fle.write('    <match>' + match + '</match>\n')


    def writeXSPFooter(self, fle, limit, order):
        fle.write('    <limit>' + str(limit) + '</limit>\n')
        if order <> "":
            fle.write('    <order direction="ascending">' + order + '</order>\n')
        fle.write('</smartplaylist>\n')


    def cleanString(self, string):
        newstr = string
        newstr = newstr.replace('&', '&amp;')
        newstr = newstr.replace('>', '&gt;')
        newstr = newstr.replace('<', '&lt;')
        return newstr


    # Open the smart playlist and read the name out of it...this is the channel name
    def getSmartPlaylistName(self, fle):
        fle = xbmc.translatePath(fle)

        try:
            xml = open(fle, "r")
        except:
            self.log("getSmartPlaylisyName: Unable to open the smart playlist " + fle, xbmc.LOGERROR)
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
            self.log('getSmartPlaylistName: return ' + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except:
            self.log("getSmartPlaylistName:Unable to get the playlist name.", xbmc.LOGERROR)
            return ''


    def getSmartPlaylistType(self, dom):
        try:
            pltype = dom.getElementsByTagName('smartplaylist')
            return pltype[0].attributes['type'].value
        except:
            self.log("getSmartPlaylistType: Unable to get the playlist type.", xbmc.LOGERROR)
            return ''
            

    def getPlaylist(self, fle):
        try:
            xml = open(fle, "r")
        except:
            self.log("getPlaylist: Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return ''
        try:
            dom = parse(xml)
        except:
            self.log('getPlaylist: Problem parsing playlist ' + fle, xbmc.LOGERROR)
            xml.close()
            return ''
        xml.close()
        return dom


#####################################################
#####################################################
#
# File List Functions
#
#####################################################
#####################################################

    def buildChannelFileList(self, location, channel):
        if channel == "all":
            self.dlg = xbmcgui.DialogProgress()
            self.dlg.create("TV Time", "Create Channels")
            self.progress = 0
            self.line1 = "Creating Channels"
            self.line2 = "Deleting Previous Channel File Lists"
            self.line3 = ""
            self.updateDialog(self.progress, self.line1, self.line2, self.line3)

            # Delete previous file lists
            self.deleteFiles(location)

            # Go through all channels, check if they need to be reset
            maxChannels = int(REAL_SETTINGS.getSetting("maxChannels"))
            for i in range(maxChannels):
                channel = i + 1
                # check what type of channel it is so we know which method to rebuild file list
                chtype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
                chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")

                self.progress = self.progress + (100/maxChannels)
                self.line2 = "Creating Channel " + str(channel) + " - " + str(chname)
                self.line3 = ""
                self.updateDialog(int(self.progress), self.line1, self.line2, self.line3)

                if chtype < 7:
                    self.makeChannelListFromPlaylist(channel, location)
                    
                elif chtype == 7: # folder based
                    chsetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
                    self.makeChannelListFromFolder(channel, chsetting1, location)

                elif chtype == 8: # music
                    self.makeChannelListFromPlaylist(channel, location)
                
                # reset channel changed to false
                ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_changed","false")
                    
            self.dlg.close()

            # if temp location copy files to prestage now that they are finished
            if location == TEMP_LOC:
                self.deleteFiles(PRESTAGE_LOC)
                self.copyFiles(TEMP_LOC, PRESTAGE_LOC)
                self.deleteFiles(TEMP_LOC)

            # 1 = Once
            if REAL_SETTINGS.getSetting("ForceChannelReset") == "1":
                REAL_SETTINGS.setSetting('ForceChannelReset', '0')
        else:

            self.dlg = xbmcgui.DialogProgress()
            self.dlg.create("TV Time", "Create Channels")
            self.progress = 0
            self.line1 = "Creating Channels"
            self.line2 = "Deleting Previous Channel File List"
            self.line3 = ""
            self.updateDialog(self.progress,self.line1,self.line2,self.line3)

            filename = "channel_" + str(channel) + ".m3u"
            if os.path.exists(os.path.join(location, filename)):
                os.remove(os.path.join(location, filename))
            chtype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
            chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")

            self.line2 = "Creating Channel " + str(channel) + " - " + str(chname)
            self.line3 = ""
            self.updateDialog(self.progress,self.line1,self.line2,self.line3)

            if chtype < 7:
                self.makeChannelListFromPlaylist(channel, location)

            elif chtype == 7: # folder
                chsetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
                self.makeChannelListFromFolder(channel, chsetting1, location)

            elif chtype == 8: # music
                self.makeChannelListFromPlaylist(channel, location)

            # reset channel changed to false
            ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_changed","false")
                
            self.dlg.close()
            
            # 1 = Once
            if REAL_SETTINGS.getSetting("ForceChannelReset") == "1":
                REAL_SETTINGS.setSetting('ForceChannelReset', '0')
        
        # save settings
        ADDON_SETTINGS.writeSettings()
            
    
    def makeChannelListFromFolder(self, channel, folder, location):
        self.log("makeChannelListFromFolder")
        fileList = []
        self.videoParser = VideoParser()
        # set the types of files we want in our folder based file list
        flext = [".avi",".mp4",".m4v",".3gp",".3g2",".f4v",".flv",".mkv",".flv"]
        # get limit
        limit = REAL_SETTINGS.getSetting("limit")

        chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
        ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_time", "0")

        self.line2 = "Creating Channel " + str(channel) + " - " + str(chname)
        self.line3 = ""
        self.updateDialog(self.progress,self.line1,self.line2,self.line3)
        
        # make sure folder exist
        if os.path.exists(folder):
            self.line3 = "Scanning Folder"
            self.updateDialog(self.progress,self.line1,self.line2,self.line3)
            # get a list of filenames from the folder
            fnlist = []
            for root, subFolders, files in os.walk(folder):            
                for file in files:
                    # get file extension
                    basename, extension = os.path.splitext(file)
                    if extension in flext:
                        fnlist.append(os.path.join(root,file))

            # randomize list
            random.shuffle(fnlist)

            numfiles = 0
            if len(fnlist) < limit:
                limit = len(fnlist)

            self.line3 = "Adding Files to Channel"
            self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                
            for i in range(limit):
                fpath = fnlist[i]
                # get metadata for file
                title = self.getTitle(fpath)
                showtitle = self.getShowTitle(fpath)
                theplot = self.getThePlot(fpath)
                # get durations
                dur = self.videoParser.getVideoLength(fpath)
                if dur > 0:
                    # add file to file list
                    tmpstr = str(dur) + ',' + title + "//" + showtitle + "//" + theplot
                    tmpstr = tmpstr[:600]
                    tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                    tmpstr = tmpstr + '\n' + fpath.replace("\\\\", "\\")
                    fileList.append(tmpstr)

        # trailers bumpers commercials
        # check if fileList contains files
        if len(fileList) == 0:
            offair = REAL_SETTINGS.getSetting("offair")
            offairFile = REAL_SETTINGS.getSetting("offairfile")            
            if offair and len(offairFile) > 0:
                self.line3 = "Channel is Off Air"
                self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                dur = self.videoParser.getVideoLength(offairFile)
                # insert offair video file
                if dur > 0:
                    numFiles = int((60 * 60 * 24)/dur)
                    for i in range(numFiles):
                        tmpstr = str(dur) + ','
                        title = "Off Air"
                        showtitle = "Off Air"
                        theplot = "This channel is currently off the air"
                        tmpstr = str(dur) + ',' + showtitle + "//" + title + "//" + theplot
                        tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                        tmpstr = tmpstr + '\n' + offairFile.replace("\\\\", "\\")
                        fileList.append(tmpstr)
                ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_offair","1")
                ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2",MODE_SERIAL)
        else:
            ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_offair","0")
            commercials = REAL_SETTINGS.getSetting("commercials")
            commercialsfolder = REAL_SETTINGS.getSetting("commercialsfolder")
            bumpers = REAL_SETTINGS.getSetting("bumpers")
            bumpersfolder = REAL_SETTINGS.getSetting("bumpersfolder")
            if (commercials == "true" and os.path.exists(commercialsfolder)) or (bumpers == "true" and os.path.exists(bumpersfolder)):
                if (commercials == "true" and os.path.exists(commercialsfolder)) :
                    commercialInterval = self.getCommercialInterval(channel, len(fileList))
                    commercialNum = self.getCommercialNum(channel, len(fileList))
                if (bumpers == "true" and os.path.exists(bumpersfolder)):
                    bumperInterval = self.getBumperInterval(channel, len(fileList))
                    bumperNum = self.getBumperNum(channel, len(fileList))
                trailerInterval = 0
                trailerNum = 0
                trailers = False
                bumpers = False
                commercials = False
                if not int(bumperInterval) == 0:
                    bumpers = True
                if not int(commercialInterval) == 0:
                    commercials = True
                fileList = self.insertFiles(channel, fileList, commercials, bumpers, trailers, commercialInterval, bumperInterval, trailerInterval, commercialNum, bumperNum, trailerNum)

        # write m3u
        self.writeFileList(channel, fileList, location)


    def getTitle(self, fpath):
        dbase = os.path.dirname(fpath)
        fbase = os.path.basename(fpath)
        fname = os.path.splitext(fbase)[0]
        tvshowdir = os.path.split(dbase)[(len(os.path.split(dbase))-2)]
        fle = os.path.join(tvshowdir, "series.xml")
        title = ""
        # look for series.xml
        # same folder as file
        if os.path.isfile(fle):
            """
            <Series>
              <SeriesName>Chuck</SeriesName>
            </Series>        
            """
            try:
                dom = parse(fle)
            except:
                self.log("getTVShow: Problem parsing playlist " + fle, xbmc.LOGERROR)
                xml.close()
                return title

            try:
                seriesNameNode = dom.getElementsByTagName('SeriesName')
            except:
                xml.close()
       
            if seriesNameNode:
                title = seriesNameNode[0].firstChild.nodeValue

        # look for tvshow.nfo
        # same folder as file
        fle = os.path.join(tvshowdir, "tvshow.nfo")
        if os.path.isfile(fle):
            """
            <tvshow>
                <title>Chuck</title>
            </tvshow>
            """
            try:
                dom = parse(fle)
            except:
                self.log("getTVShow: Problem parsing playlist " + fle, xbmc.LOGERROR)
                xml.close()
                return title

            try:
                titleNode = dom.getElementsByTagName('title')
            except:
                xml.close()
       
            if titleNode:
                title = titleNode[0].firstChild.nodeValue

        # user folder name if all else fails
        if title == "":        
            title = os.path.split(fpath)[(len(os.path.split(fpath))-1)]
        
        title = title.encode("utf-8")

        return title


    def getShowTitle(self, fpath):
        dbase = os.path.dirname(fpath)
        fbase = os.path.basename(fpath)
        fname = os.path.splitext(fbase)[0]                
        showtitle = ""
        # Media Center Master
        # location = ./metadata
        # filename format = <filename>.xml
        fle = os.path.join(dbase, "metadata", fname + ".xml")
        if os.path.isfile(fle):
            """
            <Item>
              <EpisodeName>Chuck Versus the Intersect</EpisodeName>
              <FirstAired>2007-09-24</FirstAired>
              <Overview>Chuck Bartowski is an average computer geek until files of government secrets are downloaded into his brain. He is soon scouted by the CIA and NSA to act in place of their computer.</Overview>
            </Item>        
            """
            try:
                dom = parse(fle)
            except:
                self.log("getShowTitle: Problem parsing playlist " + fle, xbmc.LOGERROR)
                xml.close()
                return showtitle

            try:
                episodeNameNode = dom.getElementsByTagName('EpisodeName')
            except:
                xml.close()
       
            if episodeNameNode:
                showtitle = episodeNameNode[0].firstChild.nodeValue

        # XBMC
        # location = same as video files
        # filename format = <filename.nfo
        fle = os.path.join(dbase, fname + ".nfo")
        if os.path.isfile(fle):
            """
            <episodedetails>
                <title>Chuck Versus the Intersect</title>
                <plot>Chuck Bartowski is an average computer geek until files of government secrets are downloaded into his brain. He is soon scouted by the CIA and NSA to act in place of their computer.</plot>
                <aired>2007-09-24</aired>
            </episodedetails>        
            """
            try:
                dom = parse(fle)
            except:
                self.log("getShowTitle: Problem parsing playlist " + fle, xbmc.LOGERROR)
                xml.close()
                return showtitle

            try:
                titleNode = dom.getElementsByTagName('title')
            except:
                xml.close()
       
            if titleNode:
                showtitle = titleNode[0].firstChild.nodeValue

        # if all else fails, get showtitle from folder
        if showtitle == "":
            showtitle = os.path.split(fpath)[(len(os.path.split(fpath))-2)]

        showtitle = showtitle.encode("utf-8")

        return showtitle


    def getThePlot(self, fpath):
        dbase = os.path.dirname(fpath)
        fbase = os.path.basename(fpath)
        fname = os.path.splitext(fbase)[0]                
        theplot = ""
        # Media Center Master
        # location = ./metadata
        # filename format = <filename>.xml
        fle = os.path.join(dbase, "metadata", fname + ".xml")
        if os.path.isfile(fle):
            # Read the video meta data
            """
            <Item>
              <EpisodeName>Chuck Versus the Intersect</EpisodeName>
              <FirstAired>2007-09-24</FirstAired>
              <Overview>Chuck Bartowski is an average computer geek until files of government secrets are downloaded into his brain. He is soon scouted by the CIA and NSA to act in place of their computer.</Overview>
            </Item>        
            """
            try:
                dom = parse(fle)
            except:
                self.log("getShowTitle: Problem parsing playlist " + fle, xbmc.LOGERROR)
                xml.close()
                return showtitle

            try:
                overviewNode = dom.getElementsByTagName('Overview')
            except:
                xml.close()
       
            if overviewNode:
                theplot = overviewNode[0].firstChild.nodeValue

        # XBMC
        # location = same as video files
        # filename format = <filename.nfo
        fle = os.path.join(dbase, fname + ".nfo")
        if os.path.isfile(fle):
            """
            <episodedetails>
                <title>Chuck Versus the Intersect</title>
                <plot>Chuck Bartowski is an average computer geek until files of government secrets are downloaded into his brain. He is soon scouted by the CIA and NSA to act in place of their computer.</plot>
                <aired>2007-09-24</aired>
            </episodedetails>        
            """
            try:
                dom = parse(fle)
            except:
                self.log("getShowTitle: Problem parsing playlist " + fle, xbmc.LOGERROR)
                xml.close()
                return showtitle

            try:
                plotNode = dom.getElementsByTagName('plot')
            except:
                xml.close()
       
            if plotNode:
                theplot = plotNode[0].firstChild.nodeValue

        theplot = theplot.encode("utf-8")
        return theplot


    def makeChannelListFromPlaylist(self, channel, location):
        limit = REAL_SETTINGS.getSetting("limit")
        if limit == "0":
            limit = 50
        elif limit == "1":
            limit = 100
        elif limit == "2":
            limit = 250

        # get channel settings
        fle = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_playlist') # Playlist filename
        chtype = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type') # Channel type
        channelName = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_3') # Channel Name
        serial = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_2') # Serial or Random

        self.line2 = "Making Channel " + str(channel) + " File List"
        self.line3 = ""
        self.updateDialog(self.progress,self.line1,self.line2,self.line3)
        
        if len(fle) == 0:
            self.log("makeChannelListFromPlaylist: Unable to locate the playlist for channel " + str(channelName), xbmc.LOGERROR)
            return False
        try:
            xml = open(fle, "r")
        except:
            self.log("makeChannelListFromPlaylist: Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return False

        try:
            dom = parse(xml)
        except:
            self.log("makeChannelListFromPlaylist: Problem parsing playlist " + fle, xbmc.LOGERROR)
            xml.close()
            return False

        pltype = self.getSmartPlaylistType(dom)

        try:
            orderNode = dom.getElementsByTagName('order')
            limitNode = dom.getElementsByTagName('limit')
        except:
            pass
        
        if limitNode:
            plimit = limitNode[0].firstChild.nodeValue
            # force a max limit of 250 for performance reason
            if int(plimit) < limit:
                limit = plimit
        
        randomize = False
        if orderNode:
            if orderNode[0].childNodes[0].nodeValue.lower() == 'random':
                randomize = True

        xml.close()

        if pltype == 'mixed':
            self.level = 0 # used in buildMixedFileListFromPlaylist to keep track of limit for different playlists
            self.fileLists = []
            self.fileLists = self.buildMixedFileListsFromPlaylist(fle, channel)
            
            if not "movies" in self.fileLists and not "episodes" in self.fileLists:
                fileList = self.buildMixedTVShowFileList(self.fileLists, channel, limit)
            else:
                fileList = self.buildMixedFileList(self.fileLists, channel, limit)
                if randomize:
                    random.shuffle(fileList)                    
        else:
            #self.channelType = pltype
            fileList = self.buildFileListFromPlaylist(channel, fle)
            if randomize:
                random.shuffle(fileList)                    

        # check if fileList contains files
        if len(fileList) == 0:
            offair = REAL_SETTINGS.getSetting("offair")
            offairFile = REAL_SETTINGS.getSetting("offairfile")            
            if offair and len(offairFile) > 0:
                self.line3 = "Channel is Off Air"
                self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                dur = self.videoParser.getVideoLength(offairFile)
                # insert offair video file
                if dur > 0:
                    numFiles = int((60 * 60 * 24)/dur)
                    for i in range(numFiles):
                        tmpstr = str(dur) + ','
                        title = "Off Air"
                        showtitle = "Off Air"
                        theplot = "This channel is currently off air"
                        tmpstr = str(dur) + ',' + showtitle + "//" + title + "//" + theplot
                        tmpstr = tmpstr.replace("\\n", " ").replace("\n", " ").replace("\r", " ").replace("\\r", " ").replace("\\\"", "\"")
                        tmpstr = tmpstr + '\n' + offairFile.replace("\\\\", "\\")
                        fileList.append(tmpstr)                
                ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_offair","1")
                ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2",MODE_SERIAL)
        else:

            ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_offair","0")

            if pltype == "movies":
                trailers = REAL_SETTINGS.getSetting("trailers")
                trailersfolder = REAL_SETTINGS.getSetting("trailersfolder")
                if (trailers == "true" and os.path.exists(trailersfolder)):
                    trailerInterval = self.getTrailerInterval(channel, len(fileList))
                    trailerNum = self.getTrailerNum(channel, len(fileList))
                    commercialInterval = 0
                    commercialNum = 0
                    bumperInterval = 0
                    bumperNum = 0
                    trailers = False
                    bumpers = False
                    commercials = False
                    if not int(trailerInterval) == 0:
                        trailers = True
                    #if not bumperInterval == 0:
                    #    bumpers = True
                    #if not commercialInterval == 0:
                    #    commercials = True
                    fileList = self.insertFiles(channel, fileList, commercials, bumpers, trailers, commercialInterval, bumperInterval, trailerInterval, commercialNum, bumperNum, trailerNum)
            else:
                commercials = REAL_SETTINGS.getSetting("commercials")
                commercialsfolder = REAL_SETTINGS.getSetting("commercialsfolder")
                bumpers = REAL_SETTINGS.getSetting("bumpers")
                bumpersfolder = REAL_SETTINGS.getSetting("bumpersfolder")
                if (commercials == "true" and os.path.exists(commercialsfolder)) or (bumpers == "true" and os.path.exists(bumpersfolder)):
                    if (commercials == "true" and os.path.exists(commercialsfolder)):
                        commercialInterval = self.getCommercialInterval(channel, len(fileList))
                        commercialNum = self.getCommercialNum(channel, len(fileList))
                    if (bumpers == "true" and os.path.exists(bumpersfolder)):
                        bumperInterval = self.getBumperInterval(channel, len(fileList))
                        bumperNum = self.getBumperNum(channel, len(fileList))
                    trailerInterval = 0
                    trailerNum = 0
                    trailers = False
                    bumpers = False
                    commercials = False
                    if not int(bumperInterval) == 0:
                        bumpers = True
                    if not int(commercialInterval) == 0:
                        commercials = True
                    fileList = self.insertFiles(channel, fileList, commercials, bumpers, trailers, commercialInterval, bumperInterval, trailerInterval, commercialNum, bumperNum, trailerNum)

        # valid channel
        self.writeFileList(channel, fileList, location)


    def getBumpersList(self, channel):
        self.log("getBumpersList")
        bumpersList = []
        chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
        type = "bumpers"

        try:
            metafile = open(META_LOC + str(type) + ".meta", "r")
        except:
            self.Error('Unable to open the meta file ' + META_LOC + str(type) + '.meta', xbmc.LOGERROR)
            return False

        for file in metafile:
            # filter by channel name
            bumperMeta = []
            bumperMeta = file.split('|')
            thepath = bumperMeta[0]
            basepath = os.path.dirname(thepath)
            chfolder = os.path.split(basepath)[1]
            # bumpers are channel specific
            if chfolder == chname:
                bumpersList.append(file)

        metafile.close()

        return bumpersList


    def getCommercialsList(self, channel):
        self.log("getCommercialsList")
        commercialsList = []
        chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
        type = "commercials"
        channelOnlyCommercials = False

        try:
            metafile = open(META_LOC + str(type) + ".meta", "r")
        except:
            self.Error('Unable to open the meta file ' + META_LOC + str(type) + '.meta', xbmc.LOGERROR)
            return False

        for file in metafile:
            # filter by channel name
            commercialMeta = []
            commercialMeta = file.split('|')
            thepath = commercialMeta[0]
            basepath = os.path.dirname(thepath)
            chfolder = os.path.split(basepath)[1]
            if chfolder == chname:
                if channelOnlyCommercials:
                    # channel specific trailers are in effect
                    commercialsList.append(file)
                else:
                    # reset list to only contain channel specific trailers
                    channelOnlyCommercials = True
                    commercialsList = []
                    commercialsList.append(file)
            else:
                if not channelOnlyCommercials:
                    commercialsList.append(file)

        metafile.close()

        return commercialsList


    def getTrailersList(self, channel):
        self.log("getTrailersList")
        trailersList = []
        chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
        type = "trailers"
        channelOnlyTrailers = False

        try:
            metafile = open(META_LOC + str(type) + ".meta", "r")
        except:
            self.log('Unable to open the meta file ' + META_LOC + str(type) + '.meta')
            return False

        for file in metafile:
            # filter by channel name
            trailerMeta = []
            trailerMeta = file.split('|')
            thepath = trailerMeta[0]
            basepath = os.path.dirname(thepath)
            chfolder = os.path.split(basepath)[1]
            if chfolder == chname:
                if channelOnlyTrailers:
                    # channel specific trailers are in effect
                    trailersList.append(file)
                else:
                    # reset list to only contain channel specific trailers
                    channelOnlyTrailers = True
                    trailersList = []
                    trailersList.append(file)
            else:
                if not channelOnlyTrailers:
                    trailersList.append(file)

        metafile.close()

        return trailersList


    def convertMetaToFile(self, metaFileStr):
        # parse file meta data
        metaFile = []
        metaFile = metaFileStr.split('|')
        thepath = metaFile[0]
        dur = metaFile[1]
        title = metaFile[2]
        showtitle = metaFile[3]
        theplot = metaFile[4]
        # format to file list structure
        tmpstr = str(dur) + ','
        tmpstr += showtitle + "//" + title + "//" + theplot
        tmpstr = tmpstr[:600]
        tmpstr = tmpstr.replace("\\n", " ").replace("\n", " ").replace("\r", " ").replace("\\r", " ").replace("\\\"", "\"")
        tmpstr = tmpstr + '\n' + thepath.replace("\\\\", "\\")
        return tmpstr
    

    def insertFiles(self, channel, fileList, commercials, bumpers, trailers, cinterval, binterval, tinterval, cnum, bnum, tnum):
        newFileList = []
        
        if bumpers:
            bumpersList = []
            bumpersList = self.getBumpersList(channel)
            
        if commercials:
            commercialsList = []
            commercialsList = self.getCommercialsList(channel)
        
        if trailers:
            trailersList = []
            trailersList = self.getTrailersList(channel)
        
        for i in range(len(fileList)):
            newFileList.append(fileList[i])
            if commercials:
                self.line3 = "Inserting Commercials"
                self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                if len(commercialsList) > 0:
                    if (i+1) % cinterval == 0:
                        for n in range(int(cnum)):
                            commercialFile = random.choice(commercialsList)
                            if len(commercialFile) > 0:
                                newFileList.append(self.convertMetaToFile(commercialFile))
                            else:
                                self.log('insertFiles: Unable to get commercial')                                        
                else:
                    self.log("No valid commercials available")

            if bumpers:
                self.line3 = "Inserting Bumpers"
                self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                if len(bumpersList) > 0:
                    # mix in bumpers
                    if (i+1) % binterval == 0:
                        for n in range(int(bnum)):
                            bumperFile = random.choice(bumpersList)
                            if len(bumperFile) > 0:
                                newFileList.append(self.convertMetaToFile(bumperFile))
                            else:
                                self.log('insertFiles: Unable to get bumper')                                                                
                else:
                    self.log("No valid bumpers available")

            if trailers:
                self.line3 = "Inserting Trailers"
                self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                if len(trailersList) > 0:
                    # mix in trailers
                    if (i+1) % tinterval == 0:
                        for n in range(int(tnum)):
                            trailerFile = random.choice(trailersList)
                            if len(trailerFile) > 0:
                                newFileList.append(self.convertMetaToFile(trailerFile))
                            else:
                                self.log('insertFiles: Unable to get trailer')
                
        fileList = newFileList    

        return fileList
        

    def buildMixedTVShowFileList(self, fileLists, channel, limit):
        self.channelType = "mixedtvshows"
        tvshowList = []        
        fileList = []
        maxFileListItems = 0
        numTotalItems = 0

        chsetting9 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_9") 
        if chsetting9 == "":
            chsetting9 = 0
        
        # get fileList sizes
        for i in range(len(fileLists)):
            numTotalItems = numTotalItems + len(fileLists[i].list)            
            if len(fileLists[i].list) > maxFileListItems:
                maxFileListItems = len(fileLists[i].list)

        if int(chsetting9) == int(MODE_RANDOM_FILELISTS):
            random.shuffle(fileLists)
            
        # make sure we have files in the lists
        if maxFileListItems > 0:
            # loop through filelists for each item using maxFileList Items
            for i in range(maxFileListItems):
                # loop through each filelist in fileLists
                fl = 0 
                for fl in range(len(fileLists)):
                    # if i is less than number items in filelist then get next item
                    if i < len(fileLists[fl].list):
                        fileList.append(fileLists[fl].list[i])
                    fl = fl + 1                

        # limit filelist
        fileList = fileList[0:int(limit)]
        return fileList


    def buildMixedFileList(self, fileLists, channel, limit):
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
                if int(movieIndex) == 999:
                    movieIndex = i
                numMovieItems = numMovieItems + len(fileLists[i].list)
                movieList.extend(fileLists[i].list)
            elif fileLists[i].type == "episodes":
                if int(episodeIndex) == 999:
                    episodeIndex = i
                numEpisodeItems = numEpisodeItems + len(fileLists[i].list)
                episodeList.extend(fileLists[i].list)
            elif fileLists[i].type == "tvshows":
                if int(tvshowIndex) == 999:
                    tvshowIndex = i
                numTVShowItems = numTVShowItems + len(fileLists[i].list)
                tvshowList.extend(fileLists[i].list)
            i = i + 1

        # randomize if playlist order set to random
        chsetting9 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_9") # randomize filelists
        if int(chsetting9) == int(MODE_RANDOM_FILELISTS):
            random.shuffle(movieList)
            random.shuffle(episodeList)
            random.shuffle(tvshowList)
            
        numTotalItems = numMovieItems + numEpisodeItems + numTVShowItems
        
        if numMovieItems > 0:
            ratioMovies = int(round(numTotalItems / numMovieItems))

        if numEpisodeItems > 0:
            ratioEpisodes = int(round(numTotalItems / numEpisodeItems))

        if numTVShowItems > 0:
            ratioTVShows = int(round(numTotalItems / numTVShowItems))

        if int(ratioMovies) > 0 or int(ratioEpisodes) > 0 or int(ratioTVShows):
            itemMultiplier = int(round(int(limit)/(int(ratioMovies) + int(ratioEpisodes) + int(ratioTVShows))))
        else:
            itemMultiplier = 0

        numMovies = itemMultiplier * ratioMovies
        numEpisodes = itemMultiplier * ratioEpisodes
        numTVShows = itemMultiplier * ratioTVShows

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

        # limit filelist
        fileList = fileList[0:int(limit)]

        return fileList


    def buildMixedFileListsFromPlaylist(self, src, channel):
        limit = REAL_SETTINGS.getSetting("limit")
        if limit == "0":
            limit = 50
        elif limit == "1":
            limit = 100
        elif limit == "2":
            limit = 250
        dom1 = self.getPlaylist(src)
        pltype = self.getSmartPlaylistType(dom1)

        try:
            rulesNode = dom1.getElementsByTagName('rule')
            orderNode = dom1.getElementsByTagName('order')
            limitNode = dom1.getElementsByTagName('limit')
        except:
            self.log('buildMixedFileListsFromPlaylist: Problem parsing playlist ' + filename, xbmc.LOGERROR)
            xml.close()
            return fileList
   
        if limitNode:
            plimit = limitNode[0].firstChild.nodeValue
            # force a max limit of 250 for performance reason
            if int(plimit) < limit:
                limit = plimit

        # get order to determine whether fileList should be randomized
        if orderNode:
            order = orderNode[0].firstChild.nodeValue
        else:
            order = ""

        self.level = self.level + 1        
        if self.level == 1:
            ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_limit",limit)
            if order == "random":
                ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_9",MODE_RANDOM_FILELISTS)
            
        # need to redo this for loop
        for rule in rulesNode:
            i = 0                        
            fileList = []
            rulename = rule.childNodes[i].nodeValue
            if os.path.exists(os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache/generated'), rulename)):
                src1 = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache/generated'), rulename)
            else:
                src1 = ""
                self.log("buildMixedFileListsFromPlaylist: Problem finding source file: " + os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/cache/generated'), rulename))
            dom1 = self.getPlaylist(src1)
            pltype1 = self.getSmartPlaylistType(dom1)
            if pltype1 == 'movies' or pltype1 == 'episodes' or pltype1 == 'tvshows':
                #tmpList = []
                fileList = self.buildFileListFromPlaylist(channel, src1)
                if len(fileList) > 0:
                    #if order == 'random':
                    #    random.shuffle(tmpList)
                    #fileList.extend(tmpList)
                    self.fileLists.append(channelFileList(pltype1, limit, fileList))
            elif pltype1 == 'mixed':
                if os.path.exists(src1):
                    self.buildMixedFileListsFromPlaylist(src1)
                else:
                    self.log("buildMixedFileListsFromPlaylist: Problem finding source file: " + src1)
            i = i + 1
        return self.fileLists


    def buildFileListFromPlaylist(self, channel, playlist, media_type="video", recursive="TRUE"):        
        fileList = []
        chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
        self.line2 = "Creating Channel " + str(channel) + " - " + str(chname)
        self.line3 = "Querying XBMC Database"
        self.updateDialog(self.progress,self.line1,self.line2,self.line3)
        self.videoParser = VideoParser()
        json_query = '{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "recursive": "%s", "fields":["duration","tagline","showtitle","album","artist","plot"]}, "id": 1}' % ( self.escapeDirJSON( playlist ), media_type, recursive )
        json_folder_detail = xbmc.executeJSONRPC(json_query)
#        self.log(json_folder_detail)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        fileNum = 1
        for f in file_detail:
            match = re.search('"file" *: *"(.*?)",', f)
            if match:
                if(match.group(1).endswith("/") or match.group(1).endswith("\\")):
                    if(recursive == "TRUE"):
                        fileList.extend(self.buildFileListFromPlaylist(match.group(1), media_type, recursive))
                else:
                    duration = re.search('"duration" *: *([0-9]*?),', f)
                    title = re.search('"label" *: *"(.*?)"', f)
                    showtitle = re.search('"showtitle" *: *"(.*?)"', f)

                    try:
                        dur = int(duration.group(1))
                    except:
                        dur = 0

                    if dur == 0:
                        dur = self.videoParser.getVideoLength(match.group(1).replace("\\\\", "\\"))
                        if showtitle != None:
                            self.line3 = "Getting Duration for " + showtitle.group(1) + " - " + title.group(1)
                        else:
                            self.line3 = "Getting Duration for " + title.group(1)
                        self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                        
                    try:
                        if dur > 0:
                            #title = re.search('"label" *: *"(.*?)"', f)
                            tmpstr = str(dur) + ','
                            #showtitle = re.search('"showtitle" *: *"(.*?)"', f)
                            plot = re.search('"plot" *: *"(.*?)",', f)
                            if showtitle != None:
                                self.line3 = "Adding " + showtitle.group(1) + " - " + title.group(1)
                            else:
                                self.line3 = "Adding " + title.group(1)
                            self.updateDialog(self.progress,self.line1,self.line2,self.line3)
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


    def getTrailerInterval(self, channel, numfiles):
        self.log("getTrailerInterval")
        trailerInterval = ''
        numTrailers = REAL_SETTINGS.getSetting("numtrailers")
        maxTrailers = REAL_SETTINGS.getSetting("maxtrailers")
        
        if numTrailers == "":
            trailerInterval = 0
            
        elif numTrailers == "0":
            # need to determine how many commercials are available compared with number of files in tv channel to get a ratio
            numTotalTrailers = len(self.getTrailersList(channel))

            if numTotalTrailers > 0:
                trailerInterval = int(numfiles) / numTotalTrailers
                # if there are more commercials than files in the channel, set interval to 1
                if trailerInterval < 1:
                    trailerInterval = 1
            else:
                trailerInterval = 0
        else:
            trailerInterval = 1
            
        return trailerInterval


    def getTrailerNum(self, channel, numfiles):
        self.log("getTrailerNum")
        trailerInterval = ''
        numTrailers = REAL_SETTINGS.getSetting("numtrailers")
        maxTrailers = REAL_SETTINGS.getSetting("maxtrailers")

        if numTrailers == "":
            numTrailers = 0
            
        elif numTrailers == "0":
            # need to determine how many commercials are available compared with number of files in tv channel to get a ratio
            numTotalTrailers = len(self.getTrailersList(channel))

            if numTotalTrailers > 0:
                numTrailers = numTotalTrailers / int(numfiles)
                if numTrailers < 1:
                    numTrailers = 1
                if numTrailers > maxTrailers:
                    numTrailers = maxTrailers
            else:
                numTrailers = 0
            
        return numTrailers


    def getCommercialInterval(self, channel, numfiles):
        self.log("getCommercialInterval")
        commercialInterval = ''
        numCommercials = REAL_SETTINGS.getSetting("numcommercials")
        maxCommercials = int(REAL_SETTINGS.getSetting("maxcommercials")) + 1

        # check if number of commercials set to auto
        if numCommercials == "":
            commercialInterval = 0
            
        elif numCommercials == "0":
            # need to determine how many commercials are available compared with number of files in tv channel to get a ratio
            numTotalCommercials = len(self.getCommercialsList(channel))

            if numTotalCommercials > 0:
                commercialInterval = int(numfiles) / numTotalCommercials
                # if there are more commercials than files in the channel, set interval to 1
                if commercialInterval < 1:
                    commercialInterval = 1
            else:
                commercialInterval = 0
        else:
            commercialInterval = 1

        return commercialInterval


    def getCommercialNum(self, channel, numfiles):
        self.log("getCommercialNum")
        numCommercials = REAL_SETTINGS.getSetting("numcommercials")
        maxCommercials = int(REAL_SETTINGS.getSetting("maxcommercials")) + 1

        # check if number of commercials set to auto
        if numCommercials == "":
            numCommercials = 0
            
        elif numCommercials == "0":
            # need to determine how many commercials are available compared with number of files in tv channel to get a ratio
            numTotalCommercials = len(self.getCommercialsList(channel))

            if numTotalCommercials > 0:
                numCommercials = numTotalCommercials / int(numfiles)
                if numCommercials < 1:
                    numCommercials = 1
                if numCommercials > maxCommercials:
                    numCommercials = maxCommercials
            else:
                numCommercials = 0

        return numCommercials


    def getBumperInterval(self, channel, numfiles):
        self.log("getBumperInterval")
        bumperInterval = ''
        numBumpers = REAL_SETTINGS.getSetting("numbumpers")
        maxBumpers = REAL_SETTINGS.getSetting("maxbumpers")

        # check if number of commercials set to auto
        if numBumpers == "":
            bumperInterval = 0
            
        elif numBumpers == "0":
            # need to determine how many bumpers are available compared with number of files in tv channel to get a ratio
            numTotalBumpers = len(self.getBumpersList(channel))

            if numTotalBumpers > 0:
                bumperInterval = int(numfiles) / numTotalBumpers
                # if there are more bumpers than files in the channel, set interval to 1
                if bumperInterval < 1:
                    bumperInterval = 1
            else:
                bumperInterval = 0
        else:
            bumperInterval = 1                

        return bumperInterval


    def getBumperNum(self, channel, numfiles):
        numBumpers = REAL_SETTINGS.getSetting("numbumpers")
        maxBumpers = REAL_SETTINGS.getSetting("maxbumpers")
        bumpersFolder = REAL_SETTINGS.getSetting("bumpersfolder")
        channelName = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
        # check if number of commercials set to auto
        if numBumpers == "":
            numBumpers = 0
            
        elif numBumpers == "0":
            # need to determine how many bumpers are available compared with number of files in tv channel to get a ratio
            numTotalBumpers = len(self.getBumpersList(channel))

            if numTotalBumpers > 0:
                # need to determine number of bumpers to play during interval
                numBumpers = numTotalBumpers / int(numfiles)
                if numBumpers < 1:
                    numBumpers = 1
                if numBumpers > maxBumpers:
                    numBumpers = maxBumpers
            else:
                numBumpers = 0

        return numBumpers


    def getTotalDuration(self, channel, location):
        try:
            fileList = open(location + "channel_" + str(channel) + ".m3u", "r")
        except:
            self.Error('getTotalDuration: Unable to open the cache file ' + location + 'channel_' + str(channel) + '.m3u', xbmc.LOGERROR)

        totalDuration = 0
        i = 0
        for string in fileList:
            # capture duration of final filelist to get total duration for channel
            if string.find("#EXTINF:") == 0:
                string_split = string.split(',')
                string = string_split[0]
                string_split = string.split(':')
                dur = string_split[1]
                totalDuration = totalDuration + int(dur)
            i = i + 1
        fileList.close()
                
        return totalDuration


    def writeFileList(self, channel, fileList, location):
        try:
            channelplaylist = open(location + "channel_" + str(channel) + ".m3u", "w")
        except:
            self.Error('writeFileList: Unable to open the cache file ' + CHANNELS_LOC + 'channel_' + str(channel) + '.m3u', xbmc.LOGERROR)

        # get channel name from settings
        channelplaylist.write("#EXTM3U\n")
        fileList = fileList[:250]
        # Write each entry into the new playlist
        string_split = []
        totalDuration = 0
        for string in fileList:
            # capture duration of final filelist to get total duration for channel
            string_split = string.split(',')
            totalDuration = totalDuration + int(string_split[0])
            # write line
            channelplaylist.write("#EXTINF:" + string + "\n")
        channelplaylist.close()
        ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_totalDuration", str(totalDuration))
        # copy to prestage to ensure there is always a prestage file available for the auto reset
        # this is to cover the use case where a channel setting has been changed 
        # after the auto reset time has expired resulting in a new channel being created
        # during the next start as well as a auto reset being triggered which moves
        # files from prestage to the cache directory
        if location == CHANNELS_LOC:
            cache_file = os.path.join(location, "channel_" + str(channel) + ".m3u")        
            shutil.copy(cache_file, PRESTAGE_LOC)


    def getFile(self, folder):
        tmpstr = ""
        self.videoParser = VideoParser()
        self.getFileTries = self.getFileTries + 1       
        self.getFile = ""
        if os.path.exists(folder):
            if self.getFileTries < 100:
                # get directory contents
                try:
                    filename = random.choice(os.listdir(folder))
                    if len(filename) > 0:
                        # get duration of file
                        dur = self.videoParser.getVideoLength(os.path.join(folder, filename))
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
            self.log("getFile: Folder does not exist " + folder)

        self.getFileTries = 0
        return self.getfile
        

#####################################################
#####################################################
#
# Utility Functions
#
#####################################################
#####################################################

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('ChannelList:' + msg, level)


    def deleteFiles(self, location):
        dir = xbmc.translatePath(os.path.join('special://profile/addon_data/',ADDON_ID,location))       
        for filename in os.listdir(dir):
            fle = os.path.join(dir, filename)
            try:
                if os.path.isfile(fle):
                    os.unlink(fle)
            except Exception, e:
                self.log(str(e))
                
        
    def copyFiles(self, source, destination):
        src_files = os.listdir(source)
        for file_name in src_files:
            full_file_name = os.path.join(source, file_name)
            if (os.path.isfile(full_file_name)):
                shutil.copy(full_file_name, destination)        


    def updateDialog(self, progress, line1, line2, line3):
        self.dlg.update(progress,line1,line2,line3)


    # handle fatal errors: log it, show the dialog, and exit
    def Error(self, message):
        self.log('FATAL ERROR: ' + message, xbmc.LOGFATAL)
        dlg = xbmcgui.Dialog()
        dlg.ok('Error', message)
        del dlg
        self.log("Error: calling end")
        self.end()


class channelFileList(object):
    def __init__(self, type, limit, list):
        self.type = type
        self.limit = limit
        self.list = list

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('channelFileList: ' + msg, level)


