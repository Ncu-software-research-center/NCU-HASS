# Run this code WITH root user on compute
echo NETWORKFAILURE-started $(date '+%Y-%m-%d %H:%M:%S,%3N'); sudo /sbin/ifdown -a; echo NETWORKFAILURE-finished $(date '+%Y-%m-%d %H:%M:%S,%3N')