#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import logging
import subprocess
import time
import config

from NovaClient import NovaClient
from RESTClient import RESTClient

POWER_FAILED = "Crash"
OS_FAILED = "Watchdog"
NETWORK_FAILED = "Network"


class HAInstance(object):
    def __init__(self, cluster_name, ha_instance):
        self._nova_client = NovaClient.get_instance()
        self._id = ha_instance["id"]
        self._name = ha_instance["name"]
        self._status = ha_instance["status"]
        self._network = ha_instance["network"]
        self._network_self = []
        self._network_provider = []
        self._update_instance_network()
        logging.info("HAInstance - Initialized")

        self._os_failure = False

        self._power_failure = False

    def check_instance_network_failure(self):
        if not self._network_provider:
            return None

        ip = self._network_provider[0]
        return not(self._ping_instance(ip))

    def check_instance_os_failure(self):
        timeout = int(config.get("watchdog", "watchdog_timeout"))
        while timeout >= 0:
            if self._os_failure is True:
                return self._os_failure
            else:
                timeout -= 1
                if timeout <= 0:
                    break
                time.sleep(1)
        return self._os_failure


    def check_instance_power_failure(self):
        return self._power_failure

    def get_instance_name(self):
        return self._name

    def get_instance_status(self):
        return self._status

    def revert_to_default(self):
        self._status = "Healthy"
        self._os_failure = False
        self._power_failure = False

    def recover_instance_crash(self):

        self._status = POWER_FAILED
        recovery_result = self._recover_instance_by_hard_reboot()

        if recovery_result:
            logging.info(
                "HAInstance - Instance is active {}".format(self._name))
            logging.info("HAInstance - Checking instance network ...")

            network_recovery_result = self._check_instance_network()
            if network_recovery_result:
                logging.info(
                    "HAInstance - Success to check instance network {}".format(self._name))
                self.revert_to_default()
                logging.info(
                    "HAInstance - Success to recover instance crash {}".format(self._name))
                logging.info("HAInstance - Revert to default")
            else:
                self._status = NETWORK_FAILED
                logging.error(
                    "HAInstance - Failed to check instance network {}".format(self._name))
            return network_recovery_result

        logging.error(
            "HAInstance - Failed to recover instance network isolation {}".format(self._name))
        self._status = POWER_FAILED

        return recovery_result

    def recover_instance_network(self):

        recovery_result = self._recover_instance_by_hard_reboot()

        if recovery_result:
            logging.info(
                "HAInstance - Instance is active {}".format(self._name))
            logging.info("HAInstance - Checking instance network ...")

            network_recovery_result = self._check_instance_network()
            if network_recovery_result:
                logging.info(
                    "HAInstance - Success to check instance network {}".format(self._name))
                self.revert_to_default()
                logging.info(
                    "HAInstance - Success to recover instance network isolation {}".format(self._name))
                logging.info("HAInstance - Revert to default")
            else:
                self._status = NETWORK_FAILED
                logging.error(
                    "HAInstance - Failed to check instance network {}".format(self._name))
            return network_recovery_result

        logging.error(
            "HAInstance - Failed to recover instance network isolation {}".format(self._name))
        self._status = NETWORK_FAILED
        return recovery_result

    def recover_instance_os_hang(self):

        self._status = OS_FAILED
        recovery_result = self._recover_instance_by_hard_reboot()

        if recovery_result:
            logging.info(
                "HAInstance - Instance is active {}".format(self._name))
            logging.info("HAInstance - Checking instance network ...")

            network_recovery_result = self._check_instance_network()
            if network_recovery_result:
                message = "HAInstance - Success to check instance network {}".format(
                    self._name)
                logging.info(message)
                self.revert_to_default()
                logging.info(
                    "HAInstance - Success to recover instance os hang {}".format(
                        self._name))
                logging.info("HAInstance - Revert to default")
            else:
                self._status = NETWORK_FAILED
                logging.error("HAInstance - Failed to check instance network {}".format(
                    self._name))
            return network_recovery_result

        logging.error(
            "HAInstance - Failed to recover instance os hang {}".format(self._name))
        self._status = OS_FAILED

        return recovery_result

    def set_instance_os_failure(self):
        self._os_failure = True

    def set_instance_power_failure(self):
        self._power_failure = True

    def _check_instance_external_network(self, ip):
        if not self._nova_client.get_instance_external_network(ip):
            return False
        return True

    def _check_instance_network(self):
        time_out = config.getint(
            "detection", "network_validation_timeout", default='30')
        ip = self._network_provider[0]
        while time_out > 0:
            try:
                # FIXME add to configuration
                response = subprocess.check_output(
                    ['timeout', '2', 'ping', '-c', '1', ip], stderr=subprocess.STDOUT, universal_newlines=True)
                return True

            except subprocess.CalledProcessError:
                time_out -= 1
                time.sleep(1)
        return False

    def _check_instance_recovery_state(self):
        timeout = int(config.get("recovery", "recovery_timeout"))
        while timeout > 0:
            # ratri - FIX new mechanism
            state = self._nova_client.get_instance_state(self._id)
            if "ACTIVE" in state:
                return True
            else:
                time.sleep(1)
                timeout -= 1
        return False

    def _ping_instance(self, ip):
        time_out = config.getint(
            "detection", "network_ping_timeout", default='30')

        while time_out >= 0:
            try:
                # FIXME move the cmd to configuration file
                response = subprocess.check_output(
                    ['timeout', '2', 'ping', '-c', '1', ip], stderr=subprocess.STDOUT, universal_newlines=True)

                # dont log when it success, it will have a lot of log
                return True

            except Exception as e:
                logging.error("HAInstance - Failed to ping {} at {}".format(
                    self._name, ip))
                time_out -= 1

                if time_out <= 0:
                    break

                time.sleep(1)

        return False

    def _recover_instance_by_hard_reboot(self):
        self._nova_client.hard_reboot(self._id)
        recovery_result = self._check_instance_recovery_state()
        
        if recovery_result:
            logging.info("HAInstance - Success to hard reboot {}".format(
                self._name))
        else:
            logging.error(
                "HAInstance - Failed to recover {}".format(self._name))

        return recovery_result

    def _update_instance_network(self):
        for router_name, ip_list in self._network.iteritems():
            for ip in ip_list:
                instance_network_status = self._check_instance_external_network(
                    ip)
                if instance_network_status:
                    self._network_provider.append(ip)
                else:
                    self._network_self.append(ip)
