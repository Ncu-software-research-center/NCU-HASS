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
