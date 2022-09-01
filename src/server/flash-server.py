import sys, os, json
sys.path.append('..')
from kernel import lib
import argparse

#Config
ip = "127.0.0.1"
port = 8080


#Millennium file
parser = argparse.ArgumentParser()
parser.add_argument("falcon_file", help="path to millennium-falcon.json", type=str)
args = parser.parse_args()
assert os.path.isfile(args.falcon_file), "Invalid Falcon File"
falcon = lib.read_json(args.falcon_file)
falcon["routes_db"] = lib.repair_path(args.falcon_file, falcon["routes_db"])
assert os.path.isfile(falcon["routes_db"]), "Invalid Falcon DB File"
routes = lib.processDB(falcon["routes_db"])

#Logs

from flask import Flask, render_template, request, make_response
from flask.logging import default_handler
import logging
from logging.config import dictConfig
from gevent.pywsgi import WSGIServer, LoggingLogAdapter

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)

formatter = RequestFormatter(
    '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
    '%(levelname)s in %(module)s: %(message)s'
)

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.handlers.TimedRotatingFileHandler',
        'filename': 'logs',
        'when': 'W0',
        'backupCount': 0,
        'formatter': 'default'
    }},
    'root': {
        'handlers': ['wsgi']
    }
})

default_handler.setFormatter(formatter)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')
    
@app.route('/odds', methods = ['POST'])
def odds():
    file = request.files['empire']
    if not file:
        return make_response("empire file is missing", 400)
    try:
        data = json.load(file)
        (countdown, hunters_planning) = lib.processEmpire_bis(data)
        result = lib.process_a_star(routes, falcon["departure"], falcon["arrival"], falcon["autonomy"], countdown, hunters_planning)    
        if result is None:
            return make_response("0%", 200)
        else:
            fail_odds = lib.compute_proba(result[0])
            if fail_odds == 0:
                return make_response("100%", 200)
            else:
                return make_response("{:.2g}%".format((1 - fail_odds)*100), 200)
    except Exception as e:
        return make_response("cannot read empire file", 403)


print("Running on {}:{}".format(ip, port))
http_server = WSGIServer((ip, port), app, log=LoggingLogAdapter(app.logger, logging.WARNING))
http_server.serve_forever()
