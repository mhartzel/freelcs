#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Mikael Hartzell 2013.
#
# This program is distributed under the GNU General Public License, version 3 (GPLv3)

# This program is used to automatically test a set of known test files with all relevant LoudnessCorrection.py settings.
# This means the program runs through the same test files with and without FFmpeg and using sample peak and truepeak measurement.
# Test results are compared agains a known good set of results created using a previous stable version of LoudnessCorrection.py
# Test results a written to a file and optionally sent to the admin by email.

import time
import os
import sys
import shutil
import subprocess
import pickle
import smtplib
import email
import email.mime
import email.mime.text
import email.mime.multipart
import copy

def read_text_lines_in_mediainfo_files_to_dictionary(directory_for_mediainfo_files):
	
	mediainfo_results_dict = {}
	global list_of_test_result_text_lines
	error_happened = False
	error_message = ''
	path = ''
	list_of_directories = []
	list_of_files = []
	
	# Read the mediainfo files and input text lines to a dictionary.
	try:																																			  
		# Get directory listing for target directory. The 'break' statement stops the for - statement from recursing into subdirectories.
		for path, list_of_directories, list_of_files in os.walk(directory_for_mediainfo_files):
			break
		
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading directory listing ' + str(reason_for_error)
		error_happened = True
	except OSError as reason_for_error:
		error_message = 'Error reading directory listing ' + str(reason_for_error)
		error_happened = True
	
	# Get text lines from mediainfo files and store them in a dictionary.
	for filename in list_of_files:

		with open(directory_for_mediainfo_files + os.sep + filename, 'r') as file_handler:

			list_of_text_lines = file_handler.readlines()

		# Remove empty lines from the end.
		while (list_of_text_lines[-1] == ''):
			del list_of_text_lines[-1]

		mediainfo_results_dict[filename] = list_of_text_lines

	return(mediainfo_results_dict, error_happened, error_message)

def assign_results_of_loudness_corrected_files_to_dictionary(list_of_results):

	info_for_one_file = []
	file_name = ''
	file_loudness = ''
	mediainfo_results_dict = {}

	# Get loudness measurement results for loudness correcetd and store them in a dictionary.
	for text_line in list_of_results:

		if text_line == '':
			continue

		info_for_one_file = text_line.split()
		file_name = ' '.join(info_for_one_file[2:])
		file_loudness = info_for_one_file[0]

		mediainfo_results_dict[file_name] = file_loudness

	return(mediainfo_results_dict)

def find_differences_in_two_result_dictionaries(mediainfo_1_dict, mediainfo_2_dict):

	# Make a copy of the dictionaries where filenames that are found in both can be deleted, leaving only filenames that are not in both lists.
	local_source_dict_1 = copy.deepcopy(mediainfo_1_dict)
	local_source_dict_2 = copy.deepcopy(mediainfo_2_dict)
	local_dict_identical_results = {}
	local_dict_differing_results = {}

	file1_text_lines = []
	file2_text_lines = []

	# Find filenames that are in both dictionaries and compare calculation results from both dictionaries to each other.
	for filename in mediainfo_1_dict:

		if filename in mediainfo_2_dict:

			file1_text_lines = local_source_dict_1.pop(filename)
			file2_text_lines = local_source_dict_2.pop(filename)

			if file1_text_lines == file2_text_lines:

				local_dict_identical_results[filename] = file1_text_lines
			else:
				local_dict_differing_results[filename] = [file1_text_lines, file2_text_lines]

	return (local_dict_identical_results, local_dict_differing_results, local_source_dict_1, local_source_dict_2)

def read_a_text_file(file_name):

	# Read the text lines from a file.
	binary_content_of_file = b''
	text_content_of_file = ''
	error_happened = False
	error_message = ''

	try:
		with open(file_name, 'rb') as file_handler:
			file_handler.seek(0) # Make sure that the 'read' - pointer is in the beginning of the source file 
			binary_content_of_file = file_handler.read()

	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading textfile: ' + str(reason_for_error)
		error_happened = True
	except OSError as reason_for_error:
		error_message = 'Error reading textfile: ' + str(reason_for_error)
		error_happened = True
	except EOFError as reason_for_error:
		error_message = 'Error reading textfile: ' + str(reason_for_error)
		error_happened = True

	text_content_of_file = str(binary_content_of_file.decode('UTF-8'))

	return(text_content_of_file, error_happened, error_message)

def write_a_list_of_text_to_a_file(list_of_data, target_file):

	# This subroutine is used to write data to a text file.

	error_happened = False
	error_message = ''
	data_to_write = '\n'.join(list_of_data)

	try:
		with open(target_file, 'at') as textfile_handler:
			textfile_handler.write(data_to_write)
			textfile_handler.flush() # Flushes written data to os cache
			os.fsync(textfile_handler.fileno()) # Flushes os cache to disk

	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_happened = True
		error_message = 'Error opening file for writing ' + str(reason_for_error)
	except OSError as reason_for_error:
		error_happened = True
		error_message = 'Error opening file for writing ' + str(reason_for_error)

	return(error_happened, error_message)

def delete_files_from_a_directory(file_extension_for_files_to_delete, target_directory):

	path = ''
	list_of_directories = []
	list_of_files = []

	error_happened = False
	error_message = ''

	# Get directory listing. The 'break' statement stops the for - statement from recursing into subdirectories.
	for path, list_of_directories, list_of_files in os.walk(target_directory):
		break

	for filename in list_of_files:

		if (file_extension_for_files_to_delete == '*') or (os.path.splitext(filename)[1] == file_extension_for_files_to_delete):

			targetfile = target_directory + os.sep + filename

			try:
				os.remove(targetfile)

			# Error routines for possible errors linking files
			except KeyboardInterrupt:
				print('\n\nUser cancelled operation.\n')
				sys.exit(1)
			# If there is an error, do not stop but gather filenames and errors and print them later
			except IOError as reason_for_error:
				error_happened = True
				error_message = 'Error deleting: ' + targetfile + str(reason_for_error)
			except OSError as reason_for_error:
				error_happened = True
				error_message = 'Error deleting: ' + targetfile + str(reason_for_error)

	return(error_happened, error_message)

def link_test_files_to_target_directory(list_of_testfile_paths, target_directory):

	error_happened = False
	error_message = ''

	for sourcefile in list_of_testfile_paths:

		targetfile = target_directory + os.sep + os.path.split(sourcefile)[1]
		try:
			os.link(sourcefile, targetfile)

		# Error routines for possible errors linking files
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n')
			sys.exit(1)
		# If there is an error, do not stop but gather filenames and errors and print them later
		except IOError as reason_for_error:
			error_happened = True
			error_message = 'Error linking: ' + sourcefile + str(reason_for_error)
		except OSError as reason_for_error:
			error_happened = True
			error_message = 'Error linking: ' + sourcefile + str(reason_for_error)

	return(error_happened, error_message)

def read_in_file_names(target_path):

	path = ''
	list_of_directories = []
	list_of_files = []
	list_of_testfile_paths = []

	# Get directory listing. The 'break' statement stops the for - statement from recursing into subdirectories.
	for path, list_of_directories, list_of_files in os.walk(target_path):

		for filename in list_of_files:

			list_of_testfile_paths.append(path + os.sep + filename)

	return(list_of_testfile_paths)

def test_that_hotfolder_and_test_files_are_on_the_same_partition(sourcedir, targetdir):

	# Check if source and target are on separate physical disk. This is later used to read source and target simultaneously if they are on separate disks.
	# The check only works on OS X and Linux. If we are not running on either of these, assume source and target are on same physical disk.
	source_and_target_are_on_same_disk = False # Assume by default that source and target dirs are on different disks.
	source_disk_device=''
	target_disk_device=''

	# Parse shell command 'df' to find out what disk device the source dir is on.
	temp1=''
	temp2=''
	command_output = subprocess.Popen(["df", "-P", sourcedir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
	temp1=str(command_output).split('\\n') # Split df output by lines using carrage return ('\n').
	temp2=str(temp1[1]).split() # The second item (second line df printed) has the device name, split the second line to separate items.
	if len(temp1)==3: # If df printed 3 lines of text ('temp1 is equal to 3), then df printed valid information about the disk device, else df did not find device name (df error message = 2 lines of text).
		source_disk_device = temp2[0] # Get source dir disk device name.

	# Parse shell command 'df' to find out what disk device the target dir is on.
	temp1=''
	temp2=''
	command_output = subprocess.Popen(["df", "-P", targetdir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
	temp1=str(command_output).split('\\n') # Split df output by lines using carrage return ('\n').
	temp2=str(temp1[1]).split() # The second item (second line df printed) has the device name, split the second line to separate items.
	if len(temp1)==3: # If df printed 3 lines of text ('temp1 is equal to 3), then df printed valid information about the disk device, else df did not find device name (df error message = 2 lines of text).
		target_disk_device = temp2[0] # Get target dir disk device name.

	if not (source_disk_device =='') and not (target_disk_device == ''): 
		if source_disk_device == target_disk_device:
			source_and_target_are_on_same_disk = True

	return(source_and_target_are_on_same_disk)

def get_version_of_loudnesscorrection_script(path_to_loudnesscorrection_script):

	commands_to_run = ['/bin/grep', "version = '", path_to_loudnesscorrection_script]
	loudness_correction_version = 0

	list_of_command_output = []
	error_happened = False
	list_of_errors = []

	list_of_command_output, error_happened, list_of_errors = run_external_program(commands_to_run)

	list_of_command_output = str(list_of_command_output[0]).split()

	if len(list_of_command_output) >= 3:
		loudness_correction_version = list_of_command_output[2].strip('"').strip("'")

	return(loudness_correction_version)

def move_files_to_a_new_directory(source_directory, target_directory):

	path = ''
	list_of_directories = []
	list_of_files = []

	if not os.path.exists(target_directory):
		os.makedirs(target_directory)

	# Get directory listing. The 'break' statement stops the for - statement from recursing into subdirectories.
	for path, list_of_directories, list_of_files in os.walk(source_directory):
		break

	for file_name in list_of_files:
		shutil.move(source_directory + os.sep + file_name,   target_directory + os.sep + file_name)

def move_list_of_files_to_target_directory(list_of_source_files, target_directory):

	if not os.path.exists(target_directory):
		os.makedirs(target_directory)

	for file_name in list_of_source_files:
		shutil.move(file_name, target_directory)

def find_matching_filename(target_path, start_of_filename_to_match):

	path = ''
	list_of_directories = []
	list_of_files = []
	matching_filename = ''

	# Get directory listing. The 'break' statement stops the for - statement from recursing into subdirectories.
	for path, list_of_directories, list_of_files in os.walk(target_path):
		break

	for file_name in list_of_files:

		if file_name.startswith(start_of_filename_to_match):

			matching_filename = file_name
			break

	return(matching_filename)

def print_info_about_usage():

	print()
	print('This program is used to automatically test a set of known test files with all relevant LoudnessCorrection.py settings.')
	print('This means the program runs through the same test files with and without FFmpeg and using sample peak and truepeak measurement.')
	print('Test results are compared agains a known good set of results created using a previous stable version of LoudnessCorrection.py')
	print('Test results a written to a file and optionally sent to the admin by email.')
	print()
	print('Note !!!!!! The test files MUST be on the same physical partition as the LoudnessCorrection HotFolder because test files are not copied but linked to the HotFolder !!!!!!!')
	print()
	print()
	print('Usage: regression_tester.py   DIR_OF_TEST_FILES	 PATH_TO_RESULT_COMPARISON_SCRIPT   PATH_TO_KNOWN_GOOD_RESULTS_DIR')
	print()
	print()

	sys.exit(1)

def read_loudnesscorrection_config_file():

	configfile_path = '/etc/Loudness_Correction_Settings.pickle'

	# Read the config variables from a file. The file contains a dictionary with the needed values.
	all_settings_dict = {}
	global email_sending_details

	try:
		with open(configfile_path, 'rb') as configfile_handler:
			all_settings_dict = pickle.load(configfile_handler)
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		print('Error reading configfile: ' + str(reason_for_error))
		sys.exit(1)
	except OSError as reason_for_error:
		print('Error reading configfile: ' + str(reason_for_error))
		sys.exit(1)
	except EOFError as reason_for_error:
		print('Error reading configfile: ' + str(reason_for_error))
		sys.exit(1)

	# Configfile was read successfully, assign values from it to our variables overriding script defaults defined in the start of this script.
	if 'hotfolder_path' in all_settings_dict:
		hotfolder_path = all_settings_dict['hotfolder_path']
	if 'directory_for_results' in all_settings_dict:
		directory_for_results = all_settings_dict['directory_for_results']
	if 'directory_for_error_logs' in all_settings_dict:
		directory_for_error_logs = all_settings_dict['directory_for_error_logs']
	if 'email_sending_details' in all_settings_dict:
		email_sending_details = all_settings_dict['email_sending_details']


	return(hotfolder_path, directory_for_results, directory_for_error_logs, email_sending_details)

def run_external_program(commands_to_run):

	list_of_errors = []
	list_of_command_output = []
	error_happened = False
	directory_for_temporary_files = '/tmp'
	stdout = b''
	stderr = b''

	try:
		# Define filenames for temporary files that we are going to use as stdout and stderr for the external command
		stdout_for_external_command = directory_for_temporary_files + os.sep + 'regression_tester_command_stdout.txt'
		stderr_for_external_command = directory_for_temporary_files + os.sep + 'regression_tester_command_stderr.txt'

		# Open the stdout and stderr temporary files in binary write mode.
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler, open(stderr_for_external_command, 'wb') as stderr_commandfile_handler:

			# Run our command.
			subprocess.Popen(commands_to_run, stdout=stdout_commandfile_handler, stderr=stderr_commandfile_handler, stdin=None, close_fds=True).communicate()

			# Make sure all data written to temporary stdout and stderr - files is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
			stderr_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stderr_commandfile_handler.fileno()) # Flushes os cache to disk

	except IOError as reason_for_error:
		error_message = 'Error writing to stdout- or stderr - file when running command: ' + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		list_of_errors.append(error_message)
	except OSError as reason_for_error:
		error_message = 'Error writing to stdout- or stderr - file when running command: ' + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		list_of_errors.append(error_message)

	# Open files we used as stdout and stderr for the external program and read in what the program did output to those files.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler, open(stderr_for_external_command, 'rb') as stderr_commandfile_handler:
			stdout = stdout_commandfile_handler.read(None)
			stderr = stderr_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_happened = True
		error_message = 'Error writing to stdout- or stderr - file when running command: ' + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		list_of_errors.append(error_message)
	except OSError as reason_for_error:
		error_happened = True
		error_message = 'Error writing to stdout- or stderr - file when running command: ' + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		list_of_errors.append(error_message)

	stdout = str(stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	stderr = str(stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.

	if len(stdout) != 0:
		list_of_command_output = stdout.splitlines()

	if len(stderr) != 0:
		list_of_errors.extend(stderr.splitlines())
	# Delete the temporary stdout and stderr - files
	try:
		os.remove(stdout_for_external_command)
		os.remove(stderr_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting stdout- or stderr - file: ' + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		list_of_errors.append(error_message)
	except OSError as reason_for_error:
		error_message = 'Error deleting stdout- or stderr - file: ' + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		list_of_errors.append(error_message)

	return(list_of_command_output, error_happened, list_of_errors)

def get_realtime():

	'''Get current time and return it so that each digit is two numbers wide (7 becomes 07)'''

	# Get current time and put hours, minutes and seconds in to their own variables.
	unix_time_in_ticks = time.time()
	current_time = time.localtime(unix_time_in_ticks)
	year = current_time.tm_year
	month = current_time.tm_mon
	day = current_time.tm_mday
	hours = current_time.tm_hour
	minutes = current_time.tm_min
	seconds = current_time.tm_sec

	# The length of each time string is either 1 or 2. Subtract the string length from number 2 and use the result to count how many zeroes needs to be before the time string.
	year = str(year)
	month = str('0' * ( 2 - len(str(month))) + str(month))
	day = str('0' * (2 - len(str(day))) + str(day))
	hours = str('0' * (2 - len(str(hours))) + str(hours))
	minutes = str('0' * ( 2 - len(str(minutes))) + str(minutes))
	seconds = str('0' * (2 - len(str(seconds))) + str(seconds))

	# Return the time string.
	realtime = year + '.' + month + '.' + day + '_' + 'at' + '_' + hours + '.' + minutes + '.' + seconds

	return (unix_time_in_ticks, realtime)

def send_email(message_title, message_text_string, message_attachment_path, email_sending_details):

	global list_of_test_result_text_lines

	# Assing email settings read from the configfile to local variables.
	use_tls = email_sending_details['use_tls']
	smtp_server_requires_authentication = email_sending_details['smtp_server_requires_authentication']
	smtp_username = email_sending_details['smtp_username']
	smtp_password = email_sending_details['smtp_password']
	smtp_server_name = email_sending_details['smtp_server_name']
	smtp_server_port = email_sending_details['smtp_server_port']
	message_recipients = email_sending_details['message_recipients']
	message_attachment_path = ''

	# Compile the start of the email message.
	email_message_content = email.mime.multipart.MIMEMultipart()
	email_message_content['From'] = smtp_username
	email_message_content['To'] = ', '.join(message_recipients)
	email_message_content['Subject'] = message_title

	# Append the user given lines of text to the email message.
	email_message_content.attach(email.mime.text.MIMEText(message_text_string.encode('utf-8'), _charset='utf-8'))

	# Read attachment file, encode it and append it to the email message.
	if message_attachment_path != '': # If no attachment path is defined, do nothing.
		 email_attachment_content = email.mime.base.MIMEBase('application', 'octet-stream')
		 email_attachment_content.set_payload(open(message_attachment_path, 'rb').read())
		 email.encoders.encode_base64(email_attachment_content)
		 email_attachment_content.add_header('Content-Disposition','attachment; filename="%s"' % os.path.basename(message_attachment_path))
		 email_message_content.attach(email_attachment_content)

	# Email message is ready, before sending it, it must be compiled  into a long string of characters.
	email_message_content_string = email_message_content.as_string()

	# Start communication with the smtp-server.
	try:
		 mailServer = smtplib.SMTP(smtp_server_name, smtp_server_port, 'localhost', 15) # Timeout is set to 15 seconds.
		 mailServer.ehlo()

		 # Check if message size is below the max limit the smpt server announced.
		 message_size_is_within_limits = True # Set the default that is used if smtp-server does not annouce max message size.
		 if 'size' in mailServer.esmtp_features:
			 server_max_message_size = int(mailServer.esmtp_features['size']) # Get smtp server announced max message size
			 message_size = len(email_message_content_string) # Get our message size
			 if message_size > server_max_message_size: # Message is too large for the smtp server to accept, abort sending.
				 message_size_is_within_limits = False
				 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Message_size (' + str(message_size), ') is larger than the max supported size (' + str(server_max_message_size) + ') of server: ' + smtp_server_name + 'Sending aborted.')
				 sys.exit(1)
		 if message_size_is_within_limits == True:
			 # Uncomment the following line if you want to see printed out the final message that is sent to the smtp server
			 # print('email_message_content_string =', email_message_content_string)
			 if use_tls == True:
				 mailServer.starttls()
				 mailServer.ehlo() # After starting tls, ehlo must be done again.
			 if smtp_server_requires_authentication == True:
				 mailServer.login(smtp_username, smtp_password)
			 mailServer.sendmail(smtp_username, message_recipients, email_message_content_string)
		 mailServer.close()

	except smtplib.socket.timeout as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, Timeout error: ' + str(reason_for_error))
	except smtplib.socket.error as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, Socket error: ' + str(reason_for_error))
	except smtplib.SMTPRecipientsRefused as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, All recipients were refused: ' + str(reason_for_error))
	except smtplib.SMTPHeloError as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, The server didn’t reply properly to the HELO greeting: ' + str(reason_for_error))
	except smtplib.SMTPSenderRefused as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, The server didn’t accept the sender address: ' + str(reason_for_error))
	except smtplib.SMTPDataError as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, The server replied with an unexpected error code or The SMTP server refused to accept the message data: ' + str(reason_for_error))
	except smtplib.SMTPException as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, The server does not support the STARTTLS extension or No suitable authentication method was found: ' + str(reason_for_error))
	except smtplib.SMTPAuthenticationError as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, The server didn’t accept the username/password combination: ' + str(reason_for_error))
	except smtplib.SMTPConnectError as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, Error occurred during establishment of a connection with the server: '+ str(reason_for_error))
	except RuntimeError as reason_for_error:
		 list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error, SSL/TLS support is not available to your Python interpreter: ' + str(reason_for_error))

def calculate_duration(start_time, end_time):

	'''This function prints out a progress bar and time estimation and optionally the transfer speed.'''

	time_display_string = '' # This variable holds the estimated time to completion (ETA).

	# Calculate how long it takes to complete the process.
	time_calculation = end_time - start_time

	if time_calculation > 0:

		days = int(time_calculation / 86400)
		time_calculation = time_calculation - (days * 84600)
		hours = int(time_calculation / 3600)
		time_calculation = time_calculation - (hours * 3600)
		minutes = int(time_calculation / 60)
		time_calculation = time_calculation - (minutes * 60)
		seconds = int(time_calculation)

		# Always use two digits when printing time  (1 becomes 01).
		days = str(days)
		temp = 2 - len(days)
		days = '0' * temp + days
		hours = str(hours)
		temp = 2 - len(hours)
		hours = '0' * temp + hours
		minutes = str(minutes)
		temp = 2 - len(minutes)
		minutes = '0' * temp + minutes
		seconds = str(seconds)
		temp = 2 - len(seconds)
		seconds = '0' * temp + seconds

		time_display_string=days + ' days ' + hours + ' hours ' + minutes + ' minutes ' + seconds + ' seconds'

	return(time_display_string)


########
# Main #
########

list_of_result_file_directories = ['ffmpeg-truepeak', 'ffmpeg-samplepeak', 'native-truepeak', 'native-samplepeak']
list_of_result_file_names = ['debug-file_processing_info-', 'debug-variables_lists_and_dictionaries-', 'error_log-', 'measured_loudness_of_loudness_corrected_files.txt', 'loudness_calculation_log-']
list_of_test_result_text_lines = []
text_marginal_1_tabs = '\t'
text_marginal_2_tabs = '\t\t'
last_printed_test_result_text_line = 0

start_time_for_complete_regression_test = 0
stop_time_for_complete_regression_test = 0
start_time_for_individual_test = 0
stop_time_for_individual_test = 0

previous_results_filenames = []
new_results_filenames = []

email_sending_details =  {}
home_directory_for_the_current_user = os.path.expanduser('~')

path_to_loudnesscorrection_script = '/usr/bin/LoudnessCorrection.py'
path_to_loudnesscorrection_config_file = '/etc/Loudness_Correction_Settings.pickle'
list_of_loudnesscorrection_commands_to_run = [[path_to_loudnesscorrection_script, '-configfile', path_to_loudnesscorrection_config_file,'-debug_all' , '-force-truepeak', '-force-quit-when-idle']]
list_of_loudnesscorrection_commands_to_run.append([path_to_loudnesscorrection_script, '-configfile', path_to_loudnesscorrection_config_file,'-debug_all' , '-force-samplepeak', '-force-quit-when-idle'])
list_of_loudnesscorrection_commands_to_run.append([path_to_loudnesscorrection_script, '-configfile', path_to_loudnesscorrection_config_file,'-debug_all' , '-force-truepeak', '-force-quit-when-idle','-force-no-ffmpeg'])
list_of_loudnesscorrection_commands_to_run.append([path_to_loudnesscorrection_script, '-configfile', path_to_loudnesscorrection_config_file,'-debug_all' , '-force-samplepeak', '-force-quit-when-idle', '-force-no-ffmpeg'])

list_of_testfile_paths = []

# There will be 20 source result filenames, initialize the list.
for counter in range(0,4):

	previous_results_filenames.append(['','','','',''])

# There will be 20 target result filenames, initialize the list.
for counter in range(0,4):

	for counter in range(0,5):

		new_results_filenames.append('')

dir_of_test_files = ''
path_to_results_comparison_script = ''
path_to_known_good_results_dir = ''

# Check if command line parameters are sane and assign commandline parameters to variables.
if len(sys.argv) < 3:
	print_info_about_usage()

if os.path.isdir(sys.argv[1]) == True:
	dir_of_test_files = sys.argv[1]
else:
	print()
	print('Path to dir of test files does not exist:', sys.argv[1])
	print()
	print()

	sys.exit(1)

if os.path.isfile(sys.argv[2]) == True:
	path_to_results_comparison_script = sys.argv[2]
else:
	print()
	print('Path to results comparison script does not exist:', sys.argv[2])
	print()
	print()

	sys.exit(1)

if os.path.isdir(sys.argv[3]) == True:
	path_to_known_good_results_dir = sys.argv[3]
	if path_to_known_good_results_dir.endswith(os.sep):
		path_to_known_good_results_dir = path_to_known_good_results_dir[:-1]
else:
	print()
	print('Path to previous results file dir does not exist:', sys.argv[3])
	print()
	print()

	sys.exit(1)

# Check if installed LoudnessCorrection.py and it's config file can be found.
if os.path.exists(path_to_loudnesscorrection_script) == False:
	print()
	print("Error: '" + path_to_loudnesscorrection_script + "' can not be found")
	print()
	sys.exit(1)

if os.path.exists(path_to_loudnesscorrection_config_file) == False:
	print()
	print("Error: '" + path_to_loudnesscorrection_config_file + "' can not be found")
	print()
	sys.exit(1)

loudness_correction_version = get_version_of_loudnesscorrection_script(path_to_loudnesscorrection_script)

if loudness_correction_version == 0:
	print()
	print("Error: can't find out 'LoudnessCorrection.py' version number")
	print()
	sys.exit(1)

# Check if libebur128 scanner is installed.
libebur128_scanner_path = '/usr/bin/loudness'

if os.path.exists(libebur128_scanner_path) == False:
	print()
	print("Error: '" + libebur128_scanner_path + "' can not be found")
	print()
	sys.exit(1)

# Check if mediainfo is installed.
mediainfo_path = '/usr/bin/mediainfo'

if os.path.exists(mediainfo_path) == False:
	print()
	print("Error: '" + mediainfo_path + "' can not be found")
	print()
	sys.exit(1)

list_of_test_result_text_lines.append('')

# Print information gathered so far.
for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
	print(list_of_test_result_text_lines[counter])
last_printed_test_result_text_line = len(list_of_test_result_text_lines)

# If there are some previous regression tests still running, then stop them.
# Find the processes from ps output, keywords are 'LoudnessCorrection.py', '-force-quit-when-idle', '-debug_all' no other process uses all these commandline options.
command_to_run = ['/bin/ps', 'aux']
processes_to_stop = []
list_of_command_output, error_happened, list_of_errors = run_external_program(command_to_run)

for line in list_of_command_output:

	if 'LoudnessCorrection.py' in line:

		if 'python3' in line:

			command_to_run = []
			pid_of_program_to_stop = line.split()[1]
			commandline_of_program_to_stop = ' '.join(line.split()[10:])
			list_of_test_result_text_lines.append('There is a LoudnessCorrection.py running in the background, I am stopping it. PID: ' + str(pid_of_program_to_stop) + ' Commandline: ' + commandline_of_program_to_stop)

			# Print information gathered so far.
			for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
				print(list_of_test_result_text_lines[counter])
			last_printed_test_result_text_line = len(list_of_test_result_text_lines)

			list_of_command_output, error_happened, list_of_errors = run_external_program(['/bin/kill', pid_of_program_to_stop])

# Read in settings from LoudnessCorrection settings file.
hotfolder_path, directory_for_results, directory_for_error_logs, email_sending_details = read_loudnesscorrection_config_file()
directory_for_old_error_logs = directory_for_error_logs + os.sep + '00-Old_Error_Logs'

# Check if path defined in LoudnessCorrection settings file exist, if not create
if os.path.exists(hotfolder_path) == False:
	os.makedirs(hotfolder_path)

if os.path.exists(directory_for_results) == False:
	os.makedirs(directory_for_results)

if os.path.exists(directory_for_error_logs) == False:
	os.makedirs(directory_for_error_logs)


# Tesfiles are linked to the target directory, check that source and target are both on the same physical disk.
source_and_target_are_on_same_disk = False
source_and_target_are_on_same_disk = test_that_hotfolder_and_test_files_are_on_the_same_partition(dir_of_test_files, hotfolder_path)

if source_and_target_are_on_same_disk == False:
	print()
	print('Error: Testfiles needs to be on the same partition as the HotFolder:', hotfolder_path)
	print()
	sys.exit(1)

# Check if previous results files can be found
for counter1 in range(0,4):

	directory_name = path_to_known_good_results_dir + os.sep + list_of_result_file_directories[counter1]

	for counter2 in range(0,5):

		file_name = list_of_result_file_names[counter2]
		name_of_matching_file = ''

		if file_name == list_of_result_file_names[3]:
			if os.path.exists(directory_name + os.sep + 'korjattujen_tiedostojen_aanekkyys.txt') == True: # The file name used to be in finnish, check if a file with the old name can be found.
				file_name = 'korjattujen_tiedostojen_aanekkyys.txt'

		name_of_matching_file = find_matching_filename(directory_name, file_name)

		if name_of_matching_file != '':
			previous_results_filenames[counter1][counter2] = name_of_matching_file
		else:
			if file_name != 'error_log-':
				print()
				print('Error: Can not find previous results file:', directory_name + os.sep + os.sep + file_name)
				print()
				sys.exit(1)

# Read test file names in to a list
list_of_testfile_paths = read_in_file_names(dir_of_test_files)

if len(list_of_testfile_paths) == 0:

	print()
	print("Error: there is zero test files in the path specified")
	print()
	sys.exit(1)

# Check if regression test result dir already exists, if true then delete it.
regression_test_results_target_dir = os.path.split(path_to_known_good_results_dir)[0] + os.sep + loudness_correction_version
if os.path.exists(regression_test_results_target_dir) == True:
	shutil.rmtree(regression_test_results_target_dir)

time_in_ticks_and_string_format = get_realtime()
start_time_for_complete_regression_test = time_in_ticks_and_string_format[0]

title_string = '# Complete Regression Test Started At: ' + time_in_ticks_and_string_format[1] + ' #'
list_of_test_result_text_lines.append('')
list_of_test_result_text_lines.append('#' * len(title_string))
list_of_test_result_text_lines.append(title_string)
list_of_test_result_text_lines.append('#' * len(title_string))
list_of_test_result_text_lines.append('')

# Print information gathered so far.
for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
	print(list_of_test_result_text_lines[counter])
last_printed_test_result_text_line = len(list_of_test_result_text_lines)

# Create directories needed to store regression test results
for path in list_of_result_file_directories:
	os.makedirs(regression_test_results_target_dir + os.sep + path + os.sep + 'mediainfo')
	list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Creating dir: ' + regression_test_results_target_dir + os.sep + path + os.sep + 'mediainfo')
	os.makedirs(regression_test_results_target_dir + os.sep + path + os.sep + 'machine_readable_results')
	list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Creating dir: ' + regression_test_results_target_dir + os.sep + path + os.sep + 'machine_readable_results')

# Print information gathered so far.
for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
	print(list_of_test_result_text_lines[counter])
last_printed_test_result_text_line = len(list_of_test_result_text_lines)

list_of_test_result_text_lines.append('')
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'loudness_correction_version = ' + loudness_correction_version)
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'source_and_target_are_on_same_disk = ' + str(source_and_target_are_on_same_disk))
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'home_directory_for_the_current_user = ' + home_directory_for_the_current_user)
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'hotfolder_path = ' + hotfolder_path)
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'directory_for_results = ' + directory_for_results)
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'directory_for_error_logs = ' + directory_for_error_logs)
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'path_to_known_good_results_dir = ' + path_to_known_good_results_dir)
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'regression_test_results_target_dir = ' + regression_test_results_target_dir)
list_of_test_result_text_lines.append('')
list_of_test_result_text_lines.append(text_marginal_2_tabs + 'email_sending_details')
list_of_test_result_text_lines.append(text_marginal_2_tabs + '----------------------')

if len(email_sending_details) != 0:
	for item in email_sending_details:
		if item == 'smtp_password':
			continue
		list_of_test_result_text_lines.append(text_marginal_2_tabs + item + ' = ' + str(email_sending_details[item]))

list_of_test_result_text_lines.append(text_marginal_2_tabs + 'len(list_of_testfile_paths) = ' + str(len(list_of_testfile_paths)))
list_of_test_result_text_lines.append('')

list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Previous results filenames')
list_of_test_result_text_lines.append(text_marginal_2_tabs + '---------------------------')

for counter in range(0, len(previous_results_filenames)):
	# list_of_result_file_directories

	title_string = list_of_result_file_directories[counter]
	list_of_test_result_text_lines.append(text_marginal_2_tabs + title_string)
	list_of_test_result_text_lines.append(text_marginal_2_tabs + '-' * len(title_string))

	for counter2 in range(0, len(previous_results_filenames[counter])):
		list_of_test_result_text_lines.append(text_marginal_2_tabs + str(previous_results_filenames[counter][counter2]))
	list_of_test_result_text_lines.append('')

list_of_test_result_text_lines.append('')

# Print information gathered so far.
for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
	print(list_of_test_result_text_lines[counter])
last_printed_test_result_text_line = len(list_of_test_result_text_lines)

########################
# Run regression tests #
########################

for test_counter in range(0,4):

	new_results_directory = list_of_result_file_directories[test_counter]
	loudness_correction_test_run_commands = list_of_loudnesscorrection_commands_to_run[test_counter]
	regression_test_log_file_name = regression_test_results_target_dir + os.sep + '00-regression_test_results_log.txt'
	previous_measured_loudness_of_loudness_corrected_files = path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + list_of_result_file_names[3]

	if os.path.exists(path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + 'korjattujen_tiedostojen_aanekkyys.txt') == True: # The file name used to be in finnish, check if a file with the old name can be found.
		previous_measured_loudness_of_loudness_corrected_files = path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + 'korjattujen_tiedostojen_aanekkyys.txt'

	new_measured_loudness_of_loudness_corrected_files = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + list_of_result_file_names[3]
	mediainfo_source_dir = path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + 'mediainfo'
	mediainfo_target_dir = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + 'mediainfo'
	list_of_files = []

	time_in_ticks_and_string_format = get_realtime()
	start_time_for_individual_test = time_in_ticks_and_string_format[0]

	title_string = '# ' + "'" + new_results_directory +"'" + ' Test Started At: ' + time_in_ticks_and_string_format[1] + ' #'
	list_of_test_result_text_lines.append('#' * len(title_string))
	list_of_test_result_text_lines.append(title_string)
	list_of_test_result_text_lines.append('#' * len(title_string))
	list_of_test_result_text_lines.append('')

	# Print information gathered so far.
	for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
		print(list_of_test_result_text_lines[counter])
	last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	loudness_scanner_commands = [libebur128_scanner_path, 'scan']

	# Move old error log files out of the way
	move_files_to_a_new_directory(directory_for_error_logs, directory_for_old_error_logs)

	# Remove files possibly left over in the HotFolder and results dir.
	error_happened, error_message = delete_files_from_a_directory('*', hotfolder_path)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	error_happened, error_message = delete_files_from_a_directory('*', directory_for_results)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	time.sleep(5)

	################################
	# Link test files to HotFolder #
	################################

	error_happened, error_message = link_test_files_to_target_directory(list_of_testfile_paths, hotfolder_path)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)


	#############################
	# Run LoudnessCorrection.py #
	#############################
	list_of_command_output, error_happened, list_of_errors = run_external_program(loudness_correction_test_run_commands)

	######################################################################
	# Move machine readable results files to regression test results dir #
	######################################################################
	list_of_files = []
	file_names_in_path = []
	file_names_in_path = read_in_file_names(directory_for_results)

	for item in file_names_in_path:
		if item.endswith('machine_readable_results.txt'):
			list_of_files.append(item)

	move_list_of_files_to_target_directory(list_of_files, regression_test_results_target_dir + os.sep + new_results_directory + os.sep + 'machine_readable_results')

	#################################################
	# Remove jpg - files from the results directory #
	#################################################
	error_happened, error_message = delete_files_from_a_directory('.jpg', directory_for_results)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)


	##################################################
	# Calculate loudness of loudness corrected files #
	##################################################
	list_of_loudness_corrected_files = []
	list_of_loudness_corrected_files = read_in_file_names(directory_for_results) 
	loudness_scanner_commands.extend(list_of_loudness_corrected_files)
	list_of_command_output, error_happened, list_of_errors = run_external_program(loudness_scanner_commands)

	# Remove last item because it is the loudness sum of all files and we only need individual results.
	del list_of_command_output[-1]
	# Sort the list of results
	list_of_command_output.sort()

	# Write results to the log.

	write_a_list_of_text_to_a_file(list_of_command_output, new_measured_loudness_of_loudness_corrected_files)

	###############################################
	# Get mediainfo from loudness corrected files #
	###############################################
	os.chdir(directory_for_results)
	for item in list_of_loudness_corrected_files:
		file_name = os.path.split(item)[1]
		command_to_run = []
		command_to_run.append(mediainfo_path)
		command_to_run.append('./' + file_name)

		list_of_command_output, error_happened, list_of_errors = run_external_program(command_to_run)

		write_a_list_of_text_to_a_file(list_of_command_output, mediainfo_target_dir + os.sep + file_name + '.txt')

	################################################################
	# Move log files from '00-Error_Logs' to our results directory #
	################################################################
	move_files_to_a_new_directory(directory_for_error_logs, regression_test_results_target_dir + os.sep + new_results_directory)

	#######################################
	# Remove all files from the HotFolder #
	#######################################
	error_happened, error_message = delete_files_from_a_directory('*', hotfolder_path)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)


	###############################################
	# Remove all files from the results directory #
	###############################################
	error_happened, error_message = delete_files_from_a_directory('*', directory_for_results)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)


	###########################################################
	# Check if LoudnessCorrection.py reported critical errors #
	###########################################################
	file_name = find_matching_filename(regression_test_results_target_dir + os.sep + new_results_directory, 'error_log-')

	if file_name != '':
		text_content_of_file, error_happened, error_message = read_a_text_file(regression_test_results_target_dir + os.sep + new_results_directory + os.sep + file_name)

		if error_happened == True:
			list_of_test_result_text_lines.append('')
			list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
			list_of_test_result_text_lines.append('')
			error_happened = False
			error_message = ''

			for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
				print(list_of_test_result_text_lines[counter])
			last_printed_test_result_text_line = len(list_of_test_result_text_lines)

		if 'Critical Python Error' in text_content_of_file:

			list_of_test_result_text_lines.append('')
			list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Error: LoudnessCorrection.py reported critical python errors !!!!!!!')
			list_of_test_result_text_lines.append('')

	# Print information gathered so far.
	for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
		print(list_of_test_result_text_lines[counter])
	last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	##########################################
	# Mediainfo for loudness corrected files #
	##########################################

	# Mediainfo records information like: format, channel count, bit depth, sample rate, duration, so comparing mediainfo - files
	# gives us confidence that all technical aspects of loudness corrected files are as expected

	mediainfo_results_1_dict = {}
	mediainfo_results_2_dict = {}

	# Read in text of mediainfo files to a dictionary (key = filename)
	mediainfo_results_1_dict, error_happened, error_message = read_text_lines_in_mediainfo_files_to_dictionary(mediainfo_source_dir)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	# Read in text of mediainfo files to a dictionary (key = filename)
	mediainfo_results_2_dict, error_happened, error_message = read_text_lines_in_mediainfo_files_to_dictionary(mediainfo_target_dir)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	# Find files that are only in source or only in target. Sets makes it very fast to compare a bunch of filenames.
	filenames_1_set = set(mediainfo_results_1_dict) # Get all source dir filenames from the dictionary to this set.
	filenames_2_set = set(mediainfo_results_2_dict) # Get all target dir filenames from the dictionary to this set.
	filenames_only_in_set_1 = set.difference(filenames_1_set, filenames_2_set) # Get all filenames that exists only in  source
	filenames_only_in_set_2 = set.difference(filenames_2_set, filenames_1_set) # Get all filenames that exists only in  target
	common_filenames_set = set.intersection(filenames_1_set, filenames_2_set) # Get all filenames that exists in both source and target to this set.

	# Store mediainfo data of one filename to dictionary and compare both results (1 file = 2 results)
	mediainfo_files_with_identical_results_list = []
	mediainfo_files_with_differing_results_dict = {}
	mediainfo_files_only_in_path_1_dict = {}
	mediainfo_files_only_in_path_2_dict = {}


	# Split text in mediainfo file and store results in a dictionary (key = field 0 in text line, value = field 1 in text line).
	for file_name in common_filenames_set:
		
		results_for_file_1_list = []
		results_for_file_2_list = []

		results_for_file_1_dict = {}
		results_for_file_2_dict = {}

		results_for_file_1_list = mediainfo_results_1_dict[file_name]
		results_for_file_2_list = mediainfo_results_2_dict[file_name]

		headline = ''

		for item1 in results_for_file_1_list:

			if item1.strip() == '':
				continue

			if ':' not in item1:
				headline = item1.strip()
				continue # This text line is the headline, skip it.

			splitted_text_1 =  item1.split(':')

			results_for_file_1_dict[headline + ' ' + splitted_text_1[0].strip()] = splitted_text_1[1].strip()

		for item2 in results_for_file_2_list:

			if ':' not in item2:
				headline = item2.strip()
				continue # This text line is the headline, skip it.

			splitted_text_2 =  item2.split(':')

			results_for_file_2_dict[headline + ' ' + splitted_text_2[0].strip()] = splitted_text_2[1].strip()

		# Mediainfo: Compare results in the two dictionaries and store results in four dictionaries.
		# Note this compares individual mediainfo result text lines.
		text_lines_with_identical_results_dict = {}
		text_lines_with_differing_results_dict = {}
		text_lines_only_in_path_1_dict = {}
		text_lines_only_in_path_2_dict = {}
		text_lines_with_identical_results_dict, text_lines_with_differing_results_dict, text_lines_only_in_path_1_dict, text_lines_only_in_path_2_dict = find_differences_in_two_result_dictionaries(results_for_file_1_dict, results_for_file_2_dict) 

		# Store list of identical files
		if (len(text_lines_with_identical_results_dict) > 0) and (len(text_lines_with_differing_results_dict) == 0) and (len(text_lines_only_in_path_1_dict) == 0) and (len(text_lines_only_in_path_2_dict) == 0):
			mediainfo_files_with_identical_results_list.append(file_name) 

		# Store info about differing result lines
		if len(text_lines_with_differing_results_dict) > 0:

			result_list = []

			for individual_item in text_lines_with_differing_results_dict:
				adjust_printing1 = ''
				adjust_printing2 = ''
				if len(individual_item + ':') < 40:
					adjust_printing1 = ' ' * int(40 - len(individual_item + ':'))
				if len(str(text_lines_with_differing_results_dict[individual_item][0]) + '|') < 25:
					adjust_printing2 = ' ' * int(25 - len(str(text_lines_with_differing_results_dict[individual_item][0]) + '|'))
				string_to_print = individual_item + ':' + adjust_printing1  + str(text_lines_with_differing_results_dict[individual_item][0]) + adjust_printing2 + '|            ' + str(text_lines_with_differing_results_dict[individual_item][1])
				result_list.append(string_to_print)

			mediainfo_files_with_differing_results_dict[file_name] = result_list

		# Store info about text lines only in file 1
		if len(text_lines_only_in_path_1_dict) > 0:

			result_list = []

			if file_name in mediainfo_files_with_differing_results_dict:
				result_list = mediainfo_files_with_differing_results_dict[file_name]

			for individual_item in text_lines_only_in_path_1_dict:

				adjust_printing1 = ''
				adjust_printing2 = ''
				if len(individual_item + ':') < 40:
					adjust_printing1 = ' ' * int(40 - len(individual_item + ':'))
				if len(str(text_lines_only_in_path_1_dict[individual_item]) + '|') < 25:
					adjust_printing2 = ' ' * int(25 - len(str(text_lines_only_in_path_1_dict[individual_item])  + '|'))

				result_list.append(individual_item + ':' + adjust_printing1  + str(text_lines_only_in_path_1_dict[individual_item]) + adjust_printing2  + '|            ' + '<No value>')

			mediainfo_files_with_differing_results_dict[file_name] = result_list

		# Store info about text lines only in file 2
		if len(text_lines_only_in_path_2_dict) > 0:

			result_list = []

			if file_name in mediainfo_files_with_differing_results_dict:
				result_list = mediainfo_files_with_differing_results_dict[file_name]

			for individual_item in text_lines_only_in_path_2_dict:

				adjust_printing1 = ''
				adjust_printing2 = ''
				if len(individual_item + ':') < 40:
					adjust_printing1 = ' ' * int(40 - len(individual_item + ':'))
				if len('<No value>'  + '|') < 25:
					adjust_printing2 = ' ' * int(25 - len('<No value>'  + '|'))

				result_list.append(individual_item + ':' + adjust_printing1  + '<No value>'  + adjust_printing2 + '|            ' + str(text_lines_only_in_path_2_dict[individual_item]))

			mediainfo_files_with_differing_results_dict[file_name] = result_list

	# Report differences in mediainfo results files
	title_string = '# Mediainfo for loudness corrected files: ' + new_results_directory + ' #'
	list_of_test_result_text_lines.append('')
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))
	list_of_test_result_text_lines.append(text_marginal_1_tabs + title_string)
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))

	# Mediainfo: Show the total number of mediainfo results
	list_of_test_result_text_lines.append('')
	list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Data for ' + str(len(mediainfo_results_1_dict)) + ' files found in path: ' + mediainfo_source_dir)
	list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Data for ' + str(len(mediainfo_results_2_dict)) + ' files found in path: ' + mediainfo_target_dir)

	# Mediainfo: Show Identical files
	if (len(mediainfo_results_1_dict) == len(mediainfo_results_2_dict)) and (len(mediainfo_results_1_dict) == len(mediainfo_files_with_identical_results_list)):

		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Results for all ' + str(len(mediainfo_files_with_identical_results_list)) + ' files are identical :)')
		list_of_test_result_text_lines.append('')
	else:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Results for ' + str(len(mediainfo_files_with_identical_results_list)) + ' files are identical :)')
		list_of_test_result_text_lines.append('')

	# Mediainfo: Show Files with differing results and each individual differing result line.
	if len(mediainfo_files_with_differing_results_dict) != 0:

		# Report any mismatch found.
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + "Mediainfo results for " + str(len(mediainfo_files_with_differing_results_dict)) + " file does not match (Note: mediainfo category title is appended as the beginning of each line)")
		list_of_test_result_text_lines.append(text_marginal_2_tabs + '-' * len("Mediainfo results for " + str(len(mediainfo_files_with_differing_results_dict)) + " file does not match (Note: mediainfo category title is appended as the beginning of each line)") + '-')
		list_of_test_result_text_lines.append('')

		list_of_non_matching_filenames = list(mediainfo_files_with_differing_results_dict)
		list_of_non_matching_filenames.sort(key=str.lower)

		for file_name in list_of_non_matching_filenames: # Get name of each file.

			list_of_test_result_text_lines.append('')
			list_of_test_result_text_lines.append(text_marginal_2_tabs + file_name)
			list_of_test_result_text_lines.append(text_marginal_2_tabs + '-' * int(len(file_name) + 1))
			list_of_test_result_text_lines.append('')

			for differing_item in mediainfo_files_with_differing_results_dict[file_name]:
				list_of_test_result_text_lines.append(text_marginal_2_tabs + differing_item)
			list_of_test_result_text_lines.append('')
		
		list_of_test_result_text_lines.append('')

	# Mediainfo: Show Files only in path 1
	if len(filenames_only_in_set_1) != 0:

		# Report any mismatch found.
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + str(len(filenames_only_in_set_1)) + " Filenames only in: " + mediainfo_source_dir)
		list_of_test_result_text_lines.append(text_marginal_2_tabs + '-' * len(str(len(filenames_only_in_set_1)) + " Filenames only in: " + mediainfo_source_dir) + '-')
		list_of_test_result_text_lines.append('')

		list_of_missing_filenames = []

		list_of_missing_filenames = list(filenames_only_in_set_1)
		list_of_missing_filenames.sort(key=str.lower)

		for item in list_of_missing_filenames:

			list_of_test_result_text_lines.append(text_marginal_2_tabs + item)

		list_of_test_result_text_lines.append('')

	# Mediainfo: Show Files only in path 2
	if len(filenames_only_in_set_2) != 0:

		# Report any mismatch found.
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + str(len(filenames_only_in_set_2)) + " Filenames only in: " + mediainfo_target_dir)
		list_of_test_result_text_lines.append(text_marginal_2_tabs + '-' * len(str(len(filenames_only_in_set_2)) + " Filenames only in: " + mediainfo_target_dir) + '-')
		list_of_test_result_text_lines.append('')

		list_of_missing_filenames = []

		list_of_missing_filenames = list(filenames_only_in_set_2)
		list_of_missing_filenames.sort(key=str.lower)

		for item in list_of_missing_filenames:

			list_of_test_result_text_lines.append(text_marginal_2_tabs + item)

	# Print information gathered so far.
	for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
		print(list_of_test_result_text_lines[counter])
	last_printed_test_result_text_line = len(list_of_test_result_text_lines)


	########################################
	# Loudness of loudness corrected files #
	########################################

	previous_results_as_text = ''
	previous_results_as_list = []
	previous_results_dict = {}
	new_results_as_text = ''
	new_results_as_list = []
	new_results_dict = {}

	previous_results_as_text, error_happened, error_message = read_a_text_file(previous_measured_loudness_of_loudness_corrected_files)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	new_results_as_text, error_happened, error_message = read_a_text_file(new_measured_loudness_of_loudness_corrected_files)

	if error_happened == True:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + error_message)
		list_of_test_result_text_lines.append('')
		error_happened = False
		error_message = ''

		for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
			print(list_of_test_result_text_lines[counter])
		last_printed_test_result_text_line = len(list_of_test_result_text_lines)


	previous_results_as_list = previous_results_as_text.split('\n')
	new_results_as_list = new_results_as_text.split('\n')

	previous_results_dict = assign_results_of_loudness_corrected_files_to_dictionary(previous_results_as_list)
	new_results_dict = assign_results_of_loudness_corrected_files_to_dictionary(new_results_as_list)

	loudness_corrected_files_with_identical_results_dict = {}
	loudness_corrected_files_with_differing_results_dict = {}
	loudness_corrected_files_only_in_path_1_dict = {}
	loudness_corrected_files_only_in_path_2_dict = {}

	# Loudness of loudness corrected files: Compare results in the two dictionaries and store results in four dictionaries.
	loudness_corrected_files_with_identical_results_dict, loudness_corrected_files_with_differing_results_dict, loudness_corrected_files_only_in_path_1_dict, loudness_corrected_files_only_in_path_2_dict = find_differences_in_two_result_dictionaries(previous_results_dict, new_results_dict) 

	# Loudness of loudness corrected files: Show the total number of mediainfo results

	title_string = '# Loudness of loudness corrected files: ' + new_results_directory + ' #'
	list_of_test_result_text_lines.append('')
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))
	list_of_test_result_text_lines.append(text_marginal_1_tabs + title_string)
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))
	list_of_test_result_text_lines.append('')

	list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Data for ' + str(len(previous_results_dict)) + ' files found in path: ' + previous_measured_loudness_of_loudness_corrected_files)
	list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Data for ' + str(len(new_results_dict)) + ' files found in path: ' + new_measured_loudness_of_loudness_corrected_files)

	# Loudness of loudness corrected files: Show Identical files
	if (len(previous_results_dict) == len(new_results_dict)) and (len(previous_results_dict) == len(loudness_corrected_files_with_identical_results_dict)):

		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Results for all ' + str(len(loudness_corrected_files_with_identical_results_dict)) + ' files are identical :)')
		list_of_test_result_text_lines.append('')
	else:
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + 'Results for ' + str(len(loudness_corrected_files_with_identical_results_dict)) + ' files are identical :)')
		list_of_test_result_text_lines.append('')

	# Loudness of loudness corrected files: Show Files with differing results
	if len(loudness_corrected_files_with_differing_results_dict) != 0:

		# Report any mismatch found.
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + str(len(loudness_corrected_files_with_differing_results_dict)) + " Calculation results don't match")
		list_of_test_result_text_lines.append(text_marginal_2_tabs + '-' * len(str(len(loudness_corrected_files_with_differing_results_dict)) + " Calculation results don't match ") + '-')
		list_of_test_result_text_lines.append('')

		list_of_non_matching_filenames = list(loudness_corrected_files_with_differing_results_dict)
		list_of_non_matching_filenames.sort(key=str.lower)

		for item in list_of_non_matching_filenames:

			file1_calculation_results = loudness_corrected_files_with_differing_results_dict[item][0]
			file2_calculation_results = loudness_corrected_files_with_differing_results_dict[item][1]

			# Make the printout prettier by aligning number values to each other.
			string_1_to_print = file1_calculation_results
			string_1_to_print = ' ' * (5 - len(string_1_to_print)) + string_1_to_print
			string_2_to_print = file2_calculation_results
			string_2_to_print = ' ' * (5 - len(string_2_to_print)) + string_2_to_print
			calculation_result_type = 'integrated_loudness\t'
			
			list_of_test_result_text_lines.append(text_marginal_2_tabs + calculation_result_type + '   ' +	string_1_to_print + '	|  ' + string_2_to_print + '	 ' +  item)
		
		list_of_test_result_text_lines.append('')

	# Loudness of loudness corrected files: Show Files only in path 1
	if len(loudness_corrected_files_only_in_path_1_dict) != 0:

		# Report any mismatch found.
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + str(len(loudness_corrected_files_only_in_path_1_dict)) + " Filenames only in: " + previous_measured_loudness_of_loudness_corrected_files)
		list_of_test_result_text_lines.append(text_marginal_2_tabs + '-' * len(str(len(loudness_corrected_files_only_in_path_1_dict)) + " Filenames only in: " + previous_measured_loudness_of_loudness_corrected_files) + '-')
		list_of_test_result_text_lines.append('')

		list_of_missing_filenames = []

		list_of_missing_filenames = list(loudness_corrected_files_only_in_path_1_dict)
		list_of_missing_filenames.sort(key=str.lower)

		for item in list_of_missing_filenames:

			list_of_test_result_text_lines.append(text_marginal_2_tabs + item)

		list_of_test_result_text_lines.append('')

	# Loudness of loudness corrected files: Show Files only in path 2
	if len(loudness_corrected_files_only_in_path_2_dict) != 0:

		# Report any mismatch found.
		list_of_test_result_text_lines.append('')
		list_of_test_result_text_lines.append(text_marginal_2_tabs + str(len(loudness_corrected_files_only_in_path_2_dict)) + " Filenames only in: " + new_measured_loudness_of_loudness_corrected_files)
		list_of_test_result_text_lines.append(text_marginal_2_tabs + '-' * len(str(len(loudness_corrected_files_only_in_path_2_dict)) + " Filenames only in: " + new_measured_loudness_of_loudness_corrected_files) + '-')
		list_of_test_result_text_lines.append('')

		list_of_missing_filenames = []

		list_of_missing_filenames = list(loudness_corrected_files_only_in_path_2_dict)
		list_of_missing_filenames.sort(key=str.lower)

		for item in list_of_missing_filenames:

			list_of_test_result_text_lines.append(text_marginal_2_tabs + item)

		list_of_test_result_text_lines.append('')

	# Print information gathered so far.
	for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
		print(list_of_test_result_text_lines[counter])
	last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	##########################################################################################################################
	# Loudness Calculation Log: Selftest: compare this regression tests loudness calculation log to machine readable results #
	##########################################################################################################################

	title_string = '# Loudness Calculation Log: Selftest: compare this regression tests loudness calculation log to machine readable results: ' + new_results_directory + ' #'
	list_of_test_result_text_lines.append('')
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))
	list_of_test_result_text_lines.append(text_marginal_1_tabs + title_string)
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))

	# path_to_results_comparison_script
	previous_loudness_calculation_log_name = find_matching_filename(regression_test_results_target_dir + os.sep + new_results_directory, list_of_result_file_names[4])
	previous_loudness_calculation_log = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + previous_loudness_calculation_log_name
	new_loudness_calculation_log = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + 'machine_readable_results'

	commands_to_run = [path_to_results_comparison_script, previous_loudness_calculation_log, new_loudness_calculation_log]

	list_of_command_output, error_happened, list_of_errors = run_external_program(commands_to_run)


	if len(list_of_command_output) != 0:

		for item in list_of_command_output:
			list_of_test_result_text_lines.append(text_marginal_2_tabs + item)

	# Print information gathered so far.
	for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
		print(list_of_test_result_text_lines[counter])
	last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	#######################################
	# Loudness Calculation Log Comparison #
	#######################################

	title_string = '# Loudness Calculation Log Comparison: ' + new_results_directory + ' #'
	list_of_test_result_text_lines.append('')
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))
	list_of_test_result_text_lines.append(text_marginal_1_tabs + title_string)
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))

	# path_to_results_comparison_script
	previous_loudness_calculation_log_name = find_matching_filename(path_to_known_good_results_dir + os.sep + new_results_directory, list_of_result_file_names[4])
	previous_loudness_calculation_log = path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + previous_loudness_calculation_log_name
	new_loudness_calculation_log_name = find_matching_filename(regression_test_results_target_dir + os.sep + new_results_directory, list_of_result_file_names[4])
	new_loudness_calculation_log = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + new_loudness_calculation_log_name

	commands_to_run = [path_to_results_comparison_script, previous_loudness_calculation_log, new_loudness_calculation_log]

	list_of_command_output, error_happened, list_of_errors = run_external_program(commands_to_run)


	if len(list_of_command_output) != 0:

		for item in list_of_command_output:
			list_of_test_result_text_lines.append(text_marginal_2_tabs + item)

	# Print information gathered so far.
	for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
		print(list_of_test_result_text_lines[counter])
	last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	#######################################
	# Machine readable results comparison #
	#######################################

	title_string = '# Machine readable results comparison: ' + new_results_directory + ' #'
	list_of_test_result_text_lines.append('')
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))
	list_of_test_result_text_lines.append(text_marginal_1_tabs + title_string)
	list_of_test_result_text_lines.append(text_marginal_1_tabs + '#' * len(title_string))

	# path_to_results_comparison_script
	previous_loudness_calculation_log = path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + 'machine_readable_results'
	new_loudness_calculation_log = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + 'machine_readable_results'


	if (os.path.exists(previous_loudness_calculation_log) == True) and (os.path.exists(new_loudness_calculation_log) == True):

		commands_to_run = [path_to_results_comparison_script, previous_loudness_calculation_log, new_loudness_calculation_log]

		list_of_command_output, error_happened, list_of_errors = run_external_program(commands_to_run)

		if len(list_of_command_output) != 0:

			for item in list_of_command_output:
				list_of_test_result_text_lines.append(text_marginal_2_tabs + item)
	else:
		list_of_test_result_text_lines.append('')
		if os.path.exists(previous_loudness_calculation_log) == False:
			list_of_test_result_text_lines.append(text_marginal_2_tabs + 'There is no machine readable results in: ' + str(path_to_known_good_results_dir + os.sep + new_results_directory))

		if os.path.exists(new_loudness_calculation_log) == False:
			list_of_test_result_text_lines.append(text_marginal_2_tabs + 'There is no machine readable results in: ' + str(regression_test_results_target_dir + os.sep + new_results_directory))
		list_of_test_result_text_lines.append('')

	# Print information gathered so far.
	for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
		print(list_of_test_result_text_lines[counter])
	last_printed_test_result_text_line = len(list_of_test_result_text_lines)

	time_in_ticks_and_string_format = get_realtime()
	stop_time_for_individual_test = time_in_ticks_and_string_format[0]
	test_duration = calculate_duration(start_time_for_individual_test, stop_time_for_individual_test)

	title_string = '# ' + "'" + new_results_directory +"'" + ' Test Ended At: ' + time_in_ticks_and_string_format[1] + '   Test duration: '+ test_duration + ' #'
	list_of_test_result_text_lines.append('')
	list_of_test_result_text_lines.append('#' * len(title_string))
	list_of_test_result_text_lines.append(title_string)
	list_of_test_result_text_lines.append('#' * len(title_string))
	list_of_test_result_text_lines.append('')

	# Print information gathered so far.
	for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
		print(list_of_test_result_text_lines[counter])
	last_printed_test_result_text_line = len(list_of_test_result_text_lines)


time_in_ticks_and_string_format = get_realtime()
stop_time_for_complete_regression_test = time_in_ticks_and_string_format[0]
complete_test_duration = calculate_duration(start_time_for_complete_regression_test, stop_time_for_complete_regression_test)

title_string = '# Complete Regression Test Ended At: ' + time_in_ticks_and_string_format[1] +  '   Complete Regression Test duration: '+ complete_test_duration + ' #'
list_of_test_result_text_lines.append('')
list_of_test_result_text_lines.append('#' * len(title_string))
list_of_test_result_text_lines.append(title_string)
list_of_test_result_text_lines.append('#' * len(title_string))
list_of_test_result_text_lines.append('')

# Print information gathered so far.
for counter in range(last_printed_test_result_text_line, len(list_of_test_result_text_lines)):
	print(list_of_test_result_text_lines[counter])
last_printed_test_result_text_line = len(list_of_test_result_text_lines)

# Write regression test results to a log file.
error_happened, error_message = write_a_list_of_text_to_a_file(list_of_test_result_text_lines, regression_test_log_file_name)

if error_happened == True:

	error_happened = False

	print()
	print(error_message)
	print()

# Send regression test result to the admin by email.
message_text_string = '\n'.join(list_of_test_result_text_lines)
send_email('Regression Test Report', message_text_string, '', email_sending_details)

# If email sending encounters errors, then the email subroutine appends errors to the results list. Check for this and write the test results log again, if necessary.
if len(list_of_test_result_text_lines) + 1 > last_printed_test_result_text_line:

	# Write regression test results to a log file.
	error_happened, error_message = write_a_list_of_text_to_a_file(list_of_test_result_text_lines, regression_test_log_file_name)

	if error_happened == True:

		error_happened = False

		print()
		print(error_message)
		print()



	#FIXME
	# Muista pyytää rootin salasana, jos komentorivillä on optio -shutdown-when-ready
	# Muista tehdä mahdollisuus luoda testitulokset ilman, että on olemassa aiempia tuloksia joihin verrata. Tätä tarvitaan, jos käyttäjä haluaa luoda ekan datasetin.

