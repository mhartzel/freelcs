#!/bin/bash
#
# This script backs up FreeLCS configuration and creates a restoration script.
# The backup can be restored to any computer running Ubuntu and no X is required.
#

if [ "$UID" != "0" ] ; then
	echo
	echo "This script must be run as root"
	echo
	exit
fi

REAL_USER_NAME=`logname 2> /dev/null`

if [ "$REAL_USER_NAME" == ""  ] ; then
        REAL_USER_NAME="$1"
fi

if [ "$REAL_USER_NAME" == ""  ] ; then
        echo
        echo "ERROR: Can not find out your login username."
	echo "Please give your login name as the first argument for the script."
	echo
	echo "Example: 00-backup_freelcs_configuration.sh   john"
	echo
	echo "The username is used to make the copied configuration files"
	echo "readable and writable to this user."
        echo
        exit
fi

# Find out the name and version number of the operating sustem
if [ ! -e "/etc/os-release" ] ; then
	echo 
	echo "Cannot read /etc/os-release to determine that we are on a supported os."
	echo "Can't continue."
	echo 
	exit
fi

# Find the os name and lowercase it
OS_NAME=""
OS_VERSION=""
OS_VERSION_MAJOR_NUMBER=""
OS_VERSION_MINOR_NUMBER=""

OS_NAME=`cat /etc/os-release | grep "^ID=" | sed 's/^ID=//' | sed 's/"//g' | sed 's/./\L&/g' `
OS_VERSION=`cat /etc/os-release | grep "^VERSION_ID=" | sed 's/^VERSION_ID=//' | sed 's/"//g'`
OS_VERSION_MAJOR_NUMBER=`echo $OS_VERSION | sed 's/\..*$//'`
OS_VERSION_MINOR_NUMBER=`echo $OS_VERSION | grep "\." | sed 's/^.*\.//'`

if [ "$OS_NAME" != "ubuntu" ] && [ "$OS_NAME" != "debian" ] ; then
	echo
	echo "The os "$OS_NAME" is not supported."
	echo "Can't continue."
	echo
	exit
fi

# Maybe it's better not to activate these os version tests. The warning that the script prints at the end of backup should be enough.
#
# if [ "$OS_NAME" == "ubuntu" ] ; then
#         if [ "$OS_VERSION_MAJOR_NUMBER" -lt "14" ] ; then
#                 echo
#                 echo "Ubuntu version "$OS_VERSION" is not supported."
#                 echo "Can't continue."
#                 echo
#                 exit
#         fi
# 
#         if [ "$OS_VERSION_MINOR_NUMBER" != "04" ] ; then
#                 echo
#                 echo "Ubuntu version "$OS_VERSION" is not supported."
#                 echo "Can't continue."
#                 echo
#                 exit
#         fi
# fi
# 
# if [ "$OS_NAME" == "debian" ] ; then
#         if [ "$OS_VERSION_MAJOR_NUMBER" -lt "8" ] ; then
#                 echo
#                 echo "Debian version "$OS_VERSION" is not supported."
#                 echo "Can't continue."
#                 echo
#                 exit
#         fi
# fi

echo
#### "123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 "
echo "This program will make a backup of your current FreeLCS installation,"
echo "that can be restored to any computer running the same version of the os."
echo "The restoration program is a shell script that doesn't require a graphical"
echo "GUI so restoration can be automated or done through a ssh - connection."
echo
echo "The reason this backup / restoration functionality exists is to make"
echo "cloning FreeLCS installation to several machines quick and painless :)"
echo
echo "A directory will be created to the current dir and backup files copied to it."
echo
echo "Press ctrl + c now to cancel ...."
echo
read -p "or the [Enter] key to start making the backup ..."
echo

# Check which init system the operating system uses init or systemd
INIT_SYSTEM_NAME=""
INIT_SYSTEM_NAME=`ps --pid 1 --no-headers -c -o cmd`

if [ "$INIT_SYSTEM_NAME" != "systemd" ] && [  "$INIT_SYSTEM_NAME" != "init" ] ; then

	echo
	echo "ERROR, Can not find out if your os init system is systemd or init"
	echo "Can not continue."
	echo
	exit
fi

# Create dir for backup files.
BACKUP_DIR_NAME="freelcs_backup"

mkdir -p "$BACKUP_DIR_NAME"

if [ ! -e "$BACKUP_DIR_NAME" ] ; then
	echo
	echo "ERROR: Can not create directory for backup files."
	echo
	exit
fi

cd "$BACKUP_DIR_NAME"

# Define paths to files to back up.
if [ "$INIT_SYSTEM_NAME" == "init" ] ; then
	LOUDNESSCORRECTION_PATH="/usr/bin/LoudnessCorrection.py"
	HEARTBEAT_CHECKER_PATH="/usr/bin/HeartBeat_Checker.py"
	SETTINGS_FILE_PATH="/etc/Loudness_Correction_Settings.pickle"
	SAMBA_CONF_PATH="/etc/samba/smb.conf"
	INIT_SCRIPT_PATH="/etc/init.d/loudnesscorrection_init_script"
	SYSTEMD_SERVICE_FILE_PATH=""
fi

if [ "$INIT_SYSTEM_NAME" == "systemd" ] ; then
	LOUDNESSCORRECTION_PATH="/usr/bin/LoudnessCorrection.py"
	HEARTBEAT_CHECKER_PATH="/usr/bin/HeartBeat_Checker.py"
	SETTINGS_FILE_PATH="/etc/Loudness_Correction_Settings.pickle"
	SAMBA_CONF_PATH="/etc/samba/smb.conf"
	INIT_SCRIPT_PATH="/etc/systemd/system/loudnesscorrection_init_script"
	SYSTEMD_SERVICE_FILE_PATH="/etc/systemd/system/freelcs.service"
fi

# Check if user has Samba installed
SAMBA_PATH=`which smbd`

# Check that all files we wan't to copy exist.
if [ ! -e "$INIT_SCRIPT_PATH" ] ; then
        echo
        echo "ERROR: Can not find FreeLCS file: "$INIT_SCRIPT_PATH", can not continue."
        echo
        exit
fi

if [ ! -e "$LOUDNESSCORRECTION_PATH" ] ; then
        echo
        echo "ERROR: Can not find FreeLCS file: "$LOUDNESSCORRECTION_PATH", can not continue."
        echo
        exit
fi

if [ ! -e "$HEARTBEAT_CHECKER_PATH" ] ; then
        echo
        echo "ERROR: Can not find FreeLCS file: "$HEARTBEAT_CHECKER_PATH", can not continue."
        echo
        exit
fi

if [ ! -e "$SETTINGS_FILE_PATH" ] ; then
        echo
        echo "ERROR: Can not find FreeLCS file: "$SETTINGS_FILE_PATH", can not continue."
        echo
        exit
fi

# Only search for samba conf - file if Samba is installed.
if [ "$SAMBA_PATH" != "" ] ; then

	if [ ! -e "$SAMBA_CONF_PATH" ] ; then
		echo
		echo "ERROR: Can not find FreeLCS file: "$SAMBA_CONF_PATH", can not continue."
		echo
		exit
	fi
fi

# Check if systemd service file is installed
if [ "$INIT_SYSTEM_NAME" == "systemd" ] ; then

	if [ ! -e "$SYSTEMD_SERVICE_FILE_PATH" ] ; then
		echo
		echo "ERROR: Can not find FreeLCS file: "$SYSTEMD_SERVICE_FILE_PATH", can not continue."
		echo
		exit
	fi
fi

# Copy FreeLCS files to backup dir.
echo
echo "Copying installed FreeLCS files to backup dir ..."
echo "--------------------------------------------------"
echo

cp $INIT_SCRIPT_PATH .

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error, could not copy: "$INIT_SCRIPT_PATH
	echo
	exit
fi

cp $LOUDNESSCORRECTION_PATH .

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error, could not copy: "$LOUDNESSCORRECTION_PATH
	echo
	exit
fi

cp $HEARTBEAT_CHECKER_PATH .

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error, could not copy: "$HEARTBEAT_CHECKER_PATH
	echo
	exit
fi

cp $SETTINGS_FILE_PATH .

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error, could not copy: "$SETTINGS_FILE_PATH
	echo
	exit
fi

# Only copy samba conf - file if Samba is installed.
if [ "$SAMBA_PATH" != "" ] ; then

	cp $SAMBA_CONF_PATH .

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not copy: "$SAMBA_CONF_PATH
		echo
		exit
	fi
fi

# Only copy systemd service file if os init system is systemd
if [ "$INIT_SYSTEM_NAME" == "systemd" ] ; then

	cp $SYSTEMD_SERVICE_FILE_PATH .

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not copy: "$SYSTEMD_SERVICE_FILE_PATH
		echo
		exit
	fi
fi

LIBEBUR128_ARCHIVE_NAME="libebur128_fork_for_freelcs_3.4.tar.xz"
LIBEBUR128_DIR_NAME="libebur128_fork_for_freelcs_3.4"

if [ -e "../../$LIBEBUR128_ARCHIVE_NAME" ] ; then
	cp "../../$LIBEBUR128_ARCHIVE_NAME" .
fi

echo "Writing restoration script to backup dir ..."
echo "---------------------------------------------"
echo

if [ "$INIT_SYSTEM_NAME" == "systemd" ] ; then

cat > "00-restore_freelcs_configuration.sh" << 'END_OF_FILE'
#!/bin/bash

if [ "$UID" != "0" ] ; then
	echo
	echo "This script must be run as root"
	echo
	exit
fi

ORIGINAL_INIT_SYSTEM_NAME="systemd"

END_OF_FILE

fi


if [ "$INIT_SYSTEM_NAME" == "init" ] ; then

cat > "00-restore_freelcs_configuration.sh" << 'END_OF_FILE'
#!/bin/bash

if [ "$UID" != "0" ] ; then
	echo
	echo "This script must be run as root"
	echo
	exit
fi

ORIGINAL_INIT_SYSTEM_NAME="init"

END_OF_FILE

fi


echo 'OS_NAME="'$OS_NAME'"' >> "00-restore_freelcs_configuration.sh"
echo 'OS_VERSION="'$OS_VERSION'"' >> "00-restore_freelcs_configuration.sh"
echo 'OS_VERSION_MAJOR_NUMBER="'$OS_VERSION_MAJOR_NUMBER'"' >> "00-restore_freelcs_configuration.sh"
echo 'OS_VERSION_MINOR_NUMBER="'$OS_VERSION_MINOR_NUMBER'"' >> "00-restore_freelcs_configuration.sh"


cat >> "00-restore_freelcs_configuration.sh" << 'END_OF_FILE'

# Check which init system the operating system uses init or systemd
INIT_SYSTEM_NAME=""
INIT_SYSTEM_NAME=`ps --pid 1 --no-headers -c -o cmd`

LIBEBUR128_ARCHIVE_NAME="libebur128_fork_for_freelcs_3.4.tar.xz"
LIBEBUR128_DIR_NAME="libebur128_fork_for_freelcs_3.4"

if [ "$INIT_SYSTEM_NAME" != "systemd" ] && [  "$INIT_SYSTEM_NAME" != "init" ] ; then

	echo
	echo "ERROR, Can not find out if your os init system is systemd or init"
	echo "Can not continue."
	echo
	exit
fi

if [ "$INIT_SYSTEM_NAME" != "$ORIGINAL_INIT_SYSTEM_NAME" ] ; then

	echo
	echo "FreeLCS was backed up on a "$ORIGINAL_INIT_SYSTEM_NAME" based os"
	echo "This operating system is based on "$INIT_SYSTEM_NAME
	echo "FreeLCS can not be restored to a different system it was backupped from."
	echo "Can not continue."
	echo
	exit
fi


# Define names for files we are about to copy back to system.

if [ "$INIT_SYSTEM_NAME" == "init" ] ; then
	LOUDNESSCORRECTION_NAME="LoudnessCorrection.py"
	HEARTBEAT_CHECKER_NAME="HeartBeat_Checker.py"
	SETTINGS_FILE_NAME="Loudness_Correction_Settings.pickle"
	SAMBA_CONF_NAME="smb.conf"
	INIT_SCRIPT_NAME="loudnesscorrection_init_script"
	SYSTEMD_SERVICE_FILE_NAME=""

	# Define paths for copy targets.
	LOUDNESSCORRECTION_PATH="/usr/bin/LoudnessCorrection.py"
	HEARTBEAT_CHECKER_PATH="/usr/bin/HeartBeat_Checker.py"
	SETTINGS_FILE_PATH="/etc/Loudness_Correction_Settings.pickle"
	SAMBA_CONF_PATH="/etc/samba/smb.conf"
	INIT_SCRIPT_PATH="/etc/init.d/loudnesscorrection_init_script"
	INIT_SCRIPT_LINK_PATH="/etc/rc2.d/S99loudnesscorrection_init_script"
	SYSTEMD_SERVICE_FILE_PATH=""
fi

if [ "$INIT_SYSTEM_NAME" == "systemd" ] ; then
	LOUDNESSCORRECTION_NAME="LoudnessCorrection.py"
	HEARTBEAT_CHECKER_NAME="HeartBeat_Checker.py"
	SETTINGS_FILE_NAME="Loudness_Correction_Settings.pickle"
	SAMBA_CONF_NAME="smb.conf"
	INIT_SCRIPT_NAME="loudnesscorrection_init_script"
	SYSTEMD_SERVICE_FILE_NAME="freelcs.service"

	# Define paths for copy targets.
	LOUDNESSCORRECTION_PATH="/usr/bin/LoudnessCorrection.py"
	HEARTBEAT_CHECKER_PATH="/usr/bin/HeartBeat_Checker.py"
	SETTINGS_FILE_PATH="/etc/Loudness_Correction_Settings.pickle"
	SAMBA_CONF_PATH="/etc/samba/smb.conf"
	INIT_SCRIPT_PATH="/etc/systemd/system/loudnesscorrection_init_script"
	SYSTEMD_SERVICE_FILE_PATH="/etc/systemd/system/freelcs.service"
fi

# Check that all files we want to copy exist.
if [ ! -e "$INIT_SCRIPT_NAME" ] ; then
        echo
        echo "ERROR: Can not find FreeLCS file: "$INIT_SCRIPT_NAME", can not continue."
        echo
        exit
fi

if [ ! -e "$LOUDNESSCORRECTION_NAME" ] ; then
        echo
        echo "ERROR: Can not find FreeLCS file: "$LOUDNESSCORRECTION_NAME", can not continue."
        echo
        exit
fi

if [ ! -e "$HEARTBEAT_CHECKER_NAME" ] ; then
        echo
        echo "ERROR: Can not find FreeLCS file: "$HEARTBEAT_CHECKER_NAME", can not continue."
        echo
        exit
fi

if [ ! -e "$SETTINGS_FILE_NAME" ] ; then
        echo
        echo "ERROR: Can not find FreeLCS file: "$SETTINGS_FILE_NAME", can not continue."
        echo
        exit
fi

if [ "$INIT_SYSTEM_NAME" == "systemd" ] ; then

	if [ ! -e "$SYSTEMD_SERVICE_FILE_NAME" ] ; then
		echo
		echo "ERROR: Can not find FreeLCS file: "$SYSTEMD_SERVICE_FILE_NAME", can not continue."
		echo
		exit
	fi
fi

SAMBA_INSTALLATION_COMMAND=""

# Check if Samba samba configuration must be restored.
if [ -e "$SAMBA_CONF_NAME" ] ; then
	SAMBA_INSTALLATION_COMMAND="samba"
fi

##############################################################################
# If temporary installation directories still exist in /tmp then delete them #
##############################################################################

if [ -e "/tmp/libebur128" ] ; then

	rm -rf "/tmp/libebur128"

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not delete temporary dir /tmp/libebur128"
		echo
		exit
	fi
fi

if [ -e "/tmp/libebur128_fork_for_freelcs_2.4" ] ; then

	rm -rf "/tmp/libebur128_fork_for_freelcs_2.4"

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not delete temporary dir /tmp/libebur128_fork_for_freelcs_2.4"
		echo
		exit
	fi
fi

if [ -e "/tmp/libebur128_fork_for_freelcs_3.4" ] ; then

	rm -rf "/tmp/libebur128_fork_for_freelcs_3.4"

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not delete temporary dir /tmp/libebur128_fork_for_freelcs_3.4"
		echo
		exit
	fi
fi

if [ -e "/tmp/$LIBEBUR128_DIR_NAME" ] ; then

	rm -rf "/tmp/$LIBEBUR128_DIR_NAME"

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not delete temporary dir /tmp/"$LIBEBUR128_DIR_NAME
		echo
		exit
	fi
fi

if [ -e "/tmp/sox_personal_fork" ] ; then

	rm -rf "/tmp/sox_personal_fork"
	
	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not delete temporary dir /tmp/sox_personal_fork"
		echo
		exit
	fi
fi


# Add here all additional packages that you want apt-get to install. Separate names with a space. Example:   ADDITIONAL_PACKAGE_INSTALLATION_COMMANDS="avconv audacity vlc".
# ADDITIONAL_PACKAGE_INSTALLATION_COMMANDS="avconv" 

echo
echo "#############################################"
echo "# Installing required packages with apt-get #"
echo "#############################################"
echo

# Only install sox from source on oses that don't have at least versio 14.4.0 available on repository
SOX_INSTALLATION_COMMAND="sox"
INSTALL_SOX_FROM_OS_REPOSITORY=true

if [ "$OS_NAME" == "ubuntu" ] && [ "$OS_VERSION" == "12.04" ] ; then 
	INSTALL_SOX_FROM_OS_REPOSITORY=false
	SOX_INSTALLATION_COMMAND=""

	# If sox is installed as a apt - package, then remove it, because we are going to install it from source.
	apt-get remove -y sox

fi


APT_PACKAGE_LIST="python3 idle3 automake autoconf libtool gnuplot mediainfo build-essential git cmake libsndfile-dev libmpg123-dev libmpcdec-dev libglib2.0-dev libfreetype6-dev librsvg2-dev libavcodec-dev libavformat-dev libtag1-dev libxml2-dev libqt4-dev"

fi

apt-get -q=2 -y --reinstall install $APT_PACKAGE_LIST $SAMBA_INSTALLATION_COMMAND $SOX_INSTALLATION_COMMAND $ADDITIONAL_PACKAGE_INSTALLATION_COMMANDS 

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error installing packages with apt-get, can not continue."
	echo
	exit
fi


echo
echo "##############################"
echo "# Installing FreeLCS scripts #"
echo "##############################"
echo

cp -f "$INIT_SCRIPT_NAME" "$INIT_SCRIPT_PATH"

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error, could not create: "$INIT_SCRIPT_PATH
	echo
	exit
fi

chown root:root "$INIT_SCRIPT_PATH"
chmod  755 "$INIT_SCRIPT_PATH"


cp -f "$LOUDNESSCORRECTION_NAME" "$LOUDNESSCORRECTION_PATH"

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error, could not create: "$LOUDNESSCORRECTION_PATH
	echo
	exit
fi

chown root:root "$LOUDNESSCORRECTION_PATH"
chmod  755 "$LOUDNESSCORRECTION_PATH"


cp -f "$HEARTBEAT_CHECKER_NAME" "$HEARTBEAT_CHECKER_PATH"

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error, could not create: "$HEARTBEAT_CHECKER_PATH
	echo
	exit
fi

chown root:root "$HEARTBEAT_CHECKER_PATH"
chmod  755 "$HEARTBEAT_CHECKER_PATH"


cp -f "$SETTINGS_FILE_NAME" "$SETTINGS_FILE_PATH"

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error, could not create: "$SETTINGS_FILE_PATH
	echo
	exit
fi

chown root:root "$SETTINGS_FILE_PATH"
chmod  644 "$SETTINGS_FILE_PATH"


if [ -e "$SAMBA_CONF_NAME" ] ; then

	mkdir -p /etc/samba
	cp -f "$SAMBA_CONF_NAME" "$SAMBA_CONF_PATH"

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not create: "$SAMBA_CONF_PATH
		echo
		exit
	fi

	chown root:root "$SAMBA_CONF_PATH"
	chmod  644 "$SAMBA_CONF_PATH"
fi


if [ "$INIT_SYSTEM_NAME" != "systemd" ] ; then

	if [ "$OS_NAME" == "ubuntu" ] ; then

		ln -s -f "$INIT_SCRIPT_PATH" "$INIT_SCRIPT_LINK_PATH"

		if [ "$?" -ne "0"  ] ; then
			echo
			echo "Error, could not create: "$INIT_SCRIPT_LINK_PATH
			echo
			exit
		fi
	fi

	if [ "$OS_NAME" == "debian" ] ; then

		insserv -d $INIT_SCRIPT_PATH

		if [ "$?" -ne "0"  ] ; then
			echo
			echo "Error, running: insserv -d "$INIT_SCRIPT_PATH
			echo
			exit
		fi
	fi
fi

if [ "$INIT_SYSTEM_NAME" == "systemd" ] ; then

	cp -f "$SYSTEMD_SERVICE_FILE_NAME" "$SYSTEMD_SERVICE_FILE_PATH"

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not create: "$SYSTEMD_SERVICE_FILE_PATH
		echo
		exit
	fi

	chown root:root "$SYSTEMD_SERVICE_FILE_PATH"
	chmod  644 "$SYSTEMD_SERVICE_FILE_PATH"

	systemctl -q enable $SYSTEMD_SERVICE_FILE_NAME

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error, could not enable FreeLCS systemd service: "$SYSTEMD_SERVICE_FILE_PATH
		echo
		exit
	fi
fi


if [ -e "$LIBEBUR128_ARCHIVE_NAME" ] ; then
	cp "$LIBEBUR128_ARCHIVE_NAME" /tmp
fi

cd /tmp

if [ -e "$LIBEBUR128_ARCHIVE_NAME" ] ; then

	echo
	echo "########################################"
	echo "# Extracting libebur128 source archive #"
	echo "########################################"
	echo

	tar xJf "$LIBEBUR128_ARCHIVE_NAME"

else

	echo
	echo "######################################"
	echo "# Downloading libebur128 source code #"
	echo "######################################"
	echo

	git clone http://github.com/mhartzel/$LIBEBUR128_DIR_NAME.git

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error downloading libebur128 source code, can not continue."
		echo
		exit
	fi

fi

cd $LIBEBUR128_DIR_NAME

# Get the git commit number of current version of libebur128
echo
LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION="5464c5a923b28fe8677479d54f0ca59602942027"
LIBEBUR128_CURRENT_COMMIT=`git rev-parse HEAD`

# If libebur128 commit number does not match, check out the correct version from git
if [ "$LIBEBUR128_CURRENT_COMMIT" == "$LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION" ] ; then
	echo "libebur128 already at the required version $LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION"
else
	echo "Checking out required version of libebur128 from git project"
	echo
	git checkout --force $LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION
	
	# Check that we have the correct version after checkout
	LIBEBUR128_CURRENT_COMMIT=`git rev-parse HEAD`
	if [ "$LIBEBUR128_CURRENT_COMMIT" == "$LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION" ] ; then
		echo "Checkout was successful"
		echo
	else
		echo "There was an error when trying to check out the correct libebur128 version from the local git repository !!!!!!!"
		echo
		exit
	fi
fi


echo
echo "########################################################################"
echo "# Applying libebur128 4.0 and 5.0 - channel patch to libebur128 source #"
echo "########################################################################"
echo

PATCH_NAME=`ls -1 libebur128-patch-*.diff`

OUTPUT_FROM_PATCHING=`patch -s -p1 < "$PATCH_NAME"`

# Check if applying patch produced an error

case "$OUTPUT_FROM_PATCHING" in
	*error*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;
	*cannot*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;
	*fatal*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;
	*fail*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;
	*) echo "libebur128 patched successfully :)" ;;
esac
echo

echo
echo "###############################################"
echo "# Preparing libebur128 source for compilation #"
echo "###############################################"
echo

cd /tmp/$LIBEBUR128_DIR_NAME
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -Wno-dev   -DCMAKE_INSTALL_PREFIX:PATH=/usr

echo
echo "#######################################"
echo "# Compiling and installing libebur128 #"
echo "#######################################"
echo

make -s -j 4

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error compiling libebur128, can not continue."
	echo
	exit
fi

make install

echo
echo "##############################################################################"
echo "# Installing executable 'loudness-freelcs' and libebur128 file input plugins #"
echo "##############################################################################"
echo

cp loudness-freelcs             /usr/bin/
cp libinput_sndfile-freelcs.so  /usr/lib/
cp libinput_ffmpeg-freelcs.so   /usr/lib/
cp libinput_mpg123-freelcs.so   /usr/lib/
cp libinput_musepack-freelcs.so /usr/lib/

chmod 755 /usr/bin/loudness-freelcs
chmod 644 /usr/lib/libinput_sndfile-freelcs.so
chmod 644 /usr/lib/libinput_ffmpeg-freelcs.so
chmod 644 /usr/lib/libinput_mpg123-freelcs.so
chmod 644 /usr/lib/libinput_musepack-freelcs.so

chown root:root /usr/bin/loudness-freelcs
chown root:root /usr/lib/libinput_sndfile-freelcs.so
chown root:root /usr/lib/libinput_ffmpeg-freelcs.so
chown root:root /usr/lib/libinput_mpg123-freelcs.so
chown root:root /usr/lib/libinput_musepack-freelcs.so

ldconfig


#################################################
# Handle loading of kernel module brd if needed #
#################################################

BRD_MODULE_BUILT_INTO_KERNEL=false
BRD_MODULE_LOADED_AS_KERNEL_MODULE=false
BRD_MODULE_LOADS_AT_OS_STARTUP=false
KERNEL_VERSION=`uname -r`
BUILTIN_MODULES_PATH="/lib/modules/"$KERNEL_VERSION"/modules.builtin"
BUILTIN_MODULES_LIST=`cat $BUILTIN_MODULES_PATH`
MODULES_LOADED_AT_BOOT_PATH="/etc/modules"

###############################################
# Test if brd module is built into the kernel #
###############################################
case $BUILTIN_MODULES_LIST in
	*brd.ko*)
		BRD_MODULE_BUILT_INTO_KERNEL=true
		;;
	*brd.ko)
		BRD_MODULE_BUILT_INTO_KERNEL=true
esac

################################################
# Test if brd module is now loaded into memory #
################################################
BRD_LOADED_INTO_RAM=`lsmod | grep brd | awk '{ print $1 }'`

if [ "$BRD_LOADED_INTO_RAM" == "brd"  ] ; then BRD_MODULE_LOADED_AS_KERNEL_MODULE=true ; fi


#########################################
# Test if brd module is in /etc/modules #
#########################################
BRD_IS_IN_MODULES_FILE=`cat /etc/modules | sed 's/#.*//g' | sed '/^\s*$/d'`


case $BRD_IS_IN_MODULES_FILE in
	*brd*)
		BRD_MODULE_LOADS_AT_OS_STARTUP=true
esac

###########################################
# Load brd if it is not running right now #
###########################################

if [ "$BRD_MODULE_BUILT_INTO_KERNEL" == false ] && [ "$BRD_MODULE_LOADED_AS_KERNEL_MODULE" == false  ] ; then

	echo
	echo "########################################################"
	echo "# Loading ram disk driver (kernel module brd) into ram #"
	echo "########################################################"
	echo

	modprobe brd
fi

######################################################
# Add brd to /etc/modules if it is not already there #
######################################################

if [ "$BRD_MODULE_BUILT_INTO_KERNEL" == false  ] && [ "$BRD_MODULE_LOADS_AT_OS_STARTUP" == false  ] ; then 

	echo
	echo "################################################################"
	echo "# Adding ram disk driver (kernel module brd) into "$MODULES_LOADED_AT_BOOT_PATH" #"
	echo "################################################################"
	echo

	echo "" >> $MODULES_LOADED_AT_BOOT_PATH
	echo "# FreeLCS needs the brd kernel ram disk driver" >> $MODULES_LOADED_AT_BOOT_PATH
	echo "brd" >> $MODULES_LOADED_AT_BOOT_PATH
	echo "" >> $MODULES_LOADED_AT_BOOT_PATH
fi


# Install sox from source
if [ "$INSTALL_SOX_FROM_OS_REPOSITORY" == false  ] ; then
	echo
	echo "#############################################"
	echo "# Downloading, compiling and installing sox #"
	echo "#############################################"
	echo

	# Download sox source
	cd /tmp

	git clone http://github.com/mhartzel/sox_personal_fork.git

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error downloading sox source code, can not continue."
		echo
		exit
	fi


	cd sox_personal_fork

	echo
	echo "Checking out required version of sox from git project"
	echo

	SOX_REQUIRED_GIT_COMMIT_VERSION="6dff9411961cc8686aa75337a78b7df334606820"
	git checkout --force $SOX_REQUIRED_GIT_COMMIT_VERSION

	# Check that we have the correct version after checkout
	SOX_CURRENT_COMMIT=`git rev-parse HEAD`

	if [ "$SOX_CURRENT_COMMIT" == "$SOX_REQUIRED_GIT_COMMIT_VERSION" ] ; then
		echo
		echo "Checkout was successful"
		echo
	else
		echo "There was an error when trying to check out the correct sox version from the local git repository !!!!!!!"
		echo
		exit
	fi

	# Build and install sox from source
	autoreconf -i
	./configure --prefix=/usr
	make -s -j 4

	if [ "$?" -ne "0"  ] ; then
		echo
		echo "Error compiling sox source code, can not continue."
		echo
		exit
	fi

	make install
fi

END_OF_FILE


if [ "$INIT_SYSTEM_NAME" == "init" ] ; then

cat >> "00-restore_freelcs_configuration.sh" << 'END_OF_FILE'

echo
echo "############"
echo "# Ready :) #"
echo "############"
echo
echo "Reboot the computer to start FreeLCS or give the following command:"
echo
echo "sudo  -b  /etc/init.d/loudnesscorrection_init_script restart"
echo

END_OF_FILE

fi


if [ "$INIT_SYSTEM_NAME" == "systemd" ] ; then

cat >> "00-restore_freelcs_configuration.sh" << 'END_OF_FILE'

echo
echo "############"
echo "# Ready :) #"
echo "############"
echo
echo "Reboot the computer to start FreeLCS or give the following command:"
echo
echo "sudo  -b  systemctl  start  freelcs"
echo

END_OF_FILE

fi


MEDIA_CONVERTER_NAME="ffmpeg"

if [ "$OS_NAME" == "ubuntu" ] && [ "$OS_VERSION_MAJOR_NUMBER" -lt "16" ] ; then
	MEDIA_CONVERTER_NAME="avconv"
fi

if [ "$OS_NAME" == "debian" ] && [ "$OS_VERSION_MAJOR_NUMBER" -lt "9" ] ; then
	MEDIA_CONVERTER_NAME="avconv"
fi


if [ "$MEDIA_CONVERTER_NAME" == "avconv" ] ; then

cat >> "00-restore_freelcs_configuration.sh" << 'END_OF_FILE'

echo "If you need libav format support, then please install it now with the command:"
echo "sudo apt-get -y install libav-tools"
echo

END_OF_FILE

fi


if [ "$MEDIA_CONVERTER_NAME" == "ffmpeg" ] ; then

cat >> "00-restore_freelcs_configuration.sh" << 'END_OF_FILE'

echo "If you need ffmpeg format support, then please install it now with the command:"
echo "sudo apt-get -y install ffmpeg"
echo

END_OF_FILE

fi


chmod 755 "00-restore_freelcs_configuration.sh"

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error making 'restore_freelcs_configuration' script executable."
	echo
	exit
fi

cd - > /dev/null

# Make backed up files readable and writable by the normal user running this script with sudo.
chown -R $REAL_USER_NAME:$REAL_USER_NAME "freelcs_backup"

echo
echo "############"
echo "# Ready :) #"
echo "############"
echo
echo "FreeLCS configuration has been saved to directory 'freelcs_backup'."
echo
echo "Please note that the restoration script '00-restore_freelcs_configuration.sh'"
echo "will not ask for confirmation but starts restoration right away when you start the script."
echo
echo "Internet connection is required for the restoration."
echo
echo "NOTE !!!!!!! It is very important that you restore FreeLCS onto the same Linux distro"
echo "and version that it was originally installed on. There are some differences between"
echo "Linux versions and FreeLCS adjusts the installation according to these differences."
echo "FreeLCS might not work correctly if restored onto a wrong distro or version."
echo

exit

