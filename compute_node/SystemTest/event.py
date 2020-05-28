from datetime import datetime
import libvirt
import threading

class Description(object):
    __slots__ = ('desc', 'args')

    def __init__(self, *args, **kwargs):
        self.desc = kwargs.get('desc')
        self.args = args

    def __str__(self):  # type: () -> str
        return self.desc
    def __getitem__(self, item):  # type: (int) -> str
        try:
            data = self.args[item]
        except IndexError:
            return self.__class__(desc=str(item))

        if isinstance(data, str):
            return self.__class__(desc=data)
        elif isinstance(data, (list, tuple)):
            desc, args = data
            return self.__class__(*args, desc=desc)

        raise TypeError(args)

DOM_EVENTS = Description(
    ("Defined", ("Added", "Updated", "Renamed", "Snapshot")),
    ("Undefined", ("Removed", "Renamed")),
    ("Started", ("Booted", "Migrated", "Restored", "Snapshot", "Wakeup")),
    ("Suspended", ("Paused", "Migrated", "IOError", "Watchdog", "Restored", "Snapshot", "API error", "Postcopy", "Postcopy failed")),
    ("Resumed", ("Unpaused", "Migrated", "Snapshot", "Postcopy")),
    ("Stopped", ("Shutdown", "Destroyed", "Crashed", "Migrated", "Saved", "Failed", "Snapshot", "Daemon")),
    ("Shutdown", ("Finished", "On guest request", "On host request")),
    ("PMSuspended", ("Memory", "Disk")),
    ("Crashed", ("Panicked",)),
)

run = True
CONNECTION_EVENTS = Description("Error", "End-of-file", "Keepalive", "Client")
WATCHDOG_ACTIONS = Description("None", "Pause", "Reset", "Poweroff", "Shutdown", "Debug", "Inject NMI")

def myConnectionCloseCallback(conn, reason, opaque):
    print("myConnectionCloseCallback: %s: %s" % (
        conn.getURI(), CONNECTION_EVENTS[reason]))
    global run
    run = False


def lifeCycleEventCallBack(conn, dom, event, detail, opaque):
    dt_domain = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(dt_domain + " [DomainCallback] %s %s %s" % (
        dom.name(), DOM_EVENTS[event], DOM_EVENTS[event][detail]))

def watchdogEventCallBack(conn, dom, action, opaque):
    dt_watchdog = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(dt_watchdog + " [WatchdogCallback] %s %s" % (
        dom.name(), WATCHDOG_ACTIONS[action]))

def virEventLoopNativeRun():
    while True:
        libvirt.virEventRunDefaultImpl()


libvirt_uri = "qemu:///system"
libvirt.virEventRegisterDefaultImpl()
eventLoopThread = None
eventLoopThread = threading.Thread(
    target=virEventLoopNativeRun, name="libvirtEventLoop")
eventLoopThread.setDaemon(True)
eventLoopThread.start()

conn = libvirt.open(libvirt_uri)
if conn == None:
    print('Failed connect')
    exit(1)
conn.registerCloseCallback(myConnectionCloseCallback, None)
print('Connection established')

conn.domainEventRegister(lifeCycleEventCallBack, None)
conn.domainEventRegisterAny(
    None, libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG, watchdogEventCallBack, None)

timeout = None
conn.setKeepAlive(5, 3)

while True:
    pass

conn.close()


