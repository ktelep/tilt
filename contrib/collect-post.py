#!/usr/bin/env python

import urllib
import urllib2
import datetime
import time
import json

url = 'http://tilt.cfapps.io/safe_dump?min_score=%d'
spring_url = 'http://localhost:6667'
min_score = 0

while True:
    time.sleep(0.5)
    header = {"pragma-directive": "no-cache"}
    print url % (min_score,)
    req = urllib2.Request(url % min_score, headers=header)
    try:
        page = urllib2.urlopen(req)
    except urllib2.HTTPError:
        continue
    parsed_data = json.loads(page.read())
    min_score = parsed_data['timestamp']
    for i in parsed_data['data']:
        info = json.loads(i)
        # Convert the timestamp to something Tableau likes
        ts = datetime.datetime.strptime(str(info['timestamp']),
                                        '%Y%m%d%H%M%S%f')
        timestamp = ts.strftime("%d%b%Y:%H:%M:%S.%f")
        info['iso_timestamp'] = timestamp
        print json.dumps(info)
        # Send POST request to spring
        req = urllib2.Request(spring_url, json.dumps(info))
        response = urllib2.urlopen(req)
        result = response.read()
        response.close()

    page.close()
