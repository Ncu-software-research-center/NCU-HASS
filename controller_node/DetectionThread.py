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
#   This is a class which detects whether computing nodes happens error or not.
##########################################################
import time
import threading
import logging
import ConfigParser
import os

import FailureType
import InstanceState
import LayerConfig
from FaultDetectionStrategy import FaultDetectionStrategy
from RESTClient import RESTClient
from NovaClient import NovaClient


class DetectionThread(threading.Thread):
    def __init__(self, cluster_name, node, polling_interval, protected_layers_string, instance_update_queue):
        threading.Thread.__init__(self)
        self.node = node
        self.__node_name = self.node.get_name()
        # init config parser
        config = ConfigParser.RawConfigParser()
        config.read('/etc/hass.conf')
        # init a logger for this thread
        self.__logger = logging.getLogger('{}'.format(self.__node_name))
        self.__logger.setLevel(config.get("log", "level"))
        # -- create file handler which logs even debug messages
        fh = logging.FileHandler('{}{}.log'.format(config.get("log", "folder_path"), self.__node_name)
)
        fh.setLevel(logging.DEBUG)
        # -- create formatter and add it to the handlers
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] : %(message)s")
        fh.setFormatter(formatter)
        # -- add the handlers to the logger
        self.__logger.addHandler(fh)
        self.__logger.info("-- finish init {} logger --".format(self.__node_name))

        self.cluster_name = node.cluster_name
        self.ipmi_status = node.ipmi_status
        self.polling_interval = polling_interval
        self.cluster_protected_layers_string = protected_layers_string
        self.loop_exit = False
        self.fault_detection_strategy = FaultDetectionStrategy(node, self.cluster_protected_layers_string, instance_update_queue)
        self.server = RESTClient.get_instance()
        self.__nova_client = NovaClient.get_instance()
        

    def run(self):
        counter = 1
        while not self.loop_exit:
            try:
                state = None
                if self.node.get_status() == FailureType.HEALTH:
                    # step 1: check whether fault occurs, and, step 2: check whether the fault is permanent fault
                    state = self.fault_detection_strategy.detect()
                    # for merged layer function: the system will merge layer when some layer detectors are disabled
                    counter += 1
                    if counter >= 5:
                        self.fault_detection_strategy.check_protected_layers_detector(self.cluster_protected_layers_string)
                        counter = 1
                else:
                    while True:
                        state = self.fault_detection_strategy.detect_host_level_highest_layer()
                        if state == FailureType.HEALTH:
                            self.node.set_status(state)
                            break
            except Exception as e:
                self.__logger.error("DT: run exception: "+str(e))
                continue

            # when a fault occurs and is a permanent fault
            if isinstance(state, tuple) and state[0] in FailureType.FAIL_LEVEL:
                # step 3: recover the permanent fault
                self.__logger.warning("node({}): DetectionThread (run) - detection result (fault type, instance name): {}".format(self.__node_name, str(state)))

                try:
                    recovery_list = self._get_recovery_list(state[0])
                    for fail_type in recovery_list:
                        recovery_result = self._recover(fail_type, state[1])
                        if recovery_result:
                            host_level_fault_list = FailureType.FAIL_LEVEL[LayerConfig.HOST_LEVEL_RANGE[0]: LayerConfig.HOST_LEVEL_RANGE[1]+1]
                            if not set(recovery_list).isdisjoint(host_level_fault_list):
                                self.fault_detection_strategy.setup_libvirt_detector(self.cluster_protected_layers_string)
                            break
                except Exception as e:
                    self.__logger.error("node({}): DetectionThread, run - Exception : {}".format(self.__node_name, str(e)))
                    self.stop()
                self.server.update_db()

            # check instance state to update instance information in the cluster, such as VM deletection and VM migration
            self.__update_instance_information_in_cluster()
            time.sleep(self.polling_interval)

    def stop(self):
        self.loop_exit = True

    def _recover(self, fault_type, failed_component):
        result = self.server.recover(fault_type, self.cluster_name, failed_component)
        if result:  # recover success
            # if fault is at node level
            if fault_type in FailureType.FAIL_LEVEL[LayerConfig.HOST_LEVEL_RANGE[0]:LayerConfig.HOST_LEVEL_RANGE[1]+1]:
                self.node.set_status(FailureType.HEALTH)
            # if fault is at VM level
            elif fault_type in FailureType.FAIL_LEVEL[LayerConfig.INSTANCE_LEVEL_RANGE[0]:LayerConfig.INSTANCE_LEVEL_RANGE[1]+1]:
                self.fault_detection_strategy.set_instance_to_default(failed_component)
        else:  # recover fail
            self.__logger.error("recover fail , change node status")
            # if fault is at node level
            if fault_type in FailureType.FAIL_LEVEL[LayerConfig.HOST_LEVEL_RANGE[0]:LayerConfig.HOST_LEVEL_RANGE[1]+1]:
                self.node.set_status(fault_type+" and recover fail")
            # if fault is at VM level
            elif fault_type in FailureType.FAIL_LEVEL[LayerConfig.INSTANCE_LEVEL_RANGE[0]:LayerConfig.INSTANCE_LEVEL_RANGE[1]+1]:
                self.fault_detection_strategy.set_instance_state(failed_component, fault_type)
        return result

    def _get_recovery_list(self, state):
        fail_level_list = FailureType.FAIL_LEVEL
        temp_layer = self.fault_detection_strategy.get_active_layers()
        sub_temp_layer = temp_layer[:fail_level_list.index(state)]
        rev_sub_temp_layer = sub_temp_layer[::-1]
        index = rev_sub_temp_layer.find("1")
        if index < 0:
            return fail_level_list[:fail_level_list.index(state)+1]         
        else:
            return fail_level_list[len(sub_temp_layer)-index:fail_level_list.index(state)+1]
    
    def __update_instance_host_on_controller(self, instance_id):
        res = self.server.update_instance_host(self.cluster_name, instance_id)
        if "succeed" in str(res):
            self.__logger.info("DetectionThread - update instance host success")
        else:
            self.__logger.warning("DetectionThread - update instance host response: {}".format(res))

    def __delete_ha_instance_on_controller(self, instance_id):
        res = self.server.delete_instance(self.cluster_name, instance_id)
        self.__logger.info("DetectionThread - delete HA Instance response: {}".format(res))

    def __update_instance_information_in_cluster(self):
        instance_name_list = self.fault_detection_strategy.get_instance_name_list()
        for instance_name in instance_name_list:
            instance_state = self.fault_detection_strategy.get_instance_state(instance_name)
            instance_id = self.fault_detection_strategy.get_instance_id(instance_name)
            if instance_state in InstanceState.VM_DESTROYED:
                try:
                    
                    self.__nova_client._get_vm(instance_id)
                    continue
                except Exception as e:
                    self.__logger.info("DetectionThread, __update_instance_information_in_cluster - Remove instance from cluster")
                    self.fault_detection_strategy.set_instance_state(instance_name, InstanceState.VM_DELETED)
                    self.__delete_ha_instance_on_controller(instance_id)

            elif instance_state in InstanceState.VM_MIGRATING:
                self.__logger.info("DetectionThread, __update_instance_information_in_cluster - {} is migrating ...".format(instance_name))
                self.__update_instance_host_on_controller(instance_id)
            elif instance_state in InstanceState.VM_MIGRATED:
                self.__logger.info("DetectionThread, __update_instance_information_in_cluster - {} is migrated ".format(instance_name))
                self.__update_instance_host_on_controller(instance_id)

if __name__ == "__main__":
    pass
