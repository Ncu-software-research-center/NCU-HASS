#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   This is a class maintains Openstack-Nova command operation
##############################################################

from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient import client
import ConfigParser
import time
import logging


class NovaClient(object):
    _instance = None  # class reference
    _helper = None  # novaclient reference

    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.openstack_version = self.config.get("version", "openstack_version")
        if NovaClient._instance != None:
            raise Exception("This class is a singleton! , cannot initialize twice")
        else:
            self._initialize_helper()
            NovaClient._instance = self

    @staticmethod
    def get_instance():
        if not NovaClient._instance:
            NovaClient()
        if not NovaClient._helper:
            NovaClient._instance._initialize_helper()
        return NovaClient._instance

    def _initialize_helper(self):
        auth = v3.Password(auth_url='http://%s:%s/v3' % (self.config.get("keystone_auth","url"), self.config.get("keystone_auth","port")),
                           username=self.config.get("openstack", "openstack_admin_account"),
                           password=self.config.get("openstack", "openstack_admin_password"),
                           project_name=self.config.get("openstack", "openstack_project_name"),
                           user_domain_name=self.config.get("openstack", "openstack_user_domain_id"),
                           project_domain_name=self.config.get("openstack", "openstack_project_domain_id"))
        sess = session.Session(auth=auth)
        if self.openstack_version == "mitaka":
            novaClient = client.Client(2.25, session=sess)
        else:
            novaClient = client.Client(2.29, session=sess)
        NovaClient._helper = novaClient

    def get_compute_pool(self):
        compute_pool = []
        hypervisorList = self._get_host_list()
        for hypervisor in hypervisorList:
            if hypervisor.state == 'up':
                compute_pool.append(str(hypervisor.hypervisor_hostname))
        return compute_pool

    def _get_image(self, id):
        vm = self._get_vm(id)
        return getattr(vm, "image")

    def _get_host_list(self):
        return NovaClient._helper.hypervisors.list()

    def _get_vm(self, instance_id):
        return NovaClient._helper.servers.get(instance_id)

    def _get_volumes(self, id):
        return NovaClient._helper.volumes.get_server_volumes(id)
        
    def get_instance_list_by_node(self, node_name):
        ret = []
        instance_list = self.get_all_instance_list()
        for instance in instance_list:
            name = getattr(instance, "OS-EXT-SRV-ATTR:hypervisor_hostname")
            if name == node_name:
                ret.append(instance)
        return ret

    def get_instance_state(self, instance_id):
        instance = self._get_vm(instance_id)
        return getattr(instance, "status")

    def get_all_instance_list(self):
        return NovaClient._helper.servers.list(search_opts={'all_tenants': 1})

    def get_instance_name(self, instance_id):
        instance = self._get_vm(instance_id)
        return getattr(instance, "OS-EXT-SRV-ATTR:instance_name")

    def get_instance_host(self, instance_id):
        status = None
        check_timeout = 120
        while status != "ACTIVE" and check_timeout > 0:
            instance = self._get_vm(instance_id)
            status = self.get_instance_state(instance_id)
            if status == "SHUTOFF": 
                break
            print "get_instance_host in nova-client : %s , %s" % (status, getattr(instance, "name"))
            check_timeout -= 1
            time.sleep(1)
        if status != "ACTIVE" and status != "SHUTOFF":
            logging.error("NovaClient get_instance_host fail,time out and state is not ACTIVE or SHUTOFF")
            print "NovaClient get_instance_host fail,time out and state is not ACTIVE or SHUTOFF"
        return getattr(self._get_vm(instance_id), "OS-EXT-SRV-ATTR:host")

    def get_instance_network(self, instance_id):
        instance = self._get_vm(instance_id)
        network = getattr(instance, "networks")
        return network

    def is_instance_power_on(self, instance_id):
        vm = self._get_vm(instance_id)
        power_state = getattr(vm, "OS-EXT-STS:power_state")
        if power_state != 1:
            return False
        return True


    def is_instance_boot_from_volume(self, instance_id):
        volume = self._get_volumes(instance_id)
        image = self._get_image(instance_id)
        if volume == [] or image != '':
            return False
        return True

    
    def _nova_service_up(self, node):
        return NovaClient._helper.services.force_down(node.name, "nova-compute", False)

    def _nova_service_down(self, node):
        return NovaClient._helper.services.force_down(node.name, "nova-compute", True)

    def live_migrate_vm(self, instance_id, target_node_name):
        instance = self._get_vm(instance_id)
        instance._live_migrate(host=target_node_name)
        return self.get_instance_host(instance_id)

    def evacuate(self, instance, target_node, fail_node):
        self._nova_service_down(fail_node)
        openstack_instance = self._get_vm(instance.id)
        if self.openstack_version == "mitaka":
            NovaClient._helper.servers.evacuate(openstack_instance, target_node.name)
        else:
            NovaClient._helper.servers.evacuate(openstack_instance, target_node.name, force=True)
        self._nova_service_up(fail_node)

    def get_instance_external_network(self, instance_ip):
        external_ip = self.config.get("openstack", "openstack_external_network_gateway_ip").split(".")
        external_ip = external_ip[0:-1]
        check_ip = instance_ip.split(".")
        if all(x in check_ip for x in external_ip):
            return instance_ip
        return None    

    def hard_reboot_instance(self, instance_id):
        try:
            instance = self._get_vm(instance_id)
            NovaClient._helper.servers.reboot(instance, reboot_type='HARD')
            instance_name = self.get_instance_name(instance_id)
            message = "NovaClient - Rebooting instance (%s) ..." % (instance_name)
            logging.info(message)
        except Exception as e:
            message = "NovaClient - failed to hard reboot instance: ", str(e)
            logging.error(message)

if __name__ == "__main__":
    a = NovaClient.get_instance()
    x = a.get_instance_host('b32ba9d4-ebe8-4414-bec2-62674f1796ad')
    print(x)
