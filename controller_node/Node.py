#########################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   This is a class maintains node data structure.
##########################################################

from DetectionThread import DetectionThread
from IPMIModule import IPMIModule
import ConfigParser
import socket
import logging
import paramiko
import time
import FailureType
import Queue

class Node(object):
    def __init__(self, name, cluster_name, protected_layers_string):
        self.name = name
        self.cluster_name = cluster_name
        self.ipmi = IPMIModule()
        self.ipmi_status = self.ipmi.get_ipmi_status(self.name)
        self.detection_thread = None
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.protected_layers_string = protected_layers_string
        self.__instance_update_queue = Queue.Queue()
        self._init_detection_thread()
        self.client = self._create_ssh_client()
        self.status = FailureType.HEALTH
        

    def start(self):
        return self.ipmi.start_node(self.name)

    def shutoff(self):
        return self.ipmi.shut_off_node(self.name)

    def reboot(self):
        return self.ipmi.reboot_node(self.name)

    def instance_overlapping_in_libvirt(self, instance):
        return instance.name in self._get_virsh_list()

    def undefine_instance(self, instance):
        logging.info("undefine instance")
        stdin, stdout, stderr = self._remote_exec("virsh destroy %s" % instance.name)
        print stdout.read()
        stdin, stdout, stderr = self._remote_exec("virsh undefine %s" % instance.name)
        print stdout.read()

    def _get_virsh_list(self):
        stdin, stdout, stderr = self._remote_exec("virsh list --all")
        return stdout.read()

    def _remote_exec(self, cmd):
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=5)
            return stdin, stdout, stderr
        except Exception as e:
            logging.error("Node - failed connect to node, establishing new SSH connection")
            self.client = self._create_ssh_client()
            if not self.client:
               logging.error("Node - SSH connection failed to establish")
               return
            try:
                stdin, stdout, stderr = self.client.exec_command(cmd, timeout=5)
                return stdin, stdout, stderr
            except Exception as e:
                logging.error("Node - failed connect to node twice, failed to run command")
                return
        
    def _create_ssh_client(self, default_timeout=1):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(self.name, username='root', password='openstack', timeout=default_timeout)
            return client
        except Exception as e:
            logging.error("Excpeption : %s" % str(e))
            print "Excpeption : %s" % str(e)
            return None

    def delete_ssh_client(self):
        if self.client:
            self.client.close()
            logging.info("ssh client closed")

    def start_detection_thread(self):
        self.detection_thread.daemon = True
        self.detection_thread.start()

    def _init_detection_thread(self):
        cluster_name = self.cluster_name
        node = self
        polling_interval = float(self.config.get("detection", "polling_interval"))
        protected_layers_string = self.protected_layers_string
        self.detection_thread = DetectionThread(cluster_name, node, polling_interval, protected_layers_string, self.__instance_update_queue)

    def delete_detection_thread(self):
        self.detection_thread.stop()

    def get_info(self):
        return {
            "node_name":self.name, 
            "below_cluster_name": self.cluster_name,
            "ipmi_enable" : self.ipmi_status,
            "status" : self.status,
            "protected_layers_string" : self.protected_layers_string
        }

    def get_name(self):
        return self.name

    def get_status(self):
        return self.status

    def set_status(self, new_status):
        self.status = new_status

    def get_layer_strings(self):
        return self.protected_layers_string

    def set_layer_strings(self, new_layer_strings):
        self.protected_layers_string = new_layer_strings

    def send_update_instance(self, action, instance_name, provider_network = None, instance_id = None):
        try:
            update_information = [action, instance_name, provider_network, instance_id]
            self.__instance_update_queue.put(update_information)
        except Exception as e:
            logging.error("send updata instance fail %s" % str(e))

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
            else :
                logging.info("undefine instance success msg %s" % data)
        except Exception as e:
            logging.error("socket send undefine instance fail %s" % str(e))
        finally:
            if sock:
                sock.close()
                print "sock close"

if __name__ == "__main__":
    a = Node("compute1", "test", "111")
    # a.send_update_instance()
    # b = Instance("xx", "instance-0000023e", "compute2")
    # # print a.undefineInstance(b)
    # i, out, err = a._remote_exec("echo 123")
    # print out.read()
    
