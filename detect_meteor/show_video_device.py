import capture_by_ffmpeg as cap
import json


li = cap.get_device_list()
s = json.dumps(li, ensure_ascii=False)
print(s)



