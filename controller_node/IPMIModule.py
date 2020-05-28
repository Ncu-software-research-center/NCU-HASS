#!/usr/bin/python
# -*- coding: utf-8 -*-

#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
#
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   This is a class maintains IPMI command operation.
##########################################################

import ConfigParser
import logging
import re
import subprocess
import time

import IPMIConf
import FailureType
from Response import Response


class IPMIModule(object):
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.ip_dict = dict(self.config._sections['ipmi'])
        self.user_dict = dict(self.config._sections['ipmi_user'])

    def reboot_node(self, node_name):
        code = ""
        message = ""
        base = self._base_cmd_generate(node_name)
        if base is None:
            raise Exception("ipmi node not found , node_name : %s" % node_name)
        try:
            command = base + IPMIConf.REBOOTNODE
            response = subprocess.check_output(command, shell=True)
            if IPMIConf.REBOOTNODE_SUCCESS_MSG in response:
                message = "The Computing Node %s is rebooted." % node_name
                logging.info("IPMIModule reboot_node - The Computing Node %s is rebooted." % node_name)
                # code = "0"
                code = "succeed"
        except Exception as e:
            message = "The Computing Node %s can not be rebooted." % node_name
            logging.error("IPMIModule reboot_node - %s" % e)
            # code = "1"
            code = "failed"
        finally:
            # result = {"code":code, "node":node_name, "message":message}
            result = Response(code=code,
                              message=message,
                              data={"node": node_name})
            return result

    def start_node(self, node_name):
        code = ""
        message = ""
        base = self._base_cmd_generate(node_name)
        if base is None:
            raise Exception("ipmi node not found , node_name : %s" % node_name)
        try:
            command = base + IPMIConf.STARTNODE
            response = subprocess.check_output(command, shell=True)
            if IPMIConf.STARTNODE_SUCCESS_MSG in response:
                message = "The Computing Node %s is started." % node_name
                logging.info("IPMIModule start_node - The Computing Node %s is started." % node_name)
                # code = "0"
                code = "succeed"
        except Exception as e:
            message = "The Computing Node %s can not be started." % node_name
            logging.error("IPMIModule start_node - %s" % e)
            # code = "1"
            code = "failed"
        finally:
            # result = {"code":code, "node":node_name, "message":message}
            result = Response(code=code,
                              message=message,
                              data={"node": node_name})
            return result

    def shut_off_node(self, node_name):
        code = ""
        message = ""
        base = self._base_cmd_generate(node_name)
        if base is None:
            raise Exception("ipmi node not found , node_name : %s" % node_name)
        try:
            command = base + IPMIConf.SHUTOFFNODE
            response = subprocess.check_output(command, shell=True)
            if IPMIConf.SHUTOFFNODE_SUCCESS_MSG in response:
                message = "The Computing Node %s is shut down." % node_name
                logging.info("IPMIModule shut_off_node - The Computing Node %s is shut down." % node_name)
                # code = "0"
                code = "succeed"
        except Exception as e:
            message = "The Computing Node %s can not be shut down." % node_name
            logging.error("IPMIModule shut_off_node - %s" % e)
            # code = "1"
            code = "failed"
        finally:
            # result = {"code":code, "node":node_name, "message":message}
            result = Response(code=code,
                              message=message,
                              data={"node": node_name})
            return result

    def get_os_status(self, node_name):
        interval = (IPMIConf.WATCHDOG_THRESHOLD / 2)
        prev_initial = None
        prev_present = None
        for _ in range(3):
            initial = self._get_os_value(node_name, IPMIConf.OS_TYPE_INITIAL)
            present = self._get_os_value(node_name, IPMIConf.OS_TYPE_PRESENT)
            if initial == False or present == False:
                return "Error"
            if (initial - present) > IPMIConf.WATCHDOG_THRESHOLD:
                return "Error"
            if prev_initial != initial:
                prev_initial = initial
                prev_present = present
                time.sleep(float(interval))
                continue
            if (prev_present - present) < interval:
                return "OK"
            if initial == FailureType.DETECTOR_FAILED and present == FailureType.DETECTOR_FAILED:
                return FailureType.DETECTOR_FAILED
            prev_present = present
            time.sleep(float(interval))
        return "Error"

    def _get_os_value(self, node_name, value_type):
        base = self._base_cmd_generate(node_name)
        if base is None:
            logging.error("ipmi node not found , node_name : %s" % node_name)
            return FailureType.DETECTOR_FAILED
        command = base + IPMIConf.GET_OS_STATUS
        try:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            response = p.wait()
            if response != 0:
                logging.error("Error! The subprocess's command is invalid.")
                return FailureType.DETECTOR_FAILED
            while True:
                info = p.stdout.readline()
                if "Stopped" in info:
                    return False
                if not info:
                    break
                if value_type in info:
                    return int(re.findall("[0-9]+", info)[0])  # find value
        except Exception as e:
            logging.error("IPMIModule-- _get_os_value fail : %s" % str(e))
            return FailureType.DETECTOR_FAILED

    def get_power_status(self, node_name):
        status = "OK"
        base = self._base_cmd_generate(node_name)
        if base is None:
            logging.error("node not found , node_name : %s" % node_name)
            return FailureType.DETECTOR_FAILED
        try:
            command = base + IPMIConf.POWER_STATUS
            response = subprocess.check_output(command, shell=True)
            if IPMIConf.POWER_STATUS_SUCCESS_MSG not in response:
                status = "Error"
                # return status
        except Exception as e:
            logging.error(
                "IPMIModule get_power_status - The Compute Node %s's IPMI session can not be established. %s" % (
                    node_name, e))
            status = FailureType.DETECTOR_FAILED
        finally:
            return status

    def _base_cmd_generate(self, node_name):
        if node_name in self.user_dict:
            user = self.user_dict[node_name].split(",")[0]
            passwd = self.user_dict[node_name].split(",")[1]
            cmd = IPMIConf.BASE_CMD % (self.ip_dict[node_name], user, passwd)
            return cmd
        else:
            return None

    def get_ipmi_status(self, node_name):
        return node_name in self.ip_dict


if __name__ == "__main__":
    i = IPMIModule()
    xy1 = i.get_power_status('compute1')
    xy2 = i.get_power_status('compute2')
    print xy1 + '  ' + xy2 
    x1 = i.get_os_status("compute1")
    x2 = i.get_os_status("compute2")
    print x1 + '  ' + x2 
    # xk1 = i.get_ipmi_status('compute1')
    # xk2 = i.get_ipmi_status('compute2')
    # print str(xk1) + '  ' + str(xk2) 
    
    # test2 = i.get_os_status('compute1')
    # print test2