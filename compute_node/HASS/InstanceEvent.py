#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import libvirt

class InstanceEvent(object):

    _event_string = (
        ("Added", "Updated", "Renamed", "Snapshot"),
        ("Removed", "Renamed"),
        ("Booted", "Migrated_when_boot", "Restored", "Snapshot", "Wakeup"),
        ("Paused", "Migrated_when_pause", "IOError", "Watchdog", "Restored",
         "Snapshot", "API error", "Postcopy", "Postcopy failed"),
        ("Unpaused", "Migrated_when_unpause", "Snapshot", "Postcopy"),
        ("Shutdown", "Destroyed", "Crashed", "Migrated_when_shutoff",
         "Saved", "Failed", "Snapshot", "Daemon"),
        ("Finished", "Prepare-ShutOff")
    )

    EVENT_FAILED = "Event_failed"
    EVENT_DESTROYED = "Event_destroyed"
    EVENT_MIGRATED = "Event_migrated"

    _event_dictionary = {
        "Event_failed": [_event_string[5][2], _event_string[5][5]],
        "Event_destroyed": [_event_string[5][1]],
        "Event_migrated": [_event_string[5][3]]
    }

    def __init__(self):
        pass

    @classmethod
    def Event_String(cls, event, detail):
        return cls._event_string[event][detail]

    @classmethod
    def Event_type(cls, event, detail):
        event_str = cls.Event_String(event, detail)
        for key in cls._event_dictionary:
            if event_str in cls._event_dictionary[key]:
                return key

        return "Normal"

    Event_watchdog_action = (
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_NONE,  # = 0, No action, watchdog ignored
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_PAUSE,  # = 1, Guest CPUs are paused
        # libvirt.VIR_DOMAIN_EVENT_WATCHDOG_RESET,  # = 2, Guest CPUs are reset
        # = 3, Guest is forcibly powered off
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_POWEROFF,
        # = 4, Guest is requested to gracefully shutdown
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_SHUTDOWN,
        # = 5, No action, a debug message logged
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_DEBUG,
        # = 6, Inject a non-maskable interrupt into guest
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_INJECTNMI,
    )
