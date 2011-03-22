#   Copyright (C) 2011 James A. Tucker
#
#
# This file is part of TVTime.
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

import os
import glob
import shutil
import xbmc, xbmcgui, xbmcaddon
from Globals import *
from xml.dom.minidom import parse, parseString, Document
from decimal import *

class presetChannel(object):
    def __init__(self, name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution):
        self.log('presetChannel: ' + name + ', type: ' + type)
        self.name = name
        self.type = type
        self.rule1 = rule1
        self.rule2 = rule2
        self.operator1 = operator1
        self.operator2 = operator2
        self.criteria1 = criteria1
        self.criteria2 = criteria2
        self.random = random
        self.unwatched = unwatched
        self.nospecials = nospecials
        self.resolution = resolution
        # self.limit
        if str(limit) == '0':
            self.limit = 10
        elif str(limit) == '1':
            self.limit = 25
        elif str(limit) == '2':
            self.limit = 50
        elif str(limit) == '3':
            self.limit = 75
        elif str(limit) == '4':
            self.limit = 100
        elif str(limit) == '5':
            self.limit = 250
        else:
            self.limit = 0
        # self.numepisodes
        if str(numepisodes) == '0':
            self.numepisodes = 1
        elif str(numepisodes) == '1':
            self.numepisodes = 2
        elif str(numepisodes) == '2':
            self.numepisodes = 3
        elif str(numepisodes) == '3':
            self.numepisodes = 4
        elif str(numepisodes) == '4':
            self.numepisodes = 5
        elif str(numepisodes) == '5':
            self.numepisodes = 6
        elif str(numepisodes) == '6':
            self.numepisodes = 7
        elif str(numepisodes) == '7':
            self.numepisodes = 8
        elif str(numepisodes) == '8':
            self.numepisodes = 9
        elif str(numepisodes) == '9':
            self.numepisodes = 10
        else:
            self.numepisodes = 0
        # self.nummovies
        if str(nummovies) == '0':
            self.nummovies = 1
        elif str(nummovies) == '1':
            self.nummovies = 2
        elif str(nummovies) == '2':
            self.nummovies = 3
        elif str(nummovies) == '3':
            self.nummovies = 4
        elif str(nummovies) == '4':
            self.nummovies = 5
        elif str(nummovies) == '5':
            self.nummovies = 6
        elif str(nummovies) == '6':
            self.nummovies = 7
        elif str(nummovies) == '7':
            self.nummovies = 8
        elif str(nummovies) == '8':
            self.nummovies = 9
        elif str(nummovies) == '9':
            self.nummovies = 10
        else:
            self.nummovies = 0


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Init: ' + msg, level)


class presetChannelFileList(object):
    def __init__(self, type, limit, list):
        self.log('presetChannelList: ' + type)
        self.type = type
        self.limit = limit
        self.list = list

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Init: ' + msg, level)


class presetChannels:
    def __init__(self):
        self.presetChannels = []    
        self.log('Creating Preset Channels')


    def findMaxPresetChannels(self):
        self.log('Determining Total Number of Channels')
        numPresetChannels = 0
        for channel in self.presetChannels:
            numPresetChannels += 1
        self.log('Total Channels: ' + str(numPresetChannels))
        return numPresetChannels
             

    def buildPresetChannels(self, numPresetChannels):
        self.log('buildPresetChannels: Started')
        # Loop through Preset Channels
        channelNum = 1

        # add some feedback to the user on the progress
        self.loadDialog = xbmcgui.DialogProgress()
        self.loadDialog.create("TV Time", "Create Channel Playlists")
        self.loadDialog.update(0, "Creating Channel Playlists")        

        # set the decimal precision
        getcontext().prec = 4
        progressIncrement = Decimal(100) / Decimal(numPresetChannels)
        progressPercentage = 0
        while (channelNum < numPresetChannels + 1):
            self.log('Build Preset Channel #:' + str(channelNum))
            self.buildPresetChannel(channelNum)
            progressPercentage = Decimal(progressPercentage) + Decimal(progressIncrement)
            self.loadDialog.update(progressPercentage, "Creating Channel Playlist " + str(channelNum))
            channelNum = channelNum + 1

        # If the user pressed cancel, stop everything and exit
        if self.loadDialog.iscanceled():
            self.log('Create Channel Playlists Cancelled')
            self.loadDialog.close()
            self.end()
            return False
        self.loadDialog.close()        
        self.log('buildPresetChannels: Completed')


    def buildPresetChannel(self, channelNum):
        self.log('buildPresetChannel: Started')
        type = self.presetChannels[channelNum-1].type
        name = self.presetChannels[channelNum-1].name
        rule1 = self.presetChannels[channelNum-1].rule1
        rule2 = self.presetChannels[channelNum-1].rule2
        operator1 = self.presetChannels[channelNum-1].operator1
        operator2 = self.presetChannels[channelNum-1].operator2
        criteria1 = self.presetChannels[channelNum-1].criteria1
        criteria2 = self.presetChannels[channelNum-1].criteria2
        limit = self.presetChannels[channelNum-1].limit
        random = self.presetChannels[channelNum-1].random
        unwatched = self.presetChannels[channelNum-1].unwatched
        nospecials = self.presetChannels[channelNum-1].nospecials
        resolution = self.presetChannels[channelNum-1].resolution
        numepisodes = self.presetChannels[channelNum-1].numepisodes
        nummovies = self.presetChannels[channelNum-1].nummovies

        self.log("#########################################################")
        self.log("buildPresetChannel:" + str(channelNum))
        self.log("type:" + str(type))
        self.log("name:" + str(name))
        self.log("rule1:" + str(rule1))
        self.log("rule2:" + str(rule2))
        self.log("operator1:" + str(operator1))
        self.log("operator2:" + str(operator2))
        self.log("criteria1:" + str(criteria1))
        self.log("criteria2:" + str(criteria2))
        self.log("limit:" + str(limit))
        self.log("random:" + str(random))
        self.log("unwatched:" + str(unwatched))
        self.log("nospecials:" + str(nospecials))
        self.log("resolution:" + str(resolution))
        self.log("numepisodes:" + str(numepisodes))
        self.log("nummovies:" + str(nummovies))
        self.log("#########################################################")

        playlists = []
        mixedplaylists = []

        if type == 'episodes':
            self.log('It is an episode channel')
            # need to check if there are multiple criteria passed
            # if so, this will have to be a mixed playlist
            criterias = []
            criterias = criteria1.split('|')
            x = 0
            if len(criterias) > 1:
                self.log('Channel has multiple criteria...creating mixed episode playlist')
                for criteria in criterias:
                    channelNum_x = str(channelNum) + '_' + str(x+1)
                    criteria1 = criteria
                    self.log('Creating episode playlist for ' + rule1 + ' ' + operator1 + ' ' + criteria1)
                    # for each criteria, create an episode playlist for the mixed channel
                    # Channel_X_x
                    self.buildPlaylist(channelNum_x, type, name, rule1, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution)
                    # combine episode playlists into a mixed playlist
                    playlists.append(channelNum_x)
                    x = x + 1
                self.log('Creating episode channel playlist')
                # reset limit for the channel
                limit = self.presetChannels[channelNum-1].limit
                # Combine playlists into a mixed playlist
                self.buildMixedPlaylist(channelNum, name, playlists, limit, random)              
            else:
                self.log('Creating episode channel playlist')
                # if not, then a standard playlist will do
                self.buildPlaylist(channelNum, type, name, rule1, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution)
  
        if type == 'movies':
            self.log('It is a movie channel')
            # need to check if there are multiple criteria passed
            # if so, this will have to be a mixed playlist
            criterias = []
            criterias = criteria1.split('|')
            x = 0
            if len(criterias) > 1:
                self.log('Channel has multiple criteria...creating mixed movie playlist')
                for criteria in criterias:
                    channelNum_x = str(channelNum) + '_' + str(x+1)
                    criteria1 = criteria
                    self.log('Creating movie playlist for ' + rule1 + ' ' + operator1 + ' ' + criteria1)
                    # for each criteria, create an episode playlist for the mixed channel
                    # Channel_X_x
                    self.buildPlaylist(channelNum_x, type, name, rule1, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution)
                    # combine episode playlists into a mixed playlist
                    playlists.append(channelNum_x)
                    x = x + 1
                # Combine playlists into a mixed playlist
                self.log('Creating movie channel playlist')
                # reset limit for the channel
                limit = self.presetChannels[channelNum-1].limit
                self.buildMixedPlaylist(channelNum, name, playlists, limit, random)              
            else:
                self.log('Creating movie channel playlist')
                # if not, then a standard playlist will do
                self.buildPlaylist(channelNum, type, name, rule1, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution)

        if type == 'mixed':
            self.log('It is a mixed channel')
            # create the episode playlist and capture playlist filename
            # Channel_X_t
            channelNum_t = str(channelNum) + '_1'
            criterias = []
            criterias = criteria1.split('|')
            if len(criterias) > 1:
                self.log('Channel has multiple episode criteria...creating mixed episode playlist')
                x = 0
                playlists = []
                for criteria in criterias:
                    channelNum_x = str(channelNum_t) + '_' + str(x+1)
                    self.log('Creating episode playlist for ' + rule1 + ' ' + operator1 + ' ' + criteria1)
                    # for each criteria, create an episode playlist for the mixed channel
                    # Channel_X_t_x
                    type = 'episodes'
                    criteria1 = criteria
                    limit = numepisodes
                    self.buildPlaylist(channelNum_x, type, name, rule1, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution)
                    playlists.append(channelNum_x)
                    x = x + 1
                # Combine playlists into a mixed playlist
                # Channel_X_1
                self.log('Combining playlists into a mixed episode playlist')
                self.buildMixedPlaylist(channelNum_t, name, playlists, limit, random)              
            else:
                type = 'episodes'
                limit = numepisodes
                self.log('Creating episode playlist')
                # if not, then a standard playlist will do
                # Channel_t
                self.buildPlaylist(channelNum_t, type, name, rule1, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution)
            episodeplaylist = channelNum_t

            # create the movie playlist and capture playlist filename
            channelNum_t = str(channelNum) + '_2'

            criterias = []
            criterias = criteria2.split('|')
            if len(criterias) > 1:
                self.log('Channel has multiple movie criteria...creating mixed movie playlist')
                x = 0
                playlists = []
                for criteria in criterias:
                    channelNum_x = str(channelNum_t) + '_' + str(x+1)
                    type = 'movies'
                    criteria1 = criteria
                    limit = nummovies
                    self.log('Creating movie playlist')
                    self.buildPlaylist(channelNum_x, type, name, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution)
                    playlists.append(channelNum_x)
                    x = x + 1
                # Channel_X_1
                self.log('Combining playlists into a mixed movie playlist')
                self.buildMixedPlaylist(channelNum_t, name, playlists, limit, random)              
            else:
                type = 'movies'
                limit = nummovies
                self.log('Creating movie playlist')
                self.buildPlaylist(channelNum_t, type, name, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution)
            movieplaylist = channelNum_t

            # reset limit
            # add episode playlist to mixedplaylist x times
            # add movie playlist to mixedplaylist x times
            # loop
            limit = self.presetChannels[channelNum-1].limit
            mixedplaylists = []

            if int(limit) < (int(numepisodes) + int(nummovies)):
                tl = 1 # total loops
            else:
                tl = int(round(int(limit)/(int(numepisodes) + int(nummovies)))) # total loops

            if tl == 0:
                tl = 1

            self.log("mix limit: " + str(limit))
            self.log("mix numepisodes: " + str(numepisodes))
            self.log("mix nummovies: " + str(nummovies))
            self.log("mix tl: " + str(tl))

            for l in range(0, tl):
                 mixedplaylists.append(episodeplaylist)
                 mixedplaylists.append(movieplaylist)
                        
            self.log('Creating mixed channel playlist')
            self.buildMixedPlaylist(channelNum, name, mixedplaylists, limit, random)                              

        if type == 'custom':
            self.log('Copying custom playlist')
            src = str(criteria1)
            self.copyCustomChannel(channelNum, src)

        self.log('buildPresetChannel: Completed')


    def buildMixedPlaylist(self, channelNum, name, mixPlaylists, limit, random):
        self.log('buildMixedPlaylist: Started')

        criteria = []
        rule = 'playlist'
        operator = 'is'
        criterias = mixPlaylists

        # create xml doc
        presetChannel = self.createPresetPlaylist()
        # add smartplaylist element
        smartplaylist = self.addSmartplaylist(presetChannel, 'mixed')
        # add name element
        self.addName(presetChannel, smartplaylist, name)
        # add match always 'one'
        match = 'one'
        self.addMatch(presetChannel, smartplaylist, match)
        # add rule1 element
        #   genre
        #   firstaired
        #   rating
        #   studio
        # loop through criteria to get each playlist and add it as a rule
        x = 0
        if len(criterias) > 1:
            for criteria in criterias:
                # need to add folder path to criteria string
                criteria = 'Channel_' + criteria + '.xsp'
                self.addRule(presetChannel, smartplaylist, rule, operator, criteria)
                x = x + 1
        if random == "true":
            # add order element with
            #     attribute direction = random
            #     attribute order = ascending
            order = 'random'
            direction = 'ascending'
            self.addOrder(presetChannel, smartplaylist, order, direction)
        else:
            # order by airdate
            order = 'airdate'
            direction = 'ascending'
            self.addOrder(presetChannel, smartplaylist, order, direction)            
        if limit > 0:                
            # add limit element
            self.addLimit(presetChannel, smartplaylist, limit)
        # log xml output
        self.log(presetChannel.toprettyxml(indent="  "))
        self.writepresetChannel(presetChannel, channelNum)        
        self.log('buildMixedPlaylist: Completed')


    def buildPlaylist(self, channelNum, type, name, rule, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution):
        self.log('buildPlaylist: Started')
        # create xml doc
        presetChannel = self.createPresetPlaylist()
        # add smartplaylist element
        smartplaylist = self.addSmartplaylist(presetChannel, type)
        # add name element
        self.addName(presetChannel, smartplaylist, name)
        # add match always 'one'
        match = 'all'
        self.addMatch(presetChannel, smartplaylist, match)

        # add rule element
        #   genre
        #   firstaired
        #   rating
        #   studio
        # add rule1 element
        if type == 'episodes':
            if rule == 'airdate':
                # first aired range requires two criteria
                self.addRule(presetChannel, smartplaylist, rule, operator1, criteria1)
                self.addRule(presetChannel, smartplaylist, rule, operator2, criteria2)          
            elif rule <> '':
                self.addRule(presetChannel, smartplaylist, rule, operator1, criteria1)
        
        if type == 'movies':
            if rule == 'year':
                if len(criteria1) > 4:
                    # sharing date format with episodes so need to convert
                    # convert yyyy/mm/dd to yyyy
                    # '2009-12-31' to '2009'
                    criteria1 = criteria1[0:4]
                if len(criteria2) > 4:
                    # sharing date format with episodes so need to convert
                    # convert yyyy/mm/dd to yyyy
                    # '2009-12-31' to '2009'
                    criteria2 = criteria2[0:4] 
                # year range requires two criteria
                self.addRule(presetChannel, smartplaylist, rule, operator1, criteria1)
                self.addRule(presetChannel, smartplaylist, rule, operator2, criteria2)                

            elif rule <> '':
                self.addRule(presetChannel, smartplaylist, rule, operator1, criteria1)

        # optional elements:
        #   unwatched only
        #   nospecials
        #   resolution
        # add rule1 elements for options
        if unwatched == "true":
            rule = 'playcount'
            operator = 'is'
            criteria = '0'
            self.addRule(presetChannel, smartplaylist, rule, operator, criteria)

        if nospecials == "true":
            if type == 'episodes':
                rule = 'season'
                operator = 'isnot'
                criteria = '0'
                self.addRule(presetChannel, smartplaylist, rule, operator, criteria)

        if resolution > 0:
            if resolution == 1:
                rule = 'videoresolution'
                operator = 'lessthan'
                criteria = '720'
                self.addRule(presetChannel, smartplaylist, rule, operator, criteria)
            if resolution == 2:
                rule = 'videoresolution'
                operator = 'greaterthan'
                criteria = '719'
                self.addRule(presetChannel, smartplaylist, rule, operator, criteria)
            if resolution == 3:
                rule = 'videoresolution'
                operator = 'greaterthan'
                criteria = '1079'
                self.addRule(presetChannel, smartplaylist, rule, operator, criteria)

        # add order element with
        #     attribute direction = random
        #     attribute order = ascending
        if random == "true":
            # direction = random
            # order = ascending
            order = 'random'
            direction = 'ascending'
            self.addOrder(presetChannel, smartplaylist, order, direction)

        # add limit element
        if limit > 0:                
            # limit number of items
            self.addLimit(presetChannel, smartplaylist, limit)

        # log xml output
        self.log(presetChannel.toprettyxml(indent="  "))
        self.writepresetChannel(presetChannel, channelNum)
        self.log('buildPlaylist: Completed')
        

    def createPresetPlaylist(self):
        self.log('createPresetPlaylist: Started')
        presetChannel = Document()
        self.log('createPresetPlaylist: Completed')
        return presetChannel


    def addSmartplaylist(self, presetChannel, type):
        self.log('addSmartplaylist: Started')
        self.log('addSmartplaylist: type=' + str(type))
        smartplaylist = presetChannel.createElement("smartplaylist")
        smartplaylist.setAttribute("type", type)
        presetChannel.appendChild(smartplaylist)
        self.log('addSmartplaylist: Completed')
        return smartplaylist


    def addName(self, presetChannel, smartplaylist, name):
        self.log('addName: Started')
        self.log('addName: name=' + str(name))
        nameElement = presetChannel.createElement("name")
        nameText = presetChannel.createTextNode(str(name))
        nameElement.appendChild(nameText)
        smartplaylist.appendChild(nameElement)
        self.log('addName: Completed')
        

    def addMatch(self, presetChannel, smartplaylist, match):
        self.log('addMatch: Started')
        self.log('addMatch: match=' + str(match))
        matchElement = presetChannel.createElement("match")
        matchText = presetChannel.createTextNode(str(match))
        matchElement.appendChild(matchText)
        smartplaylist.appendChild(matchElement)
        self.log('addMatch: Completed')
   

    def addRule(self, presetChannel, smartplaylist, field, operator, criteria):
        self.log('addRule: Started')
        self.log('addRule: field=' + str(field))
        self.log('addRule: operator=' + str(operator))
        self.log('addRule: criteria=' + str(criteria))
        ruleElement = presetChannel.createElement("rule")
        ruleElement.setAttribute("field", field)
        ruleElement.setAttribute("operator", operator)
        ruleText = presetChannel.createTextNode(str(criteria))
        ruleElement.appendChild(ruleText)
        smartplaylist.appendChild(ruleElement)
        self.log('addRule: Completed')


    def addLimit(self, presetChannel, smartplaylist, limit):
        self.log('addLimit: Started')
        self.log('addLimit: limit=' + str(limit))
        limitElement = presetChannel.createElement("limit")
        limitText = presetChannel.createTextNode(str(limit))
        limitElement.appendChild(limitText)
        smartplaylist.appendChild(limitElement)
        self.log('addLimit: Completed')


    def addOrder(self, presetChannel, smartplaylist, order, direction):
        self.log('addOrder: Started')
        self.log('addOrder: order=' + str(order))
        self.log('addOrder: direction=' + str(direction))
        orderElement = presetChannel.createElement("order")
        orderElement.setAttribute("direction", direction)
        orderText = presetChannel.createTextNode(str(order))
        orderElement.appendChild(orderText)
        smartplaylist.appendChild(orderElement)
        self.log('addOrder: Completed')


    def writepresetChannel(self, presetChannel, channelNum):
        self.log('writepresetChannel: Started')
        self.log('writepresetChannel: channelNum=' + str(channelNum))
        # get path to write to
        filename = 'Channel_' + str(channelNum) + '.xsp'
        fle = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets/'), filename)
        self.log('writepresetChannel: fle=' + str(fle))
        # write xml file
        f = open(fle, "w")
        presetChannel.writexml(f)
        f.close()
        self.log('writepresetChannel: Completed')


    def getPlaylist(self, fle):
        self.log('getPlaylist: Started')
        self.log('getPlaylist: fle=' + str(fle))
        try:
            xml = open(fle, "r")
        except:
            self.log("getPlaylist Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return ''
        try:
            dom = parse(xml)
        except:
            self.log('getPlaylist Problem parsing playlist ' + fle, xbmc.LOGERROR)
            xml.close()
            return ''
        xml.close()
        self.log('getPlaylist: Completed')
        return dom


    def copyCustomChannel(self, channelNum, src):
        self.log('copyCustomChannel: Started')
        self.log('copyCustomChannel: channelNum=' + str(channelNum))
        self.log('copyCustomChannel: src=' + str(src))
        # get path to write to
        dir = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets/')
        self.log('copyCustomChannel: dir=' + str(dir))
           
        # check if mixed playlist, if so we need to copy playlists in mixed playlist first.
        dom = self.getPlaylist(src)
        pltype = self.getSmartPlaylistType(dom)

        if pltype == 'mixed':
            self.log('copyCustomChannel: Copying mixed playlist')
            self.copyMixedPlaylist(src, channelNum)
        else:
            # Copy over main playlist
            dst = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets/Channel_' + str(channelNum) + '.xsp')
            self.log('copyCustomChannel: dst=' + str(dst))
            self.copyPlaylist(src, dst)
        self.log('copyCustomChannel: Completed')


    # This function iterates through the mixed playlist
    # It copies the root mixed playlist as the channel_x.xsp
    # It also iterates through the playlist and calls copyMixedSubPlaylist to copy the other playlists referenced by the parent.
    def copyMixedPlaylist(self, src, channelNum):
        self.log('copyMixedPlaylist: Started')
        self.log('copyMixedPlaylist: channelNum=' + str(channelNum))
        self.log('copyMixedPlaylist: src=' + str(src))
        # check if mixed playlist, if so we need to copy playlists in mixed playlist first.
        dom = self.getPlaylist(src)
        pltype = self.getSmartPlaylistType(dom)
        self.log('copyMixedPlaylist: pltype=' + str(pltype))
        try:
            rulesNode = dom.getElementsByTagName("rule")
        except:
            self.log("Unable to parse the playlist.", xbmc.LOGERROR)
            return ''
        for rule in rulesNode:
            i = 0
            criteria = rule.childNodes[i].nodeValue
            self.log('copyMixedPlaylist: criteria=' + str(criteria))
            # locate source file
            if os.path.exists(os.path.join(xbmc.translatePath('special://profile/playlists/video'), criteria)):
                src1 = os.path.join(xbmc.translatePath('special://profile/playlists/video'), criteria)
                self.log('copyMixedPlaylist: src1=' + str(src1))
            elif os.path.exists(os.path.join(xbmc.translatePath('special://profile/playlists/mixed'), criteria)):
                src1 = os.path.join(xbmc.translatePath('special://profile/playlists/mixed'), criteria)
                self.log('copyMixedPlaylist: src1=' + str(src1))
            else:
                src1 = ""
                self.log("Problem finding source file: " + os.path.join(xbmc.translatePath('special://profile/playlists/video'), criteria))

            dom1 = self.getPlaylist(src1)
            pltype1 = self.getSmartPlaylistType(dom1)
            self.log('copyMixedPlaylist: pltype1=' + str(pltype1))
            if pltype1 == 'movies' or pltype1 == 'episodes' or pltype1 == 'tvshows':
                self.log("copyMixedPlaylist: Movie, Episode or TVShow Playlist")
                # copy playlist over
                self.log('copyMixedPlaylist: src1=' + str(src1))
                self.log("copyMixedPlaylist: User Video Playlist Dir: " + xbmc.translatePath('special://profile/playlists/video'))
                self.log("copyMixedPlaylist: User Mixed Playlist Dir: " + xbmc.translatePath('special://profile/playlists/mixed'))
                fle = os.path.basename(src1)
                self.log("copyMixedPlaylist: Playlist Filename After: " + fle)
                dst1 = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets'), fle)                    
                self.log("copyMixedPlaylist: Copying Playlist")
                self.log("copyMixedPlaylist: src1:" + src1)
                self.log("copyMixedPlaylist: dst1:" + dst1)
                self.copyPlaylist(src1, dst1)                
            elif pltype1 == 'mixed':
                self.log("copyMixedPlaylist: Mixed Playlist")
                self.log("copyMixedPlaylist: src1:" + src1)
                if os.path.exists(src1):
                    self.copyMixedPlaylist(src1, "")
                else:
                    self.log("copyMixedPlaylist: Problem finding source file: " + src1)
            
            i = i + 1

        self.log("copyMixedPlaylist: src:" + src)
        if os.path.exists(src):
            self.log("copyMixedPlaylist: Source Found")
            if channelNum <> "":
                fle = "Channel_" + str(channelNum) + ".xsp"
                self.log("copyMixedPlaylist: fle:" + fle)
            else:
                fle = os.path.basename(src)
                self.log("copyMixedPlaylist: fle:" + fle)
                
            dst = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets'), fle)                    
            self.log("copyMixedPlaylist: dst:" + dst)

            try:
                self.log("copyMixedPlaylist: Copying Playlist")
                self.copyPlaylist(src, dst)
            except:
                self.log("copyMixedPlaylist: Unable to copy playlist.", xbmc.LOGERROR)
                pass
        self.log("copyMixedPlaylist: Completed")
        

    def copyPlaylist(self, src, dst):
        self.log("copyPlaylist: Started")
        self.log("copyPlaylist: src=" + src)
        self.log("copyPlaylist: dst=" + dst)
        buffer_size = 1024 * 1024
        if not hasattr(src, 'read'):
            src = open(src, 'rb')
        if not hasattr(dst, 'write'):
            dst = open(dst, 'wb')
        while 1:
            copy_buffer = src.read(buffer_size)
            if copy_buffer:
                dst.write(copy_buffer)
            else:
                break
        src.close()
        dst.close()
        self.log("copyPlaylist: Completed")


    def getSmartPlaylistType(self, dom):
        self.log("getSmartPlaylistType: Started")
        try:
            pltype = dom.getElementsByTagName('smartplaylist')
            self.log("getSmartPlaylistType: pltype=" + str(pltype))
            return pltype[0].attributes['type'].value
        except:
            self.log("getSmartPlaylistType: Unable to get the playlist type.", xbmc.LOGERROR)
            return ''
        self.log("getSmartPlaylistType: Completed")


    def deletePresetChannels(self):
        self.log("deletePresetChannels: Started")
        dir = xbmc.translatePath('special://profile/addon_data/' + ADDON_ID + '/presets/')       
        self.log("deletePresetChannels: dir=" + str(dir))

        for filename in os.listdir(dir):
            fle = os.path.join(dir, filename)
            self.log('deletePresetChannels: deleting file: ' + fle)
            try:
                if os.path.isfile(fle):
                    os.unlink(fle)
            except Exception, e:
                self.log(e)
        self.log("deletePresetChannels: Completed")
                        

    def fillCustomChannels(self):
        self.log("fillCustomChannels: Started")
        self.log("fillCustomChannels: Looking for custom channels in " + str(xbmc.translatePath('special://profile/playlists/video')))
        # read video playlist folder for Channel_x.xsd files
        if os.path.exists(xbmc.translatePath('special://profile/playlists/video')):
            self.log("fillCustomChannels: folder exists")
            path = xbmc.translatePath('special://profile/playlists/video')
            self.log("fillCustomChannels: path=" + str(path))
            for infile in glob.glob( os.path.join(path, 'Channel_*.xsp') ):
                self.log("fillCustomChannels: found channel file " + str(infile))
                # let's parse out the channel number
                bn = []
                bn_parts = []
                bn = infile.split(".")
                bn_parts = bn[0].split("_")                
                channelNum = bn_parts[1]
                src = os.path.join(path, infile)
                self.log("fillCustomChannels: Adding custom channel " + str(channelNum) )
                self.log("fillCustomChannels: Custom channel playlist: " + src )
                ADDON_SETTINGS.setSetting('custom' + channelNum + 'on', 'true')
                ADDON_SETTINGS.setSetting('custom' + channelNum, src)
        
        # read mixed playlist folder for Channel_x.xsd files
        self.log("fillCustomChannels: Looking for custom channels in " + str(xbmc.translatePath('special://profile/playlists/mixed')))
        if os.path.exists(xbmc.translatePath('special://profile/playlists/mixed')):
            self.log("fillCustomChannels: folder exists")
            path = xbmc.translatePath('special://profile/playlists/mixed')
            for infile in glob.glob( os.path.join(path, 'Channel_*.xsp') ):
                self.log("fillCustomChannels: found channel file " + str(infile))
                # let's parse out the channel number
                bn = []
                bn_parts = []
                bn = infile.split(".")
                bn_parts = bn[0].split("_")                
                channelNum = bn_parts[1]
                src = os.path.join(path, infile)
                self.log("fillCustomChannels: Adding custom channel " + str(channelNum) )
                self.log("fillCustomChannels: Custom channel playlist: " + src )
                ADDON_SETTINGS.setSetting('custom' + channelNum + 'on', 'true')
                ADDON_SETTINGS.setSetting('custom' + channelNum, src)
        self.log("fillCustomChannels: Completed")


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('PresetChannel: ' + msg, level)


    def readPresetChannelConfig(self):
        self.log("readPresetChannelConfig: Started")
        group1 = str(ADDON_SETTINGS.getSetting('group1'))
        group2 = str(ADDON_SETTINGS.getSetting('group2'))
        group3 = str(ADDON_SETTINGS.getSetting('group3'))
        group4 = str(ADDON_SETTINGS.getSetting('group4'))
        group5 = str(ADDON_SETTINGS.getSetting('group5'))
        group6 = str(ADDON_SETTINGS.getSetting('group6'))
        group7 = str(ADDON_SETTINGS.getSetting('group7'))
        group8 = str(ADDON_SETTINGS.getSetting('group8'))
        group9 = str(ADDON_SETTINGS.getSetting('group9'))
        group10 = str(ADDON_SETTINGS.getSetting('group10'))
        group11 = str(ADDON_SETTINGS.getSetting('group11'))
        group12 = str(ADDON_SETTINGS.getSetting('group12'))
        group13 = str(ADDON_SETTINGS.getSetting('group13'))
        group14 = str(ADDON_SETTINGS.getSetting('group14'))
        # 0 = TV Genres
        # 1 = TV Networks
        # 2 = TV Rating
        # 3 = TV Decades
        # 4 = TV Shows
        # 5 = Movie Genres
        # 6 = Movie Studios
        # 7 = Movie Rating
        # 8 = Movie Decades
        # 9 = Mixed Genres
        # 10 = Mixed Rating
        # 11 = Mixed Decades
        # 12 = Mixed TV Shows
        # 13 = Custom
        # Group 1
        if group1 == "0":
            self.log('Group 1: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group1 == "1":
            self.log('Group 1: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group1 == "2":
            self.log('Group 1: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group1 == "3":
            self.log('Group 1: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group1 == "4":
            self.log('Group 1: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group1 == "5":
            self.log('Group 1: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group1 == "6":
            self.log('Group 1: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group1 == "7":
            self.log('Group 1: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group1 == "8":
            self.log('Group 1: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group1 == "9":
            self.log('Group 1: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 1: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group1 == "11":
            self.log('Group 1: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group1 == "12":
            self.log('Group 1: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group1 == "13":
            self.log('Group 1: Custom')
            self.readCustomPresetChannelConfig()
        # Group 2
        if group2 == "0":
            self.log('Group 2: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group2 == "1":
            self.log('Group 2: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group2 == "2":
            self.log('Group 2: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group2 == "3":
            self.log('Group 2: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group2 == "4":
            self.log('Group 2: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group2 == "5":
            self.log('Group 2: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group2 == "6":
            self.log('Group 2: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group2 == "7":
            self.log('Group 2: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group2 == "8":
            self.log('Group 2: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group2 == "9":
            self.log('Group 2: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 2: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group2 == "11":
            self.log('Group 2: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group2 == "12":
            self.log('Group 2: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group2 == "13":
            self.log('Group 2: Custom')
            self.readCustomPresetChannelConfig()
        # Group 3
        if group3 == "0":
            self.log('Group 3: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group3 == "1":
            self.log('Group 3: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group3 == "2":
            self.log('Group 3: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group3 == "3":
            self.log('Group 3: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group3 == "4":
            self.log('Group 3: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group3 == "5":
            self.log('Group 3: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group3 == "6":
            self.log('Group 3: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group3 == "7":
            self.log('Group 3: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group3 == "8":
            self.log('Group 3: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group3 == "9":
            self.log('Group 3: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 3: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group3 == "11":
            self.log('Group 3: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group3 == "12":
            self.log('Group 3: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group3 == "13":
            self.log('Group 3: Custom')
            self.readCustomPresetChannelConfig()
        # Group 4
        if group4 == "0":
            self.log('Group 4: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group4 == "1":
            self.log('Group 4: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group4 == "2":
            self.log('Group 4: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group4 == "3":
            self.log('Group 4: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group4 == "4":
            self.log('Group 4: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group4 == "5":
            self.log('Group 4: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group4 == "6":
            self.log('Group 4: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group4 == "7":
            self.log('Group 4: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group4 == "8":
            self.log('Group 4: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group4 == "9":
            self.log('Group 4: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 4: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group4 == "11":
            self.log('Group 4: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group4 == "12":
            self.log('Group 4: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group4 == "13":
            self.log('Group 4: Custom')
            self.readCustomPresetChannelConfig()
        # Group 5
        if group5 == "0":
            self.log('Group 5: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group5 == "1":
            self.log('Group 5: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group5 == "2":
            self.log('Group 5: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group5 == "3":
            self.log('Group 5: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group5 == "4":
            self.log('Group 5: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group5 == "5":
            self.log('Group 5: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group5 == "6":
            self.log('Group 5: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group5 == "7":
            self.log('Group 5: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group5 == "8":
            self.log('Group 5: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group5 == "9":
            self.log('Group 5: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 5: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group5 == "11":
            self.log('Group 5: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group5 == "12":
            self.log('Group 5: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group5 == "13":
            self.log('Group 5: Custom')
            self.readCustomPresetChannelConfig()
        # Group 6
        if group6 == "0":
            self.log('Group 6: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group6 == "1":
            self.log('Group 6: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group6 == "2":
            self.log('Group 6: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group6 == "3":
            self.log('Group 6: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group6 == "4":
            self.log('Group 6: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group6 == "5":
            self.log('Group 6: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group6 == "6":
            self.log('Group 6: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group6 == "7":
            self.log('Group 6: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group6 == "8":
            self.log('Group 6: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group6 == "9":
            self.log('Group 6: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 6: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group6 == "11":
            self.log('Group 6: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group6 == "12":
            self.log('Group 6: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group6 == "13":
            self.log('Group 6: Custom')
            self.readCustomPresetChannelConfig()
        # Group 7
        if group7 == "0":
            self.log('Group 7: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group7 == "1":
            self.log('Group 7: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group7 == "2":
            self.log('Group 7: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group7 == "3":
            self.log('Group 7: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group7 == "4":
            self.log('Group 7: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group7 == "5":
            self.log('Group 7: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group7 == "6":
            self.log('Group 7: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group7 == "7":
            self.log('Group 7: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group7 == "8":
            self.log('Group 7: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group7 == "9":
            self.log('Group 7: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 7: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group7 == "11":
            self.log('Group 7: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group7 == "12":
            self.log('Group 7: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group7 == "13":
            self.log('Group 7: Custom')
            self.readCustomPresetChannelConfig()
        # Group 8
        if group8 == "0":
            self.log('Group 8: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group8 == "1":
            self.log('Group 8: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group8 == "2":
            self.log('Group 8: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group8 == "3":
            self.log('Group 8: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group8 == "4":
            self.log('Group 8: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group8 == "5":
            self.log('Group 8: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group8 == "6":
            self.log('Group 8: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group8 == "7":
            self.log('Group 8: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group8 == "8":
            self.log('Group 8: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group8 == "9":
            self.log('Group 8: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 8: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group8 == "11":
            self.log('Group 8: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group8 == "12":
            self.log('Group 8: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group8 == "13":
            self.log('Group 8: Custom')
            self.readCustomPresetChannelConfig()
        # Group 9
        if group9 == "0":
            self.log('Group 9: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group9 == "1":
            self.log('Group 9: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group9 == "2":
            self.log('Group 9: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group9 == "3":
            self.log('Group 9: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group9 == "4":
            self.log('Group 9: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group9 == "5":
            self.log('Group 9: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group9 == "6":
            self.log('Group 9: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group9 == "7":
            self.log('Group 9: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group9 == "8":
            self.log('Group 9: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group9 == "9":
            self.log('Group 9: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 9: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group9 == "11":
            self.log('Group 9: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group9 == "12":
            self.log('Group 9: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group9 == "13":
            self.log('Group 9: Custom')
            self.readCustomPresetChannelConfig()
        # Group 10
        if group10 == "0":
            self.log('Group 10: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group10 == "1":
            self.log('Group 10: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group10 == "2":
            self.log('Group 10: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group10 == "3":
            self.log('Group 10: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group10 == "4":
            self.log('Group 10: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group10 == "5":
            self.log('Group 10: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group10 == "6":
            self.log('Group 10: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group10 == "7":
            self.log('Group 10: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group10 == "8":
            self.log('Group 10: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group10 == "9":
            self.log('Group 10: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 10: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group10 == "11":
            self.log('Group 10: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group10 == "12":
            self.log('Group 10: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group10 == "13":
            self.log('Group 10: Custom')
            self.readCustomPresetChannelConfig()
        # Group 11
        if group11 == "0":
            self.log('Group 11: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group11 == "1":
            self.log('Group 11: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group11 == "2":
            self.log('Group 11: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group11 == "3":
            self.log('Group 11: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group11 == "4":
            self.log('Group 11: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group11 == "5":
            self.log('Group 11: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group11 == "6":
            self.log('Group 11: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group11 == "7":
            self.log('Group 11: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group11 == "8":
            self.log('Group 11: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group11 == "9":
            self.log('Group 11: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 11: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group11 == "11":
            self.log('Group 11: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group11 == "12":
            self.log('Group 11: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group11 == "13":
            self.log('Group 11: Custom')
            self.readCustomPresetChannelConfig()
        # Group 12
        if group12 == "0":
            self.log('Group 12: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group12 == "1":
            self.log('Group 12: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group12 == "2":
            self.log('Group 12: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group12 == "3":
            self.log('Group 12: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group12 == "4":
            self.log('Group 12: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group12 == "5":
            self.log('Group 12: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group12 == "6":
            self.log('Group 12: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group12 == "7":
            self.log('Group 12: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group12 == "8":
            self.log('Group 12: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group12 == "9":
            self.log('Group 12: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 12: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group12 == "11":
            self.log('Group 12: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group12 == "12":
            self.log('Group 12: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group12 == "13":
            self.log('Group 12: Custom')
            self.readCustomPresetChannelConfig()
        # Group 13
        if group13 == "0":
            self.log('Group 13: TV Genre')
            self.readTVGenrePresetChannelConfig()
        if group13 == "1":
            self.log('Group 13: TV Networks')
            self.readTVNetworkPresetChannelConfig()
        if group13 == "2":
            self.log('Group 13: TV Rating')
            self.readTVRatingPresetChannelConfig()
        if group13 == "3":
            self.log('Group 13: TV Decades')
            self.readTVDecadePresetChannelConfig()
        if group13 == "4":
            self.log('Group 13: TV Shows')
            self.readTVShowPresetChannelConfig()
        if group13 == "5":
            self.log('Group 13: Movie Genres')
            self.readMovieGenrePresetChannelConfig()
        if group13 == "6":
            self.log('Group 13: Movie Studios')
            self.readMovieStudioPresetChannelConfig()
        if group13 == "7":
            self.log('Group 13: Movie Rating')
            self.readMovieRatingPresetChannelConfig()
        if group13 == "8":
            self.log('Group 13: Movie Decades')
            self.readMovieDecadePresetChannelConfig()
        if group13 == "9":
            self.log('Group 13: Mixed Genres')
            self.readMixedGenrePresetChannelConfig()
        if group1 == "10":
            self.log('Group 13: Mixed Ratings')
            self.readMixedRatingPresetChannelConfig()
        if group13 == "11":
            self.log('Group 13: Mixed Decades')
            self.readMixedDecadePresetChannelConfig()
        if group13 == "12":
            self.log('Group 13: Mixed TV Shows')
            self.readMixedTVShowPresetChannelConfig()
        if group13 == "13":
            self.log('Group 13: Custom')
            self.readCustomPresetChannelConfig()
        self.log("readPresetChannelConfig: Completed")



########################################################################
########################################################################
#
#  CHANNEL CONFIGURATION
#
########################################################################
########################################################################

######################################################
##
##  TV GENRE
##
######################################################

    def readTVGenrePresetChannelConfig(self):
        self.log('Getting TV Genre Presets Settings')
        # TV Genre Presets
        # Shared Settings
        type = 'episodes'
        limit = ADDON_SETTINGS.getSetting('limit1')
        random = ADDON_SETTINGS.getSetting('random1')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched1')
        nospecials = ADDON_SETTINGS.getSetting('nospecials1')
        resolution = ''
        if ADDON_SETTINGS.getSetting('action-and-adventure-tv') == "true":
            name = ADDON_SETTINGS.getSetting('action-and-adventure-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'action and adventure'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('animation-tv') == "true":
            name = ADDON_SETTINGS.getSetting('animation-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'animation'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('children-tv') == "true":
            name = ADDON_SETTINGS.getSetting('children-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'children'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('comedy-tv') == "true":
            name = ADDON_SETTINGS.getSetting('comedy-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'comedy'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('documentary-tv') == "true":
            name = ADDON_SETTINGS.getSetting('documentary-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'documentary'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('drama-tv') == "true":
            name = ADDON_SETTINGS.getSetting('drama-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'drama'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('fantasy-tv') == "true":
            name = ADDON_SETTINGS.getSetting('fantasy-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'fantasy'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mini-series-tv') == "true":
            name = ADDON_SETTINGS.getSetting('mini-series-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'mini-series'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('reality-tv') == "true":
            name = ADDON_SETTINGS.getSetting('reality-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'reality'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('science-fiction-tv') == "true":
            name = ADDON_SETTINGS.getSetting('science-fiction-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'science-fiction'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('special-interest-tv') == "true":
            name = ADDON_SETTINGS.getSetting('special-interest-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'special interest'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('sport-tv') == "true":
            name = ADDON_SETTINGS.getSetting('sport-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'sport'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('western-tv') == "true":
            name = ADDON_SETTINGS.getSetting('western-tv-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'western'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVGenre1on')=="true":
            if ADDON_SETTINGS.getSetting('customTVGenre1') <> "":
                self.presetChannels.append(presetChannel('Custom TV Genre 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVGenre1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVGenre2on')=="true":
            if ADDON_SETTINGS.getSetting('customTVGenre2') <> "":
                self.presetChannels.append(presetChannel('Custom TV Genre 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVGenre2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVGenre3on')=="true":
            if ADDON_SETTINGS.getSetting('customTVGenre3') <> "":
                self.presetChannels.append(presetChannel('Custom TV Genre 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVGenre3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVGenre4on')=="true":
            if ADDON_SETTINGS.getSetting('customTVGenre4') <> "":
                self.presetChannels.append(presetChannel('Custom TV Genre 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVGenre4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVGenre5on')=="true":
            if ADDON_SETTINGS.getSetting('customTVGenre5') <> "":
                self.presetChannels.append(presetChannel('Custom TV Genre 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVGenre5"), '', '', '', '', '', '', '', ''))


######################################################
##
##  TV DECADES
##
######################################################

    def readTVDecadePresetChannelConfig(self):
        self.log('Getting TV Decade Presets Settings')
        # TV Decade Presets
        # Shared Settings
        type = 'episodes'
        limit = ADDON_SETTINGS.getSetting('limit1')
        random = ADDON_SETTINGS.getSetting('random1')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched1')
        nospecials = ADDON_SETTINGS.getSetting('nospecials1')
        resolution = ''
        if ADDON_SETTINGS.getSetting('1950s-tv') == "true":
            name = ADDON_SETTINGS.getSetting('1950s-tv-name')
            rule1 = 'airdate'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1949-12-31'
            operator2 = 'before'
            criteria2 = '1960-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('1960s-tv') == "true":
            name = ADDON_SETTINGS.getSetting('1960s-tv-name')
            rule1 = 'airdate'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1959-12-31'
            operator2 = 'before'
            criteria2 = '1970-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('1970s-tv') == "true":
            name = ADDON_SETTINGS.getSetting('1970s-tv-name')
            rule1 = 'airdate'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1969-12-31'
            operator2 = 'before'
            criteria2 = '1980-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('1980s-tv') == "true":
            name = ADDON_SETTINGS.getSetting('1980s-tv-name')
            rule1 = 'airdate'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1979-12-31'
            operator2 = 'before'
            criteria2 = '1990-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('1990s-tv') == "true":
            name = ADDON_SETTINGS.getSetting('1990s-tv-name')
            rule1 = 'airdate'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1989-12-31'
            operator2 = 'before'
            criteria2 = '2000-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('2000s-tv') == "true":
            name = ADDON_SETTINGS.getSetting('2000s-tv-name')
            rule1 = 'airdate'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1999-12-31'
            operator2 = 'before'
            criteria2 = '2010-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('2010s-tv') == "true":
            name = ADDON_SETTINGS.getSetting('2010s-tv-name')
            rule1 = 'airdate'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '2009-12-31'
            operator2 = 'before'
            criteria2 = '2020-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVDecade1on')=="true":
            if ADDON_SETTINGS.getSetting('customTVDecade1') <> "":
                self.presetChannels.append(presetChannel('Custom TV Decade 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVDecade1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVDecade2on')=="true":
            if ADDON_SETTINGS.getSetting('customTVDecade2') <> "":
                self.presetChannels.append(presetChannel('Custom TV Decade 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVDecade2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVDecade3on')=="true":
            if ADDON_SETTINGS.getSetting('customTVDecade3') <> "":
                self.presetChannels.append(presetChannel('Custom TV Decade 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVDecade3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVDecade4on')=="true":
            if ADDON_SETTINGS.getSetting('customTVDecade4') <> "":
                self.presetChannels.append(presetChannel('Custom TV Decade 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVDecade4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVDecade5on')=="true":
            if ADDON_SETTINGS.getSetting('customTVDecade5') <> "":
                self.presetChannels.append(presetChannel('Custom TV Decade 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVDecade5"), '', '', '', '', '', '', '', ''))


######################################################
##
##  TV RATINGS
##
######################################################

    def readTVRatingPresetChannelConfig(self):
        self.log('Getting TV Decade Presets Settings')
        # TV Decade Presets
        # Shared Settings
        type = 'episodes'
        limit = ADDON_SETTINGS.getSetting('limit1')
        random = ADDON_SETTINGS.getSetting('random1')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched1')
        nospecials = ADDON_SETTINGS.getSetting('nospecials1')
        resolution = ''
#        if ADDON_SETTINGS.getSetting('child-tv') == "true":
#            name = ADDON_SETTINGS.getSetting('child-tv-name')
#            rule1 = 'mpaa'
#            rule2 = ''
#            operator1 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("TV-Y")
#            criterias.append("TV-G")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria1 = criterialist
#            operator2 = ''
#            criteria2 = ''
#            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
#        if ADDON_SETTINGS.getSetting('preteen-tv') == "true":
#            name = ADDON_SETTINGS.getSetting('preteen-tv-name')
#            rule1 = 'mpaa'
#            rule2 = ''
#            operator1 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("TV-Y7")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria1 = criterialist
#            operator2 = ''
#            criteria2 = ''
#            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
#        if ADDON_SETTINGS.getSetting('teen-tv') == "true":
#            name = ADDON_SETTINGS.getSetting('teen-tv-name')
#            rule1 = 'mpaa'
#            rule2 = ''
#            operator1 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("TV-PG")
#            criterias.append("TV-14")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria1 = criterialist
#            operator2 = ''
#            criteria2 = ''
#            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
#        if ADDON_SETTINGS.getSetting('adult-tv') == "true":
#            name = ADDON_SETTINGS.getSetting('adult-tv-name')
#            rule1 = 'mpaa'
#            rule2 = ''
#            operator1 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("TV-14")
#            criterias.append("TV-MA")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria1 = criterialist
#            operator2 = ''
#            criteria2 = ''
#            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))


######################################################
##
##  TV SHOWS
##
######################################################

    def readTVShowPresetChannelConfig(self):
        # TV Show Presets
        self.log('Getting TV Show Presets ')
        # Shared Settings
        type = 'episodes'
        limit = ADDON_SETTINGS.getSetting('limit4')
        random = ADDON_SETTINGS.getSetting('random4')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched4')
        nospecials = ADDON_SETTINGS.getSetting('nospecials4')
        resolution = ''                
        #
        # [0-9]
        #
        if ADDON_SETTINGS.getSetting('24-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('24-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("24")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('90210-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('90210-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("90210")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('customTVShow1on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow1') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow2on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow2') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow3on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow3') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow4on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow4') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow5on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow5') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow5"), '', '', '', '', '', '', '', ''))
        #
        # [A-B]
        #
        if ADDON_SETTINGS.getSetting('the-abbot-and-costello-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-abbot-and-costello-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Abbot and Costello Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('alfred-hitchcock-presents-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('alfred-hitchcock-presents-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Alfred Hitchcock Presents")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('all-in-the-family-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('all-in-the-family-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("All in the Family")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('american-idol-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('american-idol-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("American Idol")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('americas-next-top-model-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('americas-next-top-model-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("America's Next Top Model")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('an-american-family-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('an-american-family-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("An American Family")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('army-wives-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('army-wives-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Army Wives")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('arrested-development-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('arrested-development-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Arrested Development")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('bad-girls-club-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('bad-girls-club-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Bad Girls Club")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('battlestar-galactica-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('battlestar-galactica-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Battlestar Galactica (2003)")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-beavis-and-butt-head-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-beavis-and-butt-head-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Beavis and Butt-Head Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-big-bang-theory-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-big-bang-theory-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Big Bang Theory")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('big-love-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('big-love-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Big Love")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('blue-bloods-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('blue-bloods-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Blue Bloods")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-bob-newhart-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-bob-newhart-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Bob Newhart Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('bones-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('bones-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Bones")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('breaking-bad-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('breaking-bad-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Breaking Bad")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('breakout-kings-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('breakout-kings-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Breakout Kings")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('brideshead-revisited-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('brideshead-revisited-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Brideshead Revisited")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('brothers-and-sisters-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('brothers-and-sisters-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Brothers and Sisters")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('buffalo-bill-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('buffalo-bill-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Buffalo Bill")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('buffy-the-vampire-slayer-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('buffy-the-vampire-slayer-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Buffy the Vampire Slayer")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('burn-notice-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('burn-notice-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Burn Notice")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow6on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow6') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 6','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow6"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow7on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow7') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 7','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow7"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow8on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow8') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 8','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow8"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow9on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow9') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 9','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow9"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow10on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow10') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 10','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow10"), '', '', '', '', '', '', '', ''))
        #
        # [C-D]
        #
        if ADDON_SETTINGS.getSetting('californication-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('californication-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Californication")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('caprica-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('caprica-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Caprica")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-carol-burnett-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-carol-burnett-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Carol Burnett Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('castle-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('castle-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Castle")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('charmed-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('charmed-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Charmed")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('cheers-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('cheers-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Cheers")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('chuck-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('chuck-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Chuck")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('criminal-minds-all-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('criminal-minds-all-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Criminal Minds")
            criterias.append("Criminal Minds: Suspect Behavior")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('criminal-minds-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('criminal-minds-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Criminal Minds")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('criminal-minds-suspect-behavior-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('criminal-minds-suspect-behavior-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Criminal Minds: Suspect Behavior")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('csi-all-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('csi-all-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("CSI: Crime Scene Investigation")
            criterias.append("CSI: Miami")
            criterias.append("CSI: Las Vegas")
            criterias.append("CSI: New York")
            criterias.append("CSI: NY")
            criterias.append("CSI")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('csi-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('csi-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("CSI: Crime Scene Investigation")
            criterias.append("CSI")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('csi-miami-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('csi-miami-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("CSI: Miami")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('csi-ny-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('csi-ny-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("CSI: New York")
            criterias.append("CSI: NY")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('dallas-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('dallas-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Dallas")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('deadwood-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('deadwood-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Deadwood")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('desperate-housewives-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('desperate-housewives-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Desperate Housewives")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('detroit-1-8-7-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('detroit-1-8-7-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Detroit 1-8-7")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('dexter-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('dexter-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Dexter")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-dick-van-dyke-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-dick-van-dyke-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Dick Van Dyke Show")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('doctor-who-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('doctor-who-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Doctor Who (2005)")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('dragnet-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('dragnet-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Dragnet")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow11on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow11') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 11','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow11"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow12on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow12') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 12','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow12"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow13on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow13') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 13','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow13"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow14on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow14') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 14','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow14"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow15on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow15') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 15','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow15"), '', '', '', '', '', '', '', ''))

        #
        # [E-F]
        #
        if ADDON_SETTINGS.getSetting('the-ed-sullivan-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-ed-sullivan-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Ed Sullivan Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('endgame-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('endgame-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Endgame")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-ernie-kovacs-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-ernie-kovacs-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Ernie Kovacs Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('eureka-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('eureka-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Eureka")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('family-guy-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('family-guy-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Family Guy")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('felicity-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('felicity-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Felicity")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('freaks-and-geeks-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('freaks-and-geeks-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Freaks and Geeks")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-french-chef-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-french-chef-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The French Chef")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('friends-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('friends-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Friends")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('fringe-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('fringe-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Fringe")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow16on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow16') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 16','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow16"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow17on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow17') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 17','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow17"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow18on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow18') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 18','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow18"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow19on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow19') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 19','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow19"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow20on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow20') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 20','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow20"), '', '', '', '', '', '', '', ''))
        #
        # [G-H]
        #
        if ADDON_SETTINGS.getSetting('gilmore-girls-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('gilmore-girls-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Gilmore Girls")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('glee-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('glee-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Glee")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-good-wife-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-good-wife-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Good Wife")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('gossip-girl-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('gossip-girl-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Gossip Girl")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('greek-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('greek-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Greek")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('greys-anatomy-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('greys-anatomy-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Grey's Anatomy")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('gunsmoke-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('gunsmoke-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Gunsmoke")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('harrys-law-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('harrys-law-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Harry's Law")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('hawaii-five-o-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('hawaii-five-o-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Hawaii Five-O (2010)")
            criterias.append("Hawaii Five-0 (2010)")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('hellcats-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('hellcats-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Hellcats")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('heroes-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('heroes-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Heroes")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('hill-street-blues-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('hill-street-blues-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Hill Street Blues")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('homicide-life-on-the-street-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('homicide-life-on-the-street-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Homicide: Life on the Street")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('house-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('house-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("House")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('how-i-met-your-mother-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('how-i-met-your-mother-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("How I Met Your Mother")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('human-target-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('human-target-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Human Target")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow21on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow21') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 21','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow21"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow22on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow22') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 22','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow22"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow23on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow23') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 23','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow23"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow24on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow24') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 24','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow24"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow25on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow25') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 25','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow25"), '', '', '', '', '', '', '', ''))
        #
        # [I-J]
        #
        if ADDON_SETTINGS.getSetting('i-claudius-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('i-claudius-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("I, Claudius")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('i-love-lucy-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('i-love-lucy-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("I Love Lucy")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('jersey-shore-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('jersey-shore-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Jersey Shore")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('justified-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('justified-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Justified")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow26on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow26') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 26','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow26"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow27on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow27') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 27','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow27"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow28on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow28') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 28','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow28"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow29on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow29') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 29','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow29"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow30on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow30') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 30','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow30"), '', '', '', '', '', '', '', ''))
        #
        # [K-L]
        #
        if ADDON_SETTINGS.getSetting('king-of-the-hill-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('king-of-the-hill-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("King of the Hill")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-larry-sanders-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-larry-sanders-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Larry Sanders Show")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('las-vegas-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('las-vegas-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Las Vegas")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('law-and-order-all-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('law-and-order-all-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Law and Order")
            criterias.append("Law and Order Los Angeles")
            criterias.append("Law and Order: Special Victims Unit")
            criterias.append("Law and Order: SVU")
            criterias.append("Law and Order: UK")
            criterias.append("Law and Order UK")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('law-and-order-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('law-and-order-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Law and Order")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('law-and-order-la-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('law-and-order-la-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Law and Order Los Angeles")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('law-and-order-svu-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('law-and-order-svu-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Law and Order: Special Victims Unit")
            criterias.append("Law and Order: SVU")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('law-and-order-uk-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('law-and-order-uk-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Law and Order: UK")
            criterias.append("Law and Order UK")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('leave-it-to-beaver-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('leave-it-to-beaver-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Leave It To Beaver")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('lie-to-me-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('lie-to-me-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Lie to Me")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('lost-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('lost-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Lost")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow31on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow31') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 31','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow31"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow32on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow32') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 32','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow32"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow33on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow33') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 33','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow33"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow34on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow34') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 34','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow34"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow35on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow35') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 35','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow35"), '', '', '', '', '', '', '', ''))
        #
        # [M-N]
        #
        if ADDON_SETTINGS.getSetting('mad-love-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('mad-love-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Mad Love")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('make-it-or-break-it-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('make-it-or-break-it-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Make It or Break It")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('married-with-children-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('married-with-children-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Married ... with Children")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mary-hartman-mary-hartman-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('mary-hartman-mary-hartman-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Mary Hartman, Mary Hartman")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-mary-tyler-moore-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-mary-tyler-moore-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Mary Tyler Moore Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mash-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('mash-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("M*A*S*H")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('merlin-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('merlin-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Merlin")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('modern-family-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('modern-family-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Modern Family")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('monty-pythons-flying-circus-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('monty-pythons-flying-circus-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Monty Python's Flying Circus")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('moonlighting-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('moonlighting-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Moonlighting")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mr-sunshine-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('mr-sunshine-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Mr. Sunshine")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('my-so-called-life-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('my-so-called-life-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("My So Called Life")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mystery-science-theater-3000-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('mystery-science-theater-3000-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Mystery Science Theater 3000")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('ncis-all-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('ncis-all-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("NCIS")            
            criterias.append("NCIS: Los Angeles")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('ncis-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('ncis-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("NCIS")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('ncis-la-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('ncis-la-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("NCIS: Los Angeles")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('nikita-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('nikita-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Nikita")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('no-ordinary-family-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('no-ordinary-family-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("No Ordinary Family")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow36on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow36') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 36','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow36"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow37on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow37') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 37','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow37"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow38on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow38') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 38','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow38"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow39on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow39') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 39','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow39"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow40on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow40') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 40','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow40"), '', '', '', '', '', '', '', ''))
        #
        # [O-P]
        #
        if ADDON_SETTINGS.getSetting('the-odd-couple-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-odd-couple-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Odd Couple")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('off-the-map-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('off-the-map-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Off the Map")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('one-tree-hill-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('one-tree-hill-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("One Tree Hill")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('outcasts-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('outcasts-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Outcasts")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('parenthood-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('parenthood-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Parenthood")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('pee-wees-playhouse-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('pee-wees-playhouse-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Pee-Wee's Playhouse")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('playhouse-90-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('playhouse-90-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Playhouse 90")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('pretty-little-liars-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('pretty-little-liars-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Pretty Little Liars")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('prime-suspect-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('prime-suspect-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Prime Suspect")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('prison-break-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('prison-break-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Prison Break")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('private-practice-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('private-practice-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Private Practice")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow41on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow41') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 41','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow41"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow42on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow42') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 42','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow42"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow43on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow43') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 43','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow43"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow44on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow44') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 44','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow44"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow45on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow45') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 45','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow45"), '', '', '', '', '', '', '', ''))
        #
        # [Q-R]
        #
        if ADDON_SETTINGS.getSetting('rocky-and-his-friends-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('rocky-and-his-friends-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Rocky and His Friends")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('roseanne-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('roseanne-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Roseanne")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow46on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow46') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 46','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow46"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow47on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow47') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 47','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow47"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow48on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow48') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 48','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow48"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow49on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow49') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 49','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow49"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow50on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow50') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 50','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow50"), '', '', '', '', '', '', '', ''))
        #
        # [S]
        #
        if ADDON_SETTINGS.getSetting('sanctuary-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('sanctuary-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Sanctuary")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('sanford-and-son-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('sanford-and-son-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Sanford and Son")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('saturday-night-live-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('saturday-night-live-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Saturday Night Live")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('scrubs-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('scrubs-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Scrubs")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('secret-diary-of-a-call-girl-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('secreat-diary-of-a-call-girl-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Secret Diary of a Call Girl")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-secret-life-of-the-american-teenager-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-secret-life-of-the-american-teenager-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Secret Life of the American Teenager")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('seinfeld-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('seinfeld-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Seinfeld")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('sex-and-the-city-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('sex-and-the-city-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Sex and the City")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('six-feet-under-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('six-feet-under-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Six Feet Under")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('skins-uk-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('skins-uk-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Skins")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('smallville-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('smallville-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Smallville")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('south-park-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('south-park-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("South Park")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('southland-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('southland-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Southland")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('spartacus-blood-and-sand-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('spartacus-blood-and-sand-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Spartacus: Blood and Sand")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('spartacus-gods-of-the-arena-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('spartacus-gods-of-the-arena-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Spartacus: Gods of the Arena")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('spongebob-squarepants-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('spongebob-squarepants-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("SpongeBob SquarePants")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('stargate-atlantis-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('stargate-atlantis-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Stargate Atlantis")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('stargate-sg1-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('stargate-sg1-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Stargate SG-1")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('stargate-universe-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('stargate-universe-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Stargate Universe")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('star-trek-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('star-trek-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Star Trek")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('star-trek-ds9-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('star-trek-ds9-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Star Trek: Deep Space Nine")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('star-trek-enterprise-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('star-trek-enterprise-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Star Trek: Enterprise")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('star-trek-the-next-generation-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('star-trek-the-next-generation-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Star Trek: The Next Generation")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('star-trek-the-animated-series-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('star-trek-the-animated-series-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Star Trek: The Animated Series")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('star-trek-voyager-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('star-trek-voyager-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Star Trek: Voyager")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('st-elsewhere-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('st-elsewhere-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("St. Elsewhere")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('supernatural-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('supernatural-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Supernatural")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('survivor-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('survivor-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Survivor")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow51on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow51') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 51','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow51"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow52on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow52') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 52','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow52"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow53on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow53') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 53','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow53"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow54on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow54') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 54','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow54"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow55on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow55') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 55','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow55"), '', '', '', '', '', '', '', ''))
        #
        # [T]
        #
        if ADDON_SETTINGS.getSetting('taxi-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('taxi-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Taxi")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-bachelor-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-bachelor-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Bachelor")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-cape-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-cape-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Cape")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-chicago-code-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-chicago-code-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Chicago Code")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-cosby-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-cosby-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Cosby Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-daily-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-daily-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Daily Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-defenders-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-defenders-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Defenders")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-event-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-event-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Event")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-game-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-game-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Game")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-honeymooners-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-honeymooners-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Honeymooners")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-mentalist-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-mentalist-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Mentalist")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-monkeys-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-monkeys-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Monkeys")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-office-uk-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-office-uk-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Office (UK)")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-office-us-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-office-us-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Office (US)")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-prisoner-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-prisoner-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Prisoner")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-real-world-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-real-world-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Real World")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-shield-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-shield-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Shield")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-singing-detective-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-singing-detective-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Singing Detective")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-simpsons-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-simpsons-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Simpsons")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-sopranos-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-sopranos-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Sopranos")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-twilight-show-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-twilight-show-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Twilight Show")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-walking-dead-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-walking-dead-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Walking Dead")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-west-wing-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-west-wing-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The West Wing")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-wire-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-wire-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Wire")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('true-blood-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('true-blood-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("True Blood")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('twin-peaks-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('twin-peaks-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Twin Peaks")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('two-and-a-half-men-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('two-and-a-half-men-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Two and a Half Men")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow56on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow56') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 56','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow56"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow57on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow57') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 57','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow57"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow58on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow58') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 58','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow58"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow59on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow59') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 59','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow59"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow60on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow60') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 60','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow60"), '', '', '', '', '', '', '', ''))
        #
        # [U-Z]
        #
        if ADDON_SETTINGS.getSetting('v-2009-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('v-2009-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("V (2009)")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-vampire-diaries-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-vampire-diaries-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Vampire Diaries")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('white-collar-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('white-collar-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("White Collar")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('wkrp-in-cincinnati-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('wkrp-in-cincinnati-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("WKRP in Cincinnati")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('wiseguy-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('wiseguy-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Wiseguy")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('the-x-files-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('the-x-files-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The X-Files")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('your-show-of-shows-tvshow') == "true":
            name = ADDON_SETTINGS.getSetting('your-show-of-shows-tvshow-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Your Show of Shows")            
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVShow61on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow61') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 61','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow61"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow62on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow62') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 62','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow62"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow63on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow63') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 63','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow63"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow64on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow64') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 64','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow64"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVShow65on')=="true":
            if ADDON_SETTINGS.getSetting('customTVShow65') <> "":
                self.presetChannels.append(presetChannel('Custom TV Show 65','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVShow65"), '', '', '', '', '', '', '', ''))


######################################################
##
##  TV NETWORKS
##
######################################################

    def readTVNetworkPresetChannelConfig(self):
        # TV Network Presets
        self.log('Getting TV Network Presets ')
        # Shared Settings
        type = 'episodes'
        limit = ADDON_SETTINGS.getSetting('limit1')
        random = ADDON_SETTINGS.getSetting('random1')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched1')
        nospecials = ADDON_SETTINGS.getSetting('nospecials1')
        resolution = ''        

        #
        # [A-E]
        #
        if ADDON_SETTINGS.getSetting('ae') == "true":
            name = ADDON_SETTINGS.getSetting('ae-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Beyond Scared Straight")
            criterias.append("Billy the Exterminator")
            criterias.append("Breakout Kings")
            criterias.append("Cradle of Lies")
            criterias.append("Crime 360")
            criterias.append("Criss Angel: Mindfreak")
            criterias.append("Dog the Bounty Hunter")
            criterias.append("Driving Force")
            criterias.append("Gene Simmons Family Jewels")
            criterias.append("Heavy")
            criterias.append("Hoarders")
            criterias.append("Intervention")
            criterias.append("Manhunters: Fugitive Task Force")
            criterias.append("Parking Wars")
            criterias.append("Private Sessions")
            criterias.append("Steve Seagal: Lawman")
            criterias.append("Storage Wars")
            criterias.append("Strange Days with Bob Saget")
            criterias.append("The Cleaner")
            criterias.append("The Glades")
            criterias.append("The Hasselhoffs")
            criterias.append("The People Speak")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('abc') == "true":
            name = ADDON_SETTINGS.getSetting('abc-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            tvnetwork = 'ABC'
            criterialist = ''
            criterias = []
            criterias.append("A Charlie Brown Christmas")
            criterias.append("A Charlie Brown Valentine")
            criterias.append("All My Children")
            criterias.append("America's Funniest Home Videos")
            criterias.append("Bachelor Pad")
            criterias.append("Beauty & the Briefcase")
            criterias.append("Better Off Ted")
            criterias.append("Better With You")
            criterias.append("Body of Proof")
            criterias.append("Boston Med")
            criterias.append("Brothers & Sisters")
            criterias.append("Castle")
            criterias.append("Commander in Chief")
            criterias.append("Cougar Town")
            criterias.append("Dance War: Bruno vs. Carrie Ann")
            criterias.append("Dancing With the Stars")
            criterias.append("Dating in the Dark")
            criterias.append("Day Break")
            criterias.append("Desperate Housewives")
            criterias.append("Detroit 1-8-7")
            criterias.append("Dirty Sexy Money")
            criterias.append("Duel")
            criterias.append("Eastwick")
            criterias.append("Eli Stone")
            criterias.append("Extreme Makeover: Home Edition")
            criterias.append("Flash Forward")
            criterias.append("General Hospital")
            criterias.append("Grey's Anatomy")
            criterias.append("Hank")
            criterias.append("Hannah Montana")
            criterias.append("Happy Endings")
            criterias.append("Happy Town")
            criterias.append("Huge")
            criterias.append("Impact")
            criterias.append("In the Motherhood")
            criterias.append("It's the Easter Beagle, Charlie Brown")
            criterias.append("Jamie Oliver's Food Revolution")
            criterias.append("Jimmy Kimmel Live")
            criterias.append("Law & Order")
            criterias.append("Legend of the Seeker")
            criterias.append("Less Than Perfect")
            criterias.append("Life on Mars")
            criterias.append("Lost")
            criterias.append("Make It or Break It")
            criterias.append("Modern Family")
            criterias.append("Mr. Sunshine")
            criterias.append("My Generation")
            criterias.append("No Ordinary Family")
            criterias.append("October Road")
            criterias.append("Off the Map")
            criterias.append("One Life to Live")
            criterias.append("Opportunity Knocks")
            criterias.append("Pretty Little Liars")
            criterias.append("Private Practice")
            criterias.append("Reaper")
            criterias.append("Rodney")
            criterias.append("Romantically Challenged")
            criterias.append("Rookie Blue")
            criterias.append("Samantha Who?")
            criterias.append("Scoundrels")
            criterias.append("Scrubs")
            criterias.append("Secret Millionaire")
            criterias.append("Shaq vs.")
            criterias.append("Shark Tank")
            criterias.append("Shrek the Halls")
            criterias.append("Six Degrees")
            criterias.append("Skating with the Stars")
            criterias.append("Supernanny")
            criterias.append("The Bachelor")
            criterias.append("The Bachelorette")
            criterias.append("The Deep End")
            criterias.append("The Forgotten")
            criterias.append("The Gates")
            criterias.append("The Goode Family")
            criterias.append("The Middle")
            criterias.append("The Oprah Winfrey Show")
            criterias.append("The Whole Truth")
            criterias.append("True Beauty")
            criterias.append("Ugly Betty")
            criterias.append("V (2009)")
            criterias.append("What About Brian")
            criterias.append("Wife Swap")
            criterias.append("Wipeout")
            criterias.append("Wonderland")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('abc-family') == "true":
            name = ADDON_SETTINGS.getSetting('abc-family-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("10 Things I Hate About You")
            criterias.append("Greek")
            criterias.append("Huge")
            criterias.append("Kicked Out")
            criterias.append("Kyle XY")
            criterias.append("Labor Pains")
            criterias.append("Lincoln Heights")
            criterias.append("Make It or Break It")
            criterias.append("Melissa & Joey")
            criterias.append("Pretty Little Liars")
            criterias.append("Revenge of the Bridesmaids")
            criterias.append("Ruby & the Rockits")
            criterias.append("The Secret Life of the American Teenager")
            criterias.append("Three Moons Over Milford")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('adult-swim') == "true":
            name = ADDON_SETTINGS.getSetting('adult-swim-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Aqua Teen Hunger Force")
            criterias.append("Children's Hospital")
            criterias.append("Delocated")
            criterias.append("Fullmetal Alchemist Brotherhood")
            criterias.append("King of the Hill")
            criterias.append("Lucy, Daughter of the Devil")
            criterias.append("Mary Shelley's Frankenhole")
            criterias.append("Metalocalypse")
            criterias.append("Robot Chicken")
            criterias.append("Squidbillies")
            criterias.append("The Venture Brothers")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('amc') == "true":
            name = ADDON_SETTINGS.getSetting('amc-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Breaking Bad")
            criterias.append("Mad Men")
            criterias.append("Rubicon")
            criterias.append("The Killing")
            criterias.append("The Walking Dead")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('animal-planet') == "true":
            name = ADDON_SETTINGS.getSetting('animal-planet-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("America's Cutest Cat")
            criterias.append("America's Cutest Dog")
            criterias.append("Animal Armageddon")
            criterias.append("Blood Dolphins")
            criterias.append("Cats 101")
            criterias.append("Confessions: Animal Hoarding")
            criterias.append("Corwin's Quest")
            criterias.append("Dirty Jobs")
            criterias.append("Dogs 101")
            criterias.append("Fatal Attractions")
            criterias.append("Fooled by Nature")
            criterias.append("Freak Encounters")
            criterias.append("I Shouldn't Be Alive")
            criterias.append("I'm Alive")
            criterias.append("Infested!")
            criterias.append("Into the Dragon's Lair")
            criterias.append("It's Me or the Dog")
            criterias.append("Jaws & Claws")
            criterias.append("Jockeys")
            criterias.append("Killer Aliens")
            criterias.append("Last Chance Highway")
            criterias.append("Lost Tapes")
            criterias.append("Meerkat Manor")
            criterias.append("Monsters Inside Me")
            criterias.append("Must Love Cats")
            criterias.append("Pets 101")
            criterias.append("Pit Boss")
            criterias.append("Pit Bulls and Parolees")
            criterias.append("River Monsters")
            criterias.append("Superfetch")
            criterias.append("Taking on Tyson")
            criterias.append("The Haunted")
            criterias.append("The Most Extreme")
            criterias.append("The Planet's Funniest Animals")
            criterias.append("The Ultimate Guide: Dolphins")
            criterias.append("Underdog to Wonderdog")
            criterias.append("Untamed & Uncut")
            criterias.append("Venom in Vegas")
            criterias.append("Weird, True & Freaky")
            criterias.append("Whale Wars")
            criterias.append("Wild Kingdom")
            criterias.append("Wild Recon")
            criterias.append("Wild Russia")
            criterias.append("World's Deadliest Towns")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('bbc-america') == "true":
            name = ADDON_SETTINGS.getSetting('bbc-america-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Being Human (UK)")
            criterias.append("Doctor Who")
            criterias.append("Peep Show (UK)")
            criterias.append("Primeval")
            criterias.append("Robin Hood")
            criterias.append("Skins")
            criterias.append("Survivors")
            criterias.append("Top Gear")
            criterias.append("Torchwood")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('bet') == "true":
            name = ADDON_SETTINGS.getSetting('bet-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Hell Date")
            criterias.append("The Mo'Nique Show")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('bio') == "true":
            name = ADDON_SETTINGS.getSetting('bio-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Biography")
            criterias.append("Celebrity Ghost Stories")
            criterias.append("I Survived")
            criterias.append("Mobsters")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('boomerang') == "true":
            name = ADDON_SETTINGS.getSetting('boomerang-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Smurfs")
            criterias.append("Dexter's Laboratory")
            criterias.append("The Powerpuff Girls")
            criterias.append("Pirates Dark Water")
            criterias.append("Samurai Jack")
            criterias.append("The Batman")
            criterias.append("Jonny Quest")
            criterias.append("SWAT Kats: Radical")
            criterias.append("Thundarr")
            criterias.append("Johnny Bravo")
            criterias.append("Tom & Jerry")
            criterias.append("Banana Splits")
            criterias.append("Wacky Races")
            criterias.append("The Flintstones")
            criterias.append("The Jetsons")
            criterias.append("Popeye")
            criterias.append("Pink Panther")
            criterias.append("Captain Planet")
            criterias.append("Richie Rich")
            criterias.append("Hong Kong Phooey")
            criterias.append("Dastardly & Muttley")
            criterias.append("Mike, Lu & Og")
            criterias.append("Pebbles & Bamm Bamm")
            criterias.append("Huckleb'ry Hound")
            criterias.append("Yogi Bear")
            criterias.append("Scooby-Doo")
            criterias.append("Amazing Chan Chan")
            criterias.append("Speed Buggy")
            criterias.append("Pokemon")
            criterias.append("Krypto the Superdog")
            criterias.append("What's New Scooby")
            criterias.append("Rocky & Bullwinkle")
            criterias.append("Perils of Penelope")
            criterias.append("Snorks")
            criterias.append("Space Ghost/Dino Boy")
            criterias.append("Hey, It's Yogi Bear")
            criterias.append("Cow & Chicken")
            criterias.append("Hole in the Wall")
            criterias.append("Duck Dodgers")
            criterias.append("Looney Tunes")
            criterias.append("The Garfield Show")
            criterias.append("Top Cat")
            criterias.append("Sylvester and Tweety Mysteries")
            criterias.append("Casper's Scare School")
            criterias.append("Mr Bean")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('bravo') == "true":
            name = ADDON_SETTINGS.getSetting('bravo')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("100 Greatest Stand-Ups of All Time")
            criterias.append("9 by Design")
            criterias.append("Battle of the Network Reality Stars")
            criterias.append("Being Bobby Brown")
            criterias.append("Bethenny Ever After")
            criterias.append("Blow Out")
            criterias.append("Bravo All-Star Reality Reunion")
            criterias.append("Bravo's A-List Awards")
            criterias.append("Caroline Rhea: Rhea's Anatomy")
            criterias.append("Celebrity Poker Showdown")
            criterias.append("Chef Academy")
            criterias.append("Date My Ex: Jo & Slade")
            criterias.append("Double Exposure")
            criterias.append("First Class All The Way")
            criterias.append("Flipping Out")
            criterias.append("Great Things About Being...")
            criterias.append("Great Things About the Holidays")
            criterias.append("Hey Paula!")
            criterias.append("Hidden Howie: The Private Life of a Public Nuisance")
            criterias.append("Inside the Actors Studio")
            criterias.append("Kathy Griffin: My Life on the D-List")
            criterias.append("Kathy Griffin: She'll Cut a Bitch")
            criterias.append("Kathy Griffin: The D-List")
            criterias.append("Kell on Earth")
            criterias.append("Last Comic Standing")
            criterias.append("Launch My Line")
            criterias.append("Make Me a Supermodel")
            criterias.append("Miami Social")
            criterias.append("Million Dollar Listing")
            criterias.append("Millionaire Matchmaker")
            criterias.append("NYC Prep")
            criterias.append("Party/Party")
            criterias.append("Project Greenlight")
            criterias.append("Project Runway")
            criterias.append("Queer Eye for the Straight Girl")
            criterias.append("Queer Eye for the Straight Guy")
            criterias.append("Shear Genius")
            criterias.append("Showdogs Moms & Dads")
            criterias.append("Significant Others")
            criterias.append("Situation: Comedy")
            criterias.append("Sports Kids Mom and Dads")
            criterias.append("Step It Up and Dance")
            criterias.append("Tabatha's Salon Takeover")
            criterias.append("The Bad Girls Club")
            criterias.append("The Fashion Show: Ultimate Collection")
            criterias.append("The Rachel Zoe Project")
            criterias.append("The Real Housewives of Atlanta")
            criterias.append("The Real Housewives of Beverly Hills")
            criterias.append("The Real Housewives of D.C.")
            criterias.append("The Real Housewives of Miami")
            criterias.append("The Real Housewives of New Jersey")
            criterias.append("The Real Housewives of New York")
            criterias.append("The Real Housewives of Orange County")
            criterias.append("The Sarah Jones Show")
            criterias.append("Thintervention with Jackie Warner")
            criterias.append("Tim Gunn's Guide to Style")
            criterias.append("Top Chef: Just Desserts")
            criterias.append("Top Chef: Masters")
            criterias.append("Top Design")
            criterias.append("Welcome to the Parker")
            criterias.append("Work Out")
            criterias.append("Work of Art: The Next Great Artist")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('cn') == "true":
            name = ADDON_SETTINGS.getSetting('cn-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Ben 10")
            criterias.append("Chowder")
            criterias.append("Foster's Home For Imaginary Friends")
            criterias.append("Squirrel Boy")
            criterias.append("The Secret Saturdays")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('cbs') == "true":
            name = ADDON_SETTINGS.getSetting('cbs-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("3 Lbs.")
            criterias.append("48 Hours Mystery")
            criterias.append("48 Hours: Live to Tell")
            criterias.append("A Dog Named Christmas")
            criterias.append("Accidentally on Purpose")
            criterias.append("As the World Turns")
            criterias.append("Batwomen of Panama")
            criterias.append("Beverly Hills 90210")
            criterias.append("Big Brother")
            criterias.append("Big Shot Live")
            criterias.append("Bleep My Dad Says")
            criterias.append("Blue Bloods")
            criterias.append("Building Green")
            criterias.append("CSI: Crime Scene Investigation")
            criterias.append("CSI: Miami")
            criterias.append("CSI: New York")
            criterias.append("Cane")
            criterias.append("Carrier")
            criterias.append("Chaotic")
            criterias.append("Clark and Michael")
            criterias.append("Cold Case")
            criterias.append("Comancho Moon")
            criterias.append("Creature Comforts")
            criterias.append("Criminal Minds")
            criterias.append("Criminal Minds: Suspect Behaviour")
            criterias.append("Design e2")
            criterias.append("Dynasty")
            criterias.append("Eleventh Hour")
            criterias.append("Family Ties")
            criterias.append("Flashpoint")
            criterias.append("Gary Unmarried")
            criterias.append("Global Voices")
            criterias.append("Gossip Girl")
            criterias.append("Guiding Light")
            criterias.append("Happy Days")
            criterias.append("Harper's Island")
            criterias.append("Hawaii Five-O")
            criterias.append("How I Met Your Mother")
            criterias.append("I Get That a Lot")
            criterias.append("I Love Lucy")
            criterias.append("In God's Name")
            criterias.append("Inturn")
            criterias.append("Jean-Michel Cousteau: Ocean Adventures")
            criterias.append("Jericho")
            criterias.append("Kid Nation")
            criterias.append("La La Land")
            criterias.append("Let's Make a Deal")
            criterias.append("Live For the Moment")
            criterias.append("Live to Dance")
            criterias.append("Loaded")
            criterias.append("Loving Leah")
            criterias.append("MacGyver")
            criterias.append("Mad Love")
            criterias.append("Made in Spain")
            criterias.append("Medal of Honor")
            criterias.append("Medium")
            criterias.append("Melrose Place")
            criterias.append("Miami Medical")
            criterias.append("Mike & Molly")
            criterias.append("Moonlight")
            criterias.append("Murder Once Removed")
            criterias.append("NCIS")
            criterias.append("NCIS: Los Angeles")
            criterias.append("Nature's Matchmaker")
            criterias.append("Nikita")
            criterias.append("Novel Adventures")
            criterias.append("Numb3rs")
            criterias.append("Perry Mason")
            criterias.append("Phoenix Mars Mission: Ashes to Ice")
            criterias.append("Pirate Master")
            criterias.append("Power of 10")
            criterias.append("Rock Star")
            criterias.append("Rudolph the Red-Nosed Reindeer")
            criterias.append("Rules of Engagement")
            criterias.append("Shark")
            criterias.append("Smith")
            criterias.append("Stand Up To Cancer")
            criterias.append("Star Trek")
            criterias.append("Star Trek: The Animated Series")
            criterias.append("Supernatural")
            criterias.append("Survivor")
            criterias.append("Swingtown")
            criterias.append("Taxi")
            criterias.append("The Amazing Race")
            criterias.append("The Big Bang Theory")
            criterias.append("The Bold and the Beautiful")
            criterias.append("The Brady Bunch")
            criterias.append("The Bridge")
            criterias.append("The Class")
            criterias.append("The Cleaner")
            criterias.append("The Defenders")
            criterias.append("The Doctors")
            criterias.append("Ghost Whisperer")
            criterias.append("The Good Wife")
            criterias.append("The King of Queens")
            criterias.append("The Love Boat")
            criterias.append("The Mentalist")
            criterias.append("The New Adventures of Old Christine")
            criterias.append("The Simpsons")
            criterias.append("The Unit")
            criterias.append("The Young and the Restless")
            criterias.append("There Goes the Neighborhood")
            criterias.append("Two and a Half Men")
            criterias.append("Undercover Boss")
            criterias.append("Viva Laughlin")
            criterias.append("Welcome to the Captain")
            criterias.append("X-Play")
            criterias.append("Yes, Virginia")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('cinemax') == "true":
            name = ADDON_SETTINGS.getSetting('cinemax-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Co-Ed Confidential")
            criterias.append("Forbidden Science")
            criterias.append("Lingerie")
            criterias.append("Life on Top")
            criterias.append("Zane's Sex Chronicles")
            criterias.append("Strikes Back")
            criterias.append("The Transporter")
            criterias.append("SCTV")
            criterias.append("Max Headroom")           
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('comedy-central') == "true":
            name = ADDON_SETTINGS.getSetting('comedy-central-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Colbert Report")
            criterias.append("The Daily Show With Jon Stewart")
            criterias.append("South Park")
            criterias.append("Futurama")
            criterias.append("Tosh.0")
            criterias.append("Ugly Americans")
            criterias.append("Nick Swardson's Pretend Time")
            criterias.append("The Benson Interruption")
            criterias.append("The Goode Family")
            criterias.append("Just Shoot Me!")
            criterias.append("MADtv")
            criterias.append("Married With Children")
            criterias.append("One Night Stand")
            criterias.append("Scrubs")
            criterias.append("Sit Down, Shut Up")
            criterias.append("It's Always Sunny in Philadelphia")
            criterias.append("Jeff Dunham Show")
            criterias.append("Mystery Science Theater 3000")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('cooking') == "true":
            name = ADDON_SETTINGS.getSetting('cooking-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Ask Aida")
            criterias.append("Brunch at Bobby's")
            criterias.append("Cook Like An Iron Chef")
            criterias.append("David Rocco's Dolce Vita")
            criterias.append("Foodography")
            criterias.append("French Food at Home")
            criterias.append("Fresh Food Fast With Emeril Lagassee")
            criterias.append("Healthy Appetite With Ellie Krieger")
            criterias.append("Unique Eats")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('cw') == "true":
            name = ADDON_SETTINGS.getSetting('cw-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("90210")
            criterias.append("Aliens in America")
            criterias.append("America's Next Top Model")
            criterias.append("Gossip Girl")
            criterias.append("Hellcats")
            criterias.append("Life Unexpected")
            criterias.append("Life is Wild")
            criterias.append("Melrose Place")
            criterias.append("Nikita")
            criterias.append("One Tree Hill")
            criterias.append("Plain Jane")
            criterias.append("Priviledged")
            criterias.append("Reaper")
            criterias.append("Shedding for the Wedding")
            criterias.append("Smallville")
            criterias.append("Supernatural")
            criterias.append("Vampire Diaries")
            criterias.append("Veronica Mars")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('discovery') == "true":
            name = ADDON_SETTINGS.getSetting('discovery-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("19 Kids and Counting")
            criterias.append("American Chopper")
            criterias.append("American Chopper: Senior vs. Junior")
            criterias.append("American Loggers")
            criterias.append("An Idiot Abroad")
            criterias.append("Auction Kings")
            criterias.append("Bad Universe")
            criterias.append("Beyond Survival with Les Stroud")
            criterias.append("Black Ops Brothers: Howe & Howe Tech")
            criterias.append("Blood Dolphins")
            criterias.append("Brace for Impact")
            criterias.append("Brew Masters")
            criterias.append("Cash Cab")
            criterias.append("Clash of the Dinosaurs")
            criterias.append("Confessions: Animal Hoarding")
            criterias.append("Construction Intervention")
            criterias.append("DC Cupcakes")
            criterias.append("Daycare Divas")
            criterias.append("Deadliest Catch")
            criterias.append("Desert Car Kings")
            criterias.append("Destroyed in Seconds")
            criterias.append("Dirty Jobs")
            criterias.append("Dual Survival")
            criterias.append("Emeril Green")
            criterias.append("Everest: Beyond the Limit")
            criterias.append("Flying Wild Alaska")
            criterias.append("Future Weapons")
            criterias.append("Ghost Interventions")
            criterias.append("Ghost Lab")
            criterias.append("Gold Rush: Alaska")
            criterias.append("Hogs GOne Wild")
            criterias.append("How Stuff Works")
            criterias.append("Into the Universe with Stephen Hawking")
            criterias.append("Kate Plus 8")
            criterias.append("Kidnap & Rescue")
            criterias.append("King Tut Unwrapped")
            criterias.append("Last Chance Highway")
            criterias.append("Last One Standing")
            criterias.append("Life")
            criterias.append("Little People, Big World")
            criterias.append("Man Vs. Wild")
            criterias.append("Man, Woman, Wild")
            criterias.append("Mega Beasts")
            criterias.append("Moments of Impact")
            criterias.append("Monsters Inside Me")
            criterias.append("Motor City Motors")
            criterias.append("My Strange Addiction")
            criterias.append("Mythbusters")
            criterias.append("One Way Out")
            criterias.append("Pit Bulls and Parolees")
            criterias.append("Pitchmen")
            criterias.append("Sci Fi Science")
            criterias.append("Shark Attack Survival Guide")
            criterias.append("Shark Bite Beach")
            criterias.append("Solving History With Olly Steeds")
            criterias.append("Sons of Guns")
            criterias.append("Storm Chasers")
            criterias.append("Stunt Junkies: Go Big or Go Home")
            criterias.append("Surviving the Cut")
            criterias.append("Swamp Loggers")
            criterias.append("Swords: Life on the Line")
            criterias.append("Tailgate Takedown")
            criterias.append("The Colony")
            criterias.append("The Detonators")
            criterias.append("The Unpoppables")
            criterias.append("Time Warp")
            criterias.append("Ultimate Air Jaws")
            criterias.append("Verminators")
            criterias.append("When We Left Earth: The NASA Missions")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('discovery-health') == "true":
            name = ADDON_SETTINGS.getSetting('discovery-health-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("911: The Bronx")
            criterias.append("I Didn't Know I Was Pregnant")
            criterias.append("I'm Pregnant and...")
            criterias.append("Little People, Big Charlie")
            criterias.append("Mystery Diagnosis")
            criterias.append("National Body Challenge")
            criterias.append("Quints by Surprise")
            criterias.append("The Body Invaders")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('disney-channel') == "true":
            name = ADDON_SETTINGS.getSetting('disney-channel-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("The Famous Jett Jackson")
            criterias.append("Bug Juice")
            criterias.append("Mad Libs")
            criterias.append("Movie Surfers")
            criterias.append("So Weird")
            criterias.append("Z Games")
            criterias.append("The Jersey")
            criterias.append("Even Stevens")
            criterias.append("In a Heartbeat")
            criterias.append("Totally Circus")
            criterias.append("Lizzie McGuire")
            criterias.append("The Proud Family")
            criterias.append("Totally Hoops")
            criterias.append("Kim Possible")
            criterias.append("Totally in Tune")
            criterias.append("That's So Raven")
            criterias.append("Lilo & Stitch: The Series")
            criterias.append("Mike's Super Short Show")
            criterias.append("Dave the Barbarian")
            criterias.append("Phil of the Future")
            criterias.append("Brandy & Mr. Whiskers")
            criterias.append("American Dragon: Jake Long")
            criterias.append("The Suite Life of Zack & Cody")
            criterias.append("The Buzz on Maggie")
            criterias.append("The Emperor's New School")
            criterias.append("Hannah Montana")
            criterias.append("The Replacements")
            criterias.append("Cory in the House")
            criterias.append("Wizards of Waverly Place")
            criterias.append("Phineas and Ferb")
            criterias.append("The Suite Life on Deck")
            criterias.append("Sonny With a Chance")
            criterias.append("Jonas L.A.")
            criterias.append("Good Luck Charlie")
            criterias.append("Fish Hooks")
            criterias.append("Shake It Up")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('playhouse-disney') == "true":
            name = ADDON_SETTINGS.getSetting('playhouse-disney-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Bear in the Big Blue House")
            criterias.append("PB&J Otter")
            criterias.append("Rolie Polie Olie")
            criterias.append("Out of the Box")
            criterias.append("The Book of Pooh")
            criterias.append("Stanley")
            criterias.append("JoJo's Circus")
            criterias.append("Higglytown Heroes")
            criterias.append("Breakfast with Bear")
            criterias.append("Johnny and the Sprites")
            criterias.append("Little Einsteins")
            criterias.append("Charlie and Lola")
            criterias.append("Micky Mouse Clubhouse")
            criterias.append("Handy Manny")
            criterias.append("My Friends Tigger & Pooh")
            criterias.append("Bunnytown")
            criterias.append("Imagination Movers")
            criterias.append("Special Agent Oso")
            criterias.append("Where Is Warehouse Mouse?")
            criterias.append("Jungle Junction")
            criterias.append("Chuggington")
            criterias.append("Jake and the Never Land Pirates")
            criterias.append("Tinga Tinga Tales")
            criterias.append("Babar and the Adventures of Badou")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('diy') == "true":
            name = ADDON_SETTINGS.getSetting('diy-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("10 Things You Must Know")
            criterias.append("BATHtastic!")
            criterias.append("Bath Crashers")
            criterias.append("Bathroom Renovations")
            criterias.append("Blog Cabin")
            criterias.append("Cool Tools")
            criterias.append("Curb Appeal")
            criterias.append("Desperate Landscapes")
            criterias.append("Disaster House")
            criterias.append("House Crashers")
            criterias.append("Indoors Out")
            criterias.append("King of Dirt")
            criterias.append("Kitchen Impossible")
            criterias.append("Man Caves")
            criterias.append("Renovation Realities")
            criterias.append("Rock Solid")
            criterias.append("Sweat Equity")
            criterias.append("Under Contruction")
            criterias.append("Wasted Spaces")
            criterias.append("Yard Crashers")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('e') == "true":
            name = ADDON_SETTINGS.getSetting('e-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Bridalplasty")
            criterias.append("Chelsea Lately")
            criterias.append("Denise Richards: It's Complicated")
            criterias.append("Holly's World")
            criterias.append("Keeping Up With the Kardashians")
            criterias.append("Kendra")
            criterias.append("Kourtney and Khloe Take Miami")
            criterias.append("Kourtney and Kim Take New York")
            criterias.append("Married to Rock")
            criterias.append("Pretty Wild")
            criterias.append("Reality Hell")
            criterias.append("Snoop Dogg's Father Hood")
            criterias.append("The E! True Hollywood Story")
            criterias.append("The E! True Hollywood Story: Young Hollywood")
            criterias.append("The Girls Next Door")
            criterias.append("The Soup")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVNetwork1on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork1') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork2on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork2') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork3on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork3') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork4on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork4') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork5on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork5') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork5"), '', '', '', '', '', '', '', ''))

        #
        # [F-J]
        #
        if ADDON_SETTINGS.getSetting('food') == "true":
            name = ADDON_SETTINGS.getSetting('food-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("30-Minute Meals")
            criterias.append("5 Ingredient Fix")
            criterias.append("Ask Aida")
            criterias.append("Barefoot Contessa")
            criterias.append("Big Daddy's House")
            criterias.append("Boy Meets Grill")
            criterias.append("Chopped")
            criterias.append("Cooking for Real")
            criterias.append("Diners, Drive-Ins and Dives")
            criterias.append("Dinner: Impossible")
            criterias.append("Down Home With the Neelys")
            criterias.append("Everyday Italian")
            criterias.append("Food Network Challenge")
            criterias.append("Giada at Home")
            criterias.append("Good Eats")
            criterias.append("Guy's Big Bite")
            criterias.append("Healthy Appetite With Ellie Krieger")
            criterias.append("How to Boil Water")
            criterias.append("Iron Chef America")
            criterias.append("Paula's Best Dishes")
            criterias.append("Paula's Home Cooking")
            criterias.append("Quick Fix Meals With Robin Miller")
            criterias.append("Sandra's Money Saving Meals")
            criterias.append("Sara's Secrets")
            criterias.append("Secrets of a Restaurant Chef")
            criterias.append("Semi-Homemade Cooking With Sandra Lee")
            criterias.append("Simply Delicioso")
            criterias.append("The Best Thing I Ever Ate")
            criterias.append("The Next Food Network Star")
            criterias.append("Throwdown with Bobby Flay")
            criterias.append("Unwrapped")
            criterias.append("Worst Cooks in America")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('fox') == "true":
            name = ADDON_SETTINGS.getSetting('fox-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("'Til Death")
            criterias.append("24")
            criterias.append("America's Most Wanted")
            criterias.append("American Idol")
            criterias.append("American Misfits")
            criterias.append("Angel")
            criterias.append("Arrested Development")
            criterias.append("Back to You")
            criterias.append("Bob's Burgers")
            criterias.append("Bones")
            criterias.append("Brothers")
            criterias.append("Buffy, the Vampire Slayer")
            criterias.append("Built to Shred")
            criterias.append("Chicago Hope")
            criterias.append("Cops")
            criterias.append("Dollhouse")
            criterias.append("Doogie Howser, M.D.")
            criterias.append("Drive")
            criterias.append("Family Guy")
            criterias.append("Firefly")
            criterias.append("Firsthand")
            criterias.append("Fringe")
            criterias.append("Futurama")
            criterias.append("Glee")
            criterias.append("Hell's Kitchen")
            criterias.append("Hill Street Blues")
            criterias.append("House")
            criterias.append("How I Met Your Mother")
            criterias.append("Human Target")
            criterias.append("In Living Color")
            criterias.append("John Doe")
            criterias.append("K-Ville")
            criterias.append("King of the Hill")
            criterias.append("Kitchen Confidential")
            criterias.append("Kitchen Nightmares")
            criterias.append("Land of the Giants")
            criterias.append("Lone Star")
            criterias.append("Lost in Space")
            criterias.append("Lou Grant")
            criterias.append("M80")
            criterias.append("Mad TV")
            criterias.append("MasterChef")
            criterias.append("Mental")
            criterias.append("More to Love")
            criterias.append("Murder One")
            criterias.append("Nanny and the Professor")
            criterias.append("New Amsterdam")
            criterias.append("New Pollution")
            criterias.append("Newhart")
            criterias.append("Osbournes: Reloaded")
            criterias.append("Past Life")
            criterias.append("Picket Fences")
            criterias.append("Prison Break")
            criterias.append("Raising Hope")
            criterias.append("Reba")
            criterias.append("Remington Steele")
            criterias.append("Return to the Planet of the Apes")
            criterias.append("Rhoda")
            criterias.append("Roswell")
            criterias.append("Running Wilde")
            criterias.append("Sit Down, Shut Up")
            criterias.append("So You THink You Can Dance")
            criterias.append("Sons of Tucson")
            criterias.append("St. Elsewhere")
            criterias.append("Stacked")
            criterias.append("Standoff")
            criterias.append("Terminator: The Sarah Connor Chronicles")
            criterias.append("The 808")
            criterias.append("The Adventures of Danny & The Dingo")
            criterias.append("The Big Valley")
            criterias.append("The Bob Newhart Show")
            criterias.append("The Captain & Casey Show")
            criterias.append("The Chicago Code")
            criterias.append("The Cleveland Show")
            criterias.append("The Fall Guy")
            criterias.append("The Good Guys")
            criterias.append("The Loop")
            criterias.append("The Mary Tyler Moore Show")
            criterias.append("The Practice")
            criterias.append("The Pretender")
            criterias.append("The Return of Jezebel James")
            criterias.append("The Simpsons")
            criterias.append("The Time Tunnel")
            criterias.append("The White Shadow")
            criterias.append("Thief")
            criterias.append("Traffic Light")
            criterias.append("Unhitched")
            criterias.append("Vanished")
            criterias.append("Voyage to the Bottom of the Sea")
            criterias.append("WKRP in Cincinnati")
            criterias.append("X Factor")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('fx') == "true":
            name = ADDON_SETTINGS.getSetting('fx-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Archer")
            criterias.append("Damages")
            criterias.append("It's Always Sunny in Philadelphia")
            criterias.append("Justified")
            criterias.append("Lights Out")
            criterias.append("Louie")
            criterias.append("Nip/Tuck")
            criterias.append("Rescue Me")
            criterias.append("Sons of Anarchy")
            criterias.append("Terriers")
            criterias.append("The League")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('g4') == "true":
            name = ADDON_SETTINGS.getSetting('g4-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Attack of the Show!")
            criterias.append("Human Wrecking Balls")
            criterias.append("It's Effin' Science")
            criterias.append("Web Soup")
            criterias.append("X-Play")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('golf') == "true":
            name = ADDON_SETTINGS.getSetting('golf-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("12 Nights at the Academy")
            criterias.append("Being John Daly")
            criterias.append("Big Break Dominican Republic")
            criterias.append("Big Break Sandals Resort")
            criterias.append("Donald J. Trump's Fabulous World of Golf")
            criterias.append("Pipe Dream")
            criterias.append("The Golf Fix")
            criterias.append("The Haney Project")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('hbo') == "true":
            name = ADDON_SETTINGS.getSetting('hbo-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Big Love")
            criterias.append("Boardwalk Empire")
            criterias.append("The Neistat Brothers")
            criterias.append("Masterclass")
            criterias.append("Treme")
            criterias.append("Funny or Die Presents")
            criterias.append("How to Make It in America")
            criterias.append("Bored to Death")
            criterias.append("Hung")
            criterias.append("Eastbound & Down")
            criterias.append("The Life & Times of Tim")
            criterias.append("Down and Dirty with Jim Norton")
            criterias.append("True Blood")
            criterias.append("In Treatment")
            criterias.append("24/7")
            criterias.append("Cathouse: The Series")
            criterias.append("Entourage")
            criterias.append("Curb Your Enthusiasm")
            criterias.append("Autopsy")
            criterias.append("Def Comedy Jam")
            criterias.append("Real Sex")
            criterias.append("America Undercover")
            criterias.append("The Pacific")
            criterias.append("Summer Heights High")
            criterias.append("Little Britain USA")
            criterias.append("Generation Kill")
            criterias.append("John Adams")
            criterias.append("Flight of the Conchords")
            criterias.append("John from Cincinnati")
            criterias.append("Tell Me You Love Me")
            criterias.append("Lucky Louie")
            criterias.append("Rome")
            criterias.append("Extras")
            criterias.append("The Comeback")
            criterias.append("Unscripted")
            criterias.append("Deadwood")
            criterias.append("Family Bonds")
            criterias.append("Carnivale")
            criterias.append("K Street")
            criterias.append("Da Ali G Show")
            criterias.append("The Wire")
            criterias.append("Band of Brothers")
            criterias.append("The Mind of the Married Man")
            criterias.append("Six Feet Under")
            criterias.append("G String Divas")
            criterias.append("The Corner")
            criterias.append("The Sopranos")
            criterias.append("Crashbox")
            criterias.append("A Little Curious")
            criterias.append("Sex and the City")
            criterias.append("From the Earth to the Moon")
            criterias.append("Oz")
            criterias.append("Tenacious D")
            criterias.append("Spawn")
            criterias.append("Spicy City")
            criterias.append("Perversions of Science")
            criterias.append("Arliss")
            criterias.append("Tracey Takes On...")
            criterias.append("Taxicab Confessions")
            criterias.append("Hardcore TV")
            criterias.append("Dream On")
            criterias.append("The Adventures of Tintin")
            criterias.append("Tales from the Crypt")
            criterias.append("The Storyteller")
            criterias.append("1st & Ten")
            criterias.append("Maximum Security")
            criterias.append("The Hitchhiker")
            criterias.append("Yesteryear")
            criterias.append("Video Jukebox")
            criterias.append("Time Was...")
            criterias.append("On Location")
            criterias.append("Standing Room Only")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('hgtv') == "true":
            name = ADDON_SETTINGS.getSetting('hgtv-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("All American Handyman")
            criterias.append("Bang For Your Buck")
            criterias.append("Carter Can")
            criterias.append("Color Splash")
            criterias.append("Curb Appeal")
            criterias.append("Dear Genevieve")
            criterias.append("Deserving Design")
            criterias.append("Design on a Dime")
            criterias.append("Designed to Sell")
            criterias.append("Desperate to Buy")
            criterias.append("Don't Sweat It")
            criterias.append("Extreme Halloween")
            criterias.append("HGTV's Design Star")
            criterias.append("Halloween Block Party")
            criterias.append("Hidden Potential")
            criterias.append("Home Rules")
            criterias.append("House Hunters")
            criterias.append("House Hunters International")
            criterias.append("Kidspace")
            criterias.append("My First Place")
            criterias.append("My First Sale")
            criterias.append("Myles of Style")
            criterias.append("Outer Spaces")
            criterias.append("Paint Over! With Jennifer Bertrand")
            criterias.append("Real Estate Intervention")
            criterias.append("Red Hot & Green")
            criterias.append("Secrets From A Stylist")
            criterias.append("Selling New York")
            criterias.append("Small Space, Big Style")
            criterias.append("Spice Up My Kitchen")
            criterias.append("Superscapes")
            criterias.append("That's Clever")
            criterias.append("The Antonio Project")
            criterias.append("The Antonio Treatment")
            criterias.append("What's with that Really Haunted Halloween House")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('history') == "true":
            name = ADDON_SETTINGS.getSetting('history-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("America: The Story of Us")
            criterias.append("American Pickers")
            criterias.append("Ancient Aliens")
            criterias.append("Ax Men")
            criterias.append("Battle 360")
            criterias.append("Brad Meltzer's Decoded")
            criterias.append("Deconstructed")
            criterias.append("History of the Holidays")
            criterias.append("Human Weapon")
            criterias.append("IRT: Deadliest Roads")
            criterias.append("Jurassic Fight Club")
            criterias.append("Modern Marvels")
            criterias.append("Only in America with Larry the Cable Guy")
            criterias.append("Pawn Stars")
            criterias.append("Science of Love")
            criterias.append("Swamp People")
            criterias.append("The Lost Evidence")
            criterias.append("The Real Face of Jesus")
            criterias.append("The Universe")
            criterias.append("Top Gear")
            criterias.append("Top Shot")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('hub') == "true":
            name = ADDON_SETTINGS.getSetting('hub-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Atomic Betty")
            criterias.append("Cosmic QUantum Ray")
            criterias.append("Dan Vs.")
            criterias.append("Deltora Quest")
            criterias.append("Dennis & Gnasher")
            criterias.append("My Little Pony Friendship is Magic")
            criterias.append("R.L. Stine's The Haunting Hour")
            criterias.append("The Adventures of Chuck & Friends")
            criterias.append("Transformers Prime")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('id') == "true":
            name = ADDON_SETTINGS.getSetting('id-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Disappeared")
            criterias.append("Stalked: Someone's Watching")
            criterias.append("Stolen Voices, Buried Secrets")
            criterias.append("True Crime with Aphrodite Jones")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVNetwork6on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork6') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 6','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork6"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork7on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork7') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 7','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork7"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork8on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork8') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 8','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork8"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork9on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork9') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 9','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork9"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork10on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork10') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 10','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork10"), '', '', '', '', '', '', '', ''))

        #
        # [K-O]
        #
        if ADDON_SETTINGS.getSetting('lifetime') == "true":
            name = ADDON_SETTINGS.getSetting('lifetime-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Army Wives")
            criterias.append("Blood Ties")
            criterias.append("Cook Yourself Thin")
            criterias.append("Cries in the Dark")
            criterias.append("Fatal Desire")
            criterias.append("Frasier")
            criterias.append("Girl, Positive")
            criterias.append("How To Look Good Naked")
            criterias.append("Lies My Mother Told Me")
            criterias.append("Models of the Runway")
            criterias.append("On the Road With Austin & Santino")
            criterias.append("One Born Every Minute")
            criterias.append("Project Runway")
            criterias.append("Seriously Funny Kids")
            criterias.append("Spotlight 25")
            criterias.append("Strong Medicine")
            criterias.append("The Fairy Jobmother")
            criterias.append("The Last Trimester")
            criterias.append("The Nanny")
            criterias.append("The Staircase Murders")
            criterias.append("Will & Grace")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('military') == "true":
            name = ADDON_SETTINGS.getSetting('military-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("At Sea")
            criterias.append("Inner Wounds of War")
            criterias.append("No Dog Left Behind")
            criterias.append("Return Salute")
            criterias.append("Science of War")
            criterias.append("Scienceof the Elite Soldier")
            criterias.append("Special Ops Mission")
            criterias.append("Strange Planes")
            criterias.append("Top Sniper")
            criterias.append("Ultimate Weapons")
            criterias.append("Weapons Masters")
            criterias.append("Weaponology")
            criterias.append("World War II in Color")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mtv') == "true":
            name = ADDON_SETTINGS.getSetting('mtv-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Aeon Flux")
            criterias.append("I Used to be Fat")
            criterias.append("Jersey Shore")
            criterias.append("Laguna Beach: The Real Orange County")
            criterias.append("My Life as Liz")
            criterias.append("Teen Mom")
            criterias.append("The Hills")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('ngc') == "true":
            name = ADDON_SETTINGS.getSetting('ngc-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("2012 Countdown to Armageddon")
            criterias.append("9/11: Science and Conspiracy")
            criterias.append("Alaska State Troopers")
            criterias.append("Alien Earths")
            criterias.append("Alone in the Wild")
            criterias.append("Bizarre Dinosaurs")
            criterias.append("Border Wars")
            criterias.append("Cowboys of the Sea: The Long Haul")
            criterias.append("Deadliest Catch")
            criterias.append("Dog Whisperer")
            criterias.append("Dogtown")
            criterias.append("Drain the Ocean")
            criterias.append("Egypt Unwrapped")
            criterias.append("Egyptian Secrets of the Afterlife")
            criterias.append("Expedition Great White")
            criterias.append("Expedition Grizzly")
            criterias.append("Explorer")
            criterias.append("Great Migrations")
            criterias.append("Hard Time")
            criterias.append("Hooked: Man vs. Fish")
            criterias.append("Hooked: Monster Fish of Mongolia")
            criterias.append("Humanly Impossible")
            criterias.append("In the Womb: Extreme Animals")
            criterias.append("Inside")
            criterias.append("Inside Guantanamo")
            criterias.append("Journey Into Amazonia")
            criterias.append("L.A. Hard Hats")
            criterias.append("Lockdown")
            criterias.append("Locked Up Abroad")
            criterias.append("Man-Made")
            criterias.append("Mars: Making the New Earth")
            criterias.append("Mysteries of the Bible")
            criterias.append("Naked Science")
            criterias.append("National Geographic")
            criterias.append("National Geographic Presents")
            criterias.append("Nature's Greatest Defender")
            criterias.append("Prehistoric Predators")
            criterias.append("Raw Anatomy")
            criterias.append("Rebel Monkeys")
            criterias.append("Rescue Ink Unleashed")
            criterias.append("Search for the Amazon Headshrinkers")
            criterias.append("Secrets of Florence")
            criterias.append("Shadow Soldiers")
            criterias.append("Taboo")
            criterias.append("The Animal Extractors")
            criterias.append("The First Jesus?")
            criterias.append("The Girl Who Cries Bloos")
            criterias.append("The Girl With Eight Limbs Revisited")
            criterias.append("The Human Family Tree")
            criterias.append("The Lost JFK Tapes: The Assassination")
            criterias.append("The Skyjacker That Got Away")
            criterias.append("The World's Smallest Girl")
            criterias.append("Time Shifters")
            criterias.append("Ultimate Factories")
            criterias.append("Unlikely Animal Friends")
            criterias.append("Wild Indonesia")
            criterias.append("Wild!")
            criterias.append("World's Toughest Fixes")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('nbc') == "true":
            name = ADDON_SETTINGS.getSetting('nbc-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("100 Questions")
            criterias.append("30 Rock")
            criterias.append("Adam-12")
            criterias.append("America's Got Talent")
            criterias.append("America's Next Great Restaurant")
            criterias.append("American Gladiators")
            criterias.append("Attack of the Show!")
            criterias.append("Battlestar Galactica")
            criterias.append("Bethenny Ever After")
            criterias.append("Blue Skies")
            criterias.append("Breakthrough with Tony Robbins")
            criterias.append("Busted on the Job")
            criterias.append("Century City")
            criterias.append("Chase")
            criterias.append("Chopping Block")
            criterias.append("Chuck")
            criterias.append("Community")
            criterias.append("Covert Affairs")
            criterias.append("Crime & Punishment")
            criterias.append("Crime and Punishment")
            criterias.append("Crusoe")
            criterias.append("Dance Your Ass Off")
            criterias.append("Days of Our Lives")
            criterias.append("Dew Underground")
            criterias.append("Double Exposure")
            criterias.append("Emergency!")
            criterias.append("Friday Night Lights")
            criterias.append("Friends with Benefits")
            criterias.append("Harry's Law")
            criterias.append("Heroes")
            criterias.append("I'm a Celebrity ... Get Me Out of Here")
            criterias.append("In Gayle We Trust")
            criterias.append("In Plain Sight")
            criterias.append("Inside the Actors Studio")
            criterias.append("Jail")
            criterias.append("Jerry Springer")
            criterias.append("Journeyman")
            criterias.append("Kings")
            criterias.append("Knight Rider")
            criterias.append("Knight Rider (2008)")
            criterias.append("Kojak")
            criterias.append("Last Comic Standing")
            criterias.append("Law & Order")
            criterias.append("Law & Order: Los Angeles")
            criterias.append("Law & Order: Special Victims Unit")
            criterias.append("Life")
            criterias.append("Lipstick Jungle")
            criterias.append("Lockup: Raw")
            criterias.append("Losing It with Jillian")
            criterias.append("Love Bites")
            criterias.append("M.A.N.T.I.S.")
            criterias.append("Mad Mad House")
            criterias.append("Magnum P.I.")
            criterias.append("McHale's Navy")
            criterias.append("Mercy")
            criterias.append("Merlin")
            criterias.append("Meteor")
            criterias.append("Monk")
            criterias.append("My Name is Earl")
            criterias.append("My Own Worst Enemy")
            criterias.append("Nashville Star")
            criterias.append("Outlaw")
            criterias.append("Outsources")
            criterias.append("Parenthood")
            criterias.append("Parks & Recreation")
            criterias.append("Perfect Couples")
            criterias.append("Persons Unknown")
            criterias.append("Quantum Leap")
            criterias.append("Raines")
            criterias.append("School Pride")
            criterias.append("Southland")
            criterias.append("The A-Team")
            criterias.append("The Apprentice")
            criterias.append("The Biggest Loser")
            criterias.append("The Biggest Loser: Families")
            criterias.append("The Cape")
            criterias.append("The Event")
            criterias.append("The Great American Road Trip")
            criterias.append("The Listener")
            criterias.append("The Marriage Ref")
            criterias.append("The Office")
            criterias.append("The Philanthropist")
            criterias.append("The Real Housewives of Atlanta")
            criterias.append("The Real Housewives of New Jersey")
            criterias.append("The Real Housewives of Orange County")
            criterias.append("The Sing-Off")
            criterias.append("The Singing Bee")
            criterias.append("The Storm")
            criterias.append("They Came from Outer Space")
            criterias.append("Tori & Dean: Home Sweet Hollywood")
            criterias.append("Trauma")
            criterias.append("Tremors: The Series")
            criterias.append("Undercovers")
            criterias.append("Work of Art: The Next Great Artist")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('nick') == "true":
            name = ADDON_SETTINGS.getSetting('nick-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Back at the Barnyard")
            criterias.append("SpongeBob SquarePants")
            criterias.append("iCarly")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('oxygen') == "true":
            name = ADDON_SETTINGS.getSetting('oxygen-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Addicted to Beauty")
            criterias.append("All About Aubrey")
            criterias.append("Captured")
            criterias.append("Coolio's Rules")
            criterias.append("Dance Your Ass Off")
            criterias.append("Deion & Pillar: Prime Time Love")
            criterias.append("Hair Battle Spectacular")
            criterias.append("House of Glam")
            criterias.append("Jersey Couture")
            criterias.append("Love Games: Bad Girls Need Love Too")
            criterias.append("Pretty Wicked")
            criterias.append("Running Russell Simmons")
            criterias.append("Snapped")
            criterias.append("The Bad Girls Club")
            criterias.append("The Janice Dickinson Modeling Agency")
            criterias.append("The Naughty Kitchen with Chef Blythe Beck")
            criterias.append("Tori & DeanL Home Sweet Hollywood")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVNetwork11on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork11') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 11','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork11"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork12on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork12') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 12','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork12"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork13on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork13') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 13','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork13"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork14on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork14') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 14','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork14"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork15on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork15') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 15','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork15"), '', '', '', '', '', '', '', ''))

        #
        # [P-Z]
        #
        if ADDON_SETTINGS.getSetting('pbs') == "true":
            name = ADDON_SETTINGS.getSetting('pbs-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Art in the Twenty-First Century")
            criterias.append("Carrier")
            criterias.append("Degrassi High")
            criterias.append("Design e2")
            criterias.append("Global Voices")
            criterias.append("Gourmet's Diary of a Foodie")
            criterias.append("Independent Lens")
            criterias.append("Japan: Memoirs of a Secret Empire")
            criterias.append("Journey to Palomar")
            criterias.append("Made in Spain")
            criterias.append("Nova")
            criterias.append("Phoenix Mars Mission: Ashes to Ice")
            criterias.append("Scientific American Frontiers")
            criterias.append("The American Experience")
            criterias.append("The Medici: Godfathers of the Renaissance")
            criterias.append("The Price of Freedom")
            criterias.append("The Roman Empire in the First Century")
            criterias.append("True Whispers: The True Story of the Navajo Codetalkers")
            criterias.append("West Point")
            criterias.append("Windows to the Sea")
            criterias.append("Wired Science")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('planet-green') == "true":
            name = ADDON_SETTINGS.getSetting('planet-green-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Boomtown")
            criterias.append("Coastwatch")
            criterias.append("Conviction Kitchen")
            criterias.append("Day of Discovery")
            criterias.append("Dean of Invention")
            criterias.append("Emeril Green")
            criterias.append("Focus Earth With Bob Woodruff")
            criterias.append("Future Food")
            criterias.append("Living With Ed")
            criterias.append("Mean Green Machines")
            criterias.append("Operation Wild")
            criterias.append("Planet Green")
            criterias.append("The Fabulous Beekman Boys")
            criterias.append("World's Greenest Homes")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('showtime') == "true":
            name = ADDON_SETTINGS.getSetting('showtime-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Dexter")
            criterias.append("Weeds")
            criterias.append("Californication")
            criterias.append("Nurse Jackie")
            criterias.append("The Tudors")
            criterias.append("The L Word")
            criterias.append("The Big C")
            criterias.append("United States of Tara")
            criterias.append("Shameless")
            criterias.append("Secret Diary of a Call Girl")
            criterias.append("Episodes")
            criterias.append("Big Brother: After Dark")
            criterias.append("Penn & Teller: Bullshit!")
            criterias.append("La La Land")
            criterias.append("The Real L Word")
            criterias.append("Body Language")
            criterias.append("Beach Heat: Miami")
            criterias.append("The Borgias")
            criterias.append("33 Brompton Place")
            criterias.append("Brotherhood")
            criterias.append("Dead Like Me")
            criterias.append("Huff")
            criterias.append("Jeremiah")
            criterias.append("Leap Years")
            criterias.append("Linc's")
            criterias.append("Masters of Horror")
            criterias.append("Meadowlands")
            criterias.append("Murder in Space")
            criterias.append("Odyssey 5")
            criterias.append("Out of Order")
            criterias.append("The Outer Limits")
            criterias.append("Queer as Folk")
            criterias.append("The Paper Chase")
            criterias.append("Poltergeist: The Legacy")
            criterias.append("Resurrection Blvd.")
            criterias.append("Sherman Oaks")
            criterias.append("Sleeper Cell")
            criterias.append("Soul Food")
            criterias.append("Street Time")
            criterias.append("Total Recall")
            criterias.append("A New Day in Eden")
            criterias.append("Barbershop: The Series")
            criterias.append("Beggars and Choosers")
            criterias.append("Bizarre")
            criterias.append("Brothers")
            criterias.append("Engine Trouble")
            criterias.append("Fat Actress")
            criterias.append("The Frantics")
            criterias.append("Free for All")
            criterias.append("Going to California")
            criterias.append("Queer Duck")
            criterias.append("Rude Awakening")
            criterias.append("Super Dave")
            criterias.append("Damon Wayan' The Underground")
            criterias.append("Tracey Ullman's State of the Union")
            criterias.append("Washington")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('style') == "true":
            name = ADDON_SETTINGS.getSetting('style-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Chelsea Lately")
            criterias.append("Clean House")
            criterias.append("Dallas Divas & Daughters")
            criterias.append("Diary of an Affair")
            criterias.append("Dress My Nest")
            criterias.append("Fashion Emergency")
            criterias.append("Giuliana & Bill")
            criterias.append("How Do I Look?")
            criterias.append("I Purpose")
            criterias.append("Jerseylicious")
            criterias.append("Kimora: Life in the Fab Lane")
            criterias.append("Mel B: It's a Scary World")
            criterias.append("Ruby")
            criterias.append("Running in Heels")
            criterias.append("Split Ends")
            criterias.append("Style Her Famous")
            criterias.append("Tacky House")
            criterias.append("Too Fat for 15: Fighting Back")
            criterias.append("Ultimate Style")
            criterias.append("What I Hate About Me")
            criterias.append("Whose Wedding Is It Anyway?")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('sundance') == "true":
            name = ADDON_SETTINGS.getSetting('sundance-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("City of Men")
            criterias.append("Iconoclasts")
            criterias.append("John Safran vs God")
            criterias.append("Live from Abbey Road")
            criterias.append("Money Dust")
            criterias.append("Nimrod Nation")
            criterias.append("Sin  City Law")
            criterias.append("Slings and Arrows")
            criterias.append("Spectacle: Elvis Costello With...")
            criterias.append("Swinging")
            criterias.append("The Education of Ms. Groves")
            criterias.append("The Girls of Hedsor Hall")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('syfy') == "true":
            name = ADDON_SETTINGS.getSetting('syfy-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("24")
            criterias.append("Alice")
            criterias.append("Battlestar Galactica (2003)")
            criterias.append("Beast Legends")
            criterias.append("Being Human")
            criterias.append("Caprica")
            criterias.append("Destination: Truth")
            criterias.append("Dincroc vs. Supergator")
            criterias.append("Eleventh Hour")
            criterias.append("Estate of Panic")
            criterias.append("Eureka")
            criterias.append("Face-Off")
            criterias.append("Fact or Faked: Paranormal Files")
            criterias.append("Flash Gordon")
            criterias.append("Fringe")
            criterias.append("Ghost Hunters")
            criterias.append("Ghost Hunters Academy")
            criterias.append("Ghost Hunters International")
            criterias.append("Haven")
            criterias.append("Heroes")
            criterias.append("Hollywood Treasure")
            criterias.append("Knight Rider (2008)")
            criterias.append("Mandrake")
            criterias.append("Mega Piranha")
            criterias.append("Merlin")
            criterias.append("Outer Space Astronauts")
            criterias.append("Red: Werewolf Hunter")
            criterias.append("SGU: Stargate Universe")
            criterias.append("Sanctuary")
            criterias.append("Scare Tactics")
            criterias.append("Sharktopus")
            criterias.append("Stargate SG-1")
            criterias.append("Stargate: Atlantis")
            criterias.append("Stargate: Continuum")
            criterias.append("The Dead Zone")
            criterias.append("The Deadliest Warrior")
            criterias.append("Torchwood")
            criterias.append("Tripping the Rift")
            criterias.append("WCG Ultimate Gamer")
            criterias.append("Warehouse 13")
            criterias.append("Witchville")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('tbs') == "true":
            name = ADDON_SETTINGS.getSetting('tbs-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("10 Items or Less")
            criterias.append("Daisy Does America")
            criterias.append("Frank TV")
            criterias.append("My Boys")
            criterias.append("Seinfeld")
            criterias.append("The Bill Engvall Show")
            criterias.append("The King of Queens")
            criterias.append("The Real Gilligan's Island")
            criterias.append("Tyler Perry's House of Payne")
            criterias.append("Tyler Perry's Meet the Browns")
            criterias.append("World's Funniest Commercials")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('tlc') == "true":
            name = ADDON_SETTINGS.getSetting('tlc-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("19 Kids and Counting")
            criterias.append("Addicted")
            criterias.append("After the Fall")
            criterias.append("Auctioneer$")
            criterias.append("BBQ Pitmasters")
            criterias.append("Bama Belles")
            criterias.append("Battle of the Wedding Designers")
            criterias.append("Battle of the Wedding Planners")
            criterias.append("Best Food Ever")
            criterias.append("Cake Boss")
            criterias.append("Cake Boss: Next Great Baker")
            criterias.append("Chocolate Wars")
            criterias.append("Crazy Christmas Lights")
            criterias.append("DC Cupcakes")
            criterias.append("Dancer with Tiny Legs")
            criterias.append("Fabulous Cakes")
            criterias.append("Flowers Uncut With Jeff Leatham")
            criterias.append("Food Buddha")
            criterias.append("Four Weddings")
            criterias.append("Freaky Eaters")
            criterias.append("Hoarding: Buried Alive")
            criterias.append("Homemade Millionaire")
            criterias.append("I Didn't Know I Was Pregnant")
            criterias.append("Inedible to Incredible")
            criterias.append("Jon & Kate Plus 8")
            criterias.append("Kate Plus 8")
            criterias.append("Kitchen Boss")
            criterias.append("LA Ink")
            criterias.append("Little Chocolatiers")
            criterias.append("Little Parents, First Baby")
            criterias.append("Little People, Big World")
            criterias.append("Lotter Changed My Life")
            criterias.append("Make Room for Multiples")
            criterias.append("Mall Cops: Mall of America")
            criterias.append("Masters of Reception")
            criterias.append("Miami Ink")
            criterias.append("My Strange Addiction")
            criterias.append("One Big Happy Family")
            criterias.append("Our Little Life")
            criterias.append("Out of Control Drivers")
            criterias.append("Paranormal Court")
            criterias.append("Police Women of Broward County")
            criterias.append("Police Women of Cincinnati")
            criterias.append("Police Women of Dallas")
            criterias.append("Police Women of Maricopa County")
            criterias.append("Police Women of Memphis")
            criterias.append("Quints by Surprise")
            criterias.append("Quintuplet Surprise")
            criterias.append("Really Reckless Drivers")
            criterias.append("Sarah Palin's Alaska")
            criterias.append("Say Yes to the Dress")
            criterias.append("Say Yes to the Dress: Atlanta")
            criterias.append("Say Yes to the Dress: Big Bliss")
            criterias.append("Sextistics: Your Love Life")
            criterias.append("Sextuplets Take New York")
            criterias.append("Sister Wives")
            criterias.append("Strange Sex")
            criterias.append("Super Pooches")
            criterias.append("Table for 12")
            criterias.append("Ted Haggard: Scandalous")
            criterias.append("The Little Couple")
            criterias.append("The Man With Half a Body")
            criterias.append("The Opener")
            criterias.append("The Unpoppables")
            criterias.append("Toddlers & Tiaras")
            criterias.append("Trashmen")
            criterias.append("Ultimate Cake Off")
            criterias.append("What Not To Wear")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('tnt') == "true":
            name = ADDON_SETTINGS.getSetting('tnt-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Angel")
            criterias.append("Dark Blue")
            criterias.append("Hawthorne")
            criterias.append("Heartland")
            criterias.append("Leverage")
            criterias.append("Men of a Certain Age")
            criterias.append("Raising the Bar")
            criterias.append("Saving Grace")
            criterias.append("Southland")
            criterias.append("The Closer")
            criterias.append("The Company")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('usa') == "true":
            name = ADDON_SETTINGS.getSetting('usa-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Burn Notice")
            criterias.append("Covert Affairs")
            criterias.append("Fairly Legal")
            criterias.append("In Plain Sight")
            criterias.append("Monk")
            criterias.append("Psych")
            criterias.append("Royal Pains")
            criterias.append("The 4400")
            criterias.append("The Dead Zone")
            criterias.append("The Starter Wife")
            criterias.append("White Collar")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customTVNetwork16on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork16') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 16','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork16"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork17on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork17') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 17','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork17"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork18on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork18') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 18','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork18"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork19on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork19') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 19','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork19"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customTVNetwork20on')=="true":
            if ADDON_SETTINGS.getSetting('customTVNetwork20') <> "":
                self.presetChannels.append(presetChannel('Custom TV Network 20','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customTVNetwork20"), '', '', '', '', '', '', '', ''))


######################################################
##
##  MOVIE GENRE
##
######################################################

    def readMovieGenrePresetChannelConfig(self):
        self.log('Getting Movie Genre Presets ')
        # Shared Settings
        type = 'movies'
        limit = ADDON_SETTINGS.getSetting('limit2')
        random = ADDON_SETTINGS.getSetting('random2')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched2')
        nospecials = ''
        resolution = ADDON_SETTINGS.getSetting('resolution2')
        #
        if ADDON_SETTINGS.getSetting('action-movies') == "true":
            name = ADDON_SETTINGS.getSetting('action-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'action'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('adventure-movies') == "true":
            name = ADDON_SETTINGS.getSetting('adventure-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'adventure'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('animation-movies') == "true":
            name = ADDON_SETTINGS.getSetting('animation-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'animation'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('biography-movies') == "true":
            name = ADDON_SETTINGS.getSetting('biography-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'action'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('comedy-movies') == "true":
            name = ADDON_SETTINGS.getSetting('comedy-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'comedy'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('crime-movies') == "true":
            name = ADDON_SETTINGS.getSetting('crime-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'crime'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('documentary-movies') == "true":
            name = ADDON_SETTINGS.getSetting('documentary-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'documentary'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('drama-movies') == "true":
            name = ADDON_SETTINGS.getSetting('drama-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'drama'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('family-movies') == "true":
            name = ADDON_SETTINGS.getSetting('family-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'family'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('fantasy-movies') == "true":
            name = ADDON_SETTINGS.getSetting('fantasy-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'fantasy'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('film-noir-movies') == "true":
            name = ADDON_SETTINGS.getSetting('film-noir-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'film-noir'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('history-movies') == "true":
            name = ADDON_SETTINGS.getSetting('history-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'history'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('horror-movies') == "true":
            name = ADDON_SETTINGS.getSetting('horror-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'horror'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('musical-movies') == "true":
            name = ADDON_SETTINGS.getSetting('musical-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'musical'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('music-movies') == "true":
            name = ADDON_SETTINGS.getSetting('music-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'music'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mystery-movies') == "true":
            name = ADDON_SETTINGS.getSetting('mystery-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'mystery'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('road-movies') == "true":
            name = ADDON_SETTINGS.getSetting('road-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'road'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('romance-movies') == "true":
            name = ADDON_SETTINGS.getSetting('romance-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'romance'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('science-fiction-movies') == "true":
            name = ADDON_SETTINGS.getSetting('science-fiction-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'science-fiction'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('short-movies') == "true":
            name = ADDON_SETTINGS.getSetting('short-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'short'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('sport-movies') == "true":
            name = ADDON_SETTINGS.getSetting('sport-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'sport'
            operator2 = ''
            criteria2 = ''
        if ADDON_SETTINGS.getSetting('thriller-movies') == "true":
            name = ADDON_SETTINGS.getSetting('thriller-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'thriller'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('war-movies') == "true":
            name = ADDON_SETTINGS.getSetting('war-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'war'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('western-movies') == "true":
            name = ADDON_SETTINGS.getSetting('western-movies-name')
            rule1 = 'genre'
            rule2 = ''
            operator1 = 'is'
            criteria1 = 'western'
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customMovieGenre1on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieGenre1') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Genre 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieGenre1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieGenre2on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieGenre2') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Genre 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieGenre2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieGenre3on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieGenre3') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Genre 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieGenre3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieGenre3on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieGenre4') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Genre 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieGenre4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieGenre4on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieGenre5') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Genre 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieGenre5"), '', '', '', '', '', '', '', ''))


######################################################
##
##  MOVIE DECADES
##
######################################################

    def readMovieDecadePresetChannelConfig(self):
        self.log('Getting Movie Decade Presets ')
        # Shared Settings
        type = 'movies'
        limit = ADDON_SETTINGS.getSetting('limit2')
        random = ADDON_SETTINGS.getSetting('random2')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched2')
        nospecials = ''
        resolution = ADDON_SETTINGS.getSetting('resolution2')
        #
        if ADDON_SETTINGS.getSetting('1950s-movies') == "true":
            name = ADDON_SETTINGS.getSetting('1950s-movies-name')
            rule1 = 'year'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1949'
            operator2 = 'before'
            criteria2 = '1960'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('1960s-movies') == "true":
            name = ADDON_SETTINGS.getSetting('1960s-movies-name')
            rule1 = 'year'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1959'
            operator2 = 'before'
            criteria2 = '1970'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('1970s-movies') == "true":
            name = ADDON_SETTINGS.getSetting('1970s-movies-name')
            rule1 = 'year'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1969'
            operator2 = 'before'
            criteria2 = '1980'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('1980s-movies') == "true":
            name = ADDON_SETTINGS.getSetting('1980s-movies-name')
            rule1 = 'year'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1979'
            operator2 = 'before'
            criteria2 = '1990'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('1990s-movies') == "true":
            name = ADDON_SETTINGS.getSetting('1990s-movies-name')
            rule1 = 'year'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1989'
            operator2 = 'before'
            criteria2 = '2000'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('2000s-movies') == "true":
            name = ADDON_SETTINGS.getSetting('2000s-movies-name')
            rule1 = 'year'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '1999'
            operator2 = 'before'
            criteria2 = '2010'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('2010s-movies') == "true":
            name = ADDON_SETTINGS.getSetting('2010s-movies-name')
            rule1 = 'year'
            rule2 = ''
            operator1 = 'after'
            criteria1 = '2009'
            operator2 = 'before'
            criteria2 = '2020'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customMovieDecade1on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieDecade1') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Decade 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieDecade1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieDecade2on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieDecade2') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Decade 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieDecade2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieDecade3on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieDecade3') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Decade 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieDecade3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieDecade3on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieDecade4') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Decade 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieDecade4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieDecade4on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieDecade5') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Decade 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieDecade5"), '', '', '', '', '', '', '', ''))


######################################################
##
##  MOVIE RATING
##
######################################################

    def readMovieRatingPresetChannelConfig(self):
        self.log('Getting Movie Rating Presets ')
        # Shared Settings
        type = 'movies'
        limit = ADDON_SETTINGS.getSetting('limit2')
        random = ADDON_SETTINGS.getSetting('random2')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched2')
        nospecials = ''
        resolution = ADDON_SETTINGS.getSetting('resolution2')
        #
        if ADDON_SETTINGS.getSetting('child-movies') == "true":
            name = ADDON_SETTINGS.getSetting('child-movies-name')
            rule1 = 'mpaarating'
            rule2 = ''
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("Rated G")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('preteen-movies') == "true":
            name = ADDON_SETTINGS.getSetting('preteen-movies-name')
            rule1 = 'mpaarating'
            rule2 = ''
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("Rated PG")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('teen-movies') == "true":
            name = ADDON_SETTINGS.getSetting('teen-movies-name')
            rule1 = 'mpaarating'
            rule2 = ''
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("Rated PG-13")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('adult-movies') == "true":
            name = ADDON_SETTINGS.getSetting('adult-movies-name')
            rule1 = 'mpaarating'
            rule2 = ''
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("Rated R")
            criterias.append("Rated NC-17")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customMovieRating1on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieRating1') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Rating 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieRating1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieRating2on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieRating2') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Rating 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieRating2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieRating3on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieRating3') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Rating 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieRating3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieRating4on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieRating4') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Rating 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieRating4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieRating5on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieRating5') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Rating 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieRating5"), '', '', '', '', '', '', '', ''))


######################################################
##
##  MOVIE STUDIOS
##
######################################################

    def readMovieStudioPresetChannelConfig(self):
        # Movie Studio Channels
        self.log('Getting Movie Studio Presets ')
        # Shared Settings
        type = 'movies'
        limit = ADDON_SETTINGS.getSetting('limit2')
        random = ADDON_SETTINGS.getSetting('random2')
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched2')
        nospecials = ADDON_SETTINGS.getSetting('nospecials2')
        resolution = ADDON_SETTINGS.getSetting('resolution2')        
        #
        if ADDON_SETTINGS.getSetting('20th-century-fox') == "true":
            name = ADDON_SETTINGS.getSetting('20th-century-fox-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Twentieth Century")
            studios.append("20th Centry Fox")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('columbia-pictures') == "true":
            name = ADDON_SETTINGS.getSetting('columbia-pictures-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Columbia Pictures")
            studios.append("Columbia Pictures Corporation")
            studios.append("Columbia Pictures Industries")
            studios.append("Columbia Tristar")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('dreamworks') == "true":
            name = ADDON_SETTINGS.getSetting('dreamworks-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("DreamWorks")
            studios.append("DreamWorks SKG")
            studios.append("DreamWorks Animation")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('lionsgate') == "true":
            name = ADDON_SETTINGS.getSetting('lionsgate-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Lionsgate")
            studios.append("Lions Gate Family Entertainment")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('lucasfilm') == "true":
            name = ADDON_SETTINGS.getSetting('lucasfilm-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Lucasfilm")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('marvel') == "true":
            name = ADDON_SETTINGS.getSetting('marvel-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Marvel Enterprises")
            studios.append("Marvel Studios")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mgm') == "true":
            name = ADDON_SETTINGS.getSetting('mgm-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Metro-Goldwyn-Mayer")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mirage') == "true":
            name = ADDON_SETTINGS.getSetting('mirage-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Mirage Enterprises")
            studios.append("Mirage Studios")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('new-line') == "true":
            name = ADDON_SETTINGS.getSetting('new-line-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("New Line Cinema")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('orion') == "true":
            name = ADDON_SETTINGS.getSetting('orion-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Orion Pictures Corporation")
            studios.append("Orion Film")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('paramount') == "true":
            name = ADDON_SETTINGS.getSetting('paramount-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Paramount Pictures")
            studios.append("Paramount Famous Productions")
            studios.append("Paramount")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('pixar') == "true":
            name = ADDON_SETTINGS.getSetting('pixar-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Pixar Animation Studios")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('sony') == "true":
            name = ADDON_SETTINGS.getSetting('sony-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Sony")
            studios.append("Sony Pictures")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('universal-studios') == "true":
            name = ADDON_SETTINGS.getSetting('universal-studios-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Universal Studios")
            studios.append("Universal Pictures")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('united-artists') == "true":
            name = ADDON_SETTINGS.getSetting('united-artists-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("United Artists")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('warner-bros') == "true":
            name = ADDON_SETTINGS.getSetting('warner-bros-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Warner Bros. Pictures")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('disney') == "true":
            name = ADDON_SETTINGS.getSetting('disney-name')
            rule1 = 'studio'
            rule2 = ''
            operator1 = 'contains'
            studiolist = ''
            studios = []
            studios.append("Disney")
            studios.append("Walt Disney Pictures")
            studios.append("Walt Disney Company")
            studios.append("Walt Disney Feature Animation")
            studios.append("Walt Disney Studios Motion Pictures")
            for studio in studios:
                if studiolist == '':
                    studiolist = studio
                else:
                    studiolist = studiolist + '|' + studio
            criteria1 = studiolist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customMovieStudio1on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieStudio1') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Studio 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieStudio1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieStudio2on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieStudio2') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Studio 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieStudio2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieStudio3on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieStudio3') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Studio 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieStudio3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieStudio4on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieStudio4') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Studio 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieStudio4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMovieStudio5on')=="true":
            if ADDON_SETTINGS.getSetting('customMovieStudio5') <> "":
                self.presetChannels.append(presetChannel('Custom Movie Studio 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMovieStudio5"), '', '', '', '', '', '', '', ''))


######################################################
##
##  MIXED GENRES
##
######################################################

    def readMixedGenrePresetChannelConfig(self):
        self.log('Getting Mixed Presets ')
        # Shared Settings
        type = 'mixed'
        limit = ADDON_SETTINGS.getSetting('limit3')
        random = ADDON_SETTINGS.getSetting('random3')
        numepisodes = ADDON_SETTINGS.getSetting('numepisodes')
        nummovies = ADDON_SETTINGS.getSetting('nummovies')
        unwatched = ADDON_SETTINGS.getSetting('unwatched3')
        nospecials = ADDON_SETTINGS.getSetting('nospecials3')
        resolution = ADDON_SETTINGS.getSetting('resolution3')
        #
        if ADDON_SETTINGS.getSetting('mixed-action') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-action-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("action")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("action")
            criterias.append("adventure")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-animation') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-animation-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("animation")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("animation")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-comedy') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-comedy-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("comedy")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("comedy")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-documentary') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-documentary-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("documentary")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("documentary")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-drama') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-drama-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("drama")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("drama")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-family') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-family-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("family")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("family")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-fantasy') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-fantasy-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("fantasy")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("fantasy")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-science-fiction') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-science-fiction-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("science-fiction")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("science-fiction")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-sport') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-sport-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("sport")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("sport")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-western') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-western-name')
            rule1 = 'genre'
            operator1 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("western")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            rule2 = 'genre'
            operator2 = 'is'
            criterialist = ''
            criterias = []
            criterias.append("western")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria2 = criterialist
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customMixedGenre1on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedGenre1') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Genre 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedGenre1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedGenre2on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedGenre2') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Genre 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedGenre2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedGenre3on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedGenre3') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Genre 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedGenre3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedGenre4on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedGenre4') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Genre 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedGenre4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedGenre5on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedGenre5') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Genre 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedGenre5"), '', '', '', '', '', '', '', ''))


######################################################
##
##  MIXED DECADES
##
######################################################

    def readMixedDecadePresetChannelConfig(self):
        self.log('Getting Mixed Presets ')
        # Shared Settings
        type = 'mixed'
        limit = ADDON_SETTINGS.getSetting('limit3')
        random = ADDON_SETTINGS.getSetting('random3')
        numepisodes = ADDON_SETTINGS.getSetting('numepisodes')
        nummovies = ADDON_SETTINGS.getSetting('nummovies')
        unwatched = ADDON_SETTINGS.getSetting('unwatched3')
        nospecials = ADDON_SETTINGS.getSetting('nospecials3')
        resolution = ADDON_SETTINGS.getSetting('resolution3')

        if ADDON_SETTINGS.getSetting('mixed-1950s') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-1950s-name')
            rule1 = 'airdate' # episodes
            rule2 = 'year' # movies
            operator1 = 'after'
            criteria1 = '1949-12-31'
            operator2 = 'before'
            criteria2 = '1960-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-1960s') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-1960s-name')
            rule1 = 'airdate' # episodes
            rule2 = 'year' # movies
            operator1 = 'after'
            criteria1 = '1959-12-31'
            operator2 = 'before'
            criteria2 = '1970-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-1970s') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-1970s-name')
            rule1 = 'airdate' # episodes
            rule2 = 'year' # movies
            operator1 = 'after'
            criteria1 = '1969-12-31'
            operator2 = 'before'
            criteria2 = '1980-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-1980s') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-1980s-name')
            rule1 = 'airdate' # episodes
            rule2 = 'year' # movies
            operator1 = 'after'
            criteria1 = '1979-12-31'
            operator2 = 'before'
            criteria2 = '1990-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-1990s') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-1990s-name')
            rule1 = 'airdate' # episodes
            rule2 = 'year' # movies
            operator1 = 'after'
            criteria1 = '1989-12-31'
            operator2 = 'before'
            criteria2 = '2000-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-2000s') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-2000s-name')
            rule1 = 'airdate' # episodes
            rule2 = 'year' # movies
            operator1 = 'after'
            criteria1 = '1999-12-31'
            operator2 = 'before'
            criteria2 = '2010-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-2010s') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-2010s-name')
            rule1 = 'airdate' # episodes
            rule2 = 'year' # movies
            operator1 = 'after'
            criteria1 = '2009-12-31'
            operator2 = 'before'
            criteria2 = '2020-01-01'
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customMixedDecades1on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedDecades1') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Decade 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedDecades1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedDecades2on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedDecades2') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Decade 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedDecades2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedDecades3on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedDecades3') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Decade 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedDecades3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedDecades4on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedDecades4') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Decade 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedDecades4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedDecades5on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedDecades5') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed Decade 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedDecades5"), '', '', '', '', '', '', '', ''))

######################################################
##
##  MIXED TV SHOWS
##
######################################################

    def readMixedTVShowPresetChannelConfig(self):
        # Mixed TV Show Presets
        self.log('Getting Mixed TV Show Presets ')
        # Shared Settings
        type = 'episodes'
        limit = ADDON_SETTINGS.getSetting('limit1')
        random = False
        numepisodes = ''
        nummovies = ''
        unwatched = ADDON_SETTINGS.getSetting('unwatched1')
        nospecials = ADDON_SETTINGS.getSetting('nospecials1')
        resolution = ''        

        if ADDON_SETTINGS.getSetting('mixed-star-trek') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-star-trek-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Star Trek")
            criterias.append("Star Trek: Deep Space Nine")
            criterias.append("Star Trek: Enterprise")
            criterias.append("Star Trek: The Animated Series")
            criterias.append("Star Trek: The Next Generation")
            criterias.append("Star Trek: Voyager")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('mixed-stargate') == "true":
            name = ADDON_SETTINGS.getSetting('mixed-stargate-name')
            type = 'episodes'
            rule1 = 'tvshow'
            rule2 = ''
            operator1 = 'is'
            # setup array of tv shows
            criterialist = ''
            criterias = []
            criterias.append("Stargate Atlantis")
            criterias.append("Stargate SG-1")
            criterias.append("Stargate Universe")
            for criteria in criterias:
                if criterialist == '':
                    criterialist = criteria
                else:
                    criterialist = criterialist + '|' + criteria
            criteria1 = criterialist
            operator2 = ''
            criteria2 = ''
            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))

        if ADDON_SETTINGS.getSetting('customMixedTVShow1on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedTVShow1') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed TV Show 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedTVShow1"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedTVShow2on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedTVShow2') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed TV Show 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedTVShow2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedTVShow3on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedTVShow3') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed TV Show 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedTVShow3"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedTVShow4on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedTVShow4') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed TV Show 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedTVShow4"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMixedTVShow5on')=="true":
            if ADDON_SETTINGS.getSetting('customMixedTVShow5') <> "":
                self.presetChannels.append(presetChannel('Custom Mixed TV Show 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMixedTVShow5"), '', '', '', '', '', '', '', ''))


######################################################
##
##  MIXED RATING
##
######################################################

    def readMixedRatingPresetChannelConfig(self):
        self.log('Getting Mixed Presets ')
        # Shared Settings
        type = 'mixed'
        limit = ADDON_SETTINGS.getSetting('limit3')
        random = ADDON_SETTINGS.getSetting('random3')
        numepisodes = ADDON_SETTINGS.getSetting('numepisodes')
        nummovies = ADDON_SETTINGS.getSetting('nummovies')
        unwatched = ADDON_SETTINGS.getSetting('unwatched3')
        nospecials = ADDON_SETTINGS.getSetting('nospecials3')
        resolution = ADDON_SETTINGS.getSetting('resolution3')

#        if ADDON_SETTINGS.getSetting('mixed-child') == "true":
#            name = ADDON_SETTINGS.getSetting('mixed-child-name')
#            rule1 = 'genre' # episodes
#            rule2 = 'mpaarating' # movies
#            operator1 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("Children")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria1 = criterialist
#            operator2 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("Rated G")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria2 = criterialist
#            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
#        if ADDON_SETTINGS.getSetting('mixed-preteen') == "true":
#            name = ADDON_SETTINGS.getSetting('mixed-preteen-name')
#            rule1 = 'rating'
#            rule2 = ''
#            operator1 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("TV-Y7")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria1 = criterialist
#            operator2 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("G")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria2 = criterialist
#            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
#        if ADDON_SETTINGS.getSetting('mixed-teen') == "true":
#            name = ADDON_SETTINGS.getSetting('mixed-teen-name')
#            rule1 = 'rating'
#            rule2 = ''
#            operator1 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("TV-PG")
#            criterias.append("TV-14")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria1 = criterialist
#            operator2 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("PG-13")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria2 = criterialist
#            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
#        if ADDON_SETTINGS.getSetting('mixed-adult') == "true":
#            name = ADDON_SETTINGS.getSetting('mixed-adult-name')
#            rule1 = 'genre'
#            rule2 = ''
#            operator1 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("TV-MA")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria1 = criterialist
#            operator2 = 'is'
#            criterialist = ''
#            criterias = []
#            criterias.append("R")
#            criterias.append("NC-17")
#            for criteria in criterias:
#                if criterialist == '':
#                    criterialist = criteria
#                else:
#                    criterialist = criterialist + '|' + criteria
#            criteria2 = criterialist
#            self.presetChannels.append(presetChannel(name, type, rule1, rule2, operator1, operator2, criteria1, criteria2, limit, random, numepisodes, nummovies, unwatched, nospecials, resolution))
        if ADDON_SETTINGS.getSetting('customMix1on')=="true":
            if ADDON_SETTINGS.getSetting('customMix1') <> "":
                self.presetChannels.append(presetChannel('Custom Mix 1','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMix2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMix2on')=="true":
            if ADDON_SETTINGS.getSetting('customMix2') <> "":
                self.presetChannels.append(presetChannel('Custom Mix 2','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMix2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMix2on')=="true":
            if ADDON_SETTINGS.getSetting('customMix2') <> "":
                self.presetChannels.append(presetChannel('Custom Mix 3','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMix2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMix2on')=="true":
            if ADDON_SETTINGS.getSetting('customMix2') <> "":
                self.presetChannels.append(presetChannel('Custom Mix 4','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMix2"), '', '', '', '', '', '', '', ''))
        if ADDON_SETTINGS.getSetting('customMix2on')=="true":
            if ADDON_SETTINGS.getSetting('customMix2') <> "":
                self.presetChannels.append(presetChannel('Custom Mix 5','custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting("customMix2"), '', '', '', '', '', '', '', ''))


######################################################
##
##  CUSTOM
##
######################################################

    def readCustomPresetChannelConfig(self):
                
        for i in range(1,250):
            settingNameCustomOn = 'custom' + str(i) + 'on'
            settingNameCustom = 'custom' + str(i)
            if ADDON_SETTINGS.getSetting(settingNameCustomOn) == "true":
                self.log("readChannelConfig: " + str(settingNameCustomOn) )
                self.log(settingNameCustomOn + ": " + ADDON_SETTINGS.getSetting(settingNameCustomOn))
                if ADDON_SETTINGS.getSetting(settingNameCustom) <> "":
                    self.log("Adding custom channel")
                    self.presetChannels.append(presetChannel('Custom ' + str(i),'custom', '', 'playlist', '', '', ADDON_SETTINGS.getSetting(settingNameCustom), '', '', '', '', '', '', '', ''))            
            i = i + 1

        