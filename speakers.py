import os
import sys
import time
import pyaudio
import numpy as np

# https://github.com/mattingalls/Soundflower

_timer_elapsed = 0
_timer_start = time.time()

def listen_splash(threshold):
    global _timer_start
    global _timer_elapsed

    CHUNK = 2048
    RATE = 44100
    p = pyaudio.PyAudio()
    #stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    dev_idx = 2
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, input_device_index=dev_idx, frames_per_buffer=CHUNK)

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
                    _splash_detected = True

            _timer_elapsed = (time.time() - _timer_start)
    except KeyboardInterrupt:
        print('bye')
        sys.exit(1)


#[0]: listen_splash() should take average of sound to use as baseline for thresholding
#[1]: listen_splash() should use *speaker* volume output rather than *microphone* input of speaker
if __name__ == '__main__':
    listen_splash(2000)
    print('[fin].')