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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows
from horizon import messages
from django.core import urlresolvers


from openstack_dashboard import api

import xmlrpclib
import re

from openstack_dashboard.REST.RESTClient import RESTClient
server = RESTClient.getInstance()

class SetHAClusterInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"),
                           max_length=255)

    class Meta(object):
        name = _("HA Cluster Information")
        help_text = _("Described HA Cluster here")
        slug = "set_ha_cluster_info"

    def clean(self):
        cleaned_data = super(SetHAClusterInfoAction, self).clean()
        name = cleaned_data.get('name')
        return cleaned_data


class SetHAClusterInfoStep(workflows.Step):
    action_class = SetHAClusterInfoAction
    contributes = ('name',)


class AddHostsToHAClusterAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(AddHostsToHAClusterAction, self).__init__(request,
                                                        *args,
                                                        **kwargs)
        err_msg = _('Unable to get the available hosts')

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        hosts = []
        try:
            hosts = api.nova.host_list(request)
        except Exception:
            exceptions.handle(request, err_msg)

        host_names = []
        for host in hosts:
            if host.host_name not in host_names and host.service == u'compute':
                host_names.append(host.host_name)
        host_names.sort()

        self.fields[field_name].choices = \
            [(host_name, host_name) for host_name in host_names]

    class Meta(object):
        name = _("Computing Nodes")
        slug = "add_host_to_ha_cluster"

class AddNodesToHAClusterAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(AddNodesToHAClusterAction, self).__init__(request,
                                                        *args,
                                                        **kwargs)
        err_msg = _('Unable to get the available hosts')

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        hosts = []
        try:
            hosts = api.nova.host_list(request)
        except Exception:
            exceptions.handle(request, err_msg)

        host_names = []
        for host in hosts:
            if host.host_name not in host_names and host.service == u'compute':
                host_names.append(host.host_name)
        host_names.sort()

        self.fields[field_name].choices = \
            [(host_name, host_name) for host_name in host_names]

    class Meta(object):
        name = _("Computing Nodes")
        slug = "add_node_to_ha_cluster"

class AddHostsToHAClusterStep(workflows.UpdateMembersStep):
    action_class = AddHostsToHAClusterAction
    help_text = _("Select the computing nodes which are unused. If no computing nodes are "
                  "selected, then the cluster still can be created.")
    available_list_title = _("All available hosts")
    members_list_title = _("Selected hosts")
    no_available_text = _("No hosts found.")
    no_members_text = _("No host selected.")
    show_roles = False
    contributes = ("computing_nodes",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['computing_nodes'] = data.get(member_field_name, [])
        return context
   
class AddComputingNodesToHAClusterStep(workflows.UpdateMembersStep):
    action_class = AddHostsToHAClusterAction
    help_text = _("Select the computing nodes which are unused.")
    available_list_title = _("All available hosts")
    members_list_title = _("Selected hosts")
    no_available_text = _("No hosts found.")
    no_members_text = _("No host selected.")
    show_roles = False
    contributes = ("computing_nodes",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['computing_nodes'] = data.get(member_field_name, [])
        return context

class CreateHAClusterWorkflow(workflows.Workflow):
    slug = "create_ha_cluster"
    name = _("Create HA Cluster")
    finalize_button_name = _("Create")
    success_message = _('Created new HA cluster "%s".')
    failure_message = _('Unable to create HA cluster "%s".')
    success_url = "horizon:haAdmin:ha_clusters:index"
    default_steps = (SetHAClusterInfoStep, AddHostsToHAClusterStep)

    def handle(self, request, context):
	authUrl = "http://user:0928759204@127.0.0.1:61209"
        #server = xmlrpclib.ServerProxy(authUrl)	

	context_computing_nodes = context['computing_nodes']
	name = context['name']
	node_list = []
	for node in context_computing_nodes:
	    node_list.append(node)
	   
        result = server.create_cluster(name, node_list)
	if 'overlapping node' in result["message"]:
	    self.failure_message = result["message"]
	    return False
	self.success_message = _('Created new HA cluster "%s".'  % name)
        return True

class AddComputingNodeWorkflow(workflows.Workflow):
    slug = "add_computing_node"
    name = _("Add Computing Node")
    finalize_button_name = _("Add")
    success_message = _('Add new Computing Node to HA cluster "%s".')
    failure_message = _('Unable to add new Computing Node "%s".')
    success_url = "horizon:haAdmin:ha_clusters:detail"
    default_steps = (AddComputingNodesToHAClusterStep,)

    def handle(self, request, context): 
        authUrl = "http://user:0928759204@127.0.0.1:61209"
        #server = xmlrpclib.ServerProxy(authUrl)	
        context_computing_nodes = context['computing_nodes']
        node_list = []
        for node in context_computing_nodes:
            node_list.append(node)
        cluster_id = self.get_cluster_id(self.get_absolute_url())
        result = server.add_node(cluster_id,node_list)
        self.success_url = urlresolvers.reverse(self.success_url, args=[cluster_id])
        if result["code"] == 'failed': # error
            self.failure_message = result["message"]
            messages.error(request, result["message"])
            return False
        self.success_message = _('Add new Computing Node %s to HA Cluster.' % (",".join(node_list)))
        messages.success(request, self.success_message )
        return True

    def get_cluster_id(self,full_url): # get cluster's id by url
        return full_url.split("/")[4]	
