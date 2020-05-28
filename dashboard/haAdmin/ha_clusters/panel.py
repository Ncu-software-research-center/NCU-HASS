from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.haAdmin import dashboard


class HA_Clusters(horizon.Panel):
    name = _("HA Clusters")
    slug = "ha_clusters"
    #permissions = ('openstack.services.compute')


dashboard.HA_Admin.register(HA_Clusters)
