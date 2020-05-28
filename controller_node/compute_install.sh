#!/bin/bash

#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

#check root privilege, only root can run this script.

if [ $EUID -ne 0 ] ; then
    echo "This script must be run as root" 1>&2
    set -e
fi
CWD=$PWD
LOG_FILE=/home/localadmin/log/hass_compute_install.log
if [ ! -e "$LOG_FILE" ] ; then
    touch $LOG_FILE
fi

install_script_start() {
    DATE=`date`
    echo "==========$DATE HASS compute install script start=============" >> $LOG_FILE
    install_watchdog_and_ipmitool
}


install_watchdog_and_ipmitool() {
    # ipmitool installation
    apt-get install ipmitool -y >> $LOG_FILE 2>> $LOG_FILE
    result=$?
    if [ $result -eq 0 ];
    then
	echo "=============ipmitool install success=============" >> $LOG_FILE
    else
	echo "=============ipmitool install failed==============" >> $LOG_FILE
        set -e
    fi
    # watchdog installation
    apt-get install watchdog -y >> $LOG_FILE 2>> $LOG_FILE
    result=$?
    if [ $result -eq 0 ];
    then
        echo "=============watchdog install success=============" >> $LOG_FILE
    else
        echo "=============watchdog install failed==============" >> $LOG_FILE
        set -e
    fi

    # git installation
    apt-get install git -y >> $LOG_FILE 2>> $LOG_FILE
    result=$?
    if [ $result -eq 0 ];
    then
        echo "=============git install success=============" >> $LOG_FILE
    else
        echo "=============git install failed==============" >> $LOG_FILE
        set -e
    fi
    configure_watchdog_and_ipmitool
}

configure_watchdog_and_ipmitool() {
    # configure ipmitool
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
	echo ipmi_si >> $MODULE_FILE ;
    fi

    modprobe ipmi_watchdog >> $LOG_FILE
    modprobe ipmi_devintf >> $LOG_FILE
    modprobe ipmi_si >> $LOG_FILE

    # configure watchdog
    WATCHDOG_CONF_FILE=/etc/watchdog.conf
    sed -e "s,^#watchdog-device\s=\s/dev/watchdog,watchdog-device = /dev/watchdog,g" -i $WATCHDOG_CONF_FILE
    sed -e "s,^#interval\t\t=\s1,interval\t\t= 1,g" -i $WATCHDOG_CONF_FILE
    service watchdog start >> $LOG_FILE
    service watchdog status >> $LOG_FILE
    install_compute_service
}

install_compute_service() {
    DIR=$CWD
    cp -r $DIR/compute_node /home/localadmin/.
    cp $DIR/example/Detectionagentd.service /etc/systemd/system/.
    systemctl daemon-reload
    systemctl enable Detectionagentd.service >> $LOG_FILE
    service Detectionagentd start >> $LOG_FILE
    service Detectionagentd status >> $LOG_FILE
}

install_script_end() {
    DATE=`date`
    echo "============$DATE HASS compute install script end==================" >> $LOG_FILE
}

install_script_start
