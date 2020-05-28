#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import config
import logging
import os
import sys
import socket

from HAInstanceManager import HAInstanceManager
from HAInstanceUpdator import HAInstanceUpdator
from InstanceDetectionThread import InstanceDetectionThread

config.basicConfiguration(os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'hass_compute.conf')))

log_level = logging.getLevelName(config.get("log", "level"))
log_file_name = config.get("log", "location")

dir = os.path.dirname(log_file_name)
if not os.path.exists(dir):
    os.makedirs(dir)

FORMAT = "%(asctime)s [%(levelname)s] : %(message)s"
logging.basicConfig(filename=log_file_name, level=log_level, format=FORMAT)


def main():
    try:
        print("Detection Agent Started")
        portNumber = int(config.get("polling", "listen_port"))

        host_detection = HAInstanceUpdator(portNumber)
        host_detection.daemon = True
        host_detection.start()

        instance_detection = InstanceDetectionThread()
        instance_detection.daemon = True
        instance_detection.start()

        while True:
            pass

    except Exception as e:
        message = "DetectionAgent - detection agent daemon thread is failed to start: ", str(
            e)
        logging.error(message)

        sys.exit(1)

    except KeyboardInterrupt as e:
        print("Exit from application")


if __name__ == "__main__":
    main()
