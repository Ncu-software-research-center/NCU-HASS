#########################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#	This is a class which maintains cluster data structure.
##########################################################

from ClusterInterface import ClusterInterface
from Response import Response
from Node import Node
from Instance import Instance
from IPMIModule import IPMIModule
from NovaClient import NovaClient
from Scheduler import Scheduler
import socket
import logging
import ConfigParser

import InstanceQueueConfig


class Cluster(object):
    def __init__(self, name, layers_string):
        self.name = name
        self.node_list = []
        self.nova_client = NovaClient.get_instance()
        self.instance_list = []
        self.protected_layers_string = layers_string
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.scheduler = Scheduler()
        

    def add_node(self, node_name_list):
        # create node list
        message = ""
        if node_name_list == []:
            return Response(code="failed",
                            message="not enter any node",
                            data=None)
        try:
            for node_name in node_name_list:
                if self._is_in_compute_pool(node_name):
                #if self._is_in_compute_pool(node_name) and self.ipmi._getIPMIStatus(node_name) == True:
                    # print node_name_list
                    logging.info("Cluster--the layer string: {}".format(self.protected_layers_string))
                    node = Node(name=node_name, cluster_name=self.name, protected_layers_string=self.protected_layers_string)
                    logging.info("Cluster--node object is init")
                    self.node_list.append(node)
                    node.start_detection_thread()
                    message = "Cluster--The node %s is added to cluster." % self._get_all_node_str()
                    logging.info(message)
                    # result = {"code": "0","cluster_name": self.name,"node":node_name, "message": message}
                    # print 'berhasil'
                    result = Response(code="succeed",
                                      message=message,
                                      data={"cluster_name": self.name, "node": self._get_all_node_list()})
                else:
                    message += "the node %s is illegal. may be shutted down or not in the compute pool, please check the configuration.  " % node_name
                    result = Response(code="failed",
                                      message=message,
                                      data={"cluster_name": self.name, "node": self._get_all_node_list()})
                    logging.error(message)
        except Exception as e:
            node_list_string = self._get_all_node_str()
            message = "Cluster-- add node fail , some node maybe overlapping or not in compute pool please check again! The node list is {node_list}, exception message: {e_message}.".format(node_list = node_list_string, e_message = str(e))
            logging.error(message)
            # result = {"code": "1", "cluster_name": self.name, "message": message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": self.name})
        finally:
            return result

    def delete_node(self, node_name):
        try:
            node = self.get_node_by_name(node_name)
            # stop Thread
            protected_instance = self.get_protected_instance_list_by_node(node)
            if protected_instance == []:
                node.delete_detection_thread()
                node.delete_ssh_client()
                self.node_list.remove(node)
                for node in self.node_list:
                    if node.name == node_name:
                        return Response(code="failed",
                                        message="delete node %s failed" % node_name,
                                        data={"fail_node":node_name})
                message = "Cluster delete node success! node is %s , node list is %s,cluster name is %s." % (
                    node_name, self._get_all_node_str(), self.name)
                logging.info(message)
                result = Response(code="succeed",
                              message=message,
                              data={"cluster_name": self.name, "node": node_name})
            else :
                result = Response(code="failed",
                                        message="delete node %s failed, there is protected instance inside" % node_name,
                                        data={"fail_node":node_name})
        except Exception as e:
            logging.error(str(e))
            message = "Cluster delete node fail , node maybe not in the node list please check again! node is %s  The node list is %s." % (
                node_name, self._get_all_node_str())
            logging.error(message)
            # result = {"code": "1", "node":node_name,"cluster_name": self.name, "message": message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": self.name, "node": node_name})
        finally:
            return result

    def get_all_node_info(self):
        nodes_info = []
        for node in self.node_list:
            nodes_info.append(node.get_info())
        return nodes_info

    def add_instance(self, instance_id):
        if not self._check_instance_exist(instance_id):
            return Response(code="failed",
                            message="instance %s doesn't exist" % instance_id,
                            data=None)
        elif not self._check_instance_boot_from_volume(instance_id):
            return Response(code="failed",
                            message="instance %s doesn't booted from volume" % instance_id,
                            data=None)
        elif not self._check_instance_power_on(instance_id):
            return Response(code="failed",
                            message="instance %s is not power on" % instance_id,
                            data=None)
        else:
            try:
                # Live migration VM to cluster node
                final_host = self._check_instance_host(instance_id)
                if final_host == None:
                    message = "Cluster-- instance host ({host_name}) not in the cluster, failed to add protection to instance ({vm_id})".format(host_name=final_host, vm_id=instance_id)
                    logging.error(message)
                    result = Response(code="failed",
                                    message=message,
                                    data=None)
                    return result
                # check the parameters of the Instance object initialization
                instance_name = self.nova_client.get_instance_name(instance_id)
                instance_status = self.nova_client.get_instance_state(instance_id)
                provider_network = self.nova_client.get_instance_network(instance_id)
                parameter_list = [instance_name, final_host, instance_status, provider_network]
                if None in parameter_list:
                    none_index = parameter_list.index(None)
                    parameter_name_list = ['instance name', 'located host', 'instance status', 'provider network ip of instance']
                    message = "Cluster-- Failed to get the information ({parameter_name)}) for adding instance ({instance_id}) from Openstack, please check the settings.".format(parameter_name=parameter_name_list[none_index], instance_id=instance_id)
                    result = Response(code="failed",
                            message=message,
                            data=None)
                    return result

                instance = Instance(id=instance_id,
                                    name=instance_name,
                                    host=final_host,
                                    status=instance_status,
                                    network=provider_network)
                
                self.instance_list.append(instance)
                # send information of new instance to node detection thread
                update_action = InstanceQueueConfig.ADD_INSTANCE
                instance_name = instance.get_name()
                instance_network_provider = instance.get_network_provider()
                instance_id = instance.get_id()
                host = self.get_node_by_name(final_host)
                host.send_update_instance(update_action, instance_name, instance_network_provider, instance_id)

                message = "Cluster--Cluster add instance success ! The instance id is %s." % (instance_id)
                logging.info(message)
                # result = {"code":"0","cluster id":self.name,"node":final_host,"instance id":instance_id,"message":message}
                result = Response(code="succeed",
                                  message=message,
                                  data={"cluster_name": self.name, "node": final_host, "instance id": instance_id})
                return result
            except Exception as e:
                print str(e)
                message = "Cluster--Cluster add instance fail ,please check again! The instance id is %s." % (instance_id)
                logging.error(message)
                # result = {"code":"1","cluster id":self.name,"instance id":instance_id,"message":message}
                result = Response(code="failed",
                                  message=message,
                                  data={"cluster_name": self.name, "instance id": instance_id})
                return result

    def delete_instance(self, instance_id):
        result = None
        for instance in self.instance_list:
            host = instance.host
            if instance.id == instance_id:
                self.instance_list.remove(instance)
                # send instance deletion information to node detection thread
                update_action = InstanceQueueConfig.REMOVE_INSTANCE
                instance_name = instance.get_name()
                host = self.get_node_by_name(host)
                host.send_update_instance(update_action, instance_name)

                message = "Cluster--delete instance success. this instance is deleted (instance_id = %s)" % instance_id
                logging.info(message)
                # result = {"code": "0", "cluster_name": self.name, "instance id": instance_id, "message": message}
                result = Response(code="succeed",
                                  message=message,
                                  data={"cluster_name": self.name, "instance_id": instance_id})
        # if instanceid not in self.instacne_list:
        if result == None:
            message = "Cluster--delete instance fail ,please check again! The instance id is %s." % instance_id
            logging.error(message)
            # result = {"code": "1", "cluster id": self.name, "instance id": instance_id, "message": message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": self.name, "instance_id": instance_id})
        return result

    def update_instance_host(self, instance_id, from_recover_vm = False):
        try:
            for instance in self.instance_list:
                if instance.id == instance_id:
                    original_host = instance.host
                    final_host = self.nova_client.get_instance_host(instance_id)
                    logging.info("Cluster, update_instance_host - updated instance ({}): original host:{}, final host : {}".format(instance_id, original_host, final_host))
                    if original_host != final_host:
                        instance.update_info()
                        # send information of new instance to node detection thread
                        if from_recover_vm:
                            update_action = InstanceQueueConfig.EVACUATE_INSTANCE
                        else:
                            update_action = InstanceQueueConfig.ADD_INSTANCE
                        instance_name = instance.get_name()
                        instance_network_provider = instance.get_network_provider()
                        instance_id = instance.get_id()
                        host = self.get_node_by_name(final_host)
                        host.send_update_instance(update_action, instance_name, instance_network_provider, instance_id)
                        # send instance deletion information to node detection thread
                        update_action = InstanceQueueConfig.REMOVE_INSTANCE
                        host = self.get_node_by_name(original_host)
                        host.send_update_instance(update_action, instance_name)

                        # result = {"code":"0","cluster id":self.name,"node":final_host,"instance id":instance_id,"message":message}
                        result = Response(code="succeed",
                              message=message,
                              data={"cluster_name": self.name, "instance id": instance_id})
                        break
            return result
        except Exception as e:
            print str(e)
            message = "Cluster, update_instance_host - instance({}) update fail, exception message: {}".format(instance_id, str(e))
            logging.error(message)
            # result = {"code":"1","cluster id":self.name,"instance id":instance_id,"message":message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": self.name, "instance id": instance_id})
            return result

    # list Instance
    def get_all_instance_info(self):
        instances_info = []
        for instance in self.instance_list[:]:
            instances_info.append(instance.get_info())
        return instances_info

    def _is_in_compute_pool(self, node_name):
        return node_name in self.nova_client.get_compute_pool()

    # be DB called
    def get_node_list(self):
        return self.node_list

    # be deleteNode called
    def get_node_by_name(self, node_name):
        # node_list = self.get_node_list()
        for node in self.node_list:
            if node.name == node_name:
                return node
        return None

    # addNode message
    def _get_all_node_str(self):
        ret = ""
        for node in self.node_list:
            ret += node.name + " "
        return ret

    def _get_all_node_list(self):
        ret = []
        for node in self.node_list:
            ret.append(node.name)
        return ret

    def get_info(self):
        return {"cluster_name": self.name}

    def _check_instance_boot_from_volume(self, instance_id):
        # if specify shared_storage to be true, enable file level HA and volume level HA
        if self.config.getboolean("default", "shared_storage") == True:
            return True
        if not self.nova_client.is_instance_boot_from_volume(instance_id):
            message = "this instance doesn't boot from volume! Instance id is %s " % instance_id
            logging.error(message)
            return False
        return True

    def _check_instance_power_on(self, instance_id):
        if not self.nova_client.is_instance_power_on(instance_id):
            message = "this instance is not running! Instance id is %s " % instance_id
            logging.error(message)
            return False
        return True

    def _check_instance_exist(self, instance_id):
        instance_list = self.nova_client.get_all_instance_list()
        for instance in instance_list:
            # print node_list
            if instance.id == instance_id:
                #logging.info("Cluster--add_instance-_check_instance_exist success")
                return True
        message = "this instance is not exist. Instance id is %s. " % instance_id
        logging.error(message)
        return False

    def is_instance_protected(self, instance_id):
        for instance in self.instance_list[:]:
            if instance.id == instance_id:
                message = "this instance is  already in the cluster. Instance id is %s. cluster name is %s .instance list is %s" % (instance_id, self.name, self.instance_list)
                logging.error(message)
                return True
        return False

    def find_target_host(self, fail_node):
        target_list = [node for node in self.node_list if node != fail_node]
        target_host = self.scheduler.find_target_host(target_list)
        return target_host

    # update all information of all instances
    def update_instance(self):
        for instance in self.instance_list:
            original_host = instance.get_host()
            instance.update_info()
            current_host = instance.get_host()
            if original_host != current_host:
                logging.info("Cluster, update_instance - instance ({}) host updated, current host is {}".format(instance.get_name(), str(current_host)))
                # update instance info of node detection thread by instance update queue
                # -- send information of new instance to node detection thread
                update_action = InstanceQueueConfig.ADD_INSTANCE
                instance_name = instance.get_name()
                instance_network_provider = instance.get_network_provider()
                instance_id = instance.get_id()
                host = self.get_node_by_name(current_host)
                host.send_update_instance(update_action, instance_name, instance_network_provider, instance_id)
                # send instance deletion information to node detection thread
                update_action = InstanceQueueConfig.REMOVE_INSTANCE
                host = self.get_node_by_name(original_host)
                host.send_update_instance(update_action, instance_name)
        #message = "Cluster, update_instance - update all instances success!"
        #logging.info(message)

    def _check_instance_host(self, instance_id):
        host = self.nova_client.get_instance_host(instance_id)
        for node in self.node_list[:]:
            if host == node.name:
                return host
        return None

    def _live_migrate_instance(self, instance_id):
        host = self.nova_client.get_instance_host(instance_id)
        target_host = self.find_target_host(host)
        print "start live migrate vm from ", host, "to ", target_host.name
        final_host = self.nova_client.live_migrate_vm(instance_id, target_host.name)
        # print final_host
        return final_host

    def evacuate(self, instance, target_host, fail_node):
        self.nova_client.evacuate(instance, target_host, fail_node)

    def get_protected_instance_list(self):
        return self.instance_list

    def get_protected_instance_by_instance_name(self, instance_name):
        for instance in self.instance_list:
            if instance.get_name() == instance_name:
                return instance
        return None

    def get_protected_instance_list_by_node(self, node):
        ret = []
        protected_instance_list = self.get_protected_instance_list()
        for instance in protected_instance_list:
            if instance.host == node.name:
                ret.append(instance)
        return ret


if __name__ == "__main__":
    a = Cluster("test")
    print a._check_instance_host
