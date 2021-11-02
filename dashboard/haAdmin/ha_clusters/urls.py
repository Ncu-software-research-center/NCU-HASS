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

from openstack_dashboard.dashboards.haAdmin.ha_clusters.views \
    import IndexView
from openstack_dashboard.dashboards.haAdmin.ha_clusters.views \
    import DetailView
from openstack_dashboard.dashboards.haAdmin.ha_clusters.views \
    import CreateView
from openstack_dashboard.dashboards.haAdmin.ha_clusters.views \
    import AddView

CLUSTERS = r'^(?P<cluster_name>[^/]+)/%s$'

urlpatterns = [#patterns(
    #'openstack_dashboard.dashboards.haAdmin.ha_clusters.views',
    url(r'^create/$',
        CreateView.as_view(), name='create'),
    url(r'^(?P<cluster_name>[^/]+)/$',
        DetailView.as_view(), name='detail'),
    url(r'^(?P<cluster_name>[^/]+)/add_node/$',
        AddView.as_view(), name='add_node'),
    url(r'^$', IndexView.as_view(), name='index'),
#)
]
