import pyaudio 

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

print(devices)
print('-------')
print(p.get_device_info_by_host_api_device_index(0, 0)) # mic
print('-------')
print(p.get_device_info_by_host_api_device_index(0, 1)) # other
print('-------')
print(p.get_device_info_by_host_api_device_index(0, 2)) # loopback