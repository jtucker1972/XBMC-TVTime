TVTime for XBMC


-----------
What is it?
-----------
    TV Time is a major modification of the pseudoTV script created by Jason Anderson.  It's channel-surfing for your media center.  Never again will you have to actually pick what you want to watch or listen to.  Use an electronic program guide (EPG) to view what's on or select a show to watch.  This script will let you create your own channels and, you know, watch them.  Doesn't actually sound useful when I have to write it in a readme.  Eh, try it and decide if it works for you.


--------
Features
--------
    - Automatic channel creation via a new channel management system.
    - Optionally customize the channels you want with smart playlists.
    - Use an EPG and view what was on, is on, and will be on.  Would you rather see something that will be on later?  Select it and watch it now!
    - Want to pause a channel while you watch another?  And then come back to it and have it be paused still?  Sounds like a weird request to me, but if you want to do it you certainly can.  It's a feature!
    - An idle-timer makes sure you aren't spinning a hard-drive needlessly all night.
    - Discover the other features on your own (so that I don't have to list them all...I'm lazy).


-----
Setup
-----
    First, install it.  This is self-explanatory (hopefully).  Really, that's all that is necessary.  Default channels will be created without any intervention.  You can choose to setup channels (next step) if you wish.

    Instructions to create your own channels.  Go to Add-on Settings and enable or disable the channels you want to use.  You can define how many episodes and movies to get for the channels as well as the ration of episodes and movies for mixed channels.  

Auto Channel Creation via Enhanced Channel Configuration Wizard:

PseudoTV added a new Channel Configuration Tool.  TV Time has enhanced this new Channel Configuration tool to provide additional channel configuration options.  The Channel Configuration Tool is located in the Add-on Settings.


--------
Controls
--------
    There are only a few things you need to know in order to control every-thing.  First of all, the Stop button ('X') stops the video and exits the script.  Scroll through channels using the arrow up and down keys, or alternatively by pressing Page up or down.
    To open the EPG, press the Select key ('Enter').  Move around using the arrow keys.  Start a program by pressing Select.  Pressing Previous Menu ('Escape') will close the EPG.
    Press 'I' to display or hide the info window.  When it is displayed, you can look at the previous and next shows on this channel using arrow left and right.
    Press 'M' to displey the OSD to enable/disable subtitles, etc.


--------
General Settings
--------
    Idle-Timer: The amount of time (in minutes) of idle time before the script is automatically stopped.

    Info when Changing Channels: Pops up a small window on the bottom of the screen where the current show information is displayed when changing channels.

    Force Channel Reset: If you want your channels to be reanalyzed then you can turn this on.

    Time Between Channel Resets: This is how often your channels will be reset. Generally, this is done automatically based on the duration of the individual channels and how long they've been watched.  You can change this to reset every certain time period (day, week, month or scheduled).  If scheduled, you can select how often Daily, Weekly or Monthly and the hour to run the channel reset.  If scheduled, you can also enable the option to exit XBMC after the reset has completed.

    Show Channel Logo: Always display the current channel logo.

    Channel Logo Folder: Select an optional folder which contains your custom channel logos


--------
Channels Settings
--------
    Channel Configuration: opens the Channgel Configuration Wizard where you can manually configure your channels and configure advanced settings.

    Auto Tune Settings: when enabled, TV Time will automatically search and add channels based on your XBMC library information.

    Channel Limit:  set the number of episodes and/or movies to add for each channel.


--------
Off Air Settings
--------
    Off Air: Adds an "off air" video file that you select when no files are found for a channel.


--------
Bumpers Settings
--------
    Enable Bumpers:  When enabled, TV Time will insert bumpers between shows.

    Bumpers Folder:  Folder where the bumper videos are found.  Bumpers are channel specific, so the video files need to be organized into subfolders matching the channel name.  For example, C:\Bumpers\ABC, C:\Bumpers\Comedy Central, etc.

    Number of Bumpers to Show: Number of bumper videos to insert between shows.  If auto, TV Time will determine when to insert a bumper based on a ratio of the number of bumpers available and the number of shows in the channel

   Maximum Number of Bumpers:  If Number of Bumpers set to Auto, this setting limits the maximum number of bumpers to insert between shows to the number selected.


--------
Commercials Settings
--------
    Enable Commercials:  When enabled, TV Time will insert commercials between shows.

    Commercials Folder:  Folder where the commercial videos are found.  

    Number of Commercials to Show: Number of commercial videos to insert between shows.  If auto, TV Time will determine when to insert a commercial based on a ratio of the number of bumpers available and the number of shows in the channel

   Maximum Number of Commercials:  If Number of Commercials set to Auto, this setting limits the maximum number of commercials to insert between shows to the number selected.


--------
Trailers Settings
--------
    Enable Trailers:  When enabled, TV Time will insert trailers between movies.  Only applies to Movie channels.  It is pretty simplistic in version 2.0.  No trailer by genre or rating yet.

    Trailers Folder:  Folder where the trailer videos are found.  

    Number of Trailers to Show: Number of trailer videos to insert between movies.  If auto, TV Time will determine when to insert a bumper based on a ratio of the number of bumpers available and the number of shows in the channel

   Maximum Number of Trailers:  If Number of Trailers set to Auto, this setting limits the maximum number of trailers to insert between shows to the number selected.


--------
Channel Configuration
--------
    Channel Types:  
	TV Network - ABC, CBS, NBC, etc.
	Movie Studio - Paramount, Lionsgate, Lucasfilm, etc.
	TV Genre - Animation, Comedy, Drama, etc.
	Movie Genre - Action, Crime, Family, etc.
	Mixed Genre - Animation, Comedy, Fantasy, etc.
	TV Show - 24, Star Trek, Doctor Who, etc.
	Folder - E:\Childrens Videos, etc.
	Music Genre - Classic Rock, Classical, Country, etc.
	None - clears the channel

    Resolution:
	All - include all resolutions
	SD Only - only include SD resolutions (less than 720p)
	720p or Higher - only include HD resolutions
	1080p - only include 1080p HD resolutions

    Unwatched Only: Only include unwatched shows

    No Specials: Do not include specials

    Randomize TV Shows: Randomize the order TV Shows appear (Only valid for TV Network Channel Type)

    Serial Mode:  When enabled shows are ordered by airdate. (Only valid for TV Network Channel Type)


-------
Credits
-------
Developers: Jason102 (original pseudoTV script), jtucker1972 (TV Time script)
Code Additions: Sranshaft, TheOddLinguist
Skins: Sranshaft, Zepfan
Preset Playlists and Images: Jtucker1972