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
#   This is a class which maintains instance data structure
##########################################################


from NovaClient import NovaClient



class Instance(object):
    def __init__(self, id, name, host, status, network):
        self.id = id
        self.name = name
        self.host = host
        self.network = network
        self.status = status
        self.nova_client = NovaClient.get_instance()

    def get_ip(self, interface_name):
        return self.nova_client.get_instance_network(self.id)[interface_name][0]

    def update_info(self):
        self.host = self.nova_client.get_instance_host(self.id)
        self.status = self.nova_client.get_instance_state(self.id)
        self.network = self.nova_client.get_instance_network(self.id)

    def get_info(self):
        return {
            'id':self.id,
            'name':self.name,
            'host':self.host,
            'status':self.status,
            'network':self.network
        }