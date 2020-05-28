from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.haProject import dashboard


class HA_Instances(horizon.Panel):
    name = _("HA Instances")
    slug = "ha_instances"
    #permissions = ('openstack.services.compute')


dashboard.HA_Project.register(HA_Instances)
