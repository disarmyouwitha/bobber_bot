import numpy
import soundcard as sc

# [get a list of all speakers]:
speakers = sc.all_speakers()
#print(speakers)

# [get the current default speaker on your system]:
default_speaker = sc.default_speaker()
#print(default_speaker)

one_speaker = sc.get_speaker('Loopback')
print(one_speaker)
one_mic = sc.get_microphone('Loopback')
print(one_mic)

# https://rogueamoeba.com/audiohijack/