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


class Authenticator:

    REST_host = None
    REST_port = None
    keystone_port = None

    def __init__(self):
        self._access_token = None
        self.REST_host = config.get("RESTful", "host")
        self.REST_port = int(config.get("RESTful", "port"))
        self.keystone_port = int(config.get("keystone_auth", "port"))

    def get_access_token(self):
        if not self._is_token_valid(self._access_token):
            self._refresh_access_token()

        return self._access_token

    def _init_access_token(self):
        try:
            openstack_user_name = config.get(
                "openstack", "openstack_admin_account")
            openstack_domain = config.get(
                "openstack", "openstack_user_domain_id")
            openstack_password = config.get(
                "openstack", "openstack_admin_password")

            data = '{ "auth": { "identity": { "methods": [ "password" ], "password": { "user": { "name": \"%s\", "domain": { "name": \"%s\" }, "password": \"%s\" } } } } }' % (
                openstack_user_name, openstack_domain, openstack_password)
            headers = {"Content-Type": "application/json"}

            http_client = httplib.HTTPConnection(
                self.REST_host, self.keystone_port, timeout=30)

            http_client.request("POST", "/v3/auth/tokens",
                                body=data, headers=headers)

            return http_client.getresponse().getheaders()[1][1]

        except Exception as e:
            message = "Authenticator - failed to initialize token to access compute node: ", str(
                e)
            logging.error(message)

        finally:
            if http_client:
                http_client.close()

    def _is_token_valid(self, token):
        if not token:
            return False

        try:
            headers = {"X-Auth-Token": self._access_token,
                       "X-Subject-Token": token}
            http_client = httplib.HTTPConnection(
                self.REST_host, self.keystone_port, timeout=30)
            http_client.request("GET", "/v3/auth/tokens", headers=headers)
            response = http_client.getresponse()

            if response.status == httplib.UNAUTHORIZED:
                self._refresh_access_token()
                return self._is_token_valid(token)

            map_response = json.loads(response.read())
            if "error" in map_response and map_response["error"]["code"] == httplib.NOT_FOUND:
                return False

            return True

        finally:
            if http_client:
                http_client.close()

    def _refresh_access_token(self):
        self._access_token = self._init_access_token()
