#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import httplib
import ConfigParser
import json
import logging

config = ConfigParser.RawConfigParser()
config.read('/etc/hass.conf')

keystone_port = int(config.get("keystone_auth","port"))

openstack_user_name = config.get("openstack", "openstack_admin_account")
openstack_domain = config.get("openstack", "openstack_user_domain_id")
openstack_password = config.get("openstack", "openstack_admin_password")

REST_host = config.get("RESTful","host")
REST_port = int(config.get("RESTful","port"))


class Authenticator(object):
  def __init__(self):
    self._access_token = self._init_access_token()

  def success(self, token):
    return self._is_token_valid(token)

  def _init_access_token(self):
    try:
      data = '{ "auth": { "identity": { "methods": [ "password" ], "password": { "user": { "name": \"%s\", "domain": { "name": \"%s\" }, "password": \"%s\" } } } } }' % (openstack_user_name, openstack_domain, openstack_password)
      headers = {"Content-Type": "application/json"}
      http_client = httplib.HTTPConnection(REST_host, keystone_port, timeout=30)
      http_client.request("POST", "/v3/auth/tokens", body=data, headers=headers)
      return http_client.getresponse().getheaders()[1][1]
    except Exception as e:
      logging.error("Authenticator - failed to init access_token")
    finally:
      if http_client:
        http_client.close()

  def _refresh_access_token(self):
    self._access_token = self._init_access_token()

  def get_access_token(self):
    if not self._is_token_valid(self._access_token):
      self._refresh_access_token()
      logging.info("token refresh %s" % self._access_token)
    return self._access_token

  def _is_token_valid(self, token):
    if not token:
      return False
    try:
      while True :
        headers = {"X-Auth-Token": self._access_token, "X-Subject-Token": token}
        http_client = httplib.HTTPConnection(REST_host, keystone_port, timeout=30)
        http_client.request("GET", "/v3/auth/tokens", headers=headers)
        response = http_client.getresponse()
        if response.status == httplib.UNAUTHORIZED:
          self._refresh_access_token()
          if http_client:
            http_client.close()
          continue
        break
      
      map_response = json.loads(response.read())
      if "error" in map_response and \
        map_response["error"]["code"] == httplib.NOT_FOUND:
        return False
      return True
    finally:
      if http_client:
        http_client.close()

if __name__ == '__main__':
  a = Authenticator()
  print a.get_iserv_token()