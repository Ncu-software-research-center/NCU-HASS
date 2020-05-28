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
#   This is a class maintains recovery methods.
##########################################################

from ResourceManager import ResourceManager
from Detector import Detector
import FailureType
import logging
import ConfigParser
import time
import subprocess


class RecoveryManager(object):
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.recover_function = {FailureType.NETWORK_FAIL: self._recover_network_isolation,
                                 FailureType.POWER_FAIL: self._recover_power_off,
                                 FailureType.OS_FAIL: self._recover_os_hanged}

    def recover(self, fail_type, cluster_name, fail_node_name):
        return self.recover_function[fail_type](cluster_name, fail_node_name)

    def _recover_os_hanged(self, cluster_name, fail_node_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            logging.error("RecoverManager : cluster not found")
            return
        fail_node = cluster.get_node_by_name(fail_node_name)
        print "fail node is %s, OS fail" % fail_node.name
        logging.info("fail node is %s, OS fail" ,fail_node.name)
        print "start recovery vm"
        self._recover_vm(cluster, fail_node)
        print "end recovery vm"
        return self._recover_node_by_reboot(fail_node)

    def _recover_power_off(self, cluster_name, fail_node_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            logging.error("RecoverManager : cluster not found")
            return
        fail_node = cluster.get_node_by_name(fail_node_name)
        print "fail node is %s, power fail" % fail_node.name
        print "start recovery vm"
        self._recover_vm(cluster, fail_node)
        print "end recovery vm"
        return self._recover_node_by_start(fail_node)

    def _recover_network_isolation(self, cluster_name, fail_node_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            logging.error("RecoverManager : cluster not found")
            return
        fail_node = cluster.get_node_by_name(fail_node_name)

        network_transient_time = int(self.config.get("default", "network_transient_time"))
        second_chance = FailureType.HEALTH
        detector = Detector(fail_node)
        while network_transient_time > 0:
            try:
                status = detector.check_network_status()
                if status == FailureType.HEALTH:
                    second_chance = FailureType.HEALTH
                    break
                else :
                    print "network unreachable for %s" % fail_node_name
                    network_transient_time -= 1
                    second_chance = FailureType.NETWORK_FAIL

            except subprocess.CalledProcessError:
                print "network unreachable for %s" % fail_node_name
                network_transient_time -= 1
                time.sleep(1)
                second_chance = FailureType.NETWORK_FAIL
        if second_chance == FailureType.HEALTH:
            print "The network status of %s return to health" % fail_node.name
            return True
        else:
            print "network still unreachable, start recovery."
            print "fail node is %s, network fail" % fail_node.name
            logging.info("fail node is %s, network fail", fail_node.name)
            print "start recovery vm"
            self._recover_vm(cluster, fail_node)
            print "end recovery vm"
            return self._recover_node_by_reboot(fail_node)

    def _recover_vm(self, cluster, fail_node):
        if len(cluster.get_node_list()) < 2:
            logging.error("RecoverManager : evacuate fail, cluster only one node")
            return
        if not fail_node:
            logging.error("RecoverManager : not found the fail node")
            return
        target_host = cluster.find_target_host(fail_node)
        print "target_host : %s" % target_host.name
        if not target_host:
            logging.error("RecoverManager : not found the target_host %s" % target_host)
            return
        protected_instance_list = cluster.get_protected_instance_list_by_node(fail_node)
        print "protected list : %s" % protected_instance_list
        for instance in protected_instance_list:
            try:
                if target_host.instance_overlapping_in_libvirt(instance):
                    logging.info("instance %s overlapping in %s" % (instance.name, target_host.name))
                    logging.info("start undefine instance in %s" % target_host.name)
                    print "instance %s overlapping in %s" % (instance.name, target_host.name)
                    print "start undefine instance in %s" % target_host.name
                    target_host.undefine_instance(instance)
                    print "end undefine instance"
            except Exception as e:
                logging.error("instance overlapping in libvirt exception")
                logging.error(str(e))
                logging.info("undefineInstance second chance via socket")
                try:
                    target_host.undefine_instance_via_socket(instance)
                except Exception as e:
                    logging.error("undefine instance sencond chance fail %s" % str(e))
                    pass
            try:
                print "start evacuate"
                logging.info("start evacuate")
                cluster.evacuate(instance, target_host, fail_node)
            except Exception as e:
                print str(e)
                logging.error(str(e))
                logging.error("RecoverManager - The instance %s evacuate failed" % instance.id)

        # print "check instance status"
        # status = self.checkInstanceNetworkStatus(fail_node, cluster)
        # if status == False:
        #     logging.error("RecoverManager : check vm status false")

        print "update instance"
        logging.info("update instance")
        cluster.update_instance()

    def _recover_node_by_reboot(self, fail_node):
        print "start recover node by reboot"
        result = fail_node.reboot()
        print "boot node result : %s" % result.message
        message = "RecoveryManager recover "
        if result.code == "succeed":
            logging.info(message + result.message)
            boot_up = self._check_node_boot_success(fail_node)
            if boot_up:
                print "Node %s recovery finished." % fail_node.name
                logging.info("Node %s recovery finished." % fail_node.name)
                return True
            else:
                logging.error(message + "Can not reboot node %s successfully", fail_node.name)
                return False
        else:
            logging.error(message + result.message)
            return False

    def _recover_node_by_start(self, fail_node):
        print "start recover node by start"
        result = fail_node.start()
        print "boot node result : %s" % result.message
        message = "RecoveryManager recover"
        if result.code == "succeed":
            logging.info(message + result.message)
            boot_up = self._check_node_boot_success(fail_node)
            if boot_up:
                print "Node %s recovery finished." % fail_node.name
                logging.info("Node %s recovery finished." % fail_node.name)
                return True
            else:
                logging.error(message + "Can not start node %s successfully", fail_node.name)
                return False
        else:
            logging.error(message + result.message)
            return False

    def _check_node_boot_success(self, node):
        time_to_wait = int(self.config.get("detection", "time_to_wait"))
        check_timeout = int(self.config.get("detection", "check_timeout"))
        detector = Detector(node)
        print "waiting node to boot"
        time.sleep(time_to_wait)
        print "start check node boot status"
        while check_timeout > 0:
            try:
                if detector.check_network_status() == FailureType.HEALTH:
                    return True
            except Exception as e:
                print str(e)
            finally:
                time.sleep(1)
                check_timeout -= 1
        return False


if __name__ == "__main__":
    pass
    # r = RecoveryManager()
    # l = r.remote_exec("compute3","virsh list --all")
