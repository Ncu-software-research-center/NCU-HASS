#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import config
import logging
import time

from keystoneauth1 import session
from keystoneauth1.identity import v3
from novaclient import client


class NovaClient(object):
    _instance = None
    _helper = None

    def __init__(self):
        self.config = config.getRawConfiguration()

        if NovaClient._instance is not None:
            raise Exception(
                "This class is a singleton! , cannot initialize twice")
        else:
            self._initialize_helper()
            NovaClient._instance = self

    @staticmethod
    def get_instance():
        if not NovaClient._instance:
            NovaClient()

        if not NovaClient._helper:
            NovaClient._instance._initialize_helper()

        logging.info("Nova Client Instance - Initialized")
        return NovaClient._instance

    def get_instance_external_network(self, instance_ip):
        external_ip = self.config.get(
            "openstack", "openstack_external_network_gateway_ip").split(".")
        external_ip = external_ip[0:-1]
        check_ip = instance_ip.split(".")
        if all(x in check_ip for x in external_ip):
            return instance_ip
        return None

    def get_instance_name(self, instance_id):
        instance = self._get_instance_detail(instance_id)
        return getattr(instance, "OS-EXT-SRV-ATTR:instance_name")

    def get_instance_state(self, instance_id):
        try:
            instance_state = self._get_instance_detail(instance_id)
            return getattr(instance_state, "status")

        except Exception as e:
            message = "NovaClient - failed to get instance state: ", str(e)
            logging.error(message)
            return None

    def hard_reboot(self, instance_id):
        try:
            instance = self._get_instance_detail(instance_id)
            self._helper.servers.reboot(instance, reboot_type='HARD')
            instance_name = self.get_instance_name(instance_id)
            message = "NovaClient - Rebooting instance ..."
            logging.info(message)

        except Exception as e:
            message = "NovaClient - failed to hard reboot instance: ", str(e)
            logging.error(message)

    # previous version this function is called get_vm
    def _get_instance_detail(self, instance_id):
        return self._helper.servers.get(instance_id)

    def _initialize_helper(self):
        auth = v3.Password(auth_url='http://%s:%s/v3' % (self.config.get("keystone_auth", "url"), self.config.get("keystone_auth", "port")),
                           username=self.config.get(
                               "openstack", "openstack_admin_account"),
                           password=self.config.get(
                               "openstack", "openstack_admin_password"),
                           project_name=self.config.get(
                               "openstack", "openstack_project_name"),
                           user_domain_name=self.config.get(
                               "openstack", "openstack_user_domain_id"),
                           project_domain_name=self.config.get("openstack", "openstack_project_domain_id"))
        sess = session.Session(auth=auth)
        nova_api = config.get("nova_api", "nova_api_version")
        NovaClient._helper = client.Client(nova_api, session=sess)
