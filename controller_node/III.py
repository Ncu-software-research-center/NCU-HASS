#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

from DatabaseManager import IIIDatabaseManager
from RESTClient import RESTClient
import ConfigParser
import logging


class III(object):
	def __init__(self):
		self.iii_database = IIIDatabaseManager()
		self.rest_client = RESTClient.getInstance()

	def update_iii_database(self, protected_instance_list, target_host, fail_node):
		logging.info("start modify iii database")
		print "start modify iii database"
		for instance in protected_instance_list:
			try:
				self.iii_database.updateInstance(instance.id, target_host.name, fail_node.name)
			except Exception as e:
				print str(e)
				logging.error("%s" % str(e))
		print "end modify iii database"
		logging.info("end modify iii database")

	def send_recover_service_failed(self, fail_node, fail_services):
		return self.rest_client.send_recover_service_failed(fail_node, fail_services)
	
	def send_ipmi_failed(self, node_name):
		return self.rest_client.send_ipmi_failed(node_name)