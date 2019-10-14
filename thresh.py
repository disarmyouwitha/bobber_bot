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
from pymouse import PyMouseEvent

# [Import Quartz for OSX, else use MSS]: (for ScreenPixel.capture())
if sys.platform == 'darwin':
    import Quartz.CoreGraphics as CG
else:
    import mss

_dev = False
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))


class ScreenPixel(object):
    # [ScreenPixel Globals]:
    _data = None
    _numpy = None
    _width = None
    _height = None
    _thresh_cnt = 0

    # [Threshold Presets]:
    bobber_lower_hsv = numpy.array([80,0,0])
    bobber_upper_hsv = numpy.array([140,255,255])
    tooltip_lower_hsv = numpy.array([0,0,0])
    tooltip_upper_hsv = numpy.array([25,255,255])
    splash_lower_hsv = numpy.array([0,0,0])
    splash_upper_hsv = numpy.array([255,255,255])

    def capture(self):
        if sys.platform == 'darwin':
            self.capture_osx()
        else:
            self.capture_mss()

    def capture_osx(self):
        region = CG.CGRectInfinite

        # [Create screenshot as CGImage]:
        image = CG.CGWindowListCreateImage(region, CG.kCGWindowListOptionOnScreenOnly, CG.kCGNullWindowID, CG.kCGWindowImageDefault)

        # [Intermediate step, get pixel data as CGDataProvider]:
        prov = CG.CGImageGetDataProvider(image)

        # [Copy data out of CGDataProvider, becomes string of bytes]:
        self._data = CG.CGDataProviderCopyData(prov)

        # [Get width/height of image]:
        self._width = CG.CGImageGetWidth(image)
        self._height = CG.CGImageGetHeight(image)

        # [Get raw pixels from the screen, save it to a Numpy array as RGB]:
        imgdata=numpy.frombuffer(self._data,dtype=numpy.uint8).reshape(int(len(self._data)/4),4)
        _numpy_bgr = imgdata[:self._width*self._height,:-1].reshape(self._height,self._width,3)
        _numpy_rgb = _numpy_bgr[...,::-1]
        self._numpy = _numpy_rgb
        #imageio.imwrite('screen.png', self._numpy)

    def capture_mss(self):
        with mss.mss() as sct:
            # [Capture Part of the screen -- NEAT!]:
            #monitor = { "top": 100, "left": 100, "width": 160, "height": 135, "mon": 0 }

            # [Equivalent to CG.CGRectInfinite]:
            monitor = sct.monitors[0] #0: All | 1: first | 2: second
            self._width = monitor['width']
            self._height = monitor['height']

            # [Get raw pixels from the screen, save it to a Numpy array as RGB]:
            _numpy_bgr = numpy.array(sct.grab(monitor)) #sct.grab()
            _numpy_rgb = cv2.cvtColor(_numpy_bgr, cv2.COLOR_BGR2RGB)
            self._numpy = _numpy_rgb
            #imageio.imwrite('screen_mss.png', self._numpy)

    def resize_image(self, nemo, scale_percent=50):
        width = int(nemo.shape[1] * scale_percent / 100)
        height = int(nemo.shape[0] * scale_percent / 100)
        dim = (width, height)
        nemo_scaled = cv2.resize(nemo, dim, interpolation = cv2.INTER_AREA)
        return nemo_scaled 

    def screen_fast(self, _limit=.85):
        y,x,_z = self._numpy.shape
        cropx = int(x*_limit)
        cropy = int(y*_limit)
        startx = (x//2-(cropx//2))
        starty = (y//2-(cropy//2))

        # [Trim _numpy array to screen_fast]:
        return self._numpy[starty:starty+cropy,startx:startx+cropx]

    def save_square(self, top, left, square_width=100, mod=2, center=False):
        top = (top*mod)
        left = (left*mod)
        square_width = square_width*mod

        if center==True:
            top = top-(square_width/2)
            left = left-(square_width/2)

        # [Correct out-of-bounds Top]:
        top_start = top
        if (top_start+square_width) > self._height:
            top_start = self._height-square_width
        if top_start < 0:
            top_start = 0
        top_stop = (top_start+square_width)

        # [Correct out-of-bounds Left]:
        left_start = left
        if (left_start+square_width) > self._width:
            left_start = self._width-square_width
        if left_start < 0:
            left_start = 0
        left_stop = (left_start+square_width)

        # [Trim _numpy array to numpy_square]:
        return self._numpy[top_start:top_stop,left_start:left_stop]

    def nothing(self, x):
        #print('Trackbar value: ' + str(x))
        pass

    # [Display calibrate images to confirm they look good]:
    def calibrate_image(self, screen='bobber'):
        # [Check for config files]:
        config_filename = 'configs/config_{0}.txt'.format(screen)
        if os.path.isfile(config_filename):
            _use_calibrate_config = input('[Calibration config found for {0} | Use this?]: '.format(screen))
            _use_calibrate_config = False if (_use_calibrate_config.lower() == 'n' or _use_calibrate_config.lower() == 'no') else True
        else:
            _use_calibrate_config = False

        # [Set HSV mask from configs]:
        if _use_calibrate_config == True:
            with open(config_filename, 'r') as f:
                config = f.read().split('\n')
                lower_hsv = numpy.array([int(config[0]), int(config[1]), int(config[2])])
                upper_hsv = numpy.array([int(config[3]), int(config[4]), int(config[5])])
            _calibrate_good = True
            # [Take calibration threshold picture of bookeeping]:
            self.thresh_image(screen)
        else:
            input('[Calibrating {0} in 3sec!]:'.format(screen))
            time.sleep(3)

            # [Capture of calibration image]:
            self.capture()
            if screen=='bobber':
                nemo = self.screen_fast(.5)
                nemo = self.resize_image(nemo, scale_percent=50)
                lower_hsv = self.bobber_lower_hsv
                upper_hsv = self.bobber_upper_hsv
            elif screen=='tooltip_square':
                nemo = self.save_square(top=725,left=1300,square_width=100,mod=2,center=False)
                lower_hsv = self.tooltip_lower_hsv
                upper_hsv = self.tooltip_upper_hsv

            # [Median Blur]:
            # [Convert BGR to HSV]:
            nemo = cv2.medianBlur(nemo, 5)
            hsv = cv2.cvtColor(nemo, cv2.COLOR_BGR2HSV)

            # [Unpack into local variables]:
            (uh, us, uv) = upper_hsv
            (lh, ls, lv) = lower_hsv

            # [Set up window]:
            window_name = 'HSV Calibrator'
            cv2.namedWindow(window_name)
            cv2.moveWindow(window_name, 40,30) 

            # [Create trackbars for Upper HSV]:
            cv2.createTrackbar('UpperH',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('UpperH',window_name, uh)
            cv2.createTrackbar('UpperS',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('UpperS',window_name, us)
            cv2.createTrackbar('UpperV',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('UpperV',window_name, uv)

            # [Create trackbars for Lower HSV]:
            cv2.createTrackbar('LowerH',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('LowerH',window_name, lh)
            cv2.createTrackbar('LowerS',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('LowerS',window_name, ls)
            cv2.createTrackbar('LowerV',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('LowerV',window_name, lv)
            font = cv2.FONT_HERSHEY_SIMPLEX

            # [Alert user calibration image is ready]:
            playsound.playsound('audio/sms_alert.mp3')

            # [Keep calibration window open until ESC is pressed]:
            while True:
                # [Threshold the HSV image]:
                mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
                cv2.putText(mask,'Lower HSV: [' + str(lh) +',' + str(ls) + ',' + str(lv) + ']', (10,30), font, 0.5, (200,255,155), 1, cv2.LINE_AA)
                cv2.putText(mask,'Upper HSV: [' + str(uh) +',' + str(us) + ',' + str(uv) + ']', (10,60), font, 0.5, (200,255,155), 1, cv2.LINE_AA)
                cv2.imshow(window_name, mask)

                # [Listen for ESC key]:
                k = cv2.waitKey(1) & 0xFF
                if k == 27:
                    break

                # [Get current positions of Upper HSV trackbars]:
                uh = cv2.getTrackbarPos('UpperH',window_name)
                us = cv2.getTrackbarPos('UpperS',window_name)
                uv = cv2.getTrackbarPos('UpperV',window_name)

                # [Get current positions of Lower HSCV trackbars]:
                lh = cv2.getTrackbarPos('LowerH',window_name)
                ls = cv2.getTrackbarPos('LowerS',window_name)
                lv = cv2.getTrackbarPos('LowerV',window_name)

                # [Set lower/upper HSV to get the current mask]:
                upper_hsv = numpy.array([uh,us,uv])
                lower_hsv = numpy.array([lh,ls,lv])

            # [Cleanup Windows]:
            cv2.destroyAllWindows()

            # [Check Calibration /w user]:
            if _use_calibrate_config == False:
                _calibrate_good = input('[Calibration Good? Ready? (y/n)]: ')
                _calibrate_good = True if _calibrate_good[0].lower() == 'y' else False

            if _calibrate_good == True:
                # [Save Calibration image]: (Great for setup debug)
                mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
                imageio.imwrite('calibrate_thresh_{0}{1}.png'.format(screen, self._thresh_cnt), mask)
                self._thresh_cnt+=1

            if _calibrate_good == True and _use_calibrate_config == False:
                # [Delete old config file]:
                if os.path.isfile(config_filename):
                    os.remove(config_filename)

                (lh, ls, lv) = lower_hsv
                (uh, us, uv) = upper_hsv

                print('[Saving calibration to: {0}]'.format(config_filename))
                with open(config_filename, 'w') as f:
                    f.write('{0}\n'.format(lh)) #lower_hue
                    f.write('{0}\n'.format(ls)) #lower_saturation
                    f.write('{0}\n'.format(lv)) #lower_value
                    f.write('{0}\n'.format(uh)) #upper_hue
                    f.write('{0}\n'.format(us)) #upper_saturation
                    f.write('{0}'.format(uv))   #upper_value

        # [Update Globals]:
        if _calibrate_good == True:
            if screen=='bobber':
                self.bobber_lower_hsv = lower_hsv
                self.bobber_upper_hsv = upper_hsv
            elif screen=='tooltip_square':
                self.tooltip_lower_hsv = lower_hsv
                self.tooltip_upper_hsv = upper_hsv
        else:
            # [Bad calibration, try again]:
            self.calibrate_image(screen)

    def thresh_image(self, screen='bobber'):
        self.capture()
        if screen=='bobber':
            nemo = self.screen_fast(.5)
            nemo = self.resize_image(nemo, scale_percent=50)
            lower_hsv = self.bobber_lower_hsv
            upper_hsv = self.bobber_upper_hsv
        elif screen=='tooltip_square':
            nemo = self.save_square(top=725,left=1300,square_width=100)
            lower_hsv = self.tooltip_lower_hsv
            upper_hsv = self.tooltip_upper_hsv

        # [Median Blur]:
        # [Convert BGR to HSV]:
        nemo = cv2.medianBlur(nemo, 5)
        hsv = cv2.cvtColor(nemo, cv2.COLOR_BGR2HSV)
        nemo_masked = cv2.inRange(hsv, lower_hsv, upper_hsv)

        if self._thresh_cnt<0: # thresh_bobber, thresh_tooltip
            imageio.imwrite('screen_thresh_{0}{1}.png'.format(screen,self._thresh_cnt), nemo_masked)
        self._thresh_cnt+=1

        return nemo_masked


# [Callback for splash detection!]:
def audio_callback(in_data, frame_count, time_info, status):
    try:
        data = numpy.frombuffer(in_data ,dtype=numpy.int16)
        peak = numpy.average(numpy.abs(data))*2
        peak = int(peak)
        
        if peak > bb._audio_threshold and bb._splash_detected==False:
            bb._splash_detected = True

            if bb._timer_start is not None:
                if bb._bobber_found == True:
                    #print('Splash detected, with bobber: {0}'.format(peak))
                    self._catch_cnt+=1
                else:
                    #print('Splash detected, no bobber: {0}'.format(peak))
                    self._miss_cnt+=1

        return data, pyaudio.paContinue

    except pyautogui.FailSafeException:
        bb._bobber_reset=True
        bb._audio_stream.stop_stream()
        bb._audio_stream.close()
        bb.pa.terminate()

        # [Die Young, Leave beautiful code]:
        print('[Bye]')
        sys.exit(1)


class bobber_bot():
    # [Included Classes]:
    sp = None
    pa = None

    # [BobberBot Globals]:
    _miss_cnt = 0
    _catch_cnt = 0
    _count_cnt = 0
    _timeout_cnt = 0
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
    _fishing_skill_loc = None
    _fishing_bauble_loc = None

    # [BobberBot Settings]:
    _use_baubles = True
    _use_auto_sell = False
    _use_mouse_mode = False

    def __init__(self):
        self.sp = ScreenPixel()
        self.pa = pyaudio.PyAudio()
        self.setup_audio()

    def setup_audio(self):
        dev_idx = 0 # Microphone as input
        dev_idx = 2 # Speakers as input
        if dev_idx > 0:
            self._audio_stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, input_device_index=dev_idx, stream_callback=audio_callback)
        else:
            self._audio_stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, stream_callback=audio_callback)

    def cast_pole(self):
        # [Check to apply bauble]:
        if self._use_baubles==True:
            self.bauble_check()

        self._timer_elapsed = 0
        self._timer_start = time.time()

        # [Use Fishing skill]:
        if self._use_mouse_mode == True:
            time.sleep(2)
            pyautogui.click(x=self._fishing_skill_loc.get('x'), y=self._fishing_skill_loc.get('y'), button='left', clicks=1)
        else:
            pyautogui.typewrite('8')

        time.sleep(3) # Wait so that we don't try and find old bobber as it fades (? needed now?)
        self._bobber_reset=True
        self._bobber_found = False
        self._splash_detected = False

    def bauble_check(self):
        if self._splash_detected == True:
            time.sleep(2) # If we caught a fish, a small delay before trying to apply bauble to make sure we aren't interrupted
        if self._bauble_elapsed >= 630: # 10min (and 30secs)
            #print('[casting_bauble]')
            if self._use_mouse_mode == True:
                # [Click Fishing bauble]:
                pyautogui.click(x=self._fishing_bauble_loc.get('x'), y=self._fishing_bauble_loc.get('y'), button='left', clicks=1)

                # [Click Fishing pole]:
                pyautogui.click(x=self._fishing_pole_loc.get('x'), y=self._fishing_pole_loc.get('y'), button='left', clicks=1)
            else:
                pyautogui.typewrite('9') # fishing bauble on toolbar
                pyautogui.typewrite('7') # fishing pole on toolbar

            time.sleep(10) # sleep while casting bauble~
            self._bauble_elapsed = 0
            self._bauble_start = time.time()
        self._bauble_elapsed = (time.time() - self._bauble_start)

    def start(self):
        # [Calibrate HSV for bobber/tooltip]:
        self.sp.calibrate_image(screen='bobber')
        self.sp.calibrate_image(screen='tooltip_square')

        if self._use_mouse_mode == True:
            self.calibrate_mouse_toolbar()

        self._timer_start = time.time()
        input('[Enter to start bot!]: (3sec delay)')
        time.sleep(3)

        print('[BobberBot Started]')
        playsound.playsound('audio/sms_alert.mp3')
        self._audio_stream.start_stream()

        while self._audio_stream.is_active():
            try:
                # [Start Fishing / 30sec fishing timer]:
                if self._timer_elapsed >= 30 or self._splash_detected:
                    # [Right-click if splash is detected]:
                    if self._splash_detected:
                        pyautogui.rightClick(x=None, y=None)
                        self._timeout_cnt = 0
                    elif self._splash_detected == False and self._timer_start is not None:
                        self._timeout_cnt+=1
                        #print('[Miss Count: {0}]: timer_elapsed: {1}'.format(self._timeout_cnt, self._timer_elapsed))

                        if self._timeout_cnt >= 20:
                            print('[WoW crashed? Miss Count: {0}]'.format(self._timeout_cnt))
                            sys.exit(1)

                    self.cast_pole()
                self._timer_elapsed = (time.time() - self._timer_start)

                # [Try to locate the bobber]:
                if self._bobber_found == False:
                    _bobber_coords = self.find_bobber()
                    if _bobber_coords != 0:
                        self._bobber_found = _bobber_coords
                        #self.track_bobber(_bobber_coords) # Track bobber for 30seconds, taking screenshots

            except pyautogui.FailSafeException:
                self._bobber_reset=True
                print('[Bye]')

                # [Stop Audio Stream]:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
                self.pa.terminate()

                # [Die Young, Leave beautiful code]:
                sys.exit(1)

        # [Stop Audio Stream]:
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.pa.terminate()

    # [Iterates over HSV threshold of screengrab to try and locate the bobber]:
    def find_bobber(self):
        thresh = self.sp.thresh_image(screen='bobber')

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
                if self._bobber_reset==True:
                    break
            if self._bobber_reset==True:
                break
        return 0

    # [Move mouse to _coords /capture/ check for tooltip]:
    def _check_bobber_loc(self, _coords):
        (top, left) = _coords

        y,x,_z = self.sp._numpy.shape
        cropx = int(x*.5)
        cropy = int(y*.5)
        startx = (x//2-(cropx//2))
        starty = (y//2-(cropy//2))

        _coords = ((top+(starty/2)), (left+(startx/2)))
        pyautogui.moveTo(_coords[1], _coords[0], duration=0)

        thresh = self.sp.thresh_image(screen='tooltip_square')
        tooltip_top = 20
        tooltip_left = 15

        _tooltip_check = 0
        for x in range(0,40,10):
            tooltip_check = thresh[tooltip_left+x, tooltip_top]
            if tooltip_check == 255:
                _tooltip_check+=1

        if _tooltip_check >= 1:
            return _coords

        return 0

    # [Track bobber for 30 seconds, taking pictures]:
    def track_bobber(self, _bobber_coords):
        while self._timer_elapsed < 30:
            self.sp.capture()
            nemo = self.sp.save_square(top=_bobber_coords[0], left=_bobber_coords[1], square_width=100, mod=2, center=True)
            self._timer_elapsed = (time.time() - self._timer_start)

    # [Have user calibrate location of items on taskbar]:
    def calibrate_mouse_toolbar(self):
        # [Check for config files]:
        config_filename = 'configs/config_mouse_toolbar.json'
        if os.path.isfile(config_filename):
            _use_calibrate_config = input('[Calibration config found for mouse_toolbar | Use this?]: ')
            _use_calibrate_config = False if (_use_calibrate_config.lower() == 'n' or _use_calibrate_config.lower() == 'no') else True
        else:
            _use_calibrate_config = False

        # [Calibrate mouse _coords for each action bar item used]:
        if _use_calibrate_config == False:
            mc = mouse_calibrator()
            mc.run()

        # [Load config file into globals]:
        with open(config_filename) as config_file:
            configs = json.load(config_file)
            self._fishing_pole_loc = configs['fishing_pole']
            self._fishing_skill_loc = configs['fishing_skill']
            self._fishing_bauble_loc = configs['fishing_bauble']

        print('[Mouse Calibration finished~ Domo Arigato!]')

    # [Bind `Interact Vendor` to `\` key]:
    def sell_fish(self, vendor_name):
        print('[Selling Fish in 3sec!]')
        time.sleep(3)
        self.chat_command('/target {0}'.format(vendor_name))
        pyautogui.press('\\') # Interact Vendor keybind
        time.sleep(3)
        pyautogui.press('esc')

    def chat_command(self, cmd):
        pyautogui.press('enter') # 
        pyautogui.typewrite(cmd)
        pyautogui.press('enter')


class mouse_calibrator(PyMouseEvent):
    _click_cnt = 0
    action_loc = None
    action_name = None
    _fishing_pole_loc = None
    _fishing_skill_loc = None
    _fishing_bauble_loc = None
    _calibrating = False

    def __init__(self):
        PyMouseEvent.__init__(self)
        print('[Calibrating fishing_pole toolbar location! Alt-tab, go left-click it && come back here!]')
        self._calibrating = True

    def save_calibration(self):
        # [Load up current configs]:
        config_filename = 'config_mouse_toolbar.json'
        with open(config_filename) as config_file:
            configs = json.load(config_file)

        # [Update config for locations]:
        configs.update(self._fishing_pole_loc)
        configs.update(self._fishing_skill_loc)
        configs.update(self._fishing_bauble_loc)

        # [Save values back to config file to update values]:
        with open(config_filename, 'w') as fp:
            json.dump(configs, fp)

        self.stop()

    def click(self, x, y, button, press):
        int_x = int(x)
        int_y = int(y)

        if button==1 and press and self._calibrating == True:
            if self._fishing_pole_loc == None:
                self._fishing_pole_loc = {"fishing_pole" : { "x":int_x, "y":int_y }}
                print(self._fishing_pole_loc)
                print('[Calibrating fishing_skill toolbar location! Alt-tab, go left-click it && come back here!]')
            elif self._fishing_skill_loc == None:
                self._fishing_skill_loc = {"fishing_skill" : { "x":int_x, "y":int_y }}
                print(self._fishing_skill_loc)
                print('[Calibrating fishing_bauble toolbar location! Alt-tab, go left-click it && come back here!]')
            elif self._fishing_bauble_loc == None:
                self._fishing_bauble_loc = {"fishing_bauble" : { "x":int_x, "y":int_y }}
                print(self._fishing_bauble_loc)
                print('Click one more time for Good Luck!')
            else:
                print('[Ending Calibration]')
                self._calibrating = False
                self.save_calibration()
                self.stop()


# def capture_mss(self):
#[2]: Windows implementation of capture() (?) https://pypi.org/project/mss/ (?)
bb = bobber_bot()
if __name__ == '__main__':
    if _dev==False:
        bb.start()
        print('[fin.]')
        bb.sell_fish('Stuart Fleming')
    else:
        # [Dev. testing stuff]:
        print('Woomy!')