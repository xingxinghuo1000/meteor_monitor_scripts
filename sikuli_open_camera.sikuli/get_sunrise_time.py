# encoding=utf-8
import datetime
import json
import astral
from astral import LocationInfo
from astral.sun import sun

city = LocationInfo(('Beijing', 'China',  39.92, 116.46, 'Asia/Shanghai', 0))

def main():
    s = sun(city.observer, date=datetime.date.today(), tzinfo=city.timezone)
    sunrise=s['sunrise'].strftime("%Y-%m-%d %H:%M:%S")
    sunset=s['sunset'].strftime("%Y-%m-%d %H:%M:%S")
    # 计算今天的日出时间
    print(json.dumps([sunrise, sunset]))

if __name__ == "__main__":
    main()
    
        

    
