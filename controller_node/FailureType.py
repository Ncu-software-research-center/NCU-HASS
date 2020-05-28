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
#   Data storage file for computing nodes state.
##########################################################

HEALTH = "health"
NETWORK_FAIL = "network"
OS_FAIL = "os"
POWER_FAIL = "power"
FAIL_LEVEL = [POWER_FAIL, OS_FAIL, NETWORK_FAIL]
NETWORK_RECOVER_FAIL = "network and recover fail"
OS_RECOVER_FAIL = "os and recover fail"
POWER_RECOVER_FAIL = "power and recover fail"
DETECTOR_FAILED = "detector failed"
DETECTOR_NOT_SUPPORTED = "detector not supported"