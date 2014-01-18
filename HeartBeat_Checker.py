#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Mikael Hartzell 2012
#
# This program is distributed under the GNU General Public License, version 3 (GPLv3)
#
# Check the license here: http://www.gnu.org/licenses/gpl.txt
# Basically this license gives you full freedom to do what ever you wan't with this program. You are free to use, modify, distribute it any way you like.
# The only restriction is that if you make derivate works of this program AND distribute those, the derivate works must also be licensed under GPL 3.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#

import os
import sys
import time
import smtplib
import email
import email.mime
import email.mime.text
import email.mime.multipart
import pickle

version = '021'

# User can set some defaults here that are used if the program is started without giving it the path to a configfile.
silent = False # Use True if you don't want this program to output anything to screen.
# heartbeat_check_interval = 120 # The number of seconds to wait between each check for the heartbeat-file.
heartbeat_check_interval = 120 # The number of seconds to wait between each check for the heartbeat-file.
use_tls = False # For Gmail use True
smtp_server_requires_authentication = False # For Gmail use True
smtp_username = "firstname.lastname@company.com" # This is the smtp server username and also the sender name of the email.
smtp_password = "password"
smtp_server_name = 'smtp.company.com' # For Gmail use smtp.gmail.com
smtp_server_port = 25 # For Gmail use 587

# Email recipient and title.
message_recipients = ['recipient1@company.com', 'recipient2@company.com'] # To send to more people, add email addresses as separate items in the list.
message_title = 'LoudnessCorrection Error Message'
message_attachment_path = ''

#========================================================================================================

def send_email(message_recipients, message_title, message_text_string, message_attachment_path):
   
	global loudness_correction_commandline
	global loudness_correction_pid
	global all_ip_addresses_of_the_machine
	global freelcs_version
	global version
	global heartbeat_checker_pid
	
	# Compile info about LoudnessCorrection and HeartBeat Checker. This info is inserted into the error email message.
	program_info = '\nLoudnessCorrection info:\n--------------------------------------\n' + 'Commandline: ' + ' '.join(loudness_correction_commandline) + '\n' + 'IP-Addresses: ' + ', '.join(all_ip_addresses_of_the_machine) + '\n' + 'PID: ' + str(loudness_correction_pid) + '\n' + 'FreeLCS version: ' + freelcs_version +  '\n\n' + 'HeartBeat Checker info:\n--------------------------------------\n' + 'Commandline: ' + ' '.join(sys.argv) + '\n' + 'PID: ' + str(heartbeat_checker_pid) + '\n' +'HeartBeat Checker version: ' + version + '\n\n'
	
	# Compile the start of the email message.
	email_message_content = email.mime.multipart.MIMEMultipart()
	email_message_content['From'] = smtp_username
	email_message_content['To'] = ', '.join(message_recipients)
	email_message_content['Subject'] = message_title

	message_text_string = message_text_string + program_info
	
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

#========================================================================================================

def parse_time(time_int):
	
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

#========================================================================================================

####################################
#### Main Program Starts Here :) ###
####################################

loudness_correction_program_info_and_timestamps = {} # This dictionary stores LoudnessCorrection.py - program info and latest timestamps read from the HeartBeat-file.
previous_values_of_loudness_correction_program_info_and_timestamps = {} # This dictionary will store the previous values of LoudnessCorrection.py - program info and timestamps.
heartbeat_has_stopped = False
alert_email_has_been_sent = False
heartbeat_file_read_error_message_has_been_sent = False
configfile_path = ''
startup_message_has_been_sent = False
heartbeat_checker_pid = os.getpid() # Get the PID of this program.

loudness_correction_commandline = ['Not known yet']
loudness_correction_pid = 'Not known yet'
all_ip_addresses_of_the_machine = ['Not known yet'] # This variable stores in a list all IP-Addresses of the machine LoudnessCorrection runs on. This info is inserted into error emails.
freelcs_version = 'Not known yet'

heartbeat_file_name = '00-HeartBeat.pickle'
heartbeat_file_was_found = False

# If the user did not give enough arguments on the commandline print an error message.
if (len(sys.argv) < 2) or (len(sys.argv) > 3):
	print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n')
	sys.exit(1)

# If there was only one argument on the commandline, it is full or partial path to the HeartBeat.pickle - file, check that the path exists.
if len(sys.argv) == 2:
	# Test if the user given target path exists.
	heartbeat_file_path = os.path.normpath(sys.argv[1])
	
	if (not os.path.exists(heartbeat_file_path)):
		time.sleep(45) # If the path does not exist, it may be because LoudnessCorrection is running but it has not yet created the HeartBeat - file. Wait 45 seconds to give it another chance.
		if (not os.path.exists(heartbeat_file_path)):
			print('\n!!!!!!! Path', heartbeat_file_path, 'does not exist.')
			print()
			sys.exit(1)

	# Test if the path user gave us has the name of the HeartBeat - file at the end of it and if the file exists.
	if (os.path.basename(heartbeat_file_path) == heartbeat_file_name) and (os.path.isfile(heartbeat_file_path)):
		heartbeat_file_was_found = True

	# If the path user gave us is a path to a directory, we need to search it to find where the file '00-HeartBeat.pickle' is located.
	if heartbeat_file_was_found == False:
		if os.path.isdir(heartbeat_file_path):
			if os.path.exists(heartbeat_file_path + os.sep + heartbeat_file_name):
				heartbeat_file_path = heartbeat_file_path + os.sep + heartbeat_file_name
				heartbeat_file_was_found = True
			if os.path.exists(heartbeat_file_path + os.sep + '00-Calculation_Queue_Information' + os.sep + heartbeat_file_name):
				heartbeat_file_path = heartbeat_file_path + os.sep + '00-Calculation_Queue_Information' + os.sep + heartbeat_file_name
				heartbeat_file_was_found = True
			if os.path.exists(heartbeat_file_path + os.sep + '00-Laskentajonon_Tiedot' + os.sep + heartbeat_file_name):
				heartbeat_file_path = heartbeat_file_path + os.sep + '00-Laskentajonon_Tiedot' + os.sep + heartbeat_file_name
				heartbeat_file_was_found = True
			if os.path.exists(heartbeat_file_path + os.sep + 'LoudnessCorrection' + os.sep + '00-Calculation_Queue_Information' + os.sep + heartbeat_file_name):
				heartbeat_file_path = heartbeat_file_path + os.sep + 'LoudnessCorrection' + os.sep + '00-Calculation_Queue_Information' + os.sep + heartbeat_file_name
				heartbeat_file_was_found = True
			if os.path.exists(heartbeat_file_path + os.sep + 'AanekkyysKorjaus' + os.sep + '00-Calculation_Queue_Information' + os.sep + heartbeat_file_name):
				heartbeat_file_path = heartbeat_file_path + os.sep + 'AanekkyysKorjaus' + os.sep + '00-Calculation_Queue_Information' + os.sep + heartbeat_file_name
				heartbeat_file_was_found = True

	if heartbeat_file_was_found == False:
		print('\n!!!!!!! Can not find file', heartbeat_file_name, 'in path', heartbeat_file_path)
		print()
		sys.exit(1)

# If there were two arguments on the commandline, then the first must be '-configfile' and the second the path to the config file. Check that the file exists and is readable.
if len(sys.argv) == 3:
	argument = sys.argv[1]
	configfile_path = sys.argv[2]
	if not (argument.lower() == '-configfile') and not (os.path.exists(configfile_path)) and not (os.access(configfile_path, os.R_OK)):
		print('\n!!!!!!! Target configfile does not exist or exists but is not readable !!!!!!!')
		print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n')	
		sys.exit(1)

###############################################################################################################################################################################
# Read user defined configuration variables from a file                                                                                                                       #
###############################################################################################################################################################################

# If there is a value in the variable 'configfile_path' then it is a valid path to a readable configfile.
# If the variable is empty, use the default values for variables defined in the beginning of this script.
if configfile_path != '':
	
	# Read the config variables from a file. The file contains a dictionary with the needed values.
	all_settings_dict = {}
	email_sending_details =  {}
	
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
	if 'silent' in all_settings_dict:
		silent = all_settings_dict['silent']
	if 'web_page_path' in all_settings_dict:
		web_page_path = all_settings_dict['web_page_path']
	if 'heartbeat_file_name' in all_settings_dict:
		heartbeat_file_name = all_settings_dict['heartbeat_file_name']
	if 'heartbeat_write_interval' in all_settings_dict:
		heartbeat_check_interval = all_settings_dict['heartbeat_write_interval'] * 4
	if 'email_sending_details' in all_settings_dict:
		email_sending_details = all_settings_dict['email_sending_details']

	# Assing email settings read from the configfile to local variables.
	heartbeat_file_path = web_page_path + os.sep + heartbeat_file_name
	use_tls = email_sending_details['use_tls']
	smtp_server_requires_authentication = email_sending_details['smtp_server_requires_authentication']
	smtp_username = email_sending_details['smtp_username']
	smtp_password = email_sending_details['smtp_password']
	smtp_server_name = email_sending_details['smtp_server_name']
	smtp_server_port = email_sending_details['smtp_server_port']
	message_recipients = email_sending_details['message_recipients']
	message_title = email_sending_details['message_title']


##############################
# The main loop starts here. #
##############################

while True:
	
	# Sleep before the next timestamp check.
	time.sleep(heartbeat_check_interval)
	
	message_text_list=['\n']
	message_text_string = ''
	heartbeat_file_read_error = False
	time_string = parse_time(time.time()) # Parse current time to a nicely formatted string.
	
	try:
		with open(heartbeat_file_path, 'rb') as heartbeat_file_handler:
			loudness_correction_program_info_and_timestamps = pickle.load(heartbeat_file_handler)
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		if silent == False:
			print(time_string + ':   ' + 'Error reading HeartBeat-file: ' + str(reason_for_error))
		heartbeat_file_read_error = True
		message_text_list.append(time_string + ':   ' + 'Error reading HeartBeat-file: ' + str(reason_for_error) + '\n\n')
	except OSError as reason_for_error:
		if silent == False:
			print(time_string + ':   ' + 'Error reading HeartBeat-file: ' + str(reason_for_error))
		heartbeat_file_read_error = True
		message_text_list.append(time_string + ':   ' + 'Error reading HeartBeat-file: ' + str(reason_for_error) + '\n\n')
	except EOFError as reason_for_error:
		if silent == False:
			print(time_string + ':   ' + 'Error reading HeartBeat-file: ' + str(reason_for_error))
		heartbeat_file_read_error = True
		message_text_list.append(time_string + ':   ' + 'Error reading HeartBeat-file: ' + str(reason_for_error) + '\n\n')
		
	############################################################################################################
	# Test if there was an error reading the HeartBeat - file, if so send email alert to user.
	############################################################################################################
	if (heartbeat_file_read_error == True) and (heartbeat_file_read_error_message_has_been_sent == False):
		# Consolidate email text lines to one string adding carriage return after each text line.
		message_text_string = '\n'.join(message_text_list)
		send_email(message_recipients, message_title, message_text_string, message_attachment_path)
		heartbeat_file_read_error_message_has_been_sent = True
		if silent == False:
			print(message_text_string)
	else:
		# If HeartBeat - file became readable again print / send message to the admin.
		if (heartbeat_file_read_error == False) and (heartbeat_file_read_error_message_has_been_sent == True):
			heartbeat_file_read_error_message_has_been_sent = False
			
			# Read LoudnessCorrection pid and commandline from the heartBeat pickle.
			loudness_correction_commandline = loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'][0]
			loudness_correction_pid = loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'][1]
			all_ip_addresses_of_the_machine = loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'][2]
			freelcs_version = loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'][3]
	
			message_text_string = 'Heartbeat - file became readable again at: ' + time_string + '\n'
			send_email(message_recipients, message_title, message_text_string, message_attachment_path)
			if silent == False:
				print(message_text_string)

	############################################################################################################
	# If there was an error reading the HeartBeat - file, skip the rest of the commands,
	# and try to read the file again after a delay.
	############################################################################################################
	if heartbeat_file_read_error == True:
		continue

	# There was no errors in reading HeartBeat - file, reset some variables.
	# First read LoudnessCorrection pid, commandline, ip-address and version number from the heartBeat pickle.
	loudness_correction_commandline = loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'][0]
	loudness_correction_pid = loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'][1]
	all_ip_addresses_of_the_machine = loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'][2]
	freelcs_version = loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'][3]
	
	# Send an email telling HeartBeat_Checker has started.
	if startup_message_has_been_sent == False:
		startup_message_has_been_sent = True
		message_text_list = ['HeartBeat_Checker started: ' + time_string]
		message_text_string = '\n'.join(message_text_list) + '\n\n'
		send_email(message_recipients, 'HeartBeat_Checker has started.', message_text_string, message_attachment_path)
	
	# If a timestamp stops updating, we wan't the first line of the emailed error message always to contain the commandline and PID of the LoudnessCorrection script.
	# If you have several versions of the script running on the same computer, the commandline tells which one encountered the error.
	message_text_list=[]
	message_text_string = ''
	stopped_timestamps_counter = 0

	# The first time this loop is run, there are no values in 'previous_values_of_loudness_correction_program_info_and_timestamps', then skip the following commands.
	if len(previous_values_of_loudness_correction_program_info_and_timestamps) != 0:
		
		############################################################################################################
		# HeartBeat file reading was successful. Read timestamps from the file and compare to the previous value.
		# If there was no change the corresponding thread in LoudnessCorrection.py has crashed.
		############################################################################################################
		for item in loudness_correction_program_info_and_timestamps:
			
			# The item called 'loudnesscorrection_program_info' holds the commandline and PID of LoudnessCorrection.py. We have already red this info into variables earlier, so skip this info here.
			if item == 'loudnesscorrection_program_info':
				continue

			# If the user disabled a functionality like for example html - writing in LoudnessCorrection.py, then it's first value in the list is 'False'.
			# In this case the timestamp of the disabled feature will not be updating, so skip the item.
			if loudness_correction_program_info_and_timestamps[item][0] == False:
				continue
			
			# If previous and new timestamp does not differ the thread in question has stopped, compile an error message describing the situation.
			if loudness_correction_program_info_and_timestamps[item][1] == previous_values_of_loudness_correction_program_info_and_timestamps[item][1]:
				
				stopped_timestamps_counter = stopped_timestamps_counter + 1 # Count how many stopped threads we have.
				heartbeat_time_string = parse_time(loudness_correction_program_info_and_timestamps[item][1]) # Parse time read from LoudnessCorrection timestamp to a nicely formatted string.
				
				# Set the error message according to the situation. There are a couple of different possible error cases. If timestamp = 0, then it was never updated, if it is bigger then it was updated at least once.
				if (loudness_correction_program_info_and_timestamps[item][1] == 0) and (item == 'write_html_progress_report'):
					message_text_list.append("LoudnessCorrection has not started updating 'html-thread' timestamps, the thread has probably crashed and a restart of the script is needed.")
					message_text_list.append('\n')
				if (loudness_correction_program_info_and_timestamps[item][1] == 0) and (item != 'write_html_progress_report'):
					message_text_list.append('LoudnessCorrection has not started updating \'' + item +  '\' timestamps, the thread has probably crashed and a restart of the script is needed.')
					message_text_list.append('\n')
				if loudness_correction_program_info_and_timestamps[item][1] > 0:
					message_text_list.append('LoudnessCorrection has stopped updating \'' + item +  '\' timestamps, the thread has probably crashed and a restart of the script is needed.' + ' Last thread timestamp update happened at: ' + heartbeat_time_string)
					message_text_list.append('\n')
					
		# Test how many stopped timestamps there was and set the variable 'heartbeat_has_stopped' accordingly.
		if stopped_timestamps_counter > 0:
			heartbeat_has_stopped = True
		else:
			heartbeat_has_stopped = False
			
		# If there were stopped timestamps / threads print and email error messages to admin.
		if (heartbeat_has_stopped == True) and (alert_email_has_been_sent == False):
			
			# Print message on screen.
			if silent == False:
				for line in message_text_list:
					print(line)
					
			# Consolidate email text lines to one string adding carriage return after each text line.
			message_text_string = '\n'.join(message_text_list)
			send_email(message_recipients, message_title, message_text_string, message_attachment_path)
			alert_email_has_been_sent = True
		else:
			# If all HeartBeat timestamps start again after being stopped, reset settings and start monitoring HeartBeat again. Also print / send message to the admin.
			if (heartbeat_has_stopped == False) and (alert_email_has_been_sent == True):
				alert_email_has_been_sent = False
				message_text_list.append('All Heartbeat timestamps started updating again at: ' + time_string + '\n\n')
				message_text_string = '\n'.join(message_text_list)
				send_email(message_recipients, message_title, message_text_string, message_attachment_path)
				
				if silent == False:
					print(message_text_string)
					
	# Store last timestamps so that we can compare them to new ones on the next while - loop run.
	previous_values_of_loudness_correction_program_info_and_timestamps = loudness_correction_program_info_and_timestamps
