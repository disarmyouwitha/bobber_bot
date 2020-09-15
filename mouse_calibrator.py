import os
import sys
import cv2
import json
import time
import imageio
import screen_pixel
from pymouse import PyMouseEvent

class mouse_calibrator(PyMouseEvent):
    _sp = None
    _nemo = 0
    _state = None
    _y_offset = None
    _coords_stop = None
    _coords_start = None
    _yield_skills = None
    _first_click = None

    def __init__(self, state=None):
        PyMouseEvent.__init__(self)
        self._sp = screen_pixel.screen_pixel()
        self._state = state
        self._first_click = True

        # [Trying to account for differences in OSX/Windows]:
        if sys.platform == 'darwin':
            self._y_offset = 0#-40 #-80 #-75 ???
        else:
            self._y_offset = -30

        if state == 'mouse_actionbar':
            print('[Go click your fishing_pole on your actionbar! Come back here!]')
            self._yield_skills = self.yield_actionbar_skills()

        elif state == 'scanarea' or state == 'health' or state == 'login':
            print('[Calibrating {0}: Click at the top-left of the area, then click on the lower-right area you want to scan.]'.format(state))
        elif state == 'tooltip':
            self._sp.capture()
            self._nemo = self._sp._numpy
            print('Click at the top-left of the tooltip, then again on the lower-right of the tooltip.]')
        else:
            print('[mouse_calibrator started without state]')
            sys.exit(1)

    def yield_actionbar_skills(self):
        yield "fishing_pole_stop"
        yield "fishing_skill_stop"
        yield "fishing_bauble_stop"

    def save_actionbar_coords(self, _action_bar_coords):
        # [Load up current configs]:
        config_filename = 'configs/coord_configs.json'
        with open(config_filename) as config_file:
            configs = json.load(config_file)

        # [Update config for locations]:
        configs.update(_action_bar_coords)

        # [Save values back to config file to update values]:
        with open(config_filename, 'w') as fp:
            json.dump(configs, fp)

    # [general purpose save]:
    def save_box_coords(self, _coords_start, _coords_stop, config_name):
        # [Load up current configs]:
        config_filename = 'configs/coord_configs.json'
        with open(config_filename) as config_file:
            configs = json.load(config_file)

        # [Add _y_offset]:
        _coords_start[config_name+'_start']['y'] += self._y_offset
        _coords_stop[config_name+'_stop']['y'] += self._y_offset

        # [Screenshot for `_control_gray.png`]:
        if 'tooltip' in config_name or 'health' in config_name or 'login' in config_name:
            nemo = self._sp.grab_rect(_coords_start[config_name+'_start'], _coords_stop[config_name+'_stop'], mod=2, nemo=self._nemo)
            gray_nemo = cv2.cvtColor(nemo, cv2.COLOR_BGR2GRAY)
            imageio.imwrite('configs/{0}_control_gray.png'.format(config_name), gray_nemo)
            

        # [Update config for locations]:
        configs.update(_coords_start)
        configs.update(_coords_stop)

        # [Save values back to config file to update values]:
        with open(config_filename, 'w') as fp:
            json.dump(configs, fp)

    def offset_configs(self, _coords_start, _coords_stop, config_name):
        _coords_start[config_name+'_start']['y'] += int(self._sp._height/2)
        _coords_start[config_name+'_start']['x'] += int(self._sp._width/2)
        _coords_stop[config_name+'_stop']['y'] += int(self._sp._height/2)
        _coords_stop[config_name+'_stop']['x'] += int(self._sp._width/2)

        return (_coords_start, _coords_stop)

    def click(self, x, y, button, press):
        int_x = int(x)
        int_y = int(y)

        # [Code for Mouse Mouse Calibration]:
        if button==1 and press and self._state=='mouse_actionbar':
            actionbar_skill = next(self._yield_skills)
            self.save_actionbar_coords({actionbar_skill : { "x":int_x, "y":int_y }})

            if 'fishing_pole_stop' in actionbar_skill:
                print('[Go click your fishing_skill on your actionbar! Come back here after!]')
            elif 'fishing_skill_stop' in actionbar_skill:
                print('[Go click your fishing_bauble on your actionbar! Come back here after!]')
            elif 'fishing_bauble_stop' in actionbar_skill:
                print('[Saving to `configs/coord_configs.json`!]')
                self.stop()

        if button==1 and self._state!='mouse_actionbar':
            print('Woomy!: ({0}, {1})'.format(int_x, int_y))

            #if press:
            if self._first_click and press:
                self._coords_start = {"{0}_start".format(self._state) : { "x":int_x, "y":int_y }}
                self._first_click = False
            elif press:
                self._coords_stop = {"{0}_stop".format(self._state) : { "x":int_x, "y":int_y }}

            # [Save bounds of box]:
            if self._coords_stop is not None:
                self.save_box_coords(self._coords_start, self._coords_stop, self._state)
                self.stop()
