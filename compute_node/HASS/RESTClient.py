#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import config
import httplib
import json
import logging

from Authenticator import Authenticator

MESSAGE_OK = 'succeed'
MESSAGE_FAIL = 'failed'


class RESTClient(object):
    _instance = None
    REST_host = None
    REST_port = None

    def __init__(self):
        logging.info("Generate RESTClient and auth")
        self.REST_host = config.get("RESTful", "host")
        self.REST_port = int(config.get("RESTful", "port"))
        self.authenticator = Authenticator()
        RESTClient._instance = self

    @staticmethod
    def get_instance():
        if not RESTClient._instance:
            RESTClient()
        return RESTClient._instance

    def list_cluster(self):
        return self._get_response("/HASS/api/clusters", "GET")

    def list_instance(self, cluster_name):
        return self._get_response("/HASS/api/instances/%s" % cluster_name, "GET")

    def _get_response(self, endpoint, method, data=None):
        conn = httplib.HTTPConnection(
            self.REST_host, self.REST_port, timeout=500)
        headers = {'Content-Type': 'application/json',
                   'X-Auth-Token': self.authenticator.get_access_token()}

        data = json.dumps(data)
        conn.request(method, endpoint, body=data, headers=headers)
        response = json.loads(conn.getresponse().read())
        return response
