#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

INSTANCE_NETWORK_LAYER_NUM = 6
GUEST_OS_LAYER_NUM = 5
INSTANCE_PROCESS_LAYER_NUM = 4
HOST_NETWORK_LAYER_NUM = 3
HOST_OS_LAYER_NUM = 2
HOST_HARDWARE_LAYER_NUM = 1
HOST_POWER_LAYER_NUM = 0

HOST_LEVEL_RANGE = [HOST_POWER_LAYER_NUM, HOST_NETWORK_LAYER_NUM]
INSTANCE_LEVEL_RANGE = [INSTANCE_PROCESS_LAYER_NUM, INSTANCE_NETWORK_LAYER_NUM]