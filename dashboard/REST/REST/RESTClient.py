from Authenticator import Authenticator
import httplib
import ConfigParser
import json
import time
import logging


config = ConfigParser.RawConfigParser()
config.read('/etc/hass.conf')
REST_host = config.get("RESTful","host")
REST_port = int(config.get("RESTful","port"))

MESSAGE_OK = 'succeed'
MESSAGE_FAIL = 'failed'

class RESTClient(object):
	_instance = None

	def __init__(self):
		self.authenticator = Authenticator()
		RESTClient._instance = self


	@staticmethod
	def get_instance():
		if not RESTClient._instance:
			RESTClient()
		return RESTClient._instance

	def create_cluster(self, name, node_list=[]):
		data = {"cluster_name": name}
		response = self._get_HASS_response("/HASS/api/cluster", "POST", data)
		if response["code"] == MESSAGE_OK:
			if node_list != []:
				return self.add_node(name, node_list)
			else:
				return response

	def delete_cluster(self, cluster_name):
		return self._get_HASS_response("/HASS/api/cluster?cluster_name=%s" % cluster_name, "DELETE")

	def list_cluster(self):
		return self._get_HASS_response("/HASS/api/clusters", "GET")

	def add_node(self, cluster_name, node_list):
		data = {"cluster_name": cluster_name,"node_list": node_list}
		return self._get_HASS_response("/HASS/api/node", "POST", data)

	def delete_node(self, cluster_name, node_name):
		return self._get_HASS_response("/HASS/api/node?cluster_name=%s&&node_name=%s" %(cluster_name, node_name), "DELETE")

	def list_node(self, cluster_name):
		return self._get_HASS_response("/HASS/api/nodes/%s" % cluster_name, "GET")

	def add_instance(self, cluster_name, instance_id):
		data = {"cluster_name": cluster_name, "instance_id": instance_id}
		return self._get_HASS_response("/HASS/api/instance", "POST", data)

	def delete_instance(self, cluster_name, instance_id):
		return self._get_HASS_response("/HASS/api/instance?cluster_name=%s&&instance_id=%s" % (cluster_name, instance_id), "DELETE")

	def list_instance(self, cluster_name):
		return self._get_HASS_response("/HASS/api/instances/%s" % cluster_name, "GET")

	def recover(self, fail_type, cluster_name, node_name):
		data = {"fail_type": fail_type, "cluster_name": cluster_name, "node_name": node_name}
		return self._get_HASS_response("/HASS/api/recover", "POST", data)

	def update_db(self):
		return self._get_HASS_response("/HASS/api/updateDB", "GET")

	def _get_HASS_response(self, endpoint, method, data=None):
		try:
			headers = {'Content-Type' : 'application/json',
					   'X-Auth-Token' : self.authenticator.get_access_token()}
			return self._get_response(REST_host, REST_port, endpoint, method, headers, data)
		except Exception as e:
			print str(e)
			logging.error(str(e))
			return False

	def _get_response(self, host, port, endpoint, method, headers, data=None):
		conn = httplib.HTTPConnection(host, port, timeout=500)
		headers = headers
		request_data = json.dumps(data)
		conn.request(method, endpoint, body=request_data, headers=headers)
		response = json.loads(conn.getresponse().read())
		conn.close()
		return response

if __name__ == '__main__':
	pass