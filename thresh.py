import os
import sys
import cv2
import json
import time
import numpy
import pyaudio
import imageio
import pyautogui
import playsound
import contextlib
import skimage.metrics

# [Import local classes]:
import screen_pixel
import mouse_calibrator

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))

# [Callback for splash detection!]:
def audio_callback(in_data, frame_count, time_info, status):
    try:
        data = numpy.frombuffer(in_data ,dtype=numpy.int16)

        # [Waits for bot to start before listening for audio]:
        if bb._timer_start is not None:
            
            peak = numpy.average(numpy.abs(data))*2
            peak = int(peak)

            if peak > bb._audio_threshold and bb._splash_detected==False:
                if bb._bobber_found:
                    #print('Splash detected, with bobber: {0}'.format(peak))
                    bb._catch_cnt+=1
                else:
                    #print('Splash detected, no bobber: {0}'.format(peak))
                    bb._miss_cnt+=1

                bb._splash_detected=True
                bb._bobber_reset=True

        return data, pyaudio.paContinue

    except pyautogui.FailSafeException:
        bb._bobber_reset=True
        bb._audio_stream.stop_stream()
        bb._audio_stream.close()
        bb.pa.terminate()

        # [Die Young && Leave beautiful code]:
        print('Run time: {0} min'.format((time.time()-bb._bot_start)/60))
        print('Catch count: {0}'.format(bb._catch_cnt))
        print('Miss count:  {0}'.format(bb._miss_cnt))

        _exit = input('[Do you wish to exit?]')
        _exit = False if (_exit.lower() == 'n' or _exit.lower() == 'no') else True
        if _exit:
            print('[Bye!]')
            sys.exit(1)

class bobber_bot():
    # [Included Classes]:
    sp = None
    pa = None

    # [BobberBot Globals]:
    _miss_cnt = 0
    _catch_cnt = 0
    _count_cnt = 0
    _fishing = True
    _timeout_cnt = 0
    _bot_start = None
    _timer_start = None
    _timer_elapsed = 30
    _audio_stream = None
    _bauble_start = None
    _bauble_elapsed = 660
    _bobber_reset = False
    _bobber_found = False
    _audio_threshold = 2000
    _splash_detected = False
    _fishing_pole_loc = None
    _fishing_pole_key = None
    _fishing_skill_loc = None
    _fishing_skill_key = None
    _fishing_bauble_loc = None
    _fishing_bauble_key = None

    # [BobberBot Settings]:
    _use_baubles = False
    _use_mouse_mode = False # Uses only mouse calls, so you can chat/use the keyboard while it's running.

    def __init__(self):
        self.sp = screen_pixel.screen_pixel()
        self.pa = pyaudio.PyAudio()
        self.setup_audio()

    def setup_audio(self):
        if sys.platform == 'darwin':
            dev_idx = 2 # For my OSX machine it's 2, might be different for you
        else:
            dev_idx = 1 # For my windows machine it's 1, might be different for you
        # ^(System Dependant, use audio.py to configure)

        self._audio_stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, input_device_index=dev_idx, stream_callback=audio_callback)

    def cast_pole(self):
        # [Check to apply bauble]:
        if self._use_baubles:
            self.bauble_check()

        self._timer_elapsed = 0
        self._timer_start = time.time()

        # [Use Fishing skill]:
        if self._use_mouse_mode:
            time.sleep(2)
            pyautogui.click(x=self._fishing_skill_loc.get('x'), y=self._fishing_skill_loc.get('y'), button='left', clicks=1)
        else:
            pyautogui.typewrite(self._fishing_skill_key)

        time.sleep(3) # Wait so that we don't try and find old bobber as it fades (? needed now?)
        self._bobber_reset = True
        self._bobber_found = False
        self._splash_detected = False
        self._count_cnt = 0

    def bauble_check(self):
        if self._splash_detected:
            time.sleep(2) # If we caught a fish, a small delay before trying to apply bauble to make sure we aren't interrupted
        if self._bauble_elapsed >= 630: # 10min (and 30secs)
            if self._use_mouse_mode:
                # [Click Fishing bauble]:
                pyautogui.click(x=self._fishing_bauble_loc.get('x'), y=self._fishing_bauble_loc.get('y'), button='left', clicks=1)
                # [Click Fishing pole]:
                pyautogui.click(x=self._fishing_pole_loc.get('x'), y=self._fishing_pole_loc.get('y'), button='left', clicks=1)
            else:
                pyautogui.typewrite(self._fishing_bauble_key) # fishing bauble on action bar
                pyautogui.typewrite(self._fishing_pole_key) # fishing pole on action bar

            time.sleep(10) # sleep while casting bauble~
            self._bauble_elapsed = 0
            self._bauble_start = time.time()
        self._bauble_elapsed = (time.time() - self._bauble_start)

    def check_login(self):
        #[Capture Login Rect]:
        print('[Checking for login screen / Checking for disconnect] 2sec..')
        time.sleep(2)

        # [Uses `mod=2` because mouse_pixel is half of screen_pixel]: (?)
        if sys.platform == 'darwin':
            nemo = self.sp.grab_rect({"x": 420, "y": 394}, {"x": 1013, "y": 673}, mod=2)
        else:
            nemo = self.sp.grab_rect({"x": 420, "y": 394}, {"x": 1013, "y": 673}, mod=1) #MOD2?

        # [Convert images to grayscale]:
        gray_test = cv2.cvtColor(nemo, cv2.COLOR_BGR2GRAY)
        gray_control = imageio.imread('img/login_control_gray.png')

        (score, diff) = skimage.metrics.structural_similarity(gray_control, gray_test, full=True)
        #diff = (diff * 255).astype("uint8")

        print("SSIM: {}".format(score))
        return True if (score > .90) else False

    # We have determined that we have disconnected.. How to reconnect?
    def reconnect(self):
        login_clear = self.check_login()

        if login_clear:
            if os.path.isfile('configs/pass.txt'):
                with open('configs/pass.txt') as f:
                    _pass = f.read().strip()

                    # [Clear login from casting attempts]:
                    for x in range(0, self._timeout_cnt):
                        pyautogui.press('backspace')

                    # [Enter password]:
                    pyautogui.typewrite(_pass)
                    pyautogui.press('enter')

                    # Delay(15s) for login / Hit Enter to login as character:
                    time.sleep(15)
                    pyautogui.press('enter')

                    # [Check if bot is dead / go ahead and exit xD]:
                    time.sleep(15)
                    if self.is_dead():
                        return -1
                    else:
                        return 1
        else:
            # Hit ESC to clear dialog / rather than clicking okay:
            pyautogui.press('esc')

        return 0

    # [Try to clear disconnect messages and reconnect 3 times]:
    def auto_reconnect(self):
        for x in range(0,3):
            _reconnected = self.reconnect()
            if _reconnected==1:
                print('[Reconnected!!]')
                break
        return _reconnected

    def is_dead(self):
        print('OooOoOoooOooo')
        return False

    def start(self):
        # [Calibrate Scanarea coords]:
        self.calibrate_mouse_scanarea()

        # [Calibrate HSV for bobber]:
        self.sp.calibrate_bobber()

        # [Calibrate Tooltip coords]:
        self.calibrate_mouse_tooltip()

        # [If using mouse_mode, calibrate coords on actionbar for skills]:
        if self._use_mouse_mode:
            self.calibrate_mouse_actionbar()
        else:
            self.load_skills_actionbar()
            #^(else, load from skills config)

        input('[Enter to start bot!]: (3sec delay)')
        self._timer_start = time.time()
        time.sleep(3)

        print('[BobberBot Started]')
        self._bot_start = time.time()

        # [Play sound to alert start of bot]:
        playsound.playsound('audio/sms_alert.mp3')

        self._audio_stream.start_stream()
        while self._audio_stream.is_active():
            try:
                # [Start Fishing / 30sec fishing timer]:
                if self._timer_elapsed >= 30 or self._splash_detected:
                    # [Right-click if splash is detected]:
                    if self._splash_detected:
                        if self._bobber_found == False:
                            pyautogui.rightClick(x=None, y=None)
                        else:
                            pyautogui.rightClick(x=self._bobber_found[1], y=self._bobber_found[0])
                        self._timeout_cnt = 0
                    elif self._splash_detected == False and self._timer_start is not None:
                        self._miss_cnt+=1
                        self._timeout_cnt+=1
                        if self._timeout_cnt >= 10:
                            print('[WoW crashed? Miss Count: {0}]'.format(self._timeout_cnt))
                            print('Run time: {0} min'.format((time.time()-self._bot_start)/60))
                            print('Catch count: {0}'.format(self._catch_cnt))
                            print('Miss count:  {0}'.format(self._miss_cnt))

                            # [Try to reconenct a few times]:
                            reconnected = self.auto_reconnect()
                            if reconnected:
                               print('[Reconnected -- Starting bot back up!] 2sec..')
                               time.sleep(2)
                            else:
                               print('[Not able to reconnect, exiting] =(')
                               sys.exit()

                    # [Cast Pole!]:
                    self.cast_pole()
                self._timer_elapsed = (time.time() - self._timer_start)

                # [Try to locate the bobber]:
                if self._bobber_found == False:
                    _bobber_coords = self.find_bobber()
                    if _bobber_coords != 0:
                        self._bobber_found = _bobber_coords

            except pyautogui.FailSafeException:
                self._bobber_reset=True

                print('Run time: {0} min'.format((time.time()-self._bot_start)/60))
                print('Catch count: {0}'.format(self._catch_cnt))
                print('Miss count:  {0}'.format(self._miss_cnt))

                _exit = input('[Do you wish to exit?]:')
                _exit = False if (_exit.lower() == 'n' or _exit.lower() == 'no') else True
                if _exit:
                    print('[Bye!]')

                    # [Stop Audio Stream]:
                    self._audio_stream.stop_stream()
                    self._audio_stream.close()
                    self.pa.terminate()

                    # [Die Young, Leave a beautiful shell]:
                    sys.exit(1)

        # [Stop Audio Stream]:
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.pa.terminate()

    # [Iterates over HSV threshold of screengrab to try and locate the bobber]:
    def find_bobber(self):
        thresh = self.sp.thresh_image()

        self._bobber_reset=False
        for x in range(0, thresh.shape[0]):
            for y in range(0, thresh.shape[1]):
                # [If white pixel found, check for bobber]:
                if thresh[x,y] == 255:
                    _coords = (x, y)
                    _bobber_loc = self._check_bobber_loc(_coords)

                    # [Found Bobber!]:
                    if _bobber_loc != 0:
                        return _bobber_loc
                    else:
                        # [Passed 30sec, pass back to main loop for recast]:
                        if self._timer_elapsed >= 30:
                            return 0
                        else:
                            if self._count_cnt != None:
                                if self._count_cnt > 10:
                                    self._count_cnt = None
                                    return 0
                                else:
                                    self._count_cnt+=1

                        self._timer_elapsed = (time.time() - self._timer_start)

                # [Check for exit conditions]:
                if self._bobber_reset:
                    break
            if self._bobber_reset:
                break
        return 0

    def check_tooltip(self):
        nemo = self.sp.grab_rect(self.sp._tooltip_start, self.sp._tooltip_stop, mod=1)

        # [Convert images to grayscale]:
        gray_test = cv2.cvtColor(nemo, cv2.COLOR_BGR2GRAY)
        gray_control = imageio.imread('img/tooltip_control_gray.png')
        imageio.imwrite('tooltip_test_gray.png', gray_test) #

        (score, diff) = skimage.metrics.structural_similarity(gray_control, gray_test, full=True)

        print("SSIM: {}".format(score))
        return True if (score > .90) else False

    # [Move mouse to _coords /capture/ check for tooltip]:
    def _check_bobber_loc(self, _coords):
        (top, left) = _coords

        _coords = ((top+self.sp._scanarea_start.get('y')), (left+self.sp._scanarea_start.get('x')))
        pyautogui.moveTo(_coords[1], _coords[0], duration=0)

        if self.check_tooltip():
            return _coords

        return 0

    # [Have user calibrate location of Scan Area]:
    def calibrate_mouse_scanarea(self):
        # [Check for config files]:
        config_filename = 'configs/scanarea.json'
        if os.path.isfile(config_filename):
            _use_calibrate_config = input('[Calibration config found for Scan Area | Use this?]: ')
            _use_calibrate_config = False if (_use_calibrate_config.lower() == 'n' or _use_calibrate_config.lower() == 'no') else True
        else:
            _use_calibrate_config = False

        # [Calibrate mouse _coords for each action bar item used]:
        if _use_calibrate_config == False:
            # [Display picture of screen for user to click]:
            mc = mouse_calibrator.mouse_calibrator('calibrate_scanarea')
            mc.run()

        # [Load config file into globals]:
        with open(config_filename) as config_file:
            configs = json.load(config_file)
            self.sp._scanarea_start = configs['scanarea_start']
            self.sp._scanarea_stop = configs['scanarea_stop']

        if _use_calibrate_config == False:
            self.sp.draw_rect(self.sp._scanarea_start, self.sp._scanarea_stop, mod=1) 

            # [Check with user to make sure they like the scan area]:
            _calibrate_good = input('[Scan Area Calibration Good? (y/n)]: ')
            _calibrate_good = True if _calibrate_good[0].lower() == 'y' else False
            if _calibrate_good == False:
                self.calibrate_mouse_scanarea()

    # [Have user calibrate location of Tooltip]:
    def calibrate_mouse_tooltip(self):
        # [Check for config files]:
        config_filename = 'configs/tooltip.json'
        if os.path.isfile(config_filename):
            _use_calibrate_config = input('[Calibration config found for Tooltip | Use this?]: ')

            _use_calibrate_config = False if (_use_calibrate_config.lower() == 'n' or _use_calibrate_config.lower() == 'no') else True
        else:
            _use_calibrate_config = False

        # [Calibrate mouse _coords for each action bar item used]:
        if _use_calibrate_config == False:
            mc = mouse_calibrator.mouse_calibrator('calibrate_tooltip')
            mc.run()

        # [Load config file into globals]:
        with open(config_filename) as config_file:
            configs = json.load(config_file)
            self.sp._tooltip_start = configs['tooltip_start']
            self.sp._tooltip_stop = configs['tooltip_stop']

        if _use_calibrate_config == False:
            self.sp.draw_rect(self.sp._tooltip_start, self.sp._tooltip_stop, mod=.5)

            # [Check with user to make sure they like the scan area]:
            _calibrate_good = input('[Tooltip Calibration Good? (y/n)]: ')
            _calibrate_good = True if _calibrate_good[0].lower() == 'y' else False
            if _calibrate_good: 
                # [Screenshot for `tooltip_control_gray`]:
                nemo = self.sp.grab_rect(self.sp._tooltip_start, self.sp._tooltip_stop, mod=1)
                gray_nemo = cv2.cvtColor(nemo, cv2.COLOR_BGR2GRAY)
                imageio.imwrite('img/tooltip_control_gray.png', gray_nemo)
            else:
                self.calibrate_mouse_tooltip()

    # [Have user calibrate location of items on taskbar]:
    def calibrate_mouse_actionbar(self):
        # [Check for config files]:
        config_filename = 'configs/mouse_actionbar.json'
        if os.path.isfile(config_filename):
            _use_calibrate_config = input('[Calibration config found for mouse_action bar | Use this?]: ')
            _use_calibrate_config = False if (_use_calibrate_config.lower() == 'n' or _use_calibrate_config.lower() == 'no') else True
        else:
            _use_calibrate_config = False

        # [Calibrate mouse _coords for each action bar item used]:
        if _use_calibrate_config == False:
            mc = mouse_calibrator.mouse_calibrator('calibrate_mouse_actionbar')
            mc.run()

        # [Load config file into globals]:
        with open(config_filename) as config_file:
            configs = json.load(config_file)
            self._fishing_pole_loc = configs['fishing_pole']
            self._fishing_skill_loc = configs['fishing_skill']
            self._fishing_bauble_loc = configs['fishing_bauble']

        print('[Mouse Calibration finished~ Domo Arigato!]')

    # [Load config file into globals]:
    def load_skills_actionbar(self):
        config_filename = 'configs/skills_actionbar.json'
        with open(config_filename) as config_file:
            configs = json.load(config_file)
            self._fishing_pole_key = configs['fishing_pole'].get('key')
            self._fishing_skill_key = configs['fishing_skill'].get('key')
            self._fishing_bauble_key = configs['fishing_bauble'].get('key')


# [0]: Ability to give commands to bot | Ability to recalibrate during loop
# [1]: Give bot chatlog? Chatlog addons? / scan bobberbot channel for commands
# [-]: Check `check_login` to make sure MOD is correct in OSX
# [0]: Check `check_login` to make sure MOD is correct in WINDOWS
# [1]: Set reasonable defaults for config/* files for Master
# [2]: Check for death upon login?
# [3]: Write `calibrate_relogin()` to get `login_control_gray` for user
bb = bobber_bot()
if __name__ == '__main__':
    _DEV = False
    if _DEV==False:
        bb.start()
    else:
        print('[_DEV testing]:')
        # [Check tooltip/calibration]:
        #bb.calibrate_mouse_tooltip()
        #print(bb.check_tooltip())

        # [Check scanarea/bobber calibration]:
        #bb.calibrate_mouse_scanarea()
        #bb.sp.calibrate_bobber()
print('[fin.]')

