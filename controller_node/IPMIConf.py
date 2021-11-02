#!/usr/bin/python
# -*- coding: utf-8 -*-
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
#   IPMI Configuration file.
##########################################################

BASE_CMD = "ipmitool -I lanplus -H %s -U %s -P %s "  # %(NODEID , USER , PASSWD)

REBOOTNODE = "chassis power reset"
REBOOTNODE_SUCCESS_MSG = "Reset"

STARTNODE = "chassis power on"
STARTNODE_SUCCESS_MSG = "Up/On"

SHUTOFFNODE = "chassis power off"
SHUTOFFNODE_SUCCESS_MSG = "Down/Off"

#HARDWARE_SENSOR_LIST = ["Inlet Temp","Temp"]
#HARDWARE_SENSOR_LIST = ["01-Inlet Ambient"]
#HARDWARE_SENSOR_UPPER_CRITICAL = 80
#HARDWARE_SENSOR_LOWER_CRITICAL = 10
SENSORS_INFO_DELIMITER = "\n"
HARDWARE_INFO_DELIMITER = "|"
NODEINFO = "sdr elist full -v -c sensor reading"
NODEINFO_BY_TYPE = "sensor get '%s'"
COMMAND_LIST_SENSORS_INFO = "sdr list"

GET_OS_STATUS = "mc watchdog get"
OS_TYPE_INITIAL = "Initial Countdown"
OS_TYPE_PRESENT = "Present Countdown"

WATCHDOG_THRESHOLD = 4

SENSOR_STATUS = "sdr elist full -v -c sensor reading"

RESET_WATCHDOG = "mc watchdog reset"
RESET_WATCHDOG_SUCCESS_MSG = "countdown restarted"

POWER_STATUS = "power status"
POWER_STATUS_SUCCESS_MSG = "Power is on"

RAW_DATA = "sdr get %s"

LAYER_FAILED = "Error"
LAYER_HEALTHY = "OK"
