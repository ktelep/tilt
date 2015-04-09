#!/usr/bin/env python

import urllib2 as urllib
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
    page = urllib.urlopen(req)
    parsed_data = json.loads(page.read())
    min_score = parsed_data['timestamp']
    for i in parsed_data['data']:
        f.write(i)
        f.write("\n")
    f.flush()
    line_count = line_count + 1
    page.close()
    if (line_count > max_records):
        f.close()
        open(filename, 'w').close()
        f = open(filename, 'a')
        line_count = 0
