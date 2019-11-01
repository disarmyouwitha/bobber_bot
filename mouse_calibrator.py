import sys
import cv2
import json
import time
import imageio
import screen_pixel
from pymouse import PyMouseEvent

class mouse_calibrator(PyMouseEvent):
    _sp = None
    _nemo = None
    _click_cnt = 0
    _y_offset = None
    _tooltip_stop = None
    _tooltip_start = None
    _scanarea_stop = None
    _scanarea_start = None
    _fishing_pole_loc = None
    _fishing_skill_loc = None
    _fishing_bauble_loc = None
    _calibrating_tooltip = False
    _calibrating_scanarea = False
    _calibrating_mouse_mode = False

    def __init__(self, state=None):
        PyMouseEvent.__init__(self)
        self._sp = screen_pixel.screen_pixel()

        # [Trying to account for differences in OSX/Windows]:
        if sys.platform == 'darwin':
            self._y_offset = -80
        else:
            self._y_offset = -30

        if state == 'calibrate_mouse_actionbar':
            print('[Calibrating fishing_pole action bar location! Alt-tab, go left-click it && come back here!]')
            self._fishing_pole_loc = None
            self._fishing_skill_loc = None
            self._fishing_bauble_loc = None
            self._calibrating_mouse_mode = True
        elif state == 'calibrate_scanarea':
            print('[Calibrating Scan Area: Click at the top-left of scan area, && drag to lower-right and release click.]')
            self._scanarea_stop = None
            self._scanarea_start = None
            self._calibrating_scanarea = True
            self._sp.capture()
            nemo = self._sp._numpy

            # [Windows might need this at 50% in WoW too?]:
            if sys.platform == 'darwin':
                nemo = self._sp.resize_image(nemo, scale_percent=50)

            cv2.imshow('Calibrate Scanarea', nemo)
            cv2.moveWindow('Calibrate Scanarea', 0,0)
        elif state == 'calibrate_tooltip':
            input('[Enter to calibrate Tooltip]: 3sec')
            time.sleep(3)
            print('Click at the top-left of the tooltip, && drag to lower-right and release.]')
            self._tooltip_stop = None
            self._tooltip_start = None
            self._calibrating_tooltip = True
            self._sp.capture() #Capture so we can get width/height
            self.nemo = self._sp.grab_rect({"x": int(self._sp._width/2), "y": int(self._sp._height/2)}, {"x": int(self._sp._width), "y": int(self._sp._height)}, mod=1, nemo=self._sp._numpy)

            cv2.imshow('Calibrate Tooltip', self.nemo)
            cv2.moveWindow('Calibrate Tooltip', 0,0)
        else:
            print('[Mouse Listening]')

    def save_actionbar_calibration(self):
        # [Load up current configs]:
        config_filename = 'configs/mouse_actionbar.json'
        with open(config_filename) as config_file:
            configs = json.load(config_file)

        # [Update config for locations]:
        configs.update(self._fishing_pole_loc)
        configs.update(self._fishing_skill_loc)
        configs.update(self._fishing_bauble_loc)

        # [Save values back to config file to update values]:
        with open(config_filename, 'w') as fp:
            json.dump(configs, fp)

    def save_scanarea(self):
        # [Load up current configs]:
        config_filename = 'configs/scanarea.json'
        with open(config_filename) as config_file:
            configs = json.load(config_file)

        self._scanarea_start['scanarea_start']['y'] += self._y_offset
        self._scanarea_stop['scanarea_stop']['y'] += self._y_offset

        # [Update config for locations]:
        configs.update(self._scanarea_start)
        configs.update(self._scanarea_stop)

        # [Save values back to config file to update values]:
        with open(config_filename, 'w') as fp:
            json.dump(configs, fp)

    def save_tooltip(self):
        # [Load up current configs]:
        config_filename = 'configs/tooltip.json'
        with open(config_filename) as config_file:
            configs = json.load(config_file)

        # [Add _y_offset]:
        self._tooltip_start['tooltip_start']['y'] += self._y_offset
        self._tooltip_stop['tooltip_stop']['y'] += self._y_offset

        # [Screenshot for `tooltip_control_gray`]:
        nemo = self._sp.grab_rect(self._tooltip_start['tooltip_start'], self._tooltip_stop['tooltip_stop'], mod=1, nemo=self.nemo)
        gray_nemo = cv2.cvtColor(nemo, cv2.COLOR_BGR2GRAY)
        imageio.imwrite('img/tooltip_control_gray.png', gray_nemo)

        # [Tooltip calibration starts from lower half, right half]:
        self._tooltip_start['tooltip_start']['y'] += int(self._sp._height/2)
        self._tooltip_start['tooltip_start']['x'] += int(self._sp._width/2)
        self._tooltip_stop['tooltip_stop']['y'] += int(self._sp._height/2)
        self._tooltip_stop['tooltip_stop']['x'] += int(self._sp._width/2)

        # [Update config for locations]:
        configs.update(self._tooltip_start)
        configs.update(self._tooltip_stop)

        # [Save values back to config file to update values]:
        with open(config_filename, 'w') as fp:
            json.dump(configs, fp)

    def click(self, x, y, button, press):
        int_x = int(x)
        int_y = int(y)

        # [Code for Mouse Mouse Calibration]:
        if button==1 and press and self._calibrating_mouse_mode:
            if self._fishing_pole_loc == None:
                self._fishing_pole_loc = {"fishing_pole" : { "x":int_x, "y":int_y }}
                print(self._fishing_pole_loc)
                print('[Calibrating fishing_skill action bar location! Alt-tab, go left-click it && come back here!]')
            elif self._fishing_skill_loc == None:
                self._fishing_skill_loc = {"fishing_skill" : { "x":int_x, "y":int_y }}
                print(self._fishing_skill_loc)
                print('[Calibrating fishing_bauble action bar location! Alt-tab, go left-click it && come back here!]')
            elif self._fishing_bauble_loc == None:
                self._fishing_bauble_loc = {"fishing_bauble" : { "x":int_x, "y":int_y }}
                print(self._fishing_bauble_loc)
                print('Click one more time for Good Luck!')
            else:
                print('[Ending Calibration]')
                self._calibrating_mouse_mode = False
                self.save_actionbar_calibration()
                self.stop()

        # [Code for Scan Area Calibration]:
        if button==1 and self._calibrating_scanarea:
            print('Woomy!: ({0}, {1})'.format(int_x, int_y))

            if press:
                self._scanarea_start = {"scanarea_start" : { "x":int_x, "y":int_y }}
            else:
                self._scanarea_stop = {"scanarea_stop" : { "x":int_x, "y":int_y }}

            # [Send coords back over to bobberbot]:
            if self._scanarea_stop is not None:
                self.save_scanarea()
                self._calibrating_scanarea = False
                cv2.destroyAllWindows()
                self.stop()

        # [Code for Scan Area Calibration]:
        if button==1 and self._calibrating_tooltip:
            print('Woomy!: ({0}, {1})'.format(int_x, int_y))

            if press:
                self._tooltip_start = {"tooltip_start" : { "x":int_x, "y":int_y }}
            else:
                self._tooltip_stop = {"tooltip_stop" : { "x":int_x, "y":int_y }}

            # [Send coords back over to bobberbot]:
            if self._tooltip_stop is not None:
                self.save_tooltip()
                self._calibrating_tooltip = False
                cv2.destroyAllWindows()
                self.stop()