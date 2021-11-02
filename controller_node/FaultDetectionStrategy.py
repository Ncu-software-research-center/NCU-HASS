#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import logging

import FailureType
import LayerConfig
from TreeBuilder import TreeBuilder 
from Detector import Detector
from InstanceDetector import InstanceDetector

class FaultDetectionStrategy(object):
    def __init__(self, node, protected_layers_string, instance_update_queue):
        self.active_layers_string = protected_layers_string
        # set up instance detector, such as callback
        self.__node_name = node.get_name()

        # get logger of this node thread
        self.__logger = logging.getLogger('{}'.format(self.__node_name))

        self.__instance_detector = InstanceDetector(self.__node_name, instance_update_queue)
        # setup libvirt callback
        self.setup_libvirt_detector(protected_layers_string)

        self.detector = Detector(node)
        self.tree_builder = TreeBuilder()
        self.binary_tree = self.tree_builder.build_tree(self.active_layers_string)
        self.function_map = [self.detector.check_power_status, 
                         self.detector.check_hardware_status, self.detector.check_os_status,
                         self.detector.check_network_status, self.__instance_detector.check_instance_power_failure, 
                         self.__instance_detector.check_instance_os_failure, self.__instance_detector.check_instance_network_failure]
        # list of methods used to verify that the layer detector is available. (sort by layer number)
        self.__detector_verification_method_list = [self.detector.check_power_status, 
                         self.detector.check_hardware_status, self.detector.check_os_status,
                         self.detector.check_network_status, self.__instance_detector.register_instance_state_callback,
                         self.__instance_detector.register_instance_watchdog_callback, self.__instance_detector.check_instance_network_detector]
        self._detection_result_list = [None]*(len(self.active_layers_string)-1)
        self.fault_type_list = FailureType.FAIL_LEVEL

    # return fault_type; if fault_type is DETECTOR_FAILED, the second return value is layer_num, otherwise there is no second return value
    def __verify(self, highest_layer_num, failed_instance_name):
        if self.binary_tree == None:
            return self.fault_type_list[highest_layer_num]
        # because layer number starts from 0, highest_layer_num is equal to the number of layers minus 1
        self._detection_result_list = [None]*(highest_layer_num)
        layer_num = self.binary_tree.get_data() # detect the root of the binary tree
        self.__detect_layer(layer_num, failed_instance_name)

        # detect nodes of the binary tree
        while True:
            # get next detector
            if self._detection_result_list[layer_num] == FailureType.HEALTH:
                next_layer = self.binary_tree.get_node_by_data(layer_num).get_right_node()
                if next_layer == None:
                    higher_active_layer_num = self.get_higher_active_layer_num(layer_num)
                    return  self.fault_type_list[higher_active_layer_num]
            elif self._detection_result_list[layer_num] in self.fault_type_list:
                next_layer = self.binary_tree.get_node_by_data(layer_num).get_left_node()
                if next_layer == None:
                    return  self.fault_type_list[layer_num]
            elif self._detection_result_list[layer_num] == FailureType.DETECTOR_FAILED:
                return FailureType.DETECTOR_FAILED, layer_num
            layer_num = next_layer.get_data()
            self.__detect_layer(layer_num, failed_instance_name)

    # return FailureType.HEALTH or (fault_type, failed_node_name/failed_instance_name); if in an unexpected state, it will return None
    def detect(self):
        failed_instance_name = None
        instance_name_list = self.__instance_detector.get_instance_name_list()
        # temp_active_layers_string: the active layer string used only for this detection
        temp_active_layers_string = self.active_layers_string
        # temp_highest_layer_num: the highest layer of this detection
        temp_highest_layer_num = LayerConfig.INSTANCE_LEVEL_RANGE[1]
        # if instance_name_list is empty or instance level is disabled, only detect host level 
        #self.__logger.info("FDS, detect -- vm list: {}; active layers: {}".format(str(instance_name_list), temp_active_layers_string))
        if not instance_name_list or temp_active_layers_string[LayerConfig.INSTANCE_NETWORK_LAYER_NUM] == "0":
            temp_highest_layer_num = LayerConfig.HOST_LEVEL_RANGE[1]
            highest_level_check = self.detect_host_level_highest_layer()
            if highest_level_check == FailureType.HEALTH:
                return FailureType.HEALTH
            temp_active_layers_string = self.__hide_instance_level_of_active_layers()

        else:
            highest_level_check, failed_instance_name = self.detect_instance_level_highest_layer(instance_name_list)
            if highest_level_check == FailureType.HEALTH:
                return FailureType.HEALTH

        self.__logger.info("node ({}): FDS--start to verify, temp active layers: {}".format(self.__node_name, temp_active_layers_string)) 
        # build the binary detection tree used for this detection
        self.binary_tree = self.tree_builder.build_tree(temp_active_layers_string)
        # because highest_level_check != FailureType.HEALTH, verify the fault type
        while True:
            state = self.__verify(temp_highest_layer_num, failed_instance_name)
            # if it is detector fail, state = (FailureType.DETECTOR_FAILED, failed layer number)
            if FailureType.DETECTOR_FAILED in state:
                temp_active_layers_string = self.__disable_layer(temp_active_layers_string, state[1])
                self.active_layers_string = self.__disable_layer(self.active_layers_string, state[1])
                self.binary_tree = self.tree_builder.build_tree(temp_active_layers_string)
                continue
            # failed instance has been removed from protection
            elif state == FailureType.INSTANCE_NOT_PROTECTED:
                return FailureType.HEALTH
            # if fault occurs, confirm whether fault is permanent
            elif state in FailureType.FAIL_LEVEL:
                is_permanent_fault = self.__confirm_permanent_fault(state, failed_instance_name)
                if is_permanent_fault == False:
                    return FailureType.HEALTH
                # if fault is at node level, the return value is (fault_type, failed_node_name); 
                if state in FailureType.FAIL_LEVEL[LayerConfig.HOST_LEVEL_RANGE[0]:LayerConfig.HOST_LEVEL_RANGE[1]+1]:
                    return state, self.__node_name
                # if fault is at VM level, the return value is (fault_type, failed_instance_name)
                elif state in FailureType.FAIL_LEVEL[LayerConfig.INSTANCE_LEVEL_RANGE[0]:LayerConfig.INSTANCE_LEVEL_RANGE[1]+1]:
                    # check VM operation (instance state) before recovering the fault.   (This is the third VM operation check)
                    is_recoverable = self.__instance_detector.check_instance_state_for_recovery(failed_instance_name)
                    if not is_recoverable:
                        return FailureType.HEALTH
                    return state, failed_instance_name
            return

    # disable the layer in layer_string, change value of disabled layer from 1 to 0 (1: active, 0: disabled)
    def __disable_layer(self, layer_string, layer_num):
        layer_list = list(layer_string)
        layer_list[layer_num] = "0"
        result = "".join(layer_list)
        return result

    # enable the layer in layer_string, change value of the layer from 0 to 1 (1: active, 0: disabled)
    def __enable_layer(self, layer_string, layer_num):
        layer_list = list(layer_string)
        layer_list[layer_num] = "1"
        result = "".join(layer_list)
        return result

    def __hide_instance_level_of_active_layers(self):
        try:
            string_list = list(self.active_layers_string)
            for index in range(LayerConfig.INSTANCE_LEVEL_RANGE[0], LayerConfig.INSTANCE_LEVEL_RANGE[1]+1):
                string_list[index] = "0"
            result = "".join(string_list)
            return result
        except Exception as e:
            self.__logger.error("node ({}): FaultDetectionStrategy - __hide_instance_level_of_active_layers, get exception: {}".format(self.__node_name, str(e)))
            raise e

    def _rebuild_tree(self):
        index = 0
        new_active_layers_string = ""
        for x in self._detection_result_list:
            if x == FailureType.DETECTOR_FAILED:
                new_active_layers_string += "0"
            else: 
                new_active_layers_string += self.active_layers_string[index]
            index += 1
        new_active_layers_string += "1" #add network layer
        self.active_layers_string = new_active_layers_string
        self.binary_tree = self.tree_builder.build_tree(self.active_layers_string)

    def __detect_layer(self, layer_num, failed_instance_name):
        if self._detection_result_list[layer_num] == None:
            # if layer is at host level, perform host level detection
            if LayerConfig.HOST_LEVEL_RANGE[0] <= layer_num <= LayerConfig.HOST_LEVEL_RANGE[1]:
                self._detection_result_list[layer_num] = self.function_map[layer_num]()
            # if layer is at instance level, use the instance name to perform instance level detection 
            if LayerConfig.INSTANCE_LEVEL_RANGE[0] <= layer_num <= LayerConfig.INSTANCE_LEVEL_RANGE[1]:
                self._detection_result_list[layer_num] = self.function_map[layer_num](failed_instance_name)

    def get_higher_active_layer_num(self, layer_num):
        active_layer_list = [char for char in self.active_layers_string]
        temp_list = active_layer_list[layer_num+1:len(active_layer_list)]
        higher_active_layer_num = layer_num+temp_list.index("1")+1
        return higher_active_layer_num

    def detect_host_level_highest_layer(self):
        return self.function_map[LayerConfig.HOST_LEVEL_RANGE[1]]()

    # detect the highest layer of instance level, return result and failed instance name
    def detect_instance_level_highest_layer(self, instance_name_list):
        result = FailureType.HEALTH
        failed_instance_name = None
        for instance_name in instance_name_list:
            result = self.function_map[LayerConfig.INSTANCE_LEVEL_RANGE[1]](instance_name)
            if result in FailureType.FAIL_LEVEL:
                failed_instance_name = instance_name
                break
        return result, failed_instance_name

    def detect_highest_layer(self):
        return self.function_map[-1]()

    def check_protected_layers_detector(self, protected_layers_string):
        if protected_layers_string != self.active_layers_string:
            new_active_layers_string = ""
            for string_index in range( len(protected_layers_string) ):
                if self.active_layers_string[string_index] != protected_layers_string[string_index]:
                    state = self.__detector_verification_method_list[string_index]()
                    if state != FailureType.DETECTOR_FAILED:
                        new_active_layers_string += "1"
                    else:
                        new_active_layers_string += "0"
                else:
                    new_active_layers_string += self.active_layers_string[string_index]
            if new_active_layers_string != self.active_layers_string:
                self.active_layers_string = new_active_layers_string
                self.binary_tree = self.tree_builder.build_tree(self.active_layers_string)

    def get_active_layers(self):
        return self.active_layers_string

    # confirm whether the fault is permanent, (output) True: the fault is permanent fault, False: the fault is transient fault
    def __confirm_permanent_fault(self, fault_type, failed_instance_name):
        # Because the network layer is always active (because it is the highest layer of the node level) and is the only layer where transient faults may occur, 
        # we only need to check the fault layer again for other fault cases except network layer faults.
        result = None
        failed_layer_num = FailureType.FAIL_LEVEL.index(fault_type)
        if fault_type != FailureType.NETWORK_FAIL:
            if LayerConfig.HOST_LEVEL_RANGE[0] <= failed_layer_num <= LayerConfig.HOST_LEVEL_RANGE[1]:
                result = self.function_map[failed_layer_num]()
            if LayerConfig.INSTANCE_LEVEL_RANGE[0] <= failed_layer_num <= LayerConfig.INSTANCE_LEVEL_RANGE[1]:
                result = self.function_map[failed_layer_num](failed_instance_name)
        else:
            # check network layer transient fault
            result = self.detector.check_network_transient_fault()
        if result == FailureType.HEALTH:
            return False
        else:
            return True

    def set_instance_state(self, instance_name, state):
        self.__instance_detector.set_instance_state(instance_name, state)

    def set_instance_to_default(self, instance_name):
        self.__instance_detector.revert_to_default(instance_name)

    def get_instance_name_list(self):
        return self.__instance_detector.get_instance_name_list()

    def get_instance_state(self, instance_name):
        return self.__instance_detector.get_instance_state(instance_name)

    def get_instance_id(self, instance_name):
        return self.__instance_detector.get_instance_id(instance_name)

    def log_instance_info(self, instance_name):
        self.__instance_detector.log_instance_info(instance_name)

    def setup_libvirt_detector(self, protected_layers_string):
        # detector info: [layer number, registration method] 
        libvirt_detector_info_list = [
          [LayerConfig.GUEST_OS_LAYER_NUM, self.__instance_detector.register_instance_state_callback], 
          [LayerConfig.GUEST_OS_LAYER_NUM, self.__instance_detector.register_instance_watchdog_callback]
        ]

        for info in libvirt_detector_info_list:
            # if layer protection is enabled, register layer detector
            if protected_layers_string[info[0]] == "1":
                result = info[1]()
                # temp disabled layer: the layer with protection enabled but the layer detector failed
                is_temp_disabled_layer = self.active_layers_string[info[0]] == "0"
                if result == True and is_temp_disabled_layer:
                    self.active_layers_string = self.__enable_layer(self.active_layers_string, info[0]) 
                elif result == FailureType.DETECTOR_FAILED and not is_temp_disabled_layer:
                    self.active_layers_string = self.__disable_layer(self.active_layers_string, info[0])

