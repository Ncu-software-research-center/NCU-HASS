#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import logging
import subprocess

from RESTClient import RESTClient
from HAInstance import HAInstance


class HAInstanceManager(object):
    _instance = None

    def __init__(self):
        pass

    @staticmethod
    def get_instance(instance_name):
        return_value = HAInstanceManager._instance.instance_list.get(
            instance_name, None)

        if return_value is None:
            logging.warning(
                "HAInstanceManager - Instance is not on protected list {}".format(instance_name))
        return return_value

    @staticmethod
    def get_instance_list():
        if not HAInstanceManager._instance:
            logging.error("HAInstanceManager - Object not created")

        return HAInstanceManager._instance.instance_list

    @staticmethod
    def update_ha_instance():
        logging.info("HAInstanceManager - update HA Instance")
        HAInstanceManager._instance = _HAInstanceManager_subClass()


class _HAInstanceManager_subClass(object):
    server = None
    instance_list = None
    ha_instance_list = None
    host = subprocess.check_output(['hostname']).strip()

    def __init__(self):
        self._init()
        self._get_instance_from_controller()
        message = "HAInstanceManager - update ha instance finish"
        logging.info(message)

    def _add_instance(self, cluster_name, ha_instance):
        new_instance = HAInstance(
            cluster_name=cluster_name, ha_instance=ha_instance)
        self.instance_list[ha_instance['name']] = new_instance

    def _get_ha_instance(self, cluster_name):
        instance_list = []
        try:
            instance_list = self.server.list_instance(
                cluster_name)["data"]["instanceList"]
        except Exception as e:
            message = "HAInstanceManager - fail to get ha instance: ", str(e)
            logging.error(message)
        finally:
            return instance_list

    def _get_instance_by_node(self, instance_lists):
        for name, instance_list in instance_lists.iteritems():
            for instance in instance_list[:]:
                if self.host not in instance["host"]:
                    instance_list.remove(instance)
        return instance_lists

    def _get_instance_from_controller(self):
        try:
            cluster_list = self.server.list_cluster()["data"]
            for cluster in cluster_list:
                cluster_name = cluster["cluster_name"]
                self.ha_instance_list[cluster_name] = self._get_ha_instance(
                    cluster_name)

            host_instance = self._get_instance_by_node(self.ha_instance_list)
            for cluster_name, instance_list in host_instance.iteritems():
                for instance in instance_list:
                    self._add_instance(cluster_name, instance)

        except Exception as e:
            message = "HAInstanceManager - failed to initialize token to access compute node: ", str(
                e)
            logging.error(message)

    def _init(self):
        self.instance_list = {}
        self.ha_instance_list = {}
        self.server = RESTClient.get_instance()
