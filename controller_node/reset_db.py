import pymysql

dbIP            = "192.168.4.14"  # IP address of the MySQL database server

dbUserName            = "root"       # User name of the database server

dbUserPassword        = "openstack"           # Password for the database user

 

databaseForDeletion         = "hass"          # Name of the database that is to be deleted

charSet                     = "utf8mb4"     # Character set

cusrorType                  = pymysql.cursors.DictCursor

 

connection   = pymysql.connect(host=dbIP, user=dbUserName, password=dbUserPassword,charset=charSet,cursorclass=cusrorType)

 

try:

    # Create a cursor object

    dbCursor        = connection.cursor()                                    

 

    # SQL Statement to delete a database

    sql = "DROP DATABASE "+databaseForDeletion  

 

    # Execute the create database SQL statment through the cursor instance

    dbCursor.execute(sql)

 

    # SQL query string

    sqlQuery            = "CREATE DATABASE hass"

 

    # Execute the sqlQuery

    dbCursor.execute(sqlQuery)

    print 'db reset done'
 

except Exception as e:

    print("Exeception occured:{}".format(e))

 

finally:

    connection.close()