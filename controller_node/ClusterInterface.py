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
#	This is a interface designed for cluster.
##########################################################


from NovaClient import NovaClient


class ClusterInterface(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.node_list = []
        self.nova_client = NovaClient.getInstance()
        self.instance_list = []
        # self.db = DatabaseManager()
