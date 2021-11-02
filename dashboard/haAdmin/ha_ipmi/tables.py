#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.utils.translation import ungettext_lazy

from django import template
from django.template.defaultfilters import title  # noqa

from horizon.utils import filters

import xmlrpclib

from horizon import tables
from horizon import messages

from openstack_dashboard import api

class Response(object):
    def __init__(self, code, message=None, data=None):
        self.code = code
	self.message = message
	self.data = data

class GetNodeInfoAction(tables.LinkAction):
    name = "nodeInfo"
    verbose_name = _("Get Node Info")
    url = "horizon:haAdmin:ha_ipmi:detail"
    classes = ("btn-log",)


class StartNodeAction(tables.BatchAction):
    name = "start"
    classes = ('btn-confirm',)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Start Node",
            u"Start Nodes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Started Node",
            u"Started Nodes",
            count
        )

    def allowed(self, request, computing_node):
        # check cn's power status
    	return (computing_node.state != "up")

    def action(self, request, obj_id):
        authUrl = "http://user:0928759204@127.0.0.1:61209"
        server = xmlrpclib.ServerProxy(authUrl)
        result = server.startNode(obj_id)
	result = Response(code=result["code"], message=result["message"], data=result["data"])
        if result.code == "failed":
            err_msg = result.message
            messages.error(request, err_msg)

class RebootNodeAction(tables.DeleteAction):

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Reboot Node",
            u"Reboot Nodes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Rebooted Node",
            u"Rebooted Nodes",
            count
        )
    
    def action(self, request, obj_id):
        authUrl = "http://user:0928759204@127.0.0.1:61209"
        server = xmlrpclib.ServerProxy(authUrl)
        result = server.rebootNode(obj_id)
	result = Response(code=result["code"], message=result["message"], data=result["data"])
        if result.code == "failed":
            err_msg = result.message
            messages.error(request, err_msg)

class ShutOffNodeAction(tables.BatchAction):
    name = "shutoff"
    classes = ('btn-reboot',)
    help_text = _("Restarted instances will lose any data"
                  " not saved in persistent storage.")
    action_type = "danger"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Shut off Node",
            u"Shut off Nodes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Shut offed Node",
            u"Shut offed Nodes",
            count
        )

    def allowd(self, request, computing_node):
        return (computing_node.state != "down")

    def action(self, request, obj_id):
        authUrl = "http://user:0928759204@127.0.0.1:61209"
        server = xmlrpclib.ServerProxy(authUrl)
        result = server.shutOffNode(obj_id)
	result = Response(code=result["code"], message=result["message"], data=result["data"])
        if result.code == "failed":
            err_msg = result.message
            messages.error(request, err_msg)


class Ipmi_CN_Table(tables.DataTable):
    
    STATUS_CHOICES = (
        ("enabled", True),
        ("disabled", False),
        ("up", True),
        ("down", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ("enabled", pgettext_lazy("Current status of a Hypervisor",
                                  u"Enabled")),
        ("disabled", pgettext_lazy("Current status of a Hypervisor",
                                   u"Disabled")),
        ("up", pgettext_lazy("Current state of a Hypervisor",
                             u"Up")),
        ("down", pgettext_lazy("Current state of a Hypervisor",
                               u"Down")),
    )
    
    hostname = tables.Column("hypervisor_hostname",
                                     link="horizon:haAdmin:ha_ipmi:detail",
                                     verbose_name=_("Node name"))    
    status = tables.Column('status',
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES,
                           verbose_name=_('Nova Compute Status'))
    state = tables.Column('state',
                          status=True,
                          status_choices=STATUS_CHOICES,
                          display_choices=STATUS_DISPLAY_CHOICES,
                          verbose_name=_('Power State'))
    
    def get_object_id(self, hypervisor):
        return "%s" % (hypervisor.hypervisor_hostname)

    class Meta:
        name = "ha_ipmi_overview"
        verbose_name = _("HA_IPMI")
        #table_actions = (AddInstanceToProtectionAction,)
	row_actions = (StartNodeAction, ShutOffNodeAction, RebootNodeAction, GetNodeInfoAction)
        #row_actions = (StartNodeAction, ShutOffNodeAction, RebootNodeAction)

class IPMINodeTemperatureTable(tables.DataTable):

    sensor = tables.Column("sensor_ID", verbose_name=_("Sensor ID"))

    device = tables.Column("device", verbose_name=_("Device"))

    value = tables.Column("value", verbose_name=_("Value"))

    lc = tables.Column("lower_critical", verbose_name=_("Lower Critical"))

    uc = tables.Column("upper_critical", verbose_name=_("Upper Critical"))  

    class Meta:
        name = "IPMI_Temp"
        hidden_title = False
        verbose_name = _("Temperature")

class IPMINodeVoltageTable(tables.DataTable):
	
    sensor = tables.Column("sensor_ID", verbose_name=_("Sensor"))

    device = tables.Column("device", verbose_name=_("Device"))

    value = tables.Column("value", verbose_name=_("Value"))

    class Meta:
        name = "IPMI_Volt"
        hidden_title = False
        verbose_name = _("Voltage")

