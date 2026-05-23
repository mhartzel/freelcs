#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#

import os
import sys
import time
import subprocess

def run_external_command(command_to_run):

	directory_for_temporary_files = os.sep + "tmp" + os.sep

	command_stdout = ''
	command_stderr = ''

	try:
		# Define filenames for temporary files that we are going to use as stdout and stderr for the external command.
		stdout_for_external_command = directory_for_temporary_files + '_stdout.txt'
		stderr_for_external_command = directory_for_temporary_files + '_stderr.txt'

		# Open the stdout and stderr temporary files in binary write mode.
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler, open(stderr_for_external_command, 'wb') as stderr_commandfile_handler:
		
			# Run Linux command
			subprocess.Popen(command_to_run, stdout=stdout_commandfile_handler, stderr=stderr_commandfile_handler, stdin=None, close_fds=True).communicate()
			
			# Make sure all data written to temporary stdout and stderr - files is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
			stderr_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stderr_commandfile_handler.fileno()) # Flushes os cache to disk
		
	except KeyboardInterrupt:
		print('\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error writing in Stdout- or stderr - file while running: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	except OSError as reason_for_error:
		error_message = 'Error writing in Stdout- or stderr - file while running: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	# Open files we used as stdout and stderr for the external program and read in what the program did output to those files.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler, open(stderr_for_external_command, 'rb') as stderr_commandfile_handler:
			command_stdout = stdout_commandfile_handler.read(None)
			command_stderr = stderr_commandfile_handler.read(None)

	except KeyboardInterrupt:
		print('\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading in Stdout- or stderr - file while running: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()
	except OSError as reason_for_error:
		error_message = 'Error reading in Stdout- or stderr - file while running: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()
	
	# Delete the temporary stdout and stderr - files
	try:
		os.remove(stdout_for_external_command)
		os.remove(stderr_for_external_command)

	except KeyboardInterrupt:
		print('\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error deleting Stdout- or stderr - file while running: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()
	except OSError as reason_for_error:
		error_message = 'Error deleting Stdout- or stderr - file while running: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	if len(command_stderr) > 0:
		command_run_stderr_utf8 = command_stderr.decode('UTF-8').strip()
		print()
		print("Error: " + command_run_stderr_utf8)
		print()

	return command_stdout.decode('UTF-8').strip()

def find_files_in_a_directory(filename_filter, source_directory):

	list_of_files_found = []

	try:
		# Get directory listing of a Folder. The 'break' statement stops the for - statement from recursing into subdirectories.
		for path, list_of_directories, list_of_files in os.walk(source_directory):                                                                                                                                              
			break

	except KeyboardInterrupt:
		print('\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading source directory ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	except OSError as reason_for_error:
		error_message = 'Error reading source directory ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	for item in list_of_files:

		if filename_filter in item:
			list_of_files_found.append(item)

	return(list_of_files_found)

def create_timestamp(return_date = True, return_time = True, return_unix_ticks = False):

	time_int = time.time()
	
	# Parse time and expand one digit values to two (7 becomes 07).
	year = str(time.localtime(time_int).tm_year)
	month = str(time.localtime(time_int).tm_mon)
	day = str(time.localtime(time_int).tm_mday)
	hours = str(time.localtime(time_int).tm_hour)
	minutes = str(time.localtime(time_int).tm_min)
	seconds = str(time.localtime(time_int).tm_sec)

	# The length of each time string is either 1 or 2. Subtract the string length from number 2 and use the result to count how many zeroes needs to be before the time string.
	month = str('0' *( 2 - len(str(month))) + str(month))
	day = str('0' * (2 - len(str(day))) + str(day))
	hours = str('0' * (2 - len(str(hours))) + str(hours))
	minutes = str('0' *( 2 - len(str(minutes))) + str(minutes))
	seconds = str('0' * (2 - len(str(seconds))) + str(seconds))

	date_string = ""
	time_string = ""

	if return_date == True:
		date_string = year + '.' + month + '.' + day

	if return_time == True:
		time_string = hours + ':' + minutes + ':' + seconds

	if return_unix_ticks == False:
		time_int = 0
	
	return(date_string, time_string, str(int(time_int)))

	
############################
# Main program starts here #
############################
debug = False
backups_to_keep_found = False
backups_to_keep = 10
backupdir_found = False
user_given_backupdir = ""
freelcs_dockerfile_dir_found = False
freelcs_dockerfile_dir = ""

for item in sys.argv[1:]:

	if item.lower() in [ '-backups_to_keep', '-k' ]:
		backups_to_keep_found = True
		continue

	if item.lower() in ['-backup_dir', '-b']:
		backupdir_found = True
		continue

	if item in [ '-freelcs_dockerfile_dir', '-d']:
		freelcs_dockerfile_dir_found = True
		continue

	if backups_to_keep_found == True:
		backups_to_keep = int(item)
		backups_to_keep_found = False
		continue

	if backupdir_found == True:
		user_given_backupdir = item
		backupdir_found = False
		continue

	if freelcs_dockerfile_dir_found == True:
		freelcs_dockerfile_dir = item
		freelcs_dockerfile_dir_found = False
		continue

if debug == True:
	print()
	print("backups_to_keep:", backups_to_keep)
	print("user_given_backupdir:", user_given_backupdir)
	print("freelcs_dockerfile_dir:", freelcs_dockerfile_dir)
	print()

if user_given_backupdir == "" or freelcs_dockerfile_dir == "" or sys.argv[1].startswith("-h") or sys.argv[1].startswith("--h"):
	print()
	print("This program will backup freelcs docker images and then shut them down and upgrade base ubuntu image" )
	print("with latest security updates. Then freelcs docker images will be rebuilt with the ubuntu image and started up." )
	print()
	print("Set this program to automatically run weekly right before your host machine Linux security updates.")
	print()
	print("Usage:")
	print("./backup_and_upgrade_freelcs_images.py -backups_to_keep 12 -backup_dir /home/mikael/Downloads -freelcs_dockerfile_dir /home/mikael/freelcs")
	print()
	print("Or")
	print()
	print("./backup_and_upgrade_freelcs_images.py -k 12 -b /home/mikael/Downloads -d /home/mikael/freelcs")
	print()
	print("-k or -backups_to_keep: Keep this many latest freelcs backups and delete others.")
	print("-b or -backup-dir: Directory named 'freelcs_docker_image_backups' will be create in backup_dir for backup files")
	print("-d or -freelcs_dockerfile_dir: Directory where freelcs compose.yml and Dockerfile are located.")
	print("")
	print("")
	print()
	sys.exit(0)

if user_given_backupdir != "":
	temp_tuple = create_timestamp(return_date = True, return_time = True, return_unix_ticks = False)
	date_string = temp_tuple[0]
	time_string = temp_tuple[1]

	if os.path.exists(user_given_backupdir) == False or os.path.isdir(user_given_backupdir) == False:
		print()
		print(date_string, time_string, "Path does not exists:", user_given_backupdir)
		sys.exit(1)

# Check that we can find the docker executable
docker_path = '/usr/bin/docker'

if not os.path.exists(docker_path):
	temp_tuple = create_timestamp(return_date = True, return_time = True, return_unix_ticks = False)
	date_string = temp_tuple[0]
	time_string = temp_tuple[1]

	print(date_string, time_string, "Docker executable not found in path:", docker_path)
	sys.exit(1)

# Get path to user home directory
user_home_dir = os.path.expanduser("~")

if debug == True:
	print("user_home_dir:", user_home_dir)

# Find the names of freelcs docker images
command_to_run = [docker_path, 'ps', '-a']

if debug == True:
	print("command_to_run:", command_to_run)

command_output = run_external_command(command_to_run)

freelcs_image_names = []

for text_line in command_output.split("\n"):

	if "freelcs" not in text_line:
		continue
	freelcs_image_names.append(text_line)

if len(text_line) == 0:
	temp_tuple = create_timestamp(return_date = True, return_time = True, return_unix_ticks = False)
	date_string = temp_tuple[0]
	time_string = temp_tuple[1]

	print(date_string, time_string, "docker ps -a did not list any images")
	sys.exit(0)

# Get timestamp we need for the file name
temp_tuple = create_timestamp(return_date = True, return_time = False, return_unix_ticks = True)
backupfile_date_string = temp_tuple[0]
backupfile_unix_ticks = temp_tuple[2]

# Remove the first row of headlines
image_names = []

# Compile image and backfile names in list
for text_line in freelcs_image_names:

	if "freelcs" not in text_line:
		continue

	items_on_the_text_line = text_line.split()
	image_name = items_on_the_text_line[1]
	backup_file_name = backupfile_unix_ticks + "-" + image_name + "-" + backupfile_date_string + ".tar"
	image_names.append([backup_file_name, image_name])

if debug == True:
	print(image_names)

backupdir = ""
if user_given_backupdir == "":
	backupdir = user_home_dir + os.sep + "freelcs_docker_image_backups"
else:
	backupdir = user_given_backupdir + os.sep + "freelcs_docker_image_backups"


if debug == True:
	print()
	print("backupdir:", backupdir)

# There needs to be a couple of directories in the target path, if they do not exist create them.
if (not os.path.exists(backupdir)):
	os.makedirs(backupdir)

document_file_name = backupdir + os.sep + "00-How_To_Restore_Docker_Image_Backups.txt"

# Write a text document to the backup directory describing how to restore backups
if (not os.path.exists(document_file_name)):

	restore_instructions = [\
			"", \
			"How to restore Docker image backups:", \
			"------------------------------------", \
			"", \
			"Image backup filenames start with a unix machine readable timestamp that is common to all imagefiles belonging to the same backup.", \
			"The backup / image rotation / image rebuild - script uses the unix timestamp to find files belonging to the same backup.", \
			"After the timestamp there's the image name and the backup date in human readable form.", \
			"", \
			"Backups are gzip compressed so you need to uncompress them and pipe the output to the Docker load - command.", \
			"Each image can be restored with a single command:", \
			"", \
			"gunzip -c /home/mikael/Downloads/freelcs_docker_image_backups/1779019292-freelcs-loudness_correction-2026.05.17.tar.gz | docker load", \
			"gunzip -c /home/mikael/Downloads/freelcs_docker_image_backups/1779019292-freelcs-heartbeat_checker-2026.05.17.tar.gz | docker load", \
			"gunzip -c /home/mikael/Downloads/freelcs_docker_image_backups/1779019292-freelcs-progress_report-2026.05.17.tar.gz | docker load", \
			"", \
			"Image backups will protect you against broken software versions that sometimes slip into Ubuntu updates.", \
			"Fortunately this happens vary rarely, but it is best to guard against it.", \
			"", \
			"You can define how many backups you want to keep when setting up the backup script in cron.", \
			"The number of backups to keep is defined like:", \
			"", \
			"/path/backup_and_update_freelcs_images.py /home/mikael/Downloads 8", \
			"", \
			"This will create the directory: '/home/mikael/Downloads/freelcs_docker_image_backups' and keep the latest 8 backups and delete others.", \
			"The script will also delete FreeLCS Docker images and recreate new ones with the latest security updates.", \
			"", \
			]

	try:
		with open(document_file_name, 'wt') as document_file_handler:
			for item in restore_instructions:
				document_file_handler.write(item + '\n')
			document_file_handler.flush() # Flushes written data to os cache
			os.fsync(document_file_handler.fileno()) # Flushes os cache to disk

	except KeyboardInterrupt:
		print('\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error writing backup restore instructions to a text file in: ' + backupdir + ' ' + reason_for_error
	except OSError as reason_for_error:
		error_message = 'Error writing backup restore instructions to a text file in: ' + backupdir + ' ' + reason_for_error

if len(image_names) == 0:
	print()
	print(date_string, time_string, "No freelcs docker images found")

# Backup FreeLCS image files
for names in image_names:

	backup_file_name = backupdir + os.sep + names[0]
	image_name = names[1]

	temp_tuple = create_timestamp(return_date = True, return_time = True, return_unix_ticks = False)
	date_string = temp_tuple[0]
	time_string = temp_tuple[1]

	print(date_string, time_string, "Backing up docker image to:", backup_file_name)

	command_to_run = [docker_path, 'save', '-o', backup_file_name, image_name]
	command_output = run_external_command(command_to_run)

	if command_output != "":
		print("command_output:", command_output)

	temp_tuple = create_timestamp(return_date = True, return_time = True, return_unix_ticks = False)
	date_string = temp_tuple[0]
	time_string = temp_tuple[1]

	print(date_string, time_string, "Compressing backup file to:", backup_file_name + ".gz")

	command_to_run = ['gzip', backup_file_name]
	command_output = run_external_command(command_to_run)

	if command_output != "":
		print("command_output:", command_output)

# Get FreeLCS backup names from the backup directory
backup_files = find_files_in_a_directory("freelcs", backupdir)

if debug == True:
	print()
	print("Found backup files:")
	print("-------------------")

	for filename in backup_files:
		print(filename)

# Get unigue timestamps from backup files
backupfile_timestamps = []

for filename in backup_files:
	backup_timestamp = filename.split("-")[0]
	backupfile_timestamps.append(backup_timestamp)

unique_backup_timestamps = list(set(backupfile_timestamps))

# Create map for each backup using the unix timestamp in the filename
# as the key and a list of filenames as the value
backups = {}
filenames_in_backup = []

for timestamp in unique_backup_timestamps:
	backups[timestamp] = []

# Insert backup filenames under the timestamp key
for filename in backup_files:
	backup_timestamp = filename.split("-")[0]
	list_of_filenames = backups[backup_timestamp]
	list_of_filenames.append(filename)
	backups[backup_timestamp] = list_of_filenames

sorted_timestamps = list(backups.keys())
sorted_timestamps.sort(reverse= True)

if debug == True:

	print()
	print("type(backups))", type(backups))
	print()
	print("Files in each backup:")
	print("---------------------")

	for item in sorted_timestamps:
		print(item + ":", backups[item])

# Delete old FreeLCS docker image backups and keep as many as user asked to
backups_to_delete = sorted_timestamps[backups_to_keep:]
temp_tuple = create_timestamp(return_date = True, return_time = True, return_unix_ticks = False)
date_string = temp_tuple[0]
time_string = temp_tuple[1]

if debug == True:
	print("backups_to_delete:", backups_to_delete)

if len(backups_to_delete) == 0:
	print(date_string, time_string, "No old backups to delete, keeping:", len(sorted_timestamps), "backups of the maximum of:", backups_to_keep)
	sys.exit(0)
else:
	print(date_string, time_string, "Deleting :", len(backups_to_delete), " old backups and keeping:", backups_to_keep, "most recent.")

	try:
		for backup_to_delete in backups_to_delete:

			filenames = backups[backup_to_delete]

			for filename in filenames:
				os.remove(backupdir + os.sep + filename)
				print("     Deleted :", backupdir + os.sep + filename)

	except KeyboardInterrupt:
		print('\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error deleting file: ' + backup_to_delete + ' ' + str(reason_for_error)
		sys.exit(1)
	except OSError as reason_for_error:
		error_message = 'Error deleting file: ' + backup_to_delete + ' ' + str(reason_for_error)
		sys.exit(1)


