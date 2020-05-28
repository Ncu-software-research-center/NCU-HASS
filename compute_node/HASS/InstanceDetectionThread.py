#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import config
import libvirt
import logging
import sys
import threading
import time

from InstanceEvent import InstanceEvent
from HAInstance import HAInstance
from HAInstanceManager import HAInstanceManager
from NovaClient import NovaClient


class InstanceDetectionThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._novaclient = NovaClient.get_instance()
        self._detection_delay = config.getint(
            "detection", "detection_delay", default='2')
        self.libvirt_uri = config.get("libvirt", "libvirt_uri")
        HAInstanceManager.update_ha_instance()

    def run(self):
        logging.info(
            "InstanceDetectionThread - Started, check every {}s".format(self._detection_delay))
        try:
            while True:
                self._create_libvirt_detection_thread()
                libvirt_connection = self._get_libvirt_connection()

                # register callback self._check_vm_state
                libvirt_connection.domainEventRegister(
                    self._check_instance_state, None)

                # register callback self._check_vm_watchdog
                libvirt_connection.domainEventRegisterAny(
                    None, libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG, self._check_instance_watchdog, None)

                libvirt_connection.setKeepAlive(5, 3)

                while True:
                    if not self._check_libvirt_connection(libvirt_connection):
                        libvirt_connection.close()
                        break

                    instance_list = HAInstanceManager.get_instance_list()
                    self._detect_and_recover_instance(
                        instance_list, libvirt_connection)

                    time.sleep(self._detection_delay)

        except Exception as e:
            message = "InstanceDetectionThread - failed to run detection method : ", str(e)
            logging.error(message)
            sys.exit(1)

    def _check_instance_state(self, connect, domain, event, detail, opaque):
        state_type = InstanceEvent.Event_type(event, detail)

        if state_type is InstanceEvent.EVENT_FAILED:
            failed_instance = HAInstanceManager.get_instance(domain.name())

            logging.error("InstanceDetectionThread - DomainCallback {} {} {}".format(state_type, InstanceEvent.Event_String(event, detail), domain.name()))

            if failed_instance is None:
                logging.warning(
                    "InstanceDetectionThread - Unprotected instance failed, do nothing {}".format(domain.name()))
                return

            logging.error(
                "InstanceDetectionThread - Protected instance failed {}".format(failed_instance.get_instance_name()))
            failed_instance.set_instance_power_failure()

    def _check_instance_watchdog(self, connect, domain, action, opaque):

        if action in InstanceEvent.Event_watchdog_action:
            failed_instance = HAInstanceManager.get_instance(domain.name())
            logging.error(
                "InstanceDetectionThread - WatchdogCallback {} {}".format(action, domain.name()))

            if failed_instance is None:
                logging.warning(
                    "InstanceDetectionThread - Unprotected instance failed, do nothing {}".format(domain.name()))
                return

            logging.error(
                "InstanceDetectionThread - Protected instance failed {}".format(failed_instance.get_instance_name()))
            failed_instance.set_instance_os_failure()

    def _check_libvirt_connection(self, libvirt_connection):
        try:
            if libvirt_connection.isAlive() == 1:
                return True
            else:
                return False

        except Exception as e:
            libvirt_connection.close()
            message = "InstanceDetectionThread - fail to check libvirt connection : ", str(
                e)
            logging.error(message)
            return False

    def _create_libvirt_detection_thread(self):
        try:
            libvirt.virEventRegisterDefaultImpl()
            event_loop_thread = threading.Thread(
                target=self.__virEventLoopNativeRun, name="libvirtEventLoop")
            event_loop_thread.setDaemon(True)
            event_loop_thread.start()

        except Exception as e:
            message = "InstanceDetectionThread - fail to create libvirt detection thread: ", str(
                e)
            logging.error(message)

    def _detect_and_recover_instance(self, instance_list, libvirt_connection):
        if not instance_list:
            return None

        for _, instance in instance_list.items():
            network_failure = instance.check_instance_network_failure()
            if network_failure is None:
                continue

            status = instance.get_instance_status()

            if network_failure and status is "Healthy":
                os_failure = instance.check_instance_os_failure()
                power_failure = instance.check_instance_power_failure()

                if not self._check_libvirt_connection(libvirt_connection):
                    logging.error(
                        "InstanceDetectionThread - libvirt connection problem")
                    break

                if os_failure:
                    logging.error(
                        "InstanceDetectionThread - OS FAILURE, attempting to recover")
                    instance.recover_instance_os_hang()
                elif power_failure:
                    logging.error(
                        "InstanceDetectionThread - POWER FAILURE, attempting to recover")
                    instance.recover_instance_crash()
                else:
                    logging.error(
                        "InstanceDetectionThread - NETWORK FAILURE, attempting to recover")
                    instance.recover_instance_network()

            elif network_failure == False and status is not "Healthy":
                logging.info("InstanceDetectionThread - revert to default")
                instance.revert_to_default()

    def _get_libvirt_connection(self):
        try:
            libvirt_connection = libvirt.openReadOnly(self.libvirt_uri)
            if libvirt_connection is None:
                message = "InstanceDetectionThread - fail to open libvirt connection to qemu:///system"
                logging.error(message)
            else:
                return libvirt_connection
        except Exception as e:
            message = "InstanceDetectionThread - fail to open libvirt connection: ", str(
                e)
            logging.error(message)

    def __virEventLoopNativeRun(self):
        while True:
            libvirt.virEventRunDefaultImpl()
