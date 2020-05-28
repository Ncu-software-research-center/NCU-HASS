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
#   This is a class which detects whether computing nodes happens error or not.
##########################################################

import threading
import time
import logging
import FailureType

from FaultDetectionStrategy import FaultDetectionStrategy
from RESTClient import RESTClient


class DetectionThread(threading.Thread):
    def __init__(self, cluster_name, node, polling_interval):
        threading.Thread.__init__(self)
        self.node = node
        self.cluster_name = node.cluster_name
        self.ipmi_status = node.ipmi_status
        self.polling_interval = polling_interval
        self.loop_exit = False
        self.fault_detection_strategy = FaultDetectionStrategy(node)
        self.server = RESTClient.get_instance()

    def run(self):
        while not self.loop_exit:
            state = None
            if self.node.get_status() == FailureType.HEALTH:
                state = self.fault_detection_strategy.detect()
            else :
                while True:
                    state = self.fault_detection_strategy.detect_highest_layer()
                    if state == FailureType.HEALTH:
                        self.node.set_status(state)
                        break
                    else :
                        continue

            if state != FailureType.HEALTH:
                logging.error("[" + self.node.name + "] " + state)
                try:
                    recover_success = self.server.recover(state, self.cluster_name, self.node.name)
                    if recover_success:  # recover success
                        print "recover success"
                        self.node.set_status(FailureType.HEALTH)
                    else:  # recover fail
                        print "recover fail , change node status"
                        self.node.set_status(state+" and recover fail")
                except Exception as e:
                    print "Exception : " + str(e)
                    self.stop()
                self.server.update_db()
            time.sleep(self.polling_interval)

    def stop(self):
        self.loop_exit = True


if __name__ == "__main__":
    # config = ConfigParser.RawConfigParser()
    # config.read('hass.conf')
    # authUrl = "http://" + config.get("rpc", "rpc_username") + ":" + config.get("rpc",
    #                                                                            "rpc_password") + "@127.0.0.1:" + config.get(
    #     "rpc", "rpc_bind_port")
    # server = xmlrpclib.ServerProxy(authUrl)

    # server.test()
    print FailureType.FAIL_LEVEL[3]
