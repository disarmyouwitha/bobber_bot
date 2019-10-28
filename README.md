# [bobber_bot]:
WoW Classic fishing bot.. for funzies.

This bot is basically finished now! I achieved pretty solid tracking once HSV threshold of the bobber / tooltip is configured~
(The script will step you through configuration each time it runs -- you want only the bobber/parts of the bobber to be selected in white)
I've been bringing in bag fulls of fish each night and just kicking back making improvements. =]

One thing that might throw things into upheaval is.. if your `Render Scale` is not set to 50% -- This script has all been developed / tested on my macbook, which uses 2880x1800 @ 50% Render Scale. (This is important because certain functions calculating mouse position are using mod=2, etc that would need to be changed if you are not using 50% render scale)

The other tricky part is setting up the sound.. `audio_callback()` is using the speaker's output to detect the sound of the splash -- This takes some setup with Soundflower on OSX, or by creating a Sound Mixer on windows.. I've included the steps below to help set that up!

# [AT THE MOMENT]:
> The bot will cast `fishing pole on "7"` when it starts, then use the `fishing skill on "8"`.
> ^(Optionally, you can enable `_use_baubles=True` to cast baubles every 10min: `Baubles on "9"` )
> ^(Optionally, you can enable `_use_mouse_mode=True` to only use the mouse for fishing actions and it will walk you through calibration -- allowing you to type to your guild, etc, if you are a chatter-bug like me =3)

> The bot will start listening when started. This is the main loop -- when a SPLASH is detected, it will try to catch/recast 

> The bot will track the bobber by using the HSV threshold set during calibration.. this usually only takes a few gueses.

> It verifies that it has found the bobber by checking the location of the `Fishing Bobber` tooltip when the bobber is moused-over.


# [Setting up audio_callback for OSX]:
> [0]: Install Soundflower:
>      https://github.com/mattingalls/Soundflower/releases/download/2.0b2/Soundflower-2.0b2.dmg
>      OR `install_files/Soundflower-2.0b2.dmg`

> [1]: Click your speaker from osx toolbar and select "Soundflower (2ch)" from the dropdown. 

> [2]: And you should be done! Use `audio.py` to figure out what index your Soundflower device is!


# [SETTING up audio_callback for WINDOWS]:
> [0]: Open Sound panel (Type "Sound" into system search)

> [1]: Select Speakers as the default playback device

> [2]: Go to the "Recording" tab

> [3]: Right click and enable "Show Disabled Devices"

> [4]: A recording device called "Wave Out Mix", "Mono Mix" or "Stereo Mix" (this was my case) should appear

> [5]: Right click on the new device and click "Enable"

> [6]: Right click on the new device and click "Set as Default Device"

> [7]: Double click on the new device to open the Properties window

> [8]: Go to the "Listen" tab

> [9]: Click on the "Listen to this device" checkbox

> [10]: Select your Speakers from the "Playback through this device" list

> And you should be done! Use `audio.py` to figure out what index your Sound Mixer device is!]


# [audio.py]:
> A small test script to make sure you are recording sound from your Input source. (Mic/Speakers)

> Used to figure out the indexes/threshold if the preset ones dont work for you!

# [thresh.py]:
> Running this script will start the "main loop" which will take you through calibration, then start the bot!



# [HIGHLY RECOMMENDED]:
# DLMS took care of most of my problems..
# DOWNLOAD ADDON: https://www.warcrafttavern.com/addons/dlms-dynamic-loot-management-system/
> I use this, rather than autosell, to blacklist trash fish that would otherwise fill up my inventory.



# [INSTALLING MODULES]:

# [OSX]:
> brew install python3

> brew install portaudio

> python -m pip install pyaudio

> install Soundflower-2.0b2.dmg from install_files (OR..)
> https://github.com/mattingalls/Soundflower/releases/download/2.0b2/Soundflower-2.0b2.dmg

# [WINDOWS]:
> install `python-3.7.5-amd64-webinstall.exe` from install_files

> install `PyAudio-0.2.11.win-amd64-py3.7.msi` from install_files

> python -m pip install `pyHook-1.5.1-cp37-cp37m-win_amd64.whl` from install_files

> python -m pip install mss


# [BOTH NEED]:
> python -m pip install numpy

> python -m pip install imageio

> python -m pip install playsound

> python -m pip install pyautogui

> python -m pip install PyUserInput

> python -m pip install scikit-image

> python -m pip install opencv-python