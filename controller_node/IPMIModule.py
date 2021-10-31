#!/usr/bin/python
# -*- coding: utf-8 -*-

#########################################################
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
        self.__hardware_sensor_name_list = self.config.get("ipmi_sensor", "hardware_sensors").split(',')

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
                return IPMIConf.LAYER_FAILED
            if (initial - present) > IPMIConf.WATCHDOG_THRESHOLD:
                return IPMIConf.LAYER_FAILED
            if prev_initial != initial:
                prev_initial = initial
                prev_present = present
                time.sleep(float(interval))
                continue
            if (prev_present - present) < interval:
                return IPMIConf.LAYER_HEALTHY
            if initial == FailureType.DETECTOR_FAILED and present == FailureType.DETECTOR_FAILED:
                return FailureType.DETECTOR_FAILED
            prev_present = present
            time.sleep(float(interval))
        return IPMIConf.LAYER_FAILED

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

    #def get_hardware_status(self, node_name):
    #    ipmi_watched_sensor_list = IPMIConf.HARDWARE_SENSOR_LIST
    #    upper_critical = IPMIConf.HARDWARE_SENSOR_UPPER_CRITICAL #80
    #    lower_critical = IPMIConf.HARDWARE_SENSOR_LOWER_CRITICAL #10
    #    try:
    #        for sensor in ipmi_watched_sensor_list:
    #            value = self.__get_sensor_info_by_node(node_name, sensor)
    #            #print value
    #            if value == FailureType.DETECTOR_FAILED:
    #                return FailureType.DETECTOR_FAILED
    #            if value[0] > upper_critical or value[0] < lower_critical:
    #                return "Error"
    #        return "OK"
    #    except Exception as e:
    #        logging.error("IPMIModule - get_hardware_status, get exception: " + str(e))
    #        return FailureType.DETECTOR_FAILED

    def get_hardware_status(self, node_name):
        base = self._base_cmd_generate(node_name)
        try:
            command = base + IPMIConf.COMMAND_LIST_SENSORS_INFO
            p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
            response, err = p.communicate()
            detection_result = self.__check_sensor_values(response)
            if detection_result == True:
                return IPMIConf.LAYER_FAILED
            elif detection_result == FailureType.DETECTOR_NOT_SUPPORTED:
                return FailureType.DETECTOR_NOT_SUPPORTED
            return IPMIConf.LAYER_HEALTHY
        except Exception as e:
            logging.error("IPMIModule - get_hardware_status, get exception: " + str(e))
            return FailureType.DETECTOR_FAILED

    # check all sensor values, if at least one value exceeds the threshold, return True, otherwise return False. 
    def __check_sensor_values(self, all_sensors_info):
        hardware_failed = False
        hardware_detector_disabled = True
        sensor_info_list = all_sensors_info.split(IPMIConf.SENSORS_INFO_DELIMITER)
        for sensor_info in sensor_info_list:
            # info_list = [sensor_id, sensor_reading, sensor_status]
            if IPMIConf.HARDWARE_INFO_DELIMITER not in sensor_info:
                continue
            info_list = sensor_info.split(IPMIConf.HARDWARE_INFO_DELIMITER)
            sensor_name = info_list[0].rstrip()
            sensor_reading = info_list[1] # sensor value. if the sensor does not exist, sensor_reading is "disable"
            sensor_status = info_list[2] # if the sensor value does not exceed the threshold, sensor_status is "ok"
            # if the sensor is not in the list of sensors to be checked, skip the check
            if sensor_name not in self.__hardware_sensor_name_list:
                continue
            hardware_detector_disabled = False
            if "disable" not in sensor_reading and "ok" not in sensor_status:
                logging.error("IPMIModule (__check_sensor_values): sensor_infor = {}".format(str(sensor_info)))
                hardware_failed = True
                break
        if hardware_detector_disabled:
            return FailureType.DETECTOR_NOT_SUPPORTED
        return hardware_failed

    def __get_sensor_info_by_node(self, node_name, sensor_type):
        base = self._base_cmd_generate(node_name)
        try:
            command = base + IPMIConf.NODEINFO_BY_TYPE % (sensor_type)
            p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
            response, err = p.communicate()
            response = response.split("\n")
            data_list = self.__temp_data_clean(response)
            return (data_list[0], data_list[1], data_list[2])  # (value,lower_critical,upper_critical)
        except Exception as e:
            logging.error("IPMIModule - get_sensor_info_by_node, get exception: " + str(e))
            return FailureType.DETECTOR_FAILED

    def __temp_data_clean(self, raw_data):
        value = raw_data[4].split(":")[1]
        value = re.findall("[0-9]+", value)[0].strip()  # use regular expression to filter
        lower_critical = raw_data[7].split(":")[1].strip()
        lower_critical = lower_critical.split(".")[0].strip()
        upper_critical = raw_data[10].split(":")[1].strip()
        upper_critical = upper_critical.split(".")[0].strip()
        return [int(value), int(lower_critical), int(upper_critical)]

    def get_power_status(self, node_name):
        status = IPMIConf.LAYER_HEALTHY
        base = self._base_cmd_generate(node_name)
        if base is None:
            logging.error("node not found , node_name : %s" % node_name)
            return FailureType.DETECTOR_FAILED
        try:
            command = base + IPMIConf.POWER_STATUS
            response = subprocess.check_output(command, shell=True)
            if IPMIConf.POWER_STATUS_SUCCESS_MSG not in response:
                status = IPMIConf.LAYER_FAILED
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
    hd1 = i.get_hardware_status('hp-compute1')
    hd2 = i.get_hardware_status('hp-compute2')
    #print xy1 + '  ' + xy2 
    #x1 = i.get_os_status("hp-compute1")
    #x2 = i.get_os_status("compute2")
    #print x1 + '  ' + x2 
    print("main: hd1={}, hd2={}".format(str(hd1), str(hd2)))
    # xk1 = i.get_ipmi_status('compute1')
    # xk2 = i.get_ipmi_status('compute2')
    # print str(xk1) + '  ' + str(xk2) 
    
    # test2 = i.get_os_status('compute1')
    # print test2
