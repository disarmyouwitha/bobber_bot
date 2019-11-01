import os
import sys
import cv2
import json
import time
import numpy
import imageio
import playsound
import pyautogui
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

# [Import Quartz for OSX, else use MSS]: (for screen_pixel.capture())
if sys.platform == 'darwin':
    import Quartz.CoreGraphics as CG
else:
    import mss

class screen_pixel(object):
    # [screen_pixel Globals]:
    _data = None
    _numpy = None
    _width = None
    _height = None
    _scanarea_start = None
    _scanarea_stop = None
    _tooltip_start = None
    _tooltip_stop = None
    _thresh_cnt = 0

    # [Threshold Presets]:
    bobber_lower_hsv = numpy.array([0,0,0])
    bobber_upper_hsv = numpy.array([21,255,255])

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
            # [Equivalent to CG.CGRectInfinite]:
            monitor = sct.monitors[0] #0: All | 1: first | 2: second
            self._width = monitor['width']
            self._height = monitor['height']

            # [Get raw pixels from the screen, save it to a Numpy array as RGB]:
            _numpy_bgr = numpy.array(sct.grab(monitor))
            _numpy_rgb = cv2.cvtColor(_numpy_bgr, cv2.COLOR_BGR2RGB)
            self._numpy = _numpy_rgb
            #imageio.imwrite('screen_mss.png', self._numpy)

    def resize_image(self, nemo, scale_percent=50):
        width = int(nemo.shape[1] * scale_percent / 100)
        height = int(nemo.shape[0] * scale_percent / 100)
        dim = (width, height)
        nemo_scaled = cv2.resize(nemo, dim, interpolation = cv2.INTER_AREA)
        return nemo_scaled 

    # [To facilitate grabbing Scan Area]:
    def grab_rect(self, json_coords_start, json_coords_stop, mod=2, nemo=0):
        _start_x = json_coords_start.get('x')
        _start_y = json_coords_start.get('y')
        start_x = (_start_x*mod)
        start_y = (_start_y*mod)

        _stop_x = json_coords_stop.get('x')
        _stop_y = json_coords_stop.get('y')
        stop_x = (_stop_x*mod)
        stop_y = (_stop_y*mod)

        # [Use provided array, or take a capture]:
        try:
            if nemo==0:
                self.capture()
                _numpy_img = self._numpy
        except Exception:
            #print('Caught exception, passing image in')
            _numpy_img = nemo
            pass

        # [Trim _numpy array to rect]:
        return _numpy_img[start_y:stop_y,start_x:stop_x]

    def draw_rect(self, json_coords_start, json_coords_stop, mod=2):
        _start_x = json_coords_start.get('x')
        _start_y = json_coords_start.get('y')
        _start_x = (_start_x*mod)
        _start_y = (_start_y*mod)

        _stop_x = json_coords_stop.get('x')
        _stop_y = json_coords_stop.get('y')
        _stop_x = (_stop_x*mod)
        _stop_y = (_stop_y*mod)

        # [Draw box around Scan Area specified with mouse]:
        print('Pause. Drawing scan area with mouse:')
        time.sleep(2)

        _diff_x = (_stop_x - _start_x)
        _diff_y = (_stop_y - _start_y)
        pyautogui.moveTo(_start_x, _start_y, duration=1)
        pyautogui.moveTo((_start_x+_diff_x),_start_y, duration=1)
        pyautogui.moveTo((_start_x+_diff_x),(_start_y+_diff_y), duration=1)
        pyautogui.moveTo(_start_x,(_start_y+_diff_y), duration=1)
        pyautogui.moveTo(_start_x,_start_y, duration=1)

    def nothing(self, x):
        #print('Trackbar value: ' + str(x))
        pass

    # [Display calibrate images to confirm they look good]:
    def calibrate_bobber(self):
        # [Check for config files]:
        config_filename = 'configs/bobber.json'
        if os.path.isfile(config_filename):
            _use_calibrate_config = input('[Use calibration from config for bobber?]: ')
            _use_calibrate_config = False if (_use_calibrate_config.lower() == 'n' or _use_calibrate_config.lower() == 'no') else True
        else:
            _use_calibrate_config = False

        # [Set HSV mask from configs]:
        if _use_calibrate_config:
            with open(config_filename) as config_file:
                configs = json.load(config_file)
                JSON_bobber_lower_hsv  = configs['bobber_lower_hsv']
                JSON_bobber_upper_hsv  = configs['bobber_upper_hsv']
                lower_hsv = numpy.array([JSON_bobber_lower_hsv.get('hue'), JSON_bobber_lower_hsv.get('saturation'), JSON_bobber_lower_hsv.get('value')])
                upper_hsv = numpy.array([JSON_bobber_upper_hsv.get('hue'), JSON_bobber_upper_hsv.get('saturation'), JSON_bobber_upper_hsv.get('value')])
            _calibrate_good = True
            self.thresh_image()
        else:
            input('[Enter to calibrate Bobber!]: 3sec')
            time.sleep(3)

            # [Capture of calibration image]:
            if sys.platform == 'darwin':
                nemo = self.grab_rect(self._scanarea_start, self._scanarea_stop, mod=2)
                nemo = self.resize_image(nemo, scale_percent=50)
            else:
                nemo = self.grab_rect(self._scanarea_start, self._scanarea_stop, mod=1)
            lower_hsv = self.bobber_lower_hsv
            upper_hsv = self.bobber_upper_hsv

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
            cv2.moveWindow(window_name, 10,10) 

            # [Create trackbars for Hue]:
            cv2.createTrackbar('LowerH',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('LowerH',window_name, lh)
            cv2.createTrackbar('UpperH',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('UpperH',window_name, uh)

            # [Create trackbars for Saturation]:
            cv2.createTrackbar('LowerS',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('LowerS',window_name, ls)
            cv2.createTrackbar('UpperS',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('UpperS',window_name, us)

            # [Create trackbars for Value]:
            cv2.createTrackbar('LowerV',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('LowerV',window_name, lv)
            cv2.createTrackbar('UpperV',window_name,0,255,self.nothing)
            cv2.setTrackbarPos('UpperV',window_name, uv)

            font = cv2.FONT_HERSHEY_SIMPLEX

            # [Alert user calibration image is ready]:
            playsound.playsound('audio/sms_alert.mp3')

            # [Keep calibration window open until ESC is pressed]:
            while True:
                # [Threshold the HSV image]:
                mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
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

            # [Save Calibration image]: (Great for setup debug)
            if _calibrate_good:
                mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
                imageio.imwrite('calibrate_thresh_bobber{0}.png'.format(self._thresh_cnt), mask)
                self._thresh_cnt+=1

            # [Update config file]:
            if _calibrate_good and _use_calibrate_config == False:
                (lh, ls, lv) = lower_hsv
                (uh, us, uv) = upper_hsv

                print('[Saving calibration to: {0}]'.format(config_filename))

                # [Load config file into local variables]:
                with open(config_filename) as config_file:
                    config = json.load(config_file)
  
                # [Update config for current calibration]:
                config.update({"bobber_lower_hsv": {"hue": int(lh), "saturation": int(ls), "value": int(lv)}})
                config.update({"bobber_upper_hsv": {"hue": int(uh), "saturation": int(us), "value": int(uv)}})

                # [Save values back to config file to update them]:
                with open(config_filename, 'w') as fp:
                    json.dump(config, fp)

        # [Update Globals]:
        if _calibrate_good:
            self.bobber_lower_hsv = lower_hsv
            self.bobber_upper_hsv = upper_hsv
        else:
            # [Bad calibration, try again]:
            self.calibrate_bobber()

    def thresh_image(self):
        if sys.platform == 'darwin':
            nemo = self.grab_rect(self._scanarea_start, self._scanarea_stop, mod=2)
            nemo = self.resize_image(nemo, scale_percent=50)
        else:
            nemo = self.grab_rect(self._scanarea_start, self._scanarea_stop, mod=1)

        lower_hsv = self.bobber_lower_hsv
        upper_hsv = self.bobber_upper_hsv

        # [Median Blur]:
        # [Convert BGR to HSV]:
        nemo = cv2.medianBlur(nemo, 5)
        hsv = cv2.cvtColor(nemo, cv2.COLOR_BGR2HSV)
        nemo_masked = cv2.inRange(hsv, lower_hsv, upper_hsv)

        if self._thresh_cnt<0:
            imageio.imwrite('screen_thresh_bobber{0}.png'.format(self._thresh_cnt), nemo_masked)
        self._thresh_cnt+=1

        return nemo_masked