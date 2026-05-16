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
		
	except IOError as reason_for_error:
		error_message = 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	except OSError as reason_for_error:
		error_message = 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	# Open files we used as stdout and stderr for the external program and read in what the program did output to those files.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler, open(stderr_for_external_command, 'rb') as stderr_commandfile_handler:
			command_stdout = stdout_commandfile_handler.read(None)
			command_stderr = stderr_commandfile_handler.read(None)

	except IOError as reason_for_error:
		error_message = 'Stdout- tai stderr - tiedoston lukeminen epäonnistui ajettaessa komentoa: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()
	except OSError as reason_for_error:
		error_message = 'Stdout- tai stderr - tiedostoon lukeminen epäonnistui ajettaessa komentoa: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()
	
	# Delete the temporary stdout and stderr - files
	try:
		os.remove(stdout_for_external_command)
		os.remove(stderr_for_external_command)

	except IOError as reason_for_error:
		error_message = 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()
	except OSError as reason_for_error:
		error_message = 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' + ' '.join(command_to_run) + '. ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	if len(command_stderr) > 0:
		command_run_stderr_utf8 = command_stderr.decode('UTF-8').strip()
		print()
		print("Komennon suoritus tulosti virheilmoituksen: " + command_run_stderr_utf8)
		print()

	return command_stdout.decode('UTF-8').strip()

def find_files_in_a_directory(filename, source_directory):

	list_of_files_found = []

	try:
		# Get directory listing of a Folder. The 'break' statement stops the for - statement from recursing into subdirectories.
		for path, list_of_directories, list_of_files in os.walk(source_directory):                                                                                                                                              
			break

	except IOError as reason_for_error:
		error_message = 'Lähdehakemistopuun lukeminen epäonnistui ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	except OSError as reason_for_error:
		error_message = 'Lähdehakemistopuun lukeminen epäonnistui ' + str(reason_for_error)
		print()
		print(error_message)
		print()

	for item in list_of_files:

		if item.startswith(os.path.basename(filename)) == True:
			list_of_files_found.append(item)

	return(list_of_files_found)

def create_timestamp():

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
	
	time_string= year + '.' + month + '.' + day + ' at ' + hours + ':' + minutes + ':' + seconds
	
	return(time_string)
	
############################
# Main program starts here #
############################
debug = False
user_given_target_dir = ""

if len(sys.argv) > 1:
	user_given_target_dir = sys.argv[1]

	if debug == True:
		print()
		print("user_given_target_dir:", user_given_target_dir)

if user_given_target_dir != "":

	if os.path.exists(user_given_target_dir) == False or os.path.isdir(user_given_target_dir) == False:
		print()
		print("Path does not exists:", user_given_target_dir)
		sys.exit(1)

# Check that we can find the docker executable
docker_path = '/usr/bin/docker'

if not os.path.exists(docker_path):
	print("Docker executable bot found in path:", docker_path)
	sys.exit(1)

# Get path to user home directory
user_home_dir = os.path.expanduser("~")

if debug == True:
	print()
	print("user_home_dir:", user_home_dir)

# Find the names of freelcs docker images
command_to_run = ['docker', 'ps']
command_output = run_external_command(command_to_run)

# Get timestamp we need for the file name
time_string = create_timestamp()

# Remove the first row of headlines
command_output = command_output.split("\n")
image_names = []

# Compile image and backfile names in list
for text_line in command_output:

	if "freelcs" not in text_line:
		continue

	items_on_the_text_line = text_line.split()
	image_name = items_on_the_text_line[1]
	backup_file_name = image_name + "-" + time_string.replace(" ", "_") + ".tar"
	image_names.append([backup_file_name, image_name])

if debug == True:
	print(image_names)

target_dir = ""
if user_given_target_dir == "":
	target_dir = user_home_dir + os.sep + "freelcs_docker_image_backups"
else:
	target_dir = user_given_target_dir + os.sep + "freelcs_docker_image_backups"


if debug == True:
	print()
	print("target_dir:", target_dir)

# There needs to be a couple of directories in the target path, if they do not exist create them.
if (not os.path.exists(target_dir)):
	os.makedirs(target_dir)

# Backup FreeLCS image files
for names in image_names:

	backup_file_name = target_dir + os.sep + names[0]
	image_name = names[1]

	print()
	print("Backing up docker image to:", backup_file_name)

	command_to_run = ['docker', 'save', '-o', backup_file_name, image_name]
	command_output = run_external_command(command_to_run)

	if command_output != "":
		print("command_output:", command_output)

	print("Compressing backup file to: ", backup_file_name + ".gz")
	command_to_run = ['gzip', backup_file_name]
	command_output = run_external_command(command_to_run)

	if command_output != "":
		print("command_output:", command_output)

# TODO
# Get timestamps of backup files and delete old ones


