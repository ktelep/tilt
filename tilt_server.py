from flask import Flask, request, render_template, jsonify, redirect
from flask import make_response, current_app
from flask_sslify import SSLify

import os
import sys
import time
import json
import redis
import logging
from datetime import timedelta
from CloudFoundryClient import CloudFoundryClient
from functools import update_wrapper

app = Flask(__name__, static_url_path='/static')
sslify = SSLify(app)

# Determine our running port.  Updated to support Diego which uses the
# 'PORT' environment variable, vs non-Diego which uses VCAP_APP_PORT

if os.getenv('VCAP_APP_PORT'):
    port = os.getenv('VCAP_APP_PORT')
elif os.getenv('PORT'):
    port = os.getenv('PORT')
else:
    port = "8080"


if os.getenv('CF_INSTANCE_INDEX'):
    inst_index = os.getenv('CF_INSTANCE_INDEX')
else:
    inst_index = "UNK"

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

visualization = '*'

if os.getenv('VCAP_APPLICATION'):
    app_name = json.loads(os.environ['VCAP_APPLICATION'])['application_name']

if os.getenv('customconfig'):
    cf_user = json.loads(os.environ['customconfig'])['cfuser']
    cf_pass = json.loads(os.environ['customconfig'])['cfpass']

if os.getenv('visualization_url'):
    visualization = os.environ['visualization_url']
else:
    visualization = '*'

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

    r.set("server:" + inst_index, 0)
    r.expire("server:" + inst_index, 3)

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
        data_length = request.headers["Content-Length"]
        print client_data.keys()
        accel_fields = ["TiltFB", "TiltLR", "Direction"]
        gps_fields = ["altitude", "latitude", "longitude"]
        info_fields = ["OS", "industry"]

        data_fields = accel_fields + gps_fields + info_fields

        #  Sanitize numerical data, so any "None" or Null values become 0's
        for key in data_fields:
            if client_data[key] is None:
                app.logger.info("Sanitized: %s on %s" % (key, client_data['devid']))
                client_data[key] = 0

        client_data['timestamp'] = current_time

        # We're going to use redis pipeline to speed up our transactions
        # to the server, redis is running in the cloud, so we just run all
        # of these commands atomically as a single transaction
        with r.pipeline() as pipe:

            # Key is devid:<UUID>, expires in 3 seconds, this is for live
            # visualization
            pipe.zadd('devid:' + client_data['devid'],
                      json.dumps(client_data), current_time)
            pipe.expire('devid:' + client_data['devid'], 3)

            # There's value in keeping the data for longer periods of time
            # however may want to consider a way to expire some of it....

            # Add key to list of devids and score by last timestamp seen
            pipe.zadd('devidlist', client_data['devid'], current_time)

            # Store bandwidth sizes
            pipe.zadd('devidhistory:'+client_data['devid']+':ReqSize:Values',
                      float(data_length), current_time)

            # Store data for historical history (currently non-expiring)
            # key here is devidhistory:<devid>:data_field
            for key in accel_fields:
                pipe.zadd('devidhistory:'+client_data['devid']+':'+key+':Values',
                          float(client_data[key]), current_time)

            # Other data is stored as just a key->value as the probability of
            # changes in GPS location is small for a devid.
            for key in gps_fields:
                pipe.set('devidhistory:'+client_data['devid']+':'+key+':Values',
                         float(client_data[key]))
 
            for key in info_fields:
                pipe.set('devidhistory:'+client_data['devid']+':'+key+':Values',
                         client_data[key])

            # Update # of connections processed
            pipe.incr('server:' + inst_index)
            pipe.expire('server:' + inst_index, 3)

            pipe.execute()

        # Handle an outgoing message to the client
        mess = r.get("message:"+client_data['devid'])
        return jsonify(status="success", message=mess)

    return jsonify(status="fail")


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
    return redirect(visualization)

@app.before_first_request
def setup_logging():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)

if __name__ == '__main__':
    app.debug = True
    print "Running on Port: " + port
    app.run(host='0.0.0.0', port=int(port))
