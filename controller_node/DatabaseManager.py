#########################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   This is a class which maintains database for both hass/iii.
##########################################################


import logging
import ConfigParser

# UPDATE - MySQLdb, MySQLdb.cursors is removed (because of the license)
# import MySQLdb, MySQLdb.cursors

# UPDATE - pymysql library for the opensource code
# install this package to use pymysql
# pip install pymysql
# pip install cryptography
import pymysql
import sys


class DatabaseManager(object):
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')
        self.db_conn = None
        self.db = None
        try:
            if self._connect() :
                logging.info("Hass AccessDB - connect to database success")
            else :
                sys.exit(1)
        except pymysql.Error, e:
            logging.error("Hass AccessDB - connect to database failed (MySQL Error: %s)", str(e))
            print "MySQL Error: %s" % str(e)
            
    def _connect(self):
        try:
            self.db_conn = pymysql.connect(host=self.config.get("mysql", "mysql_ip"),
                                       user=self.config.get("mysql", "mysql_username"),
                                       passwd=self.config.get("mysql", "mysql_password"),
                                       db=self.config.get("mysql", "mysql_db"),
                                       cursorclass=pymysql.cursors.DictCursor
                                       )
            self.db = self.db_conn.cursor()
            return True
        except pymysql.Error, e:
            logging.error("Hass AccessDB - connect to database failed (MySQL Error: %s)", str(e))
            return False
        

    def _check_db(self):
        try:
            self.db_conn.ping()
            return True
        except Exception as e:
            logging.info("MYSQL CONNECTION REESTABLISHED!")
            self._connect()

    def create_table(self):
        if self._check_db() :
            try:
                self.db.execute("SET sql_notes = 0;")
                self.db.execute("""
                                CREATE TABLE IF NOT EXISTS ha_cluster 
                                (
                                cluster_name char(18),
                                protected_layers_string char(12),
                                PRIMARY KEY(cluster_name)
                                );
                                """)
                self.db.execute("""
                                CREATE TABLE IF NOT EXISTS ha_node 
                                (
                                node_name char(18),
                                below_cluster char(36),
                                PRIMARY KEY(node_name),
                                FOREIGN KEY(below_cluster)
                                REFERENCES ha_cluster(cluster_name)
                                ON DELETE CASCADE
                                );
                                """)
                self.db.execute("""
                                CREATE TABLE IF NOT EXISTS ha_instance 
                                (
                                instance_id char(36),
                                below_cluster char(36),
                                host          char(18),
                                status        char(18),
                                network       char(36),
                                PRIMARY KEY(instance_id),
                                FOREIGN KEY(below_cluster)
                                REFERENCES ha_cluster(cluster_name)
                                ON DELETE CASCADE
                                );
                                """)
            except pymysql.Error, e:
                self._close_db()
                logging.error("Hass AccessDB - Create Table failed (MySQL Error: %s)", str(e))
                print "MySQL Error: %s" % str(e)
                sys.exit(1)

        else :
            sys.exit(1)
        

    def sync_from_db(self):
        if self._check_db() :
            try:
                self.db.execute("SELECT * FROM ha_cluster;")
                ha_cluster_date = self.db.fetchall()
                exist_cluster = []
                for cluster in ha_cluster_date:
                    node_list = []
                    instance_list = []
                    self.db.execute("SELECT * FROM ha_node WHERE below_cluster = '%s'" % cluster["cluster_name"])
                    ha_node_date = self.db.fetchall()
                    self.db.execute("SELECT * FROM ha_instance WHERE below_cluster = '%s'" % cluster["cluster_name"])
                    ha_instance_date = self.db.fetchall()

                    for node in ha_node_date:
                        node_list.append(node["node_name"])
                    for instance in ha_instance_date:
                        instance_list.append(instance["instance_id"])

                    cluster_name = cluster["cluster_name"]
                    protected_layers_string = cluster["protected_layers_string"]
                    logging.info("dbmanager, sync_from_db- {}: {}".format(cluster_name, protected_layers_string))
                    exist_cluster.append({"cluster_name": cluster_name, "protected_layers_string": protected_layers_string, "node_list": node_list,
                                          "instance_list": instance_list})
                    # cluster_manager.createCluster(cluster_name = name , cluster_id = cluster_id)
                    # cluster_manager.addNode(cluster_id, node_list)
                logging.info("Hass AccessDB - Read data success")
                return exist_cluster

            except pymysql.Error, e:
                self._close_db()
                logging.error("Hass AccessDB - Read data failed (MySQL Error: %s)", str(e))
                print "MySQL Error: %s" % str(e)
        

    def sync_to_db(self, cluster_list):
        if self._check_db() :
            self.reset_all()
            try:
                for cluster_name, cluster in cluster_list.items():
                    # sync cluster
                    data = {"cluster_name": cluster.name, "protected_layers_string": cluster.protected_layers_string}
                    self._write_db("ha_cluster", data)
                    # sync node
                    node_list = cluster.get_node_list()
                    for node in node_list:
                        data = {"node_name": node.name, "below_cluster": node.cluster_name}
                        self._write_db("ha_node", data)
                    # sync instance
                    instance_list = cluster.get_protected_instance_list()
                    for instance in instance_list:
                        data = {"instance_id": instance.id, "below_cluster": cluster_name, "host": instance.host,
                                "status": instance.status, "network": str(instance.network)}
                        self._write_db("ha_instance", data)
            except pymysql.Error, e:
                self._close_db()
                logging.error("DatabaseManager - sync data failed (MySQL Error: %s)", str(e))
                print "MySQL Error: %s" % str(e)
        

    def _write_db(self, dbName, data):
        if self._check_db() :
            if dbName == "ha_cluster":
                format = "INSERT INTO ha_cluster (cluster_name,protected_layers_string) VALUES (%(cluster_name)s, %(protected_layers_string)s);"
            elif dbName == "ha_node":
                format = "INSERT INTO ha_node (node_name,below_cluster) VALUES (%(node_name)s, %(below_cluster)s);"
            elif dbName == "ha_instance":
                format = "INSERT INTO ha_instance (instance_id, below_cluster, host, status, network) VALUES (%(instance_id)s, %(below_cluster)s, %(host)s, %(status)s, %(network)s);"
            try:
                self.db.execute(format, data)
                self.db_conn.commit()
            except Exception as e:
                logging.error("DatabaseManager - write data to DB Failed (MySQL Error: %s)", str(e))
                print "MySQL Error: %s" % str(e)
                raise
        

    def _get_all_table(self):
        if self._check_db() :
            try:
                table_list = []
                cmd = "show tables"
                self.db.execute(cmd)
                res = self.db.fetchall()  # ({'Tables_in_hass': 'talbe1'}, {'Tables_in_hass': 'table2'})
                index = "Tables_in_%s" % self.config.get("mysql", "mysql_db")
                for table in res:
                    table_list.append(table[index])
                return table_list
            except Exception as e:
                logging.error("DatabaseManager - failed to get all table")
                raise e

    def reset_all(self):
        if self._check_db() :
            try:
                table_list = self._get_all_table()
                for table in table_list:
                    self._reset_table(table)
            except Exception as e:
                logging.error("DatabaseManager - failed to reset all table")
                raise e
        

    def _reset_table(self, table_name):
        if self._check_db() :
            try:
                cmd = " DELETE FROM  `%s` WHERE true" % table_name
                self.db.execute(cmd)
                self.db_conn.commit()
            except Exception as e:
                logging.error("DatabaseManager - failed to reset table")
                raise e
        

    def _close_db(self):
        try:
            self.db.close()
            self.db_conn.close()
        except Exception as e:
            logging.error("failed to close database connection")

if __name__ == "__main__":
    a = DatabaseManager()
    #a.create_table()
    #print(a._get_all_table())
    #a.reset_all()
    #print(a._get_all_table())
    #a.getInstanceResourceID("806df263-a6e6-4e44-a8b6-79c5548ce33c")
