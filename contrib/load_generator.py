#!/usr/bin/env python

import string
import requests
import multiprocessing
import json
from time import sleep
from random import random, choice

#url = "http://tilt.cfapps.io/send"
url = "http://localhost:5000/send"


def s4(size=4, chars=string.ascii_lowercase + string.digits):
    return ''.join(choice(chars) for _ in range(size))


def guid():
    return s4()+"-"+s4()


def worker():
    my_id = guid()
    while True:
        # Create a fake payload with random data
        payload = dict(devid=my_id, TiltLR=random(), TiltFB=random(),
                       Direction=random(), OS="LoadTest")
        r = requests.post(url, dict(data=json.dumps(payload)))
        if r.status_code != 200:
            print "failed"
        print r.elapsed
        sleep(0.05)

if __name__ == '__main__':
    jobs = []
    for i in range(10):
        p = multiprocessing.Process(target=worker)
        jobs.append(p)
        p.start()
