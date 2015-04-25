#!/usr/bin/env python

import urllib2 as urllib
import datetime
import time
import json

url = 'http://tilt.cfapps.io/safe_dump?min_score=%d'
filename = './tilt_output.log'
max_records = 200 

min_score = 0
line_count = 0
f = open(filename, 'a')

while True:
    time.sleep(0.5)
    header = {"pragma-directive": "no-cache"}
    print url % (min_score,)
    req = urllib.Request(url % min_score, headers=header)
    try:
        page = urllib.urlopen(req)
    except urllib.HTTPError:
        continue
    parsed_data = json.loads(page.read())
    min_score = parsed_data['timestamp']
    for i in parsed_data['data']:
        info = i.split(':')
        # Convert the timestamp to something Tableau likes
        ts = datetime.datetime.strptime(info[0],'%Y%m%d%H%M%S%f')
        timestamp = ts.strftime("%d%b%Y:%H:%M:%S.%f")

        out_data=dict()
        out_data['id'] = info[0]
        out_data['timestamp'] = timestamp
        out_data['device_id'] = info[1]
        out_data['tiltlr'] = float(info[2])
        out_data['tiltfb'] = float(info[3])
        out_data['direction'] = float(info[4])
        out_data['deviceos'] = info[5]
        out_data['latitiude'] = info[6]
        out_data['longitude'] = info[7]
        out_data['altitude'] = info[8]
        f.write(json.dumps(out_data))
        f.write("\n")
        f.flush()

    f.flush() 
    line_count = line_count + 1
    page.close()
    if (line_count > max_records):
        f.close()
        open(filename, 'w').close()
        f = open(filename, 'a')
        line_count = 0
