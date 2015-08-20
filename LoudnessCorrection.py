#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Mikael Hartzell 2012 and contributors:
# Original idea for the program and Gnuplot commands by Timo Kaleva.
#
# This program is distributed under the GNU General Public License, version 3 (GPLv3)
#
# Check the license here: http://www.gnu.org/licenses/gpl.txt
# Basically this license gives you full freedom to do what ever you wan't with this program. You are free to use, modify, distribute it any way you like.
# The only restriction is that if you make derivate works of this program AND distribute those, the derivate works must also be licensed under GPL 3.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#
# This program calculates loudness according to EBU R128 standard for each file it finds in the HotFolder.
#
# System requirements, Linux (preferably Ubuntu), gnuplot, python3, ffmpeg, sox v14.4.0 or later.
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
import signal
import traceback

loudnesscorrection_version = '273'
freelcs_version = 'unknown version'

########################################################################################################################################################################################
# All default values for settings are defined below. These variables define directory poll interval, number of processor cores to use, language of messages and file expiry time, etc. #
# These values are used if the script is run without giving an settings file as an argument. Values read from the settingsfile override these default settings.			       #
########################################################################################################################################################################################
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

# Assign some debug variables.
silent = False # Use True if you don't want this programs to print anything on screen (useful if you want to start this program from Linux init scripts).

# When debug_file_processing == True, then information about integrated loudness calculation and time slice processing is stored in separate dictionaries.
# This information is later appended to 'debug_complete_final_information_for_all_file_processing_dict'.
# The information must be first gathered to separate dictionary because loudness calculation information is simultaneously gathered in two threads.
debug_temporary_dict_for_integrated_loudness_calculation_information = {} 
debug_temporary_dict_for_timeslice_calculation_information = {} 

# When debug_file_processing == True, then debug information about file processing is stored in this dictionary.
# This information is later appended to 'debug_complete_final_information_for_all_file_processing_dict'. 
debug_temporary_dict_for_all_file_processing_information = {} 

# All file processing debug information from the temp dictionaries defined above is gathered to this dictionary and later saved to disk.
debug_complete_final_information_for_all_file_processing_dict = {} 

# Parse commandline arguments and assign values to variables
debug_all = False
debug_lists_and_dictionaries  = False
debug_file_processing = False
save_all_measurement_results_to_a_single_debug_file = False
configfile_path = ''
configfile_found = False
target_path = ''
force_samplepeak = False
force_truepeak = False
force_no_ffmpeg = False
force_quit_when_idle = False
quit_when_idle_seconds = 3 * 60 # If the option to exit when idle is on, then this defines how long we idle before exiting the program. Default is 3 minutes.
quit_counter = 0
quit_all_threads_now = False

arguments_remaining = copy.deepcopy(sys.argv[1:])
number_of_arguments = len(arguments_remaining)

for argument in sys.argv[1:]:
	
	if configfile_found == True:
		configfile_path = argument
		arguments_remaining.pop(arguments_remaining.index(argument))
		configfile_found = False
		continue		

	if argument.lower() == '-configfile':
		configfile_found = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

	if argument.lower() == '-debug_lists_and_dictionaries':
		debug_lists_and_dictionaries = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

	if argument.lower() == '-debug_file_processing':
		debug_file_processing = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue
	
	if argument.lower() == '-debug_all':
		debug_all = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

	if argument.lower() == '-save_all_measurement_results_to_a_single_debug_file':
		save_all_measurement_results_to_a_single_debug_file = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue
	
	if argument.lower() == '-finnish':
		language = 'fi'
		finnish = 1
		english = 0
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

	if argument.lower() == '-silent':
		silent = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

	if argument.lower() == '-force-samplepeak':
		force_samplepeak = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

	if argument.lower() == '-force-truepeak':
		force_truepeak = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

	if argument.lower() == '-force-no-ffmpeg':
		force_no_ffmpeg = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

	if argument.lower() == '-force-quit-when-idle':
		force_quit_when_idle = True
		arguments_remaining.pop(arguments_remaining.index(argument))
		continue

if (configfile_path == '') and (len(arguments_remaining) > 0):
	target_path = arguments_remaining[0]
	arguments_remaining.pop(0)

if len(arguments_remaining) != 0:
	error_message = 'Error: Unknown arguments on commandline: ' * english + 'Virhe: komentorivillä on tuntemattomia argumentteja: ' * finnish + str(arguments_remaining)

	print()
	print(error_message)
	print()

	sys.exit(1)

# If the user did not define target path on the commandline print an error message.
if (configfile_path == '') and (target_path == ''):
	error_message = 'Error: Target path and configfile paths are not defined' * english + 'Virhe: Kohdehakemistoa ja asetustiedostoa ei ole määritelty' * finnish

	print()
	print(error_message)
	print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)
	print('Debug options: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -debug_all, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * english + 'Debuggausoptioita: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * finnish )
	print()

	sys.exit(1)

if configfile_path != '':

	if (os.path.exists(configfile_path) == False) or (os.access(configfile_path, os.R_OK) == False):
		error_message = 'Error: Configfile does not exist or exists but is not readable' * english + 'Virhe: Asetustiedostoa ei ole olemassa tai siihen ei ole lukuoikeuksia' * finnish

		print()
		print(error_message)
		print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)	
		print('Debug options: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -debug_all, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * english + 'Debuggausoptioita: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * finnish )
		print()

		sys.exit(1)

	if os.path.isfile(configfile_path) == False:
		error_message = 'Error: Configfile is not a regular file' * english + 'Virhe: Asetustiedosto ei ole tiedosto' * finnish

		print()
		print(error_message)
		print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)	
		print('Debug options: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -debug_all, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * english + 'Debuggausoptioita: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * finnish )
		print()

		sys.exit(1)
else:
	if os.path.exists(target_path) == True:
		if os.path.isdir(target_path):
			target_path = os.sep + target_path.strip(os.sep) # If there is a slash at the end of the path name, remove it.
		else:
			error_message = 'Error: Target path is not a directory' * english + 'Virhe: Kohdepolku ei ole hakemisto' * finnish

			print()
			print(error_message)
			print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)	
			print('Debug options: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -debug_all, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * english + 'Debuggausoptioita: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * finnish )
			print()

			sys.exit(1)
	else:
		error_message = 'Error: Target directory does not exist' * english + 'Virhe: Kohdehakemistoa ei ole olemassa' * finnish

		print()
		print(error_message)
		print('\nUSAGE: Give either the full path to the HotFolder or the option: -configfile followed by full path to the config file as the argument to the program.\n' * english + '\nKÄYTTÖOHJE: Anna ohjelman komentoriville optioksi joko Hotfolderin koko polku tai optio: -configfile ja sen perään asetustiedoston koko polku.\n' * finnish)	
		print('Debug options: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -debug_all, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * english + 'Debuggausoptioita: -debug_file_processing, -debug_lists_and_dictionaries, -save_all_measurement_results_to_a_single_debug_file, -force-samplepeak, -force-truepeak, -force-no-ffmpeg, -force-quit-when-idle' * finnish )
		print()

		sys.exit(1)

if debug_all == True:
	debug_lists_and_dictionaries = True
	debug_file_processing = True
	save_all_measurement_results_to_a_single_debug_file = True
	write_loudness_calculation_results_to_a_machine_readable_file = True
	ffmpeg_allowed_wrapper_formats = ['all']
	ffmpeg_allowed_codec_formats = ['all']

# Define folder names according to the language selected above.
if language == 'en':
	hotfolder_path = target_path + os.sep + 'LoudnessCorrection'
else:
	hotfolder_path = target_path + os.sep + 'AanekkyysKorjaus'

directory_for_temporary_files = target_path + os.sep + '00-Loudness_Calculation_Temporary_Files'
directory_for_results = hotfolder_path + os.sep + '00-Corrected_Files' * english + '00-Korjatut_Tiedostot' * finnish # This directory always needs to be a subdirectory for the hotfolder, otherwise deleting files from the results directory won't work.


os_name = '' # Create variable to store distro information.
os_version = '' # Create variable to store os version information.

delay_between_directory_reads = 5 # HotFolder poll interval (seconds) (how ofter the directory is checked for new files).
number_of_processor_cores = 6 # The number of processor cores to use for simultaneous file processing and loudness calculation. Only use even numbers. Slightly too big number often results in better performance. If you have 4 cores try defining 6 or 8 here and check the time it takes processing same set of files.
if number_of_processor_cores / 2 != int(number_of_processor_cores / 2): # If the number for processor cores is not an even number, force it to the next bigger even number.
	 number_of_processor_cores = number_of_processor_cores + 1 
file_expiry_time = 60*60*8 # This number (in seconds) defines how long the files are allowed to exist in HotFolder and results - directory. File creation time is not taken into account only the time this program first saw the file in the directory. Files are automatically deleted when they are 'expired'.

natively_supported_file_formats = ['.wav', '.flac', '.ogg'] # Natively supported formats may be processed without first decoding to flac with ffmpeg, since libebur128 and sox both support these formats.
ffmpeg_output_wrapper_format = 'wav' # Possible values are 'flac' and 'wav'. This only affects formats that are first decodec with ffmpeg (all others but wav, flac, ogg).
if not ffmpeg_output_wrapper_format == 'wav':
	ffmpeg_output_wrapper_format = 'flac'

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

# This variable is used when some of our python code caused a crash. The variable (when True) causes all error messages waiting to be sent by email to be sent immediately.
critical_python_error_has_happened = False
list_of_critical_python_errors = []

# Define lists of supported pcm bit depths
pcm_8_bit_formats = ['pcm_s8', 'pcm_s8_planar', 'pcm_u8']
pcm_16_bit_formats = ['pcm_s16be', 'pcm_s16le', 'pcm_s16le_planar', 'pcm_u16be', 'pcm_u16le']
pcm_24_bit_formats = ['pcm_dvd', 'pcm_lxf', 'pcm_s24be', 'pcm_s24daud', 'pcm_s24le', 'pcm_u24be', 'pcm_u24le']
pcm_32_bit_formats = ['pcm_f32be', 'pcm_f32le', 'pcm_s32be', 'pcm_s32le', 'pcm_u32be', 'pcm_u32le']
pcm_64_bit_formats = ['pcm_f64be', 'pcm_f64le']

#######################################
# Set defaults for MXF audio remixing #
#######################################
enable_mxf_audio_remixing = False
remix_map_file_extension = '.remix_map'
global_mxf_audio_remix_channel_map = [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2] # Example [2, 6, 2, 2]	 Create stereo, 5.1, stereo and stereo mixes (if there are enough source audio channels).

mxf_formats = ['mxf','mxf_d10']
mpeg_wrapper_formats = ['mpeg','mp2','mp3','mp4','m4v','m4a','mpegts','mpegtsraw','mpegvideo','mpeg1video','mpeg2video','vcd','svcd','dvd','vob']
ffmpeg_free_wrapper_formats = ['wav', 'flac', 'ogg', 'mkv', 'matroska', 'mka']

enable_all_nonfree_ffmpeg_wrapper_formats = True

if enable_all_nonfree_ffmpeg_wrapper_formats == True:
	ffmpeg_allowed_wrapper_formats = ['all']
else:
	ffmpeg_allowed_wrapper_formats = ffmpeg_free_wrapper_formats


ffmpeg_free_codec_formats = []
ffmpeg_free_codec_formats.extend(pcm_8_bit_formats)
ffmpeg_free_codec_formats.extend(pcm_16_bit_formats)
ffmpeg_free_codec_formats.extend(pcm_24_bit_formats)
ffmpeg_free_codec_formats.extend(pcm_32_bit_formats)
ffmpeg_free_codec_formats.extend(pcm_64_bit_formats)
ffmpeg_free_codec_formats.append('flac')
ffmpeg_free_codec_formats.append('vorbis')

enable_all_nonfree_ffmpeg_codec_formats = True

if enable_all_nonfree_ffmpeg_codec_formats == True:
	ffmpeg_allowed_codec_formats = ['all']
else:
	ffmpeg_allowed_codec_formats = ffmpeg_free_codec_formats

if debug_all == True:
	ffmpeg_allowed_wrapper_formats = ['all']
	ffmpeg_allowed_codec_formats = ['all']

########################################################
# Set defaults for 'Machine Reabable Results' settings #
########################################################

# These values will be overwritten by values that come from the installer program through the file Loudness_Correction_Settings.pickle
write_loudness_calculation_results_to_a_machine_readable_file = False
create_loudness_corrected_files = True
create_loudness_history_graphics_files = True
delete_original_file_immediately = True
unit_separator = chr(31) # This non printable ascii character is used to separate individual values for a mix.
record_separator = chr(13) + chr(10) # This string is used to separate info for different mixes. This is by default the carriage return character followed by the line feed character. This sequence is used in windows to separate lines of text.


# Define a counter that counts how long ago the ip address of the machine has been checked (needed with dynamic ip).
# Also define in seconds the interval between ip address checks (default 5 mins = 300 secs).
ip_address_refresh_interval = 300 
ip_address_refresh_counter = ip_address_refresh_interval  # Force ip address check immediately when the program is run by setting the counter to the same value as the check interval.
ip_address_acquirement_error_has_already_been_reported = False

###############################################################################################################################################################################
# Default value definitions end here :)																	      #
###############################################################################################################################################################################


def calculate_integrated_loudness(event_for_integrated_loudness_calculation, filename, hotfolder_path, libebur128_commands_for_integrated_loudness_calculation, english, finnish):

	"""This subroutine uses libebur128 program loudness to calculate integrated loudness, loudness range and difference from target loudness."""

# This subroutine works like this:
# ---------------------------------
# The subroutine is usually started from the main program in it's own thread and it calculates integrated loudness and loudness range of a file and difference from target loudness.
# Simultaneusly to this thread another subroutine calculates loudness of the file slicing the file in short segments and calculating each slice individially. Slices are 3 seconds for files 10 seconds or longer and 0.5 seconds for files 9 seconds or shorter.
# The results from this thread needs to be communicated to the time slice thread, since results of both threads are needed for the graphics generation.
# This thread communicates it's results to the other thread by putting them in dictionary 'integrated_loudness_calculation_results' that can be read in the other thread.

	try:
		global integrated_loudness_calculation_results
		integrated_loudness_calculation_stdout = b''
		integrated_loudness_calculation_stderr = b''
		file_to_process = hotfolder_path + os.sep + filename
		integrated_loudness = 0
		loudness_range = 0
		difference_from_target_loudness = 0
		global peak_measurement_method
		highest_peak_float = float('0')
		highest_peak_db = float('-120') # Set default value for sample peak.
		integrated_loudness_is_below_measurement_threshold = False
		integrated_loudness_calculation_parsed_results = []
		integrated_loudness_calculation_error = False
		integrated_loudness_calculation_error_message = ''
		integrated_loudness_calculation_stdout_string = ''
		integrated_loudness_calculation_stderr_string = ''
		integrated_loudness_calculation_results_list = []
		error_message = ''

		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_integrated_loudness_calculation_information

			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('calculate_integrated_loudness')
			debug_temporary_dict_for_integrated_loudness_calculation_information[filename] = debug_information_list

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

			# Save debug information.
			if debug_file_processing == True:
				debug_information_list.append('integrated_loudness_calculation_stdout_string')
				debug_information_list.append(integrated_loudness_calculation_stdout_string.replace('\n','\\n'))
				debug_information_list.append('integrated_loudness_calculation_stderr_string')
				debug_information_list.append(' '.join(integrated_loudness_calculation_stderr_string.replace('#','').replace('[','').replace(']','').replace('\n','').split())) # Remove # - characters and white space from string.
				debug_temporary_dict_for_integrated_loudness_calculation_information[filename] = debug_information_list

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
				integrated_loudness_calculation_uncleaned_results = integrated_loudness_calculation_stdout_string.split('\n')[0].split(',')
				integrated_loudness_calculation_parsed_results = [integrated_loudness_calculation_uncleaned_results[0].replace(' LUFS','').strip()]
				integrated_loudness_calculation_parsed_results.append(integrated_loudness_calculation_uncleaned_results[1].replace(' LU','').strip())
				integrated_loudness_calculation_parsed_results.append(integrated_loudness_calculation_uncleaned_results[2].strip())
				
				integrated_loudness = float(integrated_loudness_calculation_parsed_results[0])
				loudness_range = float(integrated_loudness_calculation_parsed_results[1])
				highest_peak_float = float(integrated_loudness_calculation_parsed_results[2])


				# Test if integrated loudness calculation results are sane (output is numeric).
				if isinstance(integrated_loudness, (float, int)) == False:
					integrated_loudness_calculation_error = True
					integrated_loudness_calculation_error_message = 'Error: libebur128 calculation result (integrated_loudness) is not a number: ' * english + 'Virhe: libebur128 laskentatulos (integroitu äänekkyys) ei ole numero: ' * finnish + '\'' + str(integrated_loudness_calculation_parsed_results[0]) + '\''

				if isinstance(loudness_range, (float, int)) == False:
					integrated_loudness_calculation_error = True
					integrated_loudness_calculation_error_message = 'Error: libebur128 calculation result (loudness_range) is not a number: ' * english + 'Virhe: libebur128 laskentatulos (äänekkyyden vaihteluväli) ei ole numero: ' * finnish + '\'' + str(integrated_loudness_calculation_parsed_results[1]) + '\''
				
				if isinstance(highest_peak_float, (float, int)) == False:
					integrated_loudness_calculation_error = True
					integrated_loudness_calculation_error_message = 'Error: libebur128 calculation result (highest_peak) is not a number: ' * english + 'Virhe: libebur128 laskentatulos (Huippuarvo) ei ole numero: ' * finnish + '\'' + str(integrated_loudness_calculation_parsed_results[2]) + '\''
				
				if highest_peak_float == 0:
					integrated_loudness_calculation_error = True
					integrated_loudness_calculation_error_message = 'Error: libebur128 calculation result (highest_peak) is zero: ' * english + 'Virhe: libebur128 laskentatulos (Huippuarvo) ei ole numero: ' * finnish + '\'' + str(integrated_loudness_calculation_parsed_results[2]) + '\''
				
				if highest_peak_float < 0:
					integrated_loudness_calculation_error = True
					integrated_loudness_calculation_error_message = 'Error: libebur128 calculation result (highest_peak) is negative: ' * english + 'Virhe: libebur128 laskentatulos (Huippuarvo) on negatiivinen: ' * finnish + '\'' + str(integrated_loudness_calculation_parsed_results[2]) + '\''

				# Save debug information.
				if debug_file_processing == True:
					debug_information_list.append('integrated_loudness_calculation_parsed_results')
					debug_information_list.append(integrated_loudness_calculation_parsed_results)
					debug_information_list.append('integrated_loudness')
					debug_information_list.append(integrated_loudness)
					debug_information_list.append('loudness_range')
					debug_information_list.append(loudness_range)
					debug_information_list.append('highest_peak_float')
					debug_information_list.append(highest_peak_float)
					debug_temporary_dict_for_integrated_loudness_calculation_information[filename] = debug_information_list

				try:
					highest_peak_db = round(20 * math.log(highest_peak_float, 10),1)
				except ValueError as reason_for_error:
					integrated_loudness_calculation_error = True
					integrated_loudness_calculation_error_message = 'Error: ' + '\'' + str(reason_for_error) + '\'' + ' trying to convert libebur128 sample / truepeak value to decibels: ' * english + 'Virhe: ' + '\'' + str(reason_for_error) + '\'' + ' muutettaessa libebur128:n huippuarvoa desibeleiksi: ' * finnish  + str(highest_peak_float)


				difference_from_target_loudness = round(integrated_loudness - float('-23'), 1)


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

		# Save debug information.
		if debug_file_processing == True:
			debug_information_list.append('peak_measurement_method ')
			debug_information_list.append(peak_measurement_method )
			debug_information_list.append('highest_peak_db')
			debug_information_list.append(highest_peak_db)
			debug_information_list.append('difference_from_target_loudness')
			debug_information_list.append(difference_from_target_loudness)
			debug_information_list.append('integrated_loudness_calculation_error')
			debug_information_list.append(integrated_loudness_calculation_error)
			debug_information_list.append('integrated_loudness_calculation_error_message')
			debug_information_list.append(integrated_loudness_calculation_error_message)
			debug_information_list.append('integrated_loudness_is_below_measurement_threshold')
			debug_information_list.append(integrated_loudness_is_below_measurement_threshold)
			debug_information_list.append('error_message')
			debug_information_list.append(error_message)
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_integrated_loudness_calculation_information[filename] = debug_information_list

		# Set the event for this calculation thread. The main program checks the events and sees that this calculation thread is ready.
		event_for_integrated_loudness_calculation.set()

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'calculate_integrated_loudness'

		# Set the event for this calculation thread. The main program checks the events and sees that this calculation thread is ready.
		event_for_integrated_loudness_calculation.set()

		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	return()

def calculate_loudness_timeslices(filename, hotfolder_path, libebur128_commands_for_time_slice_calculation, directory_for_temporary_files, directory_for_results, english, finnish, expected_number_of_time_slices, expected_file_size, event_for_timeslice_loudness_calculation, event_for_integrated_loudness_calculation):

	"""This subroutine uses libebur128 loudness-executable to calculate file loudness segmenting the file in time slices and calculating loudness of each slice."""

	# This subroutine works like this:
	# ---------------------------------
	# The subroutine is started from the main program in it's own thread.
	# This routine starts libebur128 loudness-executable to calculate the time slice loudness values and puts the resulting output (list of dB values each in it's own row) in a list.
	# Simultaneusly to this thread another subroutine calculates integrated loudness, loudness range and difference from target loudness.
	# This routine waits for the other loudness calculation thread to finnish since it's results are needed to go forward.
	# This routine then starts the loudness graphics plotting subroutine giving it loudness results from both calculation processes.

	try:
		timeslice_loudness_calculation_stdout = b''
		timeslice_loudness_calculation_stderr = b''
		timeslice_loudness_calculation_stderr_string = ''
		timeslice_loudness_calculation_result_list = []
		file_to_process = hotfolder_path + os.sep + filename
		number_of_timeslices = 0
		time_slice_duration_string = 3 # Set a default value that will be overwritten with a value sent from the main routine.
		timeslice_calculation_error = False
		timeslice_calculation_error_message =''

		error_message = ''
		file_size = 0

		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			global debug_temporary_dict_for_timeslice_calculation_information
			debug_information_list = []

			if filename in debug_temporary_dict_for_timeslice_calculation_information:
				debug_information_list = debug_temporary_dict_for_timeslice_calculation_information[filename]
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('calculate_loudness_timeslices')
			debug_temporary_dict_for_timeslice_calculation_information[filename] = debug_information_list

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

			if abs(number_of_timeslices - expected_number_of_time_slices) > 1:
				timeslice_calculation_error = True
				timeslice_calculation_error_message = 'Number of time slices from loudness calculation: ' * english + 'Äänekkyyslaskennasta saatujen aikaviipaleiden määrä: ' * finnish + str(number_of_timeslices) + ' differs from the number that was expected: ' * english + ' eroaa ennakoidusta lukumäärästä: ' * finnish + str(expected_number_of_time_slices) 

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('number_of_timeslices')
				debug_information_list.append(number_of_timeslices)
				debug_information_list.append('timeslice_loudness_calculation_result_list')
				debug_information_list.append(timeslice_loudness_calculation_result_list)
				debug_information_list.append('expected_number_of_time_slices')
				debug_information_list.append(expected_number_of_time_slices)
				debug_temporary_dict_for_timeslice_calculation_information[filename] = debug_information_list

			# Wait for the other loudness calculation thread to end since it's results are needed in the next step of the process.
			integrated_loudness_calculation_is_ready = False
			
			while integrated_loudness_calculation_is_ready == False: # Wait until the other thread has finished. event = set, means thread has finished.
				if event_for_integrated_loudness_calculation.is_set():
					integrated_loudness_calculation_is_ready = True
				else:
					time.sleep(1)
		else:
			# If we get here the file we were supposed to process vanished from disk after the main program started this thread. Print a message to the user.
			error_message = 'VIRHE !!!!!!! Tiedosto' * finnish + 'ERROR !!!!!!! FILE' * english + ' ' + filename + ' ' + 'hävisi kovalevyltä ennen käsittelyn alkua.' * finnish + 'dissapeared from disk before processing started.' * english
			send_error_messages_to_screen_logfile_email(error_message, [])

		# Check once again that the file size has not changed, if it has then we have started loudness calculation before the file was fully transmitted.	
		try:
			file_metadata=os.lstat(file_to_process) # Get file information (size, date, etc)
			file_size = file_metadata.st_size

			if file_size != expected_file_size:
				timeslice_calculation_error = True
				timeslice_calculation_error_message = 'File size has changed during processing from: ' * english + 'Tiedoston koko on muuttunut laskennan aikana: ' * finnish + str(expected_file_size) + ' to: ' * english + ' -> ' * finnish + str(file_size)
		except IOError as reason_for_error:
			# The user has deteled the file or there is another problem reading the file size, this probably means we can not continue processing the file, so to be on the safe side we halt the process.
			timeslice_calculation_error = True
			timeslice_calculation_error_message = 'Error accessing file: ' * english + 'Tiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error) 
		except OSError as reason_for_error:
			# The user has deteled the file or there is another problem reading the file size, this probably means we can not continue processing the file, so to be on the safe side we halt the process.
			timeslice_calculation_error = True
			timeslice_calculation_error_message = 'Error accessing file: ' * english + 'Tiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error) 

		# Save some debug information. 
		if debug_file_processing == True:
			debug_information_list.append('expected_file_size')
			debug_information_list.append(expected_file_size)
			debug_information_list.append('file_size')
			debug_information_list.append(file_size)
			debug_information_list.append('timeslice_calculation_error')
			debug_information_list.append(timeslice_calculation_error)
			debug_information_list.append('timeslice_calculation_error_message')
			debug_information_list.append(timeslice_calculation_error_message)
			debug_information_list.append('error_message')
			debug_information_list.append(error_message)
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_timeslice_calculation_information[filename] = debug_information_list

		# We now have all loudness calculation results needed for graphics generation, start the subprocess that plots graphics and calls another subprocess that creates loudness corrected audio with sox.
		create_gnuplot_commands(filename, number_of_timeslices, time_slice_duration_string, timeslice_calculation_error, timeslice_calculation_error_message, timeslice_loudness_calculation_stdout, hotfolder_path, directory_for_temporary_files, directory_for_results, english, finnish)
		# After generating graphics and loudness corrected audio, set the event for this calculation thread. The main program checks the events and sees that this calculation thread is ready.
		event_for_timeslice_loudness_calculation.set()

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'calculate_loudness_timeslices'

		# Set the event for this calculation thread. 
		event_for_timeslice_loudness_calculation.set()

		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

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

	try:
		global integrated_loudness_calculation_results
		global silent

		# Set default values for integrated loudness calculation results. Defaults will be overwritten by real results if integrated loudness calculation is successful. Defaults are used if calculation fails.
		integrated_loudness_calculation_results_list = [0, 0, 0, True, 'Integrated loudness calculation failed to finish', -120, False] 
		integrated_loudness = integrated_loudness_calculation_results_list[0]
		difference_from_target_loudness = integrated_loudness_calculation_results_list[1]
		loudness_range = integrated_loudness_calculation_results_list[2]
		integrated_loudness_calculation_error = integrated_loudness_calculation_results_list[3]
		integrated_loudness_calculation_error_message = integrated_loudness_calculation_results_list[4]
		highest_peak_db = integrated_loudness_calculation_results_list[5]
		integrated_loudness_is_below_measurement_threshold = integrated_loudness_calculation_results_list[6]

		commandfile_for_gnuplot = directory_for_temporary_files + os.sep + filename + '-gnuplot_commands'
		loudness_calculation_table = directory_for_temporary_files + os.sep + filename + '-loudness_calculation_table'
		gnuplot_temporary_output_graphicsfile = directory_for_temporary_files + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish
		warning_message = ''
		sox_encountered_an_error = False
		sox_error_message = ''
		
		global create_loudness_history_graphics_files
		global create_loudness_corrected_files
		global write_loudness_calculation_results_to_a_machine_readable_file
		global temp_loudness_results_for_automation

		error_message = ''
		gnuplot_commands = []

		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_all_file_processing_information

			if filename in debug_temporary_dict_for_all_file_processing_information:
				debug_information_list = debug_temporary_dict_for_all_file_processing_information[filename]
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('create_gnuplot_commands')
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list
		
		# Get loudness calculation results from the integrated loudness calculation process. Results are in list format in dictionary 'integrated_loudness_calculation_results', assing results to variables.
		if filename in integrated_loudness_calculation_results:
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


		if create_loudness_history_graphics_files == True:

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

			if audio_duration_rounded_to_seconds >= 691200: # File duration is over 192 hours.
				plotfile_x_axis_divider = 28800
				plotfile_x_axis_time = 1
				plotfile_x_axis_name = 'Days' * english + 'Päiviä' * finnish

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
		
		# Save some debug information.
		if debug_file_processing == True:
			debug_information_list.append('Message')
			debug_information_list.append('Calling subroutine: get_audiofile_info_with_sox_and_determine_output_format')
		
		# Get technical info from audio file and determine what the output format will be
		channel_count, sample_rate, bit_depth, sample_count, flac_compression_level, output_format_for_intermediate_files, output_format_for_final_file, audio_channels_will_be_split_to_separate_mono_files, audio_duration, output_file_too_big_to_split_to_separate_wav_channels, sox_encountered_an_error, sox_error_message = get_audiofile_info_with_sox_and_determine_output_format(directory_for_temporary_files, hotfolder_path, filename)

		# Save some debug information.
		if debug_file_processing == True:
			debug_information_list.append('Message')
			debug_information_list.append('Returned from subroutine: get_audiofile_info_with_sox_and_determine_output_format')

		# Write details of loudness measurement of the file to a debug logfile.
		# This is a debugging option.
		if (integrated_loudness_calculation_error == False) and (timeslice_calculation_error == False):

			if save_all_measurement_results_to_a_single_debug_file == True:

				global loudness_calculation_logfile_path

				if loudness_calculation_logfile_path == '':
					loudness_calculation_logfile_path = directory_for_error_logs + os.sep + 'loudness_calculation_log-' + str(get_realtime(english, finnish)[1]) + '.txt'

				loudness_calculation_data = filename + ',EndOFFileName,' + str(integrated_loudness) + ',' + str(loudness_range) + ',' + str(highest_peak_db) + ',' + str(channel_count) + ',' + str(sample_rate) + ',' + str(bit_depth) + ',' + str(int(audio_duration)) + '\n'

				# Save some debug information.
				if debug_file_processing == True:
					debug_information_list.append('Message')
					debug_information_list.append('Calling subroutine: debug_write_loudness_calculation_info_to_a_logfile')

				debug_write_loudness_calculation_info_to_a_logfile(loudness_calculation_data, loudness_calculation_logfile_path)

				# Save some debug information.
				if debug_file_processing == True:
					debug_information_list.append('Message')
					debug_information_list.append('Returned from subroutine: debug_write_loudness_calculation_info_to_a_logfile')


		# Write loudness calculation results of each file to separate text files in results directory.
		# This is a user definable option.
		if write_loudness_calculation_results_to_a_machine_readable_file == True:

			# Add info for all mixes found in the file to dictionary that is used to write the machine readable results file.

			error_code = 0
			error_message = ' '

			if integrated_loudness_calculation_error == True:
				error_code = 2
				error_message = 'ERROR !!! in libebur128 integrated loudness calculation: ' * english + 'VIRHE !!! libebur128:n keskimääräisen äänekkyyden laskennassa: ' * finnish + integrated_loudness_calculation_error_message
		
			if integrated_loudness_is_below_measurement_threshold == True:
				error_code = 1
				# variable 'error_message' is set by the previous if statement for this situation also. In this case it says 'Loudness is below measurement threshold'. The contents for 'error_message' is taken by the previous if statement from the variable 'integrated_loudness_calculation_error_message'.

			list_of_filenames = []

			if error_code == 0:

				number_of_files_in_this_mix = 1

				if audio_channels_will_be_split_to_separate_mono_files == True:
					number_of_files_in_this_mix = int(channel_count)

				filename_and_extension = os.path.splitext(filename)

				# The combined channels in final output file exceeds the max file size and the file needs to be split to separate mono files.
				# Create output filenames for the machine readable readable results file.
				if number_of_files_in_this_mix > 1:
				
					for counter in range(1, channel_count + 1):
						split_channel_targetfile_name = filename_and_extension[0] + '-Channel-' * english + '-Kanava-' * finnish + str(counter) + '_-23_LUFS.' + output_format_for_final_file
						list_of_filenames.append(split_channel_targetfile_name)

				else:
					# In this case the output file will be a single file.
					# Create output filename for the machine readable readable results file.
					list_of_filenames.append(str(filename_and_extension[0] + '_-23_LUFS.' + output_format_for_final_file))

				# Get values stored for machine readable results file, and complete loudness result information for the file.
				if filename in temp_loudness_results_for_automation:

					original_file_name, list_of_values =  temp_loudness_results_for_automation[filename]

					# list_of_values[0] = number_of_this_mix # This value is already correct and we don't need to change it.
					# list_of_values[1] = total_number_of_supported_mixes_in_original_file # This value is already correct and we don't need to change it.
					# list_of_values[2] = total_number_of_mixes_in_original_file # This value is already correct and we don't need to change it.
					list_of_values[3] = create_loudness_corrected_files
					list_of_values[4] = number_of_files_in_this_mix
					list_of_values[5] = integrated_loudness
					list_of_values[6] = loudness_range
					list_of_values[7] = highest_peak_db
					list_of_values[8] = channel_count
					list_of_values[9] = sample_rate
					list_of_values[10] = bit_depth
					list_of_values[11] = audio_duration

					# If some subprocess has already stored an error_code or error_message, then don't change them.
					if list_of_values[12] == 0:
						list_of_values[12] = error_code
					if list_of_values[13] == '':
						list_of_values[13] = error_message

					list_of_values[14] = list_of_filenames

					temp_loudness_results_for_automation[filename] = [original_file_name, list_of_values]

					# If there are unsupported mixes in the mxf - file and remixing is on, warn the user about unpredictable results.
					if list_of_values[12] == 9:
						warning_message = warning_message + '\\nWarning: ' + list_of_values[13] * english + '\\nVaroitus: Lähdetiedostossa on ei-tuettuja audioraitoja, remix - toiminto voi tuottaa epätoivottuja tuloksia' * finnish

			else:
				# An error has happened in the loudness caculation, so there are no results, we leave the default dymmy values as they are and insert error number and message and append an empty list of filenames to the results.
				temp_loudness_results_for_automation[filename][1][12] = error_code
				temp_loudness_results_for_automation[filename][1][13] = error_message
				temp_loudness_results_for_automation[filename][1][14] = list_of_filenames

		# If file size exceeds 4 GB, a warning message must be displayed informing the user that the
		# outputfile will either be split to separate mono channels or stored in flac - format.
		if output_format_for_intermediate_files != output_format_for_final_file:
			# The combined channels in final output file exceeds the max file size and the file needs to be split to separate mono files.
			warning_message = warning_message + '\\nWarning: file size exceeds wav format max limit 4 GB, audio channels will be split to separate mono files' * english + '\\nVaroitus: tiedoston koko ylittää wav - formaatin maksimin (4 GB), kanavat jaetaan erillisiin tiedostoihin' * finnish
		if output_format_for_final_file == 'flac':
			# File is so big that even separate mono channels would exceed 4GB each, so flac format must be used for the output file.
			warning_message = warning_message + '\\nWarning: file size exceeds wav format max limit 4 GB, file will be stored in flac - format' * english + '\\nVaroitus: tiedoston koko ylittää wav - formaatin maksimin (4 GB), tiedosto tallennetaan flac - formaattiin' * finnish
		
		# Generate gnuplot commands needed for plotting the graphics file and store commands in a list.
		if (integrated_loudness_calculation_error == True) or (timeslice_calculation_error == True) or (sox_encountered_an_error == True):
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

			if sox_encountered_an_error == True:
				error_message_to_print_with_gnuplot = error_message_to_print_with_gnuplot + sox_error_message + '\\n'
			
			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('create_loudness_history_graphics_files')
				debug_information_list.append(create_loudness_history_graphics_files)
				debug_information_list.append('gnuplot_commands')
				debug_information_list.append(gnuplot_commands)
				debug_information_list.append('error_message')
				debug_information_list.append(error_message)
				debug_information_list.append('create_loudness_corrected_files')
				debug_information_list.append(create_loudness_corrected_files)
				unix_time_in_ticks, realtime = get_realtime(english, finnish)
				debug_information_list.append('Stop Time')
				debug_information_list.append(unix_time_in_ticks)
				debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list
			
			create_gnuplot_commands_for_error_message(error_message_to_print_with_gnuplot, filename, directory_for_temporary_files, directory_for_results, english, finnish)		
		else:
			
			# Loudness calculation succeeded.

			if create_loudness_history_graphics_files == True:

				peak_measurement_string_english = '\\nSample peak: '
				peak_measurement_string_finnish = '\\nHuipputaso: '

				peak_measurement_unit = 'dBFS'

				if peak_measurement_method == '--peak=true':
					peak_measurement_string_english = '\\nTruePeak: '
					peak_measurement_string_finnish = peak_measurement_string_english
					peak_measurement_unit = 'dBTP'

				# Generate gnuplot commands for plotting the graphics. Put all gnuplot commands in a list.
				gnuplot_commands=['set terminal jpeg size 1280,960 medium font \'arial\'', \
				'set output ' + '\"' + gnuplot_temporary_output_graphicsfile.replace('"','\\"') + '\"', \
				'set yrange [ 0 : -60 ] noreverse nowriteback', \
				'set grid', \
				'set title ' + '\"\'' + filename.replace('_', ' ').replace('"','\\"') + '\'\\n' + 'Integrated Loudness ' * english + 'Keskimääräinen Äänekkyystaso ' * finnish + str(integrated_loudness) + ' LUFS\\n ' + difference_from_target_loudness_string + ' LU from target loudness (-23 LUFS)\\nLoudness Range (LRA) ' * english + ' LU:ta tavoitetasosta (-23 LUFS)\\nÄänekkyyden vaihteluväli (LRA) '  * finnish + str(loudness_range) + ' LU' + peak_measurement_string_english * english + peak_measurement_string_finnish * finnish + highest_peak_db_string + ' ' + peak_measurement_unit + warning_message + '\"', \
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
					if silent == False:
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
					if silent == False:
						print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
					sys.exit(0)
				except IOError as reason_for_error:
					error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('create_loudness_history_graphics_files')
				debug_information_list.append(create_loudness_history_graphics_files)
				debug_information_list.append('gnuplot_commands')
				debug_information_list.append(gnuplot_commands)
				debug_information_list.append('error_message')
				debug_information_list.append(error_message)
				debug_information_list.append('create_loudness_corrected_files')
				debug_information_list.append(create_loudness_corrected_files)
				unix_time_in_ticks, realtime = get_realtime(english, finnish)
				debug_information_list.append('Stop Time')
				debug_information_list.append(unix_time_in_ticks)
				debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

			# Call a subprocess to run gnuplot
			if create_loudness_history_graphics_files == True:
				run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish)

			# Call a subprocess to create the loudness corrected audio file.
			if create_loudness_corrected_files == True:
				create_sox_commands_for_loudness_adjusting_a_file(integrated_loudness_calculation_error, difference_from_target_loudness, filename, english, finnish, hotfolder_path, directory_for_results, directory_for_temporary_files, highest_peak_db, flac_compression_level, output_format_for_intermediate_files, output_format_for_final_file, channel_count, audio_channels_will_be_split_to_separate_mono_files, output_file_too_big_to_split_to_separate_wav_channels)

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'create_gnuplot_commands'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish):
	
	# This subroutine is run when there has been some kind of error and the user needs to know about it.
	# This subroutine creates the gnuplot commands needed to create a graphics file explaining the error to user.

	try:
		commandfile_for_gnuplot = directory_for_temporary_files + os.sep + filename + '-gnuplot_commands'
		loudness_calculation_table = directory_for_temporary_files + os.sep + filename + '-loudness_calculation_table'
		gnuplot_temporary_output_graphicsfile = directory_for_temporary_files + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish

		gnuplot_commands = []
		global create_loudness_history_graphics_files
		global silent
		

		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_all_file_processing_information

			if filename in debug_temporary_dict_for_all_file_processing_information:
				debug_information_list = debug_temporary_dict_for_all_file_processing_information[filename]
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('create_gnuplot_commands_for_error_message')
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		# Write 4 coordinates to gnuplot data file. These 4 coordinates are used to draw a big red cross on the error graphics file.
		if create_loudness_history_graphics_files == True:

			try:
				with open(loudness_calculation_table, 'wt') as timeslice_file_handler:
					timeslice_file_handler.write('1.0\n' + '10\n' + '\n' + '\n' + '10\n' + '1.0\n')
					timeslice_file_handler.flush() # Flushes written data to os cache
					os.fsync(timeslice_file_handler.fileno()) # Flushes os cache to disk
			except KeyboardInterrupt:
				if silent == False:
					print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error opening gnuplot datafile for writing error graphics data ' * english + 'Gnuplotin datatiedoston avaaminen virhegrafiikan datan kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error opening gnuplot datafile for writing error graphics data ' * english + 'Gnuplotin datatiedoston avaaminen virhegrafiikan datan kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])

			# Create gnuplot commands and put them in  a list.
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
				if silent == False:
					print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])

		# Save some debug information.
		if debug_file_processing == True:
			debug_information_list.append('create_loudness_history_graphics_files')
			debug_information_list.append(create_loudness_history_graphics_files)
			debug_information_list.append('gnuplot_commands')
			debug_information_list.append(gnuplot_commands)
			debug_information_list.append('error_message')
			debug_information_list.append(error_message)
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		# Call a subprocess to run gnuplot
		if create_loudness_history_graphics_files == True:
			run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish)

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'create_gnuplot_commands_for_error_message'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)
	
def run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish):

	# This subroutine runs Gnuplot and generates a graphics file.
	# Gnuplot output is searched for error messages.
	results_from_gnuplot_run = b''

	try:
		commandfile_for_gnuplot = directory_for_temporary_files + os.sep + filename + '-gnuplot_commands'
		loudness_calculation_table = directory_for_temporary_files + os.sep + filename + '-loudness_calculation_table'
		gnuplot_temporary_output_graphicsfile = directory_for_temporary_files + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish
		gnuplot_output_graphicsfile = directory_for_results + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish

		global silent
		error_message = ''

		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_all_file_processing_information

			if filename in debug_temporary_dict_for_all_file_processing_information:
				debug_information_list = debug_temporary_dict_for_all_file_processing_information[filename]
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('run_gnuplot')
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

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
			error_message = 'Error deleting gnuplot stdout - file ' * english + 'Gnuplotin stdout - tiedoston deletoiminen epäonnistui ' * finnish	+ str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error deleting gnuplot stdout - file ' * english + 'Gnuplotin stdout - tiedoston deletoiminen epäonnistui ' * finnish	+ str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
			
		# If gnuplot outputs something, there was an error. Send this message to user.
		if not len(results_of_gnuplot_run_list) == 0:
			error_message = 'ERROR !!! Plotting graphics with Gnuplot, ' * english + 'VIRHE !!! Grafiikan piirtämisessä Gnuplotilla, ' * finnish + ' ' + filename + ' : ' + results_of_gnuplot_run_list
			send_error_messages_to_screen_logfile_email(error_message, [])

		# Save some debug information.
		if debug_file_processing == True:
			debug_information_list.append('error_message')
			debug_information_list.append(error_message)
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		# Remove time slice and gnuplot command files and move graphics file to results directory.
		try:
			os.remove(commandfile_for_gnuplot)
			os.remove(loudness_calculation_table)
		except KeyboardInterrupt:
			if silent == False:
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
			if silent == False:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error moving gnuplot graphics file ' * english + 'Gnuplotin grafiikkatiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error moving gnuplot graphics file ' * english + 'Gnuplotin grafiikkatiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'run_gnuplot'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def create_sox_commands_for_loudness_adjusting_a_file(integrated_loudness_calculation_error, difference_from_target_loudness, filename, english, finnish, hotfolder_path, directory_for_results, directory_for_temporary_files, highest_peak_db, flac_compression_level, output_format_for_intermediate_files, output_format_for_final_file, channel_count, audio_channels_will_be_split_to_separate_mono_files, output_file_too_big_to_split_to_separate_wav_channels):

	'''This subroutine creates sox commands that are used to create a loudness corrected file'''

	# This subroutine works like this:
	# ---------------------------------
	# The process gets the difference from target loudness as it's argument.
	# The process creates sox commands and starts sox using the difference as gain parameter and creates a loudness corrected wav.
	# The corrected file is written to temporary directory and when ready moved to the target directory for the user to see. This prevents user from using an incomplete file by accident.
	# If ouput files uncompressed size would exceed wav 4 GB limit, then the file is split into individual mono files. If individual size of these mono channels would still exceed 4 GB then flac or another suitable codec is used.

	try:
		# Assing some values to variables.
		integrated_loudness_calculation_results_list = []
		file_to_process = hotfolder_path + os.sep + filename
		filename_and_extension = os.path.splitext(filename)
		sox_encountered_an_error = False
		global integrated_loudness_calculation_results
		global libebur128_path
		global silent
		global temp_loudness_results_for_automation
		global write_loudness_calculation_results_to_a_machine_readable_file
		
		error_message = ''
		
		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_all_file_processing_information

			if filename in debug_temporary_dict_for_all_file_processing_information:
				debug_information_list = debug_temporary_dict_for_all_file_processing_information[filename]
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('create_sox_commands_for_loudness_adjusting_a_file')
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		# Create loudness corrected file if there were no errors in loudness calculation.
		if (integrated_loudness_calculation_error == False):
			
			# Assing some values to variables.
			# Output format for files has been already been decided in subroutine: get_audiofile_info_with_sox_and_determine_output_format. Output format is wav for files of 4 GB or less and flac for very large files that can't be split to separate wav files.
			combined_channels_targetfile_name = filename_and_extension[0] + '_-23_LUFS.' + output_format_for_final_file
			temporary_peak_limited_targetfile = filename_and_extension[0] + '-Peak_Limited.' + output_format_for_intermediate_files
			difference_from_target_loudness_sign_inverted = difference_from_target_loudness * -1 # The sign (+/-) of the difference from target loudness needs to be flipped for sox. Plus becomes minus and vice versa.
			
			start_of_sox_commandline = ['sox']
			
			# Set the absolute peak level for the resulting corrected audio file.
			# If sample peak is used for the highest value, then set the absolute peak to be -4 dBFS (resulting peaks will be about 1 dB higher than this).
			# If TruePeak calculations are used to measure highest peak, then set the maximum peak level to -2 dBFS (resulting peaks will be about 1 dB higher than this).
			audio_peaks_absolute_ceiling = -4
			if peak_measurement_method == '--peak=true':
				audio_peaks_absolute_ceiling = -2
			
			# Calculate the level where absolute peaks must be limited to before gain correction, to get the resulting max peak level we want.
			hard_limiter_level = difference_from_target_loudness + audio_peaks_absolute_ceiling
			
			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('combined_channels_targetfile_name')
				debug_information_list.append(combined_channels_targetfile_name)
				debug_information_list.append('temporary_peak_limited_targetfile')
				debug_information_list.append(temporary_peak_limited_targetfile)
				debug_information_list.append('difference_from_target_loudness')
				debug_information_list.append(difference_from_target_loudness)
				debug_information_list.append('difference_from_target_loudness_sign_inverted')
				debug_information_list.append(difference_from_target_loudness_sign_inverted)
				debug_information_list.append('audio_peaks_absolute_ceiling')
				debug_information_list.append(audio_peaks_absolute_ceiling)
				debug_information_list.append('hard_limiter_level')
				debug_information_list.append(hard_limiter_level)

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
					sox_commandline.extend(start_of_sox_commandline)
					sox_commandline.append(file_to_process)
					
					# If output format is flac add flac compression level commands right after the input file name.
					if output_format_for_final_file == 'flac':
						sox_commandline.extend(flac_compression_level)
					sox_commandline.extend([directory_for_temporary_files + os.sep + combined_channels_targetfile_name, 'gain', str(difference_from_target_loudness_sign_inverted)])
					
					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('sox_commandline')
						debug_information_list.append(sox_commandline)
					
					#Gather all names of processed files to a list.
					list_of_filenames = [combined_channels_targetfile_name]
					
					# Run sox with the commandline compiled in the lines above.
					sox_encountered_an_error = run_sox(directory_for_temporary_files, directory_for_results, filename, sox_commandline, english, finnish, 0, 0)
				
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
					
					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('list_of_sox_commandlines')
						debug_information_list.append(''.join(str(list_of_sox_commandlines)))
					
					# Run several sox commands in parallel threads, this speeds up splitting the file to separate mono files.	
					sox_encountered_an_error = run_sox_commands_in_parallel_threads(directory_for_temporary_files, directory_for_results, filename, list_of_sox_commandlines, english, finnish)
				
				# Processing is ready move audio files to target directory.
				move_processed_audio_files_to_target_directory(directory_for_temporary_files, directory_for_results, list_of_filenames, english, finnish)
			
			if difference_from_target_loudness < 0:
				
				##################################################################################################
				# Create loudness corrected file. In this case volume is adjusted up so limiting might be needed #
				##################################################################################################
				
				if highest_peak_db + difference_from_target_loudness_sign_inverted > audio_peaks_absolute_ceiling:
					
					#########################################################################################################################
					# Peaks will exceed our upper peak limit defined in 'audio_peaks_absolute_ceiling'. Create a peak limited file with sox #
					# After this the loudness of the file needs to be recalculated								#
					#########################################################################################################################
					
					sox_commandline = []
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
					sox_commandline.extend(start_of_sox_commandline)
					sox_commandline.append(file_to_process)
					# If output format is flac add flac compression level commands right after the input file name.
					if output_format_for_intermediate_files == 'flac':
						sox_commandline.extend(flac_compression_level)
					sox_commandline.extend([directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile])
					sox_commandline.extend(compander_1)
					sox_commandline.extend(compander_2)
					sox_commandline.extend(compander_3)
					sox_commandline.extend(hard_limiter)
					
					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('sox_commandline')
						debug_information_list.append(sox_commandline)

					# Run sox with the commandline compiled in the lines above.
					sox_encountered_an_error = run_sox(directory_for_temporary_files, directory_for_results, filename, sox_commandline, english, finnish, 0, 0)

					# If there has been an error in processing the file with sox then stop processing this file.
					if sox_encountered_an_error == False:
					
						########################################################################################
						# Loudness of the peak limited file needs to be calculated again, measure the loudness #
						########################################################################################

						# Save some debug information.
						if debug_file_processing == True:
							unix_time_in_ticks, realtime = get_realtime(english, finnish)
							debug_information_list.append('Start Time')
							debug_information_list.append(unix_time_in_ticks)
							debug_information_list.append('Subprocess Name')
							debug_information_list.append('create_sox_commands_for_loudness_adjusting_a_file: integrated measurements after peak-limiting ')
						
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
						integrated_loudness_calculation_error = integrated_loudness_calculation_results_list[3]
						integrated_loudness_calculation_error_message = integrated_loudness_calculation_results_list[4]
						highest_peak_db = integrated_loudness_calculation_results_list[5]
						sox_commandline = []
						list_of_sox_commandlines = []
						list_of_filenames = []
						
						# Save some debug information.
						if debug_file_processing == True:
							debug_information_list.append('difference_from_target_loudness')
							debug_information_list.append(difference_from_target_loudness)
							debug_information_list.append('difference_from_target_loudness_sign_inverted')
							debug_information_list.append(difference_from_target_loudness_sign_inverted)
							debug_information_list.append('peak_measurement_method ')
							debug_information_list.append(peak_measurement_method )
							debug_information_list.append('highest_peak_db')
							debug_information_list.append(highest_peak_db)
							unix_time_in_ticks, realtime = get_realtime(english, finnish)
							debug_information_list.append('Stop Time')
							debug_information_list.append(unix_time_in_ticks)
							debug_information_list.append('Subprocess Name')
							debug_information_list.append('create_sox_commands_for_loudness_adjusting_a_file: integrated measurements after peak-limiting ')

							# Remove debug data about integrated loudness measurement of temporary peak limited file since this data is already appended to debug dictionary by the lines above.
							del debug_temporary_dict_for_integrated_loudness_calculation_information[temporary_peak_limited_targetfile]

						if integrated_loudness_calculation_error == True:

							# Print error message on result graphics file
							error_message = 'ERROR !!! in integrated loudness calculation while measuring the peak limited file: ' * english + 'VIRHE !!! keskimääräisen äänekkyyden laskennassa, kun huippulimitoitua tiedostoa käsiteltiin: ' * finnish + integrated_loudness_calculation_error_message
							create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish)

							if write_loudness_calculation_results_to_a_machine_readable_file == True:

								if filename in temp_loudness_results_for_automation:

									# An error has happened.
									error_code = 2

									temp_loudness_results_for_automation[filename][1][4] = 0 # number_of_files_in_this_mix
									temp_loudness_results_for_automation[filename][1][12] = error_code
									temp_loudness_results_for_automation[filename][1][13] = error_message
									temp_loudness_results_for_automation[filename][1][14] = []

					# If there has been an error then stop processing this file.
					if (sox_encountered_an_error == False) and (integrated_loudness_calculation_error == False):

						if audio_channels_will_be_split_to_separate_mono_files == False:
						
							# Gather sox commandline to a list.
							sox_commandline.extend(start_of_sox_commandline)
							sox_commandline.extend([directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile])
							
							# If output format is flac add flac compression level commands right after the input file name.
							if output_format_for_final_file == 'flac':
								sox_commandline.extend(flac_compression_level)
							sox_commandline.extend([directory_for_temporary_files + os.sep + combined_channels_targetfile_name, 'gain', str(difference_from_target_loudness_sign_inverted)])
							
							# Save some debug information.
							if debug_file_processing == True:
								debug_information_list.append('sox_commandline')
								debug_information_list.append(sox_commandline)
							
							#Gather all names of processed files to a list.
							list_of_filenames = [combined_channels_targetfile_name]
							
							# Run sox with the commandline compiled in the lines above.
							sox_encountered_an_error = run_sox(directory_for_temporary_files, directory_for_results, filename, sox_commandline, english, finnish, 0, 0)
						
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
								
							# Save some debug information.
							if debug_file_processing == True:
								debug_information_list.append('list_of_sox_commandlines')
								debug_information_list.append(''.join(str(list_of_sox_commandlines)))

							# Run several sox commands in parallel threads, this speeds up splitting the file to separate mono files.	
							sox_encountered_an_error = run_sox_commands_in_parallel_threads(directory_for_temporary_files, directory_for_results, filename, list_of_sox_commandlines, english, finnish)
						
						# Processing is ready move audio files to target directory.
						move_processed_audio_files_to_target_directory(directory_for_temporary_files, directory_for_results, list_of_filenames, english, finnish)
				
				else:
					
					#######################################################################################################################
					# Volume of the file needs to be adjusted up, but peaks will not exceed our upper limit so no peak limiting is needed #
					# Create loudness corrected file										      #
					#######################################################################################################################
					
					sox_commandline = []
					list_of_sox_commandlines = []
					list_of_filenames = []
					
					if audio_channels_will_be_split_to_separate_mono_files == False:
						# Gather sox commandline to a list.
						sox_commandline.extend(start_of_sox_commandline)
						sox_commandline.append(file_to_process)
						# If output format is flac add flac compression level commands right after the input file name.
						if output_format_for_final_file == 'flac':
							sox_commandline.extend(flac_compression_level)
						sox_commandline.extend([directory_for_temporary_files + os.sep + combined_channels_targetfile_name, 'gain', str(difference_from_target_loudness_sign_inverted)])
						
						# Save some debug information.
						if debug_file_processing == True:
							debug_information_list.append('sox_commandline')
							debug_information_list.append(sox_commandline)
						
						#Gather all names of processed files to a list.
						list_of_filenames = [combined_channels_targetfile_name]
						
						# Run sox with the commandline compiled in the lines above.
						sox_encountered_an_error = run_sox(directory_for_temporary_files, directory_for_results, filename, sox_commandline, english, finnish, 0, 0)
						
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
						
						# Save some debug information.
						if debug_file_processing == True:
							debug_information_list.append('list_of_sox_commandlines')
							debug_information_list.append(''.join(str(list_of_sox_commandlines)))
						
						# Run several sox commands in parallel threads, this speeds up splitting the file to separate mono files.	
						sox_encountered_an_error = run_sox_commands_in_parallel_threads(directory_for_temporary_files, directory_for_results, filename, list_of_sox_commandlines, english, finnish)
					
					# Processing is ready move audio files to target directory.
					move_processed_audio_files_to_target_directory(directory_for_temporary_files, directory_for_results, list_of_filenames, english, finnish)
			
			# If the temporary peak limited file is there, delete it.
			if os.path.exists(directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile):
				try:
					os.remove(directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile)
				except KeyboardInterrupt:
					if silent == False:
						print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
					sys.exit(0)
				except IOError as reason_for_error:
					error_message = 'Error deleting temporary peak limited file ' * english + 'Väliaikaisen limitoidun tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error deleting temporary peak limited file ' * english + 'Väliaikaisen limitoidun tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
		
		# Save some debug information.
		if debug_file_processing == True:
			debug_information_list.append('error_message')
			debug_information_list.append(error_message)
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'create_sox_commands_for_loudness_adjusting_a_file'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def run_sox_commands_in_parallel_threads(directory_for_temporary_files, directory_for_results, filename, list_of_sox_commandlines, english, finnish):

	try:
		list_of_sox_commandlines.reverse()
		number_of_allowed_simultaneous_sox_processes = 10
		events_for_sox_commands_currently_running = {}
		list_of_finished_processes = []
		sox_encountered_an_error = False

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
					event_for_sox_processing = threading.Event() # Create a unique event for the process. This event is used to signal that this process has finished.
					# When the process is ready the state of this event tells us if sox encountered an error or not. if event.set == True then there was no error.
					event_for_sox_processing_encountered_an_error = threading.Event() 

					# Add the event to the list of running sox processes.
					events_for_sox_commands_currently_running[event_for_sox_processing] = event_for_sox_processing_encountered_an_error
					
					# Create a thread for the sox proces.
					sox_process = threading.Thread(target=run_sox, args=(directory_for_temporary_files, directory_for_results, filename, sox_commandline, english, finnish, event_for_sox_processing, event_for_sox_processing_encountered_an_error)) # Create a process instance.
					
					# Start sox thread.
					sox_process.start() # Start the calculation process in it's own thread.
				
				# If all sox commandlines has been used, then break out of the loop.
				if len(list_of_sox_commandlines) == 0:
					break
				
			###################################
			# Find threads that have finished #
			###################################
			
			list_of_finished_processes=[]
			
			for sox_process_is_ready in events_for_sox_commands_currently_running:

				if sox_process_is_ready.is_set(): # Check if event is set.
					list_of_finished_processes.append(sox_process_is_ready) # Add event of finished thread to a list.
					sox_event_for_error = events_for_sox_commands_currently_running[sox_process_is_ready]

					# If running sox was not succesful then the other event is not set, test for it.
					if not sox_event_for_error.is_set():
						sox_encountered_an_error = True

			# If a thread has finished, remove it's event from the dictionary of files being processed.
			for item in list_of_finished_processes: # Get events who's processing threads have completed.
				del events_for_sox_commands_currently_running[item] # Remove the events from the dictionary of files currently being calculated upon.
			
			# If processing with sox was not succesful, then stop all prosessing and inform the calling subroutine.
			if sox_encountered_an_error == True:
				break

			# Wait 1 second before running the loop again
			time.sleep(1)
	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'run_sox_commands_in_parallel_threads'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	return(sox_encountered_an_error)

def run_sox(directory_for_temporary_files, directory_for_results, filename, sox_commandline, english, finnish, event_for_sox_processing, event_for_sox_processing_encountered_an_error):

	try:
		we_are_part_of_a_multithread_sox_command = False
		sox_encountered_an_error = False
		error_message = ''
		global debug
		global write_loudness_calculation_results_to_a_machine_readable_file
		global temp_loudness_results_for_automation
		
		# Test if the value in variable is an event or not. If it is an event, then there are other sox threads processing the same file.
		variable_type_string = str(type(event_for_sox_processing))
		if 'Event' in variable_type_string:
			we_are_part_of_a_multithread_sox_command = True
		
		# Define filename for the temporary file that we are going to use as stdout for the external command.
		results_from_sox_run = b''
		stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_sox_stdout.txt'
		
		# If there are other sox threads processing this same file, then our stdout filename must be unique.
		if we_are_part_of_a_multithread_sox_command == True:
			stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '-event-' + str(event_for_sox_processing).split(' ')[3].strip('>') + '_sox_stdout.txt'
			
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
			error_message = 'Error deleting sox stdout - file ' * english + 'Soxin stdout - tiedoston deletoiminen epäonnistui ' * finnish	+ str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error deleting sox stdout - file ' * english + 'Soxin stdout - tiedoston deletoiminen epäonnistui ' * finnish	+ str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		# If sox did output something, there was and error. Print message to user.
		if not len(results_from_sox_run_list) == 0:
			sox_encountered_an_error = True

			for item in results_from_sox_run_list:
				error_message = 'Sox error: ' * english + 'Sox virhe: ' * finnish + ' ' + filename + ': ' + item
				send_error_messages_to_screen_logfile_email(error_message, [])
			
			# Print sox error message on result graphics file
			error_message = 'Sox error: ' * english + 'Sox virhe: ' * finnish + ' ' + item
			create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish)

			if write_loudness_calculation_results_to_a_machine_readable_file == True:

				if filename in temp_loudness_results_for_automation:

					# An error has happened in the loudness caculation, so there are no results, add information about the error for the file.
					error_code = 8

					temp_loudness_results_for_automation[filename][1][4] = 0 # number_of_files_in_this_mix
					temp_loudness_results_for_automation[filename][1][12] = error_code
					temp_loudness_results_for_automation[filename][1][13] = error_message
					temp_loudness_results_for_automation[filename][1][14] = []

				
		# If we recieved an event from the calling routine, then we need to set that event.
		# We recieved an event if the calling process runs several sox commands in parallel threads.
		# The variable holding the event, might have an event or the value 0. In the latter case there are no parallel threads and we don't need to change the value in the variable.
		
		# Set our event so that the calling process knows we are ready.
		if we_are_part_of_a_multithread_sox_command == True:
			event_for_sox_processing.set()

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'run_sox'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	# This subroutine can be called directly or from the subroutine 'run_sox_commands_in_parallel_threads'.
	# The routine 'create_sox_commands_for_loudness_adjusting_a_file' calls this routine directly if loudness corrected ouput audio channels do not need to be split to separate mono files.
	#
	# This routine is called through subroutine 'run_sox_commands_in_parallel_threads' when loudness corrected output audio must be split to separate channels, and
	# when we remix audio files found in a mxf - file before loudness processing. In these cases a single instance of this subroutine is part of a multipart sox job running in several threads.
	#
	# We need to communicate back to the calling subroutine if we succeeded or not and this needs to be done differently depending on if we were called directly or are running as a thread.
	# If we were started as a thread then we set an event if we succeeded, if we were called directly then we return True / False as the value of variable 'sox_encountered_an_error'.
	if we_are_part_of_a_multithread_sox_command == True:
		if sox_encountered_an_error == False:
			event_for_sox_processing_encountered_an_error.set()
		return
	else:
		return(sox_encountered_an_error)

def move_processed_audio_files_to_target_directory(source_directory, target_directory, list_of_filenames, english, finnish):

	try:
		global silent

		for filename in list_of_filenames:
			# Check if file exists and move it to results folder.
			if os.path.exists(source_directory + os.sep + filename):
				# There were no errors, and loudness corrected file is ready, move it from temporary directory to results directory.
				try:
					shutil.move(source_directory + os.sep + filename, target_directory + os.sep + filename)
				except KeyboardInterrupt:
					if silent == False:
						print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
					sys.exit(0)
				except IOError as reason_for_error:
					error_message = 'Error moving loudness adjusted file ' * english + 'Äänekkyyskorjatun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error moving loudness adjusted file ' * english + 'Äänekkyyskorjatun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'move_processed_audio_files_to_target_directory'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def get_audiofile_info_with_sox_and_determine_output_format(directory_for_temporary_files, hotfolder_path, filename):
	
	# This subroutine gets audio file information with sox and determines based on estimated uncompressed file size what the output file format is.
	# There is only one audio stream in files that this subroutine processes.
	
	try:
		# Read audio file technical info with sox
		channel_count_string = ''
		sample_rate_string = ''
		bit_depth_string = ''
		sample_count_string = ''
		channel_count = 0
		sample_rate = 0
		bit_depth = 8
		sample_count = 0
		audio_duration = 0
		file_to_process = hotfolder_path + os.sep + filename
		estimated_uncompressed_size_for_single_mono_file = 0
		estimated_uncompressed_size_for_combined_channels = 0
		global wav_format_maximum_file_size
		flac_compression_level = ['-C', '1']
		output_format_for_intermediate_files = 'wav'
		output_format_for_final_file = 'wav'
		sox_encountered_an_error = False
		sox_error_message = ''
		results_from_sox_run = b''
		
		error_message = ''
		
		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_all_file_processing_information

			if filename in debug_temporary_dict_for_all_file_processing_information:
				debug_information_list = debug_temporary_dict_for_all_file_processing_information[filename]
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('get_audiofile_info_with_sox_and_determine_output_format')
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list
		
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
		channel_count = 0
		sample_rate = 0
		bit_depth = 0
		sample_count = 0
		
		if channel_count_string.isnumeric() == True:
			channel_count = int(channel_count_string)
		else:
			error_message = 'ERROR !!! I could not parse sox channel count string: ' * english + 'VIRHE !!! En osannut tulkita sox:in antamaa tietoa kanavamäärästä: ' * finnish + '\'' + channel_count_string + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
			sox_encountered_an_error = True
			sox_error_message = error_message

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('error_message')
				debug_information_list.append(error_message)

			send_error_messages_to_screen_logfile_email(error_message, [])

		if sample_rate_string.isnumeric() == True:
			sample_rate = int(sample_rate_string)
		else:
			error_message = 'ERROR !!! I could not parse sox sample rate string: ' * english + 'VIRHE !!! En osannut tulkita sox:in antamaa tietoa näyteenottotaajuudesta: ' * finnish + '\'' + sample_rate_string + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
			sox_encountered_an_error = True
			sox_error_message = error_message

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('error_message')
				debug_information_list.append(error_message)

			send_error_messages_to_screen_logfile_email(error_message, [])

		if bit_depth_string.isnumeric() == True:
			bit_depth = int(bit_depth_string)
		else:
			error_message = 'ERROR !!! I could not parse sox bit depth string: ' * english + 'VIRHE !!! En osannut tulkita sox:in antamaa tietoa bittisyvyydestä: ' * finnish + '\'' + bit_depth_string + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
			sox_encountered_an_error = True
			sox_error_message = error_message

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('error_message')
				debug_information_list.append(error_message)

			send_error_messages_to_screen_logfile_email(error_message, [])

		if sample_count_string.isnumeric() == True:
			sample_count = int(sample_count_string)
		else:
			error_message = 'ERROR !!! I could not parse sox sample count string: ' * english + 'VIRHE !!! En osannut tulkita sox:in antamaa tietoa näytteiden lukumäärästä: ' * finnish + '\'' + sample_count_string + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
			sox_encountered_an_error = True
			sox_error_message = error_message

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('error_message')
				debug_information_list.append(error_message)

			send_error_messages_to_screen_logfile_email(error_message, [])


		# Prevent 'division by zero' error by only doing the calculation if both values are greater than zero.
		if (sample_count != 0) and (sample_rate != 0):
			# Calculate file duration from sample count.
			audio_duration = int(sample_count / sample_rate)

		if not os.path.exists(file_to_process): # Check if the audio file still exists, user may have deleted it. If True start loudness calculation.
			error_message = 'Sox: Error accessing file' * english + 'Sox: Tiedoston lukemisessa tapahtui virhe' * finnish 
			sox_encountered_an_error = True
			sox_error_message = error_message

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('error_message')
				debug_information_list.append(error_message)

		
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

		# Save some debug information.
		if debug_file_processing == True:
			debug_information_list.append('channel_count_string')
			debug_information_list.append(channel_count_string)
			debug_information_list.append('sample_rate_string')
			debug_information_list.append(sample_rate_string)
			debug_information_list.append('bit_depth_string')
			debug_information_list.append(bit_depth_string)
			debug_information_list.append('sample_count_string')
			debug_information_list.append(sample_count_string)
			debug_information_list.append('audio_duration')
			debug_information_list.append(audio_duration)
			debug_information_list.append('sox_encountered_an_error')
			debug_information_list.append(sox_encountered_an_error)
			debug_information_list.append('sox_error_message')
			debug_information_list.append(sox_error_message)
			debug_information_list.append('wav_format_maximum_file_size')
			debug_information_list.append(wav_format_maximum_file_size)
			debug_information_list.append('estimated_uncompressed_size_for_single_mono_file')
			debug_information_list.append(estimated_uncompressed_size_for_single_mono_file)
			debug_information_list.append('estimated_uncompressed_size_for_combined_channels')
			debug_information_list.append(estimated_uncompressed_size_for_combined_channels)
			debug_information_list.append('output_format_for_intermediate_files')
			debug_information_list.append(output_format_for_intermediate_files)
			debug_information_list.append('output_format_for_final_file')
			debug_information_list.append(output_format_for_final_file)
			debug_information_list.append('audio_channels_will_be_split_to_separate_mono_files')
			debug_information_list.append(audio_channels_will_be_split_to_separate_mono_files)
			debug_information_list.append('output_file_too_big_to_split_to_separate_wav_channels')
			debug_information_list.append(output_file_too_big_to_split_to_separate_wav_channels)
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'get_audiofile_info_with_sox_and_determine_output_format'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	return(channel_count, sample_rate, bit_depth, sample_count, flac_compression_level, output_format_for_intermediate_files, output_format_for_final_file, audio_channels_will_be_split_to_separate_mono_files, audio_duration, output_file_too_big_to_split_to_separate_wav_channels, sox_encountered_an_error, sox_error_message)

def get_realtime(english, finnish):

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
	realtime = year + '.' + month + '.' + day + '_' + 'at' * english + 'klo' * finnish + '_' + hours + '.' + minutes + '.' + seconds

	return (unix_time_in_ticks, realtime)  

def decompress_audio_streams_with_ffmpeg(event_1_for_ffmpeg_audiostream_conversion, event_2_for_ffmpeg_audiostream_conversion, filename, file_format_support_information, hotfolder_path, directory_for_temporary_files, english, finnish):
	'''This subprocess decompresses all valid audiostreams from a file with ffmpeg'''

	# This subprocess works like this:
	# ---------------------------------
	# FFmpeg is started to extract all valid audio streams from the file.
	# The extracted files are losslessly compressed with flac to save disk space. (Flac also supports file sizes larger than 4 GB. Note: Flac compression routines in ffmpeg are based on flake and are much faster than the ones in the standard flac - command).
	# The resulting files are moved to the HotFolder so the program sees them as new files and queues them for loudness calculation.
	# The original file is queued for deletion.

	ffmpeg_run_output = b''

	try:
		global files_queued_for_deletion
		global silent
		global where_to_send_error_messages
		global directory_for_results
		global write_loudness_calculation_results_to_a_machine_readable_file
		global temp_loudness_results_for_automation
		error_message = ''
		
		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_all_file_processing_information

			if filename in debug_temporary_dict_for_all_file_processing_information:
				debug_information_list = debug_temporary_dict_for_all_file_processing_information[filename]
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('decompress_audio_streams_with_ffmpeg')
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list
		
		# In list 'file_format_support_information' we already have all the information FFmpeg was able to find about the valid audio streams in the file, assign all info to variables.
		natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames, mxf_audio_remixing, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, number_of_unsupported_streams_in_file = file_format_support_information
		
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

				# Save some debug information.
				if debug_file_processing == True:
					debug_information_list.append('error_message')
					debug_information_list.append(error_message)

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

		# If the audio streams we extracted came from a mxf - file and need to be remixed before processing, then call the remixing subroutine.
		if (mxf_audio_remixing == True) and (len(filenames_and_channel_counts_for_mxf_audio_remixing) > 0) and (len(audio_remix_channel_map) > 0):

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('Message')
				debug_information_list.append('Calling subroutine: remix_files_according_to_channel_map')

			list_of_files_to_move_to_loudness_processing = remix_files_according_to_channel_map(directory_for_temporary_files, filename, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, english, finnish)

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('Message')
				debug_information_list.append('Returned from subroutine: remix_files_according_to_channel_map')

			# Warn user if mxf - file remixing is on and there are some unsupported streams in the inputfile, since this can create unexpected results.
			if number_of_unsupported_streams_in_file > 0:

				error_code = 9
				error_message = 'There are unsupported audio streams in input MXF - file while remix function is on. This may create unwanted results'

				if write_loudness_calculation_results_to_a_machine_readable_file == True:

					for item in list_of_files_to_move_to_loudness_processing:

						temp_loudness_results_for_automation[item][1][12] = error_code
						temp_loudness_results_for_automation[item][1][13] = error_message

			# Delete all source files that are now remixed to new files, the original files are not needed any more.
			try:
				for item in target_filenames:

					if os.path.exists(directory_for_temporary_files + os.sep + item):
						os.remove(directory_for_temporary_files + os.sep + item)

			except IOError as reason_for_error:
				error_message = 'Error deleting file from temporary directory  ' * english + 'Tiedoston poistaminen väliaikaisten tiedostojen hakemistosta epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error deleting file from temporary directory  ' * english + 'Tiedoston poistaminen väliaikaisten tiedostojen hakemistosta epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])

			target_filenames = list_of_files_to_move_to_loudness_processing

		# Move each audio file we created from temporary directory to results directory.
		for item in target_filenames:
			try:
				shutil.move(directory_for_temporary_files + os.sep + item, hotfolder_path + os.sep + item)
			except KeyboardInterrupt:
				if silent == False:
					print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error moving ffmpeg decompressed file ' * english + 'FFmpeg:illä puretun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error moving ffmpeg decompressed file ' * english + 'FFmpeg:illä puretun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
		
		# Queue the original file for deletion. It is no longer needed since we have extracted all audio streams from it.
		if delete_original_file_immediately == True:
			files_queued_for_deletion.append(filename)
		
		# Save some debug information.
		if debug_file_processing == True:
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		# Set the events so that the main program can see that extracting audio streams from file is ready.
		event_1_for_ffmpeg_audiostream_conversion.set()
		event_2_for_ffmpeg_audiostream_conversion.set()

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'decompress_audio_streams_with_ffmpeg'

		# Set the events so that the main program can see that extracting audio streams from file is ready.
		event_1_for_ffmpeg_audiostream_conversion.set()
		event_2_for_ffmpeg_audiostream_conversion.set()

		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def send_error_messages_to_screen_logfile_email(error_message, send_error_messages_to_these_destinations):
	
	# This subroutine prints error messages to the screen or logfile or sends them by email.
	# The variable 'error_message' holds the actual message and the list 'where_to_send_error_messages' tells where to print / send them. The list can have any or all of these values: 'screen', 'logfile', 'email'.
	
	global error_messages_to_email_later_list # This variable is used to store messages that are later all sent by email in one go.
	global where_to_send_error_messages
	global error_logfile_path
	global silent
	error_message_with_timestamp = str(get_realtime(english, finnish)[1]) + '   ' + error_message # Add the current date and time at the beginning of the error message.
	
	# If the calling subroutine did not define where it wants us to send error messages then use global defaults.
	if send_error_messages_to_these_destinations == []:
		send_error_messages_to_these_destinations = where_to_send_error_messages
	
	# Print error messages to screen
	if silent == False:
		if 'screen' in send_error_messages_to_these_destinations:
			print('\033[7m' + '\r-------->	' + error_message_with_timestamp + '\033[0m')

	# Write error messages to a logfile
	if 'logfile' in send_error_messages_to_these_destinations:
		try:
			with open(error_logfile_path, 'at') as error_file_handler:
				error_file_handler.write(error_message_with_timestamp + '\n')
				error_file_handler.flush() # Flushes written data to os cache
				os.fsync(error_file_handler.fileno()) # Flushes os cache to disk
		except KeyboardInterrupt:
			if silent == False:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			exception_error_message = 'Error opening error logfile for writing ' * english + 'Virhe lokitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)

			if silent == False:
				print('\033[7m' + '\r-------->	' + exception_error_message + '\033[0m')

			error_messages_to_email_later_list.append(exception_error_message)
		except OSError as reason_for_error:
			exception_error_message = 'Error opening error logfile for writing ' * english + 'Virhe lokitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)

			if silent == False:
				print('\033[7m' + '\r-------->	' + exception_error_message + '\033[0m')

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
	global freelcs_version
	global critical_python_error_has_happened
	global quit_all_threads_now
	unix_time_in_ticks =float(0)
	realtime = ''
	
	error_messages_to_send = [] # Error messages are moved from the global list above to this local list.
	reason_for_failed_send = [] # If sending fails we store the reason for error in this variable and print it to the logfile.
	
	while True:
	
		# We are only allowed to send error messages periodically, sleep until the wait period is over.
		counter = 0
		wait_delay = 5

		while counter < email_sending_details['email_sending_interval']:
			time.sleep(wait_delay)
			counter = counter + wait_delay

			# If we have a crash somewhere causing an python interpreter error, stop waiting and send error messages immediately, because the important python error might be waiting to be sent.
			if critical_python_error_has_happened == True:
				critical_python_error_has_happened = False
				break

			# Check if the main routine asks us to exit now. This is used when running regression tests.
			if quit_all_threads_now == True:
				return()

		# The wait period is over, check if there are any new error messages in the list.
		error_messages_to_send = []
		message_text_string = ''
		
		machine_info = '\n\nLoudnessCorrection info:\n--------------------------------------\n' + 'Commandline: ' + ' '.join(sys.argv) + '\n' + 'IP-Addresses: ' + ', '.join(all_ip_addresses_of_the_machine) + '\n' + 'PID: ' + str(loudness_correction_pid) + '\n' + 'FreeLCS version: ' + freelcs_version + '\n\n'
		
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
				unix_time_in_ticks, realtime = get_realtime(english, finnish)
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
				reason_for_failed_send.append(realtime + '   Error sending email, Timeout error: ' + str(reason_for_error))
			except smtplib.socket.error as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, Socket error: ' + str(reason_for_error))
			except smtplib.SMTPRecipientsRefused as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, All recipients were refused: ' + str(reason_for_error))
			except smtplib.SMTPHeloError as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, The server didn’t reply properly to the HELO greeting: ' + str(reason_for_error))
			except smtplib.SMTPSenderRefused as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, The server didn’t accept the sender address: ' + str(reason_for_error))
			except smtplib.SMTPDataError as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, The server replied with an unexpected error code or The SMTP server refused to accept the message data: ' + str(reason_for_error))
			except smtplib.SMTPException as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, The server does not support the STARTTLS extension or No suitable authentication method was found: ' + str(reason_for_error))
			except smtplib.SMTPAuthenticationError as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, The server didn’t accept the username/password combination: ' + str(reason_for_error))
			except smtplib.SMTPConnectError as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, Error occurred during establishment of a connection with the server: ' + str(reason_for_error))
			except RuntimeError as reason_for_error:
				reason_for_failed_send.append(realtime + '   Error sending email, SSL/TLS support is not available to your Python interpreter: ' + str(reason_for_error))
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
						if silent == False:
							print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
						sys.exit(0)
					except IOError as reason_for_error:
						exception_error_message = 'Error opening error logfile for writing ' * english + 'Virhe lokitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
						if silent == False:
							print('\033[7m' + '\r-------->	' + exception_error_message + '\033[0m')
					except OSError as reason_for_error:
						exception_error_message = 'Error opening error logfile for writing ' * english + 'Virhe lokitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
						if silent == False:
							print('\033[7m' + '\r-------->	' + exception_error_message + '\033[0m')
				reason_for_failed_send = []

def write_html_progress_report_thread(english, finnish):
		
	'''This subprocess runs in it's own thread and periodically writes calculation queue information to disk in html format allowing the calculation queue progress to be monitored with a web browser'''

	try:
		global files_queued_to_loudness_calculation
		global loudness_calculation_queue
		global web_page_path
		global web_page_name
		global html_progress_report_write_interval
		global silent
		global quit_all_threads_now
		global freelcs_version
		global all_ip_addresses_of_the_machine
		
		while True:
			
			# Wait user defined number of seconds between updating the html-page.
			time.sleep(html_progress_report_write_interval)
			
			# Check if the main routine asks us to exit now. This is used when running regression tests.
			if quit_all_threads_now == True:
				return()

			loudness_correction_program_info_and_timestamps['write_html_progress_report'] = [write_html_progress_report, int(time.time())] # Update the heartbeat timestamp for the html writing thread. This is used to keep track if the thread has crashed.
			
			counter = 0
			html_code = [] # The finished html - page is stored in this list variable.
			realtime = get_realtime(english, finnish)[1] # Get the current date and time of day.
			
			# Create the start of the html page by putting the first static part of the html - code in to a list variable.
			server_string = 'Server ip-address: '

			if len(all_ip_addresses_of_the_machine) > 1:
				server_string = 'Server ip-addresses: '

			html_code_part_1 = ['<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">', \
			'<html><head>', \
			'<meta content="text/html; charset=ISO-8859-15" http-equiv="content-type">', \
			'<meta http-equiv="refresh" content="' + str(html_progress_report_write_interval) + '">', \
			'<META HTTP-EQUIV="PRAGMA" CONTENT="NO-CACHE">', \
			'<title>' + 'LoudnessCorrection_Process_Queue' * english + 'AanekkyysKorjauksen laskentajono' * finnish + '</title>', \
			'<h1>' + 'FreeLCS ' + freelcs_version + '</h1>', \
			'<h3>' + server_string + ', '.join(all_ip_addresses_of_the_machine) + '</h3>', \
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
			copy_of_completed_files_list = copy.deepcopy(completed_files_list)

			for filename in copy_of_completed_files_list:
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
				if silent == False:
					print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error opening loudness calculation queue html-file for writing ' * english + 'Laskentajonon html-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error opening loudness calculation queue html-file for writing ' * english + 'Laskentajonon html-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'write_html_progress_report_thread'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)
			
def write_to_heartbeat_file_thread():
	
	# This subprocess is started in its own thread and it periodically writes current time to the heartbeat - file.
	# An external program can monitor the heartbeat - file and do something if it stops updating (for example inform the admin or restart this program).

	try:
		global heartbeat_write_interval
		global web_page_path
		global heartbeat_file_name
		global loudness_correction_program_info_and_timestamps
		global english
		global finnish
		global silent
		global quit_all_threads_now

		while True:

			# Check if the main routine asks us to exit now. This is used when running regression tests.
			if quit_all_threads_now == True:
				return()

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
				if silent == False:
					print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error opening HeartBeat commandfile for writing ' * english + 'HeartBeat - tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error opening HeartBeat commandfile for writing ' * english + 'HeartBeat - tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except RuntimeError:
				# If the 'loudness_correction_program_info_and_timestamps' dictionary is changed by another thread in the middle of this thread writing it to disk, then a RuntimeError is raised and the save fails.
				# If save fails ignore it and try again after the wait period.
				pass

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'write_to_heartbeat_file_thread'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)
			
def debug_lists_and_dictionaries_thread():
	
	# This subprocess is started in its own thread.
	# This subroutine is used to write out the length and contents of lists and dictionaries this program uses.
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
	global ffmpeg_output_wrapper_format
	global write_html_progress_report
	global html_progress_report_write_interval
	global web_page_name
	global heartbeat
	global heartbeat_file_name
	global heartbeat_write_interval
	global where_to_send_error_messages
	global send_error_messages_to_logfile
	global send_error_messages_by_email
	global email_sending_details
	global debug_temporary_dict_for_integrated_loudness_calculation_information
	global debug_temporary_dict_for_timeslice_calculation_information
	global debug_temporary_dict_for_all_file_processing_information
	global debug_complete_final_information_for_all_file_processing_dict
	global all_settings_dict
	global freelcs_version
	global loudnesscorrection_version
	global temp_loudness_results_for_automation
	global final_loudness_results_for_automation
	global ffmpeg_executable_found
	global avconv_executable_found
	global ffmpeg_executable_name
	global peak_measurement_method
	global quit_all_threads_now
	global write_loudness_calculation_results_to_a_machine_readable_file
	global create_loudness_corrected_files
	global create_loudness_history_graphics_files
	global delete_original_file_immediately
	global unit_separator
	global record_separator
	global enable_mxf_audio_remixing
	global remix_map_file_extension
	global enable_all_nonfree_ffmpeg_wrapper_formats
	global enable_all_nonfree_ffmpeg_codec_formats
	global global_mxf_audio_remix_channel_map
	global ffmpeg_free_wrapper_formats
	global mxf_formats
	global mpeg_wrapper_formats
	global ffmpeg_allowed_wrapper_formats
	global ffmpeg_free_codec_formats
	global ffmpeg_allowed_codec_formats
	global os_name
	global os_version

	list_printouts = []
	list_printouts_old_values = []
	time_to_start_writing_to_a_new_file = int(time.time())
	real_time_string = get_realtime(english, finnish)[1]
	debug_messages_file = 'debug-variables_lists_and_dictionaries-' + real_time_string + '.txt'
	values_read_from_configfile = []
	file_name_expiry_time = 24 * 60 * 60 # This variable defines how often we change the log file name. By default it is changed every 24 hours (24 hours * 60 minutes * 60 seconds = 86400 seconds).
	
	# If LoudnessCorrection read config values from a file, then all_settings_dict is not empty.
	# Store values read from configfile to a list, so that the values can be saved at the beginning of the list and dictionary debug info file.
	if all_settings_dict != {}:

		# Store variables read from the configfile. This is useful for debugging settings previously saved in a file.
		title_text = 'FreeLCS version: ' + freelcs_version +  '\n\nLoudnessCorrection version: ' + loudnesscorrection_version + '\n\nffmpeg_executable_name = ' + str(ffmpeg_executable_name) + '\n\n\n\nLocal variable values after reading the configfile: ' + configfile_path + ' are:'
		values_read_from_configfile.append(str((len(title_text) + 1) * '-'))
		values_read_from_configfile.append(title_text)
		values_read_from_configfile.append('')
		values_read_from_configfile.append('os_name = ' + os_name)
		values_read_from_configfile.append('os_version = ' + os_version)
		values_read_from_configfile.append('os_init_system_name = ' + all_settings_dict['os_init_system_name'])
		values_read_from_configfile.append('')
		values_read_from_configfile.append('language = ' + language)
		values_read_from_configfile.append('english = ' + str(english))
		values_read_from_configfile.append('finnish = ' + str(finnish))
		values_read_from_configfile.append('')
		values_read_from_configfile.append('target_path = ' + target_path)
		values_read_from_configfile.append('hotfolder_path = ' + hotfolder_path)
		values_read_from_configfile.append('directory_for_temporary_files = ' + directory_for_temporary_files)
		values_read_from_configfile.append('directory_for_results = ' + directory_for_results)
		values_read_from_configfile.append('libebur128_path = ' + libebur128_path)
		values_read_from_configfile.append('')
		values_read_from_configfile.append('delay_between_directory_reads = ' + str(delay_between_directory_reads))	
		values_read_from_configfile.append('number_of_processor_cores = ' + str(number_of_processor_cores))
		values_read_from_configfile.append('file_expiry_time = ' + str(file_expiry_time))
		values_read_from_configfile.append('')
		values_read_from_configfile.append('natively_supported_file_formats = ' + ', '.join(natively_supported_file_formats))
		values_read_from_configfile.append('ffmpeg_output_wrapper_format = ' + ffmpeg_output_wrapper_format)
		values_read_from_configfile.append('peak_measurement_method stored to the settings file = ' + all_settings_dict['peak_measurement_method'])
		if (force_truepeak == True) or (force_samplepeak == True):
			values_read_from_configfile.append('peak_measurement_method forced with commandline option: ' + peak_measurement_method)
		values_read_from_configfile.append('')
		values_read_from_configfile.append('silent = ' + str(silent))
		values_read_from_configfile.append('')
		values_read_from_configfile.append('write_html_progress_report = ' + str(write_html_progress_report))
		values_read_from_configfile.append('html_progress_report_write_interval = ' + str(html_progress_report_write_interval))
		values_read_from_configfile.append('web_page_name = ' + web_page_name)
		values_read_from_configfile.append('web_page_path = ' + web_page_path)
		values_read_from_configfile.append('')
		values_read_from_configfile.append('heartbeat = ' + str(heartbeat))
		values_read_from_configfile.append('heartbeat_file_name = ' + heartbeat_file_name)
		values_read_from_configfile.append('heartbeat_write_interval = ' + str(heartbeat_write_interval))
		values_read_from_configfile.append('')
		values_read_from_configfile.append('where_to_send_error_messages = ' + ', '.join(where_to_send_error_messages))
		values_read_from_configfile.append('send_error_messages_to_logfile = ' + str(send_error_messages_to_logfile))
		values_read_from_configfile.append('directory_for_error_logs = ' + directory_for_error_logs)
		values_read_from_configfile.append('error_logfile_path = ' + error_logfile_path)
		values_read_from_configfile.append('')
		values_read_from_configfile.append('send_error_messages_by_email = ' + str(send_error_messages_by_email))
		values_read_from_configfile.append('email_sending_details =' + ', '.join(email_sending_details))
		values_read_from_configfile.append('')
		values_read_from_configfile.append('write_loudness_calculation_results_to_a_machine_readable_file = ' + str(write_loudness_calculation_results_to_a_machine_readable_file))
		values_read_from_configfile.append('create_loudness_corrected_files = ' + str(create_loudness_corrected_files))
		values_read_from_configfile.append('create_loudness_history_graphics_files = ' + str(create_loudness_history_graphics_files))
		values_read_from_configfile.append('delete_original_file_immediately = ' + str(delete_original_file_immediately))

		variable_string = unit_separator
		characters_in_ascii = '' 

		for item in variable_string:
			characters_in_ascii = characters_in_ascii + str(ord(item)) + ', ' 
		characters_in_ascii = characters_in_ascii[0:len(characters_in_ascii)-2]
		values_read_from_configfile.append('unit_separator (ascii numbers) = ' + characters_in_ascii)

		variable_string = record_separator
		characters_in_ascii = '' 

		for item in variable_string:
			characters_in_ascii = characters_in_ascii + str(ord(item)) + ', ' 
		characters_in_ascii = characters_in_ascii[0:len(characters_in_ascii)-2]
		values_read_from_configfile.append('record_separator (ascii numbers) = ' + characters_in_ascii)

		values_read_from_configfile.append('enable_mxf_audio_remixing = ' + str(enable_mxf_audio_remixing))
		values_read_from_configfile.append('remix_map_file_extension = ' + str(remix_map_file_extension))
		values_read_from_configfile.append('global_mxf_audio_remix_channel_map = ' + str(global_mxf_audio_remix_channel_map))
		values_read_from_configfile.append('ffmpeg_free_wrapper_formats = ' + str(ffmpeg_free_wrapper_formats))
		values_read_from_configfile.append('mxf_formats = ' + str(mxf_formats))
		values_read_from_configfile.append('mpeg_wrapper_formats = ' + str(mpeg_wrapper_formats))
		values_read_from_configfile.append('ffmpeg_allowed_wrapper_formats = ' + str(ffmpeg_allowed_wrapper_formats))
		values_read_from_configfile.append('enable_all_nonfree_ffmpeg_wrapper_formats = ' + str(enable_all_nonfree_ffmpeg_wrapper_formats))
		values_read_from_configfile.append('ffmpeg_free_codec_formats = ' + str(ffmpeg_free_codec_formats))
		values_read_from_configfile.append('ffmpeg_allowed_codec_formats = ' + str(ffmpeg_allowed_codec_formats))
		values_read_from_configfile.append('enable_all_nonfree_ffmpeg_codec_formats = ' + str(enable_all_nonfree_ffmpeg_codec_formats))

		values_read_from_configfile.append(str((len(title_text) + 1) * '-'))

	while True:
	
		# Check if the main routine asks us to exit now. This is used when running regression tests.
		if quit_all_threads_now == True:
			return()

		if debug_lists_and_dictionaries == True:

			keys_of_debug_temporary_dict_for_integrated_loudness_calculation_information = set(debug_temporary_dict_for_integrated_loudness_calculation_information)
			keys_of_debug_temporary_dict_for_timeslice_calculation_information = set(debug_temporary_dict_for_timeslice_calculation_information)
			keys_of_debug_temporary_dict_for_all_file_processing_information = set(debug_temporary_dict_for_all_file_processing_information)
			keys_of_debug_complete_final_information_for_all_file_processing_dict = set(debug_complete_final_information_for_all_file_processing_dict)
			keys_of_temp_loudness_results_for_automation = set(temp_loudness_results_for_automation)
			keys_of_final_loudness_results_for_automation = set(final_loudness_results_for_automation)

			list_printouts = []
			list_printouts.append('len(list_of_growing_files)= ' + str(len(list_of_growing_files)) + ' list_of_growing_files = ' + str(list_of_growing_files))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(files_queued_to_loudness_calculation)= ' + str(len(files_queued_to_loudness_calculation)) + ' files_queued_to_loudness_calculation = ' + str(files_queued_to_loudness_calculation))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(loudness_calculation_queue)= ' + str(len(loudness_calculation_queue)) + ' loudness_calculation_queue = ' + str(loudness_calculation_queue))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(new_hotfolder_filelist_dict)= ' + str(len(new_hotfolder_filelist_dict)) + ' new_hotfolder_filelist_dict = ' + str(new_hotfolder_filelist_dict))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(old_hotfolder_filelist_dict)= ' +  str(len(old_hotfolder_filelist_dict)) + ' old_hotfolder_filelist_dict = ' + str(old_hotfolder_filelist_dict))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(new_results_directory_filelist_dict)= '+  str(len(new_results_directory_filelist_dict)) + ' new_results_directory_filelist_dict = ' + str(new_results_directory_filelist_dict))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(old_results_directory_filelist_dict)= '+  str(len(old_results_directory_filelist_dict)) + ' old_results_directory_filelist_dict = ' + str(old_results_directory_filelist_dict))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(unsupported_ignored_files_dict)= ' + str(len(unsupported_ignored_files_dict)) + ' unsupported_ignored_files_dict = ' + str(unsupported_ignored_files_dict))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(files_queued_for_deletion)= ' + str(len(files_queued_for_deletion)) + ' files_queued_for_deletion = ' + str(files_queued_for_deletion))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(completed_files_list)= ' + str(len(completed_files_list)) + ' completed_files_list = ' + str(completed_files_list))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(completed_files_dict)= ' + str(len(completed_files_dict)) + ' completed_files_dict = ' + str(completed_files_dict))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(error_messages_to_email_later_list)= ' + str(len(error_messages_to_email_later_list)) + ' error_messages_to_email_later_list = ' + str(error_messages_to_email_later_list))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(integrated_loudness_calculation_results)= ' + str(len(integrated_loudness_calculation_results)) + ' integrated_loudness_calculation_results = ' + str(integrated_loudness_calculation_results))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(debug_temporary_dict_for_integrated_loudness_calculation_information)= ' + str(len(debug_temporary_dict_for_integrated_loudness_calculation_information)) + ' keys_of_debug_temporary_dict_for_integrated_loudness_calculation_information = ' + str(keys_of_debug_temporary_dict_for_integrated_loudness_calculation_information))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(debug_temporary_dict_for_timeslice_calculation_information)= ' + str(len(debug_temporary_dict_for_timeslice_calculation_information)) + ' keys_of_debug_temporary_dict_for_timeslice_calculation_information = ' + str(keys_of_debug_temporary_dict_for_timeslice_calculation_information))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(debug_temporary_dict_for_all_file_processing_information)= ' + str(len(debug_temporary_dict_for_all_file_processing_information)) + ' keys_of_debug_temporary_dict_for_all_file_processing_information = ' + str(keys_of_debug_temporary_dict_for_all_file_processing_information))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(debug_complete_final_information_for_all_file_processing_dict)= ' + str(len(debug_complete_final_information_for_all_file_processing_dict)) + ' keys_of_debug_complete_final_information_for_all_file_processing_dict = ' + str(keys_of_debug_complete_final_information_for_all_file_processing_dict))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(temp_loudness_results_for_automation)= ' + str(len(temp_loudness_results_for_automation)) + ' keys_of_temp_loudness_results_for_automation = ' + str(keys_of_temp_loudness_results_for_automation))
			list_printouts.append('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
			list_printouts.append('len(final_loudness_results_for_automation)= ' + str(len(final_loudness_results_for_automation)) + ' keys_of_final_loudness_results_for_automation = ' + str(keys_of_final_loudness_results_for_automation))


			# Only write list and dictionary debug info to file if the information has changed.
			if list_printouts != list_printouts_old_values:
				
				# If it has been 24 hours since starting to write to the file, then start writing to a new file.
				if int(time.time()) >= time_to_start_writing_to_a_new_file:
					time_to_start_writing_to_a_new_file = int(time.time() + file_name_expiry_time) # Write debug info to a file only a preset time and then change the file name. (Default time 24 hours).
					real_time_string = get_realtime(english, finnish)[1]
					debug_messages_file = 'debug-variables_lists_and_dictionaries-' + real_time_string + '.txt'
					first_write_to_a_new_logfile = True
				else:
					first_write_to_a_new_logfile = False

				# Write list_printouts to disk. First write it to temporary directory and then move to the target directory.
				try:
					real_time_string = get_realtime(english, finnish)[1]
					
					# Move debug_log - file to the temp directory so we can append new messages to it.
					if os.path.exists(directory_for_error_logs + os.sep + debug_messages_file):
						shutil.move(directory_for_error_logs + os.sep + debug_messages_file, directory_for_temporary_files + os.sep + debug_messages_file)
					with open(directory_for_temporary_files + os.sep + debug_messages_file, 'at') as debug_messages_filehandler:
						if first_write_to_a_new_logfile == True:
							for item in values_read_from_configfile:
								debug_messages_filehandler.write(item + '\n')
						debug_messages_filehandler.write('###################################################################################################################################################################################\n')
						
						debug_messages_filehandler.write('\nTimestamp = ' + real_time_string + '\n\n')
						for item in list_printouts:
							debug_messages_filehandler.write(item + '\n')
						debug_messages_filehandler.write('###################################################################################################################################################################################\n')
						debug_messages_filehandler.flush() # Flushes written data to os cache
						os.fsync(debug_messages_filehandler.fileno()) # Flushes os cache to disk
					shutil.move(directory_for_temporary_files + os.sep + debug_messages_file, directory_for_error_logs + os.sep + debug_messages_file)
				except KeyboardInterrupt:
					if silent == False:
						print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
					sys.exit(0)
				except IOError as reason_for_error:
					error_message = 'Error opening debug-messages file for writing ' * english + 'Debug-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error opening debug-messages file for writing ' * english + 'Debug-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				
				# Save the old state of the variable so that we can see if changes happened.
				list_printouts_old_values = list_printouts

		# Sleep between writing output
		time.sleep(30)

def get_ip_addresses_of_the_host_machine(previous_ip_addresses_of_the_machine):

	try:
		stdout = b''
		stderr = b''

		global ip_address_refresh_counter
		global directory_for_temporary_files
		global ip_address_acquirement_error_has_already_been_reported

		new_ip_addresses_of_the_machine = []

		# Create the commandline we need to run.
		commands_to_run = ['hostname', '-I']
		error_message = ''

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

		except OSError as reason_for_error:
			if error_message != '':
				error_message = error_message + '\n'
			error_message = error_message + 'Error writing to stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon kirjoittaminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)

		# Open files we used as stdout and stderr for the external program and read in what the program did output to those files.
		try:
			with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler, open(stderr_for_external_command, 'rb') as stderr_commandfile_handler:
				stdout = stdout_commandfile_handler.read(None)
				stderr = stderr_commandfile_handler.read(None)

		except IOError as reason_for_error:
			if error_message != '':
				error_message = error_message + '\n'
			error_message = error_message + 'Error reading from stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston lukeminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)

		except OSError as reason_for_error:
			if error_message != '':
				error_message = error_message + '\n'
			error_message = error_message + 'Error reading from stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedostoon lukeminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		
		stdout = str(stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		stderr = str(stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		
		# Delete the temporary stdout and stderr - files
		try:
			os.remove(stdout_for_external_command)
			os.remove(stderr_for_external_command)

		except IOError as reason_for_error:
			if error_message != '':
				error_message = error_message + '\n'
			error_message = error_message + 'Error deleting stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
		except OSError as reason_for_error:
			if error_message != '':
				error_message = error_message + '\n'
			error_message = error_message + 'Error deleting stdout- or stderr - file when running command: ' * english + 'Stdout- tai stderr - tiedoston deletoiminen epäonnistui ajettaessa komentoa: ' * finnish + ' '.join(commands_to_run) + '. ' + str(reason_for_error)
	
		if error_message == '':

			new_ip_addresses_of_the_machine = stdout.split()

			if new_ip_addresses_of_the_machine != []:
				
				# We got the ip address of the server successfully, if previous try failed then it set the error flag,
				# so that we don't repoprt this error more than once. Reset the error flag now.
				ip_address_acquirement_error_has_already_been_reported = False

				# Return the new ip addresses to the main program
				return(new_ip_addresses_of_the_machine)

		else:
			# The default interval to check if our ip address has changed is 5 minutes (300 seconds).
			# If the check succeeds, then the counter that counts seconds since last check is reset to zero.
			# If the ip address check fails, then the counter is not reset and we check again for the ip address every 5 seconds and the counter continues to grow above 300.
			# If the ip address check fails continuously for another 120 seconds (300 + 120), then send an error message.
			# Also set a flag so that we don't report this error more than once.
			# Note !!!!!!! The ip address check may sometimes fail, but it only means we don't know what the ip address is, the machine propably still has a valid address, just the check fails.
			if ip_address_refresh_counter >= 420:

				ip_address_refresh_counter = 0 # Start ip address refresh counter again from zero.

				# Error happened, send error message but only once.
				if ip_address_acquirement_error_has_already_been_reported == False:

					send_error_messages_to_screen_logfile_email(error_message, [])
					ip_address_acquirement_error_has_already_been_reported = True

		return(previous_ip_addresses_of_the_machine)
	
	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'get_ip_addresses_of_the_host_machine'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

		
def get_audio_stream_information_with_ffmpeg_and_create_extraction_parameters(filename, hotfolder_path, directory_for_temporary_files, ffmpeg_output_wrapper_format, english, finnish):
	
	# This subprocess works like this:
	# ---------------------------------
	# The process runs FFmpeg to get information about audio streams in a file.
	# FFmpeg output is then parsed and a FFmpeg commandline created that will later be used to extract all valid audio streams from the file.

	try:
		natively_supported_file_format = False # This variable tells if the file format is natively supported by libebur128 and sox. We do not yet know the format of the file, we just set the default here. If format is not natively supported by libebur128 and sox, file will be first extracted to wav or flac with ffmpeg.
		ffmpeg_supported_fileformat = False # This variable tells if the file format is natively supported by ffmpeg. We do not yet know the format of the file, we just set the default here. If format is not supported by ffmpeg, we have no way of processing the file and it will be queued for deletion.
		number_of_ffmpeg_supported_audiostreams = 0 # This variable holds the number of audio streams ffmpeg finds in the file.
		details_of_ffmpeg_supported_audiostreams = [] # Holds ffmpeg produced information about audio streams found in file (example: 'Stream #0.1[0x82]: Audio: ac3, 48000 Hz, 5.1, s16, 384 kb/s' )
		global directory_for_results
		global where_to_send_error_messages
		global debug
		global write_loudness_calculation_results_to_a_machine_readable_file
		dummy_initial_data_for_machine_readable_results_file = {}
		global temp_loudness_results_for_automation 
		global os_name
		global os_version
		
		audio_duration_string = ''
		audio_duration_fractions_string = ''
		audio_duration_list = []
		audio_duration = 0
		audio_duration_according_to_mediainfo = 0
		audio_duration_rounded_to_seconds = 0
		audio_duration_fractions = 0
		ffmpeg_error_message = ''
		ffmpeg_run_output = b''
		time_slice_duration_string = '3' # Set the default value to use in timeslice loudness calculation.
		file_to_process = hotfolder_path + os.sep + filename
		filename_and_extension = os.path.splitext(filename)
		target_filenames = []
		ffmpeg_commandline = []
		bit_depth = 0
		sample_rate = 0
		input_audiostream_codec_format = ''
		output_audiostream_codec_format = ''
		map_number = ''
		number_of_audio_channels = '0'
		estimated_uncompressed_size_for_single_mono_file = 0
		estimated_uncompressed_size_for_combined_channels = 0
		global wav_format_maximum_file_size
		file_type = ''
		list_of_error_messages_for_unsupported_streams = []
		error_message = ''
		error_code = 0
		filenames_and_channel_counts_for_mxf_audio_remixing = []
		audio_remix_channel_map = []
		mxf_audio_remixing = False
		supported_file_name = ''
		
		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_all_file_processing_information

			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('get_audio_stream_information_with_ffmpeg_and_create_extraction_parameters')
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		# Define lists of supported pcm bit depths
		global pcm_8_bit_formats
		global pcm_16_bit_formats
		global pcm_24_bit_formats
		global pcm_32_bit_formats
		global pcm_64_bit_formats

		global ffmpeg_allowed_wrapper_formats
		global ffmpeg_allowed_codec_formats
		wrapper_format_is_in_allowed_formats_list = True

		global enable_mxf_audio_remixing
		global mxf_formats
		global mpeg_wrapper_formats
		wrapper_format = ''
		mediainfo_error_message = ''
		
		try:
			# Define filename for the temporary file that we are going to use as stdout for the external command.
			stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_ffmpeg_find_audio_streams_stdout.txt'
			# Open the stdout temporary file in binary write mode.
			with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
		
				# Examine the file in HotFolder with ffmpeg.
				subprocess.Popen([ffmpeg_executable_name, '-i', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run ffmpeg.
		
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
			
		##################################################################################################
		# Find lines from FFmpeg output that have information about audio streams and file duration	 #
		# Also record channels count, bit depth, sample rate and FFmpeg map number for each stream found #
		##################################################################################################
		
		audio_stream_number = 0
		
		for item in ffmpeg_run_output_result_list:
			
			skip_this_audio_stream = False

			if 'Input #0' in item:
				# Get the type of the file.
				file_type = str(item).split('from')[0].split(',')[1].strip()

				# avconv / FFmpeg can not tell if file wrapper format is webm or matroska, it announces these all as one formatwith keywords:   matroska,webm.
				# Get true wrapper format with mediainfo.
				if file_type == 'matroska':
					wrapper_format, mediainfo_error_message = get_file_wrapper_format_with_mediainfo(directory_for_temporary_files, filename, hotfolder_path, english, finnish)
					if (mediainfo_error_message == '') and (wrapper_format != ''):
						file_type = wrapper_format

				# If allowed wrapper format is 'all' then process all formats that FFmpeg supports, otherwise limit processing to user defined wrapper formats.
				if 'all' not in ffmpeg_allowed_wrapper_formats:
					if file_type not in ffmpeg_allowed_wrapper_formats:
						wrapper_format_is_in_allowed_formats_list = False
						break

				# File is a mxf - file. Check if user has written a text file on disk holding a file specific audio remix channel map.
				# If not the subroutine returns the global audio mixing channel map.
				if file_type in mxf_formats:

					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('Message')
						debug_information_list.append('Calling subroutine: read_audio_remix_map_file')

					audio_remix_channel_map = read_audio_remix_map_file(hotfolder_path, filename, english, finnish)

					if (len(audio_remix_channel_map) > 0) and (enable_mxf_audio_remixing == True):
						mxf_audio_remixing = True
					else:
						mxf_audio_remixing = False

					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('Message')
						debug_information_list.append('Returned from subroutine: read_audio_remix_map_file')

			if 'Audio:' in item: # There is the string 'Audio' for each audio stream that ffmpeg finds. Count how many 'Audio' strings is found and put the strings in a list. The string holds detailed information about the stream and we print it later.
			
				number_of_audio_channels = '0'
				audio_stream_number = audio_stream_number + 1
				
				# Transportstreams can have streams that have 0 audio channels, skip these dummy streams.
				if ('0 channels' in item):
					if not item[item.index('0 channels')-1].isnumeric(): # Check if the character before the string '0 channels' is a number or not. Only skip stream if it has 0 audio channels, but not when it has 10 or 100 :)
						# Create error message to the results graphics file and skip the stream.
						unsupported_stream_name = filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + str(audio_stream_number) + '-ChannelCount-' * english + '-AaniKanavia-' * finnish  + '0'
						error_message = 'There are ' * english + 'Miksauksessa numero ' * finnish + str(audio_stream_number) * finnish + 'zero' * english + ' audio channels in stream number ' * english + ' on nolla äänikanavaa' * finnish + str(audio_stream_number) * english
						error_code = 5
						list_of_error_messages_for_unsupported_streams.append([unsupported_stream_name, error_message, error_code, audio_stream_number])
						continue
				
				# Create names for audio streams found in the file.
				# First parse the number of audio channels in each stream ffmpeg reported and put it in a variable.
				item = str(item.strip())
				number_of_audio_channels_as_text = str(item.split(',')[2].strip()) # FFmpeg reports audio channel count as a string.		
				
				# Split audio channel count to a list ('2 channels' becomes ['2', 'channels']
				number_of_audio_channels_as_text_split_to_a_list = number_of_audio_channels_as_text.split()
				
				# If the first item in the list is an integer bigger that 0 use it as the channel count.
				# If the conversion from string to int raises an error, then the item is not a number, but a string like 'stereo'.
				try:
					if int(number_of_audio_channels_as_text_split_to_a_list[0]) > 0:
						number_of_audio_channels = str(number_of_audio_channels_as_text_split_to_a_list[0])
				except ValueError:
					pass
			
				# FFmpeg / avconv sometimes reports some channel counts differently. Test for these cases and convert the channel count to an simple number.
				# These values are from avconv source: libavutil/channel_layout.c
				if 'mono' in number_of_audio_channels_as_text:
					number_of_audio_channels = '1'
				if 'stereo' in number_of_audio_channels_as_text:
					number_of_audio_channels = '2'
				if 'downmix' in number_of_audio_channels_as_text:
					number_of_audio_channels = '2'
				if '2.1' in number_of_audio_channels_as_text:
					number_of_audio_channels = '3'
				if '3.0' in number_of_audio_channels_as_text:
					number_of_audio_channels = '3'
				if '3.1' in number_of_audio_channels_as_text:
					number_of_audio_channels = '4'
				if '4.0' in number_of_audio_channels_as_text:
					number_of_audio_channels = '4'
				if 'quad' in number_of_audio_channels_as_text:
					number_of_audio_channels = '4'
				if '4.1' in number_of_audio_channels_as_text:
					number_of_audio_channels = '5'
				if '5.0' in number_of_audio_channels_as_text:
					number_of_audio_channels = '5'
				if '5.1' in number_of_audio_channels_as_text:
					number_of_audio_channels = '6'
				if '6.0' in number_of_audio_channels_as_text:
					number_of_audio_channels = '6'
				if 'hexagonal' in number_of_audio_channels_as_text:
					number_of_audio_channels = '6'
				if '6.1' in number_of_audio_channels_as_text:
					number_of_audio_channels = '7'
				if '7.0' in number_of_audio_channels_as_text:
					number_of_audio_channels = '7'
				if '7.1' in number_of_audio_channels_as_text:
					number_of_audio_channels = '8'
				if 'octagonal' in number_of_audio_channels_as_text:
					number_of_audio_channels = '8'

				if number_of_audio_channels == '0':
					error_message = 'ERROR !!! I could not parse FFmpeg channel count string: ' * english + 'VIRHE !!! En osannut tulkita ffmpeg:in antamaa tietoa kanavien lukumäärästä: ' * finnish + '\'' + str(number_of_audio_channels_as_text_split_to_a_list[0]) + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename

					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('error_message')
						debug_information_list.append(error_message)

					send_error_messages_to_screen_logfile_email(error_message, [])
				
				# Channel counts bigger than 6 channels are only supported for mxf - files and only if mxf audio remixing is enabled.
				# For all other filetypes with channel counts more than 6, store the stream name and error message to a list and skip the stream.
				if int(number_of_audio_channels) > 6:
					if file_type not in mxf_formats:
						skip_this_audio_stream = True

					if (file_type in mxf_formats) and (mxf_audio_remixing == False):
						skip_this_audio_stream = True
				
				if skip_this_audio_stream == True:
					unsupported_stream_name = filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + str(audio_stream_number) + '-ChannelCount-' * english + '-AaniKanavia-' * finnish  + number_of_audio_channels
					error_message = 'There are ' * english + 'Miksauksessa ' * finnish  + str(audio_stream_number) * finnish + ' on ' * finnish + str(number_of_audio_channels) + ' channels in stream ' * english + str(audio_stream_number) * english + ', only channel counts from one to six are supported' * english + ' äänikanavaa, vain kanavamäärät yhdestä kuuteen ovat tuettuja' * finnish
					error_code = 6
					list_of_error_messages_for_unsupported_streams.append([unsupported_stream_name, error_message, error_code, audio_stream_number])
					continue
				
				# Find audio stream format information
				input_audiostream_codec_format = item.split('Audio:')[1].split(',')[0].strip()
				output_audiostream_codec_format = 'pcm_s16le' # Default audio extraction bit depth is 16 bits if input file bit depth is not known.
				bit_depth = 16 # Default bit depth.

				# If allowed audio codec format is 'all' then process all formats that FFmpeg supports, otherwise limit processing to user defined codec formats.
				if 'all' not in ffmpeg_allowed_codec_formats:

					if input_audiostream_codec_format not in ffmpeg_allowed_codec_formats:

						# Create error message to the results graphics file and skip the stream.
						unsupported_stream_name = filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + str(audio_stream_number) + '-ChannelCount-' * english + '-AaniKanavia-' * finnish + number_of_audio_channels
						error_message = 'Audio compression codec ' * english + 'Audion kompressioformaatti ' * finnish + str(input_audiostream_codec_format) + ' is not supported' * english + ' ei ole tuettu' * finnish
						error_code = 11
						list_of_error_messages_for_unsupported_streams.append([unsupported_stream_name, error_message, error_code, audio_stream_number])
						continue

				# Check if the stream format is a supported PCM - format and assign output format and bit depth according to input bit depth.
				if input_audiostream_codec_format in pcm_8_bit_formats:
					output_audiostream_codec_format = 'pcm_u8'
					bit_depth = 8
					
				if input_audiostream_codec_format in pcm_16_bit_formats:
					output_audiostream_codec_format = 'pcm_s16le'
					bit_depth = 16
					
				if input_audiostream_codec_format in pcm_24_bit_formats:
					output_audiostream_codec_format = 'pcm_s24le'
					bit_depth = 24
					
				if input_audiostream_codec_format in pcm_32_bit_formats:
					output_audiostream_codec_format = 'pcm_s32le'
					bit_depth = 32
					
				if input_audiostream_codec_format in pcm_64_bit_formats: # Bit depth is bigger than 32 bits, convert to 32 bits because sox does not support bit depth over 32 bits.
					output_audiostream_codec_format = 'pcm_s32le'
					bit_depth = 32
					
				# If audio format is flac, then try to find out the bit depth of flac audio from FFmpeg text output.
				if input_audiostream_codec_format == 'flac':
				
					# Find audio bit depth from FFmpeg stream info output.
					bit_depth_info_field = str(item.split(',')[3].strip())
					
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
						error_message = 'ERROR !!! I could not parse FFmpeg bit depth string for flac format: ' * english + 'VIRHE !!! En osannut tulkita ffmpeg:in antamaa tietoa flac formaatin bittisyvyydestä: ' * finnish + '\'' + bit_depth_as_text + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename

						# Save some debug information.
						if debug_file_processing == True:
							debug_information_list.append('error_message')
							debug_information_list.append(error_message)

						send_error_messages_to_screen_logfile_email(error_message, [])
					
					# FFmpeg displays flac bit depths 24 bits and 32 bits both as 32 bits. Force flac bit depth to 24 if it is 32.
					if bit_depth == 32:
						output_audiostream_codec_format = 'pcm_s24le'
						bit_depth = 24

				# Find out what is FFmpegs map number for the audio stream.
				# There usually is some unwanted cruft right behing the map numer, so we need to find the cut point by advancing characrer by character.
				# Example for a line that we are tring to parse here (ffmpeg 0.8 / avconv 0.9 and later):   Stream #0.1(eng): Audio: ac3, 48000 Hz, 5.1, s16, 448 kb/s
				# Example for a line that we are tring to parse here (ffmpeg 2.x):   Stream #0:1: Audio: ac3, 48000 Hz, 5.1, s16, 448 kb/s
				# The first number (0) in the map means input stream number (there can be many input file. The second (1) number means the stream in the file.
				map_number = ''
				separator_character_found = False

				for map_number_counter in range(item.find('#') + 1, len(item)):
					if (separator_character_found == False) and (item[map_number_counter] == '.'): # FFmpeg / Avconv 0.8 uses . as map number separator.
						separator_character_found = True # Match separator character only once.
						continue
					if (separator_character_found == False) and (item[map_number_counter] == ':'): # FFmpeg 2.x uses : as map number separator.
						separator_character_found = True # Match separator character only once.
						continue
					if item[map_number_counter].isnumeric() == False:
						break
					
				temp_map_number_string = item[item.find('#') + 1:map_number_counter]

				# Test if we really have found the stream map number.
				try:

					if '.' in temp_map_number_string: # FFmpeg 0.8 / Avconv 0.8 and later uses . as map number separator.
						map_number = temp_map_number_string.split('.')[1]
					if ':' in temp_map_number_string: # FFmpeg 2.x uses : as map number separator.
						map_number = temp_map_number_string.split(':')[1]
				
					
					if map_number.isnumeric() == False:
						error_message = 'Error: stream map number found in FFmpeg output is not a number: ' * english + 'Virhe: FFmpegin tulosteesta löydetty streamin numero ei ole numero: ' * finnish + map_number
					
						# Save some debug information.
						if debug_file_processing == True:
							debug_information_list.append('error_message')
							debug_information_list.append(error_message)
							
						send_error_messages_to_screen_logfile_email(error_message, [])

						continue # If map number is not found then skip the stream.

				except IndexError:
					error_message = 'Error: stream map number found in FFmpeg output is not in correct format: ' * english + 'Virhe: FFmpegin tulosteesta löydetty streamin numero ei ole oikeassa formaatissa: ' * finnish + map_number		   
					
					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('error_message')
						debug_information_list.append(error_message)
						
					send_error_messages_to_screen_logfile_email(error_message, [])
					
					continue # If map number is not found then skip the stream.

				# Find audio sample rate from FFmpeg stream info.
				sample_rate_as_text = str(item.split(',')[1].strip().split(' ')[0].strip())
				
				if sample_rate_as_text.isnumeric() == True:
					sample_rate = int(sample_rate_as_text)
				else:
					error_message = 'ERROR !!! I could not parse FFmpeg sample rate string: ' * english + 'VIRHE !!! En osannut tulkita ffmpeg:in antamaa tietoa näyteenottotaajuuudesta: ' * finnish + '\'' + sample_rate_as_text + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename

					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('error_message')
						debug_information_list.append(error_message)

					send_error_messages_to_screen_logfile_email(error_message, [])
				
				number_of_ffmpeg_supported_audiostreams = number_of_ffmpeg_supported_audiostreams + 1
				details_of_ffmpeg_supported_audiostreams.append([str(item.strip()), str(audio_stream_number), number_of_audio_channels, input_audiostream_codec_format, output_audiostream_codec_format, sample_rate, bit_depth, map_number])
				
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
					error_message = 'FFmpeg Error: Audio Duration = N/A' * english + 'FFmpeg Virhe: Äänen Kesto = N/A' * finnish + ': ' + filename

					# Save some debug information.
					if debug_file_processing == True:
						debug_information_list.append('error_message')
						debug_information_list.append(error_message)

					send_error_messages_to_screen_logfile_email(error_message, [])

			if filename + ':' in item: # Try to recognize some ffmpeg error messages, these always start with the filename + ':'
				ffmpeg_error_message = 'FFmpeg Error: ' * english + 'FFmpeg Virhe: ' * finnish + item.split(':')[1] # Get the reason for error from ffmpeg output.
				
		# Test if file type is mpegts. FFmpeg can not always extract file duration correctly from mpegts so in this case get file duration with the mediainfo - command.
		if (wrapper_format_is_in_allowed_formats_list == True) and (file_type == 'mpegts'):
			not_used, not_used, not_used, not_used, audio_duration_according_to_mediainfo, not_used, not_used = get_audiofile_info_with_mediainfo(directory_for_temporary_files, filename, hotfolder_path, english, finnish, save_debug_information = False)

			if audio_duration_according_to_mediainfo != 0:
				audio_duration = audio_duration_according_to_mediainfo
				audio_duration_rounded_to_seconds = int(audio_duration_according_to_mediainfo)
		
		###################################################################################################
		# Generate the commandline that will later be used to extract all valid audio streams with FFmpeg #
		###################################################################################################

		error_code = 0
		error_message = ' '
		
		for counter in range(0, number_of_ffmpeg_supported_audiostreams):
			
			# Get info about supported audio streams from a list.
			ffmpeg_stream_info, audio_stream_number, number_of_audio_channels, input_audiostream_codec_format, output_audiostream_codec_format, sample_rate, bit_depth, map_number = details_of_ffmpeg_supported_audiostreams[counter]
			
			# Calculate estimated uncompressed file size. Add one second of data to the file size (sample_rate = 1 second of audio data) to be on the safe side.
			estimated_uncompressed_size_for_single_mono_file = int((sample_rate * audio_duration * int(bit_depth / 8)) + sample_rate)
			estimated_uncompressed_size_for_combined_channels = estimated_uncompressed_size_for_single_mono_file * int(number_of_audio_channels)
		
			# Determine the output format that FFmpeg uses when writing the audio file.
			# The format defined here is only for the temporary file that is used to store the audio stream before loudness correction.
			# The ouput format for the final loudness corrected file is defined in subroutine: get_audiofile_info_with_sox_and_determine_output_format
			# The output format for a file is stored in variable: output_format_for_final_file
	
			# Use Flac always if possible, since the lossless compression it uses also speeds up disk writes (resulting files are smaller).
			ffmpeg_output_wrapper_format = 'flac'

			# Flac can not be used as the FFmpeg output format in the following cases since these would result in bit depth conversion
			# Flac supports only bit depths 16 and 24.
			if (estimated_uncompressed_size_for_combined_channels < wav_format_maximum_file_size) and (bit_depth == 8):
				ffmpeg_output_wrapper_format = 'wav'
			if (estimated_uncompressed_size_for_combined_channels < wav_format_maximum_file_size) and (bit_depth == 32):
				ffmpeg_output_wrapper_format = 'wav'
			# Ubuntu 12.04 and Debian 7 ships with a FFmpeg version that always converts bit depths bigger than 16 to 16 when storing output to Flac.
			# On these distros use wav when using flac would result in bit depth conversion.
			if (estimated_uncompressed_size_for_combined_channels < wav_format_maximum_file_size) and (bit_depth == 24) and (os_name == 'ubuntu') and (os_version == '12.04'):
				ffmpeg_output_wrapper_format = 'wav'
			if (estimated_uncompressed_size_for_combined_channels < wav_format_maximum_file_size) and (bit_depth == 24) and (os_name == 'debian') and (os_version == '7'):
				ffmpeg_output_wrapper_format = 'wav'

			# Assign the start of FFmpeg audio extract commandline to the list.
			if len(ffmpeg_commandline) == 0:
				ffmpeg_commandline = [ffmpeg_executable_name, '-y', '-i', file_to_process, '-vn']
			
			# Compile the name of output files to a list.
			# If we are going to remix audio from a mxf - file before processing it, then the output files are temporary and needs to have names that don't conflict with the final names.
			# Also if mxf - audio needs to be remixed, then gather file names and channel counts to a list that is needed for doing the remixes.
			if (file_type in mxf_formats) and (mxf_audio_remixing == True):
				# Define names for temporary output files demuxed from a mxf - file.
				supported_file_name = filename_and_extension[0] + '-TempOutputFile-' + audio_stream_number + '.' + ffmpeg_output_wrapper_format
				target_filenames.append(supported_file_name)

				# Gather output filenames and channel counts to a list, that is later used to remix mxf audio files to mixes defined in list 'mxf_audio_remix_channel_map'.
				filenames_and_channel_counts_for_mxf_audio_remixing.append([supported_file_name, number_of_audio_channels])

				# We don't store information about these files to the dictionary used for writing machine readable results, because these files are raw material for mixes that don't exist yet.
				# The process 'remix_files_according_to_channel_map' fills in the initial data for the recreated mix after it has created the mixes.

			else:
				# File is not mxf, define names for the final output files.
				supported_file_name = filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + audio_stream_number + '-ChannelCount-' * english + '-AaniKanavia-' * finnish + number_of_audio_channels + '.' + ffmpeg_output_wrapper_format
				target_filenames.append(supported_file_name)

				# Add info for all mixes found in the file to dictionary that is used to write the machine readable results file.
				if write_loudness_calculation_results_to_a_machine_readable_file == True:

					# Insert initial dummy data for the audiostream in dictionary used for writing the machine readable loudness calculation results file.
					#
					# If the filename for the file we are inspecting with FFmpeg is already stored to 'temp_loudness_results_for_automation' then it means,
					# we are processing an audiostream extracted from a original multistream file. This in turn means that we already have all the information needed for
					# machine readable results file and we don't want to store it again.

					if filename not in temp_loudness_results_for_automation:
						dummy_initial_data_for_machine_readable_results_file[supported_file_name] = [filename, [int(audio_stream_number), 0, 0, True, 0, 0, 0, 0, 0, 0, 0, 0, error_code, error_message,[]]]


			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('Stream Filename')
				debug_information_list.append(target_filenames[-1])
				debug_information_list.append('Stream Is Supported')
				debug_information_list.append('True')
				debug_information_list.append('audio_stream_number')
				debug_information_list.append(audio_stream_number)
				debug_information_list.append('map_number')
				debug_information_list.append(map_number)
				debug_information_list.append('number_of_audio_channels')
				debug_information_list.append(number_of_audio_channels)
				debug_information_list.append('file_type')
				debug_information_list.append(file_type)
				debug_information_list.append('bit_depth')
				debug_information_list.append(bit_depth)
				debug_information_list.append('sample_rate')
				debug_information_list.append(sample_rate)
				debug_information_list.append('audio_duration')
				debug_information_list.append(audio_duration)
				debug_information_list.append('estimated_uncompressed_size_for_single_mono_file')
				debug_information_list.append(estimated_uncompressed_size_for_single_mono_file)
				debug_information_list.append('estimated_uncompressed_size_for_combined_channels')
				debug_information_list.append(estimated_uncompressed_size_for_combined_channels)
				debug_information_list.append('input_audiostream_codec_format')
				debug_information_list.append(input_audiostream_codec_format)
				debug_information_list.append('output_audiostream_codec_format')
				debug_information_list.append(output_audiostream_codec_format)
				debug_information_list.append('ffmpeg_output_wrapper_format')
				debug_information_list.append(ffmpeg_output_wrapper_format)
				debug_information_list.append('mxf_audio_remixing')
				debug_information_list.append(mxf_audio_remixing)
				debug_information_list.append('filenames_and_channel_counts_for_mxf_audio_remixing')
				debug_information_list.append(filenames_and_channel_counts_for_mxf_audio_remixing)
				debug_information_list.append('audio_remix_channel_map')
				debug_information_list.append(audio_remix_channel_map)
				debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list


			# Add audio stream mapping command to the commandline.
			# This command selects the correct audiostream from the input file for writing to a outputfile.
			temp_list = []
			temp_list = ['-map', '0:' + str(map_number)]
			ffmpeg_commandline.extend(temp_list)
			temp_list = []


			# Generate FFmpeg extract options for audio stream.
			ffmpeg_commandline.append('-acodec')
			
			if ffmpeg_output_wrapper_format == 'flac':
				ffmpeg_commandline.append('flac')

				# avconv on Ubuntu 14.04 defaults to 24 bits when saving to flac. This is waste of space if inputfile bit depth is 16 or the inputfile is a lossy compression format.
				# Force flac output to (signed) 16 bits, when input is 16 bits or lossy compression format.
				if bit_depth == 16:
					ffmpeg_commandline.append('-sample_fmt')
					ffmpeg_commandline.append('s16')

			else:
				# If output format is not flac, then use pcm format with bit depth that was decided earlier in this subroutine.
				ffmpeg_commandline.append(output_audiostream_codec_format)
				
			ffmpeg_commandline.append('-f')
			ffmpeg_commandline.append(ffmpeg_output_wrapper_format)
			ffmpeg_commandline.append(directory_for_temporary_files + os.sep + target_filenames[counter])
		
		if number_of_ffmpeg_supported_audiostreams >= 1:
			ffmpeg_supported_fileformat = True
		else:
			ffmpeg_supported_fileformat = False

		number_of_unsupported_streams_in_file = len(list_of_error_messages_for_unsupported_streams)
		total_number_of_streams_in_the_file = number_of_ffmpeg_supported_audiostreams + number_of_unsupported_streams_in_file
		
		# If there were supported and unsupported streams in the file then print error messages we gathered for the unsupported streams earlier.
		if (ffmpeg_supported_fileformat == True) and (len(list_of_error_messages_for_unsupported_streams) > 0):
			
			for unsupported_stream_name, error_message, error_code, audio_stream_number in list_of_error_messages_for_unsupported_streams:
				
				# This error message is not very important so don't send it by email, only send it to other possible destinations (screen, logfile).
				error_message_destinations = copy.deepcopy(where_to_send_error_messages)
				if 'email' in error_message_destinations:
					error_message_destinations.remove('email')
				send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, error_message_destinations)
				
				# Create the result graphics file with an error message telling stream is not supported.
				create_gnuplot_commands_for_error_message(error_message, unsupported_stream_name, directory_for_temporary_files, directory_for_results, english, finnish)

				# Add info for all mixes found in the file to dictionary that is used to write the machine readable results file.
				if write_loudness_calculation_results_to_a_machine_readable_file == True:
					
					# If there are results already stored for this oroginal file, then append this streams results to them.
					if filename in final_loudness_results_for_automation:

						mix_result_lists = final_loudness_results_for_automation[filename]
						mix_result_lists.append([audio_stream_number, number_of_ffmpeg_supported_audiostreams, total_number_of_streams_in_the_file, True, 0, 0, 0, 0, 0, 0, 0, 0, error_code, error_message,[]])

					else:
						mix_result_lists = [[audio_stream_number, number_of_ffmpeg_supported_audiostreams, total_number_of_streams_in_the_file, True, 0, 0, 0, 0, 0, 0, 0, 0, error_code, error_message,[]]]

					final_loudness_results_for_automation[filename] = mix_result_lists

				# Save some debug information.
				if debug_file_processing == True:
					# Printing error message in history graphics file adds the stream name to a debug processing information dictionary.
					# Since the stream is unsupported and will not be processed, remove it's name from the debug dictionary.
					if unsupported_stream_name in debug_temporary_dict_for_all_file_processing_information:
						del debug_temporary_dict_for_all_file_processing_information[unsupported_stream_name]
			
					debug_information_list.append('Stream Filename')
					debug_information_list.append(unsupported_stream_name)
					debug_information_list.append('Stream Is Supported')
					debug_information_list.append('False')
					debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		# If there are only unsupported audio streams in the file then assign an error message that gets printed on the results graphics file.
		# Currently the only known unsupported streams in a file are streams with channel counts of zero and more than 6 channels.
		send_ffmpeg_error_message_by_email = True

		if wrapper_format_is_in_allowed_formats_list == False:
			ffmpeg_error_message = 'File wrapper format ' * english + 'Tiedoston paketointiformaatti ' * finnish + str(file_type) + ' is not supported' * english + ' ei ole tuettu' * finnish
			send_ffmpeg_error_message_by_email = False

		if (ffmpeg_supported_fileformat == False) and (len(list_of_error_messages_for_unsupported_streams) > 0):
			ffmpeg_error_message = 'Audio streams in file are not supported, only channel counts from 1 to 6 are supported' * english + 'Tiedoston miksaukset eivät ole tuetussa formaatissa, vain kanavamäärät välillä 1 ja 6 ovat tuettuja' * finnish
			send_ffmpeg_error_message_by_email = False

		if (ffmpeg_supported_fileformat == False) and (len(list_of_error_messages_for_unsupported_streams) == 1):
			ffmpeg_error_message = list_of_error_messages_for_unsupported_streams[0][1]
			send_ffmpeg_error_message_by_email = False

		# Don't send email if FFmpeg error message is caused by an unsupported file type, for example a text file dropped to the HotFolder.
		if 'Invalid data found when processing input' in ffmpeg_error_message:
			send_ffmpeg_error_message_by_email = False
			
		# In case the file has only 1 audio stream and the format is ogg then do an additional check.
		# Sox only supports ogg files that have max 2 channels. If there are more then the audio must be converted to another format before processing.
		# 'natively_supported_file_format = False'  means audio must be converted with FFmpeg before prosessing.
		if number_of_ffmpeg_supported_audiostreams > 0: # If ffmpeg found audio streams check if the file extension is one that sox supports (wav, flac, ogg).
			if str(os.path.splitext(filename)[1]).lower() in natively_supported_file_formats:
				natively_supported_file_format = True
				
		if (number_of_ffmpeg_supported_audiostreams == 1) and (str(os.path.splitext(filename)[1]).lower() == '.ogg'): # Test if ogg - file has more than two channels, since sox only supports mono and stereo ogg - files. If there are more channels, audio must be converted before processing.
			if  (number_of_audio_channels != '1') and (number_of_audio_channels != '2'):
				natively_supported_file_format = False
		
		if (number_of_ffmpeg_supported_audiostreams > 1) and (str(os.path.splitext(filename)[1]).lower() == '.ogg'):
			# If there are more than 1 streams in ogg then extract streams with FFmpeg.
			natively_supported_file_format = False
		
		if (str(os.path.splitext(filename)[1]).lower() == '.wav') and (input_audiostream_codec_format not in ['pcm_u8', 'pcm_s16le', 'pcm_s24le', 'pcm_s32le']):
			# Wav container might contain other data than uncompressed pcm, if this is the case then first decompress audio / convert streams with FFmpeg.
			natively_supported_file_format = False
		
		if input_audiostream_codec_format in pcm_64_bit_formats:
			# Bit depth is bigger than 32 bits the file must be converted before processing because sox only supports up to 32 bits.
			natively_supported_file_format = False
		
		# Now we know the number of supported audio streams and total number of audio streams in the file. Move all data gathered for machine readable results file from the local dict to the global temp dict.
		if write_loudness_calculation_results_to_a_machine_readable_file == True:

			if (natively_supported_file_format == True) and (number_of_ffmpeg_supported_audiostreams == 1):

				# In this case the file is a supported single stream file.
				# Replace the stream name with the correct name and add number of supported streams and total number of streams.
				for item in dummy_initial_data_for_machine_readable_results_file:
					dummy_initial_data_for_machine_readable_results_file[item][1][1] = number_of_ffmpeg_supported_audiostreams
					dummy_initial_data_for_machine_readable_results_file[item][1][2] = total_number_of_streams_in_the_file

					temp_loudness_results_for_automation[filename] = dummy_initial_data_for_machine_readable_results_file[item]

			else:
				# In this case the file is a multistream file, and the stream name we stored previously is correct.
				# Add number of supported streams and total number of streams.
				for item in dummy_initial_data_for_machine_readable_results_file:
					dummy_initial_data_for_machine_readable_results_file[item][1][1] = number_of_ffmpeg_supported_audiostreams
					dummy_initial_data_for_machine_readable_results_file[item][1][2] = total_number_of_streams_in_the_file

					temp_loudness_results_for_automation[item] = dummy_initial_data_for_machine_readable_results_file[item]

		# Store information we gathered about the file so that we can return it to the calling function.
		file_format_support_information = [natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames, mxf_audio_remixing, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, number_of_unsupported_streams_in_file]
		
		# Save some debug information.
		if debug_file_processing == True:
			debug_information_list.append('Support information for main file')
			debug_information_list.append(filename)
			debug_information_list.append('ffmpeg_supported_fileformat')
			debug_information_list.append(ffmpeg_supported_fileformat)
			debug_information_list.append('natively_supported_file_format')
			debug_information_list.append(natively_supported_file_format)
			debug_information_list.append('ffmpeg_error_message')
			debug_information_list.append(ffmpeg_error_message)

			if audio_duration_rounded_to_seconds == 0:
				debug_information_list.append('Error Message')
				debug_information_list.append('Audio duration less than 1 second')

			debug_information_list.append('ffmpeg_commandline')
			debug_information_list.append(ffmpeg_commandline)
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'get_audio_stream_information_with_ffmpeg_and_create_extraction_parameters'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)
	
	return(file_format_support_information, ffmpeg_error_message, send_ffmpeg_error_message_by_email)

def get_file_wrapper_format_with_mediainfo(directory_for_temporary_files, filename, hotfolder_path, english, finnish):

	file_to_process = hotfolder_path + os.sep + filename

	mediainfo_output = b''
	mediainfo_output_decoded = ''
	error_message = ''
	wrapper_format = ''

	#####################################################
	# Find out what is the wrapper format of the file   #
	#####################################################
	
	try:
		# Define filename for the temporary file that we are going to use as stdout for the external command.
		stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_mediainfo_find_file_wrapper_format_stdout.txt'
		# Open the stdout temporary file in binary write mode.
		with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
	
			# Get the number of audio streams in the file
			subprocess.Popen(['mediainfo', '--Inform=General;%Format%', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run mediainfo.
	
			# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
			stdout_commandfile_handler.flush() # Flushes written data to os cache
			os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
			
	except IOError as reason_for_error:
		error_message = 'Error writing to mediainfo (file wrapper format) stdout - file ' * english + 'Mediainfon (wräpperi- formaatin selvitys) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error writing to mediainfo (file wrapper format) stdout - file ' * english + 'Mediainfon (wräpperi- formaatin selvitys) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
		
	# Open the file we used as stdout for the external program and read in what the external program wrote to it.
	try:
		with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
			mediainfo_output = stdout_commandfile_handler.read(None)
	except IOError as reason_for_error:
		error_message = 'Error reading from mediainfo (file wrapper format) stdout - file ' * english + 'Mediainfon (wräpperi- formaatin selvitys) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error reading from mediainfo (file wrapper format) stdout - file ' * english + 'Mediainfon (wräpperi- formaatin selvitys) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	
	# Convert mediainfo output from binary to UTF-8 text.
	try:
		mediainfo_output_decoded = mediainfo_output.decode('UTF-8') # Convert mediainfo output from binary to utf-8 text.
	except UnicodeDecodeError:
		# If UTF-8 conversion fails, try conversion with another character map.
		mediainfo_output_decoded = mediainfo_output.decode('ISO-8859-15') # Convert mediainfo output from binary to text.	
		
	# Get the file wrapper format from mediainfo output.
	if (mediainfo_output_decoded.strip() != '') and ('-' not in mediainfo_output_decoded):
		if mediainfo_output_decoded.strip().isalpha() == True:
			wrapper_format = str(mediainfo_output_decoded).strip().lower()
		
	# Delete the temporary stdout - file.
	try:
		os.remove(stdout_for_external_command)
	except IOError as reason_for_error:
		error_message = 'Error deleting mediainfo (file wrapper format) stdout - file ' * english + 'Mediainfon (wräpperi- formaatin selvitys) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])
	except OSError as reason_for_error:
		error_message = 'Error deleting mediainfo (file wrapper format) stdout - file ' * english + 'Mediainfon (wräpperi- formaatin selvitys) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message, [])	

	return(wrapper_format, error_message)

def get_audiofile_info_with_mediainfo(directory_for_temporary_files, filename, hotfolder_path, english, finnish, save_debug_information):

	try:
		global debug
		global natively_supported_file_formats
		
		audio_duration_string = ''
		audio_duration_fractions_string =''
		audio_duration_list = []
		audio_duration_rounded_to_seconds = 0
		
		audiostream_count = 0
		channel_count = 0
		bit_depth = 0
		sample_format = ''
		
		file_to_process = hotfolder_path + os.sep + filename

		mediainfo_output = b''
		mediainfo_output_decoded = ''
		natively_supported_file_format = False
		mediainfo_error_message = ''
		error_message = ''

		# Only save debug information when ffmpeg is not installed and mediainfo is used in its place to find audio from files.
		if save_debug_information == True:

			# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
			if debug_file_processing == True:
				debug_information_list = []
				global debug_temporary_dict_for_all_file_processing_information

				unix_time_in_ticks, realtime = get_realtime(english, finnish)
				debug_information_list.append('Start Time')
				debug_information_list.append(unix_time_in_ticks)
				debug_information_list.append('Subprocess Name')
				debug_information_list.append('get_audiofile_info_with_mediainfo')
				debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		#####################################################
		# Find how many audio streams there are in the file #
		#####################################################
		
		try:
			# Define filename for the temporary file that we are going to use as stdout for the external command.
			stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_mediainfo_find_audiofile_info_stdout.txt'
			# Open the stdout temporary file in binary write mode.
			with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
		
				# Get the number of audio streams in the file
				subprocess.Popen(['mediainfo', '--Inform=General;%AudioCount%', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run mediainfo.
		
				# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
				stdout_commandfile_handler.flush() # Flushes written data to os cache
				os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
				
		except IOError as reason_for_error:
			error_message = 'Error writing to mediainfo (audiostream_count) stdout - file ' * english + 'Mediainfon (audiostreamien lukumäärän selvitys) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error writing to mediainfo  (audiostream_count) stdout - file ' * english + 'Mediainfonn (audiostreamien lukumäärän selvitys) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
			
		# Open the file we used as stdout for the external program and read in what the external program wrote to it.
		try:
			with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
				mediainfo_output = stdout_commandfile_handler.read(None)
		except IOError as reason_for_error:
			error_message = 'Error reading from mediainfo (audiostream_count) stdout - file ' * english + 'Mediainfon (audiostreamien lukumäärän selvitys) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error reading from mediainfo (audiostream_count) stdout - file ' * english + 'Mediainfon (audiostreamien lukumäärän selvitys) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		
		# Convert mediainfo output from binary to UTF-8 text.
		try:
			mediainfo_output_decoded = mediainfo_output.decode('UTF-8') # Convert mediainfo output from binary to utf-8 text.
		except UnicodeDecodeError:
			# If UTF-8 conversion fails, try conversion with another character map.
			mediainfo_output_decoded = mediainfo_output.decode('ISO-8859-15') # Convert mediainfo output from binary to text.	
			
		# Get the audiostream count from mediainfo output.
		if (mediainfo_output_decoded.strip() != '') and ('-' not in mediainfo_output_decoded):
			if mediainfo_output_decoded.strip().isnumeric() == True:
				audiostream_count = int(mediainfo_output_decoded.strip())
			
		# Delete the temporary stdout - file.
		try:
			os.remove(stdout_for_external_command)
		except IOError as reason_for_error:
			error_message = 'Error deleting mediainfo (audiostream_count) stdout - file ' * english + 'Mediainfon (audiostreamien lukumäärän selvitys) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error deleting mediainfo (audiostream_count) stdout - file ' * english + 'Mediainfon (audiostreamien lukumäärän selvitys) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])	


		if audiostream_count == 1:

			######################################################
			# Find how many audio channels there are in the file #
			######################################################
			
			try:
				# Define filename for the temporary file that we are going to use as stdout for the external command.
				stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_mediainfo_find_audiofile_info_stdout.txt'
				# Open the stdout temporary file in binary write mode.
				with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
			
					# Get the number of audio channels in the file
					subprocess.Popen(['mediainfo', '--Inform=Audio;%Channels%', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run mediainfo.
			
					# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
					stdout_commandfile_handler.flush() # Flushes written data to os cache
					os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
					
			except IOError as reason_for_error:
				error_message = 'Error writing to mediainfo (channel_count) stdout - file ' * english + 'Mediainfon (kanavamäärä) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error writing to mediainfo  (channel_count) stdout - file ' * english + 'Mediainfon (kanavamäärä) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
				
			# Open the file we used as stdout for the external program and read in what the external program wrote to it.
			try:
				with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
					mediainfo_output = stdout_commandfile_handler.read(None)
			except IOError as reason_for_error:
				error_message = 'Error reading from mediainfo (channel_count) stdout - file ' * english + 'Mediainfon (kanavamäärä) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error reading from mediainfo (channel_count) stdout - file ' * english + 'Mediainfon (kanavamäärä) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			
			# Convert mediainfo output from binary to UTF-8 text.
			try:
				mediainfo_output_decoded = mediainfo_output.decode('UTF-8') # Convert mediainfo output from binary to utf-8 text.
			except UnicodeDecodeError:
				# If UTF-8 conversion fails, try conversion with another character map.
				mediainfo_output_decoded = mediainfo_output.decode('ISO-8859-15') # Convert mediainfo output from binary to text.	
				
			# Get the channel count from mediainfo output.
			if (mediainfo_output_decoded.strip() != '') and ('-' not in mediainfo_output_decoded):
				if mediainfo_output_decoded.strip().isnumeric() == True:
					channel_count = int(mediainfo_output_decoded.strip())
				
			# Delete the temporary stdout - file.
			try:
				os.remove(stdout_for_external_command)
			except IOError as reason_for_error:
				error_message = 'Error deleting mediainfo (channel_count) stdout - file ' * english + 'Mediainfon (kanavamäärä) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'Error deleting mediainfo (channel_count) stdout - file ' * english + 'Mediainfon (kanavamäärä) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			
			if channel_count != 0:
			
				############################
				# Find out audio bit depth #
				############################
				
				try:
					# Define filename for the temporary file that we are going to use as stdout for the external command.
					stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_mediainfo_find_audiofile_info_stdout.txt'
					# Open the stdout temporary file in binary write mode.
					with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
				
						# Get the bit depth of the audio file
						subprocess.Popen(['mediainfo', '--Inform=Audio;%BitDepth%', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run mediainfo.
				
						# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
						stdout_commandfile_handler.flush() # Flushes written data to os cache
						os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
						
				except IOError as reason_for_error:
					error_message = 'Error writing to mediainfo (bit_depth) stdout - file ' * english + 'Mediainfon (bittisyvyys) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error writing to mediainfo  (bit_depth) stdout - file ' * english + 'Mediainfon (bittisyvyys) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
					
				# Open the file we used as stdout for the external program and read in what the external program wrote to it.
				try:
					with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
						mediainfo_output = stdout_commandfile_handler.read(None)
				except IOError as reason_for_error:
					error_message = 'Error reading from mediainfo (bit_depth) stdout - file ' * english + 'Mediainfon (bittisyvyys) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error reading from mediainfo (bit_depth) stdout - file ' * english + 'Mediainfon (bittisyvyys) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				
				# Convert mediainfo output from binary to UTF-8 text.
				try:
					mediainfo_output_decoded = mediainfo_output.decode('UTF-8') # Convert mediainfo output from binary to utf-8 text.
				except UnicodeDecodeError:
					# If UTF-8 conversion fails, try conversion with another character map.
					mediainfo_output_decoded = mediainfo_output.decode('ISO-8859-15') # Convert mediainfo output from binary to text.
					
				# Get the bit depth from mediainfo output.
				if (mediainfo_output_decoded.strip() != '') and ('-' not in mediainfo_output_decoded):
					if mediainfo_output_decoded.strip().isnumeric() == True:
						bit_depth = int(mediainfo_output_decoded.strip())
					
				# Delete the temporary stdout - file.
				try:
					os.remove(stdout_for_external_command)
				except IOError as reason_for_error:
					error_message = 'Error deleting mediainfo (bit_depth) stdout - file ' * english + 'Mediainfon (bittisyvyys) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error deleting mediainfo (bit_depth) stdout - file ' * english + 'Mediainfon (bittisyvyys) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				
				##########################
				# Find out sample format #
				##########################
				
				try:
					# Define filename for the temporary file that we are going to use as stdout for the external command.
					stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_mediainfo_find_audiofile_info_stdout.txt'
					# Open the stdout temporary file in binary write mode.
					with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
				
						# Get the sample format of the audio file
						subprocess.Popen(['mediainfo', '--Inform=Audio;%Format%', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run mediainfo.
				
						# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
						stdout_commandfile_handler.flush() # Flushes written data to os cache
						os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
						
				except IOError as reason_for_error:
					error_message = 'Error writing to mediainfo (sample_format) stdout - file ' * english + 'Mediainfon (sample formaatti) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error writing to mediainfo  (sample_format) stdout - file ' * english + 'Mediainfon (sample formaatti) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
					
				# Open the file we used as stdout for the external program and read in what the external program wrote to it.
				try:
					with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
						mediainfo_output = stdout_commandfile_handler.read(None)
				except IOError as reason_for_error:
					error_message = 'Error reading from mediainfo (sample_format) stdout - file ' * english + 'Mediainfon (sample formaatti) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error reading from mediainfo (sample_format) stdout - file ' * english + 'Mediainfon (sample formaatti) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				
				# Convert mediainfo output from binary to UTF-8 text.
				try:
					mediainfo_output_decoded = mediainfo_output.decode('UTF-8') # Convert mediainfo output from binary to utf-8 text.
				except UnicodeDecodeError:
					# If UTF-8 conversion fails, try conversion with another character map.
					mediainfo_output_decoded = mediainfo_output.decode('ISO-8859-15') # Convert mediainfo output from binary to text.	
					
				# Get the sample format from mediainfo output.
				if (mediainfo_output_decoded.strip() != '') and ('-' not in mediainfo_output_decoded):
					sample_format = mediainfo_output_decoded.strip().lower()
					
				# Delete the temporary stdout - file.
				try:
					os.remove(stdout_for_external_command)
				except IOError as reason_for_error:
					error_message = 'Error deleting mediainfo (sample_format) stdout - file ' * english + 'Mediainfon (sample formaatti) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error deleting mediainfo (sample_format) stdout - file ' * english + 'Mediainfon (sample formaatti) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				
				#######################
				# Find audio duration #
				#######################
				
				try:
					# Define filename for the temporary file that we are going to use as stdout for the external command.
					stdout_for_external_command = directory_for_temporary_files + os.sep + filename + '_mediainfo_find_audiofile_info_stdout.txt'
					# Open the stdout temporary file in binary write mode.
					with open(stdout_for_external_command, 'wb') as stdout_commandfile_handler:
				
						# Get the audio duration of the file
						subprocess.Popen(['mediainfo', '--Inform=General;%Duration/String3%', file_to_process], stdout=stdout_commandfile_handler, stderr=stdout_commandfile_handler, stdin=None, close_fds=True).communicate()[0] # Run mediainfo.
				
						# Make sure all data written to temporary stdout - file is flushed from the os cache and written to disk.
						stdout_commandfile_handler.flush() # Flushes written data to os cache
						os.fsync(stdout_commandfile_handler.fileno()) # Flushes os cache to disk
						
				except IOError as reason_for_error:
					error_message = 'Error writing to mediainfo (audio duration) stdout - file ' * english + 'Mediainfon (audion kesto) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error writing to mediainfo (audio duration) stdout - file ' * english + 'Mediainfon (audion kesto) stdout - tiedostoon kirjoittaminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
					
				# Open the file we used as stdout for the external program and read in what the external program wrote to it.
				try:
					with open(stdout_for_external_command, 'rb') as stdout_commandfile_handler:
						mediainfo_output = stdout_commandfile_handler.read(None)
				except IOError as reason_for_error:
					error_message = 'Error reading from mediainfo (audio duration) stdout - file ' * english + 'Mediainfon (audion kesto) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error reading from mediainfo (audio duration) stdout - file ' * english + 'Mediainfon (audion kesto) stdout - tiedoston lukeminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				
				# Convert mediainfo output from binary to UTF-8 text.
				try:
					mediainfo_output_decoded = mediainfo_output.decode('UTF-8') # Convert mediainfo output from binary to utf-8 text.
				except UnicodeDecodeError:
					# If UTF-8 conversion fails, try conversion with another character map.
					mediainfo_output_decoded = mediainfo_output.decode('ISO-8859-15') # Convert mediainfo output from binary to text.
				
				# Get the file duration as a string and also calculate it in seconds.
				if (mediainfo_output_decoded.strip() != '') and ('-' not in mediainfo_output_decoded):
					audio_duration_string, audio_duration_fractions_string = mediainfo_output_decoded.split('.') # Split the time string to two variables, the last will hold the fractions part (0 - 999 hundreds of a second).
					audio_duration_list = audio_duration_string.split(':') # Separate each element in the time string (hours, minutes, seconds) and put them in a list.
					audio_duration_rounded_to_seconds = (int(audio_duration_list[0]) * 60 * 60) + (int(audio_duration_list[1]) * 60) + int(audio_duration_list[2]) # Calculate audio duration in seconds.
				
				# Delete the temporary stdout - file.
				try:
					os.remove(stdout_for_external_command)
				except IOError as reason_for_error:
					error_message = 'Error deleting mediainfo (audio duration) stdout - file ' * english + 'Mediainfon (audion kesto) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error deleting mediainfo (audio duration) stdout - file ' * english + 'Mediainfon (audion kesto) stdout - tiedoston deletoiminen epäonnistui ' * finnish  + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])

		###################################################################
		# Decide if the file is one of the natively supported formats	  #
		###################################################################
		
		if (str(os.path.splitext(filename)[1]).lower() in natively_supported_file_formats) and (audiostream_count == 1) and (channel_count != 0) and (channel_count <= 6) and (audio_duration_rounded_to_seconds > 0):
			natively_supported_file_format = True
		else:
			natively_supported_file_format = False
			# Assign a general error message about file format not supported.
			mediainfo_error_message = 'Format: \'' * english + 'Formaatti: \''* finnish + str(sample_format)  + '\' is not supported. Supported formats are: wav (pcm) 1 - 6 channels, flac 1 - 6 channels, ogg vorbis 1 - 2 channels' * english + '\' ei ole tuettu. Tuetut formaatit ovat: wav (pcm) 1 - 6 kanavaa, flac 1 - 6 kanavaa, ogg vorbis  1 - 2 kanavaa' * finnish

		if channel_count == 0:
			mediainfo_error_message = 'There are no audio channels in the file' * english + 'Tiedostossa ei ole äänikanavia' * finnish

		if channel_count > 6:
			mediainfo_error_message = 'There are ' * english + 'Tiedostossa on ' * finnish + str(channel_count) + ' channels in audio file, only channel counts from one to six are supported' * english + ' äänikanavaa, vain kanavamäärät yhdestä kuuteen ovat tuettuja' * finnish
			
		if str(os.path.splitext(filename)[1]).lower() == '.ogg':
			bit_depth = 16
		
		if (str(os.path.splitext(filename)[1]).lower() == '.ogg') and (sample_format != 'vorbis'):
			natively_supported_file_format = False
			mediainfo_error_message =  'Format: \'' * english + 'Formaatti: \'' * finnish + str(sample_format) + '\' is not supported in ogg container' * english + '\' ogg - paketissa ei ole tuettu' * finnish
			
		if (str(os.path.splitext(filename)[1]).lower() == '.ogg') and (channel_count > 2):
			natively_supported_file_format = False
			mediainfo_error_message = 'There are ' * english + 'Tiedostossa on ' * finnish + str(channel_count) + ' channels in audio file, only channel counts from one to two are supported in ogg - format' * english + ' äänikanavaa, vain kanavamäärät yhdestä kahteen ovat tuettuja ogg - formaatissa' * finnish

		if (str(os.path.splitext(filename)[1]).lower() == '.wav') and (sample_format != 'pcm'):
			natively_supported_file_format = False
			mediainfo_error_message =  'Format: \'' * english + 'Formaatti: \'' * finnish + str(sample_format) + '\' is not supported in wav container' * english + '\' wav - paketissa ei ole tuettu' * finnish
		
		if (bit_depth < 8) or (bit_depth > 32):
			natively_supported_file_format = False
			mediainfo_error_message =  'Audio bit depth: ' * english + 'Tiedoston bittisyvyys: ' * finnish + str(bit_depth) + ' bits is not supported' * english + ' bittiä ei ole tuettu' * finnish
			
		if audio_duration_rounded_to_seconds == 0:
			mediainfo_error_message =  'Audio duration is less than 1 second' * english + 'Tiedoston ääniraidan pituus on alle 1 sekunti' * finnish 

		if str(os.path.splitext(filename)[1]).lower() not in natively_supported_file_formats:
			natively_supported_file_format = False
			mediainfo_error_message =  'Format: \'' * english + 'Formaatti: \'' * finnish + str(os.path.splitext(filename)[1]).lower()  + '\' is not supported' * english + '\' ei ole tuettu' * finnish
		
		# Only save debug information when ffmpeg is not installed and mediainfo is used in its place to find audio from files.
		if save_debug_information == True:

			# Save some debug information.
			if debug_file_processing == True:
				debug_information_list.append('File extension')
				debug_information_list.append(str(os.path.splitext(filename)[1]).lower() + "'")
				debug_information_list.append('audiostream_count')
				debug_information_list.append(audiostream_count)
				debug_information_list.append('channel_count')
				debug_information_list.append(channel_count)
				debug_information_list.append('bit_depth')
				debug_information_list.append(bit_depth)
				debug_information_list.append('sample_format')
				debug_information_list.append(sample_format)
				debug_information_list.append('audio_duration_rounded_to_seconds')
				debug_information_list.append(audio_duration_rounded_to_seconds)
				debug_information_list.append('natively_supported_file_format')
				debug_information_list.append(natively_supported_file_format)
				debug_information_list.append('mediainfo_error_message')
				debug_information_list.append(mediainfo_error_message)
				unix_time_in_ticks, realtime = get_realtime(english, finnish)
				debug_information_list.append('Stop Time')
				debug_information_list.append(unix_time_in_ticks)
				debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'get_audiofile_info_with_mediainfo'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	return(audiostream_count, channel_count, bit_depth, sample_format, audio_duration_rounded_to_seconds, natively_supported_file_format, mediainfo_error_message)
	
def debug_write_loudness_calculation_info_to_a_logfile(loudness_calculation_data, target_file):

	try:
		# This subroutine can be used to write loudness calculation data to a text file.
		# It can used to write loudness calculation results of each indivudual file in a text file in results directory.
		#
		# The developer uses it also to process a bunch of test files and save the logfile.
		# When changes are made to critical parts of the program or external helper programs then it can be
		# confirmed that the results from the new version are the same as in the earlier saved file.
		#

		global silent
		global english
		global finnish
		
		try:
			with open(target_file, 'at') as loudness_calculation_logfile_handler:
				loudness_calculation_logfile_handler.write(loudness_calculation_data)
				loudness_calculation_logfile_handler.flush() # Flushes written data to os cache
				os.fsync(loudness_calculation_logfile_handler.fileno()) # Flushes os cache to disk
		except KeyboardInterrupt:
			if silent == False:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error opening loudness calculation logfile for writing ' * english + 'Äänekkyyslogitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error opening loudness calculation logfile for writing ' * english + 'Äänekkyyslogitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'debug_write_loudness_calculation_info_to_a_logfile'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def debug_manage_file_processing_information_thread():
	
	# This subprocess is started in its own thread.
	# This subroutine handles file processing debug information. When debug_file_processing == True, then LoudnessCorrection holds some debug data in memory (default 100 last files) and deletes info older than that.
	# If debug_file_processing == True, then this subroutine periodically saves debug info to disk as a pickle.
	# If debug mode is activated by sending a signal to LoudnessCorrection, then the program starts saving info until debug is cancelled by sending the same signal again.

	try:
		global debug_complete_final_information_for_all_file_processing_dict
		global debug_file_processing
		global debug_all
		global completed_files_list
		global english
		global finnish
		global quit_all_threads_now

		default_sleep_time_until_next_file_save = 10 * 60 # How often do we save debug information to disk. Default time is 10 minutes (10 * 60 seconds).

		if debug_all == True:
			default_sleep_time_until_next_file_save = 2 * 60 # We are in 'debug_all' mode, save more often.

		sleep_time_until_next_file_save = default_sleep_time_until_next_file_save
		real_time_string = get_realtime(english, finnish)[1]
		filename_for_processing_debug_info = 'debug-file_processing_info-' + real_time_string + '.pickle'
		filename_change_interval = 24 * 60 * 60 # Periodically change filename where to save to. Default 24 hours starting from LoudnessCorrection startup.
		filename_last_change_time = int(time.time())
		old_value_of_debug_file_processing = debug_file_processing

		while True:

			if debug_file_processing == False:

				# Find debug data that is too old and delete it.
				# When debug mode is on then a list of 100 last processed files is gathered for printing the filenames on the html progress report. We use the names on that list here also.
				# Delete debug data about all other files, but leave those that are on the 100 list.
				copy_of_completed_files_list = copy.deepcopy(completed_files_list)
				list_of_dictionary_keys = list(debug_complete_final_information_for_all_file_processing_dict)

				for filename in list_of_dictionary_keys:
					if filename not in copy_of_completed_files_list:
						del debug_complete_final_information_for_all_file_processing_dict[filename]

			else:
				# Debug mode is on, save data periodically to disk

				# Save the dictionary to disk if it is not empty.
				if len(debug_complete_final_information_for_all_file_processing_dict) != 0:
					try:
						with open(directory_for_error_logs + os.sep + filename_for_processing_debug_info, 'wb') as filehandler:
							pickle.dump(debug_complete_final_information_for_all_file_processing_dict, filehandler)
							filehandler.flush() # Flushes written data to os cache
							os.fsync(filehandler.fileno()) # Flushes os cache to disk

						# If file save succeeds wait the default time period before saving again.
						sleep_time_until_next_file_save = default_sleep_time_until_next_file_save

					except KeyboardInterrupt:
						print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
						sys.exit(0)
					except IOError as reason_for_error:
						error_message = 'Error opening debug file processing pickle - file  for writing ' * english + 'Tiedostoprosessoinnin debug - tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
						send_error_messages_to_screen_logfile_email(error_message, [])
					except OSError as reason_for_error:
						error_message = 'Error opening debug file processing pickle - file  for writing ' * english + 'Tiedostoprosessoinnin debug - tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
						send_error_messages_to_screen_logfile_email(error_message, [])
					except RuntimeError:
						# If the debug dictionary is changed by another thread in the middle of this thread writing it to disk, then a RuntimeError is raised and the save fails.
						# If save fails then try again in 10 seconds.
						sleep_time_until_next_file_save = 10
				
				# Check if we have saved too long to the same file and need to change the filename.
				if int(time.time()) >= int(filename_last_change_time + filename_change_interval):

					real_time_string = get_realtime(english, finnish)[1]
					filename_for_processing_debug_info = 'debug-file_processing_info-' + real_time_string + '.pickle'
					filename_last_change_time = int(time.time())
					
					# We have changed the filename, delete all debug data that is older than file save interval + 1 minute.
					# This takes care that each file saved don't have too much duplicate data in them.
					list_of_dictionary_keys = list(debug_complete_final_information_for_all_file_processing_dict)
					
					for filename in list_of_dictionary_keys:
						info_timestamp = debug_complete_final_information_for_all_file_processing_dict[filename][1]
						if int(time.time()) >= int(info_timestamp + default_sleep_time_until_next_file_save + 60):
							del debug_complete_final_information_for_all_file_processing_dict[filename]

			# Wait a couple of minutes before processing data again.
			# In the mean time check if user has turned debugging on by sending a signal to LoudnessCorrection.
			# If debugging has been turned on then exit loop and save debug data immediately.

			counter = 0
			sleep_time = 10

			while counter < sleep_time_until_next_file_save:
				time.sleep(sleep_time)

				if debug_file_processing != old_value_of_debug_file_processing:
					old_value_of_debug_file_processing = debug_file_processing

					if debug_file_processing == True:
						break

				# Check if the main routine asks us to exit now. This is used when running regression tests.
				if quit_all_threads_now == True:
					return()

				counter = counter + sleep_time

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'debug_manage_file_processing_information_thread'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def signal_handler_routine(signal_number, stack_frame):
	
	# This routine catches SIGUSR1 and SIGUSR2 sent from the outside world to LoudnessCorrection.
	#
	# SIGUSR1 flips the state of variable 'debug_file_processing' between True / False which in turn starts / stops writing of file processing debug info to disk.
	# SIGUSR2 flips the state of variable 'debug_all' between True / False which in turn starts / stops writing of all debugging information to disk.
	#
	# All debugging information means:
	#
	# - File processing
	# - Variables lists and dictionaries
	# - Loudness measurement results
	#
	# Debugging information is written to the directory '00-Error_Logs' that is in the same subdirectory as 'LoudnessCorrection'.

	try:
		global debug_all
		global debug_lists_and_dictionaries
		global debug_file_processing
		global save_all_measurement_results_to_a_single_debug_file

		# Handle SIGUSR1
		if signal_number == 10:

			if debug_file_processing == False:
				debug_file_processing = True
			else:
				debug_file_processing = False

		# Handle SIGUSR2
		if signal_number == 12:

			if debug_all == False:
				debug_all = True
				debug_lists_and_dictionaries  = True
				debug_file_processing = True
				save_all_measurement_results_to_a_single_debug_file = True
			else:
				debug_all = False
				debug_lists_and_dictionaries  = False 
				debug_file_processing = False
				save_all_measurement_results_to_a_single_debug_file = False

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'signal_handler_routine'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def check_samba_file_locks(filename):

	try:
		global silent
		global directory_for_temporary_files
		file_is_locked_by_samba = False
		stdout = b''
		stderr = b''

		# Create the commandline we need to run.
		commands_to_run = ['smbstatus', '-L']

		try:
			# Define filenames for temporary files that we are going to use as stdout and stderr for the external command.
			stdout_for_external_command = directory_for_temporary_files + os.sep + 'Smbstatus_command_stdout.txt'
			stderr_for_external_command = directory_for_temporary_files + os.sep + 'Smbstatus_command_stderr.txt'

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

		if filename in stdout:
			file_is_locked_by_samba = True

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'check_samba_file_locks'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	return(file_is_locked_by_samba)

def catch_python_interpreter_errors(error_message_as_a_list, subroutine_name):

	# This subroutine is used to catch error messages from the python interpreter.
	# When some line of code in LoudnessCorrection.py causes an error in the python interpreter, the python error message is sent to screen, logfile, email depending on user settings.
	# The main purpose of this subroutine is to reveal difficult to find bugs that happen only in specific circumstances.

	global critical_python_error_has_happened
	global list_of_critical_python_errors

	# Setting this global variable to 'True' triggers the email sending_thread to stop waiting and causes it to send error messages immediately.
	critical_python_error_has_happened = True
	
	error_message = "Critical Python Error in subroutine: '" + subroutine_name + "'"  + '\n\n'  + '\n'.join(error_message_as_a_list)

	# Only send a error message once.
	if error_message not in list_of_critical_python_errors:
		list_of_critical_python_errors.append(error_message)
		send_error_messages_to_screen_logfile_email(error_message, [])

def read_audio_remix_map_file(hotfolder_path, audio_file_name, english, finnish):

	# This subroutine checks if there is file specific text file on disk holding a audio remix channel map for the file.
	# If a file specific remix map is found then it is returned, otherwise the global remix channel map is returned

	try:

		text_lines_list = []
		global global_mxf_audio_remix_channel_map
		audio_remix_channel_map = []

		global remix_map_file_extension
		remix_mapfile_name = hotfolder_path + os.sep + os.path.splitext(audio_file_name)[0] + remix_map_file_extension

		# Read remix_map - file from disk.
		if (os.path.exists(remix_mapfile_name) == True):
			try:
				with open(remix_mapfile_name, 'rt') as remix_mapfile_handler: # Open logfile, the 'with' method closes files when execution exits the with - block
					remix_mapfile_handler.seek(0) # Make sure that the 'read' - pointer is in the beginning of the source file
					text_lines_list.extend(remix_mapfile_handler.readlines())													      

			except IOError as reason_for_error:
				error_message = 'A mxf - file remix channel map file was found, but it can not be read: ' * english + 'Mxf - tiedoston uudelleenmiksauksen ohjetiedosto löytyi, mutta sitä ei voi lukea: ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])
			except OSError as reason_for_error:
				error_message = 'A mxf - file remix channel map file was found, but it can not be read: ' * english + 'Mxf - tiedoston uudelleenmiksauksen ohjetiedosto löytyi, mutta sitä ei voi lukea: ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message, [])

			# Find comma separated numbers in text file.
			for item in text_lines_list:

				# Strip line ending and tab - characters.
				item = item.strip('\n')
				item = item.strip('\t')

				# If the first charecter on the text line is '#' (a comment line), or the line is empty, then skip the line.
				if item.strip() == '':
					continue
				if item.strip()[0] == '#':
					continue

				temporary_remix_map_list =  item.split(',')

				# Convert numbers in string format to integer.
				for number_in_str_format in temporary_remix_map_list:

					if (number_in_str_format.isnumeric() == True) and (int(number_in_str_format) >0):
						number = int(number_in_str_format)
						audio_remix_channel_map.append(number)

				# If a text line with some numbers were found, then don't process the lines after that.
				if len(audio_remix_channel_map) > 0:
					break

		if len(audio_remix_channel_map) < 1:
			audio_remix_channel_map = global_mxf_audio_remix_channel_map

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'read_audio_remix_map_file'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	return(audio_remix_channel_map)

def remix_files_according_to_channel_map(directory_for_temporary_files, original_input_file_name, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, english, finnish):

	# This subroutine calls a subroutine that creates sox commands to remix audio channels found in a mxf - file.
	# Then this routine starts as many sox processess in simultaneous threads as needed to create the mixes.
	#
	# The comma separated values in a 'remix_map' - file are used as the basis for how many channels each mix contains.
	# For example the channel map: 2,6,2,2 instructs us to form four mixes: stereo, 5.1, stereo, stereo.
	# If there are more channel map values than there are available channels, then only the mixes that we have enough channels are created.

	try:
		list_of_files_to_move_to_loudness_processing = []
		list_of_sox_commandlines = []
		list_of_files_that_match_exactly_a_channel_map = []

		global directory_for_results
		global silent
		global adjust_line_printout
		global write_loudness_calculation_results_to_a_machine_readable_file
		global temp_loudness_results_for_automation
		initial_data_for_machine_readable_results_file = {}

		list_of_sox_commandlines, list_of_files_that_match_exactly_a_channel_map, list_of_files_to_move_to_loudness_processing	= create_sox_commands_to_remix_audio(directory_for_temporary_files, original_input_file_name, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, english, finnish)

		if len(list_of_files_that_match_exactly_a_channel_map) > 0:

			# if there are some source files that don't need to be combined with other files, but can be used directly, then rename them with the final output names.
			for item in list_of_files_that_match_exactly_a_channel_map:

				source_file_name = item[0]
				target_file_name = item[1]

				# Add info about the mix to dictionary that is used to write the machine readable results file.
				if write_loudness_calculation_results_to_a_machine_readable_file == True:

					# Store initial data for the mix.
					initial_data_for_machine_readable_results_file[target_file_name] = [original_input_file_name, [0, 0, 0, True, 0, 0, 0, 0, 0, 0, 0, 0, 0, ' ', []]]

				try:
					shutil.move(directory_for_temporary_files + os.sep + source_file_name, directory_for_temporary_files + os.sep + target_file_name)

					# Filenames that were not remixed with other files, but were used as they are needs to be added to the list of files that needs to be moved back to hotfolder for loudness processing.
					list_of_files_to_move_to_loudness_processing.append(target_file_name)

				except IOError as reason_for_error:
					error_message = 'Error renaming a file in temp directory ' * english + 'Väliaikaisten tiedostojen hakemistossa olevan tiedoston uudelleen nimeäminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])
				except OSError as reason_for_error:
					error_message = 'Error renaming a file in temp directory ' * english + 'Väliaikaisten tiedostojen hakemistossa olevan tiedoston uudelleen nimeäminen epäonnistui ' * finnish + str(reason_for_error)
					send_error_messages_to_screen_logfile_email(error_message, [])

		# Add info about the mix to dictionary that is used to write the machine readable results file.
		if write_loudness_calculation_results_to_a_machine_readable_file == True:

			for item in list_of_files_to_move_to_loudness_processing:

				# Store initial data for the mix.
				initial_data_for_machine_readable_results_file[item] = [original_input_file_name, [0, 0, 0, True, 0, 0, 0, 0, 0, 0, 0, 0, 0, ' ', []]]

			# Now we know how many audiomixes there will be after remixing, so fill in the information.
			keys_for_dummy_initial_data_for_machine_readable_results_file = list(initial_data_for_machine_readable_results_file)
			keys_for_dummy_initial_data_for_machine_readable_results_file.sort()
			counter = 0

			for item in keys_for_dummy_initial_data_for_machine_readable_results_file:
				
				counter = counter + 1

				initial_data_for_machine_readable_results_file[item][1][0] = counter # The number of this mix.
				initial_data_for_machine_readable_results_file[item][1][1] = len(list_of_files_to_move_to_loudness_processing) # Total number of mixes.
				initial_data_for_machine_readable_results_file[item][1][2] = initial_data_for_machine_readable_results_file[item][1][1] # Total number of mixes equals the total number of supported files. This is because when we remix files, the number of possible unsupported streams in the original source file becomes meaningless and we can't use that information.

				temp_loudness_results_for_automation[item] = initial_data_for_machine_readable_results_file[item]

		# Run sox commands to create the mixes defined in channel maps.
		if len(list_of_sox_commandlines) > 0:

			if silent == False:
				print('\r' + adjust_line_printout, ' Remixing audio channels from file: ' * english + ' Yhdistän tiedoston: ' * finnish + original_input_file_name + ' äänikanavat uudestaan kanavakartan mukaan: ' * finnish + ' according to remix map: ' * english, end='')
				for item in audio_remix_channel_map:
					print(str(item) + '  ', end='')
				print()

			run_sox_commands_in_parallel_threads(directory_for_temporary_files, directory_for_results, original_input_file_name, list_of_sox_commandlines, english, finnish)

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'remix_files_according_to_channel_map'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	return(list_of_files_to_move_to_loudness_processing)

def create_sox_commands_to_remix_audio(directory_for_temporary_files, original_input_file_name, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, english, finnish):

	# This subroutine takes a list of available audiofiles and channels in a mxf - file and uses the remix map to create sox commands that are needed to produce the mixes.

	try:
		available_source_channels_list = []
		sox_file_combination_command_base = ['sox']
		current_sox_command = []
		list_of_sox_commandlines = []
		list_of_filenames_to_combine = []
		list_of_channels_to_extract = []
		list_of_files_that_match_exactly_a_channel_map = [] # A list of files that need not be combined with other files, but can be processed as it is.
		dont_create_sox_commands_for_this_mix = False
		source_file_name = ''
		filename_and_extension = os.path.splitext(original_input_file_name)
		output_filename = ''
		target_filenames = []
		remix_number = 0
		flac_compression_level = ['-C', '1']

		# Save some debug information. Items are always saved in pairs (Title, value) so that the list is easy to parse later.
		if debug_file_processing == True:
			debug_information_list = []
			global debug_temporary_dict_for_all_file_processing_information

			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Start Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_information_list.append('Subprocess Name')
			debug_information_list.append('create_sox_commands_to_remix_audio')
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

		# Create a list with all source audiofile channels layed out as a flat list. Add also number of channels in file and source channel number to each source_file_name.
		for item in filenames_and_channel_counts_for_mxf_audio_remixing:

			# Skip invalid items if found.
			if item == []:
				continue

			source_file_name = item[0]
			number_of_channels_in_file = int(item[1])

			# Skip invalid items if found.
			if (source_file_name == '') or (number_of_channels_in_file <1):
				continue

			for source_channel_number in range(0, number_of_channels_in_file):
				available_source_channels_list.append([source_file_name, number_of_channels_in_file, source_channel_number + 1])

		# Create sox commands to combine audiofiles and channels that fulfill the mixes defined in channel maps.
		# The sox commands simultaneously combine needed source files and extract the channels needed from them to create mixes defined in channel maps.
		if len(available_source_channels_list) > 0:

			for number_of_channels_in_a_map_item in audio_remix_channel_map: # Get a channel map. This is a number that tells how many channels there are in the mix.

				list_of_filenames_to_combine = []
				list_of_channels_to_extract = []
				current_sox_command = []
				channel_counter = 0
				dont_create_sox_commands_for_this_mix = False
				current_sox_command.extend(sox_file_combination_command_base)
				remix_number = remix_number + 1

				# Pop out items in the flat audiofile channel list and gather needed filenames and channel numbers to create a sox command needed to create the mix defined in a channel map.
				for channel in range(0, number_of_channels_in_a_map_item):

					if len(available_source_channels_list) < 1:
						break

					source_file_name, channel_count, channel_number = available_source_channels_list.pop(0)

					# Use the first channel number we get from the flat audiofile channel list as the basis for sox channel extraction command channel number and count channels up from there.
					# This ensures that channels in a file possibly used creating the previous mix in channel map are not used again in creating the next mix in the channel map.
					if channel_counter == 0:
						channel_counter = channel_number

						# If the file channel count is equal to the number of channel needed to create a mix, then we don't need to remix the file, it can be processed as it is.
						if (channel_number == 1) and (channel_count == number_of_channels_in_a_map_item):

							# Create a name for the ouput file.
							output_filename  = filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + str(remix_number) + '-ChannelCount-' * english + '-AaniKanavia-' * finnish + str(number_of_channels_in_a_map_item) + os.path.splitext(source_file_name)[1]
							list_of_files_that_match_exactly_a_channel_map.append([source_file_name, output_filename])

							dont_create_sox_commands_for_this_mix = True

				
					# Gather all file names needed in creating a mix to a list.
					if source_file_name not in list_of_filenames_to_combine:
						list_of_filenames_to_combine.append(source_file_name)

					# Gather all channel numbers needed in creating a mix to list.
					list_of_channels_to_extract.append(str(channel_counter))
					channel_counter = channel_counter + 1

				# If all input files were not found then this mix can't be created, skip item.
				if len(list_of_channels_to_extract) != number_of_channels_in_a_map_item:
					dont_create_sox_commands_for_this_mix = True

				# Create sox commands to combine files and extract channels from the combined file to fullfill the mixes defined in audio_remix_channel_map.
				# Outputfile is always in flac - format, since the mix is just an intermediate file, the final file is created after loudness measurement.
				# The mix size might be over 4 GB, so it is safest to always use flac.
				if dont_create_sox_commands_for_this_mix == False:
					# Create a name for the output file.
					output_filename  = filename_and_extension[0] + '-AudioStream-' * english + '-Miksaus-' * finnish + str(remix_number) + '-ChannelCount-' * english + '-AaniKanavia-' * finnish + str(number_of_channels_in_a_map_item) + '.flac'

					# Add output filenames to a list so that they can later easily be moved from temporary directory to the target directory.
					target_filenames.append(output_filename)

					# If the mix can be derived from a single multichannel file, then don't use the sox combine source files command '-M'.
					# If multiple input files needs to be combined to get a mix, then use the '-M' command.
					if len(list_of_filenames_to_combine) > 1:
						current_sox_command.append('-M')

					# Create sox command to remix this channel map item.
					for item in list_of_filenames_to_combine:
						current_sox_command.append(directory_for_temporary_files + os.sep + item)
					current_sox_command.extend(flac_compression_level)
					current_sox_command.append(directory_for_temporary_files + os.sep + output_filename)
					current_sox_command.append('remix')
					current_sox_command.extend(list_of_channels_to_extract)

					# Gather all sox commands to a list.
					list_of_sox_commandlines.append(current_sox_command)

				# Stop if all available audio channels in source files have been assigned to ouput files based on channel_maps.
				if len(available_source_channels_list) < 1:
					break

		# Save some debug information.
		if debug_file_processing == True:
			debug_information_list.append('list_of_sox_commandlines')
			debug_information_list.append(list_of_sox_commandlines)
			debug_information_list.append('list_of_files_that_match_exactly_a_channel_map')
			debug_information_list.append(list_of_files_that_match_exactly_a_channel_map)
			unix_time_in_ticks, realtime = get_realtime(english, finnish)
			debug_information_list.append('Stop Time')
			debug_information_list.append(unix_time_in_ticks)
			debug_temporary_dict_for_all_file_processing_information[filename] = debug_information_list

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'create_sox_commands_to_remix_audio'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

	return(list_of_sox_commandlines, list_of_files_that_match_exactly_a_channel_map, target_filenames)

def write_loudness_results_and_file_info_to_a_machine_readable_file(filename, data_for_machine_readable_results_file):

	try:
		# This subroutine can be used to write loudness calculation data and techinal data about processed files into a machine readable file.

		global silent
		global english
		global finnish
		global directory_for_temporary_files
		global directory_for_results
		global unit_separator
		global record_separator

		# Find how many results lists there are. There is one list for each output mix.
		number_of_results_lists = len(data_for_machine_readable_results_file)

		if number_of_results_lists > 1:
			data_for_machine_readable_results_file.sort() # Sort data according to stream numbers, so that the file will be more easily read.

		machine_readable_data = ''

		output_filename_extension = '-machine_readable_results.txt'
		temp_file_path = directory_for_temporary_files + os.sep + filename + output_filename_extension
		final_file_path = directory_for_results + os.sep + filename + output_filename_extension

		counter1 = 0

		while counter1 < number_of_results_lists:

			# Get one list from the list of lists. The method for getting one list is different in case there is only one list or if there is many.
			if number_of_results_lists > 1:

				data_for_one_mix = data_for_machine_readable_results_file[counter1]
			else:
				data_for_one_mix = data_for_machine_readable_results_file[0]

			data_converted_to_a_string = ''

			# Get item value out of the list.
			for counter2 in range(0, len(data_for_one_mix)):

				one_value = data_for_one_mix[counter2]

				#########################################################################################################################
				# If the item is a list, then it is a list of output filenames and we need to add them separately to the data string using the unit separator character.

				if 'list' in str(type(one_value)):

					for counter3 in range(0, len(one_value)):

						file_name = one_value[counter3]

						data_converted_to_a_string = data_converted_to_a_string + str(file_name)

						# Only append the unit separator character if this item is not the last item.
						if counter3 < len(one_value) -1:
							data_converted_to_a_string = data_converted_to_a_string + unit_separator

					# Add the record separator character / string at the end of a data line.
					data_converted_to_a_string = data_converted_to_a_string + record_separator

					# The list of output files is always at end of the results list, so there are no more values after that. We jump ahead to process the next results list.
					continue

				#########################################################################################################################

				# This part of the loop runs only for values before the list of output filenames at the end of each results list.
				data_converted_to_a_string = data_converted_to_a_string + str(one_value)

				data_converted_to_a_string = data_converted_to_a_string + unit_separator

			machine_readable_data = machine_readable_data + data_converted_to_a_string

			counter1 = counter1 + 1

		try:
			with open(temp_file_path, 'wt') as machine_readable_results_file_handler:
				machine_readable_results_file_handler.write(machine_readable_data)
				machine_readable_results_file_handler.flush() # Flushes written data to os cache
				os.fsync(machine_readable_results_file_handler.fileno()) # Flushes os cache to disk

		except KeyboardInterrupt:
			if silent == False:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error opening machine readable results file for writing ' * english + 'Koneluettavan äänekkyyslogitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error opening machine readable results file for writing ' * english + 'Koneluettavan äänekkyyslogitiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])

		# Move the results file from the temp dir to the results dir.

		try:
			shutil.move(temp_file_path, final_file_path)
		except KeyboardInterrupt:
			if silent == False:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error moving machine readable results file to results directory ' * english + 'Koneluettavan äänekkyyslogitiedoston siirtäminen tulosten hakemistoon epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error moving gnuplot graphics file ' * english + 'Gnuplotin grafiikkatiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
		subroutine_name = 'write_loudness_results_and_file_info_to_a_machine_readable_file'
		catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

def write_user_defined_configuration_settings_to_logfile():
	
	# Gather info about user defined configuration options to list. This list will be saved to the error log directory if debug_all mode is on.
	# This log helps to see if configuration options user made in the installer are correctly transferred to LoudnessCorrection.py
	global directory_for_error_logs
	global english
	global finnish

	user_defined_configuration_options = [] 

	user_defined_configuration_options.append('')
	title_text = '\nConfiguration variables written to ' + configfile_path + ' are:'
	user_defined_configuration_options.append(title_text)
	user_defined_configuration_options.append(str((len(title_text) + 1) * '-')) # Print a line exactly the length of the title text line + 1.
	user_defined_configuration_options.append('freelcs_version = ' + all_settings_dict['freelcs_version'])
	user_defined_configuration_options.append('os_name = ' + all_settings_dict['os_name'])
	user_defined_configuration_options.append('os_version = ' + all_settings_dict['os_version'])
	user_defined_configuration_options.append('os_init_system_name = ' + all_settings_dict['os_init_system_name'])
	user_defined_configuration_options.append('libebur128_path = ' + all_settings_dict['libebur128_path'])
	user_defined_configuration_options.append('----------------------------------------------------------------------------------------------------')
	user_defined_configuration_options.append('')
	user_defined_configuration_options.append('target_path = ' + all_settings_dict['target_path'])
	user_defined_configuration_options.append('language = ' + all_settings_dict['language'])
	user_defined_configuration_options.append('english = ' + str(all_settings_dict['english']))
	user_defined_configuration_options.append('finnish = ' + str(all_settings_dict['finnish']))
	user_defined_configuration_options.append('hotfolder_path = ' + all_settings_dict['hotfolder_path'])
	user_defined_configuration_options.append('directory_for_temporary_files = ' + all_settings_dict['directory_for_temporary_files'])
	user_defined_configuration_options.append('directory_for_results = ' + all_settings_dict['directory_for_results'])
	user_defined_configuration_options.append('directory_for_error_logs = ' + all_settings_dict['directory_for_error_logs'])
	user_defined_configuration_options.append('delay_between_directory_reads = ' + str(all_settings_dict['delay_between_directory_reads']))
	user_defined_configuration_options.append('number_of_processor_cores = ' + str(all_settings_dict['number_of_processor_cores']))
	user_defined_configuration_options.append('file_expiry_time = ' + str(all_settings_dict['file_expiry_time']))
	user_defined_configuration_options.append('----------------------------------------------------------------------------------------------------')
	user_defined_configuration_options.append('')
	user_defined_configuration_options.append('send_error_messages_by_email = ' + str(all_settings_dict['send_error_messages_by_email']))

	email_details_dict = all_settings_dict['email_sending_details']
	keys_in_email_details_dict = list(email_details_dict)
	keys_in_email_details_dict.sort()
	for item in keys_in_email_details_dict:
		if item == 'smtp_password':
			if email_details_dict['smtp_password'] == '':
				user_defined_configuration_options.append('smtp_password:')
			else:
				user_defined_configuration_options.append('smtp_password: **********')
		else:
			user_defined_configuration_options.append(item + ': ' + str(email_details_dict[item]))

	user_defined_configuration_options.append('where_to_send_error_messages = ' + ', '.join(all_settings_dict['where_to_send_error_messages']))
	user_defined_configuration_options.append('send_error_messages_to_logfile = '+ str(all_settings_dict['send_error_messages_to_logfile']))
	user_defined_configuration_options.append('heartbeat = ' + str(all_settings_dict['heartbeat']))
	user_defined_configuration_options.append('heartbeat_file_name = ' + all_settings_dict['heartbeat_file_name'])
	user_defined_configuration_options.append('heartbeat_write_interval = ' + str(all_settings_dict['heartbeat_write_interval']))
	user_defined_configuration_options.append('----------------------------------------------------------------------------------------------------')
	user_defined_configuration_options.append('')
	user_defined_configuration_options.append('write_html_progress_report = ' + str(all_settings_dict['write_html_progress_report']))
	user_defined_configuration_options.append('html_progress_report_write_interval = ' + str(all_settings_dict['html_progress_report_write_interval']))
	user_defined_configuration_options.append('web_page_name = ' + all_settings_dict['web_page_name'])
	user_defined_configuration_options.append('web_page_path = ' + all_settings_dict['web_page_path'])
	user_defined_configuration_options.append('peak_measurement_method = ' + all_settings_dict['peak_measurement_method'])
	user_defined_configuration_options.append('----------------------------------------------------------------------------------------------------')
	user_defined_configuration_options.append('')
	user_defined_configuration_options.append('create_loudness_corrected_files = ' + str(all_settings_dict['create_loudness_corrected_files']))
	user_defined_configuration_options.append('create_loudness_history_graphics_files = ' + str(all_settings_dict['create_loudness_history_graphics_files']))
	user_defined_configuration_options.append('delete_original_file_immediately = ' + str(all_settings_dict['delete_original_file_immediately']))
	user_defined_configuration_options.append('write_loudness_calculation_results_to_a_machine_readable_file = ' + str(all_settings_dict['write_loudness_calculation_results_to_a_machine_readable_file']))

	variable_string = all_settings_dict['unit_separator']
	characters_in_ascii = '' 

	for item in variable_string:
		characters_in_ascii = characters_in_ascii + str(ord(item)) + ', ' 
	characters_in_ascii = characters_in_ascii[0:len(characters_in_ascii)-2]
	user_defined_configuration_options.append('unit_separator (ascii numbers)  = ' + characters_in_ascii)

	variable_string = all_settings_dict['record_separator']
	characters_in_ascii = ''

	for item in variable_string:
		characters_in_ascii = characters_in_ascii + str(ord(item)) + ', '
	characters_in_ascii = characters_in_ascii[0:len(characters_in_ascii)-2]
	user_defined_configuration_options.append('record_separator (ascii numbers)  = ' + characters_in_ascii)
	user_defined_configuration_options.append('----------------------------------------------------------------------------------------------------')
	user_defined_configuration_options.append('')
	user_defined_configuration_options.append('enable_mxf_audio_remixing = ' + str(all_settings_dict['enable_mxf_audio_remixing']))
	user_defined_configuration_options.append('remix_map_file_extension = ' + all_settings_dict['remix_map_file_extension'])
	temporary_string_list = []
	for number in all_settings_dict['global_mxf_audio_remix_channel_map']:
		temporary_string_list.append(str(number))
	user_defined_configuration_options.append('global_mxf_audio_remix_channel_map = ' + ', '.join(temporary_string_list))
	temporary_string_list = []
	user_defined_configuration_options.append('natively_supported_file_formats = ' + ', '.join(all_settings_dict['natively_supported_file_formats']))
	user_defined_configuration_options.append('ffmpeg_free_wrapper_formats = ' + ', '.join(all_settings_dict['ffmpeg_free_wrapper_formats']))
	user_defined_configuration_options.append('mxf_formats = ' + ', '.join(all_settings_dict['mxf_formats']))
	user_defined_configuration_options.append('mpeg_wrapper_formats = ' + ', '.join(all_settings_dict['mpeg_wrapper_formats']))
	user_defined_configuration_options.append('ffmpeg_free_codec_formats = ' + ', '.join(all_settings_dict['ffmpeg_free_codec_formats']))
	user_defined_configuration_options.append('ffmpeg_allowed_wrapper_formats = ' + ', '.join(all_settings_dict['ffmpeg_allowed_wrapper_formats']))
	user_defined_configuration_options.append('ffmpeg_allowed_codec_formats = ' + ', '.join(all_settings_dict['ffmpeg_allowed_codec_formats']))
	user_defined_configuration_options.append('enable_all_nonfree_ffmpeg_wrapper_formats = ' + str(all_settings_dict['enable_all_nonfree_ffmpeg_wrapper_formats']))
	user_defined_configuration_options.append('enable_all_nonfree_ffmpeg_codec_formats = ' + str(all_settings_dict['enable_all_nonfree_ffmpeg_codec_formats']))
	user_defined_configuration_options.append('ffmpeg_output_wrapper_format = ' + all_settings_dict['ffmpeg_output_wrapper_format'])
	user_defined_configuration_options.append('enable_mxf_wrapper = ' + str(all_settings_dict['enable_mxf_wrapper']))                                                                            
	user_defined_configuration_options.append('enable_webm_wrapper = ' + str(all_settings_dict['enable_webm_wrapper']))                                                                          
	user_defined_configuration_options.append('enable_mpeg_wrappers = ' + str(all_settings_dict['enable_mpeg_wrappers']))                                                                          
	user_defined_configuration_options.append('enable_mp1_codec = ' + str(all_settings_dict['enable_mp1_codec']))                                                                                
	user_defined_configuration_options.append('enable_mp2_codec = ' + str(all_settings_dict['enable_mp2_codec'])) 
	user_defined_configuration_options.append('----------------------------------------------------------------------------------------------------')
	user_defined_configuration_options.append('')
	user_defined_configuration_options.append('silent = ' + str(all_settings_dict['silent']))
	user_defined_configuration_options.append('number_of_all_items_in_dictionary = ' + str(all_settings_dict['number_of_all_items_in_dictionary']))
	user_defined_configuration_options.append('config_file_created_by_installer_version = ' + all_settings_dict['config_file_created_by_installer_version'])
	user_defined_configuration_options.append('----------------------------------------------------------------------------------------------------')
	user_defined_configuration_options.append('')

	########################################################################################
	# Write settings that user defined during the installation to directory_for_error_logs #
	########################################################################################

	# Define logfile name
	installation_logfile_name = 'freelcs_installation_settings_' + str(get_realtime(english, finnish)[1]).replace(' ','_').replace(':','.') + '.txt'

	try:
		with open(directory_for_error_logs + os.sep + installation_logfile_name, 'wt') as installation_logfile_handler:
			installation_logfile_handler.write('\n'.join(user_defined_configuration_options))
			installation_logfile_handler.flush() # Flushes written data to os cache
			os.fsync(installation_logfile_handler.fileno()) # Flushes os cache to disk
	except IOError:
		# if writing fails, fail silently
		pass
	except OSError:
		# if writing fails, fail silently
		pass


##############################################################################################
#				 The main program starts here:)				     #
##############################################################################################
#
# Start the program by giving full path to the target directory.
# The program creates directories in the target, the most important ones are: '00-LoudnessCorrection', '00-LoudnessCorrection/00-Corrected_Files'.
# The program polls the '00-LoudnessCorrection' directory periodically, by default every 5 seconds.
# The program uses various dictionaries and lists for keeping track of files going through different stages of processing. The most importand variables are:
#	'number_of_processor_cores'
# The value in this variable divided by two defines how many files we can process simultaneously.
# Two processes in separate threads are started simultaneously for each file. The first calculates integrated loudness and loudness range. The second process calculates loudness by segmenting the file to time slices and calculates loudness of each slice individually. Slice duration is 0.5 secs for files 9 secs or shorter and 3 secs for files 10 seconds or longer.
# Timeslice loudness values are later used for plotting loudness graphics.
#	'new_hotfolder_filelist_dict' and 'old_hotfolder_filelist_dict'
# These dictionaries are used to keep track of files that appear to the HotFolder and the time the files were first seen there.
# This time is used to determine when files have expired and can been deleted. (Expiration time (seconds) is stored in variable 'file_expiry_time' and is 8 hours by default).
#	'list_of_growing_files'
# This list is used to keep track of files that are being transferred to the HotFolder but are not yet complete (file size is growing between directory polls).
#	'files_queued_to_loudness_calculation'
# This list holds the names of files in the HotFolder that are no longer growing and can be sent to loudness calculation.
#	 'loudness_calculation_queue'
# This list holds the names of files that are currently being calculated upon.
#	'files_queued_for_deletion'
# This list holds the names of files that are going to be deleted.
#		'completed_files_list'
#		'completed_files_dict'
# The list holds the names of 100 last files that has gone through loudness calculation, and the order processing them was completed. The dictionary holds the time processing each file was completed. The list and dictionary are only used when printing loudness calculation progress information to a web page on disk.
#
#
##############################################################################################
#
#
# Dictionary 'temp_loudness_results_for_automation'
# -------------------------------------------------
#
#	If the variable 'write_loudness_calculation_results_to_a_machine_readable_file' = True, then data needed to write a machine readble results file is gathered to this dictionary.
#
# 
#	The items saved in this dictionary are:
#	---------------------------------------
#	key = the file name of a audiostream extracted from the original file, or in case of a one stream file, just the name of the file.
#
#
#	The items stored for each key are:
#	----------------------------------
#	[original_file_name, [technical information about the mix and loudness results, [list_of_output_filenames_for_the_mix]]]
#
#	- The 'original_file_name' means the name of the original file that this mix was extracted from. This item helps us later to write loudness results for all mixes extracted from a file in a single results file.
#	- 'list_of_output_filenames_for_the_mix' is a list of output files that make up this mix. The list contains one file name in case the output file size wont exceed wav max limit of 4 GB and multiple names if this size is exceeded and the output is split to one file per audio channel.
#
#
#	The list item named above as 'technical information about the mix and loudness results' consists of several values which are:
#	-----------------------------------------------------------------------------------------------------------------------------
#
#	00 = The number of this mix.
#	01 = Total number of supported mixes in the original file.
#	02 = Total number of mixes in the original file.
#	03 = Create Loudness Corrected Files (True / False).
#	04 = Number of files in this mix (This is usually 1, except when a file would exceed wav limit 4 GB and the output is split to separate single channel files).
#
#	05 = Integrated Loudness (If loudness is below measurement threshhold, then this value is 'inf').
#	06 = Loudness Range.
#	07 = Highest Peak (dBFS or dBTP depending what user selected during installation).
#	08 = Number Of Channels in the mix.
#	09 = Sample Rate.
#	10 = Bit Depth.
#	11 = Duration rounded to seconds.
#	12 = Loudness calculation error code.
#	13 = Reason for error (text string).
#	14 = List of output filenames for the mix. The list always contains one filename except when output file size exceeds 4GB and output will be split to one audio file per channel.
#
#
#	The item number 12 above holds an error code that is explained below (name of subroutine that reports this error is in parenthesis):
#	------------------------------------------------------------------------------------------------------------------------------------------------
#	
#	0 = No Errors
#	1 = Loudness is below measurement threshold (-70 LUFS)	 (create_gnuplot_commands)
#	2 = Error in integrated loudness calculation   (create_gnuplot_commands)
#	3 = File transfer failed   (main)
#	4 = Audio duration less than 1 second	(main)
#	5 = Zero channels in audio stream   (get_audio_stream_information_with_ffmpeg)
#	6 = Channel count bigger than 6 is unsupported	 (get_audio_stream_information_with_ffmpeg, main)
#	7 = No Audio Streams Found In File   (main)
#	8 = Sox encountered an error   (create_sox_commands_for_loudness_adjusting_a_file)
#	9 = There are unsupported audio streams in input MXF - file while remix function is on. This may create unwanted results
#	10 = File wrapper format is not supported
#       11 = Audio Compression codec is not supported
#	100 = Unknown Error
#
# Dictionary 'final_loudness_results_for_automation'
# --------------------------------------------------
#
#	If the variable 'write_loudness_calculation_results_to_a_machine_readable_file' = True, then data needed to write a machine readble results file is gathered to this dictionary.
#
#	Items from dictionary 'temp_loudness_results_for_automation' are moved to this dictionary when loudness results of all mixes extracted from a file a ready.
#	This means that this dictionary holds loudness results and techninal info for all mixes extracted from a (single or) multistream file.
#	Data in this dictionary is used when results are written to machine readable results file.
#
#	- The key is the original file name that the mixes were extracted from.
#	- The value for a key is a list of lists, each list holds information for one mix and as the data is copied from dictionary 'temp_loudness_results_for_automation' the items are laid out as explained above.
#
#
#	Example: original file 'inputfile.mxf' contained three mixes. The information stored in the dictionary is:
#
#	key = filename.mxf
#
#	The item stored for the key is a list of lists meaning a list that holds three lists inside it, one list for each mix extracted from the original file.
#
#	Each of these lists is taken from the dictionary 'temp_loudness_results_for_automation' and therefore the order of items in the list is the same as described above.
#
#	The data stored for the key in this example is a list that contains three lists:
#
#	[[technical information about the mix and loudness results, [filename-AudioStream-1-ChannelCount-2.wav]], 
#	[technical information about the mix and loudness results, [filename-AudioStream-2-ChannelCount-6.wav]],
#	[technical information about the mix and loudness results, [filename-AudioStream-3-ChannelCount-2.wav]]]
#
#
#
########################################################################################################################################################
#	
#	
#	The main procedure works like this:
#	------------------------------------
#	- Read 'HotFolder' and get filenames, then check against previous directory read to see if new files have appeared.
#	- If there are new files then start monitoring if their size changes between directory polls. Also record the time the file was first seen in the HotFolder.
#	- Check if files have stayed longer in the HotFolder and Results Folder than the expiry time. Delete all files expired.
#	- When a file stops growing, check if ffmpeg can find any audiostreams in the file. If not create a graphics file telling the user about the error, otherwise record the number of streams found.
#	- Check if file format is natively supported by libebur128 and sox shipped with Ubuntu (wav, flac, ogg).
#	- If format is not natively supported extract audiostreams (max 8) from the file with ffmpeg and move the resulting files to HotFolder and delete the original file.
#	- Check to see if there is already the maximum allowed number of loudness calculations going on. If two free processor cores are available then start calculating the next file.
#	- The loudnes calculation, graphics plotting and creation of loudness corrected wavs is handled by subroutines, their operation is documented in their comments.
#
#
########################################################################################################################################################

try:

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
	adjust_line_printout='	       '
	loudness_calculation_queue={} # See explanation of the purpose for this dictionary in comments above.
	loop_counter=0
	integrated_loudness_calculation_results = {}
	previous_value_of_files_queued_to_loudness_calculation = 0 # This variable is used to track if the number of files in the calculation queue changes. A message is printed when it does.
	previous_value_of_loudness_calculation_queue = 0 # This variable is used to track if the number of files being in the calculation process changes. A message is printed when it does.
	error_messages_to_email_later_list = [] # Error messages are collected to this list for sending them by email.
	unsupported_ignored_files_dict = {} # This dictionary holds the names of files that have no audiostreams we can read with ffmpeg, or has audiostreams, but the duration is less than 1 second. Files in this list will be ignored and not processed. The time the file was first seen in the HotFolder is also recorded with the filename.
	html_progress_report_counter = 0 # This variable is used to count the seconds between writing loudness calculation queue information to a html - page on disk
	loudness_correction_pid = os.getpid() # Get the PID of this program.
	all_ip_addresses_of_the_machine = ['Not known'] # This variable stores in a list all IP-Addresses this machine has. This info is inserted into error emails.
	temp_loudness_results_for_automation = {}
	final_loudness_results_for_automation = {}  # Loudness results and file info is gathered to this dictionary if this option is turned on. This dictionary stores all results under the original source file name, even for separate mixes that were extracted from the original file.


	###############################################################################################################################################################################
	# Read user defined configuration variables from a file															      #
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
			if silent == False:
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
		if 'ffmpeg_output_wrapper_format' in all_settings_dict:
			if all_settings_dict['ffmpeg_output_wrapper_format'] != '': # If installer.py did not define a value for the variable, then don't assing anything to it here. The variable has a default value defined elsewhere in LoudnessCorrection.py, the default gets used if not defined here.
				ffmpeg_output_wrapper_format = all_settings_dict['ffmpeg_output_wrapper_format']
			
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

		if 'freelcs_version' in all_settings_dict:
			freelcs_version = all_settings_dict['freelcs_version']
		
		if 'write_loudness_calculation_results_to_a_machine_readable_file' in all_settings_dict:
			write_loudness_calculation_results_to_a_machine_readable_file = all_settings_dict['write_loudness_calculation_results_to_a_machine_readable_file']
		if 'create_loudness_corrected_files' in all_settings_dict:
			create_loudness_corrected_files = all_settings_dict['create_loudness_corrected_files']
		if 'create_loudness_history_graphics_files' in all_settings_dict:
			create_loudness_history_graphics_files = all_settings_dict['create_loudness_history_graphics_files']
		if 'delete_original_file_immediately' in all_settings_dict:
			delete_original_file_immediately = all_settings_dict['delete_original_file_immediately']
		if 'unit_separator' in all_settings_dict:
			unit_separator = all_settings_dict['unit_separator']
		if 'record_separator' in all_settings_dict:
			record_separator = all_settings_dict['record_separator']

		if 'enable_mxf_audio_remixing' in all_settings_dict:
			enable_mxf_audio_remixing = all_settings_dict['enable_mxf_audio_remixing']
		if 'remix_map_file_extension' in all_settings_dict:
			remix_map_file_extension = all_settings_dict['remix_map_file_extension']
		if 'global_mxf_audio_remix_channel_map' in all_settings_dict:
			global_mxf_audio_remix_channel_map = all_settings_dict['global_mxf_audio_remix_channel_map']
		if 'ffmpeg_free_wrapper_formats' in all_settings_dict:
			ffmpeg_free_wrapper_formats = all_settings_dict['ffmpeg_free_wrapper_formats']
		if 'mxf_formats' in all_settings_dict:
			mxf_formats = all_settings_dict['mxf_formats']
		if 'mpeg_wrapper_formats' in all_settings_dict:
			mpeg_wrapper_formats = all_settings_dict['mpeg_wrapper_formats']
		if 'ffmpeg_allowed_wrapper_formats' in all_settings_dict:
			ffmpeg_allowed_wrapper_formats = all_settings_dict['ffmpeg_allowed_wrapper_formats']
		if 'ffmpeg_free_codec_formats' in all_settings_dict:
			ffmpeg_free_codec_formats = all_settings_dict['ffmpeg_free_codec_formats']
		if 'ffmpeg_allowed_codec_formats' in all_settings_dict:
			ffmpeg_allowed_codec_formats = all_settings_dict['ffmpeg_allowed_codec_formats']
		if 'enable_all_nonfree_ffmpeg_wrapper_formats' in all_settings_dict:
			enable_all_nonfree_ffmpeg_wrapper_formats = all_settings_dict['enable_all_nonfree_ffmpeg_wrapper_formats']
		if 'enable_all_nonfree_ffmpeg_codec_formats' in all_settings_dict:
			enable_all_nonfree_ffmpeg_codec_formats = all_settings_dict['enable_all_nonfree_ffmpeg_codec_formats']

		if 'os_name' in all_settings_dict:
			os_name = all_settings_dict['os_name']
		if 'os_version' in all_settings_dict:
			os_version = all_settings_dict['os_version']

		if debug_all == True:
			write_loudness_calculation_results_to_a_machine_readable_file = True
			write_user_defined_configuration_settings_to_logfile()

	# Test if the user given target path exists.
	if (not os.path.exists(target_path)):
		error_message = '\n!!!!!!! Directory ' * english + '\n!!!!!!! Hakemistoa ' * finnish + str(target_path) + ' does not exist !!!!!!!\n' * english + ' ei ole olemassa !!!!!!!\n' * finnish
		send_error_messages_to_screen_logfile_email(error_message, [])
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

	# Define the name of the error logfile.
	error_logfile_path = directory_for_error_logs + os.sep + 'error_log-' + str(get_realtime(english, finnish)[1]) + '.txt' # Error log filename is 'error_log' + current date + time

	# Test that programs gnuplot, sox, ffmpeg, mediainfo, libebur128, smbstatus and loudness-executable can be found in the path and that they have executable permissions on.
	gnuplot_executable_found = False
	sox_executable_found = False
	ffmpeg_executable_found = False
	avconv_executable_found = False
	mediainfo_executable_found = False
	smbstatus_executable_found = False
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
			
		avconv_true_or_false = os.path.exists(os_path + os.sep + 'avconv') and os.access(os_path + os.sep + 'avconv', os.X_OK)
		if avconv_true_or_false == True:
			avconv_executable_found = True
			
		mediainfo_true_or_false = os.path.exists(os_path + os.sep + 'mediainfo') and os.access(os_path + os.sep + 'mediainfo', os.X_OK)
		if mediainfo_true_or_false == True:
			mediainfo_executable_found = True
			
		smbstatus_true_or_false = os.path.exists(os_path + os.sep + 'smbstatus') and os.access(os_path + os.sep + 'smbstatus', os.X_OK)
		if smbstatus_true_or_false == True:
			smbstatus_executable_found = True
			
		libebur128_loudness_executable_true_or_false = os.path.exists(os_path + os.sep + 'loudness') and os.access(os_path + os.sep + 'loudness', os.X_OK)
		if libebur128_loudness_executable_true_or_false == True:
			libebur128_loudness_executable_found = True
			libebur128_path = os_path + os.sep + 'loudness'
		
	if gnuplot_executable_found == False:
		error_message = '\n!!!!!!! gnuplot - can not be found or it does not have \'executable\' permissions on !!!!!!!' * english + '\n!!!!!!! gnuplot - ohjelmaa ei löydy tai sillä ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!' * finnish
		send_error_messages_to_screen_logfile_email(error_message, [])
		sys.exit(1)
	if sox_executable_found == False:
		error_message = '\n!!!!!!! sox - can not be found or it does not have \'executable\' permissions on !!!!!!!' * english + '\n!!!!!!! sox - ohjelmaa ei löydy tai sillä ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!' * finnish
		send_error_messages_to_screen_logfile_email(error_message, [])
		sys.exit(1)
	if mediainfo_executable_found == False:
		error_message = '\n!!!!!!! mediainfo - can not be found or it does not have \'executable\' permissions on !!!!!!!' * english + '\n!!!!!!! mediainfo - ohjelmaa ei löydy tai sillä ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!' * finnish
		send_error_messages_to_screen_logfile_email(error_message, [])
		sys.exit(1)
		
	# Check if libebur128 loudness-executable can be found.
	if (not os.path.exists(libebur128_path)):
		error_message = '\n!!!!!!! libebur128 loudness-executable can\'t be found in path or directory: ' * english + '\n!!!!!!! libebur128:n loudness-ohjelmaa ei löydy polusta eikä määritellystä hakemistosta: ' * finnish + str(libebur128_path) + ' !!!!!!!\n'
		send_error_messages_to_screen_logfile_email(error_message, [])
		sys.exit(1)
	else:
		# Test that libebur128n loudness-executable has executable permissions on.
		if (not os.access(libebur128_path, os.X_OK)):
			error_message = '\n!!!!!!! libebur128 loudness-executable does not have \'executable\' permissions on !!!!!!!\n' * english + '\n!!!!!!! libebur128:n loudness-ohjelmalla ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!\n' * finnish
			send_error_messages_to_screen_logfile_email(error_message, [])
			sys.exit(1)

	# If both FFmpeg and Avconv are found then decide which one to use.
	# Default is = If both are found then use avconv, not FFmpeg.
	# This is because avconv is available on Ubuntu and Debian repositories, not because avconv is better.
	# In fact it might be the opposite, but the Debian / Ubuntu maintainer has chosen to support only avconv
	# for his egoistic reasons (he is part of the avconv developer group, that forked FFmpeg to start the libav - project).
	ffmpeg_executable_name = ''

	# If user has forced no_ffmpeg on the command line, don't use FFmpeg or avconv.
	if force_no_ffmpeg == True:
		ffmpeg_executable_found = False
		avconv_executable_found = False

	if ffmpeg_executable_found == True:
		ffmpeg_executable_name = 'ffmpeg'

	if avconv_executable_found == True:
		ffmpeg_executable_name = 'avconv'

	# Override some variables, if user gave same debug options on the commandline.
	if force_samplepeak == True:
		peak_measurement_method = '--peak=sample'

	if force_truepeak == True:
		peak_measurement_method = '--peak=true'

	# Define the name of the loudness calculation logfile.
	loudness_calculation_logfile_path = '' 
	if debug_file_processing == True: 
		loudness_calculation_logfile_path = directory_for_error_logs + os.sep + 'loudness_calculation_log-' + str(get_realtime(english, finnish)[1]) + '.txt'

	# The dictionary 'loudness_correction_program_info_and_timestamps' is used to send information to the HeartBeat_Checker - program that is run independently of the LoudnessCorrection - script.
	# Some threads in LoudnessCorrection write periodically a timestamp to this dictionary indicating they are still alive. 
	# The dictionary gets written to disk periodically and the HeartBeat_Checker - program checks that the timestamps in it keeps changing and sends email to the user if they stop.
	# The commandline used to start LoudnessCorrection - script and the PID it is currently running on is also recorded in this dictionary. This infomation may be used
	# in the future to automatically kill and start again LoudnessCorrection if some of it's threads have crashed, but that is not implemented yet.
	#
	# Keys 'main_thread' and 'write_html_progress_report' have a list of two values. The first one (True / False) tells if user enabled the feature or not. For example if user does not wan't
	# LoudnessCorrection to write a html - page to disk, he set the variable 'write_html_progress_report' to False and this value is also sent to HeartBeat_Checker so that it knows the
	# Html - thread won't be updating it's timestamp.

	loudness_correction_program_info_and_timestamps = {'loudnesscorrection_program_info' : [sys.argv, loudness_correction_pid, all_ip_addresses_of_the_machine, freelcs_version, loudnesscorrection_version], 'main_thread' : [True, 0], 'write_html_progress_report' : [write_html_progress_report, 0]}

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

	# Start a debugging process that saves the contents of variables, main lists and dictionaries once a minute to a file.
	debug_lists_process = threading.Thread(target=debug_lists_and_dictionaries_thread, args=()) # Create a process instance.
	thread_object = debug_lists_process.start() # Start the process in it'own thread.

	# Start the silent debugger process that gathers file processing debug data for processed files.
	# This gathered info can be written to disk by sending LoudnessCorrection a signal.
	debug_file_processing_process = threading.Thread(target=debug_manage_file_processing_information_thread, args=()) # Create a process instance.
	thread_object = debug_file_processing_process.start() # Start the process in it'own thread.

	# Define a handler routine for signals recieved outside of program.
	signal.signal(signal.SIGUSR1, signal_handler_routine)
	signal.signal(signal.SIGUSR2, signal_handler_routine)

	# Print version information to screen
	if silent == False:
		print()
		version_string_to_print = 'LoudnessCorrection version ' + loudnesscorrection_version
		print(version_string_to_print)
		print('-' * (len(version_string_to_print) + 1))
		print()

	#############################
	# The main loop starts here #
	#############################

	while True:
		
		loudness_correction_program_info_and_timestamps['main_thread'] = [True, int(time.time())] # Update the heartbeat timestamp for the main thread. This is used to keep track if the main thread has crashed.
		loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'] = [sys.argv, loudness_correction_pid, all_ip_addresses_of_the_machine, freelcs_version, loudnesscorrection_version]

		# Get IP-Addresses of the machine, if update time has passed (default 5 minutes).
		ip_address_refresh_counter = ip_address_refresh_counter + delay_between_directory_reads

		if ip_address_refresh_counter >= ip_address_refresh_interval:
			all_ip_addresses_of_the_machine = get_ip_addresses_of_the_host_machine(all_ip_addresses_of_the_machine)
	

		try:
			# Get directory listing for HotFolder. The 'break' statement stops the for - statement from recursing into subdirectories.
			for path, list_of_directories, list_of_files in os.walk(hotfolder_path):
				break
		except KeyboardInterrupt:
			if silent == False:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error reading HotFolder directory listing ' * english + 'Lähdehakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
		except OSError as reason_for_error:
			error_message = 'Error reading HotFolder directory listing ' * english + 'Lähdehakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message, [])
			
		# The files in 'unsupported_ignored_files_dict' are files that ffmpeg was not able to find any audiostreams from, or streams were found but the duration is less than 1 second or file transfer ended prematurely.
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
		filenames_to_remove = []

		for filename in list_of_growing_files:
			if not filename in list_of_files:
				filenames_to_remove.append(filename)
		for filename in filenames_to_remove:
			list_of_growing_files.remove(filename) # If file that previously was in HotFolder has vanished, remove its name from the list_of_growing_files.

		# If user has deleted a file that did already make it to the 'debug_temporary_dict_for_all_file_processing_information' remove it from list.
		filenames_to_remove = []

		for filename in debug_temporary_dict_for_all_file_processing_information:
			if not filename in list_of_files:
				filenames_to_remove.append(filename)
		for filename in filenames_to_remove:
			del debug_temporary_dict_for_all_file_processing_information[filename] # If file that previously was in HotFolder has vanished, remove its name from the dictionary used to collect debug data.

		filenames_to_remove = []

		# Process filenames found in the directory
		try:
			for filename in list_of_files:

				if (filename.startswith('.')) and (not filename.startswith('.nfs')): # If filename starts with an '.' queue the file for deletion and continue to process next filename. Don't try to delete files that start with .nfs since these might be false files that actually are caused by a file deleted on a nfs mount. Ilmeisesti meidän BackupSysteemi tekee tiedostojärjestelmän varmuuskopiot nfs - mountin yli ja siksi näitä tiedostoja välillä ilmestyy HotFolderiin. Lisätietoa: https://stackoverflow.com/questions/8192605/how-delete-nfs-in-linux
					files_queued_for_deletion.append(filename)
					continue

				# Don't try to find audio in mxf - remix map files that are text files.
				if os.path.splitext(filename)[1] == remix_map_file_extension:
					if filename not in unsupported_ignored_files_dict:
						unsupported_ignored_files_dict[filename] = int(time.time())
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
				# Add information about a file to dictionary.
				# This statement also guarantees that files put in deletion queue by subprocess 'decompress_audio_streams_with_ffmpeg' running in separate thread, are not processed here further. That would sometimes cause files being used by one thread to be deleted by the other.
				if (filename not in files_queued_for_deletion) and (filename not in unsupported_ignored_files_dict):

					# Save information about new files into a dictionary: filename, file size, time file was first seen in HotFolder.
					if not filename in old_hotfolder_filelist_dict:
						# The file has just appeared to the HotFolder and it has not been analyzed yet.
						# However some dummy data for the file needs to be filled, so we create that data here.
						# This dummy data is replaced with real data when the file stops growing and gets analyzed.
						dummy_information = [False, False, 0, [], '3', 0, [], [], False, [], [], 0] # This dummy information will be replaced by info from FFmpeg later.
						file_information_to_save.append(dummy_information)

						# Append time the file size or timestamp was last updated.
						# As this is the first time we have seen the file, we don't have this information yet, we need to use some sane dummy value.
						# So just use the time the file was first seen in HotFolder as the last update time.
						# This information is already in 'file_information_to_save' as it's item number 1, so just copy it from there.
						file_information_to_save.append(file_information_to_save[1])

					# Data in 'file_information_to_save' is at this point (with item numbers):
					#
					# 0 = file size
					# 1 = time file was first seen in HotFolder
					# 2 = file modification time
					# 3 = [False, False, 0, [], '3', 0, [], [], False, [], [], 0] # This is dummy information that will later be replaced by data from FFmpeg. See comment below for item identification.
					# 4 = Time the file size or timestamp was last updated. At this point this is the same as the time the file was first seen in HotFolder.
					#
					# The item 3 above is a list of dummy information that later will be replaced by real file information reported by FFmpeg.
					# The data that FFmpeg fills later in this list is (with item numbers):
					# ---------------------------------------------------------------------------------------------------------------
					#
					# 00 = natively_supported_file_format
					# 01 = ffmpeg_supported_fileformat
					# 02 = number_of_ffmpeg_supported_audiostreams
					# 03 = details_of_ffmpeg_supported_audiostreams
					# 04 = time_slice_duration_string
					# 05 = audio_duration_rounded_to_seconds
					# 06 = ffmpeg_commandline
					# 07 = target_filenames
					# 08 = mxf_audio_remixing
					# 09 = filenames_and_channel_counts_for_mxf_audio_remixing
					# 10 = audio_remix_channel_map
					# 11 = number_of_unsupported_streams_in_file
					#
					new_hotfolder_filelist_dict[filename] = file_information_to_save


		except KeyboardInterrupt:
			if silent == False:
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
			if silent == False:
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
				realtime = get_realtime(english, finnish)[1]

				if os.path.exists(hotfolder_path + os.sep + filename):
					os.remove(hotfolder_path + os.sep + filename)
					files_queued_for_deletion.remove(filename)

					if silent == False:
						print('\r' + adjust_line_printout, ' Deleted file' * english + ' Poistin tiedoston' * finnish, '"' + str(filename) + '"', realtime)
		except KeyboardInterrupt:
			if silent == False:
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
		#																						     #
		# One thing that is not obvious from reading the code below is why new files gets processed and old files will not be processed again and again.				     #
		# Files only get into the processing queue through the 'list_of_growing_files'.													     #
		#																						     #
		# Only if a file was not there during the previous HotFolder poll (filename is not in 'old_hotfolder_filelist_dict'), will the file be added to the 'list_of_growing_files'.	     #
		# Only if a file was in the HotFolder during the last and the previous HotFolder poll (filename is in 'old_hotfolder_filelist_dict' and 'new_hotfolder_filelist_dict'),		     #
		# will it be moved from 'list_of_growing_files' to the processing queue.																	  #
		#																						     #
		######################################################################################################################################################################################
		
		for filename in new_hotfolder_filelist_dict:
			
			if filename in old_hotfolder_filelist_dict:
				new_filesize = new_hotfolder_filelist_dict[filename][0] # Get file size from the newest directory poll.
				new_modification_time = new_hotfolder_filelist_dict[filename][2] # Get latest file modification time.
				file_last_update_time = old_hotfolder_filelist_dict[filename][4] # Get the time the file size or time stamp was last changed.
				old_filesize = old_hotfolder_filelist_dict[filename][0] # Get file size from the previous directory poll.
				time_file_was_first_seen = old_hotfolder_filelist_dict[filename][1] # Get the time the file was first seen from the previous directory poll dictionary.
				old_modification_time = old_hotfolder_filelist_dict[filename][2] # Get old file modification time.
				file_format_support_information = old_hotfolder_filelist_dict[filename][3] # Get other file information that was gathered during the last poll.

				# If filesize is still zero and it has not changed in 1,5 hours (5400 seconds), stop waiting and remove filename from list_of_growing_files.
				if (filename in list_of_growing_files) and (new_filesize == 0) and (int(time.time()) >= (time_file_was_first_seen + 5400)):
					# When file is removed from 'list_of_growing_files' it can not get back to processing any more.
					# This is because the file has been sitting on the disk for some time, so it's name is in both 'old_hotfolder_filelist_dict' and 'new_hotfolder_filelist_dict'
					# and the only way to get into processing is if it is only in 'new_hotfolder_filelist_dict' meaning it just appeared on the disk.
					# Files removed from 'list_of_growing_files' are not touched anymore and get deleted when the expiry time comes.
					list_of_growing_files.remove(filename)

				if (filename in list_of_growing_files) and (new_filesize > 0): # If file is in the list of growing files, check if growing has stopped. If HotFolder is on a native windows network share and multiple files are transferred to the HotFolder at the same time, the files get a initial file size of zero, until the file actually gets transferred. Checking for zero file size prevents trying to process the file prematurely.

					if (new_filesize != old_filesize) or (new_modification_time != old_modification_time): # If file size or modification time has changed print message to user about waiting for file transfer to finish.
						# Store the last time the file size or timestamp were updated.
						file_last_update_time = int(time.time()) 

						if silent == False:
							print('\r' + adjust_line_printout, ' Waiting for file transfer to end' * english + ' Odotan tiedostosiirron valmistumista' * finnish, end='')

					else:
						#######################################################################################################
						# Filesize has not changed since last poll, the file is ready to be inspected.			      #
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
						
						# Check if samba has a lock on the file, if it has then the file transfer is not ready yet.
						if smbstatus_executable_found == True:
							file_is_locked_by_samba = check_samba_file_locks(filename)

							if file_is_locked_by_samba == True:
								we_have_true_read_access_to_the_file = False
								
								# If file size and timestamp have not been updated in 5 minutes and samba still has a lock on the file, file transfer has failed. Inform the user about the error.
								if (int(time.time()) >= file_last_update_time + 300) and (filename not in unsupported_ignored_files_dict):

									error_message = 'File transfer failed, please send the file again under a new file name' * english + 'Tiedoston siirto epäonnistui, lähetä tiedosto uudestaan toisella tiedostonimellä' * finnish
									
									transfer_error_message_destinations = copy.deepcopy(where_to_send_error_messages)
									
									# This error is not very important, don't send it to admin by email.
									if 'email' in transfer_error_message_destinations:
										transfer_error_message_destinations.remove('email')

									send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, transfer_error_message_destinations)
									
									create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish)
									unsupported_ignored_files_dict[filename] = int(time.time())

									# Add info for all mixes found in the file to dictionary that is used to write the machine readable results file.
									if write_loudness_calculation_results_to_a_machine_readable_file == True:

										error_code = 3

										# Write results to the machine readable results file.
										write_loudness_results_and_file_info_to_a_machine_readable_file(filename, [[0, 0, 0, create_loudness_corrected_files, 0, 0, 0, 0, 0, 0, 0, 0, error_code, error_message, []]])

						if we_have_true_read_access_to_the_file == True:

							# Test if FFmpeg is installed.
							if (ffmpeg_executable_found == True) or (avconv_executable_found == True):
								
								# Call a subroutine to inspect file with FFmpeg to get audio stream information.
								ffmpeg_parsed_audio_stream_information, ffmpeg_error_message, send_ffmpeg_error_message_by_email = get_audio_stream_information_with_ffmpeg_and_create_extraction_parameters(filename, hotfolder_path, directory_for_temporary_files, ffmpeg_output_wrapper_format, english, finnish)
								# Assign audio stream information to variables.
								natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames, mxf_audio_remixing, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, number_of_unsupported_streams_in_file = ffmpeg_parsed_audio_stream_information
							else:
								# FFmpeg is not installed, test input file with mediainfo
								audiostream_count, channel_count, bit_depth, sample_format, audio_duration_rounded_to_seconds, natively_supported_file_format, mediainfo_error_message = get_audiofile_info_with_mediainfo(directory_for_temporary_files, filename, hotfolder_path, english, finnish, save_debug_information = True)
							
								ffmpeg_error_message = mediainfo_error_message

								if natively_supported_file_format == True: 
									ffmpeg_supported_fileformat = True
									number_of_ffmpeg_supported_audiostreams = 1
									ffmpeg_error_message = ''
									temp_loudness_results_for_automation[filename] = [filename, [1, 1, number_of_ffmpeg_supported_audiostreams, create_loudness_corrected_files, 0, 0, 0, 0, 0, 0, 0, 0, 0, ' ', []]]
								else:
									ffmpeg_supported_fileformat = False
									number_of_ffmpeg_supported_audiostreams = 0
									
								ffmpeg_commandline = []
								target_filenames = []
								details_of_ffmpeg_supported_audiostreams = []
								send_ffmpeg_error_message_by_email = False
								mxf_audio_remixing = False
								filenames_and_channel_counts_for_mxf_audio_remixing = []
								audio_remix_channel_map = []
								number_of_unsupported_streams_in_file = 0 # This value is only used for printing a warning is it is >0 and mxf - remixing is on. Since FFmpeg is not installed and mxf - processing is not possible, this value is used for nothing.
								
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

									# Add info for all mixes found in the file to dictionary that is used to write the machine readable results file.
									if write_loudness_calculation_results_to_a_machine_readable_file == True:

										error_code = 7

										# Write results to the machine readable results file.
										write_loudness_results_and_file_info_to_a_machine_readable_file(filename, [[0, 0, 0, create_loudness_corrected_files, 0, 0, 0, 0, 0, 0, 0, 0, error_code, error_message, []]])

										# Delete information about the file we might have stored earlier.
										if filename in final_loudness_results_for_automation:
											del final_loudness_results_for_automation[filename]
										if filename in temp_loudness_results_for_automation:
											del temp_loudness_results_for_automation[filename]

								else:
									
									# FFmpeg error message was found tell the user about it.
									error_message = ffmpeg_error_message.replace('\\n', ' ').replace('\n',' ').replace('\t',' ').strip()
									
									error_message_destinations = copy.deepcopy(where_to_send_error_messages)
									if send_ffmpeg_error_message_by_email == False:
										if 'email' in error_message_destinations:
											error_message_destinations.remove('email')
									send_error_messages_to_screen_logfile_email(error_message + ': ' + filename, error_message_destinations)
									
									# Add info for all mixes found in the file to dictionary that is used to write the machine readable results file.
									if write_loudness_calculation_results_to_a_machine_readable_file == True:

										error_code = 100

										if 'only channel counts from 1 to 6 are supported' in error_message:
											error_code = 6
										if 'vain kanavamäärät välillä 1 ja 6 ovat tuettuja' in error_message:
											error_code = 6

										if 'File wrapper format' in error_message:
											error_code = 10
										if 'Tiedoston paketointiformaatti' in error_message:
											error_code = 10

										if 'Audio compression codec' in error_message:
											error_code = 11
										if 'Audion kompressioformaatti' in error_message:
											error_code = 11

										# Write results to the machine readable results file.
										write_loudness_results_and_file_info_to_a_machine_readable_file(filename, [[0, 0, 0, create_loudness_corrected_files, 0, 0, 0, 0, 0, 0, 0, 0, error_code, error_message, []]])

										# Delete information about the file we might have stored earlier.
										if filename in final_loudness_results_for_automation:
											del final_loudness_results_for_automation[filename]
										if filename in temp_loudness_results_for_automation:
											del temp_loudness_results_for_automation[filename]

								create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish)
								unsupported_ignored_files_dict[filename] = int(time.time())
								
								# Remove file processing information from temporary debug dictionary, as file is not supported, it will not be processed and this info is no longer needed.
								if debug_file_processing == True:
									temporary_gathering_list = debug_temporary_dict_for_all_file_processing_information.pop(filename)
									debug_complete_final_information_for_all_file_processing_dict[filename] = temporary_gathering_list

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
								
								# Remove file processing information from temporary debug dictionary, as file is not supported, it will not be processed and this info is no longer needed.
								if debug_file_processing == True:
									temporary_gathering_list = debug_temporary_dict_for_all_file_processing_information.pop(filename)
									debug_complete_final_information_for_all_file_processing_dict[filename] = temporary_gathering_list

								# Add info for all mixes found in the file to dictionary that is used to write the machine readable results file.
								if write_loudness_calculation_results_to_a_machine_readable_file == True:

									error_code = 4

									# Write results to the machine readable results file.
									write_loudness_results_and_file_info_to_a_machine_readable_file(filename, [[0, 0, 0, create_loudness_corrected_files, 0, 0, 0, 0, 0, 0, 0, 0, error_code, error_message, []]])

									# Delete information about the file we might have stored earlier.
									if filename in final_loudness_results_for_automation:
										del final_loudness_results_for_automation[filename]
									if filename in temp_loudness_results_for_automation:
										del temp_loudness_results_for_automation[filename]

							# The time slice value used in loudness calculation is normally 3 seconds. When we calculate short files <12 seconds, it's more convenient to use a smaller value of 0.5 seconds to get more detailed loudness graphics.
							if  (audio_duration_rounded_to_seconds > 0) and (audio_duration_rounded_to_seconds < 12):
								time_slice_duration_string = '0.5'
							if  audio_duration_rounded_to_seconds >= 12:
								time_slice_duration_string = '3'

							# If ffmpeg found audiostreams in the file, queue it for loudness calculation and print message to user.
							if filename not in unsupported_ignored_files_dict:
								file_format_support_information = [natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames, mxf_audio_remixing, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, number_of_unsupported_streams_in_file]
								files_queued_to_loudness_calculation.append(filename)
								if silent == False:
									print('\r' + adjust_line_printout, '"' + str(filename) + '"', 'is in the job queue as number' * english + 'on laskentajonossa numerolla' * finnish, len(files_queued_to_loudness_calculation))
							list_of_growing_files.remove(filename) # File has been queued for loudness calculation, or it is unsupported, in both cases we need to remove it from the list of growing files.

				# Save information about the file in a dictionary:
				# filename, file size, time file was first seen in HotFolder, latest modification time, file format wav / flac / ogg, if format is supported by ffmpeg (True/False), number of audio streams found, information ffmpeg printed about the audio streams, the last time the file size changed.
				new_hotfolder_filelist_dict[filename] = [new_filesize, time_file_was_first_seen, new_modification_time, file_format_support_information, file_last_update_time]
			else:
				# If we get here the file was not there in the directory poll before this one. We need to wait for another poll to see if the file is still growing. Add file name to the list of growing files.
				if (filename not in files_queued_to_loudness_calculation) and (filename not in loudness_calculation_queue): # This line prevents LoudnessCorrection.py from crashing if the user repeatedly copies and deletes the same file from the HotFolder. Filenames already in the processing queue can not enter again.
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

				# If user has deleted a file from HotFolder that was already queued for loudness calculation, remove it's name from the queue.
				copy_of_files_queued_to_loudness_calculation = copy.deepcopy(files_queued_to_loudness_calculation)

				for removed_file in copy_of_files_queued_to_loudness_calculation:
					if removed_file not in old_hotfolder_filelist_dict:
						files_queued_to_loudness_calculation.remove(removed_file)
				
				if len(files_queued_to_loudness_calculation) > 0: # Check if there are files queued for processing waiting in the queue.
					filename = files_queued_to_loudness_calculation[0] # Get the first filename from the queue and put it in a variable.
					file_format_support_information = old_hotfolder_filelist_dict[filename][3] # The information about the file format is stored in a list in the dictionary, get it and store in a list.
					natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string, audio_duration_rounded_to_seconds, ffmpeg_commandline, target_filenames, mxf_audio_remixing, filenames_and_channel_counts_for_mxf_audio_remixing, audio_remix_channel_map, number_of_unsupported_streams_in_file = file_format_support_information # Save file format information to separate variables.

					# Calculate the number of time slices we expect to get from loudness calculation.
					expected_number_of_time_slices = int(audio_duration_rounded_to_seconds / float(time_slice_duration_string)) 

					# Get the size of file, we check this once again after loudness calculation to make sure the calculation did not start too early.
					expected_file_size = old_hotfolder_filelist_dict[filename][0]
					
					realtime = get_realtime(english, finnish)[1].replace('_', ' ')
					
					# If audio fileformat is natively supported by libebur128 and sox and has only one audio stream, we don't need to do extraction and flac conversion with ffmpeg, just start two loudness calculation processes for the file.
					if (number_of_ffmpeg_supported_audiostreams == 1) and (natively_supported_file_format == True):
						# Start simultaneously two threads to calculate file loudness. The first one calculates loudness by dividing the file in time slices and calculating the loudness of each slice individually. The second process calculates integrated loudness and loudness range of the file as a whole.
						# Both processes can be done in almost the same time as one, since the first process reads the file in to os file cache, so the second process doesn't need to read the disk at all. Reading from cache is much much faster than reading from disk.
						if silent == False:
							print ('\r' + 'File' * english + 'Tiedoston' * finnish, '"' + filename + '"' + ' processing started ' * english + ' käsittely	alkoi  ' * finnish, realtime)
						
						# Create commands for both loudness calculation processes.
						libebur128_commands_for_time_slice_calculation=[libebur128_path, 'dump', '-s', time_slice_duration_string] # Put libebur128 commands in a list.
						libebur128_commands_for_integrated_loudness_calculation=[libebur128_path, 'scan', '-l', peak_measurement_method] # Put libebur128 commands in a list.
						
						# Create events for both processes. When the process is ready it sets event = set, so that we know in the main thread that we can start more processes.
						event_for_timeslice_loudness_calculation = threading.Event() # Create a unique event for the process. This event is used to signal other threads that this process has finished.
						event_for_integrated_loudness_calculation = threading.Event() # Create a unique event for the process. This event is used to signal other threads that this process has finished.
						
						# Add file name and both the calculation process events to the dictionary of files that are currently being calculated upon.
						loudness_calculation_queue[filename] = [event_for_timeslice_loudness_calculation, event_for_integrated_loudness_calculation]
						# Create threads for both processes, the threads are not started yet.
						process_1 = threading.Thread(target=calculate_loudness_timeslices, args=(filename, hotfolder_path, libebur128_commands_for_time_slice_calculation, directory_for_temporary_files, directory_for_results, english, finnish, expected_number_of_time_slices, expected_file_size, event_for_timeslice_loudness_calculation, event_for_integrated_loudness_calculation)) # Create a process instance.
						process_2 = threading.Thread(target=calculate_integrated_loudness, args=(event_for_integrated_loudness_calculation, filename, hotfolder_path, libebur128_commands_for_integrated_loudness_calculation, english, finnish)) # Create a process instance.
						
						# Start both calculation threads.
						thread_object = process_2.start() # Start the calculation process in it's own thread.
						thread_object = process_1.start() # Start the calculation process in it's own thread.
						
					else:
						
						# Fileformat is not natively supported by libebur128 and sox, or it has more than one audio streams.
						# Start a process that extracts all audio streams from the file and converts them to wav or flac and moves resulting files back to the HotFolder for loudness calculation.
						if ffmpeg_supported_fileformat == True:

							if silent == False:
								print ('\r' + 'File' * english + 'Tiedoston' * finnish, '"' + filename + '"' + ' conversion started ' * english + '  muunnos	alkoi  ' * finnish, realtime)
								print('\r' + adjust_line_printout, ' Extracting' * english + ' Puran' * finnish, str(number_of_ffmpeg_supported_audiostreams), 'audio streams from file' * english + 'miksausta tiedostosta' * finnish, filename)
								
								for counter in range(0, number_of_ffmpeg_supported_audiostreams): # Print information about all the audio streams we are going to extract.
									print('\r' + adjust_line_printout, ' ' + details_of_ffmpeg_supported_audiostreams[counter][0])
							
							event_1_for_ffmpeg_audiostream_conversion = threading.Event() # Create events for the process. The events are being used to signal other threads that this process has finished. 
							event_2_for_ffmpeg_audiostream_conversion = event_1_for_ffmpeg_audiostream_conversion 
							process_3 = threading.Thread(target = decompress_audio_streams_with_ffmpeg, args=(event_1_for_ffmpeg_audiostream_conversion, event_2_for_ffmpeg_audiostream_conversion, filename, file_format_support_information, hotfolder_path, directory_for_temporary_files, english, finnish)) # Create a process instance.
							thread_object = process_3.start() # Start the process in it'own thread.
							loudness_calculation_queue[filename] = [event_1_for_ffmpeg_audiostream_conversion, event_2_for_ffmpeg_audiostream_conversion] # Add file name and both process events to the dictionary of files that are currently being calculated upon.

					# Remove the filename from the queue.
					files_queued_to_loudness_calculation.pop(0) 

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
				
				# If user wants us to write loudness results to a machine readable file,
				# Then find the name of the original file that this mix was extracted from and store results under the original file name.
				if write_loudness_calculation_results_to_a_machine_readable_file == True:

					if filename in temp_loudness_results_for_automation:

						original_file_name = temp_loudness_results_for_automation[filename][0]
						
						total_number_of_mixes_in_original_file = temp_loudness_results_for_automation[filename][1][2]

						mix_result_lists = []

						# Get results from the temp dictionary and move them to the final dictionary.

						if original_file_name in final_loudness_results_for_automation:
							mix_result_lists = final_loudness_results_for_automation[original_file_name]

						loudness_results_for_one_mix = temp_loudness_results_for_automation[filename][1]

						if mix_result_lists == []:

							mix_result_lists = [loudness_results_for_one_mix]
						else:
							mix_result_lists.append(loudness_results_for_one_mix)

						final_loudness_results_for_automation[original_file_name] = mix_result_lists

						number_of_mixes_ready = len(final_loudness_results_for_automation[original_file_name])

						# Now that results have been moved to the final dictionary, the values stored in the temp dictionary can be removed.
						del temp_loudness_results_for_automation[filename]

						# If all results for mixes extracted from a file are ready, then print the results to machine readable results file.
						if number_of_mixes_ready == total_number_of_mixes_in_original_file:

							# Call the subroutine that writes results to the machine readable file.
							write_loudness_results_and_file_info_to_a_machine_readable_file(original_file_name, final_loudness_results_for_automation[original_file_name])

							# The results have been written to a file now and can be deleted from the dictionary.
							del final_loudness_results_for_automation[original_file_name]


				# If filename exists in 'debug_temporary_dict_for_all_file_processing_information' then move file processing debug info to the final gathering dictionary.
				# If filename is missing from 'debug_temporary_dict_for_all_file_processing_information' then user has deleted the file before processing finished. In this case delete all file processing debug information for the file.

				if debug_file_processing == True:

					event_for_process_1, event_for_process_2 = loudness_calculation_queue[filename]
					temporary_gathering_list = []

					if filename in debug_temporary_dict_for_all_file_processing_information:

						# If both events are equal (pointing to the same event object) then audiostreams were extracted with ffmpeg from the file. 
						# When loudness processing is ready then events are not equal (events point to different event objects).

						if event_for_process_1 != event_for_process_2:
							# Loudness processing of the file is ready, move debugging information to the main debugging dictionary.
							# We get here only if both integrated and time slice loudness calculation are ready.
							temporary_gathering_list = debug_temporary_dict_for_timeslice_calculation_information.pop(filename)
							temporary_gathering_list.extend(debug_temporary_dict_for_integrated_loudness_calculation_information.pop(filename))
							temporary_gathering_list.extend(debug_temporary_dict_for_all_file_processing_information.pop(filename))
							debug_complete_final_information_for_all_file_processing_dict[filename] = temporary_gathering_list
						else:
							# We get here only when the process that has finished is function: decompress_audio_streams_with_ffmpeg. 
							# Move debug processing info from temp dictionary to the main debug dictionary.
							# The decompressed file will enter processing queue, but the decompressed file has different name than the compressed,
							# So we have to remove the debug info about compressed version from the dictionary, as it is no longer used for anything.

							temporary_gathering_list = debug_temporary_dict_for_all_file_processing_information.pop(filename)
							debug_complete_final_information_for_all_file_processing_dict[filename] = temporary_gathering_list
					else:
						# User has deleted the file before processing was ready, delete all file processing debug information.

						if filename in debug_temporary_dict_for_timeslice_calculation_information:
							del debug_temporary_dict_for_timeslice_calculation_information[filename]
						if filename in debug_temporary_dict_for_integrated_loudness_calculation_information:
							del debug_temporary_dict_for_integrated_loudness_calculation_information[filename]
			

				realtime = get_realtime(english, finnish)[1].replace('_', ' ')
				del loudness_calculation_queue[filename] # Remove file name from the list of files currently being calculated upon.

				# Add filename at the beginning of the list of completed files, but if the user has dropped the same file in HotFolder before, then first remove the name from list. This moves the name to the top of the completed files list.
				if filename in completed_files_list:
					completed_files_list.remove(filename)
				completed_files_list.insert(0, filename) # This list stores only the order in which the files were completed.
				completed_files_dict[filename] = realtime # This dictionary stores the time processing each file was completed. If user drops the same file in HotFolder again, tha latest one will replace the previous one in the dictionry and that is ok.
				
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

		# If user gave the option '-force-quit-when-idle' on the commandline, then we are part of a multi cycle regession test and need to exit when test files have been processed so that the next test can run.
		if force_quit_when_idle == True:

			if len(loudness_calculation_queue) == 0:

				quit_counter = quit_counter + delay_between_directory_reads

			else:
				quit_counter = 0

			if quit_counter >= quit_when_idle_seconds:
				quit_all_threads_now = True
				sys.exit(0)

except Exception:
	exc_type, exc_value, exc_traceback = sys.exc_info()
	error_message_as_a_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
	subroutine_name = 'Main'
	catch_python_interpreter_errors(error_message_as_a_list, subroutine_name)

