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
		print(error_message)
		sys.exit(1)
	except OSError as reason_for_error:
		error_message = 'Error reading directory listing ' + str(reason_for_error)
		print(error_message)
		sys.exit(1)
	
	# Get text lines from mediainfo files and store them in a dictionary.
	for filename in list_of_files:

		with open(directory_for_mediainfo_files + os.sep + filename, 'r') as file_handler:

			list_of_text_lines = file_handler.readlines()

		mediainfo_results_dict[filename] = list_of_text_lines

	return(mediainfo_results_dict)

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

	try:
		with open(file_name, 'rb') as file_handler:
			file_handler.seek(0) # Make sure that the 'read' - pointer is in the beginning of the source file 
			binary_content_of_file = file_handler.read()

	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		print('Error reading textfile: ' + str(reason_for_error))
		sys.exit(1)
	except OSError as reason_for_error:
		print('Error reading textfile: ' + str(reason_for_error))
		sys.exit(1)
	except EOFError as reason_for_error:
		print('Error reading textfile: ' + str(reason_for_error))
		sys.exit(1)

	text_content_of_file = str(binary_content_of_file.decode('UTF-8'))

	return(text_content_of_file)

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
		source_disk_device=temp2[0] # Get source dir disk device name.

	# Parse shell command 'df' to find out what disk device the target dir is on.
	temp1=''
	temp2=''
	command_output = subprocess.Popen(["df", "-P", targetdir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
	temp1=str(command_output).split('\\n') # Split df output by lines using carrage return ('\n').
	temp2=str(temp1[1]).split() # The second item (second line df printed) has the device name, split the second line to separate items.
	if len(temp1)==3: # If df printed 3 lines of text ('temp1 is equal to 3), then df printed valid information about the disk device, else df did not find device name (df error message = 2 lines of text).
		target_disk_device=temp2[0] # Get target dir disk device name.

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
				 print('Message_size (', str(message_size), ') is larger than the max supported size (', str(server_max_message_size), ') of server:', smtp_server_name, 'Sending aborted.')
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
		 print('Error, Timeout error:', reason_for_error)
	except smtplib.socket.error as reason_for_error:
		 print('Error, Socket error:', reason_for_error)
	except smtplib.SMTPRecipientsRefused as reason_for_error:
		 print('Error, All recipients were refused:', reason_for_error)
	except smtplib.SMTPHeloError as reason_for_error:
		 print('Error, The server didn’t reply properly to the HELO greeting:', reason_for_error)
	except smtplib.SMTPSenderRefused as reason_for_error:
		 print('Error, The server didn’t accept the sender address:', reason_for_error)
	except smtplib.SMTPDataError as reason_for_error:
		 print('Error, The server replied with an unexpected error code or The SMTP server refused to accept the message data:', reason_for_error)
	except smtplib.SMTPException as reason_for_error:
		 print('Error, The server does not support the STARTTLS extension or No suitable authentication method was found:', reason_for_error)
	except smtplib.SMTPAuthenticationError as reason_for_error:
		 print('Error, The server didn’t accept the username/password combination:', reason_for_error)
	except smtplib.SMTPConnectError as reason_for_error:
		 print('Error, Error occurred during establishment of a connection with the server:', reason_for_error)
	except RuntimeError as reason_for_error:
		 print('Error, SSL/TLS support is not available to your Python interpreter:', reason_for_error)


########
# Main #
########

list_of_result_file_directories = ['ffmpeg-truepeak', 'ffmpeg-samplepeak', 'native-truepeak', 'native-samplepeak']
list_of_result_file_names = ['debug-file_processing_info-', 'debug-variables_lists_and_dictionaries-', 'error_log-', 'korjattujen_tiedostojen_aanekkyys.txt', 'loudness_calculation_log-']

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

print()

# If there are some previous regression tests still running, then stop them.
# Find the processes from ps output, keywords are 'LoudnessCorrection.py', '-force-quit-when-idle', '-debug_all' no other process uses all these commandline options.
command_to_run = ['/bin/ps', 'aux']
processes_to_stop = []
list_of_command_output, error_happened, list_of_errors = run_external_program(command_to_run)

for line in list_of_command_output:

	if 'LoudnessCorrection.py' in line:

		if '-force-quit-when-idle' in line:

			if '-debug_all' in line:
				command_to_run = []
				pid_of_program_to_stop = line.split()[1]
				commandline_of_program_to_stop = ' '.join(line.split()[10:])
				print('Stopping still running previous regression test PID:', pid_of_program_to_stop, 'Commandline:', commandline_of_program_to_stop)
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

# Check if previous results files can be found
for counter1 in range(0,4):

	directory_name = path_to_known_good_results_dir + os.sep + list_of_result_file_directories[counter1]

	for counter2 in range(0,5):

		file_name = list_of_result_file_names[counter2]

		name_of_matching_file = ''

		name_of_matching_file = find_matching_filename(directory_name, file_name)

		if name_of_matching_file != '':
			previous_results_filenames[counter1][counter2] = name_of_matching_file
		else:
			print()
			print('Error: Can not find previous results file:', file_name)
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

print()

# Create directories needed to store regression test results
for path in list_of_result_file_directories:
	os.makedirs(regression_test_results_target_dir + os.sep + path + os.sep + 'mediainfo')
	print('Creating dir:', regression_test_results_target_dir + os.sep + path + os.sep + 'mediainfo')
	os.makedirs(regression_test_results_target_dir + os.sep + path + os.sep + 'machine_readable_results')
	print('Creating dir:', regression_test_results_target_dir + os.sep + path + os.sep + 'machine_readable_results')


# FIXME
print()
print('loudness_correction_version =', loudness_correction_version)
print('source_and_target_are_on_same_disk =', source_and_target_are_on_same_disk)
print('home_directory_for_the_current_user =', home_directory_for_the_current_user)
print('hotfolder_path =', hotfolder_path)
print('directory_for_results =', directory_for_results)
print('directory_for_error_logs =', directory_for_error_logs)
print('path_to_known_good_results_dir =', path_to_known_good_results_dir)
print('regression_test_results_target_dir =', regression_test_results_target_dir)
print()
print('email_sending_details')
print('----------------------')
if len(email_sending_details) != 0:
	for item in email_sending_details:
		if item == 'smtp_password':
			continue
		print(item, '=', email_sending_details[item])

print('len(list_of_testfile_paths) =', len(list_of_testfile_paths))
print()

print('Previous results filenames')
print('---------------------------')

for counter in range(0, len(previous_results_filenames)):
	# list_of_result_file_directories
	print(list_of_result_file_directories[counter], '=', previous_results_filenames[counter])
print()



########################
# Run regression tests #
########################

for test_counter in range(0,4):

	new_results_directory = list_of_result_file_directories[test_counter]
	loudness_correction_test_run_commands = list_of_loudnesscorrection_commands_to_run[test_counter]
	regression_test_log_file_name = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + '00-regression_test_results_log.txt'
	previous_measured_loudness_of_loudness_corrected_files = path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + 'korjattujen_tiedostojen_aanekkyys.txt'
	new_measured_loudness_of_loudness_corrected_files = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + 'korjattujen_tiedostojen_aanekkyys.txt'
	mediainfo_source_dir = path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + 'mediainfo'
	mediainfo_target_dir = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + 'mediainfo'
	previous_loudness_calculation_log_name = find_matching_filename(path_to_known_good_results_dir + os.sep + new_results_directory, 'loudness_calculation_log-')
	previous_loudness_calculation_log = path_to_known_good_results_dir + os.sep + new_results_directory + os.sep + previous_loudness_calculation_log_name

	list_of_files = []

	loudness_scanner_commands = [libebur128_scanner_path, 'scan']

	# Move old error log files out of the way
	move_files_to_a_new_directory(directory_for_error_logs, directory_for_old_error_logs)

	# Remove files possibly left over in the HotFolder and results dir.
	error_happened, error_message = delete_files_from_a_directory('*', hotfolder_path)
	error_happened, error_message = delete_files_from_a_directory('*', directory_for_results)
	time.sleep(5)

	################################
	# Link test files to HotFolder #
	################################
	error_happened = False
	error_message = ''

	error_happened, error_message = link_test_files_to_target_directory(list_of_testfile_paths, hotfolder_path)

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

	###############################################
	# Remove all files from the results directory #
	###############################################
	error_happened, error_message = delete_files_from_a_directory('*', directory_for_results)

	###########################################################
	# Check if LoudnessCorrection.py reported critical errors #
	###########################################################
	file_name = find_matching_filename(regression_test_results_target_dir + os.sep + new_results_directory, 'error_log-')

	if file_name != '':
		text_content_of_file = read_a_text_file(regression_test_results_target_dir + os.sep + new_results_directory + os.sep + file_name)

		if 'Critical Python Error' in text_content_of_file:

			print()
			print('Error: LoudnessCorrection.py reported critical python errors !!!!!!!')
			print()


	##############################################
	# Mediainfo: identical and differing results #
	##############################################

	# Mediainfo records information like: format, channel count, bit depth, sample rate, duration, so comparing mediainfo - files
	# gives us confidence that all technical aspects of loudness corrected files are as expected
	mediainfo_results_1_dict = {}
	mediainfo_results_2_dict = {}
	mediainfo_results_1_dict = read_text_lines_in_mediainfo_files_to_dictionary(mediainfo_source_dir)
	mediainfo_results_2_dict = read_text_lines_in_mediainfo_files_to_dictionary(mediainfo_target_dir)

	mediainfo_files_with_identical_results_dict = {}
	mediainfo_files_with_differing_results_dict = {}
	mediainfo_files_only_in_path_1_dict = {}
	mediainfo_files_only_in_path_2_dict = {}

	# Mediainfo: Compare results in the two dictionaries and store results in four dictionaries.
	mediainfo_files_with_identical_results_dict, mediainfo_files_with_differing_results_dict, mediainfo_files_only_in_path_1_dict, mediainfo_files_only_in_path_2_dict = find_differences_in_two_result_dictionaries(mediainfo_results_1_dict, mediainfo_results_2_dict) 

	title_string = '# Mediainfo: identical and differing results for: ' + new_results_directory + ' #'
	print()
	print('#' * len(title_string))
	print(title_string)
	print('#' * len(title_string))
	print()

	# Mediainfo: Show the total number of mediainfo results
	print()
	print('Data for', str(len(mediainfo_results_1_dict)), 'files found in path:', mediainfo_source_dir)
	print('Data for', str(len(mediainfo_results_2_dict)), 'files found in path:', mediainfo_target_dir)


	# Mediainfo: Show Identical files
	if (len(mediainfo_results_1_dict) == len(mediainfo_results_2_dict)) and (len(mediainfo_results_1_dict) == len(mediainfo_files_with_identical_results_dict)):

		print()
		print('Results for all', str(len(mediainfo_files_with_identical_results_dict)), 'files are identical :)')
		print()
	else:
		print()
		print('Results for', str(len(mediainfo_files_with_identical_results_dict)), 'files are identical :)')
		print()

	# Mediainfo: Show Files with differing results
	if len(mediainfo_files_with_differing_results_dict) != 0:

		# Report any mismatch found.
		print()
		print(str(len(mediainfo_files_with_differing_results_dict)), "Calculation results don't match")
		print('-' * len(str(len(mediainfo_files_with_differing_results_dict)) + " Calculation results don't match ") + '-')
		print()

		list_of_non_matching_filenames = list(mediainfo_files_with_differing_results_dict)
		list_of_non_matching_filenames.sort(key=str.lower)

		for item in list_of_non_matching_filenames:

			file1_results = mediainfo_files_with_differing_results_dict[item][0]
			file2_results = mediainfo_files_with_differing_results_dict[item][1]

			print()
			print(item)
			print('-' * int(len(item) + 1))
			print()


			for value_counter in range(0, len(file1_results)):

				if file1_results[value_counter] != file2_results[value_counter]:
					
					# Make the printout prettier by aligning number values to each other.
					string_1_to_print = file1_results[value_counter]
					string_1_to_print = ' ' * (5 - len(string_1_to_print)) + string_1_to_print
					string_2_to_print = file2_results[value_counter]
					string_2_to_print = ' ' * (5 - len(string_2_to_print)) + string_2_to_print
					
					print(string_1_to_print + '   |  ' + string_2_to_print + '     ' +  item)
			print()
		
		print()

	# Mediainfo: Show Files only in path 1
	if len(mediainfo_files_only_in_path_1_dict) != 0:

		# Report any mismatch found.
		print()
		print(str(len(mediainfo_files_only_in_path_1_dict)), "Filenames only in:", mediainfo_source_dir)
		print('-' * len(str(len(mediainfo_files_only_in_path_1_dict)) + " Filenames only in: " + mediainfo_source_dir) + '-')
		print()

		list_of_missing_filenames = []

		list_of_missing_filenames = list(mediainfo_files_only_in_path_1_dict)
		list_of_missing_filenames.sort(key=str.lower)

		for item in list_of_missing_filenames:

			print(item)

		print()

	# Mediainfo: Show Files only in path 2
	if len(mediainfo_files_only_in_path_2_dict) != 0:

		# Report any mismatch found.
		print()
		print(str(len(mediainfo_files_only_in_path_2_dict)), "Filenames only in:", mediainfo_target_dir)
		print('-' * len(str(len(mediainfo_files_only_in_path_2_dict)) + " Filenames only in: " + mediainfo_target_dir) + '-')
		print()

		list_of_missing_filenames = []

		list_of_missing_filenames = list(mediainfo_files_only_in_path_2_dict)
		list_of_missing_filenames.sort(key=str.lower)

		for item in list_of_missing_filenames:

			print(item)

		print()

	#########################################################################
	# Loudness of loudness corrected files: identical and differing results #
	#########################################################################

	previous_results_as_text = ''
	previous_results_as_list = []
	previous_results_dict = {}
	new_results_as_text = ''
	new_results_as_list = []
	new_results_dict = {}

	previous_results_as_text = read_a_text_file(previous_measured_loudness_of_loudness_corrected_files)
	new_results_as_text = read_a_text_file(new_measured_loudness_of_loudness_corrected_files)

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

	title_string = '# Loudness of loudness corrected files: identical and differing results for: ' + new_results_directory + ' #'
	print()
	print('#' * len(title_string))
	print(title_string)
	print('#' * len(title_string))
	print()

	print('Data for', str(len(previous_results_dict)), 'files found in path:', previous_measured_loudness_of_loudness_corrected_files)
	print('Data for', str(len(new_results_dict)), 'files found in path:', new_measured_loudness_of_loudness_corrected_files)

	# Loudness of loudness corrected files: Show Identical files
	if (len(previous_results_dict) == len(new_results_dict)) and (len(previous_results_dict) == len(loudness_corrected_files_with_identical_results_dict)):

		print()
		print('Results for all', str(len(loudness_corrected_files_with_identical_results_dict)), 'files are identical :)')
		print()
	else:
		print()
		print('Results for', str(len(loudness_corrected_files_with_identical_results_dict)), 'files are identical :)')
		print()

	# Loudness of loudness corrected files: Show Files with differing results
	if len(loudness_corrected_files_with_differing_results_dict) != 0:

		# Report any mismatch found.
		print()
		print(str(len(loudness_corrected_files_with_differing_results_dict)), "Calculation results don't match")
		print('-' * len(str(len(loudness_corrected_files_with_differing_results_dict)) + " Calculation results don't match ") + '-')
		print()

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
			
			print(calculation_result_type + '   ' +  string_1_to_print + '   |  ' + string_2_to_print + '     ' +  item)
		
		print()

	# Loudness of loudness corrected files: Show Files only in path 1
	if len(loudness_corrected_files_only_in_path_1_dict) != 0:

		# Report any mismatch found.
		print()
		print(str(len(loudness_corrected_files_only_in_path_1_dict)), "Filenames only in:", previous_measured_loudness_of_loudness_corrected_files)
		print('-' * len(str(len(loudness_corrected_files_only_in_path_1_dict)) + " Filenames only in: " + previous_measured_loudness_of_loudness_corrected_files) + '-')
		print()

		list_of_missing_filenames = []

		list_of_missing_filenames = list(loudness_corrected_files_only_in_path_1_dict)
		list_of_missing_filenames.sort(key=str.lower)

		for item in list_of_missing_filenames:

			print(item)

		print()

	# Loudness of loudness corrected files: Show Files only in path 2
	if len(loudness_corrected_files_only_in_path_2_dict) != 0:

		# Report any mismatch found.
		print()
		print(str(len(loudness_corrected_files_only_in_path_2_dict)), "Filenames only in:", new_measured_loudness_of_loudness_corrected_files)
		print('-' * len(str(len(loudness_corrected_files_only_in_path_2_dict)) + " Filenames only in: " + new_measured_loudness_of_loudness_corrected_files) + '-')
		print()

		list_of_missing_filenames = []

		list_of_missing_filenames = list(loudness_corrected_files_only_in_path_2_dict)
		list_of_missing_filenames.sort(key=str.lower)

		for item in list_of_missing_filenames:

			print(item)

		print()

	#############################################################
	# Loudness Calculation Log: identical and differing results #
	#############################################################

	title_string = '# Loudness Calculation Log: identical and differing results for: ' + new_results_directory + ' #'
	print()
	print('#' * len(title_string))
	print(title_string)
	print('#' * len(title_string))
	print()

	# path_to_results_comparison_script
	new_loudness_calculation_log_name = find_matching_filename(regression_test_results_target_dir + os.sep + new_results_directory, 'loudness_calculation_log-')
	new_loudness_calculation_log = regression_test_results_target_dir + os.sep + new_results_directory + os.sep + new_loudness_calculation_log_name

	commands_to_run = [path_to_results_comparison_script, previous_loudness_calculation_log, new_loudness_calculation_log]

	list_of_command_output, error_happened, list_of_errors = run_external_program(commands_to_run)


	if len(list_of_command_output) != 0:

		print()

		for item in list_of_command_output:
			print(item)


	#FIXME
	# vertaa loudness calculation logia vanhaan hyväksi tiedettyyn
	# jos vanhat machine readable tiedostot löytyy, niin vertaa uusia niihin
	# jos vanhat machine readable tiedostot löytyy, niin vertaa niitä loudness calculation logiin.
	# Vaihda 'korjattujen_tiedostojen_aanekkyys.txt' nimi englanniks.
	# lähetä tulos sähköpostilla
	# Muista kerätä virheet ja lähettää nekin ylläpitäjälle / kirjata logiin.
	# Muista pyytää rootin salasana, jos komentorivillä on optio -shutdown-when-ready
	# Muista tehdä mahdollisuus luoda testitulokset ilman, että on olemassa aiempia tuloksia joihin verrata. Tätä tarvitaan, jos käyttäjä haluaa luoda ekan datasetin.

