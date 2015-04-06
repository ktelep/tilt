#!/usr/bin/env python

import urllib2 as urllib
import time

url = 'http://tilt.cfapps.io/dump'
filename = 'output_file.log'
max_records = 50


def checksum(st):
    return reduce(lambda x, y: x+y, map(ord, st))

line_count = 0
checksums = list()
f = open(filename, 'a')

while True:
    time.sleep(0.5)
    header = {"pragma-directive": "no-cache"}
    req = urllib.Request(url, headers=header)
    page = urllib.urlopen(req)
    new_data = page.read()
    new_data_sum = checksum(new_data)
    if new_data_sum not in checksums:
        f.write(new_data.replace(",", "\n"))
        f.write("\n")
        f.flush()
        checksums.append(new_data_sum)
        line_count = line_count + 1
    page.close()
    if (line_count > max_records):
        f.close()
        open(filename, 'w').close()
        f = open(filename, 'a')
        line_count = 0
