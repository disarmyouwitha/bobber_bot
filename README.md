# [bobber_bot]:
WoW Classic fishing bot.. for OSX.. for funzies.

This bot is not finished, but coming along nicely.. I have achieved pretty solid tracking once HSV threshold is configured.
(The script will step you through configuration the first time it runs -- you want only the bobber/tooltip to be selected in white)

I'm *pretty sure* this only works on OSX right now, however `ScreenPixel.capture()` is the only function that I think would need to be re-written for Windows, as it's using tightly optimized screen grab code for OSX right now. (Sorry Windows, yall got all the cool C hooks, so there is plenty of code you can use for this -- send me a Pull Request :P)

The other thing that might throw things into upheaval is if your `Resolution Scale` is not set to 50% -- This  script has all been developed / tested on my macbook, which.. uses 2880x1800 @ 50% resolution scale. (Certain functions calculating mouse position are using mod=2, etc that would need to change otherwise)


# [thresh.py]:
> Running this script and left clicking will start the "main loop" which will take you through calibration. 
> After calibrating you can start the bot and it will press "8" to fish and begind to track the bobber.
# [AT THE MOMENT]: 
> > The bot will cast `Baubles from "9"` onto `fishing pole on "7"` when it starts, then use the `fishing skill on "8"`.
> > It will track the bobber by using the HSV threshold set during calibration.. this usually only takes a few gueses.
> > It verifies that it has found the bobber by checking the location of the `Fishing Bobber` tooltip when the bobber is moused-over.
> > Once the bobber is found it enters a ~25 second loop where it's listening for the SPLASH sound using a volume threshold.
^ (This file may eventually be renamed, once I get everything working)~

# [Python3 re-write]:
> brew install portaudio
> python3 -m pip install pyaudio
> python3 -m pip install imageio
> python3 -m pip install pyautogui
> python3 -m pip install playsound
> python3 -m pip install opencv-python
> > https://github.com/mattingalls/Soundflower # Enables piping system output to virtual input