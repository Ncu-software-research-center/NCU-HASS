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
#   This is a interface for node data structure.
#########################################################

from NovaClient import NovaClient
from DetectionThread import DetectionThread
from IPMIModule import IPMIModule
import ConfigParser
import socket
import logging


class NodeInterface(object):
    def __init__(self, name, cluster_name):
        self.name = name
        self.cluster_name = cluster_name
        self.ipmi = IPMIModule()
        self.ipmi_status = self.ipmi._getIPMIStatus(self.name)
        self.nova_client = NovaClient.getInstance()
        self.detection_thread = None
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.initDetectionThread()

    def setNodeName(self, name):
        self.name = name

    def getNodeName(self):
        return self.name

    def setClusterId(self, cluster_name):
        self.cluster_name = cluster_name

    def getClusterId(self, cluster_name):
        return self.cluster_name

    '''
    def addInstance(self, instance):
        self.protected.instance_list.append(instance)

    def removeInstance(self, instance):
        self.instance_list.remove(instance)

    def initInstanceList(self):
        self.instance_list = []
    '''

    def initDetectionThread(self):

        cluster_name = self.cluster_name
        node = self
        polling_port = int(self.config.get("detection", "polling_port"))
        # ipmi_status = self.ipmi_status
        polling_interval = float(self.config.get("detection", "polling_interval"))

        self.detection_thread = DetectionThread(cluster_name, node, polling_port, polling_interval)

    def startDetectionThread(self):
        self.detection_thread.daemon = True
        self.detection_thread.start()

    def deleteDetectionThread(self):
        self.detection_thread.stop()

    def getInfo(self):
        return {
            "node_name":self.name, 
            "below_cluster_name": self.cluster_name,
            "ipmi_enable" : self.ipmi_status
        }

    def sendUpdateInstance(self):
        # try:
        #     logging.info("Init update instance socket to %s" % self.name)
        #     so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     so.settimeout(10)
        #     so.connect((self.name, 5001))
        #     so.send("update instance")
        #     so.close()
        # except Exception as e:
        #     logging.error("send updata instance fail %s" % str(e))
        pass

    def undefine_instance_via_socket(self, instance):
        port = int(self.config.get("detection", "polling_port"))
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(0)
            sock.settimeout(10)
            sock.connect((self.name, port))

            msg = "undefine %s" % instance.name
            sock.sendall(msg)
            data, addr = sock.recvfrom(1024)
            if data != "OK":
                logging.error("undefine instance fail msg %s" % data)
        except Exception as e:
            logging.error("socket send undefine instance fail %s" % str(e))
        finally:
            if sock:
                sock.close()
                print "sock close"


if __name__ == "__main__":
    a = NodeInterface("compute1", "23")
    a.send_undefine_instance_via_socket("instance-00000052")
    while True:
        pass
