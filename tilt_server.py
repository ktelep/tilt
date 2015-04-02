from flask import Flask, request, render_template
import os
import json
import redis

app = Flask(__name__, static_url_path='/static')
port = os.getenv('VCAP_APP_PORT', '5000')

rediscloud_service = json.loads(os.environ['VCAP_SERVICES'])['rediscloud'][0]
credentials = rediscloud_service['credentials']
r = redis.Redis(host=credentials['hostname'],
                port=credentials['port'],
                password=credentials['password'])


@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/send', methods=['POST'])
def receive_post_data():
    if request.method == 'POST':
        data_line = ":".join([request.form['UUID'], request.form['TiltLR'],
                              request.form['TiltFB'], request.form['Direction'],
                              request.form['OS']
                              ])
        r.lpush('data_list', data_line)
        r.ltrim('data_list', 0, 99)
        return "success"
    return "fail"


@app.route('/show')
def show():
    return render_template('dynamic.html')


@app.route('/dump')
def dump_data():
    return ",".join(map(str, r.lrange('data_list', -50, -1)))

if __name__ == '__main__':
    print "Port" + port
    app.run(host='0.0.0.0', port=int(port))
