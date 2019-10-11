import os
import sys
import time
import pyaudio
import numpy as np


# https://stackoverflow.com/questions/26573556/record-speakers-output-with-pyaudio
# pacmd load-module module-loopback latency_msec=5

#To have launchd start pulseaudio now and restart at login:
#  brew services start pulseaudio

#Or, if you don't want/need a background service you can just run:
#  pulseaudio

# pacmd list-sources | grep -e 'index:' -e device.string -e 'name:'

# /etc/pulse/default.pa
# ...
# set-default-source alsa_output.pci-0000_04_01.0.analog-stereo.monitor
# ...

_timer_elapsed = 0
_timer_start = time.time()

def listen_splash(threshold):
    global _timer_start
    global _timer_elapsed

    CHUNK = 2048
    RATE = 44100
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    #dev_idx = 0
    #stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, input_device_index=dev_idx, frames_per_buffer=CHUNK)

    try:
        _splash_detected = False
        while _timer_elapsed < 30 and _splash_detected==False:
            data = np.fromstring(stream.read(CHUNK),dtype=np.int16)
            peak=np.average(np.abs(data))*2
            bars="#"*int(50*peak/2**16)

            #if peak > 1000:
            print("%05d %s"%(peak,bars))

            #if peak > threshold:
            #    print '[SPLASH DETECTED!]'
            #    _splash_detected = True

            _timer_elapsed = (time.time() - _timer_start)
    except KeyboardInterrupt:
        print 'bye'
        sys.exit(1)


#[0]: listen_splash() should take average of sound to use as baseline for thresholding
#[1]: listen_splash() should use *speaker* volume output rather than *microphone* input of speaker
if __name__ == '__main__':
    listen_splash(3500)
    print '[fin].'

# https://apple.stackexchange.com/questions/221980/os-x-route-audio-output-to-audio-input
# https://www.vb-audio.com/Voicemeeter/index.htm
# https://www.rogueamoeba.com/loopback/