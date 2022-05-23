# encoding=utf-8
import datetime
import json
import requests


def main():
    today = datetime.datetime.now().strftime("%Y年%m月%d日")
    bytes1 = requests.get("https://richurimo.bmcx.com/beijing__richurimo/").content
    text = bytes1.decode("utf-8")
    for tr in text.split("<tr"):
        if '</tr>' in tr:
            line = tr.split("</tr>")[0]
            if today in line:
                #print(line)
                tds = []
                for td in line.split("<td"):
                    if '</td>' in td:
                        tds.append(td.split(">")[1].split("<")[0])
                ddd = [tds[1], tds[3]]
                print(json.dumps(ddd))
        
if __name__ == "__main__":
    main()
    
        

    
