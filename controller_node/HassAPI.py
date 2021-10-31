#########################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   Command Line Interface for users.
##########################################################
import xmlrpclib
import ConfigParser
import argparse
from Response import Response

from enum import Enum
from prettytable import PrettyTable


def enum(**enums):
    return type('Enum', (), enums)


class HassAPI():
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.authUrl = "http://" + self.config.get("rpc", "rpc_username") + ":" + self.config.get("rpc",
                                                                                                  "rpc_password") + "@127.0.0.1:" + self.config.get(
            "rpc", "rpc_bind_port")
        self.server = xmlrpclib.ServerProxy(self.authUrl)
        self.HASS_result = None
        # global variable for sensor get mapping
        self.TABLE = enum(CLUSTER='cluster', NODE='node', INSTANCE='instance')
        self.bcolors()

    def generateSensorTable(self, result):
        if result == []: raise Exception("There is no information")
        sensor_table = PrettyTable(
            ["Sensor ID", "Entity ID", "Sensor Type", "Value", "status", "lower_critical", "lower", "upper",
             "upper_critical"])
        for value in result:
            sensor_table.add_row(value)
        print sensor_table

    def bcolors(self):
        self.OK_color = '\033[92m'
        self.ERROR_color = '\033[91m'
        self.END_color = '\033[0m'

    def showResult(self, result):
        result = Response(code=result["code"], message=result["message"], data=result["data"])
        if result.code == "succeed":
            return self.OK_color + "[Success] " + self.END_color + result.message
        else:
            return self.ERROR_color + "[Error] " + self.END_color + result.message

    def showTable(self, result, type):
        # cluster list info
        if type == self.TABLE.CLUSTER:
            self.cluster_table = PrettyTable(['UUID', 'Name'])
            for (uuid, name) in result:
                self.cluster_table.add_row([uuid, name])
            print self.cluster_table
        # node list info
        elif type == self.TABLE.NODE:
            self.node_table = PrettyTable(["name", "cluster_id", "ipmi_enabled"])
            for name, cluster_id, ipmi_status in result:
                self.node_table.add_row([name, cluster_id, ipmi_status])
            print self.node_table
        elif type == self.TABLE.INSTANCE:
            self.instance_table = PrettyTable(["id", "name", "host", "state", "network"])
            for id, name, host, state, network in result:
                self.instance_table.add_row([id, name, host, state, network])
            print self.instance_table

    def Input_Command(self):
        self.parser = argparse.ArgumentParser(description='Openstack high availability software service(HASS)')
        self.subparsers = self.parser.add_subparsers(help='functions of HASS', dest='command')

        self.parser_cluster_create = self.subparsers.add_parser('cluster-create', help='Create a HA cluster')
        self.parser_cluster_create.add_argument("-n", "--name", help="HA cluster name", required=True)
        self.parser_cluster_create.add_argument("-c", "--nodes",
                                                help="Computing nodes you want to add to cluster. Use ',' to separate nodes name")

        self.parser_cluster_delete = self.subparsers.add_parser('cluster-delete', help='Delete a HA cluster')
        self.parser_cluster_delete.add_argument("-i", "--uuid", help="Cluster uuid you want to delete", required=True)

        self.parser_cluster_list = self.subparsers.add_parser('cluster-list', help='List all HA cluster')

        self.parser_node_add = self.subparsers.add_parser('node-add', help='Add computing node to HA cluster')
        self.parser_node_add.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
        self.parser_node_add.add_argument("-c", "--nodes",
                                          help="Computing nodes you want to add to cluster. Use ',' to separate nodes name",
                                          required=True)

        self.parser_node_delete = self.subparsers.add_parser('node-delete',
                                                             help='Delete computing node from HA cluster')
        self.parser_node_delete.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
        self.parser_node_delete.add_argument("-c", "--node", help="A computing node you want to delete from cluster.",
                                             required=True)

        self.parser_node_list = self.subparsers.add_parser('node-list', help='List all computing nodes of Ha cluster')
        self.parser_node_list.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)

        self.parser_node_start = self.subparsers.add_parser('node-start', help='Power on the computing node')
        self.parser_node_start.add_argument("-c", "--node", help="Computing nodes you want to power on.", required=True)

        self.parser_node_shutOff = self.subparsers.add_parser('node-shutOff', help='Shut off the computing node')
        self.parser_node_shutOff.add_argument("-c", "--node", help="Computing nodes you want to Shut off.",
                                              required=True)

        self.parser_node_reboot = self.subparsers.add_parser('node-reboot', help='Reboot the computing node')
        self.parser_node_reboot.add_argument("-c", "--node", help="Computing nodes you want to reboot.", required=True)

        self.parser_node_getAllInfo = self.subparsers.add_parser('node-info-show',
                                                                 help='Get all hardware information of the computing node')
        self.parser_node_getAllInfo.add_argument("-c", "--node",
                                                 help="Computing nodes you want to get all hardware information.",
                                                 required=True)

        self.parser_node_getInfo_by_type = self.subparsers.add_parser('node-info-get',
                                                                      help='Get detail hardware information of the computing node')
        self.parser_node_getInfo_by_type.add_argument("-c", "--node",
                                                      help="Computing nodes you want to get detail hardware information.",
                                                      required=True)
        self.parser_node_getInfo_by_type.add_argument("-t", "--types",
                                                      help="The type of sensors which you want to get. Use ',' to separate sensors' types",
                                                      required=True)

        self.parser_instance_add = self.subparsers.add_parser('instance-add',
                                                              help='Protect instance and add instance into HA cluster')
        self.parser_instance_add.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
        self.parser_instance_add.add_argument("-v", "--vmid", help="The ID of the instance you wand to protect",
                                              required=True)

        self.parser_instance_delete = self.subparsers.add_parser('instance-delete', help='remove instance protection')
        self.parser_instance_delete.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
        self.parser_instance_delete.add_argument("-v", "--vmid",
                                                 help="The ID of the instance you wand to remove protection",
                                                 required=True)

        self.parser_instance_list = self.subparsers.add_parser('instance-list', help='List all instances of Ha cluster')
        self.parser_instance_list.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)

    def Input_Command_function(self):
        self.args = self.parser.parse_args()
        if self.args.command == "cluster-create":
            try:
                if self.args.nodes != None:
                    self.HASS_result = self.server.createCluster(self.args.name, self.args.nodes.strip().split(","))
                else:
                    self.HASS_result = self.server.createCluster(self.args.name, [])
                    # return createCluster_result["code"]+";"+createCluster_result["message"]
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "cluster-delete":
            try:
                self.HASS_result = self.server.deleteCluster(self.args.uuid)
                # return result["code"] + ";" + result["message"]
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "cluster-list":
            try:
                self.HASS_result = self.server.listCluster()
                self.showTable(self.HASS_result, self.TABLE.CLUSTER)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "node-add":
            try:
                self.HASS_result = self.server.addNode(self.args.uuid, self.args.nodes.strip().split(","))
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "node-delete":
            try:
                self.HASS_result = self.server.deleteNode(self.args.uuid, self.args.node)
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "node-list":
            try:
                self.HASS_result = self.server.listNode(self.args.uuid)
                self.HASS_result = Response(code=self.HASS_result["code"], message=self.HASS_result["message"],
                                            data=self.HASS_result["data"])
                if self.HASS_result.code == "succeed":
                    self.showTable(self.HASS_result.data.get("nodeList"), self.TABLE.NODE)
                else:
                    raise Exception
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)
                # return

        elif self.args.command == "node-start":
            try:
                self.HASS_result = self.server.startNode(self.args.node)
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "node-shutOff":
            try:
                self.HASS_result = self.server.shutOffNode(self.args.node)
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "node-reboot":
            try:
                self.HASS_result = self.server.rebootNode(self.args.node)
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "node-info-show":
            try:
                self.HASS_result = self.server.getAllInfoOfNode(self.args.node)
                self.generateSensorTable(self.HASS_result["data"]["info"])
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "node-info-get":
            self.type_list = self.args.types.strip().split(",")
            try:
                self.HASS_result = self.server.getNodeInfoByType(self.args.node, self.type_list)
                print "Computing Node : " + self.args.node
                self.generateSensorTable(self.HASS_result["data"]["info"])
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "instance-add":
            try:
                self.HASS_result = self.server.addInstance(self.args.uuid, self.args.vmid)
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "instance-delete":
            try:
                self.HASS_result = self.server.deleteInstance(self.args.uuid, self.args.vmid)
                print self.showResult(self.HASS_result)
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)

        elif self.args.command == "instance-list":
            try:
                self.HASS_result = self.server.listInstance(self.args.uuid)
                self.HASS_result = Response(code=self.HASS_result["code"], message=self.HASS_result["message"],
                                            data=self.HASS_result["data"])
                if self.HASS_result.code == "succeed":
                    self.showTable(self.HASS_result.data.get("instanceList"), self.TABLE.INSTANCE)
                else:
                    raise Exception
            except Exception as e:
                print self.ERROR_color + "[Error] " + self.END_color + str(e)
                # return
                # return result["code"]+";"+result["instanceList"]
                # self.showTable(self.HASS_result, self.TABLE.INSTANCE)


def main():
    hassapi = HassAPI()
    hassapi.Input_Command()
    hassapi.Input_Command_function()


if __name__ == "__main__":
    main()
