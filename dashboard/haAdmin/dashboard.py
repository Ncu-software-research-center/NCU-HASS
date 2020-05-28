from django.utils.translation import ugettext_lazy as _

import horizon

class HA_Admin(horizon.Dashboard):
    name = _("HA Admin")
    slug = "haAdmin"
    default_panel = 'ha_instances'
    panels = ('ha_clusters','ha_instances')
    permissions = ('openstack.roles.admin',)

horizon.register(HA_Admin)

