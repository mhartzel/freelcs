#!/bin/bash

# Start LoudnessCorrection as user freelcs
runuser --user=freelcs -- /usr/bin/python3 /usr/bin/LoudnessCorrection.py -configfile /etc/Loudness_Correction_Settings.json &

# Start Samba as root
/usr/sbin/smbd --foreground --no-process-group --configfile=/etc/samba/smb.conf &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
