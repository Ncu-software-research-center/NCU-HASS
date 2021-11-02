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
from django.utils.translation import ungettext_lazy
from django.core import urlresolvers

from django import shortcuts

from horizon import tables
from horizon import messages

from openstack_dashboard.REST.RESTClient import RESTClient
server = RESTClient.get_instance()

class DeleteHACluster(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete HA Cluster",
            u"Delete HA Clusters",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted HA Cluster",
            u"Deleted HA Clusters",
            count
        )
    def handle(self, table, request, obj_ids):
	name = []
	for uuid in obj_ids:
            table_cluster_name = self.table.get_object_by_id(uuid).cluster_name # get cluster's name
    	    name.append(table_cluster_name)
            result = server.delete_cluster(table_cluster_name)
            if result["code"] == "failed":
    	        err_msg = result["message"]
    	        messages.error(request, err_msg)
    	        return False
	success_message = _('Deleted HA Cluster: %s' ) % ",".join(name)
	messages.success(request, success_message)
	return shortcuts.redirect(self.get_success_url(request))

class DeleteComputingNode(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Computing Node",
            u"Delete Computing Nodes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Computing Node",
            u"Deleted Computing Nodes",
            count
        )


    def handle(self, table, request, obj_ids):
	authUrl = "http://user:0928759204@127.0.0.1:61209"
        #server = xmlrpclib.ServerProxy(authUrl)	
	cluster_name = self.table.kwargs["cluster_name"]
	node_names = []
	for obj_id in obj_ids:
	    node_name = self.table.get_object_by_id(obj_id).computing_node_name
            result = server.delete_node(cluster_name, node_name)
	    node_names.append(node_name)
            if result["code"] == 'failed':
	        err_msg = result["message"]
                messages.error(request, err_msg)
                return False
	self.success_message = _("Deleted Computing Node: %s " % ",".join(node_names))
	messages.success(request, self.success_message)
        return shortcuts.redirect(self.get_success_url(request))

class CreateHAClusterAction(tables.LinkAction):
    name = "create"
    verbose_name = _("Create HA Cluster")
    url = "horizon:haAdmin:ha_clusters:create"
    classes = ("ajax-modal",)
    icon = "plus"

class AddComputingNodeAction(tables.LinkAction):
    name = "add_node"
    verbose_name = _("Add Computing Node")
    url = "horizon:haAdmin:ha_clusters:add_node"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum=None):
        cluster_name = self.table.kwargs["cluster_name"]
	print urlresolvers.reverse(self.url,args=[cluster_name])
        return urlresolvers.reverse(self.url, args=[cluster_name])

class ClustersTable(tables.DataTable):
    #message_list = "1234567"
    name = tables.Column("cluster_name",
			 link="horizon:haAdmin:ha_clusters:detail",
 	                 verbose_name=_("Cluster Name"))
    
    computing_number = tables.Column("computing_node_number", verbose_name=_("# of Computing nodes"))

    instance_number = tables.Column("instance_number", verbose_name=_("# of Instances"))
    
    class Meta:
        name = "ha_clusters"
        verbose_name = _("HA_Clusters")
	table_actions = (CreateHAClusterAction, DeleteHACluster)
	row_actions = (DeleteHACluster,)

class ClusterDetailTable(tables.DataTable):

    name = tables.Column("computing_node_name", verbose_name=_("Computing Node Name"))

    instance_number = tables.Column("instance_number", verbose_name=_("# of Instances"))

    class Meta:
	name = "cluster_detail"
	hidden_title = False
	verbose_name = _("Computing Nodes")
        table_actions = (AddComputingNodeAction, DeleteComputingNode) 
	row_actions = (DeleteComputingNode,)

