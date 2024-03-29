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
import logging

from openstack_dashboard.REST.RESTClient import RESTClient
server = RESTClient.get_instance()

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
            hosts = api.nova.hypervisor_list(request)
        except Exception:
            exceptions.handle(request, err_msg)

        host_names = []
        unavail_hosts = []

        cluster_list = server.list_cluster()
        for x in cluster_list['data']:
            res = server.list_node(x['cluster_name'])
            for nodeList in res['data']['nodeList']:
                unavail_hosts.append(nodeList['node_name'])

        for hypervisor in hosts:
            if hypervisor.hypervisor_hostname not in host_names and hypervisor.hypervisor_hostname not in unavail_hosts and hypervisor.state == 'up':
                host_names.append(str(hypervisor.hypervisor_hostname))
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

class SelectLayerAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(SelectLayerAction, self).__init__(request, *args, **kwargs)

        layer_option_list = [('1', 'Power'),
                          ('2', 'Hardware'),
                          ('3', 'OS'),
                          ('4', 'Network'),
                          ('5', 'VM process'),
                          ('6', 'Guest OS'),
                          ('7', 'VM network'),]

        super(SelectLayerAction, self).__init__(request, *args, **kwargs)

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)
        self.fields[field_name].choices = layer_option_list


    class Meta(object):
            name = _("Layer Option")

class SelectLayerStep(workflows.UpdateMembersStep):
    action_class = SelectLayerAction
    show_roles = False
    help_text = _("Select layer that you want to be detected in selected host. If no layers are selected, all layers will be choosen by default.")
    available_list_title = _("All Layers")
    members_list_title = _("Selected Layers")
    no_members_text = _("No Layer Selected.")
    contributes = ("layers",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['layers'] = data.get(member_field_name, [])
        return context

class SetLayerOptionAction(workflows.Action):
    vm_network = forms.BooleanField(label=_("VM Network Layer"),required=False, initial=True, help_text = 'This is mandatory layer, automatically selected')
    guest_os = forms.BooleanField(label=_("Guest OS Layer"),required=False, initial=True)
    vm_process = forms.BooleanField(label=_("VM Process Layer"),required=False, initial=True)
    network = forms.BooleanField(label=_("Network Layer"),required=False, initial=True, help_text = 'This is mandatory layer, automatically selected')
    os = forms.BooleanField(label=_("OS Layer"),required=False, initial=True)
    hardware = forms.BooleanField(label=_("Hardware Layer"),required=False, initial=True)
    power = forms.BooleanField(label=_("Power Layer"),required=False, initial=True)

    vm_network.widget.attrs['disabled'] = True
    network.widget.attrs['disabled'] = True

    class Meta(object):
        name = _("Layer Option")
        help_text = _("Select the layer that you want to be detected in selected host")

    def clean(self):
        layer_data = super(SetLayerOptionAction, self).clean()
        # logging.error(layer_data)
        layer_data['vm_network'] = True
        layer_data['network'] = True
        return layer_data


class SetLayerOptionStep(workflows.Step):
    action_class = SetLayerOptionAction
    contributes = ('power', 'hardware', 'os', 'network', 'vm_process', 'guest_os', 'vm_network',)

class CreateHAClusterWorkflow(workflows.Workflow):
    slug = "create_ha_cluster"
    name = _("Create HA Cluster")
    finalize_button_name = _("Create")
    success_message = _('Created new HA cluster "%s".')
    failure_message = _('Unable to create HA cluster "%s".')
    success_url = "horizon:haAdmin:ha_clusters:index"
    default_steps = (SetHAClusterInfoStep, AddHostsToHAClusterStep, SetLayerOptionStep)

    def handle(self, request, context):
        # logging.error(context)
    	context_computing_nodes = context['computing_nodes']
    	name = context['name']
        context_layer = [context['power'],context['hardware'],context['os'],context['network'],context['vm_process'],context['guest_os'],context['vm_network']]
        layers_string = ''
        for layer in context_layer:
            if layer == True :
                layers_string += '1'
            else :
                layers_string += '0'
    	node_list = []
        # logging.error(layers_string)
    	for node in context_computing_nodes:
    	    node_list.append(node)
        result = server.create_cluster(name, node_list, layers_string)
    	if 'overlapping node' in result["message"] or result["code"] == "failed":
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
