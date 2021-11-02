#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import logging
import ConfigParser
import random

class Scheduler(object):
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')

    def find_target_host(self, target_list):
    	target_host = random.choice(target_list)
        return target_host