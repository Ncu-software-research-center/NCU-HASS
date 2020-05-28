from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.haAdmin import dashboard


class HA_Ipmi(horizon.Panel):
    name = _("HA IPMI")
    slug = "ha_ipmi"
    #permissions = ('openstack.services.compute')


dashboard.HA_Admin.register(HA_Ipmi)
