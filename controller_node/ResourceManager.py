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
#	This is a static class which maintains all the data structure.
##########################################################

from Cluster import Cluster
from DatabaseManager import DatabaseManager
from Response import Response
import logging


class ResourceManager():
    _cluster_dict = None
    _db = None
    _RESET_DB = False

    @staticmethod
    def init():
        ResourceManager._cluster_dict = {}
        ResourceManager._db = DatabaseManager()
        ResourceManager._db.create_table()
        ResourceManager._sync_from_database()

    @staticmethod
    def create_cluster(cluster_name):
        if ResourceManager._is_name_overlapping(cluster_name):
            message = "ResourceManager - cluster name overlapping"
            # result = {"code": "1","cluster_name":cluster_name, "message": message}
            logging.error(message)
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": cluster_name})
            return result
        else:
            logging.info("ResourceManager - cluster name is not overlapping")
            result = ResourceManager._add_to_cluster_list(cluster_name)
            ResourceManager.sync_to_database()
            return result

    @staticmethod
    def delete_cluster(cluster_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            message = "delete cluster fail. The cluster is not found. (cluster_name = %s)" % cluster_name
            # result = {"code": "1", "cluster_name":cluster_name, "message":message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": cluster_name})
            return result
        else:
            result = None
            try:
                if cluster.node_list == []:
                    del ResourceManager._cluster_dict[cluster_name]
                else:
                    message = "delete cluster failed, there is protected node in the cluster"
                    logging.error(message)
                    result = Response(code="failed",
                                      message=message,
                                      data={"cluster_name": cluster_name})
                    return result
                # check del cluster
                for cluster in ResourceManager._cluster_dict:
                    if cluster == cluster_name:
                        message = "delete cluster fail"
                        logging.error(message)
                        result = Response(code="failed",
                                          message=message,
                                          data={"cluster_name": cluster_name})
                if result == None:
                    message = "delete cluster success. The cluster is deleted. (cluster_name = %s)" % cluster_name
                    logging.info(message)
                    # result = {"code": "0", "cluster_name": cluster_name, "message": message}
                    result = Response(code="succeed",
                                      message=message,
                                      data={"cluster_name": cluster_name})
                ResourceManager.sync_to_database()
                return result
            except Exception as e:
                message = "delete_cluster fail" + str(e)
                logging.error(message)
                result = Response(code="failed",
                                  message=message,
                                  data={"cluster_name": cluster_name})
                return result

    @staticmethod
    def get_clusterList():
        return ResourceManager._cluster_dict

    @staticmethod
    def list_cluster():
        clusters_info = []
        for cluster_key, cluster in ResourceManager._cluster_dict.iteritems():
            clusters_info.append((cluster.get_info()))
        return clusters_info

    @staticmethod
    def add_node(cluster_name, node_name_list):
        message = ""
        tmp = list(set(node_name_list)) # remove duplicate
        for node_name in tmp[:]:
            if not ResourceManager._check_node_overlapping_for_all_cluster(node_name):
                print "%s is already in a HA cluster. " % node_name
                logging.error("%s is already in a HA cluster. " % node_name)
                message += "%s is overlapping node" % node_name
                tmp.remove(node_name)
        if tmp == []:
            logging.error("node overlapping %s" % (str(node_name_list)))
            return Response(code="failed",
                            message="node overlapping %s" % (str(node_name_list)),
                            data={"overlapping_node":node_name_list})
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            message += "ResourceManager--Add the node to cluster failed. The cluster is not found. (cluster_name = %s)" % cluster_name
            # result = {"code": "1", "cluster_name":cluster_name, "message":message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": cluster_name})
            return result
        else:
            try:
                result = cluster.add_node(tmp)
                logging.info("ResourceManager--add node success.cluster name is %s ,node is %s " % (cluster_name, tmp))
                ResourceManager.sync_to_database()
                return result
            except Exception as e:
                message += "add node fail. node not found. (node_name = %s)"  % tmp +str(e)
                logging.error(message)
                # result = {"code": "1", "cluster_name": cluster_name, "message": message}
                result = Response(code="failed",
                                  message=message,
                                  data={"cluster_name": cluster_name})
                return result

    @staticmethod
    def delete_node(cluster_name, node_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            message = "delete the node failed. The cluster is not found. (cluster_name = %s)" % cluster_name
            # result = {"code": "1", "cluster_name":cluster_name, "message":message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": cluster_name})
            return result
        else:
            try:
                result = cluster.delete_node(node_name)
                logging.info(
                    "ResourceManager-- delete node success ,cluster name is %s node is %s" % (cluster_name, node_name))
                ResourceManager.sync_to_database()
                return result
            except Exception as e:
                # code = "1"
                message = "delete node fail. node not found. (node_name = %s)" % node_name + str(e)
                logging.error(message)
                # result = {"code": "1", "cluster_name":cluster_name, "message":message}
                result = Response(code="failed",
                                  message=message,
                                  data={"cluster_name": cluster_name})
                return result

    @staticmethod
    def list_node(cluster_name):
        try:
            cluster = ResourceManager.get_cluster(cluster_name)
            if not cluster:
                message = "list the node failed. The cluster is not found. (cluster_name = %s)" % cluster_name
                # result = {"code": "1", "cluster_name":cluster_name, "message":message}
                result = Response(code="failed",
                                  message=message,
                                  data={"cluster_name": cluster_name})
                return result
            nodelist = cluster.get_all_node_info()
            message = "ResourceManager-list_node--get all node info finish"
            logging.info(message)
            result = Response(code="succeed",
                              message=message,
                              data={"cluster_name": cluster_name, "nodeList": nodelist})
            return result
        except Exception as e:
            message = "ResourceManager--list_node-- get all node info fail" + str(e)
            logging.error(message)
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": cluster_name})
            return result

    @staticmethod
    def add_instance(cluster_name, instance_id):
        cluster = ResourceManager.get_cluster(cluster_name)
        message = ""
        if not cluster:
            message = "ResourceManager--Add the instance to cluster failed. The cluster is not found. (cluster_name = %s)" % cluster_name
            # result = {"code": "1", "cluster_name":cluster_name, "message":message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": cluster_name})
            return result
        else:
            try:
                if not ResourceManager._check_instance_not_overlapping_for_all_cluster(instance_id):
                    return Response(code="failed",
                                    message="instance %s is already being protected" % instance_id,
                                    data={"instance": instance_id})
                result = cluster.add_instance(instance_id)
                if result.code == 'failed':
                    return result
                ResourceManager.sync_to_database()
                logging.info(
                    "ResourceManager--Add instance success , instance_id : %s , cluster_name : %s" % (
                    instance_id, cluster_name))
                return result
            except Exception as e:
                print str(e)
                message = "ResourceManager --add the instacne fail.instance_id : %s , cluster_name : %s "  % (
                    instance_id, cluster_name) + str(e)
                logging.error(message)
                # result = {"code": "1", "cluster_name": cluster_name, "message": message}
                result = Response(code="failed",
                                  message=message,
                                  data={"cluster_name": cluster_name})
                return result

    @staticmethod
    def delete_instance(cluster_name, instance_id):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            message = "delete the instance to cluster failed. The cluster is not found. (cluster_name = %s)" % cluster_name
            # result = {"code": "1", "cluster_name": cluster_name, "instance id ": instance_id, "message": message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": cluster_name, "instance id": instance_id})
            return result
        else:
            try:
                result = cluster.delete_instance(instance_id)
                ResourceManager.sync_to_database()
                logging.info("ResourceManager--delete instance success")
                return result
            except Exception as e:
                #logging.error(str(e))
                print str(e)
                message = "ResourceManager--delete instance failed. this instance is not being protected (instance_id = %s)" % instance_id +str(e)
                logging.error(message)
                # result = {"code": "1", "cluster_name":cluster_name, "message":message}
                result = Response(code="failed",
                                  message=message,
                                  data={"cluster_name": cluster_name})
                return result

    @staticmethod
    def list_instance(cluster_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            message = "ResourceManager--list the instance failed. The cluster is not found. (cluster_name = %s)" % cluster_name
            return Response(code="failed",
                            message=message,
                            data={"cluster_name": cluster_name})
        try:
            instance_list = cluster.get_all_instance_info()
            logging.info("ResourceManager--list_instance,getInstanceList success,instanceList is %s" % instance_list)
            result = Response(code="succeed",
                              message=None,
                              data={"instanceList": instance_list})
            return result
        except:
            logging.error("ResourceManager--list_instance,getInstanceList fail")

    @staticmethod
    def _add_to_cluster_list(cluster_name):
        try:
            cluster = Cluster(cluster_name)
            ResourceManager._cluster_dict[cluster_name] = cluster
            message = "ResourceManager -sync to db -- create_cluster._add_to_cluster_list success, cluster_name : %s" % cluster_name
            logging.info(message)
            result = Response(code="succeed",
                               message=message,
                               data={"cluster_name": cluster_name})
            return result            
        except Exception as e:
            message = "ResourceManager - create_cluster._add_to_cluster_list fail,cluster_name : %s" % cluster_name + str(e)
            logging.error(message)
            # result = {"code": "1","cluster_name":cluster_name, "message": message}
            result = Response(code="failed",
                              message=message,
                              data={"cluster_name": cluster_name})
            return result

    @staticmethod
    def _check_node_overlapping_for_all_cluster(node_name):
        for name, cluster in ResourceManager._cluster_dict.items():
            if cluster.get_node_by_name(node_name) :
                logging.error("%s already be add into cluster %s" % (node_name))
                return False
        return True

    @staticmethod
    def _check_instance_not_overlapping_for_all_cluster(instance_id):
        for name, cluster in ResourceManager._cluster_dict.items():
            if cluster.is_instance_protected(instance_id):
                return False
        return True

    @staticmethod
    def get_cluster(cluster_name):
        if not ResourceManager._is_cluster(cluster_name):
            logging.error("cluster not found id %s" % cluster_name)
            return None
        return ResourceManager._cluster_dict[cluster_name]

    @staticmethod
    def _is_name_overlapping(name):
        for cluster_name, cluster in ResourceManager._cluster_dict.items():
            if cluster.name == name:
                return True
        return False

    @staticmethod
    def _is_cluster(cluster_name):
        if cluster_name in ResourceManager._cluster_dict:
            return True
        return False

    @staticmethod
    def update_all_clusters():
        for cluster_name, cluster in ResourceManager._cluster_dict.items():
            cluster.update_instance()
        ResourceManager.sync_to_database()

    @staticmethod
    def _sync_from_database():
        ResourceManager._cluster_dict = {}
        try:
            exist_cluster = ResourceManager._db.sync_from_db()
            for cluster in exist_cluster:
                ResourceManager.create_cluster(cluster["cluster_name"])
                if cluster["node_list"] != []:
                    ResourceManager.add_node(cluster["cluster_name"], cluster["node_list"])
                for instance in cluster["instance_list"]:
                    ResourceManager.add_instance(cluster["cluster_name"], instance)
            logging.info("ResourceManager--synco from DB finish")
        except Exception as e:
            print str(e)
            logging.error("ClusterManagwer--synco from DB fail")

    @staticmethod
    def sync_to_database():
        cluster_list = ResourceManager._cluster_dict
        ResourceManager._db.sync_to_db(cluster_list)


if __name__ == "__main__":
    cluster_name = 'test'
    ResourceManager.init()
    b = Cluster(cluster_name)
    ResourceManager._cluster_dict[cluster_name] = b 
    print(ResourceManager._cluster_dict)
