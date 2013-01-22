#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#

# This program compares two loudness_calculation logs that were written by LoudnessCorrection.py

import sys
import copy

if len(sys.argv) < 3:
	print()
	print('Usage: ', sys.argv[0], 'FILENAME1 FILENAME2 ')
	print('Usage: ', sys.argv[0], 'FILENAME1 FILENAME2 --ignore-loudness-results')
	print()
	sys.exit()

calculation_results_filename1 = sys.argv[1]
calculation_results_filename2 = sys.argv[2]
file1_dict = {}
file2_dict = {}
differing_calculation_results_dict={}
ignore_loudness_results = False

if len(sys.argv) > 3:
	if sys.argv[3] == '--ignore-loudness-results':
		ignore_loudness_results = True

print()

# Read two text files in.

with open(calculation_results_filename1, 'rb') as file_handler1, open(calculation_results_filename2, 'rb') as file_handler2:
		
	file1 = file_handler1.read()
	file2 = file_handler2.read()

	file1 = str(file1.decode('UTF-8'))
	file2 = str(file2.decode('UTF-8'))		
	
	file1_lines = (file1.split('\n'))
	file2_lines = (file2.split('\n'))
	
	
	# Skip empty lines and split filenames and calculation results found in the text files and assing all calculation results to a dictionary with filename as the key.
	
	for line1 in file1_lines:
		line1 = line1.strip()
		if line1 == '':
			continue
		filename1, loudness_calculation_info1 = line1.split(',EndOFFileName,')
		loudness_calculation_info_list1 = loudness_calculation_info1.split(',')
		file1_dict[filename1] = loudness_calculation_info_list1
	
	for line2 in file2_lines:
		line2 = line2.strip()
		if line2 == '':
			continue
		filename2, loudness_calculation_info2 = line2.split(',EndOFFileName,')
		loudness_calculation_info_list2 = loudness_calculation_info2.split(',')
		file2_dict[filename2] = loudness_calculation_info_list2
	
	# Make a copy of the dictionaries where filenames that are found in both can be deleted, leaving only filenames that are not in both lists.
	file1_dict_names_remaining = copy.deepcopy(file1_dict)
	file2_dict_names_remaining = copy.deepcopy(file2_dict)
	
	# Find filenames that are in both dictionaries and compare calculation results from both text files to each other.

	counter = 0
	filenamelist_of_differing_calculation_results = []

	for filename_file1 in file1_dict:
		
		if filename_file1 in file2_dict:
			file1_calculation_results = file1_dict_names_remaining.pop(filename_file1)
			file2_calculation_results = file2_dict_names_remaining.pop(filename_file1)
			
			for value_number in range(0, len(file1_calculation_results)):
				
				# If user wants to ignore loudness results then skip them (items 0 - 2).
				if ignore_loudness_results == True:
					if (value_number == 0) or (value_number == 1) or (value_number == 2):
						continue
				
				if file1_calculation_results[value_number] != file2_calculation_results[value_number]:

					counter = counter + 1

					# filename, integrated_loudness, loudness_range, highest_peak_db, channel_count, sample_rate, bit_depth, audio_duration
					calculation_result_type = ['\033[7m' + 'integrated_loudness' + '\033[0m', 'loudness_range     ', 'highest_peak_db    ', 'channel_count    ', 'sample_rate    ', 'bit_depth    ', 'audio_duration    '][value_number]
					
					# Make the printout prettier by aligning columns to each other.
					string_1_to_print = file1_calculation_results[value_number]
					string_1_to_print = ' ' * (5 - len(string_1_to_print)) + string_1_to_print
					string_2_to_print = file2_calculation_results[value_number]
					string_2_to_print = ' ' * (5 - len(string_2_to_print)) + string_2_to_print
					
					#print( calculation_result_type, ' ', string_1_to_print, '  | ', string_2_to_print, 'differ:',  filename_file1)
					differing_calculation_results_dict[filename_file1] = str(calculation_result_type + '   ' +  string_1_to_print + '   |  ' + string_2_to_print + ' differ: ' +  filename_file1)
					filenamelist_of_differing_calculation_results.append(filename_file1)

	if len(differing_calculation_results_dict) != 0:
	
		# Report any mismatch found.
		print()
		print("Calculation results that don't match")
		print('-------------------------------------')
		print()
		
		filenamelist_of_differing_calculation_results.sort(key=str.lower)

		for differing_item in filenamelist_of_differing_calculation_results:
			print(differing_calculation_results_dict[differing_item])
		
		print()
		print('Total differing calculation results =', counter)
		
	else:
		print()
		print('All calculation results are identical :)')
		print()

	print()

# Print filenames that were not in both dictionaries.
if len(file1_dict_names_remaining) != 0:
	filenames1_remaining_list = list(file1_dict_names_remaining)
	filenames1_remaining_list.sort(key=str.lower)
	print()
	print()
	print(str(len(filenames1_remaining_list)) + ' Filenames not found in', calculation_results_filename2 + ':')
	print('-' * (len(str(len(filenames1_remaining_list)) + 'Filenames not found in' + calculation_results_filename2 + ':') + 1))
	print()
	for filename in filenames1_remaining_list:
		print(filename)
	print()
	print('Number of filenames missing =', len(filenames1_remaining_list))
	print()
	
if len(file2_dict_names_remaining) != 0:
	filenames2_remaining_list = list(file2_dict_names_remaining)
	filenames2_remaining_list.sort(key=str.lower)
	print(str(len(filenames2_remaining_list)) + ' Filenames not found in', calculation_results_filename1 + ':')
	print('-' * (len(str(len(filenames2_remaining_list)) + ' Filenames not found in' + calculation_results_filename1 + ':') + 1))
	print()
	for filename in filenames2_remaining_list:
		print(filename)
	print()
	print('Number of filenames missing =', len(filenames2_remaining_list))
	print()

if (len(file1_dict_names_remaining) == 0) and (len(file2_dict_names_remaining) == 0):
	print()
	print('Both files have identical filenames :)')

print()
print()
