# bobber_bot
WoW Classic fishing bot.. for OSX.. for funzies.

This bot is not finished, but coming along nicely.. I have achieved pretty solid tracking once HSV threshold is configured.
(The script will step you through configuration the first time it runs -- you want only the bobber/tooltip to be selected in white)

I'm *pretty sure* this only works on OSX right now, however `ScreenPixel.capture()` is the only function that I think would need to be re-written for Windows, as it's using tightly optimized screen grab code for OSX right now. (Sorry Windows, yall got all the cool C hooks, so there is plenty of code you can use for this -- send me a Pull Request :P)

thresh.py | Running this script and left clicking will start the "main loop" which will take you through calibration. 
            After calibrating you can start the bot and it will press "8" to fish and begind to track the bobber.
            AT THE MOMENT: The bot is just putting the mouse over the bobber and "tracking" it for 30 seconds -- I'm working on splash detection now, but if you just want to see how fast it can locate a bobber.. change track_bobber() to right click rather than waiting 30seconds in a while loop =]
            ^ (This file will eventually be renamed, once I get everything working)~

sssim.py  | just a testing script with comments for notes. Will be cleaned out eventually.