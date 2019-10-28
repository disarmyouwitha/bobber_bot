# [bobber_bot]:
WoW Classic fishing bot.. for OSX.. for funzies. (wrapping up cross-platform support meow)

This bot is (more or less) finished now! I achieved pretty solid tracking once HSV threshold of the bobber / tooltip is configured~
(The script will step you through configuration the first time it runs -- you want only the bobber/tooltip to be selected in white)
I've been bringing in bag fulls of fish a night and just kicking back making improvements. =]


One of two things that might throw things into upheaval is.. if your `Render Scale` is not set to 50% -- This script has all been developed / tested on my macbook, which uses 2880x1800 @ 50% Render Scale. (This is important because certain functions calculating mouse position are using mod=2, etc that would need to change if you aren't using 50% render scale)

The other tricky part is setting up the sound.. `listen_splash()` is using the speaker's output to detect the sound of the splash -- This takes some setup (with Soundflower on OSX) or by creating a Mixer on windows.. I will honestly have to do more research/post better steps for this later. 
_If you don't want to use the speakers input, you can optionally use the mic from say, your macbook, but tbh I found this super annoying._


# [thresh.py]:
> Running this script will start the "main loop" which will take you through calibration, then start the bot!

# [audio.py]:
> A small test script to make sure you are recording sound from your Input source. (Mic/Speakers)

> Used to figure out the indexes/threshold if the preset ones dont work for you!


# [AT THE MOMENT]:
> The bot will cast `Baubles from "9"` onto `fishing pole on "7"` when it starts, then use the `fishing skill on "8"`.
> ^(Optionally you can enable `_mouse_mode=True` to only use the mouse for fishing actions and it will walk you through calibration -- allowing you to type to your guild, etc, if you are a chatter-bug like me =3)

> The bot will start listening when started. This is the main loop -- when a SPLASH is detected, it will try to catch/recast 

> The bot will track the bobber by using the HSV threshold set during calibration.. this usually only takes a few gueses.

> It verifies that it has found the bobber by checking the location of the `Fishing Bobber` tooltip when the bobber is moused-over.

# [HIGHLY RECOMMENDED]:
# DLMS took care of most of my problems..
# DOWNLOAD ADDON: https://www.warcrafttavern.com/addons/dlms-dynamic-loot-management-system/
> I use this, rather than autosell, to blacklist trash fish that would otherwise fill up my inventory.

# [Python3 modules used]:

# OSX:
> brew install python3

> brew install portaudio

> python -m pip install pyaudio

> install Soundflower-2.0b2.dmg from install_files (OR..)
> https://github.com/mattingalls/Soundflower/releases/download/2.0b2/Soundflower-2.0b2.dmg

# WINDOWS:
> install python-3.7.5-amd64-webinstall.exefrom install_files

> install PyAudio.msi from install_files

> python -m pip install mss

> python -m pip install install_files/pyHook-1.5.1-cp37-cp37m-win_amd64.whl

# BOTH NEED:
> python -m pip install numpy

> python -m pip install imageio

> python -m pip install playsound

> python -m pip install pyautogui

> python -m pip install PyUserInput

> python -m pip install scikit-image       

> python -m pip install opencv-python