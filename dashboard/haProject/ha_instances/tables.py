from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy

from django import template
from django.template.defaultfilters import title  # noqa

from horizon.utils import filters


from horizon import tables

from openstack_dashboard import api


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
    url = "horizon:haProject:ha_instances:add_to_protection"
    classes = ("ajax-modal",)
    icon = "plus"


class EditInstanceProtectionAction(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Protection")
    url = "horizon:haProject:ha_instances:update"
    classes = ("ajax-modal",)
    icon = "pencil"
     

def get_ips(instance):
    template_name = 'haProject/ha_instances/_instance_ips.html'
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
    name = tables.Column("name",
                         link="horizon:project:instances:detail",
                         verbose_name=_("Instance Name"))
    
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
