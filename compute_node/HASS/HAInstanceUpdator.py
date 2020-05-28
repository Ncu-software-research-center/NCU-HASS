#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import logging
import socket
import threading

from HAInstanceManager import HAInstanceManager


class HAInstanceUpdator(threading.Thread):
    def __init__(self, portNumber):
        threading.Thread.__init__(self)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('', portNumber))
        self.s.listen(5)
        self.portNumber = portNumber

    def run(self):
        while True:
            logging.info("HAInstanceUpdator - Listening at port %s" %
                         self.portNumber)
            cs, addr = self.s.accept()
            logging.info(("Request conection from : ", addr))
            data = cs.recv(1024)

            if "update instance" in data:
                logging.info(
                    "HAInstanceUpdator - get update instance message from controller")
                HAInstanceManager.update_ha_instance()
