# Make sure the libvirt instance name is correct : instance-000000xx
# If you run WITHOUT root-user, do following command on your host
# sudo chown root /path/filename.sh
# sudo chmod 0755 /path/filename.sh
# sudo chgrp sudo /path/filename.sh

echo POWERFAILURE-started $(date '+%Y-%m-%d %H:%M:%S,%3N');sudo kill -9 $(ps aux | grep -E '^libvirt+.*instance-0000001f' | tr -s ' ' | cut -d ' ' -f 2); echo POWERFAILURE-finished $(date '+%Y-%m-%d %H:%M:%S,%3N')