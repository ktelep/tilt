from flask import Flask, request, render_template, jsonify, redirect
from flask import make_response, request, current_app
import os
import sys
import time
import json
import redis
from datetime import timedelta
from CloudFoundryClient import CloudFoundryClient
from functools import update_wrapper

app = Flask(__name__, static_url_path='/static')

# Determine our running port.  Updated to support Diego which uses the
# 'PORT' environment variable, vs non-Diego which uses VCAP_APP_PORT

if os.getenv('VCAP_APP_PORT'):
    port = os.getenv('VCAP_APP_PORT')
elif os.getenv('PORT'):
    port = os.getenv('PORT')
else:
    port = "8080"

redis_keys = {
                'pivotalcf': {
                                'service': 'rediscloud',
                                'host': 'hostname',
                                'port': 'port',
                                'password': 'password'
                            },
                'pcfdev': {
                                'service': 'p-redis',
                                'host': 'host',
                                'port': 'port',
                                'password': 'password'
                            },
                'bluemix': {
                                'service': 'redis-2.6',
                                'host': 'hostname',
                                'port': 'port',
                                'password': 'password'
                            }
            }


def getServiceInfo():
    redis_service = None
    for value in redis_keys.iteritems():
        # Service Key Name
        service = value[1]['service']

        if service in json.loads(os.environ['VCAP_SERVICES']):
            redis_service = json.loads(os.environ['VCAP_SERVICES'])[service][0]
            break
        else:
            continue

    if redis_service:
        return redis_service
    else:
        raise KeyError("Unable to identify Redis Environment")


def getHostKey():
    hostKey = None
    for value in redis_keys.iteritems():
        # Host Key Name
        host = value[1]['host']
        if host in credentials:
            hostKey = host
            break
        else:
            continue

    if hostKey:
        return hostKey
    else:
        raise KeyError("Unable to identify Redis Host")

app_name = None
cf_user = None
cf_pass = None
visualization = 'http://tiltvis.cfapps.io'

if os.getenv('VCAP_APPLICATION'):
    app_name = json.loads(os.environ['VCAP_APPLICATION'])['application_name']

if os.getenv('customconfig'):
    cf_user = json.loads(os.environ['customconfig'])['cfuser']
    cf_pass = json.loads(os.environ['customconfig'])['cfpass']

# Connect to our Redis service in cloudfoundry
if os.getenv('VCAP_SERVICES'):
    redis_service = getServiceInfo()

    credentials = redis_service['credentials']
    hostKey = getHostKey()
    print credentials[hostKey]
    pool = redis.ConnectionPool(host=credentials[hostKey],
                                port=credentials['port'],
                                password=credentials['password'],
                                max_connections=2)

    r = redis.Redis(connection_pool=pool)
else:   # Local redis server as a failback
    r = redis.Redis()

try:
    # Test our connection
    response = r.client_list()

    r.set("server:" + port, 0)
    r.expire("server:" + port, 3)

except redis.ConnectionError:
    print "Unable to connect to a Redis server, check environment"
    sys.exit(1)


def timestamp():
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return int(time.strftime('%Y%m%d%H%M%S', localtime) + milliseconds)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/send', methods=['POST'])
def receive_post_data():
    if request.method == 'POST':
        current_time = timestamp()
        client_data = json.loads(request.form['data'])

        #  Sanitize numerical data, so any "None" or Null values become 0's
        for key in ["TiltFB", "TiltLR", "Direction", "altitude",
                    "latitude", "longitude"]:
            if client_data[key] is None:
                print "Sanitized: %s on %s" % (key, client_data['devid'])
                client_data[key] = 0

        client_data['timestamp'] = current_time

        # Key is devid:<UUID>, expires in 3 seconds
        r.zadd('devid:' + client_data['devid'],
               json.dumps(client_data), current_time)
        r.expire('devid:' + client_data['devid'], 3)

        # Update # of connections processed
        r.incr('server:' + port)
        r.expire('server:' + port, 3)
        return "success"
    return "fail"


@app.route('/show')
def show():
    return render_template('dynamic.html')


@app.route('/safe_dump', methods=['GET', 'POST'])
@crossdomain(origin=visualization)
def safe_dump():
    min_score = int(request.args.get('min_score', 0))
    only_latest = request.args.get('latest', None)
    valid_keys = r.keys('devid:*')
    data = list()
    instances = list()
    max_score = timestamp()
    if only_latest:
        for key in valid_keys:
            data.extend(r.zrevrange(key, 0, 0))
    else:
        for key in valid_keys:
            data.extend(r.zrangebyscore(key, min_score, max_score))

    for key in r.keys('server:*'):
        inst = "%s:%s" % (key, r.get(key))
        instances.append(inst)

    return jsonify(timestamp=max_score, data=data, min_score=min_score,
                   instance=instances)


@app.route('/scale', methods=['POST'])
def scale_app():
    new_instances = int(request.form['instances'])
    if ((new_instances > 8) or (new_instances < 1)):
        return "fail"
    else:
        if cf_user:
            client = CloudFoundryClient(cf_user, cf_pass)
            client.authenticate()
            app_data = client.get_app(app_name)
            client.scale_app(app_data['url'], new_instances)

    return "success"


@app.route('/view')
def view_redirect():
    return redirect('http://tilt-view.cfapps.io')


if __name__ == '__main__':
    app.debug = True
    print "Running on Port: " + port
    app.run(host='0.0.0.0', port=int(port))
