#!/usr/bin/python
#########################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   HASS Service
#   Using SimpleXMLRPC library handle http requests
#   Client can use function in Hass class directly
##########################################################

import logging

from RecoveryManager import RecoveryManager
from ResourceManager import ResourceManager
from Response import Response

class Hass(object):
    #   The SimpleRPCServer class
    #   Declare method here, and client can call it directly.
    #   All of methods just process return data from recovery module
    def __init__(self):
        ResourceManager.init()
        self.Recovery_Manager = RecoveryManager()

    def create_cluster(self, cluster_name, node_name_list=[], layers_string=""):
        """
        The function for create a HA cluster. 
        You can either put node_name_list or cluster name only.
        If you put cluster name only then this function will only create a empty cluster, 
        But if you put node parameter the function will do both create cluster and add node to cluster
        Args:
            name (str): cluster name.
            node_name_list (list): the nodes would add to cluster.
        Return:
            (map) create cluster result.
            {"code" : "0","message": message} -> success.
            {"code" : "1","message": message} -> fail.
        """
        try:
            create_cluster_result = ResourceManager.create_cluster(cluster_name, layers_string)
            if create_cluster_result.code == "succeed":
                if node_name_list != []:
                    add_node_result = ResourceManager.add_node(create_cluster_result.data.get("cluster_name"), node_name_list)
                    if add_node_result.code == "succeed":
                        message = "Create HA cluster and add computing node success, cluster name is %s , add node message %s" % (
                        create_cluster_result.data.get("cluster_name"), add_node_result.message)
                        logging.info(message)
                        # result= {"code" : "0","message": message}
                        result = Response(code="succeed",
                                          message=message)
                        return result
                    else:
                        # add node fail
                        message = "The cluster is created.(name = " + create_cluster_result.data.get(
                            "cluster_name") + ") But," + add_node_result.message
                        logging.error(message)
                        # result ={"code":"0","message":message}
                        result = Response(code="succeed",
                                          message=message)
                        return result
                else:  # node_name_list is None
                    # add_node_result = {"code":"0", "cluster_name":create_cluster_result["cluster_name"], "message":"not add any node."}
                    logging.info(create_cluster_result.message)
                    return create_cluster_result
            else:
                # create cluster
                logging.error("HASS-create cluster--create cluster fail")
                return create_cluster_result
        except:
            logging.error("HASS-create cluster-except--create cluster fail, exception happens")
            return Response(code="failed", message="HASS-create cluster-except--create cluster fail, exception happens")

    def delete_cluster(self, cluster_name):
        """
        The function for delete a HA cluster. 
        Put the cluster uuid to this function, it will delete a HA cluster.
        Args:
            cluster_name (str): cluster name.
        Return:
            (map) delete cluster result.
            {"code" : "0","message": message} -> success.
            {"code" : "1","message": message} -> fail.
        """
        try:
            result = ResourceManager.delete_cluster(cluster_name)
            return result
        except:
            logging.error("HASS--delete cluster fail")
            return Response(code="failed", message="HASS--delete cluster fail, exception happens")

    def list_cluster(self):
        """
        The function for list HA clusters. 
        Args:
            no arguments
        Return:
            (list) cluster info
        """
        try:
            result = ResourceManager.list_cluster()
            return result
        except:
            logging.error("HASS--list all cluster fail")
            return Response(code="failed", message="HASS--list all cluster fail, exception happens")

    def add_node(self, cluster_name, node_name_list):
        """
        The function for add a computing node to HA cluster. 
        Put the cluster uuid and node_name_list to this function, it will add node to HA cluster.
        Args:
            cluster_name (str): cluster uuid.
            node_name_list (str): node name.
        Return:
            (map) add node result.
            {"code" : "0","message": message} -> success.
            {"code" : "1","message": message} -> fail.
        """
        try:
            result = ResourceManager.add_node(cluster_name, node_name_list)
            return result
        except:
            logging.error("HASS--add node fail")
            return Response(code="failed", message="HASS--add node fail, exception happens")

    def delete_node(self, cluster_name, node_name):
        """
        The function for delete a computing node from HA cluster. 
        Put the cluster uuid and node name to this function, it will delete node from HA cluster.
        Args:
            cluster_name (str): cluster uuid.
            node_name (str): node name.
        Return:
            (map) delete node result.
            {"code" : "0","message": message} -> success.
            {"code" : "1","message": message} -> fail.
        """
        try:
            result = ResourceManager.delete_node(cluster_name, node_name)
            return result
        except:
            logging.error("HASS--delete node fail")
            return Response(code="failed", message="HASS--delete node fail, exception happens")

    def list_node(self, cluster_name):
        """
        The function for list computing nodes from HA cluster. 
        Put the cluster uuid to this function, it will list nodes from HA cluster.
        Args:
            cluster_name (str): cluster uuid.
        Return:
            (map) list node result.
            {"code":"0","node_name_list":node_name_list} -> success.
        """
        try:
            result = ResourceManager.list_node(cluster_name)
            return result
        except:
            logging.error("HASS--List node fail")
            return Response(code="failed", message="HASS--list node fail, exception happens")

    def add_instance(self, cluster_name, instance_id):
        """
        The function for add a instance to HA cluster. 
        Put the cluster uuid and instance id to this function, it will add instance to HA cluster.
        Args:
            cluster_name (str): cluster uuid.
            instance_id (str): instance id.
        Return:
            (map) add instance result.
            {"code" : "0","message": message} -> success.
            {"code" : "1","message": message} -> fail.
        """
        try:
            result = ResourceManager.add_instance(cluster_name, instance_id)
            if result.code == 'failed':
                logging.error("HASS--add Instance fail")
                return result
            logging.info("HASS--add instance success.")
            return result
        except:
            logging.error("HASS--add Instance fail")
            return Response(code="failed", message="HASS--add instance fail, exception happens")

    def update_instance_host(self, cluster_name, instance_id):
        """
        The function for update a instance host to HA cluster.
        Put the cluster uuid and instance id to this function, it will update instance host to HA cluster.
        Args:
            cluster_name (str): cluster uuid.
            instance_id (str): instance id.
        Return:
            (map) add instance result.
            {"code" : "0","message": message} -> success.
            {"code" : "1","message": message} -> fail.
        """
        try:
            result = ResourceManager.update_instance_host(cluster_name, instance_id)
            if result.code == 'failed':
                logging.error("HASS--update Instance fail")
                return result
            logging.info("HASS--update instance success.")
            return result
        except:
            logging.error("HASS--update Instance fail")
            return Response(code="failed", message="HASS--update instance fail, exception happens")

    def delete_instance(self, cluster_name, instance_id):
        """
        The function for delete a instance from HA cluster. 
        Put the cluster uuid and instance id to this function, it will delete instance from HA cluster.
        Args:
            cluster_name (str): cluster uuid.
            instance_id (str): instance id.
        Return:
            (map) delete instance result.
            {"code" : "0","message": message} -> success.
            {"code" : "1","message": message} -> fail.
        """
        try:
            result = ResourceManager.delete_instance(cluster_name, instance_id)
            logging.info("HASS--delete instance success")
            return result
        except:
            logging.error("HASS--delete instance fail")
            return Response(code="failed", message="HASS--delete instance fail, exception happens")

    def list_instance(self, cluster_name):
        """
        The function for list instances from HA cluster. 
        Put the cluster uuid to this function, it will list instances from HA cluster.
        Args:
            cluster_name (str): cluster uuid.
        Return:
            (map) list instance result.
            {"code":"0","instanceList":instance_list}-> success.
        """
        try:
            result = ResourceManager.list_instance(cluster_name)
            logging.info("HASS-list instance success")
            return result
        except:
            logging.error("HASS--list instance fail")
            return Response(code="failed", message="HASS-- list instance fail, exception happens")

    def recover(self, fail_type, cluster_name, fail_node_name):
        """
        The function for recover compute node fail from HA cluster. 
        Put the fail type, cluster uuid and node name to this function, it will start to recover compute node fail
        Args:
            fail_type (str): fail type
            cluster_name (str): cluster uuid
            node_name(str): node name
        Return:
            (bool) recover success or not.
            True -> success.
            False -> fail.
        """
        try:
            result = self.Recovery_Manager.recover(fail_type, cluster_name, fail_node_name)
            return result
        except Exception as e:
            print str(e)
            logging.error(str(e))
            logging.error("HASS--recover node/vm %s fail" % fail_node_name)
            return Response(code="failed", message="HASS--recover node %s fail" % fail_node_name)

    def update_db(self):
        """
        The function for updating the data structures in the system. 
        Args:
        Return:
            (bool) recover success or not.
            True -> success.
            False -> fail.
        """
        try:
            result = ResourceManager.sync_to_database()
            return result
        except Exception as e:
            logging.error("HASS--update database fail : %s" % str(e))
            return Response(code="failed", message="HASS--update database fail : %s" % str(e))

    def update_all_clusters(self):
        try:
            ResourceManager.update_all_clusters()
        except Exception as e:
            logging.error("HASS--updateAllCluster fail :" + str(e))
            return Response(code="failed", message="HASS--updateAllCluster fail :" + str(e))



