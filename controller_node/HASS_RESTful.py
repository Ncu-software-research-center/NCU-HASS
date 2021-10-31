from functools import wraps
from flask import Flask
from flask import request
from flask import jsonify
from flask import abort, make_response
import logging
import json
import threading
import sys
import ConfigParser
import os
from Response import Response
from Authenticator import Authenticator
from Hass import Hass

# for POST method, need to specify the 'Content-Type = application/json' in the request header.
# for GET method, need to specify the parameter after the url.

app = Flask(__name__)

config = ConfigParser.RawConfigParser()
config.read('/etc/hass.conf')

REST_host = config.get("RESTful","host")
REST_port = int(config.get("RESTful","port"))

HASS = None
authenticator = None

def _convert_res_to_JSON(response):
  return json.dumps(response.__dict__)

class RESTfulThread(threading.Thread):
  def __init__(self, input_HASS):
    threading.Thread.__init__(self)
    global HASS
    global authenticator
    HASS = input_HASS
    authenticator = Authenticator()

  def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
      if "X-Auth-Token" not in request.headers:
        abort(401)
      token = request.headers["X-Auth-Token"]
      if not authenticator.success(token):
        abort(401)
      print "RESTful request in."
      return f(*args, **kwargs)
    return decorated

  def run(self):
    print "RESTful server ready! host : %s, port : %s\n" % (REST_host, REST_port)
    app.run(port=REST_port, host=REST_host)

  @app.errorhandler(Exception)
  def global_exception_handle(error):
    print str(error)
    return make_response(jsonify({'message':"exception happens during request operation." ,"code":"failed","data":str(error)}), 500)

  @app.errorhandler(400)
  def lack_arguments(error):
    return make_response(jsonify({'message':"lack some arguments, please check the documentation.","code":"failed","data":400}), 400)

  @app.errorhandler(401)
  def auth_fail(error):
    return make_response(jsonify({'message':"The request you have made requires authentication.","code":"failed","data":401}), 401)

  @app.route("/HASS/api/cluster", methods=['POST'])
  @requires_auth
  def create_cluster():
    if not request.json or \
      "cluster_name" not in request.json or "node_list" not in request.json or "layers_string" not in request.json:
        abort(400)
    cluster_name = request.json["cluster_name"]
    node_name_list = request.json["node_list"]
    layers_string = request.json["layers_string"]
    logging.info("cluster_name: {}, layer_string: {}".format(cluster_name, layers_string))
    #layers_string = "1111111"
    res = HASS.create_cluster(cluster_name, node_name_list, layers_string)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/cluster", methods=['DELETE'])
  @requires_auth
  def delete_cluster():
    if not request.json or \
      "cluster_name" not in request.json:
      abort(400)
    cluster_name = request.json["cluster_name"]
    res = HASS.delete_cluster(cluster_name)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/clusters", methods=['GET'])
  @requires_auth
  def list_cluster():
    res = HASS.list_cluster()
    if res != None:
      res = Response(code="succeed",
                     message="get cluster list success",
                     data=res)
      return _convert_res_to_JSON(res)
    else:
      res = Response(code="failed",
                     message="get cluster list failed",
                     data=None)
      return _convert_res_to_JSON(res)

  @app.route("/HASS/api/node", methods=['POST'])
  @requires_auth
  def add_node():
    if not request.json or \
    "cluster_name" not in request.json or \
    "node_list" not in request.json:
        abort(400)
    cluster_name = request.json["cluster_name"]
    node_list = request.json["node_list"]
    res = HASS.add_node(cluster_name, node_list)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/node", methods=['DELETE'])
  @requires_auth
  def delete_node():
    if not request.json or \
    "cluster_name" not in request.json or \
    "node_name" not in request.json:
        abort(400)
    cluster_name = request.json["cluster_name"]
    node_name = request.json["node_name"]
    res = HASS.delete_node(cluster_name, node_name)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/nodes/<string:cluster_name>", methods=['GET'])
  @requires_auth
  def list_node(cluster_name):
    res = HASS.list_node(cluster_name)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/instance", methods=['POST'])
  @requires_auth
  def add_instance():
    if not request.json or \
      "cluster_name" not in request.json or \
      "instance_id" not in request.json:
        abort(400)
    cluster_name = request.json["cluster_name"]
    instance_id = request.json["instance_id"]
    res = HASS.add_instance(cluster_name, instance_id)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/instance", methods=['DELETE'])
  @requires_auth
  def delete_instance():
    cluster_name = request.args.get("cluster_name")
    instance_id = request.args.get("instance_id")
    if cluster_name is None or instance_id is None :
        abort(400)
    res = HASS.delete_instance(cluster_name, instance_id)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/instance", methods=['PUT'])
  @requires_auth
  def update_instance_host():
    if not request.json or \
      "cluster_name" not in request.json or \
      "instance_id" not in request.json:
        abort(400)
    cluster_name = request.json["cluster_name"]
    instance_id = request.json["instance_id"]
    res = HASS.update_instance_host(cluster_name, instance_id)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/instances/<string:cluster_name>", methods=['GET'])
  @requires_auth
  def list_instance(cluster_name):
    res = HASS.list_instance(cluster_name)
    return _convert_res_to_JSON(res)

  @app.route("/HASS/api/recover", methods=['POST'])
  @requires_auth
  def recover():
    if not request.json or \
       "fail_type" not in request.json or \
       "cluster_name" not in request.json or \
       "node_name" not in request.json:
       abort(400)
    fail_type = request.json["fail_type"]
    cluster_name = request.json["cluster_name"]
    node_name = request.json["node_name"]
    res = HASS.recover(fail_type, cluster_name, node_name)
    return json.dumps(res)

  @app.route("/HASS/api/updateDB", methods=['GET'])
  @requires_auth
  def update_db():
    res = HASS.update_db()
    return json.dumps(res)

  @app.route("/HASS/api/updateClusters", methods=['GET'])
  @requires_auth
  def update_all_clusters():
    res = HASS.update_all_clusters()
    return json.dumps(res)

def main():
    config = ConfigParser.RawConfigParser()
    config.read('/etc/hass.conf')

    log_level = logging.getLevelName(config.get("log", "level"))
    log_file_name = config.get("log", "location")
    dir = os.path.dirname(log_file_name)
    if not os.path.exists(dir):
        os.makedirs(dir)
    logging.basicConfig(filename=log_file_name, level=log_level, format="%(asctime)s [%(levelname)s] : %(message)s")
    logging.info("-- Preparing HASS --")
    HASS = Hass()

    rest_thread = RESTfulThread(HASS)
    rest_thread.daemon = True
    rest_thread.start()
    logging.info("HASS Server ready")
    print "HASS Server ready"
    try:
        while True:
          pass
    except:
        sys.exit(1)


if __name__ == "__main__":
    main()
