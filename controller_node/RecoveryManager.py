#########################################################
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
                                 FailureType.HARDWARE_FAIL: self._recover_hardware_fault,
                                 FailureType.POWER_FAIL: self._recover_power_off,
                                 FailureType.OS_FAIL: self._recover_os_hanged,
                                 FailureType.INSTANCE_POWER_FAIL: self._recover_instance_crash,
                                 FailureType.INSTANCE_OS_FAIL: self._recover_instance_os_hanged,
                                 FailureType.INSTANCE_NETWORK_FAIL: self._recover_instance_network_isolation}

    def recover(self, fail_type, cluster_name, failed_target_name):
        return self.recover_function[fail_type](cluster_name, failed_target_name)

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

    def _recover_hardware_fault(self, cluster_name, fail_node_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            logging.error("RecoverManager : cluster not found")
            return
        fail_node = cluster.get_node_by_name(fail_node_name)
        logging.info("RecoverManager : start to recover the hardware fault of node %s" % (fail_node))
        self._recover_vm(cluster, fail_node)
        return self._recover_node_by_reboot(fail_node)

    def _recover_network_isolation(self, cluster_name, fail_node_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            logging.error("RecoverManager : cluster not found")
            return
        fail_node = cluster.get_node_by_name(fail_node_name)
        logging.info("RecoverManager : start to recover the network isolation of node %s" % (fail_node))
        self._recover_vm(cluster, fail_node)
        return self._recover_node_by_reboot(fail_node)

    # output: True/False, None. True means success, False means fail, None means that it cannot find something, such as a cluster or instance.
    def _recover_instance_crash(self, cluster_name, failed_instance_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            logging.warning("RecoverManager, _recover_instance_crash: cluster not found")
            return
        failed_instance = cluster.get_protected_instance_by_instance_name(failed_instance_name)
        if failed_instance == None:
            logging.warning("RecoverManager, _recover_instance_crash: failed instance not found")
            return
        logging.info("RecoverManager : start to recover the instance crash of instance %s" % (failed_instance_name))
        result = failed_instance.recover_instance_crash()
        return result

    # output: True/False, None. True means success, False means fail, None means that it cannot find something, such as a cluster or instance.
    def _recover_instance_os_hanged(self, cluster_name, failed_instance_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            logging.warning("RecoverManager, _recover_instance_os_hanged: cluster not found")
            return
        failed_instance = cluster.get_protected_instance_by_instance_name(failed_instance_name)
        if failed_instance == None:
            logging.warning("RecoverManager, _recover_instance_os_hanged: failed instance not found")
            return
        logging.info("RecoverManager : start to recover the os hanged of instance %s" % (failed_instance_name))
        result = failed_instance.recover_instance_os_hanged()
        return result

    # output: True/False, None. True means success, False means fail, None means that it cannot find something, such as a cluster or instance.
    def _recover_instance_network_isolation(self, cluster_name, failed_instance_name):
        cluster = ResourceManager.get_cluster(cluster_name)
        if not cluster:
            logging.warning("RecoverManager, _recover_instance_network_isolation: cluster not found")
            return
        failed_instance = cluster.get_protected_instance_by_instance_name(failed_instance_name)
        if failed_instance == None:
            logging.warning("RecoverManager, _recover_instance_network_isolation: failed instance not found")
            return
        logging.info("RecoverManager : start to recover the network isolation of instance %s" % (failed_instance_name))
        result = failed_instance.recover_instance_network_isolation()
        return result

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
        # update information of instances that are evacuated
        for instance in protected_instance_list:
            cluster.update_instance_host(instance.get_id(), True)

    def _recover_node_by_reboot(self, fail_node):
        print "start recover node by reboot"
        logging.info("start recover node by reboot")
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
        logging.info("start recover node by start")
        result = fail_node.start()
        print "boot node result : %s" % result.message
        message = "RecoveryManager, _recover_node_by_start - "
        if result.code == "succeed":
            logging.info(message + result.message)
            boot_up = self._check_node_boot_success(fail_node)
            if boot_up:
                print "Node %s recovery finished." % fail_node.name
                logging.info("RecoveryManager, _recover_node_by_start - node %s recovery (start node) successed." % fail_node.name)
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
