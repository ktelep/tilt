from flask import Flask, request, render_template
from flask.ext.socketio import SocketIO
import os
import json
import redis

app = Flask(__name__, static_url_path='/static')
port = os.getenv('VCAP_APP_PORT', '5000')
socketio = SocketIO(app)
pool = None

if not os.getenv('VCAP_SERVICES'):
    # If we're running locally, use the local redis instance
    pool = redis.ConnectionPool(host='localhost',port=6379,db=0)
else:
    # Otherwise, we use the params passed in the CF environment
    rediscloud_service = json.loads(os.environ['VCAP_SERVICES'])['rediscloud'][0]
    credentials = rediscloud_service['credentials']
    pool = redis.ConnectionPool(host=credentials['hostname'], 
                            port=credentials['port'],
                            password=credentials['password'],
                            max_connections=2)


r = redis.Redis(connection_pool=pool)

@app.route('/')
def index_page():
    return render_template('index.html')

@socketio.on('data_in')
def handle_incoming_data(data):
    data_line = ":".join([data['UUID'], str(data['TiltLR']), 
                          str(data['TiltFB']), str(data['Direction']),
                          data['OS']
                          ])
    print data_line
    r.lpush('data_list', data_line)
    r.ltrim('data_list', 0, 99)
    return "success"

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
    data_range = r.lrange('data_list', -50, -1)
    if data_range:
        return ",".join(map(str, data_range))
    return

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(port))
