#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Mikael Hartzell 2012 and contributors:
# Original idea for the program and Gnuplot commands by Timo Kaleva.
#
# This program is distributed under the GNU General Public License, version 3 (GPLv3)
#
# Check the license here: http://www.gnu.org/licenses/gpl.html
# Basically this license gives you full freedom to do what ever you wan't with this program. You are free to use, modify, distribute it any way you like.
# The only restriction is that if you make derivate works of this program AND distribute those, the derivate works must also be licensed under GPL 3.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#
# This program calculates loudness according to EBU R128 standard for each file it finds in the HotFolder.
#
# System requirements, Linux (preferably Ubuntu), gnuplot, python3, ffmpeg, sox v14.3.2 or later.
#

'''This program polls the HotFolder for new files and calculates loudness from each file using libebur128'''

import sys
import os
import time
import threading
import subprocess
import shutil
import copy
import smtplib
import email
import email.mime
import email.mime.text
import email.mime.multipart
import pickle
import math
import copy

version = '190'

########################################################################################################################################################################################
# All default values for settings are defined below. These variables define directory poll interval, number of processor cores to use, language of messages and file expiry time, etc. #
# These values are used if the script is run without giving an settings file as an argument. Values read from the settingsfile override these default settings.                        #
########################################################################################################################################################################################
#
# If you change debug to 'True' the script will print out contents of all mission critical lists and dictionaries once a minute.
# It will also print out values that are read from the configfile and transferred to local variables.
#
debug = False
#
# Language to use for directories and printing messages. Finnish and english are supported.
# Python has a neat feature which enables one to print a number of characters by using a multiplication function.
# To print seven 'a' - characters in a row you could use: print('a' * 7). It is also possible to print zero of something, and that results in no output.
# Print messages in finnish or english works by using this principle.
# Both English and Finnish language statements are present in each print() - statement, and the multiplication factors stored in variables 'english' and 'finnish' control which of those actually gets printed.
# When English = 1 and Finnish = 0, only English messages are printed and vice versa.
language = 'en' # Change to fi for Finnish.
if language == 'en':
	english = 1
	finnish = 0
else:
	english = 0
	finnish = 1

# If the user did not give enough arguments on the commandline print an error message.
if (len(sys.argv) < 2) or (len(sys.argv) > 3):
	print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)
	sys.exit(1)

target_path = ''
configfile_path = ''

# If there was only one argument on the commandline, it must be path to HotFolder, check that the the path is an existing directory.
if len(sys.argv) == 2:
	target_path = sys.argv[1]
	if os.path.isdir(target_path):
		target_path = os.sep + target_path.strip(os.sep) # If there is a slash at the end of the path name, remove it.
	else:
		print('\n!!!!!!! Target is not a directory !!!!!!!' * english + '\n!!!!!!! Kohde ei ole hakemisto !!!!!!!' * finnish)
		print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)	
		sys.exit(1)

# If there were two arguments on the commandline, then the first must be '-configfile' and the second the path to the config file. Check that the file exists and is readable.
if len(sys.argv) == 3:
	argument = sys.argv[1]
	configfile_path = sys.argv[2]
	if not argument.lower() == '-configfile':
		print('\n!!!!!!! Unknown option:' * english + '\n!!!!!!! Tuntematon optio:' * finnish, argument)
		print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)	
		sys.exit(1)
	if argument.lower() == '-configfile':
		if (os.path.exists(configfile_path) == False) or (os.access(configfile_path, os.R_OK) == False):
			print('\n!!!!!!! Configfile does not exist or exists but is not readable !!!!!!!' * english + '\n!!!!!!! Asetustiedostoa ei ole olemassa tai siihen ei ole lukuoikeuksia !!!!!!!' * finnish)
			print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)	
			sys.exit(1)
	if os.path.isfile(configfile_path) == False:
		print('\n!!!!!!! Configfile is not a regular file !!!!!!!' * english + '\n!!!!!!! Asetustiedosto ei ole tiedosto !!!!!!!' * finnish)
		print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)	
		sys.exit(1)

# Define folder names according to the language selected above.
if language == 'en':
	hotfolder_path = target_path + os.sep + 'LoudnessCorrection'
else:
	hotfolder_path = target_path + os.sep + 'AanekkyysKorjaus'
directory_for_temporary_files = target_path + os.sep + '00-Loudness_Calculation_Temporary_Files'
directory_for_results = hotfolder_path + os.sep + '00-Corrected_Files' * english + '00-Korjatut_Tiedostot' * finnish # This directory always needs to be a subdirectory for the hotfolder, otherwise deleting files from the results directory won't work.

delay_between_directory_reads = 5 # HotFolder poll interval (seconds) (how ofter the directory is checked for new files).
number_of_processor_cores = 6 # The number of processor cores to use for simultaneous file processing and loudness calculation. Only use even numbers. Slightly too big number often results in better performance. If you have 4 cores try defining 6 or 8 here and check the time it takes processing same set of files.
if number_of_processor_cores / 2 != int(number_of_processor_cores / 2): # If the number for processor cores is not an even number, force it to the next bigger even number.
	 number_of_processor_cores = number_of_processor_cores + 1 
file_expiry_time = 60*60*8 # This number (in seconds) defines how long the files are allowed to exist in HotFolder and results - directory. File creation time is not taken into account only the time this program first saw the file in the directory. Files are automatically deleted when they are 'expired'.

natively_supported_file_formats = ['.wav', '.flac', '.ogg'] # Natively supported formats may be processed without first decoding to flac with ffmpeg, since libebur128 and sox both support these formats.
ffmpeg_output_format = 'wav' # Possible values are 'flac' and 'wav'. This only affects formats that are first decodec with ffmpeg (all others but wav, flac, ogg).
if not ffmpeg_output_format == 'wav':
	ffmpeg_output_format = 'flac'

silent = False # Use True if you don't want this programs to print anything on screen (useful if you want to start this program from Linux init scripts).

# Write calculation queue progress report to a html-page on disk.
write_html_progress_report = True # Controls if the program writes loudness calculation queue information to a web page on disk.
html_progress_report_write_interval = 5 # How many seconds between writing web page to disk.
web_page_name = '00-Calculation_Queue_Information.html' * english + '00-Laskentajonon_Tiedot.html' * finnish # Define the name of the web-page we write to disk.
web_page_path = hotfolder_path + os.sep + '00-Calculation_Queue_Information' * english + '00-Laskentajonon_Tiedot' * finnish # Where to write the web-page.

# Define the path for the error logfile.
directory_for_error_logs = target_path + os.sep + '00-Error_Logs' # Define the path for error log files. The file is automatically named ('error_log- ' + date + current time).
send_error_messages_to_logfile = True

# Heartbeat writes timestamp periodically to a file so that a outside program can monitor if this program has stopped.
heartbeat = True # This variable controls if this program periodically writes the current time in to a file. This file can be externally monitored to see if this program is still alive or if it has stopped due to an unexpected error.
heartbeat_file_name = '00-HeartBeat.pickle' # This variable defines the name of the file where the heartbeat timestamp will be written. The files 'modification date' reflects the last heartbeat. The time strings produced by python3 function int(time.time()) is written in to the file. 
heartbeat_write_interval = 30 # This variable defines how many seconds there approximately will be between writing the current time to the heartbeat - file. The real delay between writes gets considerably longer when the machine is under heavy disk IO. Writing the timestamp to the file can get delayed by a factor of 2 - 4. So use a longer value when determining if this program is still running. The delay during high disk IO can be avoided if the directory the heartbeat-file is written to is on a ram-disk.
# Collect error messages and send them periodically by email to the administrator.
email_sending_details = {} # All information needed to send email is gathered to this dictionary.
email_sending_details['last_send_timestamp'] = 0 # This value is always set to the last time when email was sent. This is used to calculate the next time we are allowed to send email again.
send_error_messages_by_email = False # Set to True if you wan't to send error messages by email to admin. You must also setup up all the following variables according to your smtp-server.
email_sending_details['send_error_messages_by_email'] = send_error_messages_by_email
email_sending_details['email_sending_interval'] = 600 # Wait this number of seconds between sending email. Email is only sent if there are error messages to report.
email_sending_details['use_tls'] = False # Use secure tls connection for connecting to the smtp - server. For Gmail use True.
email_sending_details['smtp_server_requires_authentication'] = False # Set to False if smtp - server does not require username and password for sending mail. For Gmail use True.
email_sending_details['smtp_username'] = "firstname.lastname@company.com" # This is the smtp server username and also the email sender name.
email_sending_details['smtp_password'] = "password" # This is the smtp user password.
email_sending_details['smtp_server_name'] = 'smtp.company.com' # Smtp - server address. For Gmail use smtp.gmail.com
email_sending_details['smtp_server_port'] = 25 # Smtp - server port. For Gmail use 587
# Email message recipient and Title.
email_sending_details['message_recipients'] = ['recipient1@company.com', 'recipient2@company.com']  # Add here the email addresses of the recipients as a list.
email_sending_details['message_title'] = 'LoudnessCorrection Error Message' # The title of the email message.

# Create a list of targets of where to send error messages based on variable definitions above.
# Don't change values here, instead change variables above named 'silent', 'send_error_messages_to_logfile', 'send_error_messages_by_email'.
where_to_send_error_messages = [] # Tells where to print / send the error messages. The list can have any or all of these values: screen, logfile, email.
if silent == False:
	where_to_send_error_messages.append('screen')
if send_error_messages_to_logfile == True:
	where_to_send_error_messages.append('logfile')
if send_error_messages_by_email == True:
	where_to_send_error_messages.append('email')

# Should we use absolute sample peak or TruePeak calculation to determine the highest peak in audio. Possible values are: '--peak=sample' and '--peak=true'
peak_measurement_method = '--peak=sample'

wav_format_maximum_file_size = 4294967296 # Define wav max file size. Theoretical max size is 2 ^ 32 = 4294967296.
# wav_format_maximum_file_size = 31000000 # Use this when debugging with shrunken test files :)
###############################################################################################################################################################################
# Default value definitions end here :)                                                                                                                                       #
###############################################################################################################################################################################

def calculate_integrated_loudness(event_for_integrated_loudness_calculation, filename, hotfolder_path, libebur128_commands_for_integrated_loudness_calculation, english, finnish):

	"""This subroutine uses libebur128 program loudness to calculate integrated loudness, loudness range and difference from target loudness."""

# This subroutine works like this:
# ---------------------------------
# The subroutine is usually started from the main program in it's own thread and it calculates integrated loudness and loudness range of a file and difference from target loudness.
# Simultaneusly to this thread another subroutine calculates loudness of the file slicing the file in short segments and calculating each slice individially. Slices are 3 seconds for files 10 seconds or longer and 0.5 seconds for files 9 seconds or shorter.
# The results from this thread needs to be communicated to the time slice thread, since results of both threads are needed for the graphics generation.
# This thread communicates it's results to the other thread by putting them in dictionary 'integrated_loudness_calculation_results' that can be read in the other thread.

	global integrated_loudness_calculation_results
	integrated_loudness_calculation_stdout = ''
	integrated_loudness_calculation_stderr = ''
	file_to_process = hotfolder_path + os.sep + filename
	highest_peak_db = float('-120') # Set default value for sample peak.
	integrated_loudness_is_below_measurement_threshold = False

	if os.path.exists(file_to_process): # Check if the audio file still exists, user may have deleted it. If True start loudness calculation.
	
		# Calculate integrated loudness and loudness range using libebur128 and parse the results from the text output of the program.
		
		# Append the name of the file we are going to process at the end of libebur128 commands.
		libebur128_commands_for_integrated_loudness_calculation.append(file_to_process)
		
		try:
			# Define filenames for temporary files that we are going to use as stdout and stderr for the external command.
			stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_integrated_loudness_calculation_stdout.txt'
			stderr_for_external_command = directory_for_temporary_files + os.sep + filename + '_integrated_loudness_calculation_stderr.txt'
			# Open the stdout and stderr temporary files in binary write mode.
			with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler, open(stderr_for_external_command, 'wb') as stderr_commandfile_handler:
			
				# Run libebur128 to calculate the integrated loudness of a audio file.
				subprocess.Popen(libebur128_commands_for_integrated_loudness_calculation, stdout=stdout_commandfile_handler, stderr=stderr_commandfile_handler, stdin=None, close_fds=True).communicate()
				
				# Make sure all data written to temporary stdout and stderr - files is flushed from the os cache and written to disk.
				stdout_commandfile_handler.flush() # Flushes written data to os cache
				os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
				stderr_commandfile_handler.flush() # Flushes written data to os cache
				os.fsync(stderr_commandfile_handler.fileno()) # Flushes os cache to disk
			
		except IOError as reason_for_error:
			error_message = 'Error writing to stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_integrated_loudness_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error writing to stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_integrated_loudness_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		# Open files we used as stdout and stderr for the external program and read in what the program did output to those files.
		try:
			with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler, open(stderr_for_external_command, 'rb') as stderr_commandfile_handler:
				integrated_loudness_calculation_stdout = stdout_commandfile_handler.read(None)
				integrated_loudness_calculation_stderr = stderr_commandfile_handler.read(None)
		except IOError as reason_for_error:
			error_message = 'Error reading from stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston lukeminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_integrated_loudness_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error reading from stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon lukeminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_integrated_loudness_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		# Convert libebur128 output from binary to UTF-8 text.
		integrated_loudness_calculation_stdout_string = str(integrated_loudness_calculation_stdout.decode('UTF-8')) 
		integrated_loudness_calculation_stderr_string = str(integrated_loudness_calculation_stderr.decode('UTF-8'))

		# Delete the temporary stdout and stderr - files
		try:
			os.remove(stdout_for_external_command)
			os.remove(stderr_for_external_command)
		except IOError as reason_for_error:
			error_message = 'Error deleting stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_integrated_loudness_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error deleting stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_integrated_loudness_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])

		# Test if libebur128 was successful in processing the file or not.
		# If libebur128 can successfully process the file it prints the results to its stdout and the progress printout to stderr.
		# If libebur128 encounters an error it won't print anything to stdout and prints error message to stderr. In some error cases libebur128 does not print anything to stdout or stderr.
		# If loudness calculation encountered an error, set result variables to default values.
		if len(integrated_loudness_calculation_stdout_string) == 0:
			# If libebur128 printed nothing (output length = 0) at its stdout, libebur128 did not succeed in loudness calculation. Then set variables to default values.
			integrated_loudness_calculation_error = True
			integrated_loudness = 0
			loudness_range = 0
			difference_from_target_loudness = 0
			# Check if libebur128 printed the reason for the error, if not use a default error message.
			if len(integrated_loudness_calculation_stderr_string) != 0:
				integrated_loudness_calculation_error_message = integrated_loudness_calculation_stderr_string
			else:
				integrated_loudness_calculation_error_message = 'libebur128 did not tell the cause of the error.' * english + 'libebur128 ei kertonut virheen syytä.' * finnish
			
		else:
			# Loudness calculation was successful, calculate loudness difference from target loudness and assign results to variables.
			integrated_loudness_calculation_error = False
			integrated_loudness_calculation_parsed_results=integrated_loudness_calculation_stdout_string.replace('LUFS', '').replace('LU','').replace(',', '').strip().split()[0:3]
			integrated_loudness = float(integrated_loudness_calculation_parsed_results[0])
			loudness_range = float(integrated_loudness_calculation_parsed_results[1])
			highest_peak_float = float(integrated_loudness_calculation_parsed_results[2])
			highest_peak_db = round(20 * math.log(highest_peak_float, 10),1)
			difference_from_target_loudness = round(integrated_loudness - float('-23'), 1)
			integrated_loudness_calculation_error_message = ''
			# If integrated loudness measurement is below -70 LUFS, then libebur128 says the measurement is '-inf', which means roughly 'not possible to measure'. Generate error since '-inf' can not be used in calculations.
			if integrated_loudness == float('-inf'):
				integrated_loudness_calculation_error = True
				integrated_loudness_calculation_error_message = 'Loudness is below measurement threshold (-70 LUFS)' * english + 'Äänekkyys on alle mittauksen alarajan (-70 LUFS)' * finnish
				integrated_loudness_is_below_measurement_threshold = True
		integrated_loudness_calculation_results_list = [integrated_loudness, difference_from_target_loudness, loudness_range, integrated_loudness_calculation_error, integrated_loudness_calculation_error_message, highest_peak_db, integrated_loudness_is_below_measurement_threshold] # Assign result variables to the list that is going to be read in the other loudness calculation process.
		integrated_loudness_calculation_results[filename] = integrated_loudness_calculation_results_list # Put loudness calculation results in a dictionary along with the filename.		
	else:
		# If we get here the file we were supposed to process vanished from disk after the main program started this thread. Print a message to the user.
		error_message ='ERROR !!!!!!! FILE' * english + 'VIRHE !!!!!!! Tiedosto' * finnish + ' ' + filename + ' ' + 'dissapeared from disk before processing started.' * english + 'hävisi kovalevyltä ennen käsittelyn alkua.' * finnish
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Set the event for this calculation thread. The main program checks the events and sees that this calculation thread is ready.
	event_for_integrated_loudness_calculation.set()
	return()

def calculate_loudness_timeslices(filename, hotfolder_path, libebur128_commands_for_time_slice_calculation, directory_for_temporary_files, directory_for_results, english, finnish):

	"""This subroutine uses libebur128 loudness-executable to calculate file loudness segmenting the file in time slices and calculating loudness of each slice."""

	# This subroutine works like this:
	# ---------------------------------
	# The subroutine is started from the main program in it's own thread.
	# This routine starts libebur128 loudness-executable to calculate the time slice loudness values and puts the resulting output (list of dB values each in it's own row) in a list.
	# Simultaneusly to this thread another subroutine calculates integrated loudness, loudness range and difference from target loudness.
	# This routine waits for the other loudness calculation thread to finnish since it's results are needed to go forward.
	# This routine then starts the loudness graphics plotting subroutine giving it loudness results from both calculation processes.

	timeslice_loudness_calculation_stdout = ''
	timeslice_loudness_calculation_stderr = ''
	file_to_process = hotfolder_path + os.sep + filename

	if os.path.exists(file_to_process): # Check if the audio file still exists, user may have deleted it. If True start loudness calculation.
		# Start time slice loudness calculation.
		time_slice_duration_string = libebur128_commands_for_time_slice_calculation[3] # Timeslice for files <10 seconds is 0.5 sec, and 3 sec for files >= 10 sec. Get the timeslice duration.
		libebur128_commands_for_time_slice_calculation.append(file_to_process) # Append the name of the file we are going to process at the end of libebur128 commands.
		
		try:
			# Define filenames for temporary files that we are going to use as stdout and stderr for the external command.
			stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_timeslice_loudness_calculation_stdout.txt'
			stderr_for_external_command = directory_for_temporary_files + os.sep + filename + '_timeslice_loudness_calculation_stderr.txt'
			# Open the stdout and stderr temporary files in binary write mode.
			with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler, open(stderr_for_external_command, 'wb') as stderr_commandfile_handler:
		
				# Run libebur128 to calculate the loudness of individual time slices of a audio file.
				subprocess.Popen(libebur128_commands_for_time_slice_calculation, stdout=stdout_commandfile_handler, stderr=stderr_commandfile_handler, stdin=None, close_fds=True).communicate()
		
				# Make sure all data written to temporary stdout and stderr - files is flushed from the os cache and written to disk.
				stdout_commandfile_handler.flush() # Flushes written data to os cache
				os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
				stderr_commandfile_handler.flush() # Flushes written data to os cache
				os.fsync(stderr_commandfile_handler.fileno()) # Flushes os cache to disk
		
		except IOError as reason_for_error:
			error_message = 'Error writing to stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_time_slice_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error writing to stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_time_slice_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		# Open files we used as stdout and stderr for the external program and read in what the program did output to those files.
		try:
			with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler, open(stderr_for_external_command, 'rb') as stderr_commandfile_handler:
				timeslice_loudness_calculation_stdout = stdout_commandfile_handler.read(None)
				timeslice_loudness_calculation_stderr = stderr_commandfile_handler.read(None)
		except IOError as reason_for_error:
			error_message = 'Error reading from stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston lukeminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_time_slice_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error reading from stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon lukeminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_time_slice_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		# Convert libebur128 output from binary to UTF-8 text.
		timeslice_loudness_calculation_result_list = str(timeslice_loudness_calculation_stdout.decode('UTF-8')).split('\n') # Convert libebur128 output from binary to UTF-8 text, split values in the text by line feeds and insert these individual values in to a list.
		timeslice_loudness_calculation_stderr_string = str(timeslice_loudness_calculation_stderr.decode('UTF-8')) # Convert libebur128 possible error output from binary to UTF-8 text.
		
		# Delete the temporary stdout and stderr - files
		try:
			os.remove(stdout_for_external_command)
			os.remove(stderr_for_external_command)
		except IOError as reason_for_error:
			error_message = 'Error deleting stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_time_slice_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error deleting stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(libebur128_commands_for_time_slice_calculation) + '. ' + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		if '' in timeslice_loudness_calculation_result_list: # There usually is an empty item [''] at the end of the list, remove it.
			timeslice_loudness_calculation_result_list.remove('')
		
		# Test if libebur128 was successful in processing the file or not.	
		# If libebur128 can successfully process the file it prints the results to its stdout.
		# If libebur128 encounters an error it won't print anything to stdout and prints error message to stderr. In some error cases libebur128 does not print anything to stdout or stderr.
		# If loudness calculation encountered an error the number of timeslice values in the list is 0.
		number_of_timeslices=len(timeslice_loudness_calculation_result_list) # Get the number of timeslices we have. As each slice is a dB number in its own row in the result, the number of timeslices is the same as the number of rows in the loudness calculation result.
		timeslice_calculation_error = False
		timeslice_calculation_error_message =''
		
		if number_of_timeslices == 0:
			timeslice_calculation_error = True
			# If libebur128 did output an error message use it, else use a default message.
			if len(timeslice_loudness_calculation_stderr_string) != 0:
				timeslice_calculation_error_message = timeslice_loudness_calculation_stderr_string
			else:
				timeslice_calculation_error_message = 'Loudness calculation table is empty' * english + 'Äänekkyysmittaustulosten taulukko on tyhjä' * finnish

		# Wait for the other loudness calculation thread to end since it's results are needed in the next step of the process.
		integrated_loudness_calculation_is_ready = False
		event_for_timeslice_loudness_calculation, event_for_integrated_loudness_calculation = loudness_calculation_queue[filename] # Take events for both of the loudness calculation threads from the dictionary.
		while integrated_loudness_calculation_is_ready == False: # Wait until the other thread has finished. event = set, means thread has finished.
			if event_for_integrated_loudness_calculation.is_set():
				integrated_loudness_calculation_is_ready = True
			else:
				time.sleep(1)
	else:
		# If we get here the file we were supposed to process vanished from disk after the main program started this thread. Print a message to the user.
		error_message = 'VIRHE !!!!!!! Tiedosto' * finnish + 'ERROR !!!!!!! FILE' * english + ' ' + filename + ' ' + 'hävisi kovalevyltä ennen käsittelyn alkua.' * finnish + 'dissapeared from disk before processing started.' * english
		send_error_messages_to_screen_logfile_email(error_message, [])

	# We now have all loudness calculation results needed for graphics generation, start the subprocess that plots graphics and calls another subprocess that creates loudness corrected audio with sox.
	create_gnuplot_commands(filename, number_of_timeslices, time_slice_duration_string, timeslice_calculation_error, timeslice_calculation_error_message, timeslice_loudness_calculation_stdout, hotfolder_path, directory_for_temporary_files, directory_for_results, english, finnish)
	# After generating graphics and loudness corrected audio, set the event for this calculation thread. The main program checks the events and sees that this calculation thread is ready.
	event_for_timeslice_loudness_calculation.set()

def create_gnuplot_commands(filename, number_of_timeslices, time_slice_duration_string, timeslice_calculation_error, timeslice_calculation_error_message, timeslice_loudness_calculation_stdout, hotfolder_path, directory_for_temporary_files, directory_for_results, english, finnish):

	'''This subprocess plots an jpeg graphics file using combined results from two loudness calculation processes'''

	# This subroutine works like this:
	# ---------------------------------
	# The program checks how much time slices we have in the loudness calculation results and calculates file duration from that.
	# Then the program generates the x - axis (time axis) information for the graphics generation. The program sets time markers (minutes or seconds) along the x - axis in even intervals taking the file duration into account.
	# If there has been an error in loudness calculations the routine generates preset graphics with the error message on it.
	# Then the routine generates commands needed for gnuplot and puts them in a list.
	# The timeslice list of loudness values is written to a file, since gnuplot uses values from the file for plotting the loudness curve.
	# Then the gnuplot commands are written to a file and a subroutine called to run gnuplot.


	global integrated_loudness_calculation_results
	integrated_loudness_calculation_results_list = []
	commandfile_for_gnuplot = directory_for_temporary_files + os.sep + filename + '-gnuplot_commands'
	loudness_calculation_table = directory_for_temporary_files + os.sep + filename + '-loudness_calculation_table'
	gnuplot_temporary_output_graphicsfile = directory_for_temporary_files + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish
	gnuplot_output_graphicsfile = directory_for_results + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish
	warning_message = ''
	
	# Get loudness calculation results from the integrated loudness calculation process. Results are in list format in dictionary 'integrated_loudness_calculation_results', assing results to variables.
	integrated_loudness_calculation_results_list = integrated_loudness_calculation_results.pop(filename)# Get loudness results for the file and remove this information from dictionary.
	integrated_loudness = integrated_loudness_calculation_results_list[0]
	difference_from_target_loudness = integrated_loudness_calculation_results_list[1]
	loudness_range = integrated_loudness_calculation_results_list[2]
	integrated_loudness_calculation_error = integrated_loudness_calculation_results_list[3]
	integrated_loudness_calculation_error_message = integrated_loudness_calculation_results_list[4]
	highest_peak_db = integrated_loudness_calculation_results_list[5]
	integrated_loudness_is_below_measurement_threshold = integrated_loudness_calculation_results_list[6]
	# If TruePeak method was used to determine the highest peak, then it can be above 0 dBFS, add a plus sign if this is the case.
	if highest_peak_db > 0:
		highest_peak_db_string = '+' + str(highest_peak_db)
	else:
		highest_peak_db_string = str(highest_peak_db)
	# If calculated loudness difference from target -23 LUFS loudness is a positive number, create a string with a plus sign and the difference number in it.
	if difference_from_target_loudness > 0:
		difference_from_target_loudness_string = '+' + str(difference_from_target_loudness)
	else:
		difference_from_target_loudness_string = str(difference_from_target_loudness) # The loudness difference from target loudness is negative, just create a string with the negative result number in it.

	# Scale loudness graphics x-axis time information according to file duration.
	# Loudness calculation is done in 3 second slices when audio duration is 12 seconds or longer.
	# If file duration is shorter than 12 seconds then slices are 0.5 seconds each.
	audio_duration_rounded_to_seconds = int(number_of_timeslices * float(time_slice_duration_string))
		
	# If file duration is shorter than 12 seconds. Time slices are 0.5 seconds each.
	if audio_duration_rounded_to_seconds < 12:
		plotfile_x_axis_divider = 2 # Define how many time slices there are between each printed x-axis time number.
		plotfile_x_axis_time = 1 # Define the steps of increasing x-axis time numbers.
		plotfile_x_axis_name = 'Seconds' * english + 'Sekunnit' * finnish
	# File duration is 10 seconds or longer. Time slices are 3 seconds each.
	if (audio_duration_rounded_to_seconds >= 12) and (audio_duration_rounded_to_seconds <= 60): # File duration is between 10 seconds and 1 minute.
		plotfile_x_axis_divider = 1 # Define how many time slices there are between each printed x-axis time number.
		plotfile_x_axis_time = 3 # Define the steps of increasing x-axis time numbers.
		plotfile_x_axis_name = 'Seconds' * english + 'Sekunnit' * finnish # X-axis time name (seconds / minutes hours).
	if (audio_duration_rounded_to_seconds > 60) and (audio_duration_rounded_to_seconds <= 180): # File duration is between 1 and 3 minutes.
		plotfile_x_axis_divider = 5
		plotfile_x_axis_time = 15
		plotfile_x_axis_name = 'Seconds' * english + 'Sekunnit' * finnish
	if (audio_duration_rounded_to_seconds > 180) and (audio_duration_rounded_to_seconds < 1800): # File duration is between 3 minutes and 30 minutes.
		plotfile_x_axis_divider = 20
		plotfile_x_axis_time = 1
		plotfile_x_axis_name = 'Minutes' * english + 'Minuutit' * finnish
	if (audio_duration_rounded_to_seconds >= 1800) and (audio_duration_rounded_to_seconds < 3600): # File duration is between 30 minutes and 1 hour.
		plotfile_x_axis_divider = 60
		plotfile_x_axis_time = 3
		plotfile_x_axis_name = 'Minutes' * english + 'Minuutit' * finnish
	if (audio_duration_rounded_to_seconds >= 3600) and (audio_duration_rounded_to_seconds < 7200): # File duration is between 1 and 2 hours.
		plotfile_x_axis_divider = 100
		plotfile_x_axis_time = 5
		plotfile_x_axis_name = 'Minutes' * english + 'Minuutit' * finnish
	if (audio_duration_rounded_to_seconds >= 7200) and (audio_duration_rounded_to_seconds < 21600): # File duration is between 2 and 6 hours.
		plotfile_x_axis_divider = 300
		plotfile_x_axis_time = 15
		plotfile_x_axis_name = 'Minutes' * english + 'Minuutit' * finnish
	if (audio_duration_rounded_to_seconds >= 21600) and (audio_duration_rounded_to_seconds < 43200): # File duration is between 6 and 12 hours.
		plotfile_x_axis_divider = 600
		plotfile_x_axis_time = 30
		plotfile_x_axis_name = 'Minutes' * english + 'Minuutit' * finnish
	if (audio_duration_rounded_to_seconds >= 43200) and (audio_duration_rounded_to_seconds < 86400): # File duration is between 12 and 24 hours.
		plotfile_x_axis_divider = 1200
		plotfile_x_axis_time = 1
		plotfile_x_axis_name = 'Hours' * english + 'Tunnit' * finnish
	if (audio_duration_rounded_to_seconds >= 86400) and (audio_duration_rounded_to_seconds < 172800): # File duration is between 24 and 48 hours.
		plotfile_x_axis_divider = 2400
		plotfile_x_axis_time = 2
		plotfile_x_axis_name = 'Hours' * english + 'Tunnit' * finnish
	if (audio_duration_rounded_to_seconds >= 172800) and (audio_duration_rounded_to_seconds < 345600): # File duration is between 48 and 96 hours.
		plotfile_x_axis_divider = 4800
		plotfile_x_axis_time = 4
		plotfile_x_axis_name = 'Hours' * english + 'Tunnit' * finnish
	if (audio_duration_rounded_to_seconds >= 345600) and (audio_duration_rounded_to_seconds < 691200): # File duration is between 96 and 192 hours.
		plotfile_x_axis_divider = 9600
		plotfile_x_axis_time = 8
		plotfile_x_axis_name = 'Hours' * english + 'Tunnit' * finnish

	# Generate x-axis texts needed for gnuplot and store them in a list.
	plotfile_x_axis_time_information=[]
	if timeslice_calculation_error == False:
		plotfile_x_axis_time_information.append('set xtics (')
		counter=1
		for counter in range(0, int(number_of_timeslices / (plotfile_x_axis_divider) + 1), 1):
			plotfile_x_axis_time_information.append('\"' + str(counter * plotfile_x_axis_time) + '\" ' + str(counter * plotfile_x_axis_divider) + ' ')
			if counter <  int(number_of_timeslices / (plotfile_x_axis_divider)):
				plotfile_x_axis_time_information.append(', ')
		plotfile_x_axis_time_information.append(')')
		plotfile_x_axis_time_information = ''.join(plotfile_x_axis_time_information)
	
	# Get technical info from audio file and determine what the ouput format will be
	channel_count, sample_rate, bit_depth, sample_count, flac_compression_level, output_format_for_intermediate_files, output_format_for_final_file, audio_channels_will_be_split_to_separate_mono_files, audio_duration, output_file_too_big_to_split_to_separate_wav_channels = get_audiofile_info_with_sox_and_determine_output_format(directory_for_temporary_files, hotfolder_path, filename)
	
	# Write details of the file to a logfile.
	if debug == True:
		debug_write_loudness_calculation_info_to_a_logfile(filename, integrated_loudness, loudness_range, highest_peak_db, channel_count, sample_rate, bit_depth, audio_duration)
	
	# If file size exceeds 4 GB, a warning message must be displayed informing the user that the
	# outputfile will either be split to separate mono channels or stored in flac - format.
	if output_format_for_intermediate_files != output_format_for_final_file:
		# The combined channels in final output file exceeds the max file size and the file needs to be split to separate mono files.
		warning_message = warning_message + '\\nWarning: file size exceeds wav format max limit 4 GB, audio channels will be split to separate mono files' * english + '\\nVaroitus: tiedoston koko ylittää wav - formaatin maksimin (4 GB), kanavat jaetaan erillisiin tiedostoihin' * finnish
	if output_format_for_final_file == 'flac':
		# File is so big that even separate mono channels would exceed 4GB each, so flac format must be used for the output file.
		warning_message = warning_message + '\\nWarning: file size exceeds wav format max limit 4 GB, file will be stored in flac - format' * english + '\\nVaroitus: tiedoston koko ylittää wav - formaatin maksimin (4 GB), tiedosto tallennetaan flac - formaattiin' * finnish
	
	# Generate gnuplot commands needed for plotting the graphicsfile and store commands in a list.
	if (integrated_loudness_calculation_error == True) or (timeslice_calculation_error == True):
		# Loudness calculation encountered an error, generate gnuplot commands for plotting default graphics with the error message.
		error_message_to_print_with_gnuplot = ''
		
		if integrated_loudness_calculation_error == True:
			error_message = 'ERROR !!! in libebur128 integrated loudness calculation: ' * english + 'VIRHE !!! libebur128:n lra laskennassa: ' * finnish + integrated_loudness_calculation_error_message
			error_message_destinations = []
			
			if integrated_loudness_is_below_measurement_threshold == True:
				# This error message is not very important so don't send it by email, only send it to other possible destinations (screen, logfile).
				error_message_destinations = copy.deepcopy(where_to_send_error_messages)
				if 'email' in error_message_destinations:
					error_message_destinations.remove('email')
					
			send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, error_message_destinations)
			error_message_to_print_with_gnuplot = integrated_loudness_calculation_error_message + '\\n'
			
		if timeslice_calculation_error == True:
			error_message = 'ERROR !!! in libebur128 timeslice calculation: ' * english + 'VIRHE !!! libebur128:n aanekkyystaulukon laskennassa: ' * finnish +  timeslice_calculation_error_message
			send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, [])
			error_message_to_print_with_gnuplot = error_message_to_print_with_gnuplot + timeslice_calculation_error_message + '\\n'
		create_gnuplot_commands_for_error_message(error_message_to_print_with_gnuplot, filename, directory_for_temporary_files, directory_for_results, english, finnish)		
	else:
		# Loudness calculation succeeded.
		
		peak_measurement_string_english = '\\nSample peak: '
		peak_measurement_string_finnish = '\\nHuipputaso: '
		if peak_measurement_method == '--peak=true':
			peak_measurement_string_english = '\\nTruePeak: '
			peak_measurement_string_finnish = peak_measurement_string_english
		
		# Generate gnuplot commands for plotting the graphics. Put all gnuplot commands in a list.
		gnuplot_commands=['set terminal jpeg size 1280,960 medium font \'arial\'', \
		'set output ' + '\"' + gnuplot_temporary_output_graphicsfile.replace('"','\\"') + '\"', \
		'set yrange [ 0 : -60 ] noreverse nowriteback', \
		'set grid', \
		'set title ' + '\"\'' + filename.replace('_', ' ').replace('"','\\"') + '\'\\n' + 'Integrated Loudness ' * english + 'Äänekkyystaso ' * finnish + str(integrated_loudness) + ' LUFS\\n ' + difference_from_target_loudness_string + ' dB from target loudness (-23 LUFS)\\nLoudness Range (LRA) ' * english + ' dB:tä tavoitetasosta (-23 LUFS)\\nÄänekkyyden vaihteluväli (LRA) '  * finnish + str(loudness_range) + ' LU' + peak_measurement_string_english * english + peak_measurement_string_finnish * finnish + highest_peak_db_string + ' dBFS' + warning_message + '\"', \
		'set ylabel ' + '\"Loudness (LUFS)\"' * english + '\"Äänekkyystaso (LUFS)\"' *finnish, \
		plotfile_x_axis_time_information, \
		'set xlabel \"' + plotfile_x_axis_name + '\"', \
		'plot ' + '-23 title \'0 LU (Target Level)\' lw 6 lc rgb \'#99ff00\', ' * english + '-23 title \'0 LU (Tavoitetaso)\' lw 6 lc rgb \'#99ff00\', ' * finnish + '\"' + loudness_calculation_table.replace('"','\\"') + '\"' + ' with lines lw 1 lc rgb \'#c4a45a\' title \'Short-term Loudness\', ' * english + ' with lines lw 1 lc rgb \'#c4a45a\' title \'Tiedoston lyhytaikainen äänekkyystaso\', ' * finnish + str(integrated_loudness) + ' title \'Integrated Loudness\' lw 2 lc rgb \'#008327\'' * english + ' title \'Tiedoston keskimääräinen äänekkyystaso\' lw 2 lc rgb \'#008327\'' * finnish]

		# Write loudness time slice calculation results in a file, gnuplot uses this file for plotting graphics.
		try:
			with open(loudness_calculation_table, 'wb') as timeslice_file_handler:
				timeslice_file_handler.write(b'-60\n') # There is no timeslice at the beginning of the audio (at 0 seconds), however graphics plotting needs this. Add a dummy '-60' value at the beginning of the time slice list. This does not affect loudness calculation result, only graphics plotting.
				timeslice_file_handler.write(timeslice_loudness_calculation_stdout)
				timeslice_file_handler.flush() # Flushes written data to os cache
				os.fsync(timeslice_file_handler.fileno()) # Flushes os cache to disk
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error opening timeslice tablefile for writing ' * english + 'Aikaviipaleiden taulukkotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error opening timeslice tablefile for writing ' * english + 'Aikaviipaleiden taulukkotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])

		# Write gnuplot commands to a file.
		try:
			with open(commandfile_for_gnuplot, 'wt') as gnuplot_commandfile_handler:
				for item in gnuplot_commands:
					gnuplot_commandfile_handler.write(item + '\n')
				gnuplot_commandfile_handler.flush() # Flushes written data to os cache
				os.fsync(gnuplot_commandfile_handler.fileno()) # Flushes os cache to disk
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])

		# Call a subprocess to run gnuplot
		run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish)

		# Call a subprocess to create the loudness corrected audio file.
		create_sox_commands_for_loudness_adjusting_a_file(integrated_loudness_calculation_error, difference_from_target_loudness, filename, english, finnish, hotfolder_path, directory_for_results, directory_for_temporary_files, highest_peak_db, flac_compression_level, output_format_for_intermediate_files, output_format_for_final_file, channel_count, audio_channels_will_be_split_to_separate_mono_files, output_file_too_big_to_split_to_separate_wav_channels)


def create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish):
	
	# This subroutine is run when there has been some kind of error and the user needs to know about it.
	# This subroutine creates the gnuplot commands needed to create a graphics file explaining the error to user.
	
	commandfile_for_gnuplot = directory_for_temporary_files + os.sep + filename + '-gnuplot_commands'
	loudness_calculation_table = directory_for_temporary_files + os.sep + filename + '-loudness_calculation_table'
	gnuplot_temporary_output_graphicsfile = directory_for_temporary_files + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish
	gnuplot_output_graphicsfile = directory_for_results + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish

	# Write 4 coordinates to gnuplot data file. These 4 coordinates are used to draw a big red cross on the error graphics file.
	try:
		with open(loudness_calculation_table, 'wt') as timeslice_file_handler:
			timeslice_file_handler.write('1.0\n' + '10\n' + '\n' + '\n' + '10\n' + '1.0\n')
			timeslice_file_handler.flush() # Flushes written data to os cache
			os.fsync(timeslice_file_handler.fileno()) # Flushes os cache to disk
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error opening gnuplot datafile for writing error graphics data ' * english + 'Gnuplotin datatiedoston avaaminen virhegrafiikan datan kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error opening gnuplot datafile for writing error graphics data ' * english + 'Gnuplotin datatiedoston avaaminen virhegrafiikan datan kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Create gnuplot commands and put then in  a list.
	gnuplot_commands=['set terminal jpeg size 1280,960 medium font \'arial\'', \
	'set output ' + '\"' + gnuplot_temporary_output_graphicsfile.replace('"','\\"') + '\"', \
	'set yrange [ 1 : 10 ]', \
	'set title ' + '\"\'' + filename.replace('_', ' ').replace('"','\\"') + '\'\\n' + 'Loudness calculation encountered an error\\n\\n' * english + 'Äänekkyyden mittaamisessa tapahtui virhe:\\n\\n' * finnish + 'Error Message: ' * english + 'Virheilmoitus: ' * finnish + str(error_message), \
	'plot ' + '\"' + loudness_calculation_table.replace('"','\\"') + '\"' + ' with lines lw 2 title \'\'']

	# Write gnuplot commands to a file.
	try:
		with open(commandfile_for_gnuplot, 'wt') as gnuplot_commandfile_handler:
			for item in gnuplot_commands:
				gnuplot_commandfile_handler.write(item + '\n')
			gnuplot_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(gnuplot_commandfile_handler.fileno()) # Flushes os cache to disk
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Call a subprocess to run gnuplot
	run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish)
	
def run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish):

	# This subroutine runs Gnuplot and generates a graphics file.
	# Gnuplot output is searched for error messages.
	
	commandfile_for_gnuplot = directory_for_temporary_files + os.sep + filename + '-gnuplot_commands'
	loudness_calculation_table = directory_for_temporary_files + os.sep + filename + '-loudness_calculation_table'
	gnuplot_temporary_output_graphicsfile = directory_for_temporary_files + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish
	gnuplot_output_graphicsfile = directory_for_results + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish

	try:
		# Define filename for the temporary file that we are going to use as stdout for the external command.
		stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_gnuplot_stdout.txt'
		# Open the stdout and stderr temporary files in binary write mode.
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:

			# Start gnuplot and give time slice and gnuplot command file names as arguments. Gnuplot generates graphics file in the temporary files directory.
			subprocess.Popen(['gnuplot', commandfile_for_gnuplot], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run gnuplot.
		
			# Make sure all data written to temporary stdout and stderr - files is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
		
	except IOError as reason_for_error:
		error_message = 'Error writing to gnuplot stdout- file ' * english + 'Gnuplotin Stdout- tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error writing to gnuplot stdout- file ' * english + 'Gnuplotin Stdout- tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	# Open the file we used as stdout for the external program and read in what the external program wrote to it.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
			results_from_gnuplot_run = stdout_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_message = 'Error reading from gnuplot stdout- file ' * english + 'Gnuplotin Stdout- tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading from gnuplot stdout- file ' * english + 'Gnuplotin Stdout- tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Convert gnuplot output from binary to UTF-8 text.
	results_of_gnuplot_run_list = results_from_gnuplot_run.decode('UTF-8').strip()
	
	# Delete the temporary stdout - file.
	try:
		os.remove(stdout_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting gnuplot stdout - file ' * english + 'Gnuplotin stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting gnuplot stdout - file ' * english + 'Gnuplotin stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	# If gnuplot outputs something, there was an error. Print message to user.
	if not len(results_of_gnuplot_run_list) == 0:
		error_message = 'ERROR !!! Plotting graphics with Gnuplot, ' * english + 'VIRHE !!! Grafiikan piirtämisessä Gnuplotilla, ' * finnish + ' ' + filename + ' : ' + results_of_gnuplot_run_list
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Remove time slice and gnuplot command files and move graphics file to results directory.
	try:
		os.remove(commandfile_for_gnuplot)
		os.remove(loudness_calculation_table)
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error deleting gnuplot command- or time slice file ' * english + 'Gnuplotin komento- tai aikaviipale-tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting gnuplot command- or time slice file ' * english + 'Gnuplotin komento- tai aikaviipale-tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

	try:
		shutil.move(gnuplot_temporary_output_graphicsfile, gnuplot_output_graphicsfile)
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error moving gnuplot graphics file ' * english + 'Gnuplotin grafiikkatiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error moving gnuplot graphics file ' * english + 'Gnuplotin grafiikkatiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

def create_sox_commands_for_loudness_adjusting_a_file(integrated_loudness_calculation_error, difference_from_target_loudness, filename, english, finnish, hotfolder_path, directory_for_results, directory_for_temporary_files, highest_peak_db, flac_compression_level, output_format_for_intermediate_files, output_format_for_final_file, channel_count, audio_channels_will_be_split_to_separate_mono_files, output_file_too_big_to_split_to_separate_wav_channels):

	'''This subroutine creates sox commands that are used to create a loudness corrected file'''

	# This subroutine works like this:
	# ---------------------------------
	# The process gets the difference from target loudness as it's argument.
	# The process creates sox commands and starts sox using the difference as gain parameter and creates a loudness corrected wav.
	# The corrected file is written to temporary directory and when ready moved to the target directory for the user to see. This prevents user from using an incomplete file by accident.
	# If ouput files uncompressed size would exceed wav 4 GB limit, then the file is split into individual mono files. If individual size of these mono channels would still exceed 4 GB then flac or another suitable codec is used.
	
	# Assing some values to variables.
	integrated_loudness_calculation_results_list = []
	file_to_process = hotfolder_path + os.sep + filename
	filename_and_extension = os.path.splitext(filename)
	global integrated_loudness_calculation_results
	global libebur128_path

	# Create loudness corrected file if there were no errors in loudness calculation.
	if (integrated_loudness_calculation_error == False):
		
		# Assing some values to variables.
		# Output format for files has been already been decided in subroutine: get_audiofile_info_with_sox_and_determine_output_format. Output format is wav for files of 4 GB or less and flac for very large files that can't be split to separate wav files.
		combined_channels_targetfile_name = filename_and_extension[0] + '_-23_LUFS.' + output_format_for_final_file
		temporary_peak_limited_targetfile = filename_and_extension[0] + '-Peak_Limited.' + output_format_for_intermediate_files
		difference_from_target_loudness_sign_inverted = difference_from_target_loudness * -1 # The sign (+/-) of the difference from target loudness needs to be flipped for sox. Plus becomes minus and vice versa.
		
		start_of_sox_commandline = ['sox']
		# If output file exceeds 4 GB then sox can't read input file reliably (uncompressed size of it exceed 4 GB also), we need to read inputfile through libsndfile. Libsndfile reads bigger than 4 GB files only in 64 bit Ubuntu, 32 bit will not work correctly.
		if (audio_channels_will_be_split_to_separate_mono_files == True) or (output_file_too_big_to_split_to_separate_wav_channels == True):
			start_of_sox_commandline.extend(['-t', 'sndfile'])
		
		# Set the absolute peak level for the resulting corrected audio file.
		# If sample peak is used for the highest value, then set the absolute peak to be -4 dBFS (resulting peaks will be about 1 dB higher than this).
		# If TruePeak calculations are used to measure highest peak, then set the maximum peak level to -2 dBFS (resulting peaks will be about 1 dB higher than this).
		audio_peaks_absolute_ceiling = -4
		if peak_measurement_method == '--peak=true':
			audio_peaks_absolute_ceiling = -2
		
		# Calculate the level where absolute peaks must be limited to before gain correction, to get the resulting max peak level we want.
		hard_limiter_level = difference_from_target_loudness + audio_peaks_absolute_ceiling
		
		if difference_from_target_loudness >= 0:
			
			#############################################################################################################################################
			# Create loudness corrected file. In this case volume is adjusted down or it is not adjusted (already at -23 LUFS) so no limiting is needed #
			#############################################################################################################################################
				
			# Loudness correction requires decreasing volume, no peak limiting is needed. Run sox without limiter.
			sox_commandline = []
			list_of_sox_commandlines = []
			list_of_filenames = []
			
			if audio_channels_will_be_split_to_separate_mono_files == False:
				# Gather sox commandline to a list.
				sox_commandline = start_of_sox_commandline
				sox_commandline.append(file_to_process)
				
				# If output format is flac add flac compression level commands right after the input file name.
				if output_format_for_final_file == 'flac':
					sox_commandline.extend(flac_compression_level)
				sox_commandline.extend([directory_for_temporary_files + os.sep + combined_channels_targetfile_name, 'gain', str(difference_from_target_loudness_sign_inverted)])
				
				#Gather all names of processed files to a list.
				list_of_filenames = [combined_channels_targetfile_name]
				
				# Run sox with the commandline compiled in the lines above.
				run_sox(directory_for_temporary_files, filename, sox_commandline, english, finnish, 0)
			
			else:
			
				# The combined channels in final output file exceeds the max file size and the file needs to be split to separate mono files.
				# Create commandlines for extracting each channel to its own file.
				
				for counter in range(1, channel_count + 1):
					split_channel_targetfile_name = filename_and_extension[0] + '-Channel-' * english + '-Kanava-' * finnish + str(counter) + '_-23_LUFS.' + output_format_for_final_file
					sox_commandline = []
					sox_commandline.extend(start_of_sox_commandline)
					sox_commandline.extend([file_to_process, directory_for_temporary_files + os.sep + split_channel_targetfile_name, 'remix', str(counter), 'gain', str(difference_from_target_loudness_sign_inverted)])
			
					#Gather all commands needed to process a file to a list of sox commandlines.
					list_of_sox_commandlines.append(sox_commandline)
					list_of_filenames.append(split_channel_targetfile_name)
				
				# Run several sox commands in parallel threads, this speeds up splitting the file to separate mono files.	
				run_sox_commands_in_parallel_threads(directory_for_temporary_files, filename, list_of_sox_commandlines, english, finnish)
			
			# Processing is ready move audio files to target directory.
			move_processed_audio_files_to_target_directory(directory_for_temporary_files, directory_for_results, list_of_filenames, english, finnish)
		
		if difference_from_target_loudness < 0:
			
			##################################################################################################
			# Create loudness corrected file. In this case volume is adjusted up so limiting might be needed #
			##################################################################################################
			
			if highest_peak_db + difference_from_target_loudness_sign_inverted > audio_peaks_absolute_ceiling:
				
				#########################################################################################################################
				# Peaks will exceed our upper peak limit defined in 'audio_peaks_absolute_ceiling'. Create a peak limited file with sox #
				# After this the loudness of the file needs to be recalculated                                                          #
				#########################################################################################################################
				
				list_of_sox_commandlines = []
				
				# Create sox commands for all four limiter stages.
				# The limiter tries to introduce as little distortion as possible while being very effective in hard-limiting the peaks.
				# There are three limiting - stages each 1 dB above previous and with 'tighter' attack and release values than the previous one.
				# These stages limit the peaks while rounding the peaks.
				# Still some very fast peaks escape these three stages and the final hard-limiter stage deals with those.
				compander_1 = ['compand', '0.005,0.3', '1:' + str(hard_limiter_level + -3) + ',' + str(hard_limiter_level + -3) + ',0,' + str(hard_limiter_level +  -2)]
				compander_2 = ['compand', '0.002,0.15', '1:' + str(hard_limiter_level + -2) + ',' + str(hard_limiter_level + -2) + ',0,' + str(hard_limiter_level +  -1)]
				compander_3 = ['compand', '0.001,0.075', '1:' + str(hard_limiter_level + -1) + ',' + str(hard_limiter_level + -1) + ',0,' + str(hard_limiter_level +  -0)]
				hard_limiter = ['compand', '0,0', '3:' + str(hard_limiter_level + -3) + ',' + str(hard_limiter_level + -3) + ',0,'+ str(hard_limiter_level + 0)]
				
				# Combine all sox commands into one list.
				sox_commandline = start_of_sox_commandline
				sox_commandline.append(file_to_process)
				# If output format is flac add flac compression level commands right after the input file name.
				if output_format_for_intermediate_files == 'flac':
					sox_commandline.extend(flac_compression_level)
				sox_commandline.extend([directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile])
				sox_commandline.extend(compander_1)
				sox_commandline.extend(compander_2)
				sox_commandline.extend(compander_3)
				sox_commandline.extend(hard_limiter)
				
				#Gather all commands needed to process a file to a list of sox commandlines.
				list_of_sox_commandlines.append(sox_commandline)
				
				# Run sox with the commandline compiled in the lines above.
				run_sox(directory_for_temporary_files, filename, sox_commandline, english, finnish, 0)
				
				########################################################################################
				# Loudness of the peak limited file needs to be calculated again, measure the loudness #
				########################################################################################
				
				event_for_integrated_loudness_calculation = threading.Event() # Create a dummy event for loudness calculation subroutine. This is needed by the subroutine, but not used anywhere else, since we do not start loudness calculation as a thread.
				libebur128_commands_for_integrated_loudness_calculation=[libebur128_path, 'scan', '-l', peak_measurement_method] # Put libebur128 commands in a list.
				calculate_integrated_loudness(event_for_integrated_loudness_calculation, temporary_peak_limited_targetfile, directory_for_temporary_files, libebur128_commands_for_integrated_loudness_calculation, english, finnish)
				
				##################################################################################################
				# After calculating loudness of the peak limited file, adjust the volume of the file to -23 LUFS #
				##################################################################################################
				
				# Get loudness calculation results from the integrated loudness calculation process. Results are in list format in dictionary 'integrated_loudness_calculation_results', assing results to variables.
				integrated_loudness_calculation_results_list = integrated_loudness_calculation_results.pop(temporary_peak_limited_targetfile)# Get loudness results for the file and remove this information from dictionary.
				difference_from_target_loudness = integrated_loudness_calculation_results_list[1]
				difference_from_target_loudness_sign_inverted = difference_from_target_loudness * -1 # The sign (+/-) of the difference from target loudness needs to be flipped for sox. Plus becomes minus and vice versa.
				highest_peak_db = integrated_loudness_calculation_results_list[5]
				sox_commandline = []
				list_of_sox_commandlines = []
				list_of_filenames = []
				
				if audio_channels_will_be_split_to_separate_mono_files == False:
					# Gather sox commandline to a list.
					sox_commandline = [start_of_sox_commandline, directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile]
					# If output format is flac add flac compression level commands right after the input file name.
					if output_format_for_final_file == 'flac':
						sox_commandline.extend(flac_compression_level)
					sox_commandline.extend([directory_for_temporary_files + os.sep + combined_channels_targetfile_name, 'gain', str(difference_from_target_loudness_sign_inverted)])
					
					#Gather all names of processed files to a list.
					list_of_filenames = [combined_channels_targetfile_name]
					
					# Run sox with the commandline compiled in the lines above.
					run_sox(directory_for_temporary_files, filename, sox_commandline, english, finnish, 0)
				
				else:
			
					# The combined channels in final output file exceeds the max file size and the file needs to be split to separate mono files.
					# Create commandlines for extracting each channel to its own file.
					
					for counter in range(1, channel_count + 1):
						split_channel_targetfile_name = filename_and_extension[0] + '-Channel-' * english + '-Kanava-' * finnish + str(counter) + '_-23_LUFS.' + output_format_for_final_file
						sox_commandline = []
						sox_commandline.extend(start_of_sox_commandline)
						sox_commandline.extend([directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile, directory_for_temporary_files + os.sep + split_channel_targetfile_name, 'remix', str(counter), 'gain', str(difference_from_target_loudness_sign_inverted)])
				
						#Gather all commands needed to process a file to a list of sox commandlines.
						list_of_sox_commandlines.append(sox_commandline)
						list_of_filenames.append(split_channel_targetfile_name)

					# Run several sox commands in parallel threads, this speeds up splitting the file to separate mono files.	
					run_sox_commands_in_parallel_threads(directory_for_temporary_files, filename, list_of_sox_commandlines, english, finnish)
				
				# Processing is ready move audio files to target directory.
				move_processed_audio_files_to_target_directory(directory_for_temporary_files, directory_for_results, list_of_filenames, english, finnish)
			
			else:
				
				#######################################################################################################################
				# Volume of the file needs to be adjusted up, but peaks will not exceed our upper limit so no peak limiting is needed #
				# Create loudness corrected file                                                                                      #
				#######################################################################################################################
				
				sox_commandline = []
				list_of_sox_commandlines = []
				list_of_filenames = []
				
				if audio_channels_will_be_split_to_separate_mono_files == False:
					# Gather sox commandline to a list.
					sox_commandline = start_of_sox_commandline
					sox_commandline.append(file_to_process)
					# If output format is flac add flac compression level commands right after the input file name.
					if output_format_for_final_file == 'flac':
						sox_commandline.extend(flac_compression_level)
					sox_commandline.extend([directory_for_temporary_files + os.sep + combined_channels_targetfile_name, 'gain', str(difference_from_target_loudness_sign_inverted)])
					
					#Gather all names of processed files to a list.
					list_of_filenames = [combined_channels_targetfile_name]
					
					# Run sox with the commandline compiled in the lines above.
					run_sox(directory_for_temporary_files, filename, sox_commandline, english, finnish, 0)
					
				else:
			
					# The combined channels in final output file exceeds the max file size and the file needs to be split to separate mono files.
					# Create commandlines for extracting each channel to its own file.
					
					for counter in range(1, channel_count + 1):
						split_channel_targetfile_name = filename_and_extension[0] + '-Channel-' * english + '-Kanava-' * finnish + str(counter) + '_-23_LUFS.' + output_format_for_final_file
						sox_commandline = []
						sox_commandline.extend(start_of_sox_commandline)
						sox_commandline.extend([file_to_process, directory_for_temporary_files + os.sep + split_channel_targetfile_name, 'remix', str(counter), 'gain', str(difference_from_target_loudness_sign_inverted)])
				
						#Gather all commands needed to process a file to a list of sox commandlines.
						list_of_sox_commandlines.append(sox_commandline)
						list_of_filenames.append(split_channel_targetfile_name)
					
					# Run several sox commands in parallel threads, this speeds up splitting the file to separate mono files.	
					run_sox_commands_in_parallel_threads(directory_for_temporary_files, filename, list_of_sox_commandlines, english, finnish)
				
				# Processing is ready move audio files to target directory.
				move_processed_audio_files_to_target_directory(directory_for_temporary_files, directory_for_results, list_of_filenames, english, finnish)
		
		# If the temporary peak limited file is there, delete it.
		if os.path.exists(directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile):
			try:
				os.remove(directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile)
			except KeyboardInterrupt:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error deleting temporary peak limited file ' * english + 'Väliaikaisen limitoidun tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error deleting temporary peak limited file ' * english + 'Väliaikaisen limitoidun tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])

def run_sox_commands_in_parallel_threads(directory_for_temporary_files, filename, list_of_sox_commandlines, english, finnish):
	
	list_of_sox_commandlines.reverse()
	number_of_allowed_simultaneous_sox_processes = 10
	events_for_sox_commands_currently_running = []
	list_of_finished_processes = []
	
	while True:
		
		# If processing of all sox commands is ready then exit the loop.
		if (len(list_of_sox_commandlines) == 0) and (len(events_for_sox_commands_currently_running) == 0):
			break
	
		# Check if there are less processing threads going on than allowed, if true start some more.
		while len(events_for_sox_commands_currently_running) < number_of_allowed_simultaneous_sox_processes:
			
			if len(list_of_sox_commandlines) > 0: # Check if there still is unprocessed sox commands waiting in the list of sox commandlines.
		
				# Get one commandline from list of commandlines.
				sox_commandline = list_of_sox_commandlines.pop()
		
				# Create event for the process. When the process is ready it sets event = set, so that we know that we can start more processes.
				event_for_sox_command = threading.Event() # Create a unique event for the process. This event is used to signal that this process has finished.
				
				# Add the event to the list of running sox processes.
				events_for_sox_commands_currently_running.append(event_for_sox_command)
				
				# Create a thread for the sox proces.
				sox_process = threading.Thread(target=run_sox, args=(directory_for_temporary_files, filename, sox_commandline, english, finnish, event_for_sox_command)) # Create a process instance.
				
				# Start sox thread.
				thread_object = sox_process.start() # Start the calculation process in it's own thread.
			
			# If all sox commandlines has been used, then break out of the loop.
			if len(list_of_sox_commandlines) == 0:
				break
			
		###################################
		# Find threads that have finished #
		###################################
		
		list_of_finished_processes=[]
		
		for counter in range(0, len(events_for_sox_commands_currently_running)):
			if events_for_sox_commands_currently_running[counter].is_set(): # Check if event is set.
				list_of_finished_processes.append(events_for_sox_commands_currently_running[counter]) # Add event of finished thread to a list.

		# If a thread has finished, remove it's event from the list of files being processed.
		for item in list_of_finished_processes: # Get events who's processing threads have completed.
			events_for_sox_commands_currently_running.remove(item) # Remove the event from the list of files currently being calculated upon.
		
		# Wait 1 second before running the loop again
		time.sleep(1)


def run_sox(directory_for_temporary_files, filename, sox_commandline, english, finnish, event_for_sox_command):
	
	we_are_part_of_a_multithread_sox_command = False
	global debug
	
	if debug == True:
		print()
		print('Sox commandline:', sox_commandline)
		print()
	
	# Test if the value in variable is an event or not. If it is an event, then there are other sox threads processing the same file.
	variable_type_string = str(type(event_for_sox_command))
	if 'Event' in variable_type_string:
		we_are_part_of_a_multithread_sox_command = True
	
	# Define filename for the temporary file that we are going to use as stdout for the external command.
	results_from_sox_run = b''
	stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_sox_stdout.txt'
	
	# If there are other sox threads processing this same file, then our stdout filename must be unique.
	if we_are_part_of_a_multithread_sox_command == True:
		stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '-event-' + str(event_for_sox_command).split(' ')[3].strip('>') + '_sox_stdout.txt'
		
	# Open the stdout temporary file in binary write mode.
	try:
		
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
			
			# Run a sox command.
			subprocess.Popen(sox_commandline, stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0]
			
			# Make sure all data written to temporary stdout and stderr - files is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
	
	except IOError as reason_for_error:
		error_message = 'Error writing to sox stdout - file ' * english + 'Soxin stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error writing to sox stdout - file ' * english + 'Soxin stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	# Open the file we used as stdout for sox and read in what it wrote to it.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
			results_from_sox_run = stdout_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_message = 'Error reading from sox stdout - file ' * english + 'Soxin stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading from sox stdout - file ' * english + 'Soxin stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])	

	# Convert sox output from binary to UTF-8 text.
	results_from_sox_run_string = results_from_sox_run.decode('UTF-8').strip()
	
	# Split sox output to a list of text lines.
	if results_from_sox_run_string != '':
		results_from_sox_run_list = results_from_sox_run_string.split('\n')
	else:
		results_from_sox_run_list = []
	
	# Delete the temporary stdout - file.
	try:
		if os.path.exists(stdout_for_external_command):
			os.remove(stdout_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting sox stdout - file ' * english + 'Soxin stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting sox stdout - file ' * english + 'Soxin stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	# If sox did output something, there was and error. Print message to user.
	if not len(results_from_sox_run_list) == 0:
		for item in results_from_sox_run_list:
			error_message = 'ERROR !!!' * english + 'VIRHE !!!' * finnish + ' ' + filename + ': ' + item
			send_error_messages_to_screen_logfile_email(error_message, [])
			
	# If we recieved an event from the calling routine, then we need to set that event.
	# We recieved an event if the calling process runs several sox commands in parallel threads.
	# The variable holding the event, might have an event or the value 0. In the latter case there are no parallel threads and we don't need to change the value in the variable.
	
	# Set our event so that the calling process knows we are ready.
	if we_are_part_of_a_multithread_sox_command == True:
		event_for_sox_command.set()

def move_processed_audio_files_to_target_directory(source_directory, target_directory, list_of_filenames, english, finnish):
	
	for filename in list_of_filenames:
		# Check if file exists and move it to results folder.
		if os.path.exists(source_directory + os.sep + filename):
			# There were no errors, and loudness corrected file is ready, move it from temporary directory to results directory.
			try:
				shutil.move(source_directory + os.sep + filename, target_directory + os.sep + filename)
			except KeyboardInterrupt:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error moving loudness adjusted file ' * english + 'Äänekkyyskorjatun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error moving loudness adjusted file ' * english + 'Äänekkyyskorjatun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])

def get_audiofile_info_with_sox_and_determine_output_format(directory_for_temporary_files, hotfolder_path, filename):
	
	# This subroutine gets audio file information with sox and determines based on estimated uncompressed file size what the output file format is.
	# There is only one audio stream in files that this subroutine processes.
	
	# Read audio file technical info with sox
	channel_count_string = ''
	sample_rate_string = ''
	bit_depth_string = ''
	sample_count_string = ''
	channel_count = 0
	sample_rate = 0
	bit_depth = 8
	sample_count = 0
	file_to_process = hotfolder_path + os.sep + filename
	estimated_uncompressed_size_for_single_mono_file = 0
	estimated_uncompressed_size_for_combined_channels = 0
	global wav_format_maximum_file_size
	flac_compression_level = ['-C', '1']
	output_format_for_intermediate_files = 'wav'
	output_format_for_final_file = 'wav'
	
	try:
		# Define filename for the temporary file that we are going to use as stdout for the external command.
		stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_sox_read_audio_info_stdout.txt'
		# Open the stdout temporary file in binary write mode.
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
			
			# Get technical info from audio file using sox.
			subprocess.Popen(['sox', '--i', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0]
		
			# Make sure all data written to temporary stdout and stderr - files is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
			
	except IOError as reason_for_error:
		error_message = 'Error writing to (audio file info reading) sox stdout - file ' * english + 'Soxin (audiotiedoston teknisten tietojen luku) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error writing to (audio file info reading) sox stdout - file ' * english + 'Soxin (audiotiedoston teknisten tietojen luku) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Open the file we used as stdout for the external program and read in what the external program wrote to it.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
			results_from_sox_run = stdout_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_message = 'Error reading from  (audio file info reading)sox stdout - file ' * english + 'Soxin (audiotiedoston teknisten tietojen luku) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading from  (audio file info reading)sox stdout - file ' * english + 'Soxin (audiotiedoston teknisten tietojen luku) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])	

	# Convert sox output from binary to UTF-8 text and split text lines to a list.

	audio_file_technical_info_list = results_from_sox_run.decode('UTF-8').split('\n')

	# Delete the temporary stdout - file.
	try:
		os.remove(stdout_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting (audio file info reading) sox stdout - file ' * english + 'Soxin (audiotiedoston teknisten tietojen luku) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting (audio file info reading) sox stdout - file ' * english + 'Soxin (audiotiedoston teknisten tietojen luku) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Assign audio file technical data to variables
	for text_line in audio_file_technical_info_list:
		if 'Channels' in text_line:
			channel_count_string = text_line.split(':')[1].strip()
		if 'Sample Rate' in text_line:
			sample_rate_string = text_line.split(':')[1].strip()
		if 'Precision' in text_line:
			bit_depth_string = text_line.split(':')[1].strip().split('-')[0]
		if 'Duration' in text_line:
			sample_count_string = text_line.split('=')[1].strip().split(' ')[0]

	# Convert audio technical information from string to integer and assign to variables.
	if channel_count_string.isnumeric() == True:
		channel_count = int(channel_count_string)
	else:
		error_message = 'ERROR !!! I could not parse sox channel count string: ' * english + 'VIRHE !!! En osannut tulkita sox:in antamaa tietoa kanavamäärästä: ' * finnish + '\'' + channel_count_string + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
		send_error_messages_to_screen_logfile_email(error_message, [])

	if sample_rate_string.isnumeric() == True:
		sample_rate = int(sample_rate_string)
	else:
		error_message = 'ERROR !!! I could not parse sox sample rate string: ' * english + 'VIRHE !!! En osannut tulkita sox:in antamaa tietoa näyteenottotaajuudesta: ' * finnish + '\'' + sample_rate_string + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
		send_error_messages_to_screen_logfile_email(error_message, [])

	if bit_depth_string.isnumeric() == True:
		bit_depth = int(bit_depth_string)
	else:
		error_message = 'ERROR !!! I could not parse sox bit depth string: ' * english + 'VIRHE !!! En osannut tulkita sox:in antamaa tietoa bittisyvyydestä: ' * finnish + '\'' + bit_depth_string + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
		send_error_messages_to_screen_logfile_email(error_message, [])

	if sample_count_string.isnumeric() == True:
		sample_count = int(sample_count_string)
	else:
		error_message = 'ERROR !!! I could not parse sox sample count string: ' * english + 'VIRHE !!! En osannut tulkita sox:in antamaa tietoa näytteiden lukumäärästä: ' * finnish + '\'' + sample_count_string + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Sox can not get duration from long files correctly, get audio duration with mediainfo.
	audio_duration = get_audiofile_duration_with_mediainfo(directory_for_temporary_files, filename, file_to_process, english, finnish)
	
	# Calculate estimated uncompressed file size. Add one second of data to the file size (sample_rate = 1 second) to be on the safe side.
	estimated_uncompressed_size_for_single_mono_file = int((sample_rate * audio_duration * int(bit_depth / 8)) + sample_rate)
	estimated_uncompressed_size_for_combined_channels = estimated_uncompressed_size_for_single_mono_file * channel_count
	
	output_file_too_big_to_split_to_separate_wav_channels = False
	audio_channels_will_be_split_to_separate_mono_files = False
	
	# Test if output file will exceed the max size of wav format and assign sox commands and output formats accordingly.
	if (estimated_uncompressed_size_for_combined_channels >= wav_format_maximum_file_size) and (estimated_uncompressed_size_for_single_mono_file >= wav_format_maximum_file_size):
		# In this case both the combined channels in one file and separate mono files each will exceed wav format maximum size. Use lossless compression always.
		output_file_too_big_to_split_to_separate_wav_channels = True
		output_format_for_intermediate_files = 'flac'
		output_format_for_final_file = 'flac'
			
	if (estimated_uncompressed_size_for_combined_channels >= wav_format_maximum_file_size) and (estimated_uncompressed_size_for_single_mono_file < wav_format_maximum_file_size):
		# In this case the combined channels in the file exceeds the maximum size but separate mono files do not.
		# Use lossless compression for intermediate files and split final file to separate mono files.
		audio_channels_will_be_split_to_separate_mono_files = True
		output_format_for_intermediate_files = 'flac'
		output_format_for_final_file = 'wav'
		
	if estimated_uncompressed_size_for_combined_channels < wav_format_maximum_file_size:
		# In this case the combined channels in one file does not exceed the maximum size, so we can use wav for all processing.
		output_format_for_intermediate_files = 'wav'
		output_format_for_final_file = 'wav'
	
	# Print technical data for each file when in debug mode.
	if debug == True:
	
		print()
		print('get_audiofile_info_with_sox_and_determine_output_format')
		print('---------------------------------------------------------')
		print(filename)
		print((len(filename) + 1) * '-')
		print('channel_count_string =', channel_count_string)
		print('sample_rate_string =', sample_rate_string)
		print('bit_depth_string =', bit_depth_string)
		print('sox: sample_count_string (this is not used in calculations because it is incorrect for very long files) =', sample_count_string)
		print('mediainfo: audio_duration (this is used in calculations instead of sox sample count) =', audio_duration)
		print('wav_format_maximum_file_size =', wav_format_maximum_file_size)
		print('estimated_uncompressed_size_for_combined_channels =', estimated_uncompressed_size_for_combined_channels)
		print('difference to max size', wav_format_maximum_file_size - estimated_uncompressed_size_for_combined_channels)
		print('estimated_uncompressed_size_for_single_mono_file =', estimated_uncompressed_size_for_single_mono_file)
		print('difference to max size', wav_format_maximum_file_size - estimated_uncompressed_size_for_single_mono_file)
		print('output_format_for_intermediate_files =', output_format_for_intermediate_files)
		print('output_format_for_final_file =', output_format_for_final_file)
		print('estimated_uncompressed_size_for_combined_channels =', estimated_uncompressed_size_for_combined_channels)
		print('audio_channels_will_be_split_to_separate_mono_files =', audio_channels_will_be_split_to_separate_mono_files)
		print('output_file_too_big_to_split_to_separate_wav_channels =', output_file_too_big_to_split_to_separate_wav_channels)
		print()
	
	return(channel_count, sample_rate, bit_depth, sample_count, flac_compression_level, output_format_for_intermediate_files, output_format_for_final_file, audio_channels_will_be_split_to_separate_mono_files, audio_duration, output_file_too_big_to_split_to_separate_wav_channels)

def get_realtime(english, finnish):

	'''Get current time and return it so that each digit is two numbers wide (7 becomes 07)'''

	# Get current time and put hours, minutes and seconds in to their own variables.
	current_time = time.localtime
	year = current_time().tm_year
	month = current_time().tm_mon
	day = current_time().tm_mday
	hours = current_time().tm_hour
	minutes = current_time().tm_min
	seconds = current_time().tm_sec

	# The length of each time string is either 1 or 2. Subtract the string length from number 2 and use the result to count how many zeroes needs to be before the time string.
	year = str(year)
	month = str('0' *( 2 - len(str(month))) + str(month))
	day = str('0' * (2 - len(str(day))) + str(day))
	hours = str('0' * (2 - len(str(hours))) + str(hours))
	minutes = str('0' *( 2 - len(str(minutes))) + str(minutes))
	seconds = str('0' * (2 - len(str(seconds))) + str(seconds))

	# Return the time string.
	realtime = year + '.' + month + '.' + day + '_' + 'at' * english + 'klo' * finnish + '_' + hours + '.' + minutes + '.' + seconds
	return (realtime)

def decompress_audio_streams_with_ffmpeg(event_1_for_ffmpeg_audiostream_conversion, event_2_for_ffmpeg_audiostream_conversion, filename, file_format_support_information, hotfolder_path, directory_for_temporary_files, english, finnish):
	'''This subprocess decompresses all valid audiostreams from a file with ffmpeg'''

	# This subprocess works like this:
	# ---------------------------------
	# FFmpeg is started to extract all valid audio streams from the file.
	# The extracted files are losslessly compressed with flac to save disk space. (Flac also supports file sizes larger than 4 GB. Note: Flac compression routines in ffmpeg are based on flake and are much faster than the ones in the standard flac - command).
	# The resulting files are moved to the HotFolder so the program sees them as new files and queues them for loudness calculation.
	# The original file is queued for deletion.

	global files_queued_for_deletion
	
	# In list 'file_format_support_information' we already have all the information FFmpeg was able to find about the valid audio streams in the file, assign all info to variables.
	natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames = file_format_support_information
	
	try:
		# Define filename for the temporary file that we are going to use as stdout for the external command.
		stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_ffmpeg_audio_stream_demux_stdout.txt'
		# Open the stdout temporary file in binary write mode.
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
	
			# Run ffmpeg to extract valid audio streams and parse output
			subprocess.Popen(ffmpeg_commandline, stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0]
	
			# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
	
	except IOError as reason_for_error:
		error_message = 'Error writing to ffmpeg (audio stream demux) stdout - file ' * english + 'FFmpeg (audio streamien demux) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error writing to ffmpeg (audio stream demux) stdout - file ' * english + 'FFmpeg (audio streamien demux) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Open the file we used as stdout for the external program and read in what the external program wrote to it.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
			ffmpeg_run_output = stdout_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_message = 'Error reading from ffmpeg (audio stream demux) stdout - file ' * english + 'FFmpeg (audio streamien demux) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading from ffmpeg (audio stream demux) stdout - file ' * english + 'FFmpeg (audio streamien demux) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Convert ffmpeg output from binary to UTF-8 text.
	try:
		ffmpeg_run_output_decoded = ffmpeg_run_output.decode('UTF-8') # Convert ffmpeg output from binary to utf-8 text.
	except UnicodeDecodeError:
		# If UTF-8 conversion fails, try conversion with another character map.
		ffmpeg_run_output_decoded = ffmpeg_run_output.decode('ISO-8859-15') # Convert ffmpeg output from binary to text.
	
	ffmpeg_run_output_result_list = str(ffmpeg_run_output_decoded).split('\n')
	for item in ffmpeg_run_output_result_list:
		if 'error:' in item.lower(): # If there is the string 'error' in ffmpeg's output, there has been an error.
			error_message = 'ERROR !!! Extracting audio streams with ffmpeg, ' * english + 'VIRHE !!! Audio streamien purkamisessa ffmpeg:illä, ' * finnish + ' ' + filename + ' : ' + item
			send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Delete the temporary stdout - file.
	try:
		os.remove(stdout_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting ffmpeg (audio stream demux) stdout - file ' * english + 'FFmpeg (audio streamien demux) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting ffmpeg (audio stream demux) stdout - file ' * english + 'FFmpeg (audio streamien demux) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Move each audio file we created from temporary directory to results directory.
	for item in target_filenames:
		try:
			shutil.move(directory_for_temporary_files + os.sep + item, hotfolder_path + os.sep + item)
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error moving ffmpeg decompressed file ' * english + 'FFmpeg:illä puretun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error moving ffmpeg decompressed file ' * english + 'FFmpeg:illä puretun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Queue the original file for deletion. It is no longer needed since we have extracted all audio streams from it.		
	files_queued_for_deletion.append(filename)

	# Set the events so that the main program can see that extracting audio streams from file is ready.
	event_1_for_ffmpeg_audiostream_conversion.set()
	event_2_for_ffmpeg_audiostream_conversion.set()

def send_error_messages_to_screen_logfile_email(error_message, send_error_messages_to_these_destinations):
	
	# This subroutine prints error messages to the screen or logfile or sends them by email.
	# The variable 'error_message' holds the actual message and the list 'where_to_send_error_messages' tells where to print / send them. The list can have any or all of these values: 'screen', 'logfile', 'email'.
	
	global error_messages_to_email_later_list # This variable is used to store messages that are later all sent by email in one go.
	global where_to_send_error_messages
	global error_logfile_path
	error_message_with_timestamp = str(get_realtime(english, finnish)) + '   ' + error_message # Add the current date and time at the beginning of the error message.
	
	# If the calling subroutine did not define where it wants us to send error messages then use global defaults.
	if send_error_messages_to_these_destinations == []:
		send_error_messages_to_these_destinations = where_to_send_error_messages
	
	# Print error messages to screen
	if 'screen' in send_error_messages_to_these_destinations:
		print('\033[7m' + '\r-------->  ' + error_message_with_timestamp + '\033[0m')

	# Print error messages to a logfile
	if 'logfile' in send_error_messages_to_these_destinations:
		try:
			with open(error_logfile_path, 'at') as error_file_handler:
				error_file_handler.write(error_message_with_timestamp + '\n')
				error_file_handler.flush() # Flushes written data to os cache
				os.fsync(error_file_handler.fileno()) # Flushes os cache to disk
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			exception_error_message = 'Error opening error logfile for writing ' * english + 'Virhe lokitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			print('\033[7m' + '\r-------->  ' + exception_error_message + '\033[0m')
			error_messages_to_email_later_list.append(exception_error_message)
		except OSError as reason_for_error:
			exception_error_message = 'Error opening error logfile for writing ' * english + 'Virhe lokitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			print('\033[7m' + '\r-------->  ' + exception_error_message + '\033[0m')
			error_messages_to_email_later_list.append(exception_error_message)
			
	# If user wants us to send error messages by email, write error message to a list that is watched by the thread that sends the emails.
	if 'email' in send_error_messages_to_these_destinations:
		error_messages_to_email_later_list.append(error_message_with_timestamp)
		
def send_error_messages_by_email_thread(email_sending_details, english, finnish):
	
	# This subroutine is started from the main program as it's own thread and it sends error messages by email in intervals defined by the user.
	# The error messages are continuously gathered to a list called 'error_messages_to_email_later_list' by the subroutine 'send_error_messages_to_screen_logfile_email'.
	# The dictionary 'email_sending_details' holds the details needed to send email messages: smpt-server, port, sender email address, recipient email addresses, username and password to smpt - server.
	
	global silent
	global error_logfile_path
	global error_messages_to_email_later_list # This global variable holds all the error messages we need to send.
	global all_ip_addresses_of_the_machine
	global loudness_correction_pid
	global version
	
	error_messages_to_send = [] # Error messages are moved from the global list above to this local list.
	reason_for_failed_send = [] # If sending fails we store the reason for error in this variable and print it to the logfile.
	
	while True:
	
		# We are only allowed to send error messages periodically, sleep until the wait period is over.
		time.sleep(email_sending_details['email_sending_interval'])

		# The wait period is over, check if there are any new error messages in the list.
		error_messages_to_send = []
		message_text_string = ''
		
		# Get IP-Addresses of the machine.
		all_ip_addresses_of_the_machine = get_ip_addresses_of_the_host_machine()
		machine_info = '\n\nLoudnessCorrection info:\n--------------------------------------\n' + 'Commandline: ' + ' '.join(sys.argv) + '\n' + 'IP-Addresses: ' + ','.join(all_ip_addresses_of_the_machine) + '\n' + 'PID: ' + str(loudness_correction_pid) + '\n' + 'LoudnessCorrection version: ' + version + '\n\n'
		
		if len(error_messages_to_email_later_list) > 0:
			
			# Delete error messages from the global list and copy them to our local list.
			while len(error_messages_to_email_later_list) > 0:
				error_messages_to_send.append(error_messages_to_email_later_list.pop(0))

			# Consolidate email text lines to one string adding carriage return after each text line.
			if len(error_messages_to_send) > 1: # The join method adds a line feed after every line of text. But if there is only one line it won't add the linefeed. Use join to add carriage return if there are more than 1 message lines.
				message_text_string = '\n\n'.join(error_messages_to_send)
			else:
				message_text_string = error_messages_to_send[0] + '\n'
			message_text_string = message_text_string + machine_info
			
			# Compile the start of the email message.
			email_message_content = email.mime.multipart.MIMEMultipart()
			email_message_content['From'] = email_sending_details['smtp_username']
			email_message_content['To'] = ', '.join(email_sending_details['message_recipients'])
			email_message_content['Subject'] = email_sending_details['message_title']
		   
			# Append the error messages to the email message.
			email_message_content.attach(email.mime.text.MIMEText(message_text_string.encode('utf-8'), _charset='utf-8'))
		   
			# Email message is ready, before sending it, it must be compiled into a long string of characters.
			email_message_content_string = email_message_content.as_string()

			# Start communication with the smtp-server.
			try:
				mailServer = smtplib.SMTP(email_sending_details['smtp_server_name'], email_sending_details['smtp_server_port'], 'localhost', 15) # Timeout is set to 15 seconds.
				mailServer.ehlo()
				  
				# Uncomment the following line if you want to see printed out the final message that is sent to the smtp server
				# print('email_message_content_string =', email_message_content_string)
				
				# Open a secure tls connection if the smtp-server requires it.
				if email_sending_details['use_tls'] == True:
					mailServer.starttls()
					mailServer.ehlo() # After starting tls, ehlo must be done again.
				# If smtp-server requires authentication, send username and password.
				if email_sending_details['smtp_server_requires_authentication'] == True:
					mailServer.login(email_sending_details['smtp_username'], email_sending_details['smtp_password'])
				# Send email.
				mailServer.sendmail(email_sending_details['smtp_username'], email_sending_details['message_recipients'], email_message_content_string)
				mailServer.close()
				
			except smtplib.socket.timeout as reason_for_error:
				reason_for_failed_send.append('Error, Timeout error: ' + str(reason_for_error))
			except smtplib.socket.error as reason_for_error:
				reason_for_failed_send.append('Error, Socket error: ' + str(reason_for_error))
			except smtplib.SMTPRecipientsRefused as reason_for_error:
				reason_for_failed_send.append('Error, All recipients were refused: ' + str(reason_for_error))
			except smtplib.SMTPHeloError as reason_for_error:
				reason_for_failed_send.append('Error, The server didn’t reply properly to the HELO greeting: ' + str(reason_for_error))
			except smtplib.SMTPSenderRefused as reason_for_error:
				reason_for_failed_send.append('Error, The server didn’t accept the sender address: ' + str(reason_for_error))
			except smtplib.SMTPDataError as reason_for_error:
				reason_for_failed_send.append('Error, The server replied with an unexpected error code or The SMTP server refused to accept the message data: ' + str(reason_for_error))
			except smtplib.SMTPException as reason_for_error:
				reason_for_failed_send.append('Error, The server does not support the STARTTLS extension or No suitable authentication method was found: ' + str(reason_for_error))
			except smtplib.SMTPAuthenticationError as reason_for_error:
				reason_for_failed_send.append('Error, The server didn’t accept the username/password combination: ' + str(reason_for_error))
			except smtplib.SMTPConnectError as reason_for_error:
				reason_for_failed_send.append('Error, Error occurred during establishment of a connection with the server: ' + str(reason_for_error))
			except RuntimeError as reason_for_error:
				reason_for_failed_send.append('Error, SSL/TLS support is not available to your Python interpreter: ' + str(reason_for_error))
			# If sending the email failed, print the reason for error to screen and logfile, but only if user has allowed printing to screen and logfile.
			if len(reason_for_failed_send) > 0:
				if silent == False:
					for item in reason_for_failed_send:
						print(item)
				if 'logfile' in where_to_send_error_messages:
					try:
						with open(error_logfile_path, 'at') as error_file_handler:
							for item in reason_for_failed_send:
								error_file_handler.write(item + '\n')
							error_file_handler.flush() # Flushes written data to os cache
							os.fsync(error_file_handler.fileno()) # Flushes os cache to disk
					except KeyboardInterrupt:
						print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
						sys.exit(0)
					except IOError as reason_for_error:
						exception_error_message = 'Error opening error logfile for writing ' * english + 'Virhe lokitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
						if silent == False:
							print('\033[7m' + '\r-------->  ' + exception_error_message + '\033[0m')
					except OSError as reason_for_error:
						exception_error_message = 'Error opening error logfile for writing ' * english + 'Virhe lokitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
						if silent == False:
							print('\033[7m' + '\r-------->  ' + exception_error_message + '\033[0m')
				reason_for_failed_send = []

def write_html_progress_report_thread(english, finnish):
		
	'''This subprocess runs in it's own thread and periodically writes calculation queue information to disk in html format allowing the calculation queue progress to be monitored with a web browser'''
	
	global files_queued_to_loudness_calculation
	global loudness_calculation_queue
	global web_page_path
	global web_page_name
	global html_progress_report_write_interval
	
	while True:
		
		# Wait user defined number of seconds between updating the html-page.
		time.sleep(html_progress_report_write_interval)
		
		loudness_correction_program_info_and_timestamps['write_html_progress_report'] = [write_html_progress_report, int(time.time())] # Update the heartbeat timestamp for the html writing thread. This is used to keep track if the thread has crashed.
		
		counter = 0
		html_code = [] # The finished html - page is stored in this list variable.
		realtime = get_realtime(english, finnish) # Get the current date and time of day.
		
		# Create the start of the html page by putting the first static part of the html - code in to a list variable.
		html_code_part_1 = ['<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">', \
		'<html><head>', \
		'<meta content="text/html; charset=ISO-8859-15" http-equiv="content-type">', \
		'<meta http-equiv="refresh" content="' + str(html_progress_report_write_interval) + '">', \
		'<META HTTP-EQUIV="PRAGMA" CONTENT="NO-CACHE">', \
		'<title>' + 'LoudnessCorrection_Process_Queue' * english + 'AanekkyysKorjauksen laskentajono' * finnish + '</title>', \
		'<h1>' + 'LoudnessCorrection, version ' * english + '&Auml;&auml;nekkyysKorjaus, versio ' * finnish + version + '</h1><br>', \
		'</head><body style="background-color: rgb(255, 255, 255);">', \
		'<h2><font color="#000000">' + str(len(files_queued_to_loudness_calculation)) + ' &nbsp ' + ' Files Waiting In The Queue' * english + 'Tiedostoa jonossa' * finnish + ' &nbsp ' + realtime.replace('_', ' ')  + '</font></h2>', \
		'<hr style="width: 100%; height: 2px;"><font color="#000000"><br>']

		# Get the first 10 filenames waiting for getting into loudness calculation and insert those names in to the html code.
		first_ten_files_queued_to_loudness_calculation = files_queued_to_loudness_calculation[:10] # Get the first 10 filenames from the waiting queue into a list.

		for counter in range(10, 0, -1): # Create index numbers to print in the html-page before each filename.
			# If there is a filename at the queue position then get it's name from the list, if not then use the queue number with an empty string as the filename.
			filename = ''
			if (len(first_ten_files_queued_to_loudness_calculation) > 0) and (counter <= len(first_ten_files_queued_to_loudness_calculation)):
				filename = first_ten_files_queued_to_loudness_calculation[counter - 1]
				filename = filename.replace('ä', '&auml;').replace('Ä', '&Auml;').replace('ö', '&ouml;').replace('Ö', '&Ouml;').replace('å', '&aring;').replace('Å', '&Aring;') # Special Finnish characters in filename won't print correctly unless they are replaced with proper html-codes.
			position_in_queue = str(counter) # This variable holds the queue number we print in html for each file in the queue.
			if len(position_in_queue) == 1: # If queue number is only one digit long (1, 2, 3, etc), use two digits instead (01, 02, 03, etc).
				position_in_queue = '0' + position_in_queue
			# Append information generated above to the html-code.
			html_code_part_1.append(position_in_queue + ': &nbsp;&nbsp;&nbsp; ' + str(filename + '<br>')) # Insert queue number and corresponing filename into the html-code.
		
		# Create the next static part of html-code.		
		html_code_part_2 = ['<br>', \
		'<br>', \
		'<font color="#000000">', \
		'<table color="#FFFFFF" bgcolor="#DDDDDD" border="3" width="100%">', \
		'<tbody>', \
		'<tr>', \
		'<td width="100%">', \
		'<h2><font color="#000000" size="5">', \
		# '<h2><font color="#000000" face="Monotype Corsiva, Verdana" size="5">', \
		'Files Being Processed' * english + 'K&auml;sittelyss&auml; olevat tiedostot' * finnish + '</font></h2>', \
		'<hr style="width: 100%; height: 2px;">', \
		'<p><font color="#000000" size="4">']
		
		# Get the filenames currently in loudness calculation and insert their names into the html-code.
		maximum_number_of_simultaneously_processed_files = int(number_of_processor_cores / 2) # This variable holds the number of files we are able to process simultanously. As two loudness calculation processed are started for each file, this number is always the value in variable 'number_of_processor_cores' divided by two.
		loudness_calculation_queue_list = list(loudness_calculation_queue) # Get the list of filesnames currently in loudness calculation from the 'loudness_calculation_queue' dictionary.
		
		for counter in range(1, maximum_number_of_simultaneously_processed_files + 1): # Create index numbers to print in the html-page before each filename and if there is a file currently in the loudness calculation corresponding to the index number then print that name after the number.
			# If there is a filename at the calculation queue position then get it's name from the list, if not then use empty string as the filename.
			filename = ''
			if (len(loudness_calculation_queue_list) > 0) and (counter <= len(loudness_calculation_queue_list)):
				filename = loudness_calculation_queue_list[counter - 1]
				filename = filename.replace('ä', '&auml;').replace('Ä', '&Auml;').replace('ö', '&ouml;').replace('Ö', '&Ouml;').replace('å', '&aring;').replace('Å', '&Aring;') # Special Finnish characters in filename won't print correctly unless they are replaced with proper html-codes.
			position_in_queue = str(counter) # This variable holds a number we print before the filename.
			if len(position_in_queue) == 1: # If queue number is only one digit long (1, 2, 3, etc), use two digits instead (01, 02, 03, etc).
				position_in_queue = '0' + position_in_queue
			# Append information generated above to the html-code.
			html_code_part_2.append(position_in_queue + ': &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ' + str(filename + '<br>'))
		
		# Create the next static part of html-code.		
		html_code_part_3 = ['</font></p>', \
		'</td>', \
		'</tr>', \
		'</tbody>', \
		'</table>', \
		'<br>', \
		'</font>', \
		'</font>', \
		'<h2><font color="#000000">' + 'Completed Files' * english + 'K&auml;sitellyt tiedostot' * finnish + '</font></font></h2>', \
		'<hr style="width: 100%; height: 2px;"><font color="#000000"><br>']
		
		# Generate the list of files that has gone through loudness calculation and insert names in the html-code.
		for filename in completed_files_list:
			# Append information generated above to the html-code.
			completion_time = completed_files_dict[filename]
			filename = filename.replace('ä', '&auml;').replace('Ä', '&Auml;').replace('ö', '&ouml;').replace('Ö', '&Ouml;').replace('å', '&aring;').replace('Å', '&Aring;') # Special Finnish characters in filename won't print correctly unless they are replaced with proper html-codes.
			html_code_part_3.append(completion_time + ':&nbsp;&nbsp;&nbsp;' + str(filename + '<br>'))
		
		# Create the last static part of html-code.		
		html_code_part_4 = ['<br>', \
		'<br>', \
		'</font>', \
		'</font>', \
		'</body></html>']

		# Combine all parts of html code to a complete web-page
		html_code.extend(html_code_part_1)
		html_code.extend(html_code_part_2)
		html_code.extend(html_code_part_3)
		html_code.extend(html_code_part_4)
		
		# Write complete web-page to disk. First write it to temporary directory and then move to the target directory.
		try:
			with open(web_page_path + os.sep + '.temporary_files' + os.sep + web_page_name, 'wt') as webpage_filehandler:
				for item in html_code:
					webpage_filehandler.write(item + '\n')
				webpage_filehandler.flush() # Flushes written data to os cache
				os.fsync(webpage_filehandler.fileno()) # Flushes os cache to disk
			shutil.move(web_page_path + os.sep + '.temporary_files' + os.sep + web_page_name, web_page_path + os.sep + web_page_name)
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error opening loudness calculation queue html-file for writing ' * english + 'Laskentajonon html-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error opening loudness calculation queue html-file for writing ' * english + 'Laskentajonon html-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
			
def write_to_heartbeat_file_thread():
	
	# This subprocess is started in its own thread and it periodically writes current time to the heartbeat - file.
	# An external program can monitor the heartbeat - file and do something if it stops updating (for example inform the admin or restart this program).
	
	global heartbeat_write_interval
	global web_page_path
	global heartbeat_file_name
	global loudness_correction_program_info_and_timestamps

	while True:

		# Wait user defined number of seconds between writing to the heartbeat file.
		time.sleep(heartbeat_write_interval)
		
		# Write timestamp to the heartbeat file, indicating that we are still alive :)
		# Create the file in temp - directory and then move to the target location.
		try:
			with open(web_page_path + os.sep + '.temporary_files' + os.sep + heartbeat_file_name, 'wb') as heartbeat_commandfile_handler:
				pickle.dump(loudness_correction_program_info_and_timestamps, heartbeat_commandfile_handler)
				heartbeat_commandfile_handler.flush() # Flushes written data to os cache
				os.fsync(heartbeat_commandfile_handler.fileno()) # Flushes os cache to disk
				shutil.move(web_page_path + os.sep + '.temporary_files' + os.sep + heartbeat_file_name, web_page_path + os.sep + heartbeat_file_name)
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error opening HeartBeat commandfile for writing ' * english + 'HeartBeat - tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error opening HeartBeat commandfile for writing ' * english + 'HeartBeat - tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
			
def debug_lists_and_dictionaries():
	
	# This subroutine is used to print out the length and contents of lists and dictionaries this program uses.
	# This subroutine is only used for debugging purposes.
	
	global list_of_growing_files
	global unsupported_ignored_files_dict
	global files_queued_to_loudness_calculation
	global loudness_calculation_queue
	global files_queued_for_deletion
	global completed_files_list
	global error_messages_to_email_later_list
	global finished_processes
	global integrated_loudness_calculation_results
	global silent
	global web_page_path
	global directory_for_error_logs
	debug_messages_path = web_page_path
	debug_messages_file = 'debug_messages-' + str(get_realtime(english, finnish)) + '.txt' # Debug messages filename is 'debug_messages-' + current date + time
	
	while True:
		
		list_printouts = []
		list_printouts.append('###################################################################################################################################################################################')
		list_printouts.append('len(new_hotfolder_filelist_dict)= ' + str(len(new_hotfolder_filelist_dict)) + ' new_hotfolder_filelist_dict = ' + str(new_hotfolder_filelist_dict))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(old_hotfolder_filelist_dict)= ' +  str(len(old_hotfolder_filelist_dict)) + ' old_hotfolder_filelist_dict = ' + str(old_hotfolder_filelist_dict))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(new_results_directory_filelist_dict)= '+  str(len(new_results_directory_filelist_dict)) + ' new_results_directory_filelist_dict = ' + str(new_results_directory_filelist_dict))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(old_results_directory_filelist_dict)= '+  str(len(old_results_directory_filelist_dict)) + ' old_results_directory_filelist_dict = ' + str(old_results_directory_filelist_dict))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(list_of_growing_files)= ' + str(len(list_of_growing_files)) + ' list_of_growing_files = ' + str(list_of_growing_files))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(unsupported_ignored_files_dict)= ' + str(len(unsupported_ignored_files_dict)) + ' unsupported_ignored_files_dict = ' + str(unsupported_ignored_files_dict))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(files_queued_to_loudness_calculation)= ' + str(len(files_queued_to_loudness_calculation)) + ' files_queued_to_loudness_calculation = ' + str(files_queued_to_loudness_calculation))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(loudness_calculation_queue)= ' + str(len(loudness_calculation_queue)) + ' loudness_calculation_queue = ' + str(loudness_calculation_queue))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(files_queued_for_deletion)= ' + str(len(files_queued_for_deletion)) + ' files_queued_for_deletion = ' + str(files_queued_for_deletion))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(completed_files_list)= ' + str(len(completed_files_list)) + ' completed_files_list = ' + str(completed_files_list))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(completed_files_dict)= ' + str(len(completed_files_dict)) + ' completed_files_dict = ' + str(completed_files_dict))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(error_messages_to_email_later_list)= ' + str(len(error_messages_to_email_later_list)) + ' error_messages_to_email_later_list = ' + str(error_messages_to_email_later_list))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(finished_processes)= ' + str(len(finished_processes)) + ' finished_processes = ' + str(finished_processes))
		list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
		list_printouts.append('len(integrated_loudness_calculation_results)= ' + str(len(integrated_loudness_calculation_results)) + ' integrated_loudness_calculation_results = ' + str(integrated_loudness_calculation_results))
		list_printouts.append('###################################################################################################################################################################################')
		
		# Print list_printouts to screen
		if not silent == True:
			for item in list_printouts:
				print(item)
		
		# Print list_printouts to disk. First write it to temporary directory and then move to the target directory.
		try:
			# Move debug_log - file to the temp directory so we can append new messages to it.
			if os.path.exists(directory_for_error_logs + os.sep + debug_messages_file):
				shutil.move(directory_for_error_logs + os.sep + debug_messages_file, directory_for_temporary_files + os.sep + debug_messages_file)
			with open(directory_for_temporary_files + os.sep + debug_messages_file, 'at') as debug_messages_filehandler:
				for item in list_printouts:
					debug_messages_filehandler.write(item + '\n')
				debug_messages_filehandler.flush() # Flushes written data to os cache
				os.fsync(debug_messages_filehandler.fileno()) # Flushes os cache to disk
			shutil.move(directory_for_temporary_files + os.sep + debug_messages_file, directory_for_error_logs + os.sep + debug_messages_file)
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error opening debug-messages file for writing ' * english + 'Debug-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error opening debug-messages file for writing ' * english + 'Debug-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])

		# Sleep between writing output
		time.sleep(60)

def debug_variables_read_from_configfile():

	if all_settings_dict != {}:
		# Print variables read from the configfile. This is useful for debugging settings previously saved in a file.
		global language
		global english
		global finnish
		global target_path
		global hotfolder_path
		global directory_for_temporary_files
		global directory_for_results
		global libebur128_path
		global delay_between_directory_reads
		global number_of_processor_cores
		global file_expiry_time
		global natively_supported_file_formats
		global ffmpeg_output_format
		global silent
		global write_html_progress_report
		global html_progress_report_write_interval
		global web_page_name
		global web_page_path
		global heartbeat
		global heartbeat_file_name
		global heartbeat_write_interval
		global where_to_send_error_messages
		global send_error_messages_to_logfile
		global directory_for_error_logs
		global send_error_messages_by_email
		global email_sending_details
		
		title_text = '\nLocal variable values after reading the configfile: ' + configfile_path + ' are:'
		print(title_text)
		print((len(title_text) + 1) * '-' + '\n') # Print a line exactly the length of the title text line + 1.
		
		print('language =', language)
		print('english =', english)
		print('finnish =', finnish)
		print()	
		print('target_path =', target_path)
		print('hotfolder_path =', hotfolder_path)
		print('directory_for_temporary_files =', directory_for_temporary_files)
		print('directory_for_results =', directory_for_results)
		print('libebur128_path =', libebur128_path)
		print()
		print('delay_between_directory_reads =', delay_between_directory_reads)	
		print('number_of_processor_cores =', number_of_processor_cores)
		print('file_expiry_time =', file_expiry_time)
		print()
		print('natively_supported_file_formats =', natively_supported_file_formats)
		print('ffmpeg_output_format =', ffmpeg_output_format)
		print('peak_measurement_method =', all_settings_dict['peak_measurement_method'])
		print()	
		print('silent =', silent)
		print()	
		print('write_html_progress_report =', write_html_progress_report)
		print('html_progress_report_write_interval =', html_progress_report_write_interval)
		print('web_page_name =', web_page_name)
		print('web_page_path =', web_page_path)
		print()
		print('heartbeat =', heartbeat)
		print('heartbeat_file_name =', heartbeat_file_name)
		print('heartbeat_write_interval =', heartbeat_write_interval)
		print()
		print('where_to_send_error_messages =', where_to_send_error_messages)
		print('send_error_messages_to_logfile =', send_error_messages_to_logfile)
		print('directory_for_error_logs =', directory_for_error_logs)
		print('error_logfile_path =', error_logfile_path)
		print()
		print('send_error_messages_by_email =', send_error_messages_by_email)
		print('email_sending_details =', email_sending_details)
		print()

def get_ip_addresses_of_the_host_machine():
	
	global all_ip_addresses_of_the_machine
	global directory_for_temporary_files
	
	# Create the commandline we need to run as root.
	commands_to_run = ['hostname', '-I']

	if debug == True:
		print()
		print('Running commands:', commands_to_run)
	
	try:
		# Define filenames for temporary files that we are going to use as stdout and stderr for the external command.
		stdout_for_external_command = directory_for_temporary_files + os.sep + 'Hostname_command_stdout.txt'
		stderr_for_external_command = directory_for_temporary_files + os.sep + 'Hostname_command_stderr.txt'
				
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
		error_message = 'Error writing to stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error writing to stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Open files we used as stdout and stderr for the external program and read in what the program did output to those files.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler, open(stderr_for_external_command, 'rb') as stderr_commandfile_handler:
			stdout = stdout_commandfile_handler.read(None)
			stderr = stderr_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_message = 'Error reading from stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston lukeminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading from stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon lukeminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	stdout = str(stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	stderr = str(stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# Delete the temporary stdout and stderr - files
	try:
		os.remove(stdout_for_external_command)
		os.remove(stderr_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	all_ip_addresses_of_the_machine = stdout.split()
	
	return(all_ip_addresses_of_the_machine)
	
	if debug == True:
		print()
		print('stdout:', stdout)
		print('stderr:', stderr)
		print('all_ip_addresses_of_the_machine =', all_ip_addresses_of_the_machine)
		
def get_audio_stream_information_with_ffmpeg_and_create_extraction_parameters(filename, hotfolder_path, directory_for_temporary_files, ffmpeg_output_format, english, finnish):
	
	# This subprocess works like this:
	# ---------------------------------
	# The process runs FFmpeg the get information about audio streams in a file.
	# FFmpeg output is then parsed and a FFmpeg commandline created that will later be used to extract all valid audio streams from the file.

	natively_supported_file_format = False # This variable tells if the file format is natively supported by libebur128 and sox. We do not yet know the format of the file, we just set the default here. If format is not natively supported by libebur128 and sox, file will be first extracted to flac with ffmpeg.
	ffmpeg_supported_fileformat = False # This variable tells if the file format is natively supported by ffmpeg. We do not yet know the format of the file, we just set the default here. If format is not supported by ffmpeg, we have no way of processing the file and it will be queued for deletion.
	number_of_ffmpeg_supported_audiostreams = 0 # This variable holds the number of audio streams ffmpeg finds in the file.
	details_of_ffmpeg_supported_audiostreams = [] # Holds ffmpeg produced information about audio streams found in file (example: 'Stream #0.1[0x82]: Audio: ac3, 48000 Hz, 5.1, s16, 384 kb/s' )
	global directory_for_results
	global where_to_send_error_messages
	global debug
	
	audio_duration_string = ''
	audio_duration_fractions_string = ''
	audio_duration_list = []
	audio_duration = 0
	audio_duration_according_to_mediainfo = 0
	audio_duration_rounded_to_seconds = 0
	audio_duration_fractions = 0
	ffmpeg_error_message = ''
	time_slice_duration_string = '3' # Set the default value to use in timeslice loudness calculation.
	file_to_process = hotfolder_path + os.sep + filename
	filename_and_extension = os.path.splitext(filename)
	target_filenames = []
	ffmpeg_stream_mapping_commands = []
	ffmpeg_commandline = []
	bit_depth = 0
	sample_rate = 0
	number_of_audio_channels = '0'
	estimated_uncompressed_size_for_single_mono_file = 0
	estimated_uncompressed_size_for_combined_channels = 0
	global wav_format_maximum_file_size
	file_type = ''
	audio_coding_format = ''
	list_of_error_messages_for_unsupported_streams = []	
	
	try:
		# Define filename for the temporary file that we are going to use as stdout for the external command.
		stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_ffmpeg_find_audio_streams_stdout.txt'
		# Open the stdout temporary file in binary write mode.
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
	
			# Examine the file with ffmpeg and parse its output.
			subprocess.Popen(['ffmpeg', '-i', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run ffmpeg.
	
			# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
			
	except IOError as reason_for_error:
		error_message = 'Error writing to ffmpeg stdout - file ' * english + 'FFmpegin stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error writing to ffmpeg stdout - file ' * english + 'FFmpegin stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	# Open the file we used as stdout for the external program and read in what the external program wrote to it.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
			ffmpeg_run_output = stdout_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_message = 'Error reading from ffmpeg stdout - file ' * english + 'FFmpegin stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading from ffmpeg stdout - file ' * english + 'FFmpegin stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Convert ffmpeg output from binary to UTF-8 text.
	try:
		ffmpeg_run_output_decoded = ffmpeg_run_output.decode('UTF-8') # Convert ffmpeg output from binary to utf-8 text.
	except UnicodeDecodeError:
		# If UTF-8 conversion fails, try conversion with another character map.
		ffmpeg_run_output_decoded = ffmpeg_run_output.decode('ISO-8859-15') # Convert ffmpeg output from binary to text.
		
	ffmpeg_run_output_result_list = str(ffmpeg_run_output_decoded).split('\n') # Split ffmpeg output by linefeeds to a list.
	
	# Delete the temporary stdout - file.
	try:
		os.remove(stdout_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting ffmpeg stdout - file ' * english + 'FFmpegin stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting ffmpeg stdout - file ' * english + 'FFmpegin stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	#############################################################################################
	# Find lines from FFmpeg output that have information about audio streams and file duration #
	# Also record channels count for each stream found                                          #
	#############################################################################################
	
	audio_stream_number = 0
	
	for item in ffmpeg_run_output_result_list:
		
		if 'Audio:' in item: # There is the string 'Audio' for each audio stream that ffmpeg finds. Count how many 'Audio' strings is found and put the strings in a list. The string holds detailed information about the stream and we print it later.
			
			number_of_audio_channels = '0'
			audio_stream_number = audio_stream_number + 1
			
			# Transportstreams can have streams that have 0 audio channels, skip these dummy streams.
			if ('0 channels' in item):
				if not item[item.index('0 channels')-1].isnumeric(): # Check if the character before the string '0 channels' is a number or not. Only skip stream if it has 0 audio channels, but not when it has 10 or 100 :)
					# Create error message to the results graphics file and skip the stream.
					unsupported_stream_name = filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + str(audio_stream_number) + '-ChannelCount-' * english + '-AaniKanavia-' * finnish  + '0'
					error_message = 'There are ' * english + 'Miksauksessa numero ' * finnish + str(audio_stream_number) * finnish + 'zero' * english + ' audio channels in stream number ' * english + ' on nolla äänikanavaa' * finnish + str(audio_stream_number) * english
					list_of_error_messages_for_unsupported_streams.append([unsupported_stream_name, error_message])
					continue
			
			# Create names for audio streams found in the file.
			# First parse the number of audio channels in each stream ffmpeg reported and put it in a variable.
			ffmpeg_stream_info = str(item.strip())
			number_of_audio_channels_as_text = str(ffmpeg_stream_info.split(',')[2].strip()) # FFmpeg reports audio channel count as a string.		
			
			# Split audio channel count to a list ('2 channels' becomes ['2', 'channels']
			number_of_audio_channels_as_text_split_to_a_list = number_of_audio_channels_as_text.split()
			
			# If the first item in the list is an integer bigger that 0 use it as the channel count.
			# If the conversion from string to int raises an error, then the item is not a number, but a string like 'stereo'.
			try:
				if int(number_of_audio_channels_as_text_split_to_a_list[0]) > 0:
					number_of_audio_channels = str(number_of_audio_channels_as_text_split_to_a_list[0])
			except ValueError:
				pass
		
			# FFmpeg sometimes reports some channel counts differently. Test for these cases and convert the channel count to an simple number.
			if number_of_audio_channels_as_text == 'mono':
				number_of_audio_channels = '1'
			if number_of_audio_channels_as_text == 'stereo':
				number_of_audio_channels = '2'
			if number_of_audio_channels_as_text == 'quad':
				number_of_audio_channels = '4'
			if number_of_audio_channels_as_text == '5.1':
				number_of_audio_channels = '6'
			if number_of_audio_channels_as_text == '7.1':
				number_of_audio_channels = '8'
			
			if number_of_audio_channels == '0':
				error_message = 'ERROR !!! I could not parse FFmpeg channel count string: ' * english + 'VIRHE !!! En osannut tulkita ffmpeg:in antamaa tietoa kanavien lukumäärästä: ' * finnish + '\'' + str(number_of_audio_channels_as_text_split_to_a_list[0]) + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
				send_error_messages_to_screen_logfile_email(error_message, [])
			
			# Channel counts bigger than 6 are not supported, get the stream name and error message to a list and skip the stream.
			if int(number_of_audio_channels) > 6:
				
				unsupported_stream_name = filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + str(audio_stream_number) + '-ChannelCount-' * english + '-AaniKanavia-' * finnish  + number_of_audio_channels
				error_message = 'There are ' * english + 'Miksauksessa ' * finnish  + str(audio_stream_number) * finnish + ' on ' * finnish + str(number_of_audio_channels) + ' channels in stream ' * english + str(audio_stream_number) * english + ', only channel counts from one to six are supported' * english + ' äänikanavaa, vain kanavamäärät yhdestä kuuteen ovat tuettuja' * finnish
				list_of_error_messages_for_unsupported_streams.append([unsupported_stream_name, error_message])			
				continue
			
			number_of_ffmpeg_supported_audiostreams = number_of_ffmpeg_supported_audiostreams + 1
			details_of_ffmpeg_supported_audiostreams.append([str(item.strip()), str(audio_stream_number), number_of_audio_channels])
			
		if 'Duration:' in item:
			audio_duration_string = str(item).split(',')[0].strip() # The first item on the line is the duration, get it.
			audio_duration_string = audio_duration_string.split(' ')[1].strip() # Remove the string 'Duration:' that is in front of the time string we want.
			# Check that audio duration is a valid time, if it is 'N/A' then ffmpeg can not extract the audio stream.
			if not 'N/A' in audio_duration_string:
				# Get the file duration as a string and also calculate it in seconds.
				audio_duration_string, audio_duration_fractions_string = audio_duration_string.split('.') # Split the time string to two variables, the last will hold the fractions part (0 - 99 hundreds of a second).
				audio_duration_fractions = int(audio_duration_fractions_string) / 100
				audio_duration_list = audio_duration_string.split(':') # Separate each element in the time string (hours, minutes, seconds) and put them in a list.
				audio_duration_rounded_to_seconds = (int(audio_duration_list[0]) * 60 * 60) + (int(audio_duration_list[1]) * 60) + int(audio_duration_list[2]) # Calculate audio duration in seconds.
				audio_duration = audio_duration_rounded_to_seconds + audio_duration_fractions
			else:
				# The FFmpeg reported audio duration as 'N/A' then this means ffmpeg could not determine the audio duration. Set audio duration to 0 seconds and inform user about the error.
				audio_duration_rounded_to_seconds = 0
				error_message = 'FFmpeg Error : Audio Duration = N/A' * english + 'FFmpeg Virhe: Äänen Kesto = N/A' * finnish + ': ' + filename
				send_error_messages_to_screen_logfile_email(error_message, [])
		if 'Input #0' in item:
			# Get the type of the file, if it is 'mpegts' then we later need to do some tricks to get the correct duration from the file.
			file_type = str(item).split('from')[0].split(',')[1].strip()
		if filename + ':' in item: # Try to recognize some ffmpeg error messages, these always start with the filename + ':'
			ffmpeg_error_message = 'FFmpeg Error : ' * english + 'FFmpeg Virhe: ' * finnish + item.split(':')[1] # Get the reason for error from ffmpeg output.
			
	# Test if file type is mpegts. FFmpeg can not always extract file duration correctly from mpegts so in this case get file duration with the mediainfo - command.
	if file_type == 'mpegts':
		audio_duration_according_to_mediainfo = get_audiofile_duration_with_mediainfo(directory_for_temporary_files, filename, file_to_process, english, finnish)
		if audio_duration_according_to_mediainfo != 0:
			audio_duration = audio_duration_according_to_mediainfo
			audio_duration_rounded_to_seconds = int(audio_duration_according_to_mediainfo)
	
	###################################################################################################
	# Generate the commandline that will later be used to extract all valid audio streams with FFmpeg #
	###################################################################################################
	
	# Go through FFmpeg output that tells about audio streams and find channel counts for each stream #
	
	for counter in range(0, number_of_ffmpeg_supported_audiostreams):
		
		# Get info about supported audio streams and their channel counts from a list.
		ffmpeg_stream_info, audio_stream_number, number_of_audio_channels = details_of_ffmpeg_supported_audiostreams[counter]
		
		# Find audio sample rate from FFmpeg stream info.
		sample_rate_as_text = str(ffmpeg_stream_info.split(',')[1].strip().split(' ')[0].strip())
		
		if sample_rate_as_text.isnumeric() == True:
			sample_rate = int(sample_rate_as_text)
		else:
			error_message = 'ERROR !!! I could not parse FFmpeg sample rate string: ' * english + 'VIRHE !!! En osannut tulkita ffmpeg:in antamaa tietoa näyteenottotaajuuudesta: ' * finnish + '\'' + sample_rate_as_text + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		# Find audio bit depth from FFmpeg stream info output.
		bit_depth_info_field = str(ffmpeg_stream_info.split(',')[3].strip())
		
		for start_character in range(0, len(bit_depth_info_field)):
			if bit_depth_info_field[start_character].isnumeric() == True:
				break
		
		end_character = start_character + 1 # In case 'start_character' already points to the last character of 'bit_depth_info_field', then 'end_character' must be manually assigned because the following for loop won't run.
		
		for end_character in range(start_character + 1, len(bit_depth_info_field)):
			if bit_depth_info_field[end_character].isnumeric() == False:
				break
		
		bit_depth_as_text = bit_depth_info_field[start_character:end_character + 1]		
		
		if bit_depth_as_text.isnumeric() == True:
			bit_depth = int(bit_depth_as_text)
		else:
			error_message = 'ERROR !!! I could not parse FFmpeg bit depth string: ' * english + 'VIRHE !!! En osannut tulkita ffmpeg:in antamaa tietoa bittisyvyydestä: ' * finnish + '\'' + bit_depth_as_text + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		# FFmpeg displays bit depths 24 bits and 32 bits both as 32 bits. Force bit depth to 24 if it is 32.
		if bit_depth == 32:
			bit_depth = 24
		
		# Calculate estimated uncompressed file size. Add one second of data to the file size (sample_rate = 1 second) to be on the safe side.
		estimated_uncompressed_size_for_single_mono_file = int((sample_rate * audio_duration * int(bit_depth / 8)) + sample_rate)
		estimated_uncompressed_size_for_combined_channels = estimated_uncompressed_size_for_single_mono_file * int(number_of_audio_channels)
		
		# Test if output file will exceed the max size of wav format and assign sox commands and output formats accordingly.
		if estimated_uncompressed_size_for_combined_channels < wav_format_maximum_file_size:
			# In this case the output filesize does not exceed the maximum size, so we can use wav.
			ffmpeg_output_format = 'wav'
			
		if (estimated_uncompressed_size_for_combined_channels >= wav_format_maximum_file_size) or (bit_depth == 16):
			# Use lossless flac compression if input file bit depth is 16 bits or if estimated output file size is bigger that wav max 4 GB.
			ffmpeg_output_format = 'flac'
		
		# Assign the inital commandline to the list and decide what output format to use.
		# Demux audio to wav if output file size is below wav max 4 GB limit.
		# Try to preserve bit depth even though FFmpeg bugs makes it a bit difficult.
		# FFmpeg uses always bit depth of 16 when writing flac, so we try to avoid flac if possible.

		if len(ffmpeg_commandline) == 0:
			
			if ffmpeg_output_format == 'flac':
				
				# FFmpeg flac writing always forces bit depth to 16 bits, so we use flac only when we have no choice (ouput file bigger than 4 GB).
				ffmpeg_commandline = ['ffmpeg', '-y', '-i', file_to_process, '-vn', '-acodec', 'flac']
				
			if ffmpeg_output_format == 'wav':
				
				ffmpeg_commandline = ['ffmpeg', '-y', '-i', file_to_process, '-vn', '-acodec', 'pcm_s16le'] # If bit depth is something else than 8 or 24 bits, then always use 16 bits.
				
				if bit_depth == 24:
					ffmpeg_commandline = ['ffmpeg', '-y', '-i', file_to_process, '-vn', '-acodec', 'pcm_s24le']
					
				if bit_depth == 8:
					ffmpeg_commandline = ['ffmpeg', '-y', '-i', file_to_process, '-vn', '-acodec', 'pcm_u8']
					
		# Find audio coding format from FFmpeg output.
		audio_coding_format = str(ffmpeg_stream_info.split('Audio:')[1].split(',')[0].strip())	
		
		if debug == True:
			print()
			print('get_audio_stream_information_with_ffmpeg_and_create_extraction_parameters')
			print('--------------------------------------------------------------------------')
			print('filename =', filename)
			print('file_type =', file_type)
			print('bit_depth =', bit_depth)
			print('sample_rate =', sample_rate)
			print('number_of_audio_channels =', number_of_audio_channels)
			print('estimated_uncompressed_size_for_single_mono_file =', estimated_uncompressed_size_for_single_mono_file)
			print('estimated_uncompressed_size_for_combined_channels =', estimated_uncompressed_size_for_combined_channels)
			print('audio_duration =', audio_duration)
			print('audio_coding_format =', audio_coding_format)
			print('ffmpeg_output_format =', ffmpeg_output_format)
			print()
		
		# Compile the name of the audiostream to an list of all audio stream filenames.
		target_filenames.append(filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + audio_stream_number + '-ChannelCount-' * english + '-AaniKanavia-' * finnish  + number_of_audio_channels + '.' + ffmpeg_output_format)
		
		# Generate FFmpeg extract options for audio stream.
		ffmpeg_commandline.append('-f')
		ffmpeg_commandline.append(ffmpeg_output_format)
		ffmpeg_commandline.append(directory_for_temporary_files + os.sep + target_filenames[counter])
		
		# Find out what is FFmpegs map number for the audio stream.	
		for map_number_counter in range(ffmpeg_stream_info.find('#') + 1, len(ffmpeg_stream_info)):
			if ffmpeg_stream_info[map_number_counter] == '.':
				continue
			if ffmpeg_stream_info[map_number_counter].isnumeric() == False:
				break

		map_number = ffmpeg_stream_info[ffmpeg_stream_info.find('#') + 1:map_number_counter]
		
		# Test if we really have found the stream map number.
		mapnumber_digit_1 = ''
		mapnumber_digit_2 = ''
		map_number_test_list = map_number.split('.')
		
		try:
			mapnumber_digit_1 = map_number_test_list[0]
			mapnumber_digit_2 = map_number_test_list[1]
			
			if (mapnumber_digit_1.isnumeric() == False) or (mapnumber_digit_2.isnumeric() == False):
				error_message = 'Error: stream map number found in FFmpeg output is not a number: ' * english + 'Virhe: FFmpegin tulosteesta löydetty streamin numero ei ole numero: ' * finnish + map_number
				send_error_messages_to_screen_logfile_email(error_message, [])
		except IndexError:
			error_message = 'Error: stream map number found in FFmpeg output is not in correct format: ' * english + 'Virhe: FFmpegin tulosteesta löydetty streamin numero ei ole oikeassa formaatissa: ' * finnish + map_number
			send_error_messages_to_screen_logfile_email(error_message, [])
	
		# Create a audio stream mapping command list that will be appended at the end of ffmpeg commandline. Without this the streams would be extracted in random order and our stream numbers wouldn't match the streams.
		ffmpeg_stream_mapping_commands.extend(['-map',  str(map_number) + ':0.' + str(counter)])
	
	# Complete the FFmpeg commandline by adding stream mapping commands at the end of it. The commandline is later used to extract all valid audio streams from the file.
	ffmpeg_commandline.extend(ffmpeg_stream_mapping_commands)
	
	if number_of_ffmpeg_supported_audiostreams >= 1:
		ffmpeg_supported_fileformat = True
	else:
		ffmpeg_supported_fileformat = False
	
	# If there were supported and unsupported streams in the file then print error messages we gathered for the unsupported streams earlier.
	if (ffmpeg_supported_fileformat == True) and (len(list_of_error_messages_for_unsupported_streams) > 0):
		
		for unsupported_stream_name, error_message in list_of_error_messages_for_unsupported_streams:
			
			# This error message is not very important so don't send it by email, only send it to other possible destinations (screen, logfile).
			error_message_destinations = copy.deepcopy(where_to_send_error_messages)
			if 'email' in error_message_destinations:
				error_message_destinations.remove('email')
			send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, error_message_destinations)
			
			# Create the result graphics file with an error message telling stream is not supported.
			create_gnuplot_commands_for_error_message(error_message, unsupported_stream_name, directory_for_temporary_files, directory_for_results, english, finnish)
			
	# If there are only unsupported audio streams in the file then assign an error message that gets printed on the results graphics file.
	# Currently the only known unsupported streams in a file are streams with channel counts of zero and more than 6 channels.
	send_ffmpeg_error_message_by_email = True
	if (ffmpeg_supported_fileformat == False) and (len(list_of_error_messages_for_unsupported_streams) > 0):
		ffmpeg_error_message = 'Audio streams in file are unsupported, only channel counts from 1 to 6 are supported' * english + 'Tiedoston miksaukset eivät ole tuetussa formaatissa, vain kanavamäärät välillä 1 ja 6 ovat tuettuja' * finnish
		send_ffmpeg_error_message_by_email = False
		
	# In case the file has only 1 audio stream and the format is ogg then do an additional check.
	# Sox only supports ogg files that have max 2 channels. If there are more then the audio must be converted to another format before processing.
	# 'natively_supported_file_format = False'  means audio must be converted with FFmpeg before prosessing.
	if number_of_ffmpeg_supported_audiostreams > 0: # If ffmpeg found audio streams check if the file extension is one that sox supported (wav, flac, ogg).
		if str(os.path.splitext(filename)[1]).lower() in natively_supported_file_formats:
			natively_supported_file_format = True
			
	if (number_of_ffmpeg_supported_audiostreams == 1) and (str(os.path.splitext(filename)[1]).lower() == '.ogg'): # Test if ogg - file has more than two channels, since sox only supports mono and stereo ogg - files. If there are more channels, audio must be converted before processing.
		if  (number_of_audio_channels != '1') and (number_of_audio_channels != '2'):
			natively_supported_file_format = False
	
	if (number_of_ffmpeg_supported_audiostreams > 1) and (str(os.path.splitext(filename)[1]).lower() == '.ogg'):
		# If there are more than 1 streams in ogg then extract streams with FFmpeg.
		natively_supported_file_format = False
	
	if (str(os.path.splitext(filename)[1]).lower() == '.wav') and (audio_coding_format not in ['pcm_u8', 'pcm_s16le', 'pcm_s24le', 'pcm_s32le']):
		# Wav container might contain other data than uncompressed pcm, if this is the case then first decompress audio / convert streams with FFmpeg.
		natively_supported_file_format = False
	
	file_format_support_information = [natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames]	
	
	if debug == True:
		print('ffmpeg_commandline =', ffmpeg_commandline) 
	
	return(file_format_support_information, ffmpeg_error_message, send_ffmpeg_error_message_by_email)
	
def get_audiofile_duration_with_mediainfo(directory_for_temporary_files, filename, file_to_process, english, finnish):
	
	audio_duration_string = ''
	audio_duration_fractions_string =''
	audio_duration_list = []
	audio_duration_rounded_to_seconds = 0
	audio_duration_fractions = 0
	audio_duration = 0
	global debug
	
	mediainfo_output = ''
	mediainfo_output_decoded = ''
	mediainfo_output
	
	try:
		# Define filename for the temporary file that we are going to use as stdout for the external command.
		stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_ffmpeg_find_audio_streams_stdout.txt'
		# Open the stdout temporary file in binary write mode.
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
	
			# Examine the file with ffmpeg and parse its output.
			subprocess.Popen(['mediainfo', '--Inform=General;%Duration/String3%', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run mediainfo.
	
			# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
			
	except IOError as reason_for_error:
		error_message = 'Error writing to mediainfo stdout - file ' * english + 'Mediainfon stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error writing to mediainfo stdout - file ' * english + 'Mediainfon stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	# Open the file we used as stdout for the external program and read in what the external program wrote to it.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
			mediainfo_output = stdout_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_message = 'Error reading from mediainfo stdout - file ' * english + 'Mediainfon stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading from mediainfo stdout - file ' * english + 'Mediainfon stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Convert ffmpeg output from binary to UTF-8 text.
	try:
		mediainfo_output_decoded = mediainfo_output.decode('UTF-8') # Convert ffmpeg output from binary to utf-8 text.
	except UnicodeDecodeError:
		# If UTF-8 conversion fails, try conversion with another character map.
		mediainfo_output_decoded = mediainfo_output.decode('ISO-8859-15') # Convert ffmpeg output from binary to text.
	
	if debug == True:
		print()
		print("Mediainfo says '" + filename + "' duration is:", mediainfo_output)
		print()		
		
	# Get the file duration as a string and also calculate it in seconds.
	if (mediainfo_output_decoded.strip() != '') and ('-' not in mediainfo_output_decoded):
		audio_duration_string, audio_duration_fractions_string = mediainfo_output_decoded.split('.') # Split the time string to two variables, the last will hold the fractions part (0 - 999 hundreds of a second).
		audio_duration_fractions = int(audio_duration_fractions_string) / 1000
		audio_duration_list = audio_duration_string.split(':') # Separate each element in the time string (hours, minutes, seconds) and put them in a list.
		audio_duration_rounded_to_seconds = (int(audio_duration_list[0]) * 60 * 60) + (int(audio_duration_list[1]) * 60) + int(audio_duration_list[2]) # Calculate audio duration in seconds.
		audio_duration = audio_duration_rounded_to_seconds + audio_duration_fractions
		
	# Delete the temporary stdout - file.
	try:
		os.remove(stdout_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting mediainfo stdout - file ' * english + 'Mediainfon stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting mediainfo stdout - file ' * english + 'Mediainfon stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	return(audio_duration)
	
	
def debug_write_loudness_calculation_info_to_a_logfile(filename, integrated_loudness, loudness_range, highest_peak_db, channel_count, sample_rate, bit_depth, audio_duration):
	
	# This subroutine can be used to write loudness calculation data to a text file in error_log - directory.
	# The developer can process a bunch of test files and save the logfile.
	# When changes are made to critical parts of the program or external helper programs then it can be
	# confirmed that the results from the new version are the same as in the earlier saved file.
	
	global loudness_calculation_logfile_path
	loudness_calculation_data = filename + ',EndOFFileName,' + str(integrated_loudness) + ',' + str(loudness_range) + ',' + str(highest_peak_db) + ',' + str(channel_count) + ',' + str(sample_rate) + ',' + str(bit_depth) + ',' + str(int(audio_duration)) + '\n'
	
	try:
		with open(loudness_calculation_logfile_path, 'at') as loudness_calculation_logfile_handler:
			loudness_calculation_logfile_handler.write(loudness_calculation_data)
			loudness_calculation_logfile_handler.flush() # Flushes written data to os cache
			os.fsync(loudness_calculation_logfile_handler.fileno()) # Flushes os cache to disk
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error opening loudness calculation logfile for writing ' * english + 'Äänekkyyslogitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error opening loudness calculation logfile for writing ' * english + 'Äänekkyyslogitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
			
			

##############################################################################################
#                                The main program starts here:)                              #
##############################################################################################
#
# Start the program by giving full path to the target directory.
# The program creates directories in the target, the most important ones are: '00-LoudnessCorrection', '00-LoudnessCorrection/00-Corrected_Files'.
# The program polls the '00-LoudnessCorrection' directory periodically, by default every 5 seconds.
# The program uses various dictionaries and lists for keeping track of files going through different stages of processing. The most importand variables are:
#       'number_of_processor_cores'
# The value in this variable divided by two defines how many files we can process simultaneously.
# Two processes in separate threads are started simultaneously for each file. The first calculates integrated loudness and loudness range. The second process calculates loudness by segmenting the file to time slices and calculates loudness of each slice individually. Slice duration is 0.5 secs for files 9 secs or shorter and 3 secs for files 10 seconds or longer.
# Timeslice loudness values are later used for plotting loudness graphics.
#       'new_hotfolder_filelist_dict' and 'old_hotfolder_filelist_dict'
# These dictionaries are used to keep track of files that appear to the HotFolder and the time the files were first seen there.
# This time is used to determine when files have expired and can been deleted. (Expiration time (seconds) is stored in variable 'file_expiry_time' and is 8 hours by default).
#       'list_of_growing_files'
# This list is used to keep track of files that are being transferred to the HotFolder but are not yet complete (file size is growing between directory polls).
#       'files_queued_to_loudness_calculation'
# This list holds the names of files in the HotFolder that are no longer growing and can be sent to loudness calculation.
#        'loudness_calculation_queue'
# This list holds the names of files that are currently being calculated upon.
#       'files_queued_for_deletion'
# This list holds the names of files that are going to be deleted.
#		'completed_files_list'
# 		'completed_files_dict'
# The list holds the names of 100 last files that has gone through loudness calculation, and the order processing them was completed. The dictionary holds the time processing each file was completed. The list and dictionary are only used when printing loudness calculation progress information to a web page on disk.
#
# The main procedure works like this:
# ------------------------------------
# - Read 'HotFolder' and get filenames, then check against previous directory read to see if new files have appeared.
# - If there are new files then start monitoring if their size changes between directory polls. Also record the time the file was first seen in the HotFolder.
# - Check if files have stayed longer in the HotFolder and Results Folder than the expiry time. Delete all files expired.
# - When a file stops growing, check if ffmpeg can find any audiostreams in the file. If not create a graphics file telling the user about the error, otherwise record the number of streams found.
# - Check if file format is natively supported by libebur128 and sox shipped with Ubuntu (wav, flac, ogg).
# - If format is not natively supported extract audiostreams (max 8) from the file with ffmpeg to flac and move the resulting files to HotFolder and delete the original file.
# - Check to see if there is already the maximum allowed number of loudness calculations going on. If two free processor cores are available then start calculating the next file.
# - The loudnes calculation, graphics plotting and creation of loudness corrected wavs is handled by subroutines, their operation is documented in their comments.

new_hotfolder_filelist_dict={} # See explanation of the purpose for this dictionary in comments above.
old_hotfolder_filelist_dict={} # See explanation of the purpose for this dictionary in comments above.
new_results_directory_filelist_dict={}
old_results_directory_filelist_dict={}
finished_processes=[]
path=''
filename = ''
list_of_directories=[]
list_of_files=[]
list_of_growing_files=[] # See explanation of the purpose for this dictionary in comments above.
files_queued_to_loudness_calculation=[] # See explanation of the purpose for this dictionary in comments above.
files_queued_for_deletion=[] # See explanation of the purpose for this dictionary in comments above.
completed_files_list = [] # This variable holds the names of 100 last files that have gone through loudness calculation.
completed_files_dict = {} # This dictionary stores the time processing each file was completed.
adjust_line_printout='         '
loudness_calculation_queue={} # See explanation of the purpose for this dictionary in comments above.
loop_counter=0
integrated_loudness_calculation_results = {}
previous_value_of_files_queued_to_loudness_calculation = 0 # This variable is used to track if the number of files in the calculation queue changes. A message is printed when it does.
previous_value_of_loudness_calculation_queue = 0 # This variable is used to track if the number of files being in the calculation process changes. A message is printed when it does.
error_messages_to_email_later_list = [] # Error messages are collected to this list for sending them by email.
unsupported_ignored_files_dict = {} # This dictionary holds the names of files that have no audiostreams we can read with ffmpeg, or has audiostreams, but the duration is less than 1 second. Files in this list will be ignored and not processed. The time the file was first seen in the HotFolder is also recorded with the filename.
html_progress_report_counter = 0 # This variable is used to count the seconds between writing loudness calculation queue information to a html - page on disk
loudness_correction_pid = os.getpid() # Get the PID of this program.
all_ip_addresses_of_the_machine = [] # This variable stores in a list all IP-Addresses this machine has. This info is inserted into error emails.


###############################################################################################################################################################################
# Read user defined configuration variables from a file                                                                                                                       #
###############################################################################################################################################################################

# If there is a value in the variable 'configfile_path' then it is a valid path to a readable configfile.
# If the variable is empty, use the default values for variables defined in the beginning of this script.

all_settings_dict = {}

if configfile_path != '':
	
	# Read the config variables from a file. The file contains a dictionary with the needed values.
	
	try:
		with open(configfile_path, 'rb') as configfile_handler:
			all_settings_dict = pickle.load(configfile_handler)
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading configfile: ' * english + 'Asetustiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		sys.exit(1)
	except OSError as reason_for_error:
		error_message = 'Error reading configfile: ' * english + 'Asetustiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		sys.exit(1)
	except EOFError as reason_for_error:
		error_message = 'Error reading configfile: ' * english + 'Asetustiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		sys.exit(1)

	# Configfile was read successfully, assign values from it to our variables overriding script defaults defined in the start of this script.
	if 'language' in all_settings_dict:
		language = all_settings_dict['language']
	if 'english' in all_settings_dict:
		english = all_settings_dict['english']
	if 'finnish' in all_settings_dict:
		finnish = all_settings_dict['finnish']
		
	if 'target_path' in all_settings_dict:
		target_path = all_settings_dict['target_path']
	if 'hotfolder_path' in all_settings_dict:
		hotfolder_path = all_settings_dict['hotfolder_path']
	if 'directory_for_temporary_files' in all_settings_dict:
		directory_for_temporary_files = all_settings_dict['directory_for_temporary_files']
	if 'directory_for_results' in all_settings_dict:
		directory_for_results = all_settings_dict['directory_for_results']
	if 'libebur128_path' in all_settings_dict:
		libebur128_path = all_settings_dict['libebur128_path']
	if 'mediainfo_path' in all_settings_dict:
		mediainfo_path = all_settings_dict['mediainfo_path']

	if 'delay_between_directory_reads' in all_settings_dict:
		delay_between_directory_reads = all_settings_dict['delay_between_directory_reads']		
	if 'number_of_processor_cores' in all_settings_dict:
		number_of_processor_cores = all_settings_dict['number_of_processor_cores']
	if 'file_expiry_time' in all_settings_dict:
		file_expiry_time = all_settings_dict['file_expiry_time']

	if 'natively_supported_file_formats' in all_settings_dict:
		natively_supported_file_formats = all_settings_dict['natively_supported_file_formats']
	if 'ffmpeg_output_format' in all_settings_dict:
		if all_settings_dict['ffmpeg_output_format'] != '': # If installer.py did not define a value for the variable, then don't assing anything to it here. The variable has a default value defined elsewhere in LoudnessCorrection.py, the default gets used if not defined here.
			ffmpeg_output_format = all_settings_dict['ffmpeg_output_format']
		
	if 'silent' in all_settings_dict:
		silent = all_settings_dict['silent']
		
	if 'write_html_progress_report' in all_settings_dict:
		write_html_progress_report = all_settings_dict['write_html_progress_report']
	if 'html_progress_report_write_interval' in all_settings_dict:
		html_progress_report_write_interval = all_settings_dict['html_progress_report_write_interval']
	if 'web_page_name' in all_settings_dict:
		web_page_name = all_settings_dict['web_page_name']
	if 'web_page_path' in all_settings_dict:
		web_page_path = all_settings_dict['web_page_path']

	if 'heartbeat' in all_settings_dict:
		heartbeat = all_settings_dict['heartbeat']	
	if 'heartbeat_file_name' in all_settings_dict:
		heartbeat_file_name = all_settings_dict['heartbeat_file_name']
	if 'heartbeat_write_interval' in all_settings_dict:
		heartbeat_write_interval = all_settings_dict['heartbeat_write_interval']
	
	if 'send_error_messages_by_email' in all_settings_dict:
		send_error_messages_by_email = all_settings_dict['send_error_messages_by_email']
	if 'email_sending_details' in all_settings_dict:
		email_sending_details = all_settings_dict['email_sending_details']
		
	if 'where_to_send_error_messages' in all_settings_dict:
		where_to_send_error_messages = all_settings_dict['where_to_send_error_messages']
	if 'send_error_messages_to_logfile' in all_settings_dict:
		send_error_messages_to_logfile = all_settings_dict['send_error_messages_to_logfile']
	if 'directory_for_error_logs' in all_settings_dict:
		directory_for_error_logs = all_settings_dict['directory_for_error_logs']
	if 'peak_measurement_method' in all_settings_dict:
		peak_measurement_method = all_settings_dict['peak_measurement_method']
	

# Test if the user given target path exists.
if (not os.path.exists(target_path)):
	print('\n!!!!!!! Directory' * english + '\n!!!!!!! Hakemistoa' * finnish , target_path, 'does not exist !!!!!!!\n' * english + 'ei ole olemassa !!!!!!!\n' * finnish)
	sys.exit(1)
# There needs to be a couple of directories in the target path, if they do not exist create them.
if (not os.path.exists(hotfolder_path)):
	os.makedirs(hotfolder_path)
	if silent == False:
		print('Created directory' * english + 'Loin hakemiston' * finnish, str(hotfolder_path))
if (not os.path.exists(directory_for_temporary_files)):
	os.makedirs(directory_for_temporary_files)
	if silent == False:
		print('Created directory' * english + 'Loin hakemiston' * finnish, str(directory_for_temporary_files))
if (not os.path.exists(directory_for_results)):
	os.makedirs(directory_for_results)
	if silent == False:
		print('Created directory' * english + 'Loin hakemiston' * finnish, str(directory_for_results))
if (not os.path.exists(directory_for_error_logs)):
	os.makedirs(directory_for_error_logs)
	if silent == False:
		print('Created directory' * english + 'Loin hakemiston' * finnish, str(directory_for_error_logs))
if (not os.path.exists(web_page_path)):
	if ((write_html_progress_report == True)) or (heartbeat == True):
		os.makedirs(web_page_path)
		if silent == False:
			print('Created directory' * english + 'Loin hakemiston' * finnish, str(web_page_path))
if (not os.path.exists(web_page_path + os.sep + '.temporary_files')):
	if ((write_html_progress_report == True)) or (heartbeat == True):
		os.makedirs(web_page_path + os.sep + '.temporary_files')
		if silent == False:
			print('Created directory' * english + 'Loin hakemiston' * finnish, str(web_page_path + os.sep + '.temporary_files'))

# Test that programs gnuplot, sox, ffmpeg, mediainfo and libebur128 loudness-executable can be found in the path and that they have executable permissions on.
gnuplot_executable_found = False
sox_executable_found = False
ffmpeg_executable_found = False
mediainfo_executable_found = False
libebur128_loudness_executable_found = False
libebur128_path = '/usr/bin/loudness'
os_environment_list = os.environ["PATH"].split(os.pathsep)
for os_path in os_environment_list:
	
	gnuplot_true_or_false = os.path.exists(os_path + os.sep + 'gnuplot') and os.access(os_path + os.sep + 'gnuplot', os.X_OK) # True if gnuplot can be found in the path and it has executable permissions on.
	if gnuplot_true_or_false == True:
		gnuplot_executable_found = True
		
	sox_true_or_false = os.path.exists(os_path + os.sep + 'sox') and os.access(os_path + os.sep + 'sox', os.X_OK)
	if sox_true_or_false == True:
		sox_executable_found = True
		
	ffmpeg_true_or_false = os.path.exists(os_path + os.sep + 'ffmpeg') and os.access(os_path + os.sep + 'ffmpeg', os.X_OK)
	if ffmpeg_true_or_false == True:
		ffmpeg_executable_found = True
		
	mediainfo_true_or_false = os.path.exists(os_path + os.sep + 'mediainfo') and os.access(os_path + os.sep + 'mediainfo', os.X_OK)
	if mediainfo_true_or_false == True:
		mediainfo_executable_found = True
		
	libebur128_loudness_executable_true_or_false = os.path.exists(os_path + os.sep + 'loudness') and os.access(os_path + os.sep + 'loudness', os.X_OK)
	if libebur128_loudness_executable_true_or_false == True:
		libebur128_loudness_executable_found = True
		libebur128_path = os_path + os.sep + 'loudness'
	
if gnuplot_executable_found == False:
	print('\n!!!!!!! gnuplot - can not be found or it does not have \'executable\' permissions on !!!!!!!' * english + '\n!!!!!!! gnuplot - ohjelmaa ei löydy tai sillä ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!' * finnish)
	sys.exit(1)
if sox_executable_found == False:
	print('\n!!!!!!! sox - can not be found or it does not have \'executable\' permissions on !!!!!!!' * english + '\n!!!!!!! gnuplot - ohjelmaa ei löydy tai sillä ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!' * finnish)
	sys.exit(1)
if ffmpeg_executable_found == False:
	print('\n!!!!!!! ffmpeg - can not be found or it does not have \'executable\' permissions on !!!!!!!' * english + '\n!!!!!!! ffmpeg - ohjelmaa ei löydy tai sillä ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!' * finnish)
	sys.exit(1)
if mediainfo_executable_found == False:
	print('\n!!!!!!! mediainfo - can not be found or it does not have \'executable\' permissions on !!!!!!!' * english + '\n!!!!!!! mediainfo - ohjelmaa ei löydy tai sillä ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!' * finnish)
	sys.exit(1)
	
# Check if libebur128 loudness-executable can be found.
if (not os.path.exists(libebur128_path)):
	print('\n!!!!!!! libebur128 loudness-executable can\'t be found in path or directory' * english + '\n!!!!!!! libebur128:n loudness-ohjelmaa ei löydy polusta eikä määritellystä hakemistosta' * finnish, libebur128_path, '!!!!!!!\n')
	sys.exit(1)
else:
	# Test that libebur128n loudness-executable has executable permissions on.
	if (not os.access(libebur128_path, os.X_OK)):
		print('\n!!!!!!! libebur128 loudness-executable does not have \'executable\' permissions on !!!!!!!\n' * english + '\n!!!!!!! libebur128:n loudness-ohjelmalla ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!\n' * finnish)
		sys.exit(1)

# If you wan't to enable debug mode to see debug messages printed on the terminal window, then uncomment the line below.
# debug = True

# Define the name of the error logfile.
error_logfile_path = directory_for_error_logs + os.sep + 'error_log-' + str(get_realtime(english, finnish)) + '.txt' # Error log filename is 'error_log' + current date + time

# Define the name of the loudness calculation logfile.
if debug == True:
	loudness_calculation_logfile_path = directory_for_error_logs + os.sep + 'loudness_calculation_log-' + str(get_realtime(english, finnish)) + '.txt'

# Get IP-Addresses of the machine.
all_ip_addresses_of_the_machine = get_ip_addresses_of_the_host_machine()

# The dictionary 'loudness_correction_program_info_and_timestamps' is used to send information to the HeartBeat_Checker - program that is run indipendently of the LoudnessCorrection - script.
# Some threads in LoudnessCorrection write periodically a timestamp to this dictionary indicating they are still alive. 
# The dictionary gets written to disk periodically and the HeartBeat_Checker - program checks that the timestamps in it keeps changing and sends email to the user if they stop.
# The commandline used to start LoudnessCorrection - script and the PID it is currently running on is also recorded in this dictionary. This infomation may be used
# in the future to automatically kill and start again LoudnessCorrection if some of it's threads have crashed, but that is not implemented yet.
#
# Keys 'main_thread' and 'write_html_progress_report' have a list of two values. The first one (True / False) tells if user enabled the feature or not. For example if user does not wan't
# LoudnessCorrection to write a html - page to disk, he set the variable 'write_html_progress_report' to False and this value is also sent to HeartBeat_Checker so that it knows the
# Html - thread won't be updating it's timestamp.

loudness_correction_program_info_and_timestamps = {'loudnesscorrection_program_info' : [sys.argv, loudness_correction_pid, all_ip_addresses_of_the_machine, version], 'main_thread' : [True, 0], 'write_html_progress_report' : [write_html_progress_report, 0]}

# Start in its own thread the subroutine that sends error messages by email.
if email_sending_details['send_error_messages_by_email'] == True:
	email_process = threading.Thread(target=send_error_messages_by_email_thread, args=(email_sending_details, english, finnish)) # Create a process instance.
	thread_object = email_process.start() # Start the process in it'own thread.
	
# Start in its own thread the subroutine that writes process queue information to a web-page on disk periodically.
if write_html_progress_report == True:
	html_writing_process = threading.Thread(target=write_html_progress_report_thread, args=(english, finnish)) # Create a process instance.
	thread_object = html_writing_process.start() # Start the process in it'own thread.

# Start in its own thread the subroutine that writes current time periodically to the HeartBeat-file indicating that we are still alive and running :)
if heartbeat == True:
	heartbeat_process = threading.Thread(target=write_to_heartbeat_file_thread, args=()) # Create a process instance.
	thread_object = heartbeat_process.start() # Start the process in it'own thread.

# If degub = True the script will print out the contents of main lists and dictionaries once a minute.
if debug == True:
	debug_lists_process = threading.Thread(target=debug_lists_and_dictionaries, args=()) # Create a process instance.
	thread_object = debug_lists_process.start() # Start the process in it'own thread.

# If degub = True the script will print out variable values read from the configfile.
if debug == True:
	debug_variables_read_from_configfile()
	
# Print version information to screen
if silent == False:
	print()
	version_string_to_print = 'LoudnessCorrection version ' + version
	print(version_string_to_print)
	print('-' * (len(version_string_to_print) + 1))
	print()


#############################
# The main loop starts here #
#############################

while True:
	
	loudness_correction_program_info_and_timestamps['main_thread'] = [True, int(time.time())] # Update the heartbeat timestamp for the main thread. This is used to keep track if the main thread has crashed.
	loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'] = [sys.argv, loudness_correction_pid, all_ip_addresses_of_the_machine, version]
	
	try:
		# Get directory listing for HotFolder. The 'break' statement stops the for - statement from recursing into subdirectories.
		for path, list_of_directories, list_of_files in os.walk(hotfolder_path):
			break
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading HotFolder directory listing ' * english + 'Lähdehakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading HotFolder directory listing ' * english + 'Lähdehakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	# The files in 'unsupported_ignored_files_dict' are files that ffmpeg was not able to find any audiostreams from, or streams were found but the duration is less than 1 second.
	# Check if files in the unsupported files dictionary have vanished from the HotFolder. If a name has disappeared from HotFolder, remove it also from the list of unsupported files.
	# Check if files in the unsupported files dictionary have been there longer than the expiry time allows, queue expired files for deletion.
	unsupported_ignored_files_list = list(unsupported_ignored_files_dict) # Copy filesnames from dictionary to a list to use as for - loop iterable, since we can't use the dictionary directly because we are going to delete values from it. The for loop - iterable is forbidden to change.
	for filename in unsupported_ignored_files_list:
		if not filename in list_of_files:
			unsupported_ignored_files_dict.pop(filename) # If unsupported file that previously was in HotFolder has vanished, remove its name from the unsupported files list.
			continue
		if int(time.time()) - unsupported_ignored_files_dict[filename] >= file_expiry_time: # If file has expired then queue it for deletion.
			files_queued_for_deletion.append(filename)
	# If user has deleted a file that did already make it to the 'list_of_growing_files' remove it from list.
	for filename in list_of_growing_files:
		if not filename in list_of_files:
			list_of_growing_files.remove(filename) # If file that previously was in HotFolder has vanished, remove its name from the list_of_growing_files.
			continue
	
	# Process filenames found in the directory
	try:
		for filename in list_of_files:
			if filename.startswith('.'): # If filename starts with an '.' queue the file for deletion and continue to process next filename.
				files_queued_for_deletion.append(filename)
				continue
			file_metadata=os.lstat(hotfolder_path + os.sep + filename) # Get file information (size, date, etc)
			file_information_to_save=[file_metadata.st_size, int(time.time()), file_metadata.st_mtime] # Put in a list: file size, time the file was first seen in HotFolder and file modification time.

			##########################################################################################################################################
			# Que expired files in HotFolder for deletion. Make sure no other thread is currently processing the files before queueing for deletion. #
			##########################################################################################################################################
			# Test if the time between now and the time the file was first seen in HotFolder is longer that expiry time, if true queue file for deletion.
			if (filename in old_hotfolder_filelist_dict) and (int(time.time()) - old_hotfolder_filelist_dict[filename][1] > file_expiry_time) and (filename not in list_of_growing_files) and (filename not in loudness_calculation_queue) and (filename not in files_queued_to_loudness_calculation):
				files_queued_for_deletion.append(filename)
				
			#################################################################################
			# Add files we need to study further to a dictionary with some file information #
			#################################################################################
			# Add the files information to dictionary.
			# This statement also guarantees that files put in deletion queue by subprocess 'decompress_audio_streams_with_ffmpeg' running in separate thread, are not processed here further. That would sometimes cause files being used by one thread to be deleted by the other.
			if (filename not in files_queued_for_deletion) and (filename not in unsupported_ignored_files_dict):
				# Save information about the file in a dictionary: filename, file size, time file was first seen in HotFolder.
				if not filename in old_hotfolder_filelist_dict:
					# When the file has just appeared to the HotFolder, it has not been analyzed yet.
					# However some dummy data for the file needs to be filled, so we create that data here.
					# This dummy data is replaced with real data when the file stops growing and gets analyzed.
					# file_information_to_save = [ FileSize, TimeAppearedToHotFolder, ModificationTime, InformationFilledByFFmpeg ]
					dummy_information = [False, False, 0, [], '3'] 
					file_information_to_save.append(dummy_information)
				new_hotfolder_filelist_dict[filename] = file_information_to_save
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading HotFolder file metadata ' * english + 'Lähdehakemistopussa olevan tiedoston tietojen lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading HotFolder file metadata ' * english + 'Lähdehakemistopussa olevan tiedoston tietojen lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	################################################################################
	# Find expired files in results - directory and add them to the deletion queue #
	################################################################################
	try:
		for path, list_of_directories, list_of_files in os.walk(directory_for_results):
			break
		for filename in list_of_files:
			if filename == web_page_name:
				continue # Skip loudness calculation web - page we have created, we don't wan't to delete that.
			partial_path=os.path.relpath(path + os.sep + filename, hotfolder_path) # Truncate file path by removing the preceding 'HotFolder' path.
			time_file_was_first_seen = 0
			if partial_path in old_results_directory_filelist_dict:
				# If the file was there in poll previous to this one, the time the file was first seen is in dictionary 'old_results_directory_filelist_dict' get it and put in a variable.
				time_file_was_first_seen = old_results_directory_filelist_dict[partial_path]
				if int(time.time()) - time_file_was_first_seen > file_expiry_time: # Check if file has been there longer than the expiry time, if true queue file for deletion.
					files_queued_for_deletion.append(partial_path)
				else:
					# The file was there in the poll previous to this one, put the time the file was first seen in a dictionary along with filename.
					new_results_directory_filelist_dict[partial_path] = time_file_was_first_seen
			else:
				# If we get here the file was not there in the poll previous to this. The file is new, put the time the file was first seen in a dictionary along with the filename.
				new_results_directory_filelist_dict[partial_path] = int(time.time())
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading ResultsFolder directory listing ' * english + 'Tuloshakemiston hakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading ResultsFolder directory listing ' * english + 'Tuloshakemiston hakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])

	# Save latest directory poll information for the next poll.
	old_results_directory_filelist_dict = new_results_directory_filelist_dict
	new_results_directory_filelist_dict = {}

	########################################################
	# Delete all files that have been queued for deletion. #
	########################################################
	try:
		files_to_delete = copy.deepcopy(files_queued_for_deletion) # Copy file list to a new list, since we are going to modify the original list it can not be used as the iterator for the for-loop.
		for filename in files_to_delete:
			realtime = get_realtime(english, finnish)
			if os.path.exists(hotfolder_path + os.sep + filename):
				os.remove(hotfolder_path + os.sep + filename)
				files_queued_for_deletion.remove(filename)
				if silent == False:
					print('\r' + adjust_line_printout, ' Deleted file' * english + ' Poistin tiedoston' * finnish, '"' + str(filename) + '"', realtime)
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error deleting files queued for deletion ' * english + 'Poistettavien luettelossa olevan tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting files queued for deletion ' * english + 'Poistettavien luettelossa olevan tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
			
	files_to_delete = []

	##########################################################################################
	# Check if file has stopped growing, if true test if ffmpeg can find audio streams in it #
	######################################################################################################################################################################################
	#                                                                                                                                                                                    #
	# One thing that is not obvious from reading the code below is why new files gets processed and old files will not be processed again and again.                                     #
	# Files only get into the processing queue through the 'list_of_growing_files'.                                                                                                      #
	#                                                                                                                                                                                    #
	# Only if a file was not there during the previous HotFolder poll (filename is not in 'old_hotfolder_filelist_dict'), will the file be added to the 'list_of_growing_files'.         #
	# Only if a file was in the HotFolder during the last and the previous HotFolder poll (filename is in 'old_hotfolder_filelist_dict' and 'new_hotfolder_filelist_dict'),              #
	# it will be added to the processing queue.                                                                                                                                          #
	#                                                                                                                                                                                    #
	######################################################################################################################################################################################
	
	for filename in new_hotfolder_filelist_dict:
		
		if filename in old_hotfolder_filelist_dict:
			new_filesize = new_hotfolder_filelist_dict[filename][0] # Get file size from the newest directory poll.
			new_modification_time = new_hotfolder_filelist_dict[filename][2] # Get latest file modification time.
			old_filesize = old_hotfolder_filelist_dict[filename][0] # Get file size from the previous directory poll.
			time_file_was_first_seen = old_hotfolder_filelist_dict[filename][1] # Get the time the file was first seen from the previous directory poll dictionary.
			old_modification_time = old_hotfolder_filelist_dict[filename][2] # Get old file modification time.
			file_format_support_information = old_hotfolder_filelist_dict[filename][3] # Get other file information that was gathered during the last poll.

			# If filesize is still zero and it has not changed in 1,5 hours (5400 seconds), stop waiting and remove filename from list_of_growing_files.
			if (filename in list_of_growing_files) and (new_filesize == 0) and (int(time.time()) >= (time_file_was_first_seen + 5400)):
				list_of_growing_files.remove(filename)
			if (filename in list_of_growing_files) and (new_filesize > 0): # If file is in the list of growing files, check if growing has stopped. If HotFolder is on a native windows network share and multiple files are transferred to the HotFolder at the same time, the files get a initial file size of zero, until the file actually gets transferred. Checking for zero file size prevents trying to process the file prematurely.
				if (new_filesize != old_filesize) or (new_modification_time != old_modification_time): # If file size or modification time has changed print message to user about waiting for file transfer to finish.
					if silent == False:
						print('\r' + adjust_line_printout, ' Waiting for file transfer to end' * english + ' Odotan tiedostosiirron valmistumista' * finnish, end='')
				else:
					#######################################################################################################
					# Filesize has not changed since last poll, the file is ready to be inspected.                        #
					#######################################################################################################
					
					# Test if we really have read access to the file.
					# In case the HotFolder is on a native windows server, the server sometimes reports the file size as if the file transfer is ready,
					# when in fact the transfer is still in progress and the server has the file locked (no read access).
					
					we_have_true_read_access_to_the_file = True
					file_to_test = hotfolder_path + os.sep + filename
					
					try:
						# Open the file and read the first byte from it. If this fails skip the file for now, try again after the next HotFolder poll.
						with open(file_to_test, 'rb') as file_handler:
							byte = file_handler.read(1)
					except IOError:
						we_have_true_read_access_to_the_file = False
					except OSError:
						we_have_true_read_access_to_the_file = False
					
					if we_have_true_read_access_to_the_file == True:
						
						# Call a subroutine to inspect file with FFmpeg to get audio stream information.
						ffmpeg_parsed_audio_stream_information, ffmpeg_error_message, send_ffmpeg_error_message_by_email = get_audio_stream_information_with_ffmpeg_and_create_extraction_parameters(filename, hotfolder_path, directory_for_temporary_files, ffmpeg_output_format, english, finnish)
						# Assign audio stream information to variables.
						natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames = ffmpeg_parsed_audio_stream_information

						if (ffmpeg_supported_fileformat == False) and (filename not in unsupported_ignored_files_dict):
							# No audiostreams were found in the file, plot an error graphics file to tell the user about it and add the filename and the time it was first seen to the list of files we will ignore.
							if ffmpeg_error_message == '': # Check if ffmpeg printed an error message.
							
								# If ffmpeg error message can not be found, use a default message.
								error_message = 'No Audio Streams Found In File' * english + 'Tiedostosta ei löytynyt ääniraitoja' * finnish
								
								# This error message is not very important so don't send it by email, only send it to other possible destinations (screen, logfile).
								error_message_destinations = copy.deepcopy(where_to_send_error_messages)
								if 'email' in error_message_destinations:
									error_message_destinations.remove('email')
								send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, error_message_destinations)
								
							else:
								
								# FFmpeg error message was found tell the user about it.
								error_message = ffmpeg_error_message
								
								error_message_destinations = copy.deepcopy(where_to_send_error_messages)
								if send_ffmpeg_error_message_by_email == False:
									if 'email' in error_message_destinations:
										error_message_destinations.remove('email')
								send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, error_message_destinations)
								
							create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish)
							unsupported_ignored_files_dict[filename] = int(time.time())
						
						# If file duration was not found, or it is less than one second, then we have an error.
						# Don't process file, inform user by plotting an error graphics file and add the filename to the list of files we will ignore.
						if (ffmpeg_supported_fileformat == True) and (not audio_duration_rounded_to_seconds > 0) and (filename not in unsupported_ignored_files_dict):
							error_message = 'Audio duration less than 1 second ' * english + 'Tiedoston ääniraidan pituus on alle 1 sekunti' * finnish
							
							# This error message is not very important so don't send it by email, only send it to other possible destinations (screen, logfile).
							error_message_destinations = copy.deepcopy(where_to_send_error_messages)
							if 'email' in error_message_destinations:
								error_message_destinations.remove('email')
							send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, error_message_destinations)
							
							create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish)
							unsupported_ignored_files_dict[filename] = int(time.time())
						# The time slice value used in loudness calculation is normally 3 seconds. When we calculate short files <12 seconds, it's more convenient to use a smaller value of 0.5 seconds to get more detailed loudness graphics.
						if  (audio_duration_rounded_to_seconds > 0) and (audio_duration_rounded_to_seconds < 12):
							time_slice_duration_string = '0.5'
						if  audio_duration_rounded_to_seconds >= 12:
							time_slice_duration_string = '3'
						
						# If ffmpeg found audiostreams in the file, queue it for loudness calculation and print message to user.
						if filename not in unsupported_ignored_files_dict:
							file_format_support_information = [natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames]
							files_queued_to_loudness_calculation.append(filename)
							if silent == False:
								print('\r' + adjust_line_printout, '"' + str(filename) + '"', 'is in the job queue as number' * english + 'on laskentajonossa numerolla' * finnish, len(files_queued_to_loudness_calculation))
						list_of_growing_files.remove(filename) # File has been queued for loudness calculation, or it is unsupported, in both cases we need to remove it from the list of growing files.
			# Save information about the file in a dictionary:
			# filename, file size, time file was first seen in HotFolder, latest modification time, file format wav / flac / ogg, if format is supported by ffmpeg (True/False), number of audio streams found, information ffmpeg printed about the audio streams.
			new_hotfolder_filelist_dict[filename] = [new_filesize, time_file_was_first_seen, new_modification_time, file_format_support_information]
		else:
			# If we get here the file was not there in the directory poll before this one. We need to wait for another poll to see if the file is still growing. Add file name to the list of growing files.
			list_of_growing_files.append(filename)

	# Save latest directory poll information for the next round.
	old_hotfolder_filelist_dict = new_hotfolder_filelist_dict
	new_hotfolder_filelist_dict = {}

	##########################################################################
	# Start loudness calculation or ffmpeg decompression in separate threads #
	##########################################################################
	# One round of the following while - loop takes approximately 1 second to complete, the number stored in 'delay_between_directory_reads' determines how many times this loop is performed before exiting the while - loop and polling the HotFolder again.
	while loop_counter < delay_between_directory_reads:
		
		# Check if there are less processing threads going on than allowed, if true start some more.
		if (len(loudness_calculation_queue) * 2) < number_of_processor_cores:
			
			if len(files_queued_to_loudness_calculation) > 0: # Check if there are files queued for processing waiting in the queue.
				filename = files_queued_to_loudness_calculation.pop(0) # Remove the first file from the queue and put it in a variable.
				file_format_support_information = old_hotfolder_filelist_dict[filename][3] # The information about the file format is stored in a list in the dictionary, get it and store in a list.
				natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames = file_format_support_information # Save file format information to separate variables.
				realtime = get_realtime(english, finnish).replace('_', ' ')
				
				# If audio fileformat is natively supported by libebur128 and sox and has only one audio stream, we don't need to do extraction and flac conversion with ffmpeg, just start two loudness calculation processes for the file.
				if (number_of_ffmpeg_supported_audiostreams == 1) and (natively_supported_file_format == True):
					# Start simultaneously two threads to calculate file loudness. The first one calculates loudness by dividing the file in time slices and calculating the loudness of each slice individually. The second process calculates integrated loudness and loudness range of the file as a whole.
					# Both processes can be done in almost the same time as one, since the first process reads the file in to os file cache, so the second process doesn't need to read the disk at all. Reading from cache is much much faster than reading from disk.
					if silent == False:
						print ('\r' + 'File' * english + 'Tiedoston' * finnish, '"' + filename + '"' + ' processing started ' * english + ' käsittely   alkoi  ' * finnish, realtime)
					
					# Create commands for both loudness calculation processes.
					libebur128_commands_for_time_slice_calculation=[libebur128_path, 'dump', '-s', time_slice_duration_string] # Put libebur128 commands in a list.
					libebur128_commands_for_integrated_loudness_calculation=[libebur128_path, 'scan', '-l', peak_measurement_method] # Put libebur128 commands in a list.
					
					# Create events for both processes. When the process is ready it sets event = set, so that we know in the main thread that we can start more processes.
					event_for_timeslice_loudness_calculation = threading.Event() # Create a unique event for the process. This event is used to signal other threads that this process has finished.
					event_for_integrated_loudness_calculation = threading.Event() # Create a unique event for the process. This event is used to signal other threads that this process has finished.
					
					# Add file name and both the calculation process events to the dictionary of files that are currently being calculated upon.
					loudness_calculation_queue[filename] = [event_for_timeslice_loudness_calculation, event_for_integrated_loudness_calculation]
					# Create threads for both processes, the threads are not started yet.
					process_1 = threading.Thread(target=calculate_loudness_timeslices, args=(filename, hotfolder_path, libebur128_commands_for_time_slice_calculation, directory_for_temporary_files, directory_for_results, english, finnish)) # Create a process instance.
					process_2 = threading.Thread(target=calculate_integrated_loudness, args=(event_for_integrated_loudness_calculation, filename, hotfolder_path, libebur128_commands_for_integrated_loudness_calculation, english, finnish)) # Create a process instance.
					
					# Start both calculation threads.
					thread_object = process_2.start() # Start the calculation process in it's own thread.
					thread_object = process_1.start() # Start the calculation process in it's own thread.
					
				else:
					
					# Fileformat is not natively supported by libebur128 and sox, or it has more than one audio streams.
					# Start a process that extracts all audio streams from the file and converts them to wav or flac and moves resulting files back to the HotFolder for loudness calculation.
					if silent == False:
						print ('\r' + 'File' * english + 'Tiedoston' * finnish, '"' + filename + '"' + ' conversion started ' * english + '  muunnos    alkoi  ' * finnish, realtime)
						print('\r' + adjust_line_printout, ' Extracting' * english + ' Puran' * finnish, str(number_of_ffmpeg_supported_audiostreams), 'audio streams from file' * english + 'miksausta tiedostosta' * finnish, filename)
						
						for counter in range(0, number_of_ffmpeg_supported_audiostreams): # Print information about all the audio streams we are going to extract.
							print('\r' + adjust_line_printout, ' ' + details_of_ffmpeg_supported_audiostreams[counter][0])
					
					event_1_for_ffmpeg_audiostream_conversion = threading.Event() # Create two unique events for the process. The events are being used to signal other threads that this process has finished. This thread does not really need two events, only one, but as other calculation processes are started in pairs resulting two events per file, two events must be created here also for this process..
					event_2_for_ffmpeg_audiostream_conversion = threading.Event()
					process_3 = threading.Thread(target = decompress_audio_streams_with_ffmpeg, args=(event_1_for_ffmpeg_audiostream_conversion, event_2_for_ffmpeg_audiostream_conversion, filename, file_format_support_information, hotfolder_path, directory_for_temporary_files, english, finnish)) # Create a process instance.
					thread_object = process_3.start() # Start the process in it'own thread.
					loudness_calculation_queue[filename] = [event_1_for_ffmpeg_audiostream_conversion, event_2_for_ffmpeg_audiostream_conversion] # Add file name and both process events to the dictionary of files that are currently being calculated upon.

		######################################################################################
		# Tell user how many files are being processed and how many are waiting in the queue #
		######################################################################################
		# Only print message if there has been a change in the number of files in the queue or files in the calculation process.
		if (previous_value_of_files_queued_to_loudness_calculation != len(files_queued_to_loudness_calculation)) or (previous_value_of_loudness_calculation_queue != len(loudness_calculation_queue)):
			
			if silent == False:
				print('\r' + adjust_line_printout, ' Processing ' * english + ' Käsittelyssä ' * finnish + str(len(loudness_calculation_queue)) + ' files, ' * english + ' tiedostoa, ' * finnish +  str(len(files_queued_to_loudness_calculation)) + ' jobs in the queue' * english + ' työtä jonossa.' * finnish)
			previous_value_of_files_queued_to_loudness_calculation = len(files_queued_to_loudness_calculation)
			previous_value_of_loudness_calculation_queue = len(loudness_calculation_queue)

		###################################
		# Find threads that have finished #
		###################################
		finished_processes=[]
		for filename in loudness_calculation_queue:
			event_for_process_1, event_for_process_2 = loudness_calculation_queue[filename] # Take both events for the file from the dictionary.
			
			if (event_for_process_1.is_set()) and (event_for_process_2.is_set()): # Check if both events are set (= both threads have finished), if true add the file name to the list of finished processes.
				finished_processes.append(filename)

		# If both threads processing the file have finished, remove file from the queue of files being processed.
		for filename in finished_processes: # Get names of files who's processing threads have completed and print message to user.
			realtime = get_realtime(english, finnish).replace('_', ' ')
			del loudness_calculation_queue[filename] # Remove file name from the list of files currently being calculated upon.
			completed_files_list.insert(0, filename) # Add filename at the beginning of the list of completed files. This list stores only the order in which the files were completed.
			completed_files_dict[filename] = realtime # This dictionary stores the time processing each file was completed.
			if silent == False:
				print('\r' + 'File' * english + 'Tiedoston' * finnish, '"' + filename + '"', 'processing finished' * english + 'käsittely valmistui' * finnish, realtime)
			
			# Keep the list of completed files to only 100 items long, if longer then remove last item from the list.
			if len(completed_files_list) > 100:
				
				# Remove oldest filename from list and dictionary
				filename_to_remove = completed_files_list.pop()
				del completed_files_dict[filename_to_remove]

		# Wait one second before checking if processor cores have become free and more calculation processes can be started.
		time.sleep(1)
		loop_counter = loop_counter + 1
					
	# Check if the time between directory polls has expired and a new poll needs to be made. One advacement of the counter is approximately one second. Default time between directory polls is 5 seconds.
	if loop_counter >= delay_between_directory_reads:
		loop_counter = 0
