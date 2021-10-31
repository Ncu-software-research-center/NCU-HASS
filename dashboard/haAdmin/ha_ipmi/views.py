from django.utils.translation import ugettext_lazy as _
#from django.utils.datastructures import SortedDict
from collections import OrderedDict as SortedDict
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse

from horizon import tabs
from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon.utils import functions as utils

from openstack_dashboard import api
from openstack_dashboard.api import nova

from openstack_dashboard.dashboards.haAdmin.ha_ipmi import tables as project_tables

import xmlrpclib

class Temperature:
    def __init__(self, id, sensor_ID, device, value, lower_critical, upper_critical):
        self.id = id
        self.sensor_ID = sensor_ID
        self.device = device
        self.value = value
        self.lower_critical = lower_critical
        self.upper_critical = upper_critical

class Voltage:
    def __init__(self, id, sensor_ID, device, value):
        self.id = id
        self.sensor_ID = sensor_ID
        self.device = device
        self.value = value

class IndexView(tables.DataTableView):
    table_class = project_tables.Ipmi_CN_Table
    template_name = 'haAdmin/ha_ipmi/index.html'
    page_title = _("HA_IPMI_Node")

    def get_data(self):
        hypervisors = []
        try:
            hypervisors = nova.hypervisor_list(self.request)
            hypervisors.sort(key=utils.natural_sort('hypervisor_hostname'))
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve hypervisor information.'))
        return hypervisors

class DetailView(tables.MultiTableView):
    table_classes = (project_tables.IPMINodeTemperatureTable, project_tables.IPMINodeVoltageTable)
    template_name = 'haAdmin/ha_ipmi/detail.html'
    page_title = _("IPMI-based Node : {{node_id}}")
    
    volt_list = []

    def get_IPMI_Temp_data(self):
        authUrl = "http://user:0928759204@127.0.0.1:61209"
        server = xmlrpclib.ServerProxy(authUrl)
        result = server.getAllInfoOfNode(self.kwargs["node_id"])
        self.volt_list = []
        temp_data = []
        #if correct == "0":
        data_id = 0
        for data in result:
            if "Temp" in data[0]:
                temp_data.append(Temperature(data_id, data[0], data[1], data[2], data[3], data[4]))
                data_id = data_id + 1
            else:
                self.volt_list.append(data)
        return temp_data

    def get_IPMI_Volt_data(self):
        volt_data = []
        volt_id = 0
        for volt in self.volt_list:
            volt_data.append(Voltage(volt_id, volt[0], volt[1], volt[2]))
            volt_id = volt_id + 1
        return volt_data

