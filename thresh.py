import os
import sys
import cv2
import time
import pyautogui
import contextlib
import scipy.misc #do I need to import the whole module, or just imsave below?
import numpy as np
from scipy.misc import imsave
import matplotlib.pyplot as plt # probably don't need this once finished
from playsound import playsound
import Quartz.CoreGraphics as CG
from pymouse import PyMouseEvent
from skimage.measure import compare_ssim

pyautogui.PAUSE = 0#2.5
pyautogui.FAILSAFE = True


# [SSIM]:
# https://towardsdatascience.com/image-classification-using-ssim-34e549ec6e12
# https://scikit-image.org/docs/dev/auto_examples/transform/plot_ssim.html
# [Tensor Flow SSIM]:
# https://www.tensorflow.org/api_docs/python/tf/image/ssim
# [Motion Detection]:
# http://www.robindavid.fr/opencv-tutorial/motion-detection-with-opencv.html
# [Average/Dominant Color]:
# https://zeevgilovitz.com/detecting-dominant-colours-in-python


class ScreenPixel(object):
    # [ScreenPixel Globals]:
    _data = None
    _numpy = None
    _thresh_cnt = 0
    _screen_fast = None  # Not nessisary if we are returning / passing around the array(?)
    _numpy_square = None # Not nessisary if we are returning / passing around the array(?)

    # [Threshold Presets]:
    bobber_lower_hsv = np.array([80,0,0])
    bobber_upper_hsv = np.array([140,255,255])
    tooltip_lower_hsv = np.array([0,0,0])
    tooltip_upper_hsv = np.array([25,255,255])
    splash_lower_hsv = np.array([0,0,0])
    splash_upper_hsv = np.array([255,255,255])

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

        #imsave('screen.png', self._numpy)

    def get_numpy(self):
        imgdata=np.fromstring(self._data,dtype=np.uint8).reshape(len(self._data)/4,4)
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

        # [Trim _numpy array to _screen_fast]:
        self._screen_fast = self._numpy[starty:starty+cropy,startx:startx+cropx]
        return self._screen_fast

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

        # [Trim _numpy array to _numpy_square]:
        self._numpy_square = self._numpy[top_start:top_stop,left_start:left_stop]
        return self._numpy_square

    def nothing(self, x):
        #print('Trackbar value: ' + str(x))
        pass

    # [Display calibrate images to confirm they look good]:
    def calibrate_image(self, screen='bobber'):
        # [Check for config files]:
        config_filename = 'config_{0}.txt'.format(screen)
        if os.path.isfile(config_filename):
            _use_calibrate_config = raw_input('[Calibration config found for {0} | Use this?]: '.format(screen))
            _use_calibrate_config = False if (_use_calibrate_config.lower() == 'n' or _use_calibrate_config.lower() == 'no') else True
        else:
            _use_calibrate_config = False

        # [Set HSV mask from configs]:
        if _use_calibrate_config == True:
            with open(config_filename, 'r') as f:
                config = f.read().split('\n')
                lower_hsv = np.array([int(config[0]), int(config[1]), int(config[2])])
                upper_hsv = np.array([int(config[3]), int(config[4]), int(config[5])])
            _calibrate_good = True
            # [Take calibration threshold picture of bookeeping]:
            self.thresh_image(screen)
        else:
            raw_input('[Calibrating {0} in 3sec!]:'.format(screen))
            time.sleep(3)
            playsound('audio/sms_alert.mp3')
            #playsound('audio/eas_beep.mp3')
            #playsound('audio/bomb_siren.mp3')

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
                upper_hsv = np.array([uh,us,uv])
                lower_hsv = np.array([lh,ls,lv])

            # [Cleanup Windows]:
            cv2.destroyAllWindows()

            # [Check Calibration /w user]:
            if _use_calibrate_config == False:
                _calibrate_good = raw_input('[Calibration Good? Ready? (y/n)]: ')
                _calibrate_good = True if _calibrate_good[0].lower() == 'y' else False

            if _calibrate_good == True:
                # [Save Calibration image]: (Great for setup debug)
                mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
                imsave('calibrate_thresh_{0}{1}.png'.format(screen, self._thresh_cnt), mask)
                self._thresh_cnt+=1

            if _calibrate_good == True and _use_calibrate_config == False:
                # [Delete old config file]:
                if os.path.isfile(config_filename):
                    os.remove(config_filename)

                (lh, ls, lv) = lower_hsv
                (uh, us, uv) = upper_hsv

                print '[Saving calibration to: {0}]'.format(config_filename)
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
            imsave('screen_thresh_{0}{1}.png'.format(screen,self._thresh_cnt), nemo_masked)
        self._thresh_cnt+=1

        return nemo_masked

@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print '%s: %.02fms' % (msg, (end-start)*1000)


class mouse_listener(PyMouseEvent):
    # [MouseListener Globals]:
    _fishing = False
    _timer_start = None
    _timer_elapsed = 30
    _bobber_reset = False
    _check_cnt = 0 # Disabled right now
    _first_bobber_square = None
    _last_bobber_square = None

    # [Screen Pixel]:
    _cnt = 0
    sp = None

    def __init__(self, screen_pixel):
        PyMouseEvent.__init__(self) 
        self.sp = screen_pixel
        print '[Mouse Listening]'

    def cast_pole(self, note=''):
        self._fishing = False
        self._timer_elapsed = 0
        self._first_bobber_square = None

        print '[casting_pole: {0}]'.format(note)
        self._timer_start = time.time()

        if self._fishing == False:
            pyautogui.typewrite('8') # Fishing skill on actionbar
            time.sleep(2) # Wait so that we don't try and find old bobber as it fades
            self._bobber_reset=True
            self._fishing=True

    def click(self, x, y, button, press):
        int_x = int(x)
        int_y = int(y)

        if button == 1 and press == True and self._cnt==0:
            self._cnt+=1

            # [Calibrate HSV for bobber/tooltip]:
            self.sp.calibrate_image(screen='bobber')
            self.sp.calibrate_image(screen='tooltip_square')

            # I can script the bot to click on the screen before it starts / no delay / "start from python" rather than "start from wow"
            raw_input('[Enter to start bot!]: (3sec delay)')
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
                        self.track_bobber(_bobber_coords)

                except pyautogui.FailSafeException:
                    self._bobber_reset=True
                    print '[Bye]'
                    continue
                except KeyboardInterrupt:
                    #self.cast_pole('Keyboard Interrupt')
                    sys.exit(1)
                    continue
            self.stop()

        if button == 2 and press == True and self._cnt==0:
            self._cnt+=1
            print '[EXITING BOBBER BOT]'
            sys.exit(1)
            self.stop()

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
                            self.cast_pole('10_check_cnt')
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
            print '[FOUND IT!]: {0} | {1}'.format(_tooltip_check, _coords)
            return _coords

        return 0

    # [Splash]:
    def track_bobber(self, _bobber_coords):
        # [Track bobber for 30 seconds, taking pictures]:
        _bobber_found = False
        while self._timer_elapsed < 30 and _bobber_found==False:
            # [Take screenshot of square around bobber for splash detection bounds]:
            self.sp.capture()
            nemo = self.sp.save_square(top=_bobber_coords[0], left=_bobber_coords[1], square_width=100, mod=2, center=True)

            # [SSIM vs last bobber]:
            if self._first_bobber_square is None:
                self._first_bobber_square = nemo
                self._last_bobber_square = nemo
                #imsave('square_bobber_{0}.png'.format(self._cnt), nemo)
                self._cnt+=1
            else:
                if self.bobber_ssim(nemo, .64):
                #if self.gauge_water(nemo, .0165):
                    print '[SPLASH DETECTED!]'
                    pyautogui.rightClick(x=None, y=None)
                    _bobber_found = True
                    self.cast_pole('Found Bobber')

                # [Make current bobber, last bobber]:
                self._last_bobber_square = nemo

            self._timer_elapsed = (time.time() - self._timer_start)


    #vs_first: USUALLY above .75  | ALMOST ALWAYS above .7
    #stepwise: USUALLY above .8   | ALMOST ALWAYS above .75
    #_splash_: vs_first BELOW: .7 | stepwise BELOW: .75
    def bobber_ssim(self, nemo, threshold):
        # [from_first]:
        imageA = self._first_bobber_square
        imageB = nemo
        grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
        grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
        (score, diff) = compare_ssim(grayA, grayB, full=True)
        #diff = (diff * 255).astype("uint8")
        _ssim_score_vs_first = score
        ssim_score_1 = '_ssim_score_vs_first: {:2.5f}'.format(_ssim_score_vs_first)
        #print ssim_score_1

        # [stepwise]:
        imageA = self._last_bobber_square
        imageB = nemo
        grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
        grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
        (score, diff) = compare_ssim(grayA, grayB, full=True)
        #diff = (diff * 255).astype("uint8")
        _ssim_score_stepwise = score
        ssim_score_2 = '_ssim_score_stepwise: {:2.5f}'.format(_ssim_score_stepwise)
        #print ssim_score_2

        # [Splash Cam]:
        if _ssim_score_vs_first < threshold:
            print ssim_score_1
            print ssim_score_2
            imsave('square_bobber_SPLASH_{0}_1.png'.format(self._cnt), self._last_bobber_square)
            imsave('square_bobber_SPLASH_{0}_2.png'.format(self._cnt), nemo)
            self._cnt+=1

        with open('bobber_bot.log', 'a') as f:
            if _ssim_score_vs_first < threshold:
                f.write('[SPLASH DETECTED]\n')

            f.write(ssim_score_1+'\n')
            f.write(ssim_score_2+'\n\n')

        return _ssim_score_vs_first < threshold
        #return (_ssim_score_vs_first+_ssim_score_stepwise)/2 # Is Average SSIM useful? xD


    # https://github.com/KevinTyrrell/FishingBot/blob/1b736a7949969b8486dd79f6e3dbc327ae01e8f4/src/model/singleton/Angler.java
    def gauge_water(self, nemo, threshold):
        total_pixels = nemo.shape[0]*nemo.shape[1]

        nemo[:, :, 0] = 0     # Zero out contribution from red
        nemo[:, :, 1] = 0     # Zero out contribution from green
        #nemo[:, :, 2] = 0    # Zero out contribution from blue
        #plt.imshow(nemo)
        #plt.show()

        # [Isolate Blue channel and sum total]:
        blue_channel = nemo[:, :, 2]
        blue_sum = np.sum(blue_channel)
        blue_str = 'blue_sum: {0}'.format(blue_sum)
        blue_percent = total_pixels/blue_sum

        with open('bobber_bot.log', 'a') as f:
            if blue_percent > threshold:
                f.write('[SPLASH DETECTED]\n')

            #print blue_str
            #print '{:2.5f}'.format(blue_percent)
            f.write(blue_str+'\n')
            f.write('{:2.5f}\n\n'.format(blue_percent))

        return blue_percent > threshold


#[0]: gaugeWater test / SSIM test / motion detection test
#[1]: Threaded calls with Twisted (rather than sleep-based)
#[2]: keyboard interrupt: reset bot/cast_pole
if __name__ == '__main__':
    sp = ScreenPixel()
    c = mouse_listener(sp)
    c.run()
    print '[fin.]'