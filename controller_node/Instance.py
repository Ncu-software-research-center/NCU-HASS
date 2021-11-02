#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

#########################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   This is a class which maintains instance data structure
##########################################################

import ConfigParser
import time
import logging
import subprocess

import InstanceFailure
from NovaClient import NovaClient


class Instance(object):
    def __init__(self, id, name, host, status, network):
        self.id = id
        self.name = name
        self.host = host
        self.network = network
        self.status = status
        self.nova_client = NovaClient.get_instance()
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.__provider_network_name = self.config.get("openstack", "openstack_provider_network_name")

    def get_ip(self, interface_name):
        return self.nova_client.get_instance_network(self.id)[interface_name][0]

    def get_id(self):
        return self.id

    def get_host(self):
        return self.host

    def update_info(self):
        self.host = self.nova_client.get_instance_host(self.id)
        self.status = self.nova_client.get_instance_state(self.id)
        self.network = self.nova_client.get_instance_network(self.id)

    def get_name(self):
        return self.name

    def get_network_provider(self):
        network_provider = self.network.get(self.__provider_network_name)
        return network_provider

    def get_info(self):
        return {
            'id':self.id,
            'name':self.name,
            'host':self.host,
            'status':self.status,
            'network':self.network
        }

    def __recover_instance_by_hard_reboot(self):
        self.nova_client.hard_reboot_instance(self.id)
        recovery_result = self.__check_instance_recovery_state()
        
        if recovery_result:
            logging.info("HAInstance - Success to hard reboot {}".format(self.name))
        else:
            logging.error(
                "HAInstance - Failed to recover {}".format(self.name))

        return recovery_result

    def __check_instance_recovery_state(self):
        timeout = int(self.config.get("recovery", "instance_recovery_timeout"))
        while timeout > 0:
            # ratri - FIX new mechanism
            state = self.nova_client.get_instance_state(self.id)
            if "ACTIVE" in state:
                return True
            else:
                time.sleep(1)
                timeout -= 1
        return False

    def __check_instance_network(self):
        logging.info("Instance - Cheking instance connection...")
        time_out = self.config.getint(
            "recovery", "network_validation_timeout")
        network_provider_list = self.get_network_provider()
        ip = network_provider_list[0]
        ping_timeout = 1
        while time_out > 0:
            try:
                # FIXME add to configuration
                response = subprocess.check_output(
                    ['timeout', str(ping_timeout), 'ping', '-c', '1', ip], stderr=subprocess.STDOUT, universal_newlines=True)
                return True
            except subprocess.CalledProcessError as ce:
                time_out -= ping_timeout
        return False

    # output: True/False. True means success, False means fail
    def recover_instance_crash(self):
        recovery_result = self.__recover_instance_by_hard_reboot()

        if recovery_result:
            network_recovery_result = self.__check_instance_network()
            if not network_recovery_result:
                logging.warning(
                    "HAInstance, recover_instance_crash - Failed to check instance network {}".format(self.name))
            return network_recovery_result

        logging.warning(
            "HAInstance - Failed to recover instance crash {}".format(self.name))
        return recovery_result

    # output: True/False. True means success, False means fail
    def recover_instance_os_hanged(self):
        recovery_result = self.__recover_instance_by_hard_reboot()

        if recovery_result:
            network_recovery_result = self.__check_instance_network()
            if not network_recovery_result:
                logging.warning("HAInstance, recover_instance_os_hanged - Failed to check instance network {}".format(self.name))
            return network_recovery_result
        
        logging.warning(
            "HAInstance - Failed to recover instance os hang {}".format(self.name))
        return recovery_result

    # output: True/False. True means success, False means fail
    def recover_instance_network_isolation(self):
        recovery_result = self.__recover_instance_by_hard_reboot()

        if recovery_result:
            network_recovery_result = self.__check_instance_network()
            if not network_recovery_result:
                logging.warning(
                    "HAInstance, recover_instance_network_isolation - Failed to check instance network {}".format(self.name))
            return network_recovery_result

        logging.warning(
            "HAInstance - Failed to recover instance network isolation {}".format(self.name))
        return recovery_result
