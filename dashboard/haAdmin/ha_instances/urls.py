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

#from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.haAdmin.ha_instances.views \
    import IndexView
from openstack_dashboard.dashboards.haAdmin.ha_instances.views \
    import UpdateView
from openstack_dashboard.dashboards.haAdmin.ha_instances.views \
    import AddView

INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'

urlpatterns = [#patterns(
    #'',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^add_to_protection/$', AddView.as_view(), name='add_to_protection'),
    url(INSTANCES % 'update',
        UpdateView.as_view(),
        name='update'), 
#)
]
