from django.utils.translation import ugettext_lazy as _
#from django.utils.datastructures import SortedDict
from collections import OrderedDict as SortedDict
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import tables
from horizon import forms

from openstack_dashboard import api

from openstack_dashboard.dashboards.haProject.ha_instances import tables as project_tables
from openstack_dashboard.dashboards.haProject.ha_instances\
    import forms as project_forms


from openstack_dashboard.REST.RESTClient import RESTClient
server = RESTClient.get_instance()

class Response(object):
	def __init__(self, code, message=None, data=None):
		self.code = code
		self.message = message
		self.data = data

class AddView(forms.ModalFormView):
    form_class = project_forms.AddForm
    template_name = 'haProject/ha_instances/create.html'
    success_url = reverse_lazy('horizon:haProject:ha_instances:index')
    submit_label = _("Add")
    submit_url = "horizon:haProject:ha_instances:add_to_protection"
    page_title = _("Add Instance To Protection")


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdateForm
    form_id = "update_instance_form"
    modal_header = _("Edit Instance")
    template_name = 'haProject/ha_instances/update.html'
    success_url = reverse_lazy("horizon:haProject:ha_instances:index")
    page_title = _("Update Instance")
    submit_label = _("Save Changes")
    submit_url = "horizon:haProject:ha_instances:update"

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.kwargs['instance_id'],)
        context["instance_id"] = self.kwargs['instance_id']
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def _get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            return api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse("horizon:haProject:ha_instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        initial.update({'instance_id': self.kwargs['instance_id'],
                        'name': getattr(self._get_object(), 'name', '')})
        return initial



class IndexView(tables.DataTableView):
    table_class = project_tables.InstancesTable
    template_name = 'haProject/ha_instances/index.html'
    page_title = _("HA_Instances")

    def get_data(self):
	authUrl = "http://user:0928759204@127.0.0.1:61209"
        #server = xmlrpclib.ServerProxy(authUrl)
        clusters = server.list_cluster()["data"]
        instances = []
        ha_instances = []
	for cluster in clusters:
	    uuid = cluster["cluster_name"]
	    name = cluster["cluster_name"]
            _cluster_instances = server.list_instance(name)
            _cluster_instances = Response(code=_cluster_instances["code"], message=_cluster_instances["message"], data=_cluster_instances["data"])
            #result,cluster_instances = _cluster_instances.split(";")
	    result = _cluster_instances.code
	    cluster_instances = _cluster_instances.data.get("instanceList")
            if result == 'succeed':
                if cluster_instances != "":
		    for _instance in cluster_instances:
                    #cluster_instances = cluster_instances.split(",")
                    #for _instance_id in cluster_instances:
                        instance_id = _instance["id"]
                        try:
                            instance = api.nova.server_get(self.request, instance_id)
                            instance.cluster_name = name
                            instance.cluster_id = uuid
                            ha_instances.append(instance)
                        except Exception:
                            msg = _('Unable to retrieve instance list.')
                            exceptions.handle(self.request, msg)

        marker = self.request.GET.get(
            project_tables.InstancesTable._meta.pagination_param, None)
        search_opts = self.get_filters({'marker': marker, 'paginate': True})
        # Gather our tenants to correlate against IDs
        
	try:
            total_instances, self._more = api.nova.server_list(
                self.request,
                search_opts=search_opts)
        except Exception:
            self._more = False
            total_instances = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instances.'))	
	
	for instance in ha_instances:
	    print instance
	    for _instance in total_instances:
	    	if instance.id == _instance.id:
		    instances.append(instance)
        if instances:
            try:
                api.network.servers_update_addresses(self.request, instances)
            except Exception:
                exceptions.handle(
                    self.request,
                    message=_('Unable to retrieve IP addresses from Neutron.'),
                    ignore=True)

            # Gather our flavors and images and correlate our instances to them
            try:
                flavors = api.nova.flavor_list(self.request)
            except Exception:
                flavors = []
                exceptions.handle(self.request, ignore=True)

            try:
                # TODO(gabriel): Handle pagination.
                images, more, prev = api.glance.image_list_detailed(
                    self.request)
            except Exception:
                images = []
                exceptions.handle(self.request, ignore=True)

            full_flavors = SortedDict([(str(flavor.id), flavor)
                                       for flavor in flavors])
            image_map = SortedDict([(str(image.id), image)
                                    for image in images])

            # Loop through instances to get flavor info.
            for instance in instances:
                if hasattr(instance, 'image'):
                    # Instance from image returns dict
                    if isinstance(instance.image, dict):
                        if instance.image.get('id') in image_map:
                            instance.image = image_map[instance.image['id']]

                try:
                    flavor_id = instance.flavor["id"]
                    if flavor_id in full_flavors:
                        instance.full_flavor = full_flavors[flavor_id]
                    else:
                        # If the flavor_id is not in full_flavors list,
                        # get it via nova api.
                        instance.full_flavor = api.nova.flavor_get(
                            self.request, flavor_id)
                except Exception:
                    msg = ('Unable to retrieve flavor "%s" for instance "%s".'
                           % (flavor_id, instance.id))
                    LOG.info(msg)
        return instances

    def get_filters(self, filters):
        filter_action = self.table._meta._filter_action
        if filter_action:
            filter_field = self.table.get_filter_field()
            if filter_action.is_api_filter(filter_field):
                filter_string = self.table.get_filter_string()
                if filter_field and filter_string:
                    filters[filter_field] = filter_string
        return filters
