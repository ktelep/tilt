from flask import Flask, request, render_template
import time
import os
import json
import redis

app = Flask(__name__, static_url_path='/static')
port = os.getenv('VCAP_APP_PORT', '5000')

rediscloud_service = json.loads(os.environ['VCAP_SERVICES'])['rediscloud'][0]
credentials = rediscloud_service['credentials']
pool = redis.ConnectionPool(host=credentials['hostname'],
                            port=credentials['port'],
                            password=credentials['password'],
                            max_connections=2)

r = redis.Redis(connection_pool=pool)


def timestamp():
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return int(time.strftime('%Y%m%d%H%M%S', localtime) + milliseconds)


@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/send', methods=['POST'])
def receive_post_data():
    if request.method == 'POST':
        data_line = ":".join([request.form['UUID'],
                              request.form['TiltLR'],
                              request.form['TiltFB'],
                              request.form['Direction'],
                              request.form['OS']
                              ])
        # Key is uuid:<UUID>, expires in 3 seconds
        r.zadd('uuid:' + request.form['UUID'], data_line, timestamp())
        r.expire('uuid:' + request.form['UUID'], 3)
        return "success"
    return "fail"


@app.route('/show')
def show():
    return render_template('dynamic.html')


@app.route('/dump')
def spring_dump():
    valid_keys = r.keys('uuid:*')
    data = list()
    max_score = timestamp()
    for key in valid_keys:
        data.extend(r.zrange(key, 0, max_score))
        r.zremrangebyscore(key, 0, max_score)
    return ",".join(map(str, data))

if __name__ == '__main__':
    app.debug = True
    print "Port" + port
    app.run(host='0.0.0.0', port=int(port))
