# NCU-HASS Installation guide (ver. 5.1) <a id="top"/>
###### last updated: `October 30, 2021`
###### author: `Yen-Lin, Lee` `ratriabdatush`

## Table of Contents

* [1. OPENSTACK](#openstack)
  * [Prerequisites](#Prerequisites)
  * [OpenStack Services](#OpenStack-Services)
  * [References](#references1)
* [2. OpenStack Settings](#openstack_settings)
  * [Network and Subnet](#Network-and-Subnet)
  * [Security Groups](#Security-Groups)
  * [Flavor Setting](#Flavor-Setting)
  * [Instance Setting](#Instance-Setting)
  * [Volume Setting](#Volume-Setting)
  * [References](#references2)
* [3. IPMITOOL](#ipmitool)
  * [Installation](#Installation)
  * [Verification](#verification1)
  * [References](#references3)
* [4. Install HASS](#hass)
  * [Controller node](#Controller-node)
* [5. Watchdog](#watchdog)
  * [Verification](#verification2)
* [6. Create your own ubuntu image](#create_image)
  * [Install Watchdog daemon](#Install-Watchdog-daemon)
  * [Shrink qcow2 image (Optional)](#Shrink-qcow2-image)
  * [Verification](#verification3)
  * [References](#references4)
* [7. Enable password-less SSH (Optional)](#enable_ssh)
* [8. VM Evacuation Settings](#vm_evacuation_settings)
  * [Verification](#verification4)
  * [References](#references5)
* [Policy (Optional)](#policy)
  * [References](#references6)

## 1. OPENSTACK <a id="openstack"/>

**version: Queens**

### Prerequisites
| Items              |            Controller             |              Compute              |           Blockstorage            |
| ------------------ |:---------------------------------:|:---------------------------------:|:---------------------------------:|
| Operating System   | Ubuntu 16.04 LTS (desktop/server) | Ubuntu 16.04 LTS (desktop/server) | Ubuntu 16.04 LTS (desktop/server) |
| Security           |            (Optional)             |                 -                 |                 -                 |
| Host networking    |                yes                |                yes                |                yes                |
| NTP                |                yes                |                yes                |                yes                |
| OpenStack packages |                yes                |                yes                |                yes                |
| SQL database       |                yes                |                 -                 |                 -                 |
| Message queue      |                yes                |                 -                 |                 -                 |
| Memcached          |                yes                |                 -                 |                 -                 |
| Etcd               |                yes                |                 -                 |                 -                 |

### OpenStack Services
| Items                         | Controller | Compute | Blockstorage |
| ----------------------------- |:----------:|:-------:|:------------:|
| Keystone (identity service)   |    yes     |    -    |      -       |
| Glance (image service)        |    yes     |    -    |      -       |
| Nova (compute service)        |    yes     |   yes   |      -       |
| Neutron (networking service)  |    yes     |   yes   |      -       |
| Horizon (dashboard service)   |    yes     |    -    |      -       |
| Cinder (blockstorage service) |    yes     |    -    |     yes      |

:information_source:
The OS version used in this installation guide is Ubuntu 18.04.5 LTS (server), and the django version is 1.11.11.

### References <a id="references1"/>

- [OpenStack Queens installations](https://docs.openstack.org/queens/install/)

<a href="#top">:arrow_heading_up: back to top</a>

## 2. OpenStack Settings <a id="openstack_settings"/>

### Network and Subnet <a id="Network-and-Subnet"/>

* Go to Horizon menu 
  `Admin` > `Network` > `Networks` > `Create Network`, and follow the steps below to complete the creation.
#### 1. On the "Network" sub-page, follow the steps below to fill out the form.  
  * Name: `NETWORK_NAME` 
  * Project: `admin`
  * Provider Network Type: `Flat`
  * Physical Netwok: `provider`
  * Check the "Enable Admin State", "Shared", "External Network", and "Create Subnet" options
  
:information_source: 
Note: Replace NETWORK_NAME with a suitable name.
  
#### 2. On the "Subnet" sub-page, follow the steps below to fill out the form.
  * Subnet Name `SUBNET_NAME`
  * Network Addess `NETWORK_IP/XX` (example: 192.168.1.0/24)
  * Gateway IP `GATEWAY_IP` (example: 192.168.1.1)

:information_source: 
Note: Replace SUBNET_NAME with a suitable name, and replace NETWORK_IP and GATEWAY_IP with the IP of the domain where the controller node is located.

#### 3. On the "Subnet Details" sub-page, follow the steps below to fill out the form.
  * Check the "Enable DHCP" option
  * Allocation Pools `START_IP, END_IP` (example: "192.168.1.100, 192.168.1.150)
  * DNS Name Servers `DNS_IP` (example: 8.8.4.4)

:information_source: 
Note: Replace START_IP and END_IP with the first and last IP of the IP range you plan to assign to the instance, and replace the DNS_IP with a suitable DNS IP.

### Security Groups <a id="Security-Groups"/>
Go to Horizon menu 
`Project` > `Network` > `Security Groups` > `Manage Rules`, and follow the steps below to complete the setup.

#### 1. Add ICMP Egress
  * Click the "Add Rule" button and follow the steps below to fill out the form.
    * Rule: `All ICMP`
    * Direction: `Egress`
    * Remote: `CIDR`
    * CIDR: `0.0.0.0/0`
    * Ether Type: `IPv4`

#### 2. Add ICMP Ingress
  * Click the "Add Rule" button and follow the steps below to fill out the form.
    * Rule: `All ICMP`
    * Direction: `Ingress`
    * Remote: `CIDR`
    * CIDR: `0.0.0.0/0`
    * Ether Type: `IPv4`

#### 3. Add Custom TCP
  * Click the "Add Rule" button and follow the steps below to fill out the form.
    * Rule: `Custom TCP Rule`
    * Direction: `Egress`
    * Open Port: `Port`
    * Port: `22`
    * Remote: `CIDR`
    * CIDR: `0.0.0.0/0`
    * Ether Type: `IPv4`

### Flavor Setting
#### 1. Source the admin credentials to gain access to admin-only CLI commands:
```
$ . admin-openrc
```

#### 2. Create flavor <a id="CreateFlavor"/>
```
$ openstack flavor create FLAVOR_NAME --vcpus 1 --ram 1000 --disk 10 --id 1
```
:information_source: 
Note: Replace FLAVOR_NAME with a suitable name.

#### 3. Add watchdog metadata 
```
$ openstack flavor set FLAVOR_NAME --property hw:watchdog_action=none
```
:information_source: 
Note: FLAVOR_NAME is the flavor name created in the [previous step](#CreateFlavor)

#### 4. Verification
```
$ openstack flavor show FLAVOR_NAME
```
:information_source: 
Note: FLAVOR_NAME is the flavor name created in the [previous step](#CreateFlavor)

### Instance Setting

:warning: 
Create instance from volume. This version only provides live migration for intance-boot-from-volume.

### Volume Setting
Please complete the following steps on the Controller node and the storage node.
#### 1. Edit the **/etc/cinder/cinder.conf** file and complete the following actions:
In the [DEFAULT] section, add the following line:

```
[DEFAULT]
# ...
allowed_direct_url_schemes = cinder
image_upload_use_cinder_backend = True
```

#### 2. Restart the Cinder service

* On Controller node

```
# service nova-api restart
# service cinder-scheduler restart
# service apache2 restart
```

* On storage node

```
# service tgt restart
# service cinder-volume restart
```

### References <a id="references2"/>
* [Configure the Volume-backed image](https://docs.openstack.org/cinder/latest/admin/blockstorage-volume-backed-image.html)

<a href="#top">:arrow_heading_up: back to top</a>

## 3. IPMITOOL <a id="ipmitool"/>

### Installation
- On Controller node
```
# apt-get install ipmitool
```
- On Compute node with IPMI
```
# apt-get install ipmitool openipmi
# modprobe ipmi_msghandler
# modprobe ipmi_devintf
# modprobe ipmi_si 
```
:information_source: 
On compute node without IPMI, both module `ipmi_devintf` and `ipmi_si` cannot be loaded.

### Verification <a id="verification1"/>
* On Controller node
1. Get chassis status from IPMI
```
$ ipmitool -I lanplus -U IPMI_USER -P IPMI_PASSWORD -H IPMI_IP_ADDRESS chassis status
```

2. Restart the host
```
$ ipmitool -I lanplus -U IPMI_USER -P IPMI_PASSWORD -H IPMI_IP_ADDRESS chassis power reset
```
3. Print the system event log
```
$ ipmitool -I lanplus -U IPMI_USER -P IPMI_PASSWORD -H IPMI_IP_ADDRESS sel list
```
4. Get IPMI hardware sensor value
```
$ ipmitool -I lanplus -U IPMI_USER -P IPMI_PASSWORD -H IPMI_IP_ADDRESS sdr list
```
:information_source:
Note: Replace IPMI_USER, IPMI_PASSWORD, and IPMI_IP_ADDRESS with the corresponding username, password, and IP address.

* On Compute node with IPMI
1. Get IPMI hardware sensor value
```
# ipmitool sdr list 
```
2. Get watchdog value
```
# ipmitool mc watchdog get
```

### References <a id="references3"/>
- [How to work on IPMI and IPMITOOL](https://community.pivotal.io/s/article/How-to-work-on-IPMI-and-IPMITOOL)
- [Fun with IPMI](https://blog.bofh.it/id_124)
- [How to Use IPMItool to Control Power](https://docs.oracle.com/cd/E19273-01/html/821-0243/gixvt.html)

<a href="#top">:arrow_heading_up: back to top</a>

## 4. Install HASS <a id="hass"/>
Please complete the following steps on the Controller node.
### Prerequisites
To create the databases, complete these steps:
- Use the database access client to connect to the database server as the root user:
```
# mysql
```

- Create the hass databases:
```
MariaDB [(none)]> CREATE DATABASE hass;
```

- Grant proper access to the databases:
```
MariaDB [(none)]> GRANT ALL PRIVILEGES ON hass.* TO 'hass'@'controller' IDENTIFIED BY 'HASSDB_PASS';

MariaDB [(none)]> GRANT ALL PRIVILEGES ON hass.* TO 'hass'@'localhost' IDENTIFIED BY 'HASSDB_PASS';

MariaDB [(none)]> GRANT ALL PRIVILEGES ON hass.* TO 'hass'@'%' IDENTIFIED BY 'HASSDB_PASS';
```
:information_source:
Note: Replace HASSDB_PASS with a suitable password.

### Install and configure components
#### 1. Download the NCU-HASS package
Download the NCU-HASS package from github to the PACKAGE_PATH on the controller node. 
Then copy the directory to a suitable location to complete the NCU-HASS installation.

*  Copy the **haAdmin** directory to the OpenStack dashboards directory.
```
# cp -r [PACKAGE_PATH]/dashboard/haAdmin [OPENSTACK_DASHBOARD_PATH]/dashboards/.
```

* Copy the **haProject** directory to the OpenStack dashboards directory.
```
# cp -r [PACKAGE_PATH]/dashboard/haProject [OPENSTACK_DASHBOARD_PATH]/dashboards/.
```

* Copy the **REST** directory to the OpenStack dashboards directory.
```
# cp [PACKAGE_PATH]/dashboard/REST [OPENSTACK_DASHBOARD_PATH]/.
```

* Enable **haAdmin** and **haProject** menus
```
# cp [PACKAGE_PATH]/dashboard/enabled/_2600_haAdmin.py [OPENSTACK_DASHBOARD_PATH]/enabled/.

# cp [PACKAGE_PATH]/dashboard/enabled/_2400_haProject.py [OPENSTACK_DASHBOARD_PATH]/enabled/.
```

:information_source:
Note: \
**PACKAGE_PATH** is the path where the NCU-HASS package is located. \
**OPENSTACK_DASHBOARD_PATH** is the path of OpenStack openstack_dashboard directory, the default is **/usr/share/openstack-dashboard/openstack_dashboard**

#### 2. Modify `hass.conf` file

Edit the **PACKAGE_PATH/controller_node/hass.conf** file and complete the following actions:

* In the [openstack] section, configure database access and network information:
```
[openstack]
openstack_admin_account = ADMIN_ACCOUNT
openstack_admin_password = ADMIN_PASS
openstack_user_domain_id = USER_DOMAIN_ID
openstack_project_domain_id = PROJECT_DOMAIN_ID
openstack_project_name = admin
openstack_external_network_gateway_ip = CONTROLLER_GATEWAY
openstack_provider_network_name = PROVIDER_NETWORK_NAME
```
:information_source:
Note: \
Replace **ADMIN_ACCOUNT**, **ADMIN_PASS**, **USER_DOMAIN_ID**, and **PROJECT_DOMAIN_ID** with the corresponding admin account, admin password, user domain id, and project domain id registered in OpenStack database (In the OpenStack installation guide, it is recommended to use'default' as the user domain id and project domain id).\
Replace **CONTROLLER_GATEWAY** with the network gateway of the controller node, and **PROVIDER_NETWORK_NAME** with the **NETWORK_NAME** used in the [previous step](#network_settings).

* In the [ipmi] and [ipmi_user] sections, configure ipmi access:
```
[ipmi]
# ...

# example: compute1 = 192.168.2.xx
COMPUTE_HOSTNAME = IPMI_IP_ADDRESS
COMPUTE_HOSTNAME2 = IPMI_IP_ADDRESS2


[ipmi_user]
COMPUTE_HOSTNAME = IPMI_USER,IPMI_PASSWORD
COMPUTE_HOSTNAME2 = IPMI_USER2,IPMI_PASSWORD2
```
:information_source:
Note: 
Replace **IPMI_IP_ADDRESS**, **IPMI_USER**, and **IPMI_PASSWORD** with the corresponding ipmi ip, ipmi user account and ipmi password set on the computing host. Please fill in the information of all computing hosts to be protected by NCU-HASS.

* In the [ipmi_sensor] section, configure ipmi sensor information:
```
[ipmi_sensor]
ipmi_watched_sensors = SENSOR_NAMES
```
:information_source:
Note: 
Replace **SENSOR_NAMES** with the names of all IPMI hardware sensors used. Please separate each sensor name with',', do not use spaces. For example, `ipmi_watched_sensors = 02-CPU,02-CPU 1,03-CPU 2`.

* In the [mysql] section, configure database access:
```
[mysql]
mysql_ip = DB_IP
mysql_username = hass 
mysql_password = HASSDB_PASS
mysql_db = hass
```
:information_source:
Note: 
Replace **DB_IP** with the ip of the host where the OpenStack database is installed, and replace **HASSDB_PASS** with the hass password recorded in the OpenStack database.

* In the [keystone_auth] section, configure keystone access:
```
[keystone_auth]
url = KEYSTONE_URL
port = KEYSTONE_PORT
```
:information_source:
Note: 
Replace **KEYSTONE_URL** with the ip of the host where the keystone is installed, and replace **KEYSTONE_PORT** with the port used by the keystone.

* In the [keystone_auth] section, configure NCU-HASS RESTful server access:
```
[RESTful]
host = CONTROLLER_IP
port = 9999
```
:information_source:
Note: 
Replace **CONTROLLER_IP** with the controller node ip.

#### 3. Move `hass.conf` to `/etc/.` 

```bash
$ sudo -H pip install flask
$ sudo -H pip install pymysql
$ sudo -H pip install prctl
$ sudo -H pip install cryptography
```

#### 4. Set log folder for NCU-HASS
```
service apache2 reload

# mkdir /var/log/hass && \
# bash -c 'echo> /var/log/hass/hass.log' && \
# chmod 666 /var/log/hass/hass.log
```

#### 5. Enable NCU-HASS as a daemon

* Create `/etc/systemd/system/hass.service` as `root` on compute host with following content. Modify `WorkingDirectory` to point to the controller_node folder.

```
[Unit]
Description=DetectionAgent
After=libvirt-bin.service

[Service]
WorkingDirectory=[PACKAGE_PATH]/controller_node/
ExecStart=/usr/bin/python HASS_RESTful.py
Environment=PYTHONUNBUFFERED=TRUE
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

* Start NCU-HASS 
```
# chmod 664 /etc/systemd/system/hass.service
# systemctl daemon-reload
# systemctl enable hass.service
# systemctl start hass.service
```

* Check the status of the `hass` daemon
```
# service hass status 
```

<a href="#top">:arrow_heading_up: back to top</a>

## 5. Watchdog - On Physical Machine with IPMI <a id="watchdog"/>

1. Install the packages:
```
# apt install watchdog
```


2. Edit the `/etc/watchdog.conf` file and complete the following actions:

* setup `watchdog-device`, `interval`, and `priority`

```
# ...
watchdog-device        = /dev/watchdog

# ...
interval                = 1

# ...
priority                = 1
```

3. Start watchdog service
```
# modprobe ipmi_watchdog

# service watchdog start

# ln /lib/systemd/system/watchdog.service /etc/systemd/system/multi-user.target.wants/watchdog.service
```

4. Edit the `/etc/modules` file
* add `ipmi_watchdog`, `ipmi_devintf`, and `ipmi_si` to the file. 
```
# lp
# rtc
ipmi_watchdog
ipmi_devintf
ipmi_si
```

5. Reboot the host
```
# reboot
```

:information_source: 
[Module rpc&lp has been removed ages ago.](https://bugs.launchpad.net/ubuntu/+source/hw-detect/+bug/1317077)

:information_source: 
On compute node without IPMI, you can install `softdog` and use `modprobe softdog` to make watchdog working. But `softdog` cannot be probed on boot up even if added in `/etc/modules`.

#### References

[watchdog service is not working because /dev/watchdog does not exist](https://serverfault.com/questions/638064/watchdog-service-is-not-working-because-dev-watchdog-does-not-exist)

### Verification <a id="verification2"/>
1. Check the information 
```
# lsmod | grep ipmi
```
The output should look like this:
```
ipmi_devintf
ipmi_si
ipmi_watchdog
ipmi_msghandler
```

2. Check the status of the watchdog service
```
# service watchdog status
```
The output should show: `watchdog is running`

3. Check the hardware timer status:
```
# ipmitool mc watchdog get
```
The output should look like this:
```
Watchdog Timer Use:     SMS/OS (0x44)
Watchdog Timer Is:      Started/Running
Watchdog Timer Actions: Hard Reset (0x01)
Pre-timeout interval:   0 seconds
Timer Expiration Flags: 0x00
Initial Countdown:      60 sec
Present Countdown:      59 sec
```
If you do it a few times, you will see the countdown being reset regularly by the daemon.

#### References
[Setup the Hardware Watchdog Timer on Ubuntu 12.04](https://github.com/miniwark/miniwark-howtos/blob/master/setup_the_hardware_watchdog_timer_on-ubuntu_12.04.md)

 
<a href="#top">:arrow_heading_up: back to top</a>


## 6. Create your own ubuntu image <a id="create_image"/>
For creating our image using on openstack, follow instruction below and install `cloud-init`.
https://docs.openstack.org/image-guide/ubuntu-image.html

Also, you can use `virt-manager` to create vm and follow instrunction from `Log in to newly created image` chapter.

During the above image creation process, you should complete the following steps in the instance before the "Shut down the instance" step.

1. Edit `/etc/cloud/cloud.cfg` to enable login with password. 
```
lock_passwd: False
```

:information_source: 
Nova expects the volume to be available within defined timeout. With larger images it might take longer to create the volume than the default configured timeout. Hence we need to edit `block_device_allocate_retries` in `/etc/nova/nova.conf` of controller and compute. After that, restart `nova-compute` service.

2. Install Watchdog daemon <a id="Install-Watchdog-daemon"/>
* Execute the following commands in the instance.
```
# apt-get update

# apt-get install --no-install-recommends linux-image-extra-virtual

# apt-get install watchdog
```
3. Edit `/etc/watchdog.conf` file
```
# ...
watchdog-device        = /dev/watchdog
watchdog-timeout       = 5

interval                = 1 
priority                = 1
```

4. Comment out `blacklist i6300esb` and `blacklist softdog` in `/etc/modprobe.d/blacklist-watchdog.conf` and `/lib/modprobe.d/blacklist*.conf`

:information_source: An example of the `blacklist*.conf` file is `blacklist_linux_4.15.0-159-generic.conf`

5. Edit `/etc/modules-load.d/modules.conf` file and add the following content.
```
i6300esb
```

6. Edit `/etc/modprobe.d/i6300esb.conf` file and add the following content.
```
options i6300esb heartbeat=5
```
:information_source: 
The files that tell the system which kernel modules to load go into **"/etc/modules-load.d/"**. The files that tell the system which parameters to pass to the kernel modules when loading them go into **"/etc/modprobe.d/"**.

7. Edit `/lib/systemd/system/watchdog.service` file and add the following content in [Install] section.
```
[Install]
WantedBy=multi-user.target
```
8. Enable watchdog service
```
# systemctl enable watchdog.service
```

### Shrink qcow2 image (Optional) <a id="Shrink-qcow2-image"/>
Complete the following steps in the instance.

1. Install the packages 
```
# apt-get install zerofree
# apt-get clean
```
2. In recovery mode, use zerofree tag unsed block as sparse space
```
zerofree -v /dev/sda...
```
:information_source: 
You need to remount it to read-only mode if `/dev/xxx is mounted in rw` pop up. For more information see [How to umount / ? It's busy](https://superuser.com/questions/429199/how-to-umount-its-busy)


3. Noop conversion (qcow2-to-qcow2) removes sparse space (-O) and add compression to the output image:
```
qemu-img convert -c -O qcow2 source.qcow2 shrunk.qcow2
```

4. Verify: There is a comparison of image between with and without compression
```bash
-rw------- 1 root root 15363M  05:19 ubuntu.qcow2
-rw-r--r-- 1 root root   686M  05:40 ubuntuWithCompression.qcow2
```

### Verification <a id="verification3"/>
Before verifying the instance, you should complete the image and volume creation according to the guidelines provided by OpenStack. Then verify the instance through the following steps.

1. On the OpenStack Dashboard, go to `Admin` > `Compute` > `Flavors`
- Click the `Create Flavor` button to create a flavor with metadata `hw:watchdog_action`
![](https://i.imgur.com/shvxsZR.png)

:information_source: 
[Avaiable parameter](https://docs.openstack.org/python-glanceclient/latest/cli/property-keys.html): disabled/reset/poweroff/pause/none. 
`reset` is not supported by recovery service of HASS system. 
We recommend using 'none'

2. Lannch VM with the flavor. From inside the instance:
![](https://i.imgur.com/ARyaCZr.png)


3. Check the status of the watchdog service
```
# systemctl status watchdog
```
The output is as follows:

![](https://i.imgur.com/kD9LbhB.png)

4. Create a cluster according to the NCU-HASS user manual and add computing nodes and instances to the cluster.

5. Hang guest os, the instance will be reboot by NCU-HASS on the computing node.

:warning: 
Some file might may be damaged after hard-rebooting executed by NCU-HASS.
For example:

- Before
![](https://i.imgur.com/VbEuCmn.jpg)

- After
![](https://i.imgur.com/cagCH9y.jpg)


### references <a id="references4"/>
- https://blog.csdn.net/somehow1002/article/details/78702742
- https://serverfault.com/questions/432119/is-there-any-way-to-shrink-qcow2-image-without-converting-it-raw
- [How to upload a volume to an image which is in 'in-use' status](
https://access.redhat.com/solutions/3211471)

<a href="#top">:arrow_heading_up: back to top</a>

## 7. Enable password-less SSH (Optional) <a id="enable_ssh"/>
Enable password-less SSH so that root on one compute host can log on to any other compute host without providing a password. The libvirtd daemon, which runs as `root`, uses the SSH protocol to copy the instance to the destination and can't know the passwords of all compute hosts.

```
# compute node /etc/ssh/sshd_config
PermitRootLogin yes
```

`service ssh restart`

You may, for example, compile root's public SSH keys on all compute hosts into an authorized_keys file and deploy that file to the compute hosts.

For example, on compute host
```bash
# change root's pwd of compute nodes
compute1@compute1:~$ sudo passwd root

# publish public key from a compute node to another compute node
compute1@compute1:~$ sudo -i
root@compute1:~# ssh-keygen
root@compute1:~# ssh-copy-id -i ~/.ssh/id_rsa.pub root@compute1
root@compute1:~# ssh-copy-id -i ~/.ssh/id_rsa.pub root@compute2
root@compute1:~# ssh-copy-id -i ~/.ssh/id_rsa.pub root@compute3
root@compute1:~# ssh-copy-id -i ~/.ssh/id_rsa.pub root@compute4

# verify
root@compute1:~# ssh root@hostname
root@compute2:~# ssh root@hostname
```
:information_source: 
For running HASS testcase script, you should deploy that file to each compute host from controller with `root` & `controller` account.


**Reference**
- [Configure SSH between compute nodes](https://docs.openstack.org/nova/rocky/admin/ssh-configuration.html)

<a href="#top">:arrow_heading_up: back to top</a>

## 8. VM Evacuation Settings <a id="vm_evacuation_settings"/>
Since NCU-HASS will evacuate the VM for failover, we need to enable VM evacuation.

For each computing node, edit the `libvirtd.conf` and `libvirtd` files.

- In `/etc/libvirt/libvirtd.conf` file
```
# enable
listen_tls = 0

# enable
listen_tcp = 1

# add
auth_tcp = "none"
```

- In `/etc/default/libvirtd` file
```
# modify
libvirtd_opts="-l"
```

### Verification <a id="verification4"/>
- After restart Libvirtd, Libvirt is listening on port 16509.
```bash
root@compute1:~# systemctl restart libvirtd
root@compute1:~# netstat -lntp | grep libvirtd
tcp        0      0 0.0.0.0:16509           0.0.0.0:*               LISTEN      3169/libvirtd   
tcp6       0      0 :::16509                :::*                    LISTEN      3169/libvirtd   
root@compute1:~# ps -ef | grep libvirt
libvirt+  1847     1  0 00:55 ?        00:00:00 /usr/sbin/dnsmasq --conf-file=/var/lib/libvirt/dnsmasq/default.conf --leasefile-ro --dhcp-script=/usr/lib/libvirt/libvirt_leaseshelper
root      1848  1847  0 00:55 ?        00:00:00 /usr/sbin/dnsmasq --conf-file=/var/lib/libvirt/dnsmasq/default.conf --leasefile-ro --dhcp-script=/usr/lib/libvirt/libvirt_leaseshelper
root      3169     1  0 01:45 ?        00:00:00 /usr/sbin/libvirtd -l
root      3262  3013  0 01:52 pts/2    00:00:00 grep --color=auto libvirt
```

- On any computing node, try to use `virsh` to connect to another computing node
```bash
root@compute2:~# virsh -c qemu+tcp://COMPUTE_IP/system
Welcome to virsh, the virtualization interactive terminal.

Type:  'help' for help with commands
       'quit' to quit

virsh # 
```
:information_source:
Replace COMPUTE_IP with the ip of another computing node.

- Create an instance and do live-migration operation to verify.
```bash
$ openstack server migrate --live [host] [server]
```

> :information_source: 
>When encounter a message below:
>```
>Unacceptable CPU info: CPU doesn't have compatibility.
>
>0
>```
>Use `lshw -c cpu` to check if cpu of target and source host are the same >generation. 
>
>---
>
>For example, these cpu are different generation so that live-migration from host with newer cpu to host with older cpu will be impossible. **Libvirt** won't make it happen and will throw `VIR_CPU_COMPARE_ERROR`.
>
>```bash
>localadmin@compute1:~$ lshw -c cpu
>WARNING: you should run this program as super-user.
>  *-cpu                   
>       product: Intel(R) Xeon(R) CPU E5-2620 v4 @ 2.10GHz
># ------------------------------------------------------------
>localadmin@compute2:~$ lshw -c cpu
>WARNING: you should run this program as super-user.
>  *-cpu                   
>       product: Intel(R) Xeon(R) CPU E3-1220 v6 @ 3.00GHz
>```
>
>~~
>
>```
>To view a full list of the CPU models supported for an architecture type, 
>run the virsh cpu-models architecture command. For example: 
>
>$ virsh cpu-models x86_64
>486
>pentium
>pentium2
>pentium3
>pentiumpro
>coreduo
>n270
>...
>```
>
>**XML** format used to represent domains.
>
>If we wanna each instance run with simulated Haswell CPU, edit **xml** to specify the cpu model:
>```bash
>~# virsh list
>
>
> Id    Name                           State
> --------------------------------------------
> -     testInstance                   shutoff
>
>~# virsh edit testInstance
>```
>```xml
><cpu match='exact'>
>  <model fallback='allow'>Haswell</model> # sepcify cpu model
>  <vendor>Intel</vendor>
>  <topology sockets='1' cores='2' threads='1'/>
>  <cache level='3' mode='emulate'/>
>  <feature policy='disable' name='lahf_lm'/>
></cpu>
>```
>```bash
>~# virsh start testInstance
>~# virsh list
>
>
> Id    Name                           State
> --------------------------------------------
> 16     testInstance                   running
>```
>Do this operation on each computing node.
>
>Reference: 
>- [LibvirtXMLCPUModel](https://wiki.openstack.org/wiki/LibvirtXMLCPUModel)
>- [CPU model and topology](https://libvirt.org/formatdomain.html#elementsCPU)
>- [1.4. Supported Guest CPU Models](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/virtualization_deployment_and_administration_guide/sect-kvm_guest_virtual_machine_compatibility-supported_cpu_models)
>---
>
>Unfortunately, **nova** will overwrite our setting using `nova.conf` each time we start the instance (unless you never use **nova**), then previous method will not work.
>
>To achieve our goal, modify `/etc/nova/nova.conf` on each compute.
>```
>[libvirt]
>cpu_mode = custom
>cpu_model = Haswell
>```
>Reference: 
>- [Specify the CPU model of KVM guests](https://docs.openstack.org/mitaka/config-reference/compute/hypervisor-kvm.html)

### References <a id="references5"/>
- [libvirt-bin.conf file missing](https://askubuntu.com/questions/932098/libvirt-bin-conf-file-missing)
- [How to Migrate an Instance with Zero Downtime: OpenStack Live Migration with KVM Hypervisor and NFS Shared Storage](https://www.mirantis.com/blog/tutorial-openstack-live-migration-with-kvm-hypervisor-and-nfs-shared-storage/)
- [Libvirt daemon is not listening on tcp ports although configured to](https://wiki.libvirt.org/page/Libvirt_daemon_is_not_listening_on_tcp_ports_although_configured_to)
- [Openstack Queen Configure live migrations](https://docs.openstack.org/nova/queens/admin/configuring-migrations.html)
- [Live-migrate instances](https://docs.openstack.org/nova/queens/admin/live-migration-usage.html)
- [Live Migration Error](https://bugs.launchpad.net/starlingx/+bug/1837256)

>:warning: 
>When using Horizon, on the `Live Migrate` panel,
>* if the instance is boot from image, then `Block Migration` must be selected. 
>* if the instance is boot from volume, then `Block Migration` must not be selected.

<a href="#top">:arrow_heading_up: back to top</a>


## Policy (Optional) <a id="policy"/>
Modify `/etc/nova/policy.json` to allow account expect admin can:
1. determine which host instance launch on and migrate to.
2. see host which instance running on

with openstack api
```json=
// /etc/nova/policy.json
{
      "os_compute_api:os-extended-server-attributes": "",
      "os_compute_api:os-migrate-server:migrate": "",
      "os_compute_api:os-migrate-server:migrate_live": "",
      "os_compute_api:servers:create:forced_host": ""
}                                                                                                                                        
```

### References <a id="references6"></a>
- [Policies](https://docs.openstack.org/security-guide/identity/policies.html)

<a href="#top">:arrow_heading_up: back to top</a>