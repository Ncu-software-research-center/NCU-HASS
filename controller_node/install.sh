#!/bin/bash

#check root privilege, only root can run this script.

if [ $EUID -ne 0 ] ; then
    echo "This script must be run as root" 1>&2
    set -e
fi

CWD=$PWD
LOG_FILE=$CWD/install.log
if [ ! -e "$LOG_FILE" ] ; then
    touch $LOG_FILE
fi

install_script_start() {
    DATE=`date`
    echo "==========$DATE HASS install script start=============" >> $LOG_FILE
    apt-get install python-mysqldb -y >> $LOG_FILE 2>> $LOG_FILE
    cp $CWD/hass.conf /etc/.
    upstart_setting
}

upstart_setting() {
    UPSTART_CONF_FILE=$CWD/example/HASSd.service
    cp $UPSTART_CONF_FILE /etc/systemd/system/.
    systemctl daemon-reload
    systemctl enable HASSd.service >> $LOG_FILE
    ipmitool_install
}

ipmitool_install() {
    apt-get install ipmitool -y >> $LOG_FILE 2>> $LOG_FILE
    result=$?
    if [ $result -eq 0 ] ;
    then
	echo "===========ipmitool install success============" >> $LOG_FILE
    else
	echo "===========ipmitool install failed=============" >> $LOG_FILE
	set -e
    fi
    MODULE_FILE=/etc/modules
    if ! grep -q ipmi_watchdog "$MODULE_FILE" ;
    then
	echo ipmi_watchdog >> $MODULE_FILE
    fi

    if ! grep -q ipmi_devintf "$MODULE_FILE" ;
    then
	echo ipmi_devintf >> $MODULE_FILE ;
    fi

    if ! grep -q ipmi_si "$MODULE_FILE" ;
    then
	echo ipmi_si >> "$MODULE_FILE" ;
    fi
    dashboard_setting
}

dashboard_setting() {
    OPENSTACK_DASHBOARD_DIR=/usr/share/openstack-dashboard/openstack_dashboard/dashboards/
    OPENSTACK_ENABLE_DIR=/usr/share/openstack-dashboard/openstack_dashboard/enabled/
    OPENSTACK_REST_DIR=/usr/share/openstack-dashboard/openstack_dashboard/
    rm -rf "$OPENSTACK_DASHBOARD_DIR"haAdmin/
    rm -rf "$OPENSTACK_DASHBOARD_DIR"haProject/
    cp $CWD/hass.conf $CWD/Dashboards/REST/
    cp -r $CWD/Dashboards/haAdmin/ $OPENSTACK_DASHBOARD_DIR
    cp -r $CWD/Dashboards/haProject/ $OPENSTACK_DASHBOARD_DIR
    cp -r $CWD/Dashboards/REST/ $OPENSTACK_REST_DIR
    cp $CWD/Dashboards/_2400_haProject.py $OPENSTACK_ENABLE_DIR
    cp $CWD/Dashboards/_2600_haAdmin.py $OPENSTACK_ENABLE_DIR
    service apache2 restart >> $LOG_FILE
    start_HASS_service
}

start_HASS_service() {
    service HASSd restart >> $LOG_FILE
    install_script_end
}

install_script_end() {
    DATE=`date`
    echo "============$DATE HASS install script end==================" >> $LOG_FILE
}

install_script_start
#dashboard_setting
