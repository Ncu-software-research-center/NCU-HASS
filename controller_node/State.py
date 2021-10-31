#########################################################
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
FAIL_LEVEL = [POWER_FAIL, OS_FAIL, NETWORK_FAIL, SERVICE_FAIL]
