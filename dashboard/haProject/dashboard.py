from django.utils.translation import ugettext_lazy as _

import horizon

class HA_Project(horizon.Dashboard):
    name = _("HA Project")
    slug = "haProject"
    default_panel = 'ha_instances'
    panels = ('ha_instances',)


horizon.register(HA_Project)

