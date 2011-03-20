TVTimefor XBMC


-----------
What is it?
-----------
    It's a modification of the pseudoTV script created by Jason Anderson.  It's channel-surfing for your media center.  Never again will you have to actually pick what you want to watch.  Use an electronic program guide (EPG) to view what's on or select a show to watch.  This script will let you create your own channels and, you know, watch them.  Doesn't actually sound useful when I have to write it in a readme.  Eh, try it and decide if it works for you.

TVTime adds a new channel management system to make adding new channels as simple as enabling it in the add-on settings.  The new channel management system can automatically import your existing Channel_x files located in the video and mixed playlist folder allowing users to use previous channel configuration and/or the new system.

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


Auto Channel Creation via Channel Management System:

XBMC added a new Channel Management System to Jason Anderson's pseudoTV script.  The Channel Management System is located in the Add-on Settings.  There are over 200 predefined channels to chose from organized into various groups:  TV Genres, TV Decades, TV Networks, TV Shows, Movie Genres, Movie Decades, Movie Studios, Mixed Genre, and Mixed Decades.  Each group can be assigned 5 custom channels based on a manually created playlist (see below).  In addition, you can assign up to 100 custom playlists to the custom channels.

If you have created Channel_x playlists which you used in pseudoTV, they will automatically be imported and assigned to the custom channels (1-100).  If you have more than 100 custom channels, the script will still import all your channels, but only 1-100 will be viewable via the Channel Management System.

In addition to selecting which channel to enable in each group, you also can set general settings for TV Channels, Movie Channels and Mixed Channels.  This is where you can define the number of episodes or movies to get for each channel in those groups as well as whether you want to watch specials, previously watched, what resolution of movies, and whether you want the episodes randomized.  Tip:  All channels should be randomized except for TV Shows. If you want to watch the TV Show in order, then do not enable Randomize for TV Shows.


Manually creating channels:

Each channel is really just a smart playlist.  The name of the playlist is also the name your channel will have (that should be a feature...maybe I'll add it at some point).  This part is important: when it asks you what the filename of the playlist should be, name it "Channel_x" where 'x' is the number of the channel.  If you have made
channels 1 and 2, though, don't skip to 4.  You must have sequential numbers or things will not work the way you'd like.
    So when this thing starts up for the first time, it will read your play-lists in the video and mixed playlists folder and auto-configure these as custom channels in the channel management system.  Depending on how many channels you have and how many items are in each, this may take a couple of minutes.  After the first
time, channels will only be updated occasionally.  Don't worry about when or why, just trust that it happens sometimes.  If you do care, you can modify the
setting in the configuration.


--------
Controls
--------
    There are only a few things you need to know in order to control every-thing.  First of all, the Stop button ('X') stops the video and exits the script.  Scroll through channels using the arrow up and down keys, or alternatively by pressing Page up or down.
    To open the EPG, press the Select key ('Enter').  Move around using the arrow keys.  Start a program by pressing Select.  Pressing Previous Menu ('Escape') will close the EPG.
    Press 'I' to display or hide the info window.  When it is displayed, you can look at the previous and next shows on this channel using arrow left and right.


--------
Settings
--------
    Idle-Timer: The amount of time (in minutes) of idle time before the script is automatically stopped.

    Info when Changing Channels: Pops up a small window on the bottom of the screen where the current show information is displayed when changing channels.

    Force Channel Reset: If you want your channels to be reanalyzed then you can turn this on.

    Time Between Channel Resets: This is how often your channels will be reset. Generally, this is done automatically based on the duration of the individual channels and how long they've been watched.  You can change this to reset every certain time period (day, week, month).

    Fill in Custom Channels: If enabled, it will import your custom Channel_x playlists and assign them to Custom Channels (1-100) in the Channel Management System.

    Show Channel Logo: Always display the current channel logo.


-------
Credits
-------
Developers: Jason102 (original pseudoTV script), jtucker1972 (channel management system)
Code Additions: Sranshaft, TheOddLinguist
Skins: Sranshaft, Zepfan
Preset Playlists and Images: Jtucker1972