#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import ConfigParser
import threading
import logging
import time
import os
import Queue
import libvirt
import subprocess
import sys

import FailureType
import InstanceState
from InstanceEvent import InstanceEvent
import InstanceQueueConfig
import LibvirtCallbackConfig

class InstanceDetector():
    def __init__(self, node_name, queue):
        self.__node_name = node_name
        # get the logger of this node thread
        self.__logger = logging.getLogger('{}'.format(self.__node_name))

        self.__instance_dictionary = dict()
        # index of the instance information list stored in the instance dictionary
        self.__INSTANCE_POWER_FAILURE_INDEX = 0
        self.__INSTANCE_OS_FAILURE_INDEX = 1
        self.__INSTANCE_STATE_INDEX = 2
        self.__INSTANCE_NETWORK_PROVIDER_INDEX = 3
        self.__INSTANCE_ID_INDEX = 4
        
        self.__libvirt_connection = None
        self.__libvirt_detection_thread = None
        self.__libvirt_callback_register_list = []
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.libvirt_uri = self.config.get("libvirt", "libvirt_uri").format(n_name = self.__node_name)
        self.__instance_dict_update_queue = queue
        self.__lock = threading.Lock()

    def __check_instance_state(self, connect, domain, event, detail, opaque):
        #print("instance state: "+ str(domain.name()) + " , " + str(event) + " , " + str(detail))
        state_type = InstanceEvent.Event_type(event, detail)
        #print("instance state, state type: "+ str(state_type))
        #self.__logger.error("InstanceDetector - instance state callback - event type: {event_type}".format(event_type = state_type))
        self.__check_instance_update()

        #print("state_type not in migrated: "+str(state_type not in InstanceEvent.EVENT_MIGRATED))
        if state_type not in InstanceEvent.EVENT_MIGRATED:
            failed_instance = self.__instance_dictionary.get(domain.name())
            # DEBUG
            # self.__logger.error("{} {} {}".format(state_type, InstanceEvent.Event_String(event, detail), domain.name()))
            if failed_instance is None:
                self.__logger.warning(
                    "node ({}) - InstanceDetector - Unprotected instance failed, do nothing {}".format(self.__node_name, domain.name()))
                return

            instance_previous_state = failed_instance[self.__INSTANCE_STATE_INDEX]

            if state_type is InstanceEvent.EVENT_FAILED:
                self.__logger.info(
                "InstanceDetector, __check_instance_state - Protected instance ({}) failed: {}".format(domain.name(), str(self.__instance_dictionary.get(domain.name()))))

                failed_instance[self.__INSTANCE_OS_FAILURE_INDEX] = True
                failed_instance[self.__INSTANCE_POWER_FAILURE_INDEX] = True

            elif state_type is InstanceEvent.EVENT_DESTROYED:
                if instance_previous_state in (FailureType.INSTANCE_NETWORK_FAIL, FailureType.INSTANCE_OS_FAIL, FailureType.INSTANCE_POWER_FAIL):
                    return
                else:
                    self.__logger.info("node ({}): InstanceDetector, __check_instance_state - ({}) {} is to be ignored".format(self.__node_name, InstanceEvent.Event_String(event, detail), domain.name()))
                    failed_instance[self.__INSTANCE_STATE_INDEX] = InstanceState.VM_DESTROYED

            elif state_type is InstanceEvent.EVENT_SHUTOFF:
                failed_instance[self.__INSTANCE_STATE_INDEX] = InstanceState.VM_SHUTOFF
                self.__logger.info("node ({}); InstanceDetector, __check_instance_state - vm ({}) state is  {}".format(self.__node_name, domain.name(), str(self.__instance_dictionary.get(domain.name())[self.__INSTANCE_STATE_INDEX])))
            elif state_type is InstanceEvent.EVENT_STARTED:
                if instance_previous_state in (FailureType.INSTANCE_NETWORK_FAIL, FailureType.INSTANCE_OS_FAIL, FailureType.INSTANCE_POWER_FAIL):
                    # self.__logger.info(failed_instance.get_instance_status())
                    return
                else:
                    failed_instance[self.__INSTANCE_STATE_INDEX] = InstanceState.VM_STARTED
                    self.__logger.info("node ({}): InstanceDetector, __check_instance_state - vm ({}) state is  {}".format(self.__node_name, domain.name(), str(self.__instance_dictionary.get(domain.name())[self.__INSTANCE_STATE_INDEX])))

            elif state_type is InstanceEvent.EVENT_MIGRATING:
                # self.__logger.info("InstanceDetectionThread - ({}) {} is migrating ...".format(InstanceEvent.Event_String(event, detail), domain.name()))
                failed_instance[self.__INSTANCE_STATE_INDEX] = InstanceState.VM_MIGRATING
                self.__logger.info("node ({}); InstanceDetector, __check_instance_state - vm ({}) state is  {}".format(self.__node_name, domain.name(), str(self.__instance_dictionary.get(domain.name())[self.__INSTANCE_STATE_INDEX])))


    def set_instance_state(self, instance_name, state):
        if self.__instance_dictionary.get(instance_name) != None:
            self.__instance_dictionary[instance_name][self.__INSTANCE_STATE_INDEX] = state

    # return True/False; True means the instance is recoverable, False means the instance should not be recovered
    def check_instance_state_for_recovery(self, instance_name):
        self.__check_instance_update()
        if self.__instance_dictionary.get(instance_name) != None:
            instance_state = self.__instance_dictionary[instance_name][self.__INSTANCE_STATE_INDEX]
            # check instance state
            if instance_state not in (InstanceState.VM_SHUTOFF, InstanceState.VM_DESTROYED, InstanceState.VM_MIGRATING):
                return True
        return False

    def __check_instance_watchdog(self, connect, domain, action, opaque):
        print("instance watchdog: "+ str(domain.name()) + " , " + str(action))
        self.__check_instance_update()
        if action in InstanceEvent.Event_watchdog_action:
            failed_instance = self.__instance_dictionary.get(domain.name())
            if failed_instance is None:
                self.__logger.warning(
                    "InstanceDetector, __check_instance_watchdog - Unprotected instance failed, do nothing {}".format(domain.name()))
                return

            failed_instance[self.__INSTANCE_OS_FAILURE_INDEX] = True
            self.__logger.info(
                "InstanceDetector, __check_instance_watchdog - Protected instance ({}) failed: {}".format(domain.name(), str(self.__instance_dictionary.get(domain.name()))))

    def __check_libvirt_connection(self):
        try:
            if self.__libvirt_connection.isAlive() == 1:
                return True
            else:
                return False
        except Exception as e:
            self.__libvirt_connection.close()
            message = "InstanceDetector - fail to check libvirt connection : ", str(e)
            self.__logger.error(message)
            return False

    def register_instance_state_callback(self):
        try:
            # check whether the detection thread used for libvirt callback is created
            if self.__libvirt_detection_thread is None:
                self.__libvirt_detection_thread = self.__create_libvirt_detection_thread()

            # check whether the libvirt connection exists
            if self.__libvirt_connection is None:
                self.__libvirt_connection = self.__create_libvirt_connection()

            # check whether the libvirt connection is disconnected
            is_connected = self.__check_libvirt_connection()
            if not is_connected:
                del self.__libvirt_callback_register_list[:]
                self.__libvirt_connection = self.__create_libvirt_connection()

            # check whether the instance state callback is registered
            if LibvirtCallbackConfig.INSTANCE_STATE not in self.__libvirt_callback_register_list:
                self.__libvirt_connection.domainEventRegister(self.__check_instance_state, None)
                self.__libvirt_connection.setKeepAlive(5, 3)
                self.__libvirt_callback_register_list.append(LibvirtCallbackConfig.INSTANCE_STATE)
            return True
        except Exception as e:
            message = "InstanceDetector - fail to register instance state callback: " +  str(e)
            self.__logger.error(message)
            return FailureType.DETECTOR_FAILED

    def register_instance_watchdog_callback(self):
        try:
            # check whether the detection thread used for libvirt callback is created
            if self.__libvirt_detection_thread is None:
                self.__libvirt_detection_thread = self.__create_libvirt_detection_thread()

            # check whether the libvirt connection exists
            if self.__libvirt_connection is None:
                self.__libvirt_connection = self.__create_libvirt_connection()

            # check whether the libvirt connection is disconnected
            is_connected = self.__check_libvirt_connection()
            if not is_connected:
                del self.__libvirt_callback_register_list[:]
                self.__libvirt_connection = self.__create_libvirt_connection()

            # check whether the instance watchdog callback is registered
            if LibvirtCallbackConfig.INSTANCE_WATCHDOG not in self.__libvirt_callback_register_list:
                self.__libvirt_connection.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG, self.__check_instance_watchdog, None)
                self.__libvirt_connection.setKeepAlive(5, 3)
                self.__libvirt_callback_register_list.append(LibvirtCallbackConfig.INSTANCE_WATCHDOG)
            return True
        except Exception as e:
            message = "InstanceDetector - fail to register instance watchdog callback: ", str(e)
            self.__logger.error(message)
            return FailureType.DETECTOR_FAILED

    def __create_libvirt_connection(self):
        libvirt_conn = libvirt.open(self.libvirt_uri)
        if libvirt_conn is None:
            message = "InstanceDetector - fail to open libvirt connection to {lib_uri}".format(lib_uri = self.libvirt_uri)
            self.__logger.error(message)
            raise Exception
        else:
            return libvirt_conn

    def __virEventLoopNativeRun(self):
        while True:
            libvirt.virEventRunDefaultImpl()    

    def __create_libvirt_detection_thread(self):
        libvirt.virEventRegisterDefaultImpl()
        event_loop_thread = threading.Thread(target=self.__virEventLoopNativeRun, name="libvirtEventLoop")
        event_loop_thread.setDaemon(True)
        event_loop_thread.start()
        return event_loop_thread

    def __check_instance_update(self):
        # get lock to wirte __instance_dictionary
        self.__lock.acquire()
        try:
            # If the update queue is empty, it means no update
            if self.__instance_dict_update_queue.empty():
                result = True
            # update the instance dictionary
            # get update information from the update queue
            loop_range = self.__instance_dict_update_queue.qsize()
            for _ in range(loop_range):
                # item: [action_number, instance_name, instance_network_provider_list, instance_id]
                item = self.__instance_dict_update_queue.get()
                self.__logger.warning("node({}): InstanceDetector, check_instance_update - item: {}".format(self.__node_name, str(item)))
                action = item[InstanceQueueConfig.ACTION_INDEX]
                instance_name = item[InstanceQueueConfig.INSTANCE_NAME_INDEX]
                instance_id = item[InstanceQueueConfig.INSTANCE_ID_INDEX]
                # add instance to the instance dictionary or 
                # add evacuating instance to the instance dictionary
                if action == InstanceQueueConfig.ADD_INSTANCE or action == InstanceQueueConfig.EVACUATE_INSTANCE:
                    instance_dict_element = [None]*5
                    # -- setup values of instance dictionary element
                    instance_dict_element[self.__INSTANCE_POWER_FAILURE_INDEX] = False
                    instance_dict_element[self.__INSTANCE_OS_FAILURE_INDEX] = False
                    if action == InstanceQueueConfig.ADD_INSTANCE:
                        instance_dict_element[self.__INSTANCE_STATE_INDEX] = InstanceState.VM_HEALTHY
                    else:
                        instance_dict_element[self.__INSTANCE_STATE_INDEX] = InstanceState.VM_EVACUATING
                    network_provider_list = []
                    network_provider_list.extend(item[InstanceQueueConfig.NETWORK_PROVIDER_INDEX])
                    instance_dict_element[self.__INSTANCE_NETWORK_PROVIDER_INDEX] = network_provider_list
                    instance_dict_element[self.__INSTANCE_ID_INDEX] = instance_id
                    # -- add instance dictionary element into instance dictionary
                    self.__instance_dictionary[instance_name] = instance_dict_element
                # delete instance from the instance dictionary
                elif action == InstanceQueueConfig.REMOVE_INSTANCE:
                    if self.__instance_dictionary.get(instance_name) != None:
                        del self.__instance_dictionary[instance_name]
            result = True
        except Exception as e:
            self.__logger.warning("node({}): InstanceDetector (check_instance_update) - exception: {}".format(self.__node_name, str(e)))
            result = False
        # release lock
        self.__lock.release()
        return result

    def revert_to_default(self, instance_name):
        # instance_inform: [power_failure, os_failure, instance_state, network_provider_list]
        instance_inform = self.__instance_dictionary.get(instance_name)
        if instance_inform != None:
            self.__instance_dictionary[instance_name][self.__INSTANCE_POWER_FAILURE_INDEX] = False
            self.__instance_dictionary[instance_name][self.__INSTANCE_OS_FAILURE_INDEX] = False
            self.__instance_dictionary[instance_name][self.__INSTANCE_STATE_INDEX] = InstanceState.VM_HEALTHY
    
    def get_instance_id(self, instance_name):
        if self.__instance_dictionary.get(instance_name) != None:
            return self.__instance_dictionary[instance_name][self.__INSTANCE_ID_INDEX]
        else:
            return None

    def get_instance_state(self, instance_name):
        try:
            return self.__instance_dictionary[instance_name][self.__INSTANCE_STATE_INDEX]
        except:
            return None

    def __ping_instance(self, ip):
        time_out = self.config.getint("detection", "instance_ping_timeout")
        ping_timeout = 1
        while time_out > 0:
            try:
                # FIXME move the cmd to configuration file
                response = subprocess.check_output(['timeout', str(ping_timeout), 'ping', '-c', '1', ip], stderr=subprocess.STDOUT, universal_newlines=True)
                return True
            except subprocess.CalledProcessError as ce:
                self.__logger.warning("node ({}): InstanceDetector, ping_instance - exception, time_out: {}".format(self.__node_name, str(time_out)))
                time_out -= ping_timeout
                if time_out <= 0:
                    break
        return False

    def check_instance_network_failure(self, instance_name):
        result = FailureType.HEALTH
        # update instance list
        self.__check_instance_update()
        # check whether the target instance is under HA protection
        if self.__instance_dictionary.get(instance_name) == None:
            return FailureType.INSTANCE_NOT_PROTECTED

        # get instance state
        instance_state = self.get_instance_state(instance_name)
        # check instance state. (This is the first VM operation check)
        if instance_state in (InstanceState.VM_SHUTOFF, InstanceState.VM_DESTROYED, InstanceState.VM_MIGRATING):
            return result

        # get instance network provider ip
        ip = self.__instance_dictionary[instance_name][self.__INSTANCE_NETWORK_PROVIDER_INDEX][0]
        if ip is None:
            return None
        ping_result = self.__ping_instance(ip)
        network_failure = not(ping_result)
        # get instance state for second check. (This is the second VM operation check)
        instance_state = self.get_instance_state(instance_name)
        # Instance network fault occurs only when the instance is healthy and does not respond to pings
        if network_failure == True and instance_state is InstanceState.VM_HEALTHY:
            self.__logger.error("node ({}): InstanceDetector - Failed to ping {} at {}; lock state: {}".format(self.__node_name, instance_name, ip, self.__lock.locked()))
            result = FailureType.INSTANCE_NETWORK_FAIL
        elif network_failure == False and instance_state is not InstanceState.VM_HEALTHY:
            self.revert_to_default(instance_name)
        return result

    def check_instance_os_failure(self, instance_name):
        is_libvirt_connected = self.__check_libvirt_connection()
        if is_libvirt_connected == False:
            return FailureType.DETECTOR_FAILED
        if self.__instance_dictionary.get(instance_name) == None:
            return FailureType.INSTANCE_NOT_PROTECTED

        # because vm watchdog callback needs about 4 seconds to respond if vm restart before, we set a time out to check it.
        time_out = self.config.getint("detection", "instance_os_check_timeout")
        while time_out > 0:
            os_failure = self.__instance_dictionary[instance_name][self.__INSTANCE_OS_FAILURE_INDEX]
            if os_failure:
                return FailureType.INSTANCE_OS_FAIL

            time.sleep(0.5)
            time_out -= 0.5

        return FailureType.HEALTH

    def check_instance_power_failure(self, instance_name):
        is_libvirt_connected = self.__check_libvirt_connection()
        if is_libvirt_connected == False:
            return FailureType.DETECTOR_FAILED
        if self.__instance_dictionary.get(instance_name) == None:
            return FailureType.INSTANCE_NOT_PROTECTED
        power_failure = self.__instance_dictionary[instance_name][self.__INSTANCE_POWER_FAILURE_INDEX]
        if power_failure:
            return FailureType.INSTANCE_POWER_FAIL
        return FailureType.HEALTH

    def get_instance_name_list(self):
        self.__check_instance_update()
        return self.__instance_dictionary.keys()

    def check_instance_network_detector(self):
        heartbeat_time = int(self.config.get("default","heartbeat_time"))
        while heartbeat_time > 0:
            try:
                response = subprocess.check_output(['timeout', '1', 'ping', '-c', '1', self.__node_name], stderr=subprocess.STDOUT, universal_newlines=True)
                return FailureType.HEALTH
            except Exception as e:
                heartbeat_time -= 1
        return FailureType.NETWORK_FAIL


    # log instance information for debug
    def log_instance_info(self, instance_name):
        self.__logger.info("--debug-- node({}): InstanceDetector, log_instance_info - instance ({}) info: {}".format(self.__node_name, instance_name, str(self.__instance_dictionary.get(instance_name))))

if __name__ == "__main__":
    config = ConfigParser.RawConfigParser()
    config.read('hass.conf')
    host_name = "compute2"

    log_level = logging.getLevelName(config.get("log", "level"))
    log_file_name = "hass.log"
    dir = os.path.dirname(log_file_name)
    if os.path.exists(dir) == None:
        os.makedirs(dir)
    logging.basicConfig(filename=log_file_name, level=log_level, format="%(asctime)s [%(levelname)s] : %(message)s")
    logging.info("-- Preparing InstanceDetector --")

    q = Queue.Queue()
    idr = InstanceDetector(host_name, q)

    res = idr.register_instance_state_callback()
    print("r state call: " + str(res))
    if res != True:
        print("instance state callback register fail")
    res = idr.register_instance_watchdog_callback()
    print("r watchdog call: " + str(res))
    if res != True:
        print("instance watchdog callback register fail")

    ins_name = "instance-00000015"
    ins1 = [InstanceQueueConfig.ADD_INSTANCE, ins_name, "192.168.4.210"]
    q.put(ins1)
    while True:
        result = idr.check_instance_network_failure(ins_name)
        print("net: " + str(result))

        result = idr.check_instance_os_failure(ins_name)
        print("os: " + str(result))
        
        result = idr.check_instance_power_failure(ins_name)
        print("pow: " + str(result))

        time.sleep(2)
