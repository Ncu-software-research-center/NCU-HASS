#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import FailureType
from TreeBuilder import TreeBuilder 

from Detector import Detector


class FaultDetectionStrategy(object):
    def __init__(self, node, needed_layers_string='111'):
        self.needed_layers_string = needed_layers_string
        self.tree_builder = TreeBuilder()
        self.binary_tree = self.tree_builder.build_tree(self.needed_layers_string)
        self.detector = Detector(node)
        self.function_map = [self.detector.check_power_status, self.detector.check_os_status,
                         self.detector.check_network_status]
        self._detection_result_list = [None]*(len(self.needed_layers_string)-1)
        self.fault_type_list = FailureType.FAIL_LEVEL

    def _verify(self):
        if self.binary_tree == None:
            return self.fault_type_list[-1]
        self._detection_result_list = [None]*(len(self.needed_layers_string)-1)
        layer_num = self.binary_tree.get_data()
        self._detect_layer(layer_num)
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
            layer_num = next_layer.get_data()
            self._detect_layer(layer_num)

    def detect(self):
        highest_level_check = self.detect_highest_layer()
        if highest_level_check != FailureType.HEALTH:
            state = self._verify()
            if state == FailureType.HEALTH:
                return FailureType.HEALTH
            else:
                return state
        return FailureType.HEALTH

    def _detect_layer(self, layer_num):
        if self._detection_result_list[layer_num] == None:
            self._detection_result_list[layer_num] = self.function_map[layer_num]()

    def get_higher_active_layer_num(self, layer_num):
        active_layer_list = [char for char in self.needed_layers_string]
        temp_list = active_layer_list[layer_num+1:len(active_layer_list)]
        higher_active_layer_num = layer_num+temp_list.index("1")+1
        return higher_active_layer_num

    def detect_highest_layer(self):
        return self.function_map[-1]()
