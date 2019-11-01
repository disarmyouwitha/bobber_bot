import os
import sys
import time
import numpy
import pyaudio
import playsound

# https://github.com/mattingalls/Soundflower
# https://github.com/mattingalls/Soundflower/releases/download/2.0b2/Soundflower-2.0b2.dmg
# ^ (DMG for installing, definitely preferred)

# [Callback for splash detection!]:
def audio_callback(in_data, frame_count, time_info, status):
    data = numpy.frombuffer(in_data ,dtype=numpy.int16)

    peak = numpy.average(numpy.abs(data))*2
    peak = int(peak)
    print(peak)

    if peak > 10000:
        print('Splash detected: {0}'.format(peak))
        sys.exit(1)

    return data, pyaudio.paContinue



# [CHANGE DEV INDEX HERE TO TEST]:
def listen_splash():
    pa = pyaudio.PyAudio()

    if sys.platform == 'darwin':
        dev_idx = 2 # For my OSX machine it's 2, might be different for you
    else:
        dev_idx = 1 # For my windows machine it's 1, might be different for you
    # ^(System Dependant, use audio.py to configure)

    _audio_stream = pa.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, input_device_index=dev_idx, stream_callback=audio_callback)

    _timer_elapsed = 0
    _timer_start = time.time()
    _audio_stream.start_stream()

    while _audio_stream.is_active():
        try:
            _timer_elapsed = (time.time() - _timer_start)

            if _timer_elapsed >= 30:
                print('[timer_elapsed]')
                sys.exit(1)

        except Exception as e:
            print(e)
            _audio_stream.stop_stream()
            _audio_stream.close()
            pa.terminate()

            # [Die Young, Leave beautiful code]:
            sys.exit(1) 

def detect_devices():
    pa = pyaudio.PyAudio()

    # detect devices:
    host_info = pa.get_host_api_info_by_index(0)    
    device_count = host_info.get('deviceCount')
    devices = []

    # iterate between devices:
    for i in range(0, device_count):
        print('dev_idx: {0}'.format(i))
        device = pa.get_device_info_by_host_api_device_index(0, i)
        devices.append(device['name'])
        print(pa.get_device_info_by_host_api_device_index(0, i))
        print('-------')

    print()
    print('[Now go set `dev_idx` to Soundflower/Mixer index && uncomment `listen_splash()` to check that the program "hears" your speakers output]')
    print()


if __name__ == '__main__':
    #[0]: Display device index / device info for all devices found:
    detect_devices()

    #[1]: Used to find proper index:
    listen_splash() 