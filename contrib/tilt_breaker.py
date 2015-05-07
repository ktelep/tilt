#!/usr/bin/env python

import sys
import getopt
import string
import requests
import multiprocessing
import json
from time import sleep
from random import random, choice, randrange

url = ""

fake_gps_data = [[42.40, -73.45],   # Albany, NY
                 [35.05, -106.39],  # Albaquerque, NM
                 [43.36, -116.13],  # Boise, ID
                 [32.47, -79.56],   # Charleston, SC
                 [46.49, -92.5],    # Duluth, MI
                 [19, -99.13],      # Mexico City, Mexico
                 [45.5, -73.5],     # Montreal
                 ]


def s4(size=4, chars=string.ascii_lowercase + string.digits):
    return ''.join(choice(chars) for _ in range(size))


def guid():
    return s4()+"-"+s4()+"-Sim"


def worker():
    my_id = guid()
    lat, lon = fake_gps_data[randrange(0, len(fake_gps_data))]
    while True:
        # Create a fake payload with random data
        print lat, lon
        payload = dict(devid=my_id, TiltLR=None, TiltFB=None,
                       Direction=random(), altitude=0, latitude=lat,
                       longitude=lon, OS="LoadTest")
        print json.dumps(payload)
        r = requests.post(url, dict(data=json.dumps(payload)))
        if r.status_code != 200:
            print "failed with %s" % str(r.status_code)
        print r.elapsed
        sleep(0.05)


def display_usage():
    print("Usage: %s -t http://targeturl:port -n <number of workers>"
          % sys.argv[0])
    sys.exit(0)

if __name__ == '__main__':

    num_workers = 0

    try:
        myopts, args = getopt.getopt(sys.argv[1:], "t:n:")
    except:
        display_usage()

    if (len(myopts) != 2):
        display_usage()

    for o, a in myopts:
        if o == '-t':
            if '/send' not in url:
                url = a + '/send'
            else:
                url = a
            print "Setting target URL to: %s" % url
        elif o == '-n':
            print "Number of workers: %s" % a
            num_workers = int(a)
        else:
            display_usage()

        jobs = []
        for i in range(num_workers):
            p = multiprocessing.Process(target=worker)
            jobs.append(p)
            p.start()
