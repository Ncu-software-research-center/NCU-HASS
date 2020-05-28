# Run this code WITHOUT root user on compute

ssh ubuntu@192.168.2.116 "echo NETWORKFAILURE-started $(date '+%Y-%m-%d %H:%M:%S,%3N'); sudo /sbin/ifdown -a; echo NETWORKFAILURE-finished $(date '+%Y-%m-%d %H:%M:%S,%3N')"