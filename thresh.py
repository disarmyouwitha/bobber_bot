import os
import sys
import cv2
import time
import numpy
import pyaudio
import imageio
import pyautogui
import playsound
import contextlib
import Quartz.CoreGraphics as CG

#[Python3 re-write]:
#python3 -m pip install scipy
#python3 -m pip install pyaudio
#python3 -m pip install imageio
#python3 -m pip install pyautogui
#python3 -m pip install playsound
#python3 -m pip install opencv-python

pyautogui.PAUSE = 0#2.5
pyautogui.FAILSAFE = True

class ScreenPixel(object):
    # [ScreenPixel Globals]:
    _data = None
    _numpy = None
    _thresh_cnt = 0

    # [Threshold Presets]:
    bobber_lower_hsv = numpy.array([80,0,0])
    bobber_upper_hsv = numpy.array([140,255,255])
    tooltip_lower_hsv = numpy.array([0,0,0])
    tooltip_upper_hsv = numpy.array([25,255,255])
    splash_lower_hsv = numpy.array([0,0,0])
    splash_upper_hsv = numpy.array([255,255,255])

    def capture(self):
        region = CG.CGRectInfinite

        # [Create screenshot as CGImage]:
        image = CG.CGWindowListCreateImage(region, CG.kCGWindowListOptionOnScreenOnly, CG.kCGNullWindowID, CG.kCGWindowImageDefault)

        # [Intermediate step, get pixel data as CGDataProvider]:
        prov = CG.CGImageGetDataProvider(image)

        # [Copy data out of CGDataProvider, becomes string of bytes]:
        self._data = CG.CGDataProviderCopyData(prov)

        # [Get width/height of image]:
        self.width = CG.CGImageGetWidth(image)
        self.height = CG.CGImageGetHeight(image)
        self.get_numpy()

        #imageio.imwrite('screen.png', self._numpy)

    def get_numpy(self):
        imgdata=numpy.frombuffer(self._data,dtype=numpy.uint8).reshape(int(len(self._data)/4),4)
        _numpy_bgr = imgdata[:self.width*self.height,:-1].reshape(self.height,self.width,3)
        _numpy_rgb = _numpy_bgr[...,::-1]
        self._numpy = _numpy_rgb

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
        if (top_start+square_width) > self.height:
            top_start = self.height-square_width
        if top_start < 0:
            top_start = 0
        top_stop = (top_start+square_width)

        # [Correct out-of-bounds Left]:
        left_start = left
        if (left_start+square_width) > self.width:
            left_start = self.width-square_width
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
        config_filename = 'config_{0}.txt'.format(screen)
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

        if self._thresh_cnt<=3: # thresh_bobber, thresh_tooltip
            imageio.imwrite('screen_thresh_{0}{1}.png'.format(screen,self._thresh_cnt), nemo_masked)
        self._thresh_cnt+=1

        return nemo_masked


@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))


class bobber_bot():
    # [BobberBot Globals]:
    _check_cnt = 0
    _fishing = False
    _timer_start = None
    _timer_elapsed = 30
    _bobber_reset = False
    _bauble_start = None
    _bauble_elapsed = 660

    # [Included Classes]:
    sp = None
    pa = None
    _cnt = 0

    def __init__(self, screen_pixel):
        self.sp = screen_pixel
        self.pa = pyaudio.PyAudio()
        print('[BobberBot Started]')

    def cast_pole(self, note=''):
        self._fishing = False
        self._timer_elapsed = 0
        self._first_bobber_square = None

        self.bauble_check() # Apply bauble

        print('[casting_pole: {0}]'.format(note))
        self._timer_start = time.time()

        if self._fishing == False:
            pyautogui.typewrite('8') # Fishing skill on actionbar
            time.sleep(2) # Wait so that we don't try and find old bobber as it fades
            self._bobber_reset=True
            self._fishing=True

    def bauble_check(self):
        if self._bauble_elapsed >= 660: # 10min
            print('[casting_bauble]')
            pyautogui.typewrite('9') # bauble skill on actionbar
            pyautogui.typewrite('7') # bauble skill on actionbar
            time.sleep(10) # sleep while casting bauble~
            self._bauble_elapsed = 0
            self._bauble_start = time.time()
        self._bauble_elapsed = (time.time() - self._bauble_start)

    def start(self):
        # [Calibrate HSV for bobber/tooltip]:
        self.sp.calibrate_image(screen='bobber')
        self.sp.calibrate_image(screen='tooltip_square')

        input('[Enter to start bot!]: (3sec delay)')
        time.sleep(3)

        while True:
            try:
                # [Start Fishing / 30sec fishing timer]:
                if self._timer_elapsed >= 30:
                    self.cast_pole('30sec')
                self._timer_elapsed = (time.time() - self._timer_start)

                # [Try to locate the bobber]:
                _bobber_coords = self.find_bobber()
                if _bobber_coords != 0:
                    #self.track_bobber(_bobber_coords)
                    self.listen_splash()

            except pyautogui.FailSafeException:
                self._bobber_reset=True
                print('[Bye]')
                continue
            except KeyboardInterrupt:
                #self.cast_pole('Keyboard Interrupt')
                sys.exit(1)
                continue

    def find_bobber(self):
        thresh = self.sp.thresh_image(screen='bobber')

        self._bobber_reset=False
        for x in range(0, thresh.shape[0]):
            for y in range(0, thresh.shape[1]):
                # [Check for white pixel]:
                if thresh[x,y] == 255:
                    _coords = (x, y)
                    _bobber_loc = self._check_bobber_loc(_coords)

                    # [Found Bobber!]:
                    if _bobber_loc != 0:
                        self._check_cnt=0
                        self._fishing=False
                        return _bobber_loc
                    else:
                        if self._check_cnt > 10:
                            self._bobber_reset = True
                            self._check_cnt = 0
                        else:
                            self._check_cnt+=1

                    # [Check to see if we are past 30 second timer]:
                    if self._timer_elapsed >= 30:
                        self.cast_pole('30sec_bobber')
                    self._timer_elapsed = (time.time() - self._timer_start)

                # [Check for exit conditions]:
                if self._bobber_reset==True or self._fishing==False:
                    break
            if self._bobber_reset==True or self._fishing==False:
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
            print('[FOUND IT!]: {0} | {1}'.format(_tooltip_check, _coords))
            return _coords

        return 0

    # [Track bobber for 30 seconds, taking pictures]:
    def track_bobber(self, _bobber_coords):
        while self._timer_elapsed < 30:
            self.sp.capture()
            nemo = self.sp.save_square(top=_bobber_coords[0], left=_bobber_coords[1], square_width=100, mod=2, center=True)
            self._timer_elapsed = (time.time() - self._timer_start)

    def listen_splash(self, threshold=1500):
        CHUNK = 2**11
        RATE = 44100
        stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

        _splash_detected = False
        while self._timer_elapsed < 30 and _splash_detected==False:
            data = numpy.frombuffer(stream.read(CHUNK),dtype=numpy.int16)
            peak=numpy.average(numpy.abs(data))*2
            bars="#"*int(50*peak/2**16)

            if peak > 1000:
                print("%05d %s"%(peak,bars))

            if peak > threshold:
                print('[SPLASH DETECTED!]')
                pyautogui.rightClick(x=None, y=None)
                _splash_detected = True
                self.cast_pole('Found Bobber')

            self._timer_elapsed = (time.time() - self._timer_start)

        return 0


#[0]: listen_splash() should take average of sound to use as baseline for thresholding
#[1]: listen_splash() should use *speaker* volume output rather than *microphone* input of speaker
#[2]: Windows implementation of capture() (?) https://pypi.org/project/mss/ (?)
#[3]: Can I script the bot to click on the screen before it starts / no delay / "start from python" rather than "start from wow"
if __name__ == '__main__':
    sp = ScreenPixel()
    bobber_bot(sp).start()
    print('[fin.]')