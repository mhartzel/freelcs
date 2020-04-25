#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Mikael Hartzell 2013.
#
# This program is distributed under the GNU General Public License, version 3 (GPLv3)
#
# This program compares loudness calculation results in a loudness_calculation log to another loudness calculation log or to the results of multiple machine readable results files.
#
# This line is used to identify this script when it is started from an external script, don't change. Identifier: compare_two_loudness_calculation_logs.py
#

import sys
import copy
import os
import time

def read_values_in_machine_readable_results_files_to_dictionary(directory_for_machine_readable_result_files):

	results_dict = {}
	list_of_machine_readable_result_files = []
	global unit_separator
	global record_separator

	# Read the machine readble result files and input all values to a dictionary.
	try:                                                                                                                                                                                                                                                                                                
		# Get directory listing for HotFolder. The 'break' statement stops the for - statement from recursing into subdirectories.
		for path, list_of_directories, list_of_files in os.walk(directory_for_machine_readable_result_files):
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

	# Check if file is a machine readable results file and store filenames to a list.
	for filename in list_of_files:

		if '-machine_readable_results.txt' in filename:
			list_of_machine_readable_result_files.append(filename)

	# Get values from machine readable result files and store them in a dictionary.
	for filename in list_of_machine_readable_result_files:

		with open(directory_for_machine_readable_result_files + os.sep + filename, 'r') as file_handler:

			list_of_results_for_mixes = file_handler.readlines()

			for values_for_one_mix in list_of_results_for_mixes:

				# Split values to a list using the unit separator character / string.
				values_for_one_mix_list = values_for_one_mix.split(unit_separator)

				integrated_loudness = values_for_one_mix_list[5]
				loudness_range = values_for_one_mix_list[6]
				highest_peak_db = values_for_one_mix_list[7]
				channel_count = values_for_one_mix_list[8]
				sample_rate = values_for_one_mix_list[9]
				bit_depth = values_for_one_mix_list[10]
				audio_duration = values_for_one_mix_list[11]
				error_code = values_for_one_mix_list[12]

				if highest_peak_db == '-0.0':
					highest_peak_db = '0.0'

				# Get the name of the output file name, if value is a list of filenames then just take the first name.
				if 'list' in str(type(values_for_one_mix_list[14])):
					output_stream_filename = values_for_one_mix_list[14][0].strip()
				else:
					output_stream_filename = values_for_one_mix_list[14].strip()

				if output_stream_filename == '':
					continue

				# The loudness calculation log stores input file names and their results,
				# The machine readable files store filenames of loudness corrected files and the loudness calculation results.
				# As the names in these two files won't match, we need to convert the names in the machine readble results files
				# to match the names in the loudness calculation log before we can find and compare results in both files.
				#
				# Strip out the file extension since it also can be different in input and output files.
				filename_and_extension = os.path.splitext(output_stream_filename)
				output_stream_filename = filename_and_extension[0]

				# Convert the output filename to the same format that is used in the loudness calculation log.
				# Strip out parts of the file name that are added to the loudness corrected file when it is processed.
				if '-Channel-' in output_stream_filename:
					output_stream_filename = output_stream_filename[:output_stream_filename.find('-Channel-')]

				if '-Kanava-' in output_stream_filename:
					output_stream_filename = output_stream_filename[:output_stream_filename.find('-Kanava-')]

				if '_LUFS' in output_stream_filename:
					output_stream_filename = output_stream_filename[:output_stream_filename.rfind('_LUFS') - 4]

				# Only add information to the results dictionary, if the error code indicates there hasn't been any serious errors when processing the file.
				if (int(error_code) == 0) or (int(error_code) == 9):
					results_dict[output_stream_filename] = [integrated_loudness, loudness_range, highest_peak_db, channel_count, sample_rate, bit_depth, audio_duration]

	return(results_dict)

def read_values_in_loudness_calculation_log_to_dictionary(calculation_results_filename):

	loudness_calculation_log_results_dict = {}

	with open(calculation_results_filename, 'rb') as file_handler:
			
		file_contents = file_handler.read()
		file_contents_decoded = str(file_contents.decode('UTF-8'))
		list_of_text_lines = (file_contents_decoded.split('\n'))
		
		# Skip empty lines and split filenames and calculation results found in the text file and assing all calculation results to a dictionary with filename as the key.
		for line in list_of_text_lines:

			line = line.strip()

			if line == '':
				continue

			# Split the text line to two parts using the separator string.
			# The first part is the input audiofile name and the second is a comma separated list of loudness calculation values and technical info.
			filename, loudness_calculation_info = line.split(',EndOFFileName,')

			# Split the loudness calculation and technical info to a list of values.
			loudness_calculation_info_list = loudness_calculation_info.split(',')

			# Remove extension from the file name.
			filename_and_extension = os.path.splitext(filename)
			filename = filename_and_extension[0]

			if loudness_calculation_info_list[2] == '-0.0':
				loudness_calculation_info_list[2] = '0.0'

			# Store results to a dictionary.
			loudness_calculation_log_results_dict[filename] = loudness_calculation_info_list

	return(loudness_calculation_log_results_dict)

def print_instructions_on_program_usage():

	print()
	print('This program can compare results from two loudness calculation logs,')
	print('or results from one loudness calculation log and several machine readable result files,')
	print('or results from two sets of machine readable result files.')
	print()
	print('Usage: ', sys.argv[0], 'LOUDNESS_CALCULATION_LOG_1    LOUDNESS_CALCULATION_LOG_2')
	print('Usage: ', sys.argv[0], 'LOUDNESS_CALCULATION_LOG_1    PATH_TO/MACHINE_READBLE_RESULTS/DIR')
	print('Usage: ', sys.argv[0], 'PATH_TO/MACHINE_READBLE_RESULTS/DIR_1    PATH_TO/MACHINE_READBLE_RESULTS/DIR_2')
	print('Usage: ', sys.argv[0], 'LOUDNESS_CALCULATION_LOG_1    LOUDNESS_CALCULATION_LOG_2   --no-result-highlighting')
	print('Usage: ', sys.argv[0], 'FILENAME1 FILENAME2 --ignore-loudness-results')
	print('Usage: ', sys.argv[0], 'FILENAME1 FILENAME2 --ignore-peak-measurement')
	print()

	sys.exit()

def find_differences_in_two_sets_of_results(loudness_calculation_log_1_dict, loudness_calculation_log_2_dict):

	# Make a copy of the dictionaries where filenames that are found in both can be deleted, leaving only filenames that are not in both lists.
	local_source_dict_1 = copy.deepcopy(loudness_calculation_log_1_dict)
	local_source_dict_2 = copy.deepcopy(loudness_calculation_log_2_dict)
	local_dict_identical_results = {}
	local_dict_differing_results = {}

	file1_calculation_results = []
	file2_calculation_results = []

	global ignore_loudness_results
	global ignore_peak_measurement

	number_of_expected_identical_results = 7

	if ignore_loudness_results == True:
		number_of_expected_identical_results = 4

	if ignore_peak_measurement == True:
		number_of_expected_identical_results = 6

	# Find filenames that are in both dictionaries and compare calculation results from both dictionaries to each other.
	for filename in loudness_calculation_log_1_dict:
		
		if filename in local_source_dict_2:
			file1_calculation_results = local_source_dict_1.pop(filename)
			file2_calculation_results = local_source_dict_2.pop(filename)

			counter_for_identical_values = 0

			 # Test individual measurement results one by one.
			for value_counter in range(0, len(file1_calculation_results)):
				
				# If user wants to ignore loudness results then skip items 0 - 2.
				if ignore_loudness_results == True:

					if (value_counter == 0) or (value_counter == 1) or (value_counter == 2):
						continue

				# If user wants to ignore peak measurements then skip item 2.
				if ignore_peak_measurement == True:

					if value_counter == 2:
						continue

				if file1_calculation_results[value_counter] == file2_calculation_results[value_counter]:

					counter_for_identical_values = counter_for_identical_values + 1

			# Add files to different dictionaries depending on whether the results for the file match or not.
			if counter_for_identical_values == number_of_expected_identical_results:

				local_dict_identical_results[filename] = file1_calculation_results
			else:
				local_dict_differing_results[filename] = [file1_calculation_results, file2_calculation_results]

	return (local_dict_identical_results, local_dict_differing_results, local_source_dict_1, local_source_dict_2)

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


################################################################################
#                                 Initialization                               #
################################################################################

unit_separator = chr(31)
record_separator = chr(13) + chr(10)

path_of_loudness_results1 = ''
path_of_loudness_results2 = ''

loudness_calculation_log_1_dict = {}
loudness_calculation_log_2_dict = {}
files_with_identical_results_dict = {}
files_with_differing_results_dict = {}
files_only_in_path_1_dict = {}
files_only_in_path_2_dict = {}

ignore_loudness_results = False
ignore_peak_measurement = False
no_result_highlighting = False

# The program operates in one of three operating modes:
# 1 = compare two loudness calculation logs
# 2 = compare one loudness calculation log against several machine readable results files
# 3 = compare several machine readable results files against one loudness calculation log
# 4 = compare two sets of machine readable results files against each other
comparison_mode = 0

# Check if command line parameters are sane.
if len(sys.argv) < 3:
	print_instructions_on_program_usage()

if (os.path.isfile(sys.argv[1]) == True) and (os.path.isfile(sys.argv[2]) == True):
	path_of_loudness_results1 = sys.argv[1]
	path_of_loudness_results2 = sys.argv[2]
	comparison_mode = 1

if (os.path.isfile(sys.argv[1]) == True) and (os.path.isdir(sys.argv[2]) == True):
	path_of_loudness_results1 = sys.argv[1]
	path_of_loudness_results2 = sys.argv[2]
	comparison_mode = 2

if (os.path.isdir(sys.argv[1]) == True) and (os.path.isfile(sys.argv[2]) == True):
	path_of_loudness_results1 = sys.argv[1]
	path_of_loudness_results2 = sys.argv[2]
	comparison_mode = 3

if (os.path.isdir(sys.argv[1]) == True) and (os.path.isdir(sys.argv[2]) == True):
	path_of_loudness_results1 = sys.argv[1]
	path_of_loudness_results2 = sys.argv[2]
	comparison_mode = 4

if comparison_mode == 0:
	print_instructions_on_program_usage()

# The user can disable from the commandline all loudness result checks or just the peak measurement check.
if len(sys.argv) > 3:
	if (sys.argv[3] == '--ignore-loudness-results') or (sys.argv[3] == '-ignore-loudness-results'):
		ignore_loudness_results = True

if len(sys.argv) > 3:
	if (sys.argv[3] == '--ignore-peak-measurement') or (sys.argv[3] == '-ignore-peak-measurement'):
		ignore_peak_measurement = True

if ('--no-result-highlighting' in sys.argv) or ('-no-result-highlighting' in sys.argv):
	no_result_highlighting = True


################################################################################
#                                     Main                                     #
################################################################################

# Read in values from loudness calculation and machine readable logs accoring to operating mode :)
if comparison_mode == 1:
	loudness_calculation_log_1_dict = read_values_in_loudness_calculation_log_to_dictionary(path_of_loudness_results1)
	loudness_calculation_log_2_dict = read_values_in_loudness_calculation_log_to_dictionary(path_of_loudness_results2)

if comparison_mode == 2:
	loudness_calculation_log_1_dict = read_values_in_loudness_calculation_log_to_dictionary(path_of_loudness_results1)
	loudness_calculation_log_2_dict = read_values_in_machine_readable_results_files_to_dictionary(path_of_loudness_results2)

if comparison_mode == 3:
	loudness_calculation_log_1_dict = read_values_in_machine_readable_results_files_to_dictionary(path_of_loudness_results1)
	loudness_calculation_log_2_dict = read_values_in_loudness_calculation_log_to_dictionary(path_of_loudness_results2)

if comparison_mode == 4:
	loudness_calculation_log_1_dict = read_values_in_machine_readable_results_files_to_dictionary(path_of_loudness_results1)
	loudness_calculation_log_2_dict = read_values_in_machine_readable_results_files_to_dictionary(path_of_loudness_results2)

# Compare results in the two dictionaries and store results in four dictionaries.
files_with_identical_results_dict, files_with_differing_results_dict, files_only_in_path_1_dict, files_only_in_path_2_dict = find_differences_in_two_sets_of_results(loudness_calculation_log_1_dict, loudness_calculation_log_2_dict)


###################
# Display results #
###################

time_string = get_realtime()[1]

print()
print('Test run time:', time_string)
print('-' * len('Test run time: ' + time_string) + '-')

# Print a warning if the user has disabled some checks.
if ignore_loudness_results == True:

	print()
	print("Warning: the option '--ignore-loudness-results' is turned on !!!!!!!")

if ignore_peak_measurement == True:

	print()
	print("Warning: the option '--ignore-peak-measurement' is turned on !!!!!!!")


###########################################
# Show the total number of source results #
###########################################

print()
print('Data for', str(len(loudness_calculation_log_1_dict)), 'files found in path:', path_of_loudness_results1)
print('Data for', str(len(loudness_calculation_log_2_dict)), 'files found in path:', path_of_loudness_results2)


###################
# Identical files #
###################

if (len(loudness_calculation_log_1_dict) == len(loudness_calculation_log_2_dict)) and (len(loudness_calculation_log_1_dict) == len(files_with_identical_results_dict)):

	print()
	print('Results for all', str(len(files_with_identical_results_dict)), 'files are identical :)')
	print()
else:
	print()
	print('Results for', str(len(files_with_identical_results_dict)), 'files are identical :)')
	print()


################################
# Files with differing results #
################################

if len(files_with_differing_results_dict) != 0:

	# Report any mismatch found.
	print()
	print("Calculation results for " + str(len(files_with_differing_results_dict)) + " files don't match")
	print('-' * len("Calculation results for " + str(len(files_with_differing_results_dict)) + " files don't match") + '--')
	print()

	list_of_non_matching_filenames = list(files_with_differing_results_dict)
	list_of_non_matching_filenames.sort(key=str.lower)

	for item in list_of_non_matching_filenames:

		file1_calculation_results = files_with_differing_results_dict[item][0]
		file2_calculation_results = files_with_differing_results_dict[item][1]

		for value_counter in range(0, len(file1_calculation_results)):

			if file1_calculation_results[value_counter] != file2_calculation_results[value_counter]:
				# integrated_loudness, loudness_range, highest_peak_db, channel_count, sample_rate, bit_depth, audio_duration
				if no_result_highlighting == False:
					calculation_result_type = ['\033[7m' + 'integrated_loudness\t' + '\033[0m', 'loudness_range\t\t', 'highest_peak_db\t\t', 'channel_count\t\t', 'sample_rate\t\t', 'bit_depth\t\t', 'audio_duration\t\t'][value_counter]
				else:
					calculation_result_type = ['integrated_loudness\t', 'loudness_range\t\t', 'highest_peak_db\t\t', 'channel_count\t\t', 'sample_rate\t\t', 'bit_depth\t\t', 'audio_duration\t\t'][value_counter]
				
				# Make the printout prettier by aligning number values to each other.
				string_1_to_print = file1_calculation_results[value_counter]
				string_1_to_print = ' ' * (5 - len(string_1_to_print)) + string_1_to_print
				string_2_to_print = file2_calculation_results[value_counter]
				string_2_to_print = ' ' * (5 - len(string_2_to_print)) + string_2_to_print
				
				print(calculation_result_type + '   ' +  string_1_to_print + '   |  ' + string_2_to_print + '     ' +  item)
	
	print()


########################
# Files only in path 1 #
########################

if len(files_only_in_path_1_dict) != 0:

	# Report any mismatch found.
	print()
	print(str(len(files_only_in_path_1_dict)), "Filenames only in:", path_of_loudness_results1)
	print('-' * len(str(len(files_only_in_path_1_dict)) + " Filenames only in: " + path_of_loudness_results1) + '-')
	print()

	list_of_missing_filenames = []

	list_of_missing_filenames = list(files_only_in_path_1_dict)
	list_of_missing_filenames.sort(key=str.lower)

	for item in list_of_missing_filenames:

		print(item)

	print()


########################
# Files only in path 2 #
########################

if len(files_only_in_path_2_dict) != 0:

	# Report any mismatch found.
	print()
	print(str(len(files_only_in_path_2_dict)), "Filenames only in:", path_of_loudness_results2)
	print('-' * len(str(len(files_only_in_path_2_dict)) + " Filenames only in: " + path_of_loudness_results2) + '-')
	print()

	list_of_missing_filenames = []

	list_of_missing_filenames = list(files_only_in_path_2_dict)
	list_of_missing_filenames.sort(key=str.lower)

	for item in list_of_missing_filenames:

		print(item)

	print()



