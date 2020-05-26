
NCU-HASS
===

## Table of Contents

* [Description](#Description)
  * [System Architecture](#System-Architecture)
  * [Requirement](#Requirement)
* [Installation](#Installation)
* [Usage](#Usage)
* [Roadmap](#Roadmap)
* [Contributing](#Contributing)
* [License](#License)
* [Project Status](#Project-Status)

## Description
NCU-HASS is a fault detection and failover system for OpenSatck, which can improve the availability of OpenStack. In OpenStack, users can run services on virtual machines (instances), so the liveness of virtual machines is an important target to be protected by NCU-HASS. In order to protect the virtual machines running on the physical computing nodes and to improve the availability of OpenStack, NCU-HASS will failover all affected virtual machines to other normal computing nodes after detecting the computing node fault, and then try to recover the failed computing node, that is, restart it. If the unexpected termination of the virtual machine is not due to a computing node fault, NCU-HASS will also detect and recover the failed virtual machine (restart it).

Through NCU-HASS, users can create an abstract cluster and add the computing nodes and virtual machines they want to protect to the cluster. NCU-HASS will use Internet Control Message Protocol (ICMP) and Intelligent Platform Management Interface (IPMI) to detect computing node faults, and ICMP and Libvirt to detect virtual machine faults. NCU-HASS logically abstracts the computing nodes into several layers, as shown below. Computing node faults include Power layer, OS layer, and Network layer faults, and virtual machine faults include VM process, guest OS, and guest network faults.

![](https://i.imgur.com/8S3YUAt.png)

NCU-HASS will not modify any OpenStack source code, so as long as OpenStack does not modify the API call method, the OpenStack upgrade will not affect the use of NCU-HASS.

### System Architecture
![](https://i.imgur.com/woxjq8D.png)

### Requirement
The required hardware / software and tested versions are given below:

Hardware:
1.	IPMI supproted machines: HP server (DL380 Gen9, ML30 Gen9), DELL server (PowerEdge T130)

Software:
1.	OS: Ubuntu 16.04
2.	OpenStack: Queen
3.	Python: 2.7

VM:
1. Guest OS: Ubuntu 16.04

Installation
---
Please follow the instructions in the installation guide to complete the installation

Usage
---
There are complete instructions in the user manual to use this project

Roadmap
---
In the next version, the following changes will be made:

1. The part of HASS on the computing node will be merged into the part on the controller node, that is, HASS will only be on the controller node and retain all the features.
2. Based on the first change, HASS will be able to tolerate detector fault and unsupported. Users can select the layer they want to protect. Among them, when users want to protect computing nodes and virtual machines, the network layer and the guest network layer will be automatically selected and cannot be canceled. In addition, HASS can make the correct detection even when detector fails. In addition, even if the detector fails (except for the network layer and the guest network layer), HASS can still correctly detect the fault and fail over the virtual machine.
3. Based on the first change, HASS allows users to shut down / boot / reboot / migrate / delete virtual machines protected by HASS.

Contributing
---
Currently, the project does not accept any contribution.

License
---
[BSD 3-Clause](https://opensource.org/licenses/BSD-3-Clause)

Project Status
---
We are constantly updating the version. (2020/5/16)
