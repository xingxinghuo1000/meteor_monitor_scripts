import json
import capture_by_ffmpeg as cap


li = cap.get_device_list()
for device_name in li:
    ret = cap.get_video_format_support(device_name)
    print(json.dumps(ret, indent=2))

