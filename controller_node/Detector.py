#########################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#	This is a class which contains detect functions.
##########################################################

import subprocess
import FailureType
import time
import logging
import ConfigParser
from IPMIModule import IPMIModule
import IPMIConf

class Detector(object):
    def __init__(self, node):
        self.node = node.name
        self.ipmi_status = node.ipmi_status
        self.ipmi_module = IPMIModule()
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.max_message_size = int(self.config.get("default","max_message_size"))

    def check_network_status(self):
        heartbeat_time = int(self.config.get("default","heartbeat_time"))
        while heartbeat_time > 0:
            try:
                response = subprocess.check_output(['timeout', '0.2', 'ping', '-c', '1', self.node], stderr=subprocess.STDOUT, universal_newlines=True)
                return FailureType.HEALTH
            except Exception as e:
                print " [%s] network transient failure" %self.node
                time.sleep(1)
                heartbeat_time -= 1
        return FailureType.NETWORK_FAIL

    def check_power_status(self):
        if not self.ipmi_status:
            return FailureType.DETECTOR_NOT_SUPPORTED
        status = self.ipmi_module.get_power_status(self.node)
        if status == IPMIConf.LAYER_HEALTHY:
            return FailureType.HEALTH
        elif status == FailureType.DETECTOR_FAILED:
            return status
        else:
            return FailureType.POWER_FAIL

    def check_hardware_status(self):
        if not self.ipmi_status:
            return FailureType.DETECTOR_NOT_SUPPORTED
        status = self.ipmi_module.get_hardware_status(self.node)
        if status == IPMIConf.LAYER_HEALTHY:
            return FailureType.HEALTH
        elif status == IPMIConf.LAYER_FAILED:
            return FailureType.HARDWARE_FAIL
        elif status == FailureType.DETECTOR_NOT_SUPPORTED:
            return FailureType.DETECTOR_NOT_SUPPORTED
        else:
            return FailureType.DETECTOR_FAILED

    def check_os_status(self):
        if not self.ipmi_status:
            return FailureType.DETECTOR_NOT_SUPPORTED
        status = self.ipmi_module.get_os_status(self.node)
        if status == IPMIConf.LAYER_HEALTHY:
            return FailureType.HEALTH
        elif status == FailureType.DETECTOR_FAILED:
            return status
        else:
            return FailureType.OS_FAIL

    def check_network_transient_fault(self):
        network_transient_time = int(self.config.get("default", "network_transient_time"))
        status = FailureType.NETWORK_FAIL
        while network_transient_time > 0:
            try:
                status = self.check_network_status()
                if status == FailureType.HEALTH:
                    break
                else:
                    network_transient_time -= 1
            except subprocess.CalledProcessError:
                network_transient_time -= 1
                time.sleep(1)
        return status
