#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Mikael Hartzell 2012 and contributors:
# Gnuplot commands Timo Kaleva.
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

version = '154'

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
	if not (argument.lower() == '-configfile') and not (os.path.exists(configfile_path)) and not (os.access(configfile_path, os.R_OK)):
		print('\n!!!!!!! Target configfile does not exist or exists but is not readable !!!!!!!' * english + '\n!!!!!!! Asetustiedostoa ei ole olemassa tai siihen ei ole lukuoikeuksia !!!!!!!' * finnish)
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
ffmpeg_output_format = 'flac' # Possible values are 'flac' and 'wav'. This only affects formats that are first decodec with ffmpeg (all others but wav, flac, ogg). The output file is moved to HotFolder for loudness calculation. Flac has the advantage that file sizes can be huge and as the format is (losslessly) compressed it saves disk space and disk bandwidth. Wav has a 4 GB limitation in filesize and 5.1 audio in wav is not supported natively by libebur128. Note that the final loudness adjusted file will always be wav. This option only affects the intermediate file format that is produced when uncompressing files with ffmpeg. You can safely leave it to 'flac'.
if not ffmpeg_output_format == 'flac':
	ffmpeg_output_format = 'wav'

silent = False # Use True if you don't want this programs to print anything on screen (useful if you want to start this program from Linux init scripts).

# Write calculation queue progress report to a html-page on disk.
write_html_progress_report = True # Controls if the program writes loudness calculation queue information to a web page on disk.
html_progress_report_write_interval = 5 # How many seconds between writing web page to disk.
web_page_name = '00-Calculation_Queue_Information.html' * english + '00-Laskentajonon_Tiedot.html' * finnish # Define the name of the web-page we write to disk.
web_page_path = hotfolder_path + os.sep + '00-Calculation_Queue_Information' * english + '00-Laskentajonon_Tiedot' * finnish # Where to write the web-page.

# Error Log printing options.
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
peak_measuring_method = '--peak=sample'

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

	if os.path.exists(file_to_process): # Check if the audio file still exists, user may have deleted it. If True start loudness calculation.
		# Calculate integrated loudness and loudness range using libebur128 and parse the results from the text output of the program.
		libebur128_commands_for_integrated_loudness_calculation.append(file_to_process) # Append the name of the file we are going to process at the end of libebur128 commands.
		integrated_loudness_calculation_stdout, integrated_loudness_calculation_stderr = subprocess.Popen(libebur128_commands_for_integrated_loudness_calculation, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate() # Start libebur128.
		integrated_loudness_calculation_stdout_string = str(integrated_loudness_calculation_stdout.decode('UTF-8')) # Convert libebur128 output from binary to UTF-8 text.
		integrated_loudness_calculation_stderr_string = str(integrated_loudness_calculation_stderr.decode('UTF-8')) # Convert libebur128 possible error output from binary to UTF-8 text.
		
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
				integrated_loudness_calculation_error_message = 'libebur128 did not tell the cause of the error'
			
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
				integrated_loudness_calculation_error_message = 'Measured loudness is too low (below -70 LUFS).'
		integrated_loudness_calculation_results_list = [integrated_loudness, difference_from_target_loudness, loudness_range, integrated_loudness_calculation_error, integrated_loudness_calculation_error_message, highest_peak_db] # Assign result variables to the list that is going to be read in the other loudness calculation process.
		integrated_loudness_calculation_results[filename] = integrated_loudness_calculation_results_list # Put loudness calculation results in a dictionary along with the filename.		
	else:
		# If we get here the file we were supposed to process vanished from disk after the main program started this thread. Print a message to the user.
		error_message ='ERROR !!!!!!! FILE' * english + 'VIRHE !!!!!!! Tiedosto' * finnish + ' ' + filename + ' ' + 'dissapeared from disk before processing started.' * english + 'hävisi kovalevyltä ennen käsittelyn alkua.' * finnish
		send_error_messages_to_screen_logfile_email(error_message)

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
		timeslice_loudness_calculation_stdout, timeslice_loudness_calculation_stderr = subprocess.Popen(libebur128_commands_for_time_slice_calculation, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate() # Start libebur128.
		timeslice_loudness_calculation_result_list = str(timeslice_loudness_calculation_stdout.decode('UTF-8')).split('\n') # Convert libebur128 output from binary to UTF-8 text, split values in the text by line feeds and insert these individual values in to a list.
		timeslice_loudness_calculation_stderr_string = str(timeslice_loudness_calculation_stderr.decode('UTF-8')) # Convert libebur128 possible error output from binary to UTF-8 text.
		
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
		send_error_messages_to_screen_logfile_email(error_message)

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

	# Get loudness calculation results from the integrated loudness calculation process. Results are in list format in dictionary 'integrated_loudness_calculation_results', assing results to variables.
	integrated_loudness_calculation_results_list = integrated_loudness_calculation_results.pop(filename)# Get loudness results for the file and remove this information from dictionary.
	integrated_loudness = integrated_loudness_calculation_results_list[0]
	difference_from_target_loudness = integrated_loudness_calculation_results_list[1]
	loudness_range = integrated_loudness_calculation_results_list[2]
	integrated_loudness_calculation_error = integrated_loudness_calculation_results_list[3]
	integrated_loudness_calculation_error_message = integrated_loudness_calculation_results_list[4]
	highest_peak_db = integrated_loudness_calculation_results_list[5]
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
	
	# Generate gnuplot commands needed for plotting the graphicsfile and store them in a list.
	if (integrated_loudness_calculation_error == True) or (timeslice_calculation_error == True):
		# Loudness calculation encountered an error, generate gnuplot commands for plotting default graphics with the error message.
		error_message_to_print_with_gnuplot = ''
		if integrated_loudness_calculation_error == True:
			error_message = 'ERROR !!! in libebur128 integrated loudness calculation: ' * english + 'VIRHE !!! libebur128:n lra laskennassa: ' * finnish + integrated_loudness_calculation_error_message
			send_error_messages_to_screen_logfile_email(error_message)
			error_message_to_print_with_gnuplot = integrated_loudness_calculation_error_message + '\\n'
		if timeslice_calculation_error == True:
			error_message = 'ERROR !!! in libebur128 timeslice calculation: ' * english + 'VIRHE !!! libebur128:n aanekkyystaulukon laskennassa: ' * finnish +  timeslice_calculation_error_message
			send_error_messages_to_screen_logfile_email(error_message)
			error_message_to_print_with_gnuplot = error_message_to_print_with_gnuplot + timeslice_calculation_error_message + '\\n'
		create_gnuplot_commands_for_error_message(error_message_to_print_with_gnuplot, filename, directory_for_temporary_files, directory_for_results, english, finnish)		
	else:
		# Loudness calculation succeeded.
		
		peak_measurement_string_english = '\\nSample peak: '
		peak_measurement_string_finnish = '\\nHuipputaso: '
		if peak_measuring_method == '--peak=true':
			peak_measurement_string_english = '\\nTruePeak: '
			peak_measurement_string_finnish = peak_measurement_string_english
		
		# Generate gnuplot commands for plotting the graphics. Put all gnuplot commands in a list.
		gnuplot_commands=['set terminal jpeg size 1280,960 medium font \'arial\'', \
		'set output ' + '\"' + gnuplot_temporary_output_graphicsfile.replace('"','\\"') + '\"', \
		'set yrange [ 0 : -60 ] noreverse nowriteback', \
		'set grid', \
		'set title ' + '\"\'' + filename.replace('_', ' ').replace('"','\\"') + '\'\\n' + 'Integrated Loudness ' * english + 'Äänekkyystaso ' * finnish + str(integrated_loudness) + ' LUFS\\n ' + difference_from_target_loudness_string + ' dB from target loudness (-23 LUFS)\\nLoudness Range (LRA) ' * english + ' dB:tä tavoitetasosta (-23 LUFS)\\nÄänekkyyden vaihteluväli (LRA) '  * finnish + str(loudness_range) + ' LU' + peak_measurement_string_english * english + peak_measurement_string_finnish * finnish + highest_peak_db_string + ' dBFS' + '\"', \
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
			send_error_messages_to_screen_logfile_email(error_message)
		except OSError as reason_for_error:
			error_message = 'Error opening timeslice tablefile for writing ' * english + 'Aikaviipaleiden taulukkotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message)

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
			send_error_messages_to_screen_logfile_email(error_message)
		except OSError as reason_for_error:
			error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message)

		# Call a subprocess to run gnuplot
		run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish)

		# Call a subprocess to create the loudness corrected audio file.
		create_loudness_adjusted_wav_with_sox(timeslice_calculation_error, difference_from_target_loudness, filename, english, finnish, hotfolder_path, directory_for_results, directory_for_temporary_files, highest_peak_db)


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
		send_error_messages_to_screen_logfile_email(error_message)
	except OSError as reason_for_error:
		error_message = 'Error opening gnuplot datafile for writing error graphics data ' * english + 'Gnuplotin datatiedoston avaaminen virhegrafiikan datan kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)

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
		send_error_messages_to_screen_logfile_email(error_message)
	except OSError as reason_for_error:
		error_message = 'Error opening Gnuplot commandfile for writing ' * english + 'Gnuplotin komentotiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)

	# Call a subprocess to run gnuplot
	run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish)
	

def run_gnuplot(filename, directory_for_temporary_files, directory_for_results, english, finnish):

	# This subroutine runs Gnuplot and generates a graphics file.
	# Gnuplot output is searched for error messages.
	
	
	commandfile_for_gnuplot = directory_for_temporary_files + os.sep + filename + '-gnuplot_commands'
	loudness_calculation_table = directory_for_temporary_files + os.sep + filename + '-loudness_calculation_table'
	gnuplot_temporary_output_graphicsfile = directory_for_temporary_files + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish
	gnuplot_output_graphicsfile = directory_for_results + os.sep + filename + '-Loudness_Results_Graphics.jpg' * english + '-Aanekkyyslaskennan_Tulokset.jpg' * finnish

	# Start gnuplot and give time slice and gnuplot command file names as arguments. Gnuplot generates graphics file in the temporary files directory.
	results_from_gnuplot_run = subprocess.Popen(['gnuplot', commandfile_for_gnuplot], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0] # Run gnuplot.
	results_of_gnuplot_run_list = results_from_gnuplot_run.decode('UTF-8').strip()
	
	# If gnuplot outputs something, there was an error. Print message to user.
	if not len(results_of_gnuplot_run_list) == 0:
		error_message = 'ERROR !!! Plotting graphics with Gnuplot, ' * english + 'VIRHE !!! Grafiikan piirtämisessä Gnuplotilla, ' * finnish + ' ' + filename + ' : ' + results_of_gnuplot_run_list
		send_error_messages_to_screen_logfile_email(error_message)

	# Remove time slice and gnuplot command files and move graphics file to results directory.
	try:
		os.remove(commandfile_for_gnuplot)
		os.remove(loudness_calculation_table)
		pass
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error deleting gnuplot command- or time slice file ' * english + 'Gnuplotin komento- tai aikaviipale-tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
	except OSError as reason_for_error:
		error_message = 'Error deleting gnuplot command- or time slice file ' * english + 'Gnuplotin komento- tai aikaviipale-tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)

	try:
		shutil.move(gnuplot_temporary_output_graphicsfile, gnuplot_output_graphicsfile)
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error moving gnuplot graphics file ' * english + 'Gnuplotin grafiikkatiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
	except OSError as reason_for_error:
		error_message = 'Error moving gnuplot graphics file ' * english + 'Gnuplotin grafiikkatiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)


def create_loudness_adjusted_wav_with_sox(timeslice_calculation_error, difference_from_target_loudness, filename, english, finnish, hotfolder_path, directory_for_results, directory_for_temporary_files, highest_peak_db):

	'''This subroutine creates a loudness corrected wav using sox'''

	# This subroutine works like this:
	# ---------------------------------
	# The process gets the difference from target loudness as it's argument.
	# The process starts sox using the difference as gain parameter and creates a loudness corrected wav.
	# The corrected file is written to temporary directory and when ready moved to the target directory for the user to see. This prevents user from using an incomplete file by accident.

	integrated_loudness_calculation_results_list = []
	global integrated_loudness_calculation_results
	global libebur128_path

	# Create loudness corrected file if there were no errors in loudness calculation.
	if (timeslice_calculation_error == False):
		file_to_process = hotfolder_path + os.sep + filename
		filename_and_extension = os.path.splitext(filename)
		temporary_targetfile = directory_for_temporary_files + os.sep + filename_and_extension[0] + '_-23_LUFS' + '.wav'
		temporary_peak_limited_targetfile = filename_and_extension[0] + '-Peak_Limited' + '.wav'
		targetfile = directory_for_results + os.sep + filename_and_extension[0] + '_-23_LUFS' + '.wav'
		difference_from_target_loudness_sign_inverted = difference_from_target_loudness * -1 # The sign (+/-) of the difference from target loudness needs to be flipped for sox. Plus becomes minus and vice versa.
		
		
		# Set the absolute peak level for the resulting corrected audio file.
		# If sample peak is used for the highest value, then set the absolute peak to be -4 dBFS (resulting peaks will be about 1 dB higher than this).
		# If TruePeak calculations are used to measure highest peak, then set the maximum peak level to -2 dBFS (resulting peaks will be about 1 dB higher than this).
		audio_peaks_absolute_ceiling = -4
		if peak_measuring_method == '--peak=true':
			audio_peaks_absolute_ceiling = -2
		
		# Calculate the level where absolute peaks must be limited to before gain correction, to get the resulting max peak level we want.
		hard_limiter_level = difference_from_target_loudness + audio_peaks_absolute_ceiling

		# Start sox and create loudness corrected file to temporary files directory.
		if difference_from_target_loudness >= 0:
			# Loudness correction requires decreasing volume, no peak limiting is needed. Run sox without limiter.
			results_from_sox_run = subprocess.Popen(['sox', file_to_process, temporary_targetfile, 'gain', str(difference_from_target_loudness_sign_inverted)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
			
			# If sox did output something, there was and error. Print message to user.
			results_from_sox_run_list = results_from_sox_run.decode('UTF-8').strip()
			if not len(results_from_sox_run_list) == 0:
				error_message = 'ERROR !!!' * english + 'VIRHE !!!' * finnish + ' ' + filename + ': ' + results_from_sox_run_list 
				send_error_messages_to_screen_logfile_email(error_message)
		if difference_from_target_loudness < 0:
			
			# Loudness correction requires increasing the volume, and peaks after correction might exceed our upper sample peak limit defined in 'audio_peaks_absolute_ceiling'. Run sox with a limiter if limiting is needed.
			
			if highest_peak_db + difference_from_target_loudness_sign_inverted > audio_peaks_absolute_ceiling:
				# Peaks after loudness correction will exceed our upper sample peak limit defined in 'audio_peaks_absolute_ceiling'. Run sox with a limiter.
				# Peaks will be limited below -3 dBFS because fast peaks higher than this might cause clipping in the DA-Converter when the sound is played.
				# The limiter tries to introduce as little distortion as possible while being very effective in hard-limiting the peaks.
				# There are three limiting - stages each 1 dB above previous and with 'tighter' attack and release values than the previous one.
				# These stages limit the peaks while rounding the resulting peak waveforms.
				# Still some very fast peaks escape these three stages and the final hard-limiter stage deals with those.

				# Create sox commands for all four limiter stages.
				compander_1 = ['compand', '0.005,0.3', '1:' + str(hard_limiter_level + -3) + ',' + str(hard_limiter_level + -3) + ',0,' + str(hard_limiter_level +  -2)]
				compander_2 = ['compand', '0.002,0.15', '1:' + str(hard_limiter_level + -2) + ',' + str(hard_limiter_level + -2) + ',0,' + str(hard_limiter_level +  -1)]
				compander_3 = ['compand', '0.001,0.075', '1:' + str(hard_limiter_level + -1) + ',' + str(hard_limiter_level + -1) + ',0,' + str(hard_limiter_level +  -0)]
				hard_limiter = ['compand', '0,0', '3:' + str(hard_limiter_level + -3) + ',' + str(hard_limiter_level + -3) + ',0,'+ str(hard_limiter_level + 0)]
				
				# Combine all sox commands into one list.
				sox_commandline = ['sox', file_to_process, directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile]
				sox_commandline.extend(compander_1)
				sox_commandline.extend(compander_2)
				sox_commandline.extend(compander_3)
				sox_commandline.extend(hard_limiter)
				
				# Hard-limit peaks from the file with sox. No gain is added at this stage.
				results_from_sox_run = subprocess.Popen(sox_commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
				
				# If sox did output something, there was and error. Print message to user.
				results_from_sox_run_list = results_from_sox_run.decode('UTF-8').strip()
				if not len(results_from_sox_run_list) == 0:
					error_message = 'ERROR !!!' * english + 'VIRHE !!!' * finnish + ' ' + filename + ': ' + results_from_sox_run_list 
					send_error_messages_to_screen_logfile_email(error_message)
				
				# Peak limiting probably changed integrated loudness of the file. We need to calculate loudness again before creating the loudness corrected file.
				event_for_integrated_loudness_calculation = threading.Event() # Create a dummy event for loudness calculation subroutine. This is needed by the subroutine, but not used anywhere else, since we do not start loudness calculation as a thread.
				libebur128_commands_for_integrated_loudness_calculation=[libebur128_path, 'scan', '-l', peak_measuring_method] # Put libebur128 commands in a list.
				calculate_integrated_loudness(event_for_integrated_loudness_calculation, temporary_peak_limited_targetfile, directory_for_temporary_files, libebur128_commands_for_integrated_loudness_calculation, english, finnish)
				
				# Get loudness calculation results from the integrated loudness calculation process. Results are in list format in dictionary 'integrated_loudness_calculation_results', assing results to variables.
				integrated_loudness_calculation_results_list = integrated_loudness_calculation_results.pop(temporary_peak_limited_targetfile)# Get loudness results for the file and remove this information from dictionary.
				difference_from_target_loudness = integrated_loudness_calculation_results_list[1]
				difference_from_target_loudness_sign_inverted = difference_from_target_loudness * -1 # The sign (+/-) of the difference from target loudness needs to be flipped for sox. Plus becomes minus and vice versa.
				highest_peak_db = integrated_loudness_calculation_results_list[5]
				
				# Now we need the integrated loudness of the peak limited file, adjust it's loudness with sox
				results_from_sox_run = subprocess.Popen(['sox', directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile, temporary_targetfile, 'gain', str(difference_from_target_loudness_sign_inverted)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
				
				# If sox did output something, there was and error. Print message to user.
				results_from_sox_run_list = results_from_sox_run.decode('UTF-8').strip()
				if not len(results_from_sox_run_list) == 0:
					error_message = 'ERROR !!!' * english + 'VIRHE !!!' * finnish + ' ' + filename + ': ' + results_from_sox_run_list 
					send_error_messages_to_screen_logfile_email(error_message)
			else:
				# Peaks after loudness correction will not exceed our upper sample peak limit defined in 'audio_peaks_absolute_ceiling'. Run sox without a limiter.
				results_from_sox_run = subprocess.Popen(['sox', file_to_process, temporary_targetfile, 'gain', str(difference_from_target_loudness_sign_inverted)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
		
				results_from_sox_run_list = results_from_sox_run.decode('UTF-8').strip()
				# If sox did output something, there was and error. Print message to user.
				if not len(results_from_sox_run_list) == 0:
					error_message = 'ERROR !!!' * english + 'VIRHE !!!' * finnish + ' ' + filename + ': ' + results_from_sox_run_list 
					send_error_messages_to_screen_logfile_email(error_message)
			
		# If the temporary peak limited file is there, delete it.
		if os.path.exists(directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile):
			try:
				os.remove(directory_for_temporary_files + os.sep + temporary_peak_limited_targetfile)
			except KeyboardInterrupt:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error deleting temporary peak limited file ' * english + 'Väliaikaisen limitoidun tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message)
			except OSError as reason_for_error:
				error_message = 'Error deleting temporary peak limited file ' * english + 'Väliaikaisen limitoidun tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message)
				
		# Even if sox reported errors, check if sox created the loudness corrected wav and move it to results folder.
		if os.path.exists(temporary_targetfile):
			# There were no errors, and loudness corrected file is ready, move it from temporary directory to results directory.
			try:
				shutil.move(temporary_targetfile, targetfile)
			except KeyboardInterrupt:
				print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
				sys.exit(0)
			except IOError as reason_for_error:
				error_message = 'Error moving loudness adjusted file ' * english + 'Äänekkyyskorjatun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message)
			except OSError as reason_for_error:
				error_message = 'Error moving loudness adjusted file ' * english + 'Äänekkyyskorjatun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
				send_error_messages_to_screen_logfile_email(error_message)

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

def decompress_audio_streams_with_ffmpeg(event_1_for_ffmpeg_audiostream_conversion, event_2_for_ffmpeg_audiostream_conversion, filename, file_format_support_information, hotfolder_path, directory_for_temporary_files, adjust_line_printout, english, finnish, ffmpeg_output_format):

	'''This subprocess decompresses the first 8 audiostreams from a file with ffmpeg'''

	# This subprocess works like this:
	# ---------------------------------
	# The process gets the number of audio streams ffmpeg previously found in the file.
	# FFmpeg options for extracting audio streams are created and ffmpeg started.
	# The resulting files are losslessly compressed with flac to save disk space. (Flac also supports file sizes larger than 4 GB. Note: Flac compression routines in ffmpeg are based on flake and are much faster than the ones in the standard flac - command).
	# The resulting files are moved to the HotFolder so the program sees them as new files and queues them for loudness calculation.
	# The original file is queued for deletion.

	# Get the information ffmpeg previously found out about the audio streams in the file and put each piece of information in a variable.
	natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string = file_format_support_information
	file_to_process = hotfolder_path + os.sep + filename
	filename_and_extension = os.path.splitext(filename)
	target_filenames = []
	global files_queued_for_deletion
	
	# Generate the beginning of the ffmpeg commandline options.
	if ffmpeg_output_format == 'flac': # User want's resulting files to be written in flac, adjust options for that.
		ffmpeg_commandline = ['ffmpeg', '-y', '-i', file_to_process, '-vn', '-acodec', 'flac']
	else:
		# User want's resulting files to be written in wav, adjust options for that.
		ffmpeg_commandline = ['ffmpeg', '-y', '-i', file_to_process, '-vn', '-acodec', 'pcm_s16le']

	# Generate the rest of the ffmpeg options.
	for counter in range(0, number_of_ffmpeg_supported_audiostreams):
		# Create names for audio streams found in the file.
		# First parse the number of audio channels in each stream ffmpeg reported and put it in a variable.
		number_of_audio_channels = '0'
		number_of_audio_channels_as_text = str(details_of_ffmpeg_supported_audiostreams[counter]).split(',')[2].strip() # FFmpeg reports audio channel count as a string.
		
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
		if number_of_audio_channels_as_text == '5.1':
			number_of_audio_channels = '6'
		
		if number_of_audio_channels == '0':
			error_message = 'ERROR !!! I could not parse FFmpeg channel count string: ' * english + 'VIRHE !!! En osannut tulkita ffmpeg:in antamaa kanavien lukumäärää: ' * finnish + '\'' + str(number_of_audio_channels_as_text_split_to_a_list[0]) + '\'' + ' for file:' * english + ' tiedostolle ' * finnish + ' ' + filename
			send_error_messages_to_screen_logfile_email(error_message)
		
		# Compile the name of the audiostream to an list of all audio stream filenames.
		target_filenames.append(filename_and_extension[0] + '-AudioStream-' + str(counter + 1) + '-AudioChannels-' * english + '-AaniKanavia-' * finnish  + number_of_audio_channels + '.' + ffmpeg_output_format)
		
		# Generate options for each audio stream found.
		ffmpeg_commandline.append('-f')
		ffmpeg_commandline.append(ffmpeg_output_format)
		ffmpeg_commandline.append(directory_for_temporary_files + os.sep + target_filenames[counter])

	# Run ffmpeg and parse output
	ffmpeg_run_output = subprocess.Popen(ffmpeg_commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
	ffmpeg_run_output_decoded = ffmpeg_run_output.decode('UTF-8')
	ffmpeg_run_output_result_list = str(ffmpeg_run_output_decoded).split('\n')
	for item in ffmpeg_run_output_result_list:
		if 'error:' in item.lower(): # If there is the string 'error' in ffmpeg's output, there has been an error.
			error_message = 'ERROR !!! Extracting audio streams with ffmpeg, ' * english + 'VIRHE !!! Audio streamien purkamisessa ffmpeg:illä, ' * finnish + ' ' + filename + ' : ' + results_of_gnuplot_run_list
			send_error_messages_to_screen_logfile_email(error_message)

	# Move each audio file we created from temporary directory to results directory.
	for item in target_filenames:
		try:
			shutil.move(directory_for_temporary_files + os.sep + item, hotfolder_path + os.sep + item)
		except KeyboardInterrupt:
			print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
			sys.exit(0)
		except IOError as reason_for_error:
			error_message = 'Error moving ffmpeg decompressed file ' * english + 'FFmpeg:illä puretun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message)
		except OSError as reason_for_error:
			error_message = 'Error moving ffmpeg decompressed file ' * english + 'FFmpeg:illä puretun tiedoston siirtäminen epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message)
	
	# Queue the original file for deletion. It is no longer needed since we have extracted all audio streams from it.		
	files_queued_for_deletion.append(filename)

	# Set the events so that the main program can see that extracting audio streams from file is ready.
	event_1_for_ffmpeg_audiostream_conversion.set()
	event_2_for_ffmpeg_audiostream_conversion.set()

def send_error_messages_to_screen_logfile_email(error_message):
	
	# This subroutine prints error messages to the screen or logfile or sends them by email.
	# The variable 'error_message' holds the actual message and the list 'where_to_send_error_messages' tells where to print / send them. The list can have any or all of these values: 'screen', 'logfile', 'email'.
	
	global error_messages_to_email_later_list # This variable is used to store messages that are later all sent by email in one go.
	global where_to_send_error_messages
	global error_logfile_path
	error_message_with_timestamp = str(get_realtime(english, finnish)) + '   ' + error_message # Add the current date and time at the beginning of the error message.
	
	# Print error messages to screen
	if 'screen' in where_to_send_error_messages:
		print('\033[7m' + '\r-------->  ' + error_message_with_timestamp + '\033[0m')

	# Print error messages to a logfile
	if 'logfile' in where_to_send_error_messages:
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
	if 'email' in where_to_send_error_messages:
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
		machine_info = '\n\nMachine info:\n----------------------------\n' + 'Commandline: ' + ' '.join(sys.argv) + '\n' + 'IP-Addresses: ' + ','.join(all_ip_addresses_of_the_machine) + '\n' + 'PID: ' + str(loudness_correction_pid) + '\n\n'
		
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
				reason_for_failed_send.append('Error, Timeout error:', reason_for_error)
			except smtplib.socket.error as reason_for_error:
				reason_for_failed_send.append('Error, Socket error:', reason_for_error)
			except smtplib.SMTPRecipientsRefused as reason_for_error:
				reason_for_failed_send.append('Error, All recipients were refused:', reason_for_error)
			except smtplib.SMTPHeloError as reason_for_error:
				reason_for_failed_send.append('Error, The server didn’t reply properly to the HELO greeting:', reason_for_error)
			except smtplib.SMTPSenderRefused as reason_for_error:
				reason_for_failed_send.append('Error, The server didn’t accept the sender address:', reason_for_error)
			except smtplib.SMTPDataError as reason_for_error:
				reason_for_failed_send.append('Error, The server replied with an unexpected error code or The SMTP server refused to accept the message data:', reason_for_error)
			except smtplib.SMTPException as reason_for_error:
				reason_for_failed_send.append('Error, The server does not support the STARTTLS extension or No suitable authentication method was found:', reason_for_error)
			except smtplib.SMTPAuthenticationError as reason_for_error:
				reason_for_failed_send.append('Error, The server didn’t accept the username/password combination:', reason_for_error)
			except smtplib.SMTPConnectError as reason_for_error:
				reason_for_failed_send.append('Error, Error occurred during establishment of a connection with the server:', reason_for_error)
			except RuntimeError as reason_for_error:
				reason_for_failed_send.append('Error, SSL/TLS support is not available to your Python interpreter:', reason_for_error)
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
			send_error_messages_to_screen_logfile_email(error_message)
		except OSError as reason_for_error:
			error_message = 'Error opening loudness calculation queue html-file for writing ' * english + 'Laskentajonon html-tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message)
			
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
			send_error_messages_to_screen_logfile_email(error_message)
		except OSError as reason_for_error:
			error_message = 'Error opening HeartBeat commandfile for writing ' * english + 'HeartBeat - tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message)
			
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
			send_error_messages_to_screen_logfile_email(error_message)
		except OSError as reason_for_error:
			error_message = 'Error opening debug-messages file for writing ' * english + 'Debug--tiedoston avaaminen kirjoittamista varten epäonnistui ' * finnish + str(reason_for_error)
			send_error_messages_to_screen_logfile_email(error_message)

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
		print('peak_measuring_method =', all_settings_dict['peak_measuring_method'])
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
	
	# Create the commandline we need to run as root.
	commands_to_run = ['hostname', '-I']

	if debug == True:
		print()
		print('Running commands:', commands_to_run)

	# Run our command.
	stdout, stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
	stdout = str(stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	stderr = str(stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	all_ip_addresses_of_the_machine = stdout.split()
	
	return(all_ip_addresses_of_the_machine)
	
	if debug == True:
		print()
		print('stdout:', stdout)
		print('stderr:', stderr)
		print('all_ip_addresses_of_the_machine =', all_ip_addresses_of_the_machine)

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
all_ip_addresses_of_the_machine = get_ip_addresses_of_the_host_machine() # Get IP-Addresses of the machine.


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
		send_error_messages_to_screen_logfile_email(error_message)
		sys.exit(1)
	except OSError as reason_for_error:
		error_message = 'Error reading configfile: ' * english + 'Asetustiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
		sys.exit(1)
	except EOFError as reason_for_error:
		error_message = 'Error reading configfile: ' * english + 'Asetustiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
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

	if 'delay_between_directory_reads' in all_settings_dict:
		delay_between_directory_reads = all_settings_dict['delay_between_directory_reads']		
	if 'number_of_processor_cores' in all_settings_dict:
		number_of_processor_cores = all_settings_dict['number_of_processor_cores']
	if 'file_expiry_time' in all_settings_dict:
		file_expiry_time = all_settings_dict['file_expiry_time']

	if 'natively_supported_file_formats' in all_settings_dict:
		natively_supported_file_formats = all_settings_dict['natively_supported_file_formats']
	if 'ffmpeg_output_format' in all_settings_dict:
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
	if 'peak_measuring_method' in all_settings_dict:
		peak_measuring_method = all_settings_dict['peak_measuring_method']
	

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

# Test that programs gnuplot, sox, ffmpeg and libebur128 loudness-executable can be found in the path and that they have executable permiossions on.
gnuplot_executable_found = False
sox_executable_found = False
ffmpeg_executable_found = False
libebur128_loudness_executable_found = False
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
# Check if libebur128 loudness-executable can be found.
if (not os.path.exists(libebur128_path)):
	print('\n!!!!!!! libebur128 loudness-executable can\'t be found in path or directory' * english + '\n!!!!!!! libebur128:n loudness-ohjelmaa ei löydy polusta eikä määritellystä hakemistosta' * finnish, libebur128_path, '!!!!!!!\n')
	sys.exit(1)
else:
	# Test that libebur128n loudness-executable has executable permissions on.
	if (not os.access(libebur128_path, os.X_OK)):
		print('\n!!!!!!! libebur128 loudness-executable does not have \'executable\' permissions on !!!!!!!\n' * english + '\n!!!!!!! libebur128:n loudness-ohjelmalla ei ole käynnistyksen mahdollistava \'executable\' oikeudet päällä !!!!!!!\n' * finnish)
		sys.exit(1)

# Define the name of the error logfile.
error_logfile_path = directory_for_error_logs + os.sep + 'error_log-' + str(get_realtime(english, finnish)) + '.txt' # Error log filename is 'error_log' + current date + time

# The dictionary 'loudness_correction_program_info_and_timestamps' is used to send information to the HeartBeat_Checker - program that is run indipendently of the LoudnessCorrection - script.
# Some threads in LoudnessCorrection write periodically a timestamp to this dictionary indicating they are still alive. 
# The dictionary gets written to disk periodically and the HeartBeat_Checker - program checks that the timestamps in it keeps changing and sends email to the user if they stop.
# The commandline used to start LoudnessCorrection - script and the PID it is currently running on is also recorded in this dictionary. This infomation may be used
# in the future to automatically kill and start again LoudnessCorrection if some of it's threads have crashed, but that is not implemented yet.
#
# Keys 'main_thread' and 'write_html_progress_report' have a list of two values. The first one (True / False) tells if user enabled the feature or not. For example if user does not wan't
# LoudnessCorrection to write a html - page to disk, he set the variable 'write_html_progress_report' to False and this value is also sent to HeartBeat_Checker so that it knows the
# Html - thread won't be updating it's timestamp.

loudness_correction_program_info_and_timestamps = {'loudnesscorrection_program_info' : [sys.argv, loudness_correction_pid, all_ip_addresses_of_the_machine], 'main_thread' : [True, 0], 'write_html_progress_report' : [write_html_progress_report, 0]}

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

#################
# The main loop #
#################
while True:
	
	loudness_correction_program_info_and_timestamps['main_thread'] = [True, int(time.time())] # Update the heartbeat timestamp for the main thread. This is used to keep track if the main thread has crashed.
	loudness_correction_program_info_and_timestamps['loudnesscorrection_program_info'] = [sys.argv, loudness_correction_pid, all_ip_addresses_of_the_machine]
	
	try:
		# Get directory listing for HotFolder. The 'break' statement stops the for - statement from recursing into subdirectories.
		for path, list_of_directories, list_of_files in os.walk(hotfolder_path):
			break
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading HotFolder directory listing ' * english + 'Lähdehakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
	except OSError as reason_for_error:
		error_message = 'Error reading HotFolder directory listing ' * english + 'Lähdehakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
		
	# The files in 'unsupported_ignored_files_dict' are files that ffmpeg was not able to find any audiostreams from, or streams were found but the duration is less than 1 second.
	# Check if files in the unsupported files dictionary have vanished from the HotFolder. If a name has disappeared from HotFolder, remove it also from the list of unsupported files.
	# Check if files in the unsupported files dictionary have been there longer than the expiry time allows, queue expired files for deletion.
	unsupported_ignored_files_list = list(unsupported_ignored_files_dict) # Copy filesnames from dictionary to a list to use as for - loop iterable, since we can't use the dictionary directly because we are going to delete values from it. The for loop - iterable is forbidden to change.
	for filename in unsupported_ignored_files_list:
		if not filename in list_of_files:
			unsupported_ignored_files_dict.pop(filename) # If unsupported file that previously was in HotFolder has vanished, remove its name from the unsupported files list.
			continue
		if int(time.time()) - unsupported_ignored_files_dict[filename] >= file_expiry_time:
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
			file_information_to_save=[file_metadata.st_size, int(time.time())] # Put file size and the time the file was first seen in HotFolder in a list.

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
					dummy_information = [False, False, 0, [], '3'] 
					file_information_to_save.append(dummy_information)
				new_hotfolder_filelist_dict[filename] = file_information_to_save
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n' * english + '\n\nKäyttäjä pysäytti ohjelman.\n' * finnish)
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading HotFolder file metadata ' * english + 'Lähdehakemistopussa olevan tiedoston tietojen lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
	except OSError as reason_for_error:
		error_message = 'Error reading HotFolder file metadata ' * english + 'Lähdehakemistopussa olevan tiedoston tietojen lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
		
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
		send_error_messages_to_screen_logfile_email(error_message)
	except OSError as reason_for_error:
		error_message = 'Error reading ResultsFolder directory listing ' * english + 'Tuloshakemiston hakemistopuun lukeminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)

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
		send_error_messages_to_screen_logfile_email(error_message)
	except OSError as reason_for_error:
		error_message = 'Error deleting files queued for deletion ' * english + 'Poistettavien luettelossa olevan tiedoston poistaminen epäonnistui ' * finnish + str(reason_for_error)
		send_error_messages_to_screen_logfile_email(error_message)
			
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
			old_filesize = old_hotfolder_filelist_dict[filename][0] # Get file size from the previous directory poll.
			time_file_was_first_seen = old_hotfolder_filelist_dict[filename][1] # Get the time the file was first seen from the previous directory poll dictionary.				
			file_format_support_information = old_hotfolder_filelist_dict[filename][2] # Get other file information that was gathered during the last poll.

			# If filesize is still zero and it has not changed in 1,5 hours (5400 seconds), stop waiting and remove filename from list_of_growing_files.
			# (int(time.time()) - old_hotfolder_filelist_dict[filename][1] > file_expiry_time)
			if (filename in list_of_growing_files) and (new_filesize == 0) and (int(time.time()) >= (time_file_was_first_seen + 5400)):
				list_of_growing_files.remove(filename)
			if (filename in list_of_growing_files) and (new_filesize > 0): # If file is in the list of growing files, check if growing has stopped. If HotFolder is on a native windows network share and multiple files are transferred to the HotFolder at the same time, the files get a initial file size of zero, until the file actually gets transferred. Checking for zero file size prevents trying to process the file prematurely.
				if new_filesize != old_filesize: # If file size has changed print message to user about waiting for file transfer to finish.
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
					
					# Test with ffmpeg if the file has audio streams in it, if true queue file for loudness calculation  
					if we_have_true_read_access_to_the_file == True:
						
						natively_supported_file_format = False # This variable tells if the file format is natively supported by libebur128 and sox. We do not yet know the format of the file, we just set the default here. If format is not natively supported by libebur128 and sox, file will be first extracted to flac with ffmpeg.
						ffmpeg_supported_fileformat = False # This variable tells if the file format is natively supported by ffmpeg. We do not yet know the format of the file, we just set the default here. If format is not supported by ffmpeg, we have no way of processing the file and will be queued for deletion.
						number_of_ffmpeg_supported_audiostreams = 0 # This variable holds the number of audio streams ffmpeg finds in the file.
						details_of_ffmpeg_supported_audiostreams = [] # Holds ffmpeg produced information about audio streams found in file (example: 'Stream #0.1[0x82]: Audio: ac3, 48000 Hz, 5.1, s16, 384 kb/s' )
						audio_duration_string = ''
						audio_duration_list = []
						audio_duration_rounded_to_seconds = 0
						time_slice_duration_string = '3' # Set the default value to use in timeslice loudness calculation. This will be changed by the program to 0.5, if file duration is <= 9 seconds.
						ffmpeg_error_message = ''
						
						# Examine the file with ffmpeg and parse its output.
						ffmpeg_run_output = subprocess.Popen(['ffmpeg', '-i', file_to_test], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0] # Run ffmpeg.
						ffmpeg_run_output_decoded = ffmpeg_run_output.decode('UTF-8') # Convert ffmpeg output from binary to utf-8 text.
						ffmpeg_run_output_result_list = str(ffmpeg_run_output_decoded).split('\n') # Split ffmpeg output by linefeeds to a list.

						# Parse ffmpeg output inspecting it line by line.
						for item in ffmpeg_run_output_result_list:
							if 'Audio:' in item: # There is the string 'Audio' for each audio stream that ffmpeg finds. Count how many 'Audio' strings is found and put the strings in a list. The string holds detailed information about the stream and we print it later.
								number_of_ffmpeg_supported_audiostreams = number_of_ffmpeg_supported_audiostreams + 1
								details_of_ffmpeg_supported_audiostreams.append(item.strip())
							if 'Duration:' in item:
								audio_duration_string = str(item).split(',')[0].strip() # The first item on the line is the duration, get it.
								audio_duration_string = audio_duration_string.split(' ')[1].strip() # Remove the string 'Duration:' that is in front of the time string we want.
								# Check that audio duration is a valid time, if it is 'N/A' then ffmpeg can not extract the audio stream.
								if not 'N/A' in audio_duration_string:
									# Get the file duration as a string and also calculate it in seconds.
									audio_duration_string = audio_duration_string.split('.')[0] # Remove the fraction part from time string. This rounds the time to seconds.
									audio_duration_list = audio_duration_string.split(':') # Separate each element in the time string (hours, minutes, seconds) and put them in a list.
									audio_duration_rounded_to_seconds = (int(audio_duration_list[0]) * 60 * 60) + (int(audio_duration_list[1]) * 60) + int(audio_duration_list[2]) # Calculate audio duration in seconds.
								else:
									# The FFmpeg reported audio duration as 'N/A' then this means ffmpeg could not determine the audio duration. Set audio duration to 0 seconds and inform user about the error.
									audio_duration_rounded_to_seconds = 0
									error_message = 'FFmpeg Error : Audio Duration = N/A' * english + 'FFmpeg Virhe: Äänen Kesto = N/A' * finnish + ': ' + filename
									send_error_messages_to_screen_logfile_email(error_message)
							if filename + ':' in item: # Try to recognize some ffmpeg error messages, these always start with the filename + ':'
								ffmpeg_error_message = item.split(':')[1] # Get the reason for error from ffmpeg output.
						if number_of_ffmpeg_supported_audiostreams > 0: # If ffmpeg found audio streams check if the file extension is one of the libebur128 and sox supported ones (wav, flac, ogg).
							ffmpeg_supported_fileformat = True
							if str(os.path.splitext(filename)[1]).lower() in natively_supported_file_formats:
								natively_supported_file_format = True
						if (number_of_ffmpeg_supported_audiostreams == 1) and (str(os.path.splitext(filename)[1]).lower() == '.wav'): # Test if wav - file has more than two channels, since libebur128 only supports mono and stereo wav - files.  If there are more channels, queue file to audio extraction and flac conversion with ffmpeg.
							number_of_audio_channels = str(details_of_ffmpeg_supported_audiostreams).split(',')[2].strip() # Get the number of audio channels from ffmpeg output. FFmpeg output is in a list, since wav does not support more than 1 audiostreams, the list always has only 1 item and can be safely converted to string for manipulation.
							if  (number_of_audio_channels != '1 channels') and (number_of_audio_channels != 'mono') and (number_of_audio_channels != '2 channels') and (number_of_audio_channels != 'stereo'): # If there are more than 2 channels in wav, queue file for audio extraction and flac conversion with ffmpeg.
								natively_supported_file_format = False
						if (number_of_ffmpeg_supported_audiostreams == 1) and (str(os.path.splitext(filename)[1]).lower() == '.ogg'): # Test if ogg - file has more than two channels, since sox only supports mono and stereo wav - files. If there are more channels, queue file to audio extraction and flac compression with ffmpeg.
							number_of_audio_channels = str(details_of_ffmpeg_supported_audiostreams).split(',')[2].strip() # Get the number of audio channels from ffmpeg output.
							if  (number_of_audio_channels != '1 channels') and (number_of_audio_channels != 'mono') and (number_of_audio_channels != '2 channels') and (number_of_audio_channels != 'stereo'): # If there are more than 2 channels in ogg, queue file for audio extraction and flac conversion with ffmpeg.
								natively_supported_file_format = False
						if (ffmpeg_supported_fileformat == False) and (filename not in unsupported_ignored_files_dict):
							# No audiostreams were found in the file, plot an error graphics file to tell the user about it and add the filename and the time it was first seen to the list of files we will ignore.
							if ffmpeg_error_message == '': # Check if ffmpeg printed an error message.
								# If ffmpeg error message can not be found, use a default message.
								error_message = 'No Audio Streams Found In File: ' * english + 'Tiedostosta: ' * finnish + filename + ' ei löytynyt ääniraitoja.' * finnish
							else:
								# FFmpeg error message was found tell the user about it.
								error_message = 'FFmpeg Error : ' * english + 'FFmpeg Virhe: ' * finnish + filename + ': ' + ffmpeg_error_message
							send_error_messages_to_screen_logfile_email(error_message)
							create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish)
							unsupported_ignored_files_dict[filename] = int(time.time())
						if (ffmpeg_supported_fileformat == True) and (not audio_duration_rounded_to_seconds > 0) and (filename not in unsupported_ignored_files_dict):
							# If file duration was not found, or it is less than one second, then we have an error. Don't process file, inform user by plotting an error graphics file and add the filename to the list of files we will ignore.
							error_message = 'Audio duration less than 1 second: ' * english + 'Tiedoston: ' * finnish + filename + ' ääniraidan pituus on alle 1 sekunti.' * finnish
							send_error_messages_to_screen_logfile_email(error_message)
							create_gnuplot_commands_for_error_message(error_message, filename, directory_for_temporary_files, directory_for_results, english, finnish)
							unsupported_ignored_files_dict[filename] = int(time.time())
						# The time slice value used in loudness calculation is normally 3 seconds. When we calculate short files <12 seconds, it's more convenient to use a smaller value of 0.5 seconds to get more detailed loudness graphics.
						if  (audio_duration_rounded_to_seconds > 0) and (audio_duration_rounded_to_seconds < 12):
							time_slice_duration_string = '0.5'
						if  audio_duration_rounded_to_seconds >= 12:
							time_slice_duration_string = '3'
						
						# If ffmpeg finds audiostreams in the file, queue it for loudness calculation and print message to user.
						if filename not in unsupported_ignored_files_dict:
							file_format_support_information = [natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string]
							files_queued_to_loudness_calculation.append(filename)
							if silent == False:
								print('\r' + adjust_line_printout, '"' + str(filename) + '"', 'is in the job queue as number' * english + 'on laskentajonossa numerolla' * finnish, len(files_queued_to_loudness_calculation))
						list_of_growing_files.remove(filename) # File has been queued for loudness calculation, or it is unsupported, in both cases we need to remove it from the list of growing files.
			# Save information about the file in a dictionary:
			# filename, file size, time file was first seen in HotFolder, file format wav / flac / ogg, if format is supported by ffmpeg (True/False), number of audio streams found, information ffmpeg printed about the audio streams.
			new_hotfolder_filelist_dict[filename] = [new_filesize, time_file_was_first_seen, file_format_support_information]
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
				file_format_support_information = old_hotfolder_filelist_dict[filename][2] # The information about the file format is stored in a list in the dictionary, get it and store in a list.
				natively_supported_file_format, ffmpeg_supported_fileformat, number_of_ffmpeg_supported_audiostreams, details_of_ffmpeg_supported_audiostreams, time_slice_duration_string = file_format_support_information # Save file format information to separate variables.
				realtime = get_realtime(english, finnish).replace('_', ' ')
				
				# If audio fileformat is natively supported by libebur128 and sox and has only one audio stream, we don't need to do extraction and flac conversion with ffmpeg, just start two loudness calculation processes for the file.
				if (number_of_ffmpeg_supported_audiostreams == 1) and (natively_supported_file_format == True):
					# Start simultaneously two threads to calculate file loudness. The first one calculates loudness by dividing the file in time slices and calculating the loudness of each slice individually. The second process calculates integrated loudness and loudness range of the file as a whole.
					# Both processes can be done in almost the same time as one, since the first process reads the file in to os file cache, so the second process doesn't need to read the disk at all. Reading from cache is much much faster than reading from disk.
					if silent == False:
						print ('\r' + 'File' * english + 'Tiedoston' * finnish, '"' + filename + '"' + ' processing started ' * english + ' käsittely   alkoi  ' * finnish, realtime)
					
					# Create commands for both loudness calculation processes.
					libebur128_commands_for_time_slice_calculation=[libebur128_path, 'dump', '-s', time_slice_duration_string] # Put libebur128 commands in a list.
					libebur128_commands_for_integrated_loudness_calculation=[libebur128_path, 'scan', '-l', peak_measuring_method] # Put libebur128 commands in a list.
					# Create events for both processes. When the process is ready it sets event = set, so that we now in the main thread that we can start more processes.
					event_for_timeslice_loudness_calculation = threading.Event() # Create a unique event for the process. This event is used to signal other threads that this process has finished.
					event_for_integrated_loudness_calculation = threading.Event() # Create a unique event for the process. This event is used to signal other threads that this process has finished.
					# Add file name and both the calculation process events to the dictionary of files that are currently being calculated upon.
					loudness_calculation_queue[filename] = [event_for_timeslice_loudness_calculation, event_for_integrated_loudness_calculation]
					# Create threads for both processes, the threads are not started yet.
					process_1 = threading.Thread(target=calculate_loudness_timeslices, args=(filename, hotfolder_path, libebur128_commands_for_time_slice_calculation, directory_for_temporary_files, directory_for_results, english, finnish)) # Create a process instance.
					process_2 = threading.Thread(target=calculate_integrated_loudness, args=(event_for_integrated_loudness_calculation, filename, hotfolder_path, libebur128_commands_for_integrated_loudness_calculation, english, finnish)) # Create a process instance.
					# Start both calculation threads.
					thread_object = process_2.start() # Start the calculation process in it's own thread.
					time.sleep(1)
					thread_object = process_1.start() # Start the calculation process in it's own thread.
				else:
					# Filefomat is not natively supported by libebur128 and sox, or it has more than one audio streams.
					# Start a process that extracts all audio streams from the file to flac and moves resulting files back to the HotFolder for loudness calculation.
					if silent == False:
						print ('\r' + 'File' * english + 'Tiedoston' * finnish, '"' + filename + '"' + ' conversion started ' * english + '  muunnos    alkoi  ' * finnish, realtime)
						print('\r' + adjust_line_printout, ' Extracting' * english + ' Puran' * finnish, str(number_of_ffmpeg_supported_audiostreams), 'audio streams from file' * english + 'miksausta tiedostosta' * finnish, filename)
						for counter in range(0, number_of_ffmpeg_supported_audiostreams): # Print information about all the audio streams we are going to extract.
							print('\r' + adjust_line_printout, ' ' + details_of_ffmpeg_supported_audiostreams[counter])
					event_1_for_ffmpeg_audiostream_conversion = threading.Event() # Create two unique events for the process. The events are being used to signal other threads that this process has finished. This thread does not really need two events, only one, but as other calculation processes are started in pairs resulting two events per file, two events must be created here also for this process..
					event_2_for_ffmpeg_audiostream_conversion = threading.Event()
					process_3 = threading.Thread(target = decompress_audio_streams_with_ffmpeg, args=(event_1_for_ffmpeg_audiostream_conversion, event_2_for_ffmpeg_audiostream_conversion, filename, file_format_support_information, hotfolder_path, directory_for_temporary_files, adjust_line_printout, english, finnish, ffmpeg_output_format)) # Create a process instance.
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
