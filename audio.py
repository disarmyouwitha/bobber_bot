import os
import sys
import time
import pyaudio
import numpy as np

# https://github.com/mattingalls/Soundflower
# https://github.com/mattingalls/Soundflower/releases/download/2.0b2/Soundflower-2.0b2.dmg
# ^ (DMG for installing, definitely preferred)

_timer_elapsed = 0
_timer_start = time.time()

def detect_devices():
    # detect devices:
    p = pyaudio.PyAudio()
    host_info = p.get_host_api_info_by_index(0)    
    device_count = host_info.get('deviceCount')
    devices = []

    # iterate between devices:
    for i in range(0, device_count):
        print(i)
        device = p.get_device_info_by_host_api_device_index(0, i)
        devices.append(device['name'])
        print(p.get_device_info_by_host_api_device_index(0, 1))
        print('-------')

def listen_splash(threshold):
    _timer_elapsed = 0
    _timer_start = time.time()

    CHUNK = 2048
    RATE = 44100
    p = pyaudio.PyAudio()

    dev_idx = 0 # Microphone as input
    dev_idx = 2 # Speakers as input
    if dev_idx > 0:
        print('[Listening| Go cast your pole in WOW and see if it detects the sound of the splash]')
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, input_device_index=dev_idx, frames_per_buffer=CHUNK)
    else:
        print('Listening|(Mic?): Make some noise to see if it registers -- play with the threshold here')
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

    try:
        _splash_detected = False
        while _timer_elapsed < 30 and _splash_detected==False:
            data = np.frombuffer(stream.read(CHUNK),dtype=np.int16)
            peak=np.average(np.abs(data))*2
            bars="#"*int(50*peak/2**16)

            if peak > 1000:
                print('%05d %s'%(peak,bars))

                if peak > threshold:
                    print('[SPLASH DETECTED!]')
                    #_splash_detected = True

            _timer_elapsed = (time.time() - _timer_start)
    except KeyboardInterrupt:
        print('bye')
        sys.exit(1)


if __name__ == '__main__':
    detect_devices()    # Display device index / device info for all devices found.
    listen_splash(2000) # Threshold goes here | You may need to adjust the index from detect devices^
    print('[fin].')