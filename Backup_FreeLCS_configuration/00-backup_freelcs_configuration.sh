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

apt-get -q=2 -y --reinstall install python3 idle3 automake autoconf libtool gnuplot mediainfo build-essential git cmake libsndfile-dev libmpg123-dev libmpcdec-dev libglib2.0-dev libfreetype6-dev librsvg2-dev libspeexdsp-dev libavcodec-dev libavformat-dev libtag1-dev libxml2-dev libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev libqt4-dev $SAMBA_INSTALLATION_COMMAND $SOX_INSTALLATION_COMMAND $ADDITIONAL_PACKAGE_INSTALLATION_COMMANDS 

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


echo
echo "##########################"
echo "# Downloading libebur128 #"
echo "##########################"
echo

cd /tmp
git clone http://github.com/mhartzel/libebur128_fork_for_freelcs_2.4.git

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error downloading libebur128 source code, can not continue."
	echo
	exit
fi

mv libebur128_fork_for_freelcs_2.4 libebur128
cd libebur128

# Get the git commit number of current version of libebur128
echo
LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION="18d1b743b27b810ebf04e012c34105a71c1620b1"
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
echo "#######################################################################################################################"
echo "# Writing libebur128 4.0 and 5.0 and progress bar disable patch to a separate file for patching the libebur128 source #"
echo "#######################################################################################################################"
echo

FULL_PATH_TO_SELF="/tmp/libebur128_download_commands.sh"
FULL_PATH_TO_PATCH="/tmp/libebur128/libebur128_scanner_4.0_and_5.0_channel_mapping_hack.diff"

cat > "$FULL_PATH_TO_PATCH" << 'END_OF_PATCH'
diff --git a/ebur128/ebur128.c b/ebur128/ebur128.c
index 320a6b5..f194d83 100644
--- a/ebur128/ebur128.c
+++ b/ebur128/ebur128.c
@@ -166,6 +166,17 @@ static int ebur128_init_channel_map(ebur128_state* st) {
       default: st->d->channel_map[i] = EBUR128_UNUSED;         break;
     }
   }
+  
+  if (st->channels == 4) {
+	st->d->channel_map[2] = EBUR128_LEFT_SURROUND;
+	st->d->channel_map[3] = EBUR128_RIGHT_SURROUND;
+	}
+
+  if (st->channels == 5) {
+	st->d->channel_map[3] = EBUR128_LEFT_SURROUND;
+	st->d->channel_map[4] = EBUR128_RIGHT_SURROUND;
+	}
+
   return EBUR128_SUCCESS;
 }
 
diff --git a/scanner/inputaudio/ffmpeg/input_ffmpeg.c b/scanner/inputaudio/ffmpeg/input_ffmpeg.c
index f41d0c9..f3600f8 100644
--- a/scanner/inputaudio/ffmpeg/input_ffmpeg.c
+++ b/scanner/inputaudio/ffmpeg/input_ffmpeg.c
@@ -177,6 +177,7 @@ close_file:
 }
 
 static int ffmpeg_set_channel_map(struct input_handle* ih, int* st) {
+  return 1;
   if (ih->codec_context->channel_layout) {
     unsigned int channel_map_index = 0;
     int bit_counter = 0;
diff --git a/scanner/inputaudio/gstreamer/input_gstreamer.c b/scanner/inputaudio/gstreamer/input_gstreamer.c
index 6f28822..9f3663e 100644
--- a/scanner/inputaudio/gstreamer/input_gstreamer.c
+++ b/scanner/inputaudio/gstreamer/input_gstreamer.c
@@ -256,6 +256,7 @@ static int gstreamer_open_file(struct input_handle* ih, const char* filename) {
 }
 
 static int gstreamer_set_channel_map(struct input_handle* ih, int* st) {
+  return 0;
   gint j;
   for (j = 0; j < ih->n_channels; ++j) {
     switch (ih->channel_positions[j]) {
diff --git a/scanner/inputaudio/sndfile/input_sndfile.c b/scanner/inputaudio/sndfile/input_sndfile.c
index aee098b..79e0f04 100644
--- a/scanner/inputaudio/sndfile/input_sndfile.c
+++ b/scanner/inputaudio/sndfile/input_sndfile.c
@@ -60,6 +60,7 @@ static int sndfile_open_file(struct input_handle* ih, const char* filename) {
 }
 
 static int sndfile_set_channel_map(struct input_handle* ih, int* st) {
+  return 1;
   int result;
   int* channel_map = (int*) calloc((size_t) ih->file_info.channels, sizeof(int));
   if (!channel_map) return 1;
diff --git a/scanner/scanner-common/scanner-common.c b/scanner/scanner-common/scanner-common.c
index 3a65db0..417dfad 100644
--- a/scanner/scanner-common/scanner-common.c
+++ b/scanner/scanner-common/scanner-common.c
@@ -331,16 +331,19 @@ void process_files(GSList *files, struct scan_opts *opts) {
 
     // Start the progress bar thread. It misuses progress_mutex and
     // progress_cond to signal when it is ready.
-    g_mutex_lock(progress_mutex);
-    progress_bar_thread = g_thread_create(print_progress_bar,
-                                          &started, TRUE, NULL);
-    while (!started)
-        g_cond_wait(progress_cond, progress_mutex);
-    g_mutex_unlock(progress_mutex);
+    //
+    // Note progress bar causes hangs sometimes and this is why progress bar is disabled when using libebur128 with FreeLCS
+    //
+    // g_mutex_lock(progress_mutex);
+    // progress_bar_thread = g_thread_create(print_progress_bar,
+    //                                       &started, TRUE, NULL);
+    // while (!started)
+    //     g_cond_wait(progress_cond, progress_mutex);
+    // g_mutex_unlock(progress_mutex);
 
     pool = g_thread_pool_new((GFunc) init_state_and_scan_work_item,
                              opts, nproc(), FALSE, NULL);
     g_slist_foreach(files, (GFunc) init_state_and_scan, pool);
     g_thread_pool_free(pool, FALSE, TRUE);
-    g_thread_join(progress_bar_thread);
+    // g_thread_join(progress_bar_thread);
 }
diff --git a/scanner/scanner.c b/scanner/scanner.c
index d952f80..05fcd7e 100644
--- a/scanner/scanner.c
+++ b/scanner/scanner.c
@@ -90,6 +90,10 @@ static void print_help(void) {
     printf("  -m, --momentary=INTERVAL   print momentary loudness every INTERVAL seconds\n");
     printf("  -s, --shortterm=INTERVAL   print shortterm loudness every INTERVAL seconds\n");
     printf("  -i, --integrated=INTERVAL  print integrated loudness every INTERVAL seconds\n");
+    printf("\n");
+    printf("  Patched to support 4.0 (L, R, LS, RS) and 5.0 (L, R, C, LS, RS) files.\n");
+    printf("  Patched to disable progress bar.\n");
+    printf("\n");
 }
 
 static gboolean recursive = FALSE;

END_OF_PATCH


echo
echo "########################################################################"
echo "# Applying libebur128 4.0 and 5.0 - channel patch to libebur128 source #"
echo "########################################################################"
echo

OUTPUT_FROM_PATCHING=`git apply --whitespace=nowarn "$FULL_PATH_TO_PATCH" 2>&1`

# Check if applying patch produced an error

case "$OUTPUT_FROM_PATCHING" in
	*error*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;
	*cannot*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;
	*fatal*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;
	*) echo "libebur128 patched successfully :)" ;;
esac
echo

echo
echo "###############################################"
echo "# Preparing libebur128 source for compilation #"
echo "###############################################"
echo

cd /tmp/libebur128
mkdir build
cd build
cmake -DUSE_AVFORMAT=False -Wno-dev -DCMAKE_INSTALL_PREFIX:PATH=/usr ..

echo
echo "#######################################"
echo "# Compiling and installing libebur128 #"
echo "#######################################"
echo

cd /tmp/libebur128/build
make -s -j 4

if [ "$?" -ne "0"  ] ; then
	echo
	echo "Error compiling libebur128, can not continue."
	echo
	exit
fi

make install


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

