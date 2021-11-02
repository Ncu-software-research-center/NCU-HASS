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

from django import template
from django.template.defaultfilters import title  # noqa

from horizon.utils import filters


from horizon import tables



POWER_STATES = {
    0: "NO STATE",
    1: "RUNNING",
    2: "BLOCKED",
    3: "PAUSED",
    4: "SHUTDOWN",
    5: "SHUTOFF",
    6: "CRASHED",
    7: "SUSPENDED",
    8: "FAILED",
    9: "BUILDING",
}

class AddInstanceToProtectionAction(tables.LinkAction):
    name = "add_to_protection"
    verbose_name = _("Add Instance to Protection")
    url = "horizon:haAdmin:ha_instances:add_to_protection"
    classes = ("ajax-modal",)
    icon = "plus"


class EditInstanceProtectionAction(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Protection")
    url = "horizon:haAdmin:ha_instances:update"
    classes = ("ajax-modal",)
    icon = "pencil"
     

def get_ips(instance):
    template_name = 'haAdmin/ha_instances/_instance_ips.html'
    ip_groups = {}

    for ip_group, addresses in instance.addresses.iteritems():
        ip_groups[ip_group] = {}
        ip_groups[ip_group]["floating"] = []
        ip_groups[ip_group]["non_floating"] = []

        for address in addresses:
            if ('OS-EXT-IPS:type' in address and
               address['OS-EXT-IPS:type'] == "floating"):
                ip_groups[ip_group]["floating"].append(address)
            else:
                ip_groups[ip_group]["non_floating"].append(address)

    context = {
        "ip_groups": ip_groups,
    }
    return template.loader.render_to_string(template_name, context)

def get_power_state(instance):
    return POWER_STATES.get(getattr(instance, "OS-EXT-STS:power_state", 0), '')

POWER_DISPLAY_CHOICES = (
    ("NO STATE", pgettext_lazy("Power state of an Instance", u"No State")),
    ("RUNNING", pgettext_lazy("Power state of an Instance", u"Running")),
    ("BLOCKED", pgettext_lazy("Power state of an Instance", u"Blocked")),
    ("PAUSED", pgettext_lazy("Power state of an Instance", u"Paused")),
    ("SHUTDOWN", pgettext_lazy("Power state of an Instance", u"Shut Down")),
    ("SHUTOFF", pgettext_lazy("Power state of an Instance", u"Shut Off")),
    ("CRASHED", pgettext_lazy("Power state of an Instance", u"Crashed")),
    ("SUSPENDED", pgettext_lazy("Power state of an Instance", u"Suspended")),
    ("FAILED", pgettext_lazy("Power state of an Instance", u"Failed")),
    ("BUILDING", pgettext_lazy("Power state of an Instance", u"Building")),
)

class InstancesTable(tables.DataTable):
    
    number = tables.Column("number", verbose_name=_("#"))
    
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))

    host = tables.Column("OS-EXT-SRV-ATTR:host",
                         verbose_name=_("Host"),
                         classes=('nowrap-col',))    
 
    name = tables.Column("name",
                         link="horizon:project:instances:detail",
                         verbose_name=_("Instance Name"))
    
    # cluster_id = tables.Column("cluster_id", hidden=True, verbose_name=_("Cluster ID"))
    
    cluster_name = tables.Column("cluster_name",
				 verbose_name=_("Cluster"))

    protection = tables.Column("protection",
				verbose_name=_("Protection"))

    ip = tables.Column(get_ips,
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})

    state = tables.Column(get_power_state,
                          filters=(title, filters.replace_underscores),
                          verbose_name=_("Power State"),
                          display_choices=POWER_DISPLAY_CHOICES)

    created = tables.Column("created",
			    verbose_name=_("Time since created"),
			    filters=(filters.parse_isotime,
				     filters.timesince_sortable),
			    attrs={'data-type': 'timesince'})
    """
    name = tables.Column('name', \
                         verbose_name=_("Name"))
    status = tables.Column('status', \
                           verbose_name=_("Status"))
    zone = tables.Column('availability_zone', \
                         verbose_name=_("Availability Zone"))
    image_name = tables.Column('image_name', \
                               verbose_name=_("Image Name"))
    """
    class Meta:
        name = "ha_instances"
        verbose_name = _("HA_Instances")
	table_actions = (AddInstanceToProtectionAction,)
	row_actions = (EditInstanceProtectionAction,)
