# Run this code WITHOUT root user on compute

ssh ubuntu@192.168.2.116 "sudo sh -c 'echo OSFAILURE-first $(date '+%Y-%m-%d %H:%M:%S,%3N'); echo 1 > /proc/sys/kernel/sysrq; echo OSFAILURE-second $(date '+%Y-%m-%d %H:%M:%S,%3N');echo c > /proc/sysrq-trigger; echo OSFAILURE-third $(date '+%Y-%m-%d %H:%M:%S,%3N')'"