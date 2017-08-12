
This script is targeted at advanced users who know their way around Linux and the Terminal.

This program will make a backup of your current FreeLCS settings, that can be restored to any computer running Ubuntu.

The restoration program is a shell script that doesn't require a graphical GUI so restoration can be automated or done through a ssh - connection.

The reason this backup / restoration functionality exists is to make cloning FreeLCS installation to several machines quick and painless :)


Usage
-----

1. Install FreeLCS with the normal graphical installer and adjust settings the way you want.
2. Then run '00-backup_freelcs_configuration.sh' to make a backup of the installation settings. Files needed for restoration and a restoration script will be created in directory 'freelcs_backup'.
3. Copy the contents of dir 'freelcs_backup' to all machines that you want to have the same configuration and run the restoration script '00-restore_freelcs_configuration.sh' on each.
4. The restoration script will install all programs and scripts that FreeLCS needs to function. After restoration all machines will have identical FreeLCS installation.
5. Reboot the machines or start loudness correction scripts manually (restoration script displays the startup command at the end of the run).

Result: The FreeLCS installation has been cloned to several machines.

Note: Internet connection is required during restoration, since all needed programs are downloaded and installed from the net


