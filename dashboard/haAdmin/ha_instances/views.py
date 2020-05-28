from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse


from horizon import exceptions
from horizon import tables
from horizon import forms

from openstack_dashboard import api

from openstack_dashboard.dashboards.haAdmin.ha_instances import tables as project_tables
from openstack_dashboard.dashboards.haAdmin.ha_instances\
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
    template_name = 'haAdmin/ha_instances/create.html'    
    success_url = reverse_lazy('horizon:haAdmin:ha_instances:index')
    submit_label = _("Add")
    submit_url = "horizon:haAdmin:ha_instances:add_to_protection"
    page_title = _("Add Instance To Protection")


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdateForm
    form_id = "update_instance_form"
    modal_header = _("Edit Instance")
    template_name = 'haAdmin/ha_instances/update.html'
    success_url = reverse_lazy("horizon:haAdmin:ha_instances:index")
    page_title = _("Update Instance")
    submit_label = _("Save Changes")
    submit_url = "horizon:haAdmin:ha_instances:update"
    
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
            redirect = reverse("horizon:haAdmin:ha_instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)
    
    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        initial.update({'instance_id': self.kwargs['instance_id'],
                        'name': getattr(self._get_object(), 'name', '')})
        return initial


class IndexView(tables.DataTableView):
    table_class = project_tables.InstancesTable
    template_name = 'haAdmin/ha_instances/index.html'
    page_title = _("HA_Instances")

    #def has_more_data(self, table):
        #return self._more

    def get_data(self):
	authUrl = "http://user:0928759204@127.0.0.1:61209"
        #server = xmlrpclib.ServerProxy(authUrl)
	clusters = server.list_cluster()["data"]
        instances = []
	for cluster in clusters:
	    name = cluster["cluster_name"]
	    _cluster_instances = server.list_instance(name)
	    _cluster_instances = Response(code=_cluster_instances["code"], message=_cluster_instances["message"], data=_cluster_instances["data"])
	    result = _cluster_instances.code
	    cluster_instances = _cluster_instances.data.get("instanceList")
	    if result == 'succeed':
		if cluster_instances != "":
		    #cluster_instances = cluster_instances.split(",")
		    for _instance in cluster_instances:
			instance_id = _instance["id"]
			try:
			    instance = api.nova.server_get(self.request, instance_id)
			    instance.cluster_name = name
			    # instance.cluster_id = uuid
			    instances.append(instance)
			except Exception:
			    msg = _('Unable to retrieve instance list.')
			    exceptions.handle(self.request, msg)
		
        marker = self.request.GET.get(
            project_tables.InstancesTable._meta.pagination_param, None)
        search_opts = self.get_filters({'marker': marker, 'paginate': True})
        # Gather our tenants to correlate against IDs
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve instance project information.')
            exceptions.handle(self.request, msg)

        if 'project' in search_opts:
            ten_filter_ids = [t.id for t in tenants
                              if t.name == search_opts['project']]
            del search_opts['project']
            if len(ten_filter_ids) > 0:
                search_opts['tenant_id'] = ten_filter_ids[0]
            else:
                self._more = False
                return []
	"""
        try:
            instances, self._more = api.nova.server_list(
                self.request,
                search_opts=search_opts,
                all_tenants=True)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))
        """
	if instances:
            try:
                api.network.servers_update_addresses(self.request, instances,
                                                     all_tenants=True)
            except Exception:
                exceptions.handle(
                    self.request,
                    message=_('Unable to retrieve IP addresses from Neutron.'),
                    ignore=True)

            # Gather our flavors to correlate against IDs
            try:
                flavors = api.nova.flavor_list(self.request)
            except Exception:
                # If fails to retrieve flavor list, creates an empty list.
                flavors = []

            full_flavors = SortedDict([(f.id, f) for f in flavors])
            tenant_dict = SortedDict([(t.id, t) for t in tenants])
            count = 1 # to count instances number
            # Loop through instances to get flavor and tenant info.
            for inst in instances:
                flavor_id = inst.flavor["id"]
                try:
                    if flavor_id in full_flavors:
                        inst.full_flavor = full_flavors[flavor_id]
                    else:
                        # If the flavor_id is not in full_flavors list,
                        # gets it via nova api.
                        inst.full_flavor = api.nova.flavor_get(
                            self.request, flavor_id)
                except Exception:
                    msg = _('Unable to retrieve instance size information.')
                    exceptions.handle(self.request, msg)
                tenant = tenant_dict.get(inst.tenant_id, None)
		inst.number = count
                inst.tenant_name = getattr(tenant, "name", None)

		cluster_name = inst.cluster_name
	        #result, node_list = server.listNode(cluster_id).split(";")
		cluster_node = server.list_node(cluster_name)
                cluster_node = Response(code=cluster_node["code"], message=cluster_node["message"], data=cluster_node["data"])
		result = cluster_node.code
		node_list = cluster_node.data.get("nodeList")
		cluster_nodes = []
		for node in node_list:
			cluster_nodes.append(node["node_name"])
	        if len(cluster_nodes) == 1:
		    inst.protection = "Incomplete Protected"
	        else:
		    inst.protection = "Protected"
		count = count +1
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

