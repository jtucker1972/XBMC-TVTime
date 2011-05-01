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
import shutil
import glob

import Globals

from xml.dom.minidom import parse, parseString

from Playlist import Playlist
from Globals import *
from Channel import Channel
from VideoParser import VideoParser

# Globals
NUMBER_CHANNEL_TYPES = Globals.NUMBER_CHANNEL_TYPES


class PrestageThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.networkList = []
        self.studioList = []
        self.mixedGenreList = []
        self.showGenreList = []
        self.movieGenreList = []
        self.showList = []
        REAL_SETTINGS.setSetting("ForceChannelResetActive","false")
        self.getFileTries = 0

    def run(self):        
        isRunning = False
        while (Globals.prestageThreadExit == 0):
            if not isRunning:
                isRunning == True
                self.buildMetaFileLists()
                self.buildPrestageFileLists()
            time.sleep(1)
        self.log("Exiting Thread")
        thread.exit()


#####################################################
#####################################################
#
# Playlist Functions
#
#####################################################
#####################################################

    def getSmartPlaylistType(self, dom):
        if (Globals.prestageThreadExit == 0):
            try:
                pltype = dom.getElementsByTagName('smartplaylist')
                return pltype[0].attributes['type'].value
            except:
                self.log("getSmartPlaylistType: Unable to get the playlist type.", xbmc.LOGERROR)
                return ''
        else:
            self.abort()
            

    def getPlaylist(self, fle):
        if (Globals.prestageThreadExit == 0):
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
        else:
            self.abort()

#####################################################
#####################################################
#
# Meta File List Functions
#
#####################################################
#####################################################

    def buildMetaFileLists(self):
        if (Globals.prestageThreadExit == 0):
            # Build Metadata file for commercials, bumpers and trailers
            # so we don't have to reprocess them for each channel
            # only build metafile data if feature enabled
            if REAL_SETTINGS.getSetting("bumpers") == "true":
                folder = REAL_SETTINGS.getSetting("bumpersfolder")
                type = "bumpers"
                self.buildMetaFile(type, folder)
            if REAL_SETTINGS.getSetting("commercials") == "true":
                folder = REAL_SETTINGS.getSetting("commercialsfolder")
                type = "commercials"
                self.buildMetaFile(type, folder)
            if REAL_SETTINGS.getSetting("trailers") == "true":
                folder = REAL_SETTINGS.getSetting("trailersfolder")
                type = "trailers"
                self.buildMetaFile(type, folder)


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
        

#####################################################
#####################################################
#
# File List Functions
#
#####################################################
#####################################################

    def buildPrestageFileLists(self):
        if (Globals.prestageThreadExit == 0):
            # Delete previous file lists if channels changed
            if Globals.resetPrestage == 1:
                self.deleteFiles(TEMP_LOC)
                Globals.resetPrestage = 0

            # Go through all channels, check if they need to be reset
            maxChannels = int(REAL_SETTINGS.getSetting("maxChannels"))
            for i in range(maxChannels):
                if (Globals.prestageThreadExit == 0):
                    channel = i + 1
                    if not os.path.exists(os.path.join(TEMP_LOC,"channel_"+str(channel)+".m3u")):
                        # check what type of channel it is so we know which method to rebuild file list
                        chtype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
                        chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")

                        if chtype < 7:
                            self.makeChannelListFromPlaylist(channel, TEMP_LOC)
                            
                        elif chtype == 7: # folder
                            chsetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
                            self.makeChannelListFromFolder(channel, chsetting1, TEMP_LOC)

                        elif chtype == 8: # music
                            self.makeChannelListFromPlaylist(channel, TEMP_LOC)                        

            # if copy files to prestage now that they are finished
            self.deleteFiles(PRESTAGE_LOC)
            self.copyFiles(TEMP_LOC, PRESTAGE_LOC)
            self.deleteFiles(TEMP_LOC)

            # 1 = Once
            if REAL_SETTINGS.getSetting("ForceChannelReset") == "1":
                REAL_SETTINGS.setSetting('ForceChannelReset', '0')

        else:
            self.abort()
            

    def makeChannelListFromFolder(self, channel, folder, location):
        if (Globals.prestageThreadExit == 0):
            self.log("makeChannelListFromFolder")
            fileList = []
            self.videoParser = VideoParser()
            # set the types of files we want in our folder based file list
            flext = [".avi",".mp4",".m4v",".3gp",".3g2",".f4v",".flv",".mkv"]
            # get limit
            limit = REAL_SETTINGS.getSetting("limit")

            chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
            #ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_time", "0")

            # make sure folder exist
            if os.path.exists(folder):
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
                    #
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
                            tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                            tmpstr = tmpstr + '\n' + offairFile.replace("\\\\", "\\")
                            fileList.append(tmpstr)                
            else:
                commercials = REAL_SETTINGS.getSetting("commercials")
                commercialsfolder = REAL_SETTINGS.getSetting("commercialsfolder")
                bumpers = REAL_SETTINGS.getSetting("bumpers")
                bumpersfolder = REAL_SETTINGS.getSetting("bumpersfolder")
                if (commercials == "true" and os.path.exists(commercialsfolder)) or (bumpers == "true" and os.path.exists(bumpersfolder)):
                    if (commercials == "true" and os.path.exists(commercialsfolder)):
                        commercialInterval = self.getCommercialInterval(channel, len(fileList))
                        commercialNum = self.getCommercialNum(channel, len(fileList))
                    else:
                        commercialInterval = 0
                        commercialNum = 0                        
                    if (bumpers == "true" and os.path.exists(bumpersfolder)):
                        bumperInterval = self.getBumperInterval(channel, len(fileList))
                        bumperNum = self.getBumperNum(channel, len(fileList))
                    else:
                        bumperInterval = 0
                        bumperNum = 0                        
                    trailerInterval = 0
                    trailerNum = 0 
                    trailers = False
                    bumpers = False
                    commercials = False

                    if not bumperInterval == 0:
                        bumpers = True
                    if not commercialInterval == 0:
                        commercials = True

                    fileList = self.insertFiles(channel, fileList, commercials, bumpers, trailers, commercialInterval, bumperInterval, trailerInterval, commercialNum, bumperNum, trailerNum)

            # write m3u
            self.writeFileList(channel, fileList, location)
        else:
            self.abort()


    def getTitle(self, fpath):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def getShowTitle(self, fpath):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def getThePlot(self, fpath):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def makeChannelListFromPlaylist(self, channel, location):
        if (Globals.prestageThreadExit == 0):
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
                self.channelType = pltype
                fileList = self.buildFileListFromPlaylist(channel, fle)
                if randomize:
                    random.shuffle(fileList)                    


            # check if fileList contains files
            if len(fileList) == 0:
                offair = REAL_SETTINGS.getSetting("offair")
                offairFile = REAL_SETTINGS.getSetting("offairfile")            
                if offair and len(offairFile) > 0:
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
            else:
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
                        if not trailerInterval == 0:
                            trailers = True                            
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
                        if not bumperInterval == 0:
                            bumpers = True
                        if not commercialInterval == 0:
                            commercials = True
                        fileList = self.insertFiles(channel, fileList, commercials, bumpers, trailers, commercialInterval, bumperInterval, trailerInterval, commercialNum, bumperNum, trailerNum)

            # valid channel
            self.writeFileList(channel, fileList, location)

        else:
            self.abort()


    def getBumpersList(self, channel):
        if (Globals.prestageThreadExit == 0):
            bumpersList = []
            chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
            type = "bumpers"

            try:
                metafile = open(META_LOC + str(type) + ".meta", "r")
            except:
                self.Error('Unable to open the meta file ' + META_LOC + str(type) + '.meta', xbmc.LOGERROR)
                return False

            for file in metafile:
                if (Globals.prestageThreadExit == 0):
                    # filter by channel name
                    bumperMeta = []
                    bumperMeta = file.split('|')
                    thepath = bumperMeta[0]
                    basepath = os.path.dirname(thepath)
                    chfolder = os.path.split(basepath)[1]
                    # bumpers are channel specific
                    if chfolder == chname:
                        bumpersList.append(file)
                else:
                    metafile.close()
                    self.abort()

            metafile.close()

            return bumpersList
        else:
            self.abort()


    def getCommercialsList(self, channel):
        if (Globals.prestageThreadExit == 0):
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
                if (Globals.prestageThreadExit == 0):
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
                else:
                    metafile.close()
                    self.abort()

            metafile.close()

            return commercialsList
        else:
            self.abort()


    def getTrailersList(self, channel):
        if (Globals.prestageThreadExit == 0):
            trailersList = []
            chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
            type = "trailers"
            channelOnlyTrailers = False

            try:
                metafile = open(META_LOC + str(type) + ".meta", "r")
            except:
                self.Error('Unable to open the meta file ' + META_LOC + str(type) + '.meta', xbmc.LOGERROR)
                return False

            for file in metafile:
                if (Globals.prestageThreadExit == 0):
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
                else:
                    metafile.close()
                    self.abort()

            metafile.close()

            return trailersList
        else:
            self.abort()


    def convertMetaToFile(self, metaFileStr):
        if (Globals.prestageThreadExit == 0):
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
        else:
            self.abort()
    

    def insertFiles(self, channel, fileList, commercials, bumpers, trailers, cinterval, binterval, tinterval, cnum, bnum, tnum):
        if (Globals.prestageThreadExit == 0):
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
                    if len(commercialsList) > 0:
                        # mix in commercials
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
                    if len(bumpersList) > 0:
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
                    if len(trailersList) > 0:
                        if (i+1) % tinterval == 0:
                            for n in range(int(tnum)):
                                trailerFile = random.choice(trailersList)
                                if len(trailerFile) > 0:
                                    newFileList.append(self.convertMetaToFile(trailerFile))
                                else:
                                    self.log('insertFiles: Unable to get trailer')
                    
            fileList = newFileList    
            return fileList
        
        else:
            self.abort()


    def buildMixedTVShowFileList(self, fileLists, channel, limit):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def buildMixedFileList(self, fileLists, channel, limit):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def buildMixedFileListsFromPlaylist(self, src, channel):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def buildFileListFromPlaylist(self, channel, playlist, media_type="video", recursive="TRUE"):        
        if (Globals.prestageThreadExit == 0):
            fileList = []
            chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
            self.videoParser = VideoParser()
            """
            XBMC-VERSION:
              0 - Dharma (Version 10)
              1 - Pre-Eden (Nightlies)
            """
            if REAL_SETTINGS.getSetting("XBMC-VERSION") == "0":
                # Dharma version
                json_query = '{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "recursive": "%s", "fields":["duration","tagline","showtitle","album","artist","plot"]}, "id": 1}' % ( self.escapeDirJSON( playlist ), media_type, recursive )
            else:
                # Pre-Eden - Version
                json_query = '{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "fields":["duration","tagline","showtitle","album","artist","plot"]}, "id": 1}' % ( self.escapeDirJSON( playlist ), media_type )

            json_folder_detail = xbmc.executeJSONRPC(json_query)
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
                            
                        try:
                            if dur > 0:
                                #title = re.search('"label" *: *"(.*?)"', f)
                                tmpstr = str(dur) + ','
                                #showtitle = re.search('"showtitle" *: *"(.*?)"', f)
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

        else:
            self.abort()


    def getTrailerInterval(self, channel, numfiles):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def getTrailerNum(self, channel, numfiles):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def getCommercialInterval(self, channel, numfiles):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def getCommercialNum(self, channel, numfiles):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def getBumperInterval(self, channel, numfiles):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def getBumperNum(self, channel, numfiles):
        if (Globals.prestageThreadExit == 0):
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

        else:
            self.abort()


    def writeFileList(self, channel, fileList, location):
        if (Globals.prestageThreadExit == 0):
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
            #ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_totalDuration", str(totalDuration))
            # copy to prestage to ensure there is always a prestage file available for the auto reset
            # this is to cover the use case where a channel setting has been changed 
            # after the auto reset time has expired resulting in a new channel being created
            # during the next start as well as a auto reset being triggered which moves
            # files from prestage to the cache directory
            #if location == CHANNELS_LOC:
            #    cache_file = os.path.join(location, "channel_" + str(channel) + ".m3u")        
            #    shutil.copy(cache_file, PRESTAGE_LOC)

        else:
            self.abort()


    def getFile(self, folder):
        if (Globals.prestageThreadExit == 0):
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
        
        else:
            self.abort()


#
# Channel Reset Functions
#
    """
    # rebuild filelists
    def forceChannelReset(self, channel):
        if (Globals.prestageThreadExit == 0):
            self.channels = []

            if channel == "all":
                # reset all channels
                # we only want one reset occuring at a time so let's put a check in
                if REAL_SETTINGS.getSetting("ForceChannelResetActive") == "false" or REAL_SETTINGS.getSetting("ForceChannelResetActive") == "":
                    REAL_SETTINGS.setSetting('LastResetTime', str( int ( time.time() ) ) )
                    REAL_SETTINGS.setSetting('ForceChannelResetActive', "true")
                    # if force reset, delete all cache files 
                    self.deleteFiles(CHANNELS_LOC)
                    # if force reset, delete all prestage files
                    self.deleteFiles(PRESTAGE_LOC)
                    # call function to rebuild all channel file lists
                    self.buildChannelFileList(CHANNELS_LOC, "all")
                    # reset the force setting to Never if it was set to Once
                    if REAL_SETTINGS.getSetting("ForceChannelReset") == "1":
                        REAL_SETTINGS.setSetting("ForceChannelReset", "0")
                    # reset finished
                    REAL_SETTINGS.setSetting('ForceChannelResetActive', "false")
                else:
                    pass
            else:
                # only reset the channel passed
                if REAL_SETTINGS.getSetting("ForceChannelResetActive") == "false" or REAL_SETTINGS.getSetting("ForceChannelResetActive") == "":
                    filename = "channel_" + str(channel) + ".m3u"
                    REAL_SETTINGS.setSetting('LastResetTime', str(int(time())))
                    REAL_SETTINGS.setSetting('ForceChannelResetActive', "true")
                    # if force reset, delete cache file 
                    os.remove(os.path.join(CHANNELS_LOC, filename))
                    # if force reset, delete all prestage files
                    os.remove(os.path.join(PRESTAGE_LOC, filename))
                    # call function to rebuild all channel file lists
                    self.buildChannelFileList(CHANNELS_LOC, channel)
                    # reset finished
                    REAL_SETTINGS.setSetting('ForceChannelResetActive', "false")
            
        else:
            self.abort()

    
    def autoChannelReset(self):
        if (Globals.prestageThreadExit == 0):
            if REAL_SETTINGS.getSetting("autoResetChannelActive") == "false":
                # reset started
                REAL_SETTINGS.setSetting("autoResetChannelActive", "true")
                # delete previous files in the cache
                self.deleteFiles(CHANNELS_LOC)        
                # copy pre-staged channel file lists to cache
                self.copyFiles(PRESTAGE_LOC, CHANNELS_LOC)
                REAL_SETTINGS.setSetting("autoResetChannelActive", "false")
        else:
            self.abort()


    # check if auto reset times have expired
    def checkAutoChannelReset(self):
        if (Globals.prestageThreadExit == 0):
            autoChannelResetSetting = int(REAL_SETTINGS.getSetting("autoChannelResetSetting"))

            # need to get channel settings
            self.channels = []
            needsreset = False
            try:
                self.lastResetTime = int(REAL_SETTINGS.getSetting("LastResetTime"))
            except:
                self.lastResetTime = 0
            
            # loop through channel settings to get
            #   totalTimePlayed
            #   totalDuration
            for i in range(int(REAL_SETTINGS.getSetting("maxChannels"))):                

                totalTimePlayed = ADDON_SETTINGS.getSetting("Channel_" + str(i+1) + "_time")
                if totalTimePlayed == "":
                    totalTimePlayed = 0

                totalDuration =  ADDON_SETTINGS.getSetting("Channel_" + str(i+1) + "_totalDuration")
                if totalDuration == "":
                    totalDuration = 0

                channelResetSetting = REAL_SETTINGS.getSetting("ChannelResetSetting")
                if channelResetSetting == "":
                    channelResetSetting = 0

                if channelResetSetting == 0 and totalTimePlayed > totalDuration:
                    needsreset = True


            if autoChannelResetSetting > 0 and autoChannelResetSetting < 4:
                timedif = time.time() - self.lastResetTime

                if channelResetSetting == 1 and timedif > (60 * 60 * 24):
                    needsreset = True

                if channelResetSetting == 2 and timedif > (60 * 60 * 24 * 7):
                    needsreset = True

                if channelResetSetting == 3 and timedif > (60 * 60 * 24 * 30):
                    needsreset = True

                if timedif < 0:
                    needsreset = True

                if needsreset:
                    REAL_SETTINGS.setSetting('LastResetTime', str(int(time.time())))

            return needsreset
 
        else:
            self.abort()
    """

#####################################################
#####################################################
#
# Utility Functions
#
#####################################################
#####################################################

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('PrestageThread:' + msg, level)


    def deleteFiles(self, location):
        if (Globals.prestageThreadExit == 0):
            dir = xbmc.translatePath(os.path.join('special://profile/addon_data/',ADDON_ID,location))       
            for filename in os.listdir(dir):
                fle = os.path.join(dir, filename)
                try:
                    if os.path.isfile(fle):
                        os.unlink(fle)
                except Exception, e:
                    self.log(str(e))
        else:
            self.abort()
        

    def copyFiles(self, source, destination):
        if (Globals.prestageThreadExit == 0):
            src_files = os.listdir(source)
            for file_name in src_files:
                full_file_name = os.path.join(source, file_name)
                if (os.path.isfile(full_file_name)):
                    shutil.copy(full_file_name, destination)        
        else:
            self.abort()


    def escapeDirJSON(self, dir_name):
        if (dir_name.find(":")):
            dir_name = dir_name.replace("\\", "\\\\")
            return dir_name
        else:
            self.abort()

    def abort(self):
        self.log("PrestageThread Aborted")
        self.log("Exiting Thread")
        thread.exit()


class channelFileList(object):
    def __init__(self, type, limit, list):
        self.type = type
        self.limit = limit
        self.list = list

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('channelFileList: ' + msg, level)


    

