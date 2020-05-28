# NCU-HASS Installation guide (ver. 4.1) <a id="top"/>
###### last updated: `2020/05/28`
###### author: `Harry` `ratriabdatush`

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
* [4. HASS](#hass)
  * [Controller node](#Controller-node)
  * [Compute node](#Compute-node)
* [5. Watchdog](#watchdog)
  * [Verification](#verification2)
* [6. Create your own ubuntu image](#create_image)
  * [Install Watchdog daemon](#Install-Watchdog-daemon)
  * [Shrink qcow2 image](#Shrink-qcow2-image)
  * [Verification](#verification3)
  * [References](#references4)
* [7. Enable password-less SSH](#enable_ssh)
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
This version uses Ubuntu 16.04 LTS (desktop/server)

### References <a id="references1"/>

- [OpenStack Queens installations](https://docs.openstack.org/queens/install/)

<a href="#top">:arrow_heading_up: back to top</a>

## 2. OpenStack Settings <a id="openstack_settings"/>

### Network and Subnet

* Create Network 

  Go to Horizon menu 
  `Admin` > `Network` > `Networks` > `Create Network`
  * Name `NAME`
  * Project `admin`
  * Provider Network Type `Flat`
  * Physical Netwok `provider`
  * Enable Admin State `yes`
  * Shared `yes`
  * External Network `yes`
  * Create Subnet `yes`

* Create Subnet
  * Subnet Name `SUBNET_NAME`
  * Network Addess `NETWORK_IP/XX` (example 192.168.1.0/24)
  * Gateway IP `GATEWAY_IP` (example 192.168.1.1)

* Subnet Details
  * Enable DHCP `yes`
  * Allocation Pools `192.168.1.100, 192.168.1.150` (example)
  * DNS Name Servers `8.8.4.4` (example)

### Security Groups
Go to Horizon menu 
`Project` > `Network` > `Security Groups` > `Manage Rules` > `Add Rule`

* Add ICMP Egress
  * Rule `All ICMP`
  * Direction `Egress`
  * Remote `CIDR`
  * CIDR `0.0.0.0/0`
  * Ether Type `IPv4`

* Add ICMP Ingress
  * Rule `All ICMP`
  * Direction `Ingress`
  * Remote `CIDR`
  * CIDR `0.0.0.0/0`
  * Ether Type `IPv4`

* Add Custom TCP
  * Rule `Custom TCP Rule`
  * Direction `Egress`
  * Open Port `Port`
  * Port `22`
  * Remote `CIDR`
  * CIDR `0.0.0.0/0`
  * Ether Type `IPv4`

### Flavor Setting
```
$ . admin-openrc
```

#### 1. Create flavor 
Create flavor named `medium`
```
$ openstack flavor create medium --vcpus 1 --ram 1000 --disk 10 --id 1
```

#### 2. Watchdog metadata
Add metadata `watchdog` 
```
$ openstack flavor set medium --property hw:watchdog_action=none
```

#### 3. Verification
```
$ openstack flavor show medium
```

### Instance Setting

:warning: 
Create instance from volume. This version only provides live migration for intance-boot-from-volume.

### Volume Setting

#### 1. Modify **/etc/cinder/cinder.conf** on Controller and Blockstorage

[DEFAULT]

```
allowed_direct_url_schemes = cinder
image_upload_use_cinder_backend = True
```

#### 2. Restart cinder service

* On Controller

```
# service nova-api restart
# service cinder-scheduler restart
# service apache2 restart
```

* On Blockstorage

```
# service tgt restart
# service cinder-volume restart
```

### References <a id="references2"/>
* [Configure the Volume-backed image](https://docs.openstack.org/cinder/latest/admin/blockstorage-volume-backed-image.html)

<a href="#top">:arrow_heading_up: back to top</a>

## 3. IPMITOOL <a id="ipmitool"/>

### Installation
- On Controller
```bash
sudo apt-get install ipmitool
```
- On Compute node with IPMI
```
sudo apt-get install ipmitool openipmi
sudo modprobe ipmi_msghandler
sudo modprobe ipmi_devintf
sudo modprobe ipmi_si 
```
:information_source: 
On compute node without IPMI, both module `ipmi_devintf` and `ipmi_si` cannot be loaded.

### Verification <a id="verification1"/>
- On Controller
```
ipmitool -I lanplus -U IPMI_USER -P IPMI_PASSWORD -H IPMI_IP_ADDRESS chassis status
ipmitool -I lanplus -U IPMI_USER -P IPMI_PASSWORD -H IPMI_IP_ADDRESS chassis status

ipmitool -I lanplus -H IPMI_IP_ADDRESS -U IPMI_USER -P IPMI_PASSWORD shell

# Show the parameters for Ethernet access
lan print 

# Reset the system
chassis power reset

# Print the system event log
sel list

# Read a specific sensor
sensor get "Temp"
```
- On Compute node with IPMI
```
# Show sensor output
sudo ipmitool sdr type Temperature 

# Display lan settings
sudo ipmitool lan print 1
```

### References <a id="references3"/>
- [How to work on IPMI and IPMITOOL](https://community.pivotal.io/s/article/How-to-work-on-IPMI-and-IPMITOOL)
- [Fun with IPMI](https://blog.bofh.it/id_124)
- [How to Use IPMItool to Control Power](https://docs.oracle.com/cd/E19273-01/html/821-0243/gixvt.html)

<a href="#top">:arrow_heading_up: back to top</a>

## 4. HASS <a id="hass"/>
- [HASS Source Code](), branch: `HASS-4.1`
### Controller node
#### MySQL
```bash
mysql -u root
CREATE DATABASE hass;

GRANT ALL PRIVILEGES ON hass.* TO 'hass'@'controller' IDENTIFIED BY 'HASSDB_PASS';
GRANT ALL PRIVILEGES ON hass.* TO 'hass'@'localhost' IDENTIFIED BY 'HASSDB_PASS';
GRANT ALL PRIVILEGES ON hass.* TO 'hass'@'%' IDENTIFIED BY 'HASSDB_PASS';
```
Replace HASSDB_PASS with a suitable password.

#### Config
##### 1. copy file

[source code path]: the path of source code downloaded from github \
[openstack_dashboard path]: the path of OpenStack openstack_dashboard directory, for example: **/usr/share/openstack-dashboard/openstack_dashboard**

```
# Copy [HA Admin] menu to the OpenStack dashboards directory
sudo cp -r [source code path]/dashboard/haAdmin [openstack_dashboard path]/dashboards/.

# Copy [HA Project] menu to the OpenStack dashboards directory
sudo cp -r [source code path]/dashboard/haProject [openstack_dashboard path]/dashboards/.

# Enable [HA Admin] menu to the OpenStack enabled directory
sudo cp [source code path]/dashboard/enabled/_2600_haAdmin.py [openstack_dashboard path]/enabled/.

# Enable [HA Project] menu to the OpenStack enabled directory
sudo cp [source code path]/dashboard/enabled/_2400_haProject.py [openstack_dashboard path]/enabled/.

# Enable [REST] function to the OpenStack openstack_dashboard directory
sudo cp [source code path]/dashboard/REST [openstack_dashboard path]/.

```

##### 2. Move `[source code path]/controller_node/` to `/home/localadmin/`

##### 3. Modify `hass.conf`

The **hass.conf** file is located in the controller_node folder

> sudo nano hass.conf

```
[openstack]
openstack_admin_account = admin
openstack_admin_password = ADMIN_PASS
openstack_user_domain_id = default
openstack_project_domain_id = default
openstack_project_name = admin
openstack_external_network_gateway_ip = CONTROLLER_GATEWAY

[ipmi]
# example: vendor = DELL
vendor = VENDOR_NAME
# example: compute1 = 192.168.2.xx
COMPUTE_HOSTNAME = IPMI_IP_ADDRESS
COMPUTE_HOSTNAME = IPMI_IP_ADDRESS

[ipmi_sensor]
ipmi_watched_sensors = ["Inlet Temp","Temp"]
ipmi_node_sensors = ["Temp", "Inlet Temp", "Fan1", "Fan2"]
upper_critical = 80
lower_critical = 10

[ipmi_user]
COMPUTE_HOSTNAME = IPMI_USER,IPMI_PASSWORD
COMPUTE_HOSTNAME = IPMI_USER,IPMI_PASSWORD

[mysql]
mysql_ip = controller
# HASSDB_USER
mysql_username = hass 
mysql_password = HASSDB_PASS
mysql_db = hass

[log]
# There are two level INFO and ERROR.
# Note : Level need to use uppercase letters.
level = INFO
location = /var/log/hass/hass.log

[detection]
polling_interval = 5
polling_threshold = 2
polling_port = 2468
wait_restart_threshold = 2

[schedule]
policy = default

[path]
# Where you put HASS folder in compute host
agent_path = /home/localadmin/HASS-4.1/compute_node/HASS/

[version]
openstack_version = queens
os_version = 16

[default]
network_transient_time = 30
heartbeat_time = 3
shared_storage = true
max_message_size = 1024

[RESTful]
host = 192.168.2.11
port = 9999

[iii]
# No longer use
iii_support = false
mysql_ip = CONTROLLER_IP_ADDRESS
mysql_username = novaadmin
mysql_password = openstack
mysql_db = iSoftCloudFrontEndDB
user_name = novaadmin
password = openstack
port = 8080
enterprise = iii

[detector]
ping_command = ['timeout', '0.2', 'ping', '-c', '1', self.node], stderr=subprocess.STDOUT, universal_newlines=True
```
##### 4. Move `hass.conf` to `/etc/.` 

#### Almost done

```bash
pip install flask
pip install pymysql
pip install prctl
pip install cryptography

service apache2 reload

sudo mkdir /var/log/hass && \
sudo bash -c 'echo> /var/log/hass/hass.log' && \
sudo chmod 666 /var/log/hass/hass.log
```

##### Enable hass.service

Create `/etc/systemd/system/hass.service` as `root` on compute host with following content. Modify `WorkingDirectory` to point to the controller_node folder, for example: `WorkingDirectory=/home/localadmin/controller_node/`.

```
[Unit]
Description=DetectionAgent
After=libvirt-bin.service

[Service]
WorkingDirectory=[controller_node folder path]
ExecStart=/usr/bin/python HASS_RESTful.py
Environment=PYTHONUNBUFFERED=TRUE

[Install]
WantedBy=multi-user.target
```
Then, 
```
sudo chmod 664 /etc/systemd/system/hass.service
sudo systemctl daemon-reload
sudo systemctl enable hass.service
sudo systemctl start hass.service
```
Check the status of the `hass` daemon
```
sudo service hass status 
```

### Compute node

:warning: 
Run HASS_RESTful.py on controller first.

:information_source: 
Every compute nodes must be set up, including compute node without IPMI.


##### 1. Move `HASS-4.1/compute_node/HASS/` to `/home/localadmin/`
##### 2. Modify `hass_compute.conf`

The **hass_compute.conf** file is located in the `HASS` folder

> sudo nano hass_compute.conf

```
[openstack]
openstack_admin_account = admin
openstack_admin_password = ADMIN_PASS
openstack_user_domain_id = default
openstack_project_domain_id = default
openstack_project_name = Admin
openstack_external_network_gateway_ip = CONTROLLER_GATEWAY

[detection]
# detection delay
detection_delay = 2
# ping timeout check
network_ping_timeout = 1
# network validation timeout
network_validation_timeout = 30

[keystone_auth]
url = CONTROLLER_IP_ADDRESS
port = 5000

[libvirt]
libvirt_uri = qemu:///system

[log]
# There are two level INFO and ERROR.
# Note : Level need to use uppercase letters.
level = INFO
location = /var/log/hass/hass_compute.log.log

[nova_api]
nova_api_version = 2.29

[polling]
listen_port = 2468

[recovery]
recovery_timeout = 30

[RESTful]
host = CONTROLLER_IP_ADDRESS
port = 9999

[ubuntu_os_version]
version = 16

[watchdog]
watchdog_timeout = 6

```
```
sudo mkdir /var/log/hass && \
sudo bash -c 'echo> /var/log/hass/hass_compute.log' && \
sudo chmod 666 /var/log/hass/hass_compute.log
```

##### Enable detectionagent.service

Create `/etc/systemd/system/detectionagent.service` as `root` on compute host with following content. Modify `WorkingDirectory` to point to the HASS folder, for example: `WorkingDirectory=/home/localadmin/HASS/`.
```
[Unit]
Description=DetectionAgent
After=libvirt-bin.service

[Service]
WorkingDirectory= [HASS folder path] 
ExecStart=/usr/bin/python DetectionAgent.py
Environment=PYTHONUNBUFFERED=TRUE

[Install]
WantedBy=multi-user.target
```
Then, 
```
sudo chmod 664 /etc/systemd/system/detectionagent.service
sudo systemctl daemon-reload
sudo systemctl enable detectionagent.service
sudo systemctl start detectionagent.service
```
Check the status of the detectionagent daemon
```
sudo service detectionagent status
```

<a href="#top">:arrow_heading_up: back to top</a>

## 5. Watchdog - On Physical Machine with IPMI <a id="watchdog"/>

### Installation

`sudo apt install watchdog`


1. Modify `/etc/watchdog.conf`

uncomment `watchdog-device`, `interval`, and `priority`

```
...
watchdog-device        = /dev/watchdog

...
interval                = 1

...
priority                = 1
```
```bash
sudo modprobe ipmi_watchdog
sudo service watchdog start

# auto start on boot up
sudo ln /lib/systemd/system/watchdog.service /etc/systemd/system/multi-user.target.wants/watchdog.service
```

2. Modify `/etc/modules`
> sudo nano /etc/modules

```
# lp
# rtc
ipmi_watchdog
ipmi_devintf
ipmi_si
```

:information_source: 
[Module rpc&lp has been removed ages ago.](https://bugs.launchpad.net/ubuntu/+source/hw-detect/+bug/1317077)

:information_source: 
On compute node without IPMI, you can install `softdog` and use `modprobe softdog` to make watchdog working. But `softdog` cannot be probed on boot up even if added in `/etc/modules`.

#### References

[watchdog service is not working because /dev/watchdog does not exist](https://serverfault.com/questions/638064/watchdog-service-is-not-working-because-dev-watchdog-does-not-exist)

### Verification <a id="verification2"/>

```
sudo reboot
sudo lsmod | grep ipmi
```
Your result must be like:
```
ipmi_devintf
ipmi_si
ipmi_watchdog
ipmi_msghandler
```
```
sudo service watchdog status
```
It must says: `watchdog is running`

Check the hardware timer status:`sudo ipmitool mc watchdog get`
Which display something like:
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
For creating our image using on openstack, follow instruction below and install `clout-init`.
https://docs.openstack.org/image-guide/ubuntu-image.html

Also, you can use `virt-manager` to create vm and follow instrunction from `Log in to newly created image` chapter.

Before shutdown instance, you should have installed watchdog daemon and set up `/etc/cloud/cloud.cfg` to enable login with password. 
```
lock_passwd: False
```

Finally, shrink qcow2 image.

:information_source: 
Nova expects the volume to be available within defined timeout. With larger images it might take longer to create the volume than the default configured timeout. Hence we need to edit `block_device_allocate_retries` in `/etc/nova/nova.conf` of controller and compute. After that, restart `nova-compute` service.

### Install Watchdog daemon
From inside the virtual machine
```bash
sudo apt-get update
sudo apt-get install --no-install-recommends linux-image-extra-virtual
sudo apt-get install watchdog
```
Edit /etc/watchdog.conf
```
watchdog-device        = /dev/watchdog
watchdog-timeout       = 5

interval                = 1 
priority                = 1
```

Comment out `blacklist i6300esb` and `blacklist softdog` in `/etc/modprobe.d/blacklist-watchdog.conf` and `/lib/modprobe.d/blacklist*.conf`

Edit /etc/modules-load.d/modules.conf
```
i6300esb
```

Setting module options using files in /etc/modprobe.d/i6300esb.conf
```
options i6300esb heartbeat=5
```
:information_source: 
The files that tell the system which kernel modules to load go into **"/etc/modules-load.d/"**. The files that tell the system which parameters to pass to the kernel modules when loading them go into **"/etc/modprobe.d/"**.

Edit /lib/systemd/system/watchdog.service
```
[Install]
WantedBy=multi-user.target
```
Then `sudo systemctl enable watchdog.service`

### Shrink qcow2 image
From inside the instance
```
apt-get install zerofree
apt-get clean
```
In recovery mode, use zerofree tag unsed block as sparse space
```
zerofree -v /dev/sda...
```
:information_source: 
You need to remount it to read-only mode if `/dev/xxx is mounted in rw` pop up. For more information see [How to umount / ? It's busy](https://superuser.com/questions/429199/how-to-umount-its-busy)


Noop conversion (qcow2-to-qcow2) removes sparse space (-O) and add compression to the output image:
```
qemu-img convert -c -O qcow2 source.qcow2 shrunk.qcow2
```

There is a comparison of image between with and without compression
```bash
-rw------- 1 root root 15363M  05:19 ubuntu.qcow2
-rw-r--r-- 1 root root   686M  05:40 ubuntuWithCompression.qcow2
```

### Verification <a id="verification3"/>
Create a flavor with metadata `hw:watchdog_action`
![](https://i.imgur.com/shvxsZR.png)

:information_source: 
[Avaiable parameter](https://docs.openstack.org/python-glanceclient/latest/cli/property-keys.html): disabled/reset/poweroff/pause/none. 
`reset` is not supported by recovery service of HASS system. 
We recommend using 'none'

Lannch VM with the flavor. From inside the instance: 
![](https://i.imgur.com/ARyaCZr.png)


`sudo systemctl status watchdog`
![](https://i.imgur.com/kD9LbhB.png)

Hang guest os, the system will be reboot by HASS on compute.

:warning: 
Some file might may be damaged after hard-rebooting executed by detectagention.service of HASS.
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

## 7. Enable password-less SSH <a id="enable_ssh"/>
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
Since NCU-HASS will evacuate the VM for failover, we need to enable VM evacuation

For each computing node, modify the `libvirtd.conf` and `libvirtd` file
> /etc/libvirt/libvirtd.conf
```
# enable
listen_tls = 0

# enable
listen_tcp = 1

# add
auth_tcp = "none"
```

>  /etc/default/libvirtd
```
# modify
libvirtd_opts="-l"
```
### Verification <a id="verification4"/>
After restart Libvirtd, Libvirt is listening on port 16509.
```bash
root@compute1:~# sudo systemctl restart libvirtd
root@compute1:~# sudo netstat -lntp | grep libvirtd
tcp        0      0 0.0.0.0:16509           0.0.0.0:*               LISTEN      3169/libvirtd   
tcp6       0      0 :::16509                :::*                    LISTEN      3169/libvirtd   
root@compute1:~# sudo ps -ef | grep libvirt
libvirt+  1847     1  0 00:55 ?        00:00:00 /usr/sbin/dnsmasq --conf-file=/var/lib/libvirt/dnsmasq/default.conf --leasefile-ro --dhcp-script=/usr/lib/libvirt/libvirt_leaseshelper
root      1848  1847  0 00:55 ?        00:00:00 /usr/sbin/dnsmasq --conf-file=/var/lib/libvirt/dnsmasq/default.conf --leasefile-ro --dhcp-script=/usr/lib/libvirt/libvirt_leaseshelper
root      3169     1  0 01:45 ?        00:00:00 /usr/sbin/libvirtd -l
root      3262  3013  0 01:52 pts/2    00:00:00 grep --color=auto libvirt
```

On any compute try using virsh to connect another compute
```bash
root@compute2:~# virsh -c qemu+tcp://compute1/system
Welcome to virsh, the virtualization interactive terminal.

Type:  'help' for help with commands
       'quit' to quit

virsh # 
```
Create an instance and do live-migration operation to verify.
```bash
openstack server migrate --live [host] [server]
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
>Do this operation on each compute.
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