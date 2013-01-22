#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#

# This program reads a 'debug-file_processing_info.pickle' the and displays all values in it.

import pickle
import sys
import os

# Read the config variables from a file. The file contains a dictionary with the needed values.
file_path = ''

if len(sys.argv) > 1:
	file_path = sys.argv[1]

if file_path == '':
	print()
	print("ERROR: Give the path of a 'debug-file_processing_info.pickle' - file on the commandline.")
	print()
	sys.exit()

if (not os.path.exists(file_path)):
	print()
	print("ERROR: File: '" + file_path + "' cannot be found.")
	print()
	sys.exit()

file_processing_debug_info = {}

try:
	print()

	with open(file_path, 'rb') as file_handler:
		file_processing_debug_info = pickle.load(file_handler)

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


#######################################
# Print info read from the dictionary #
#######################################

if len(file_processing_debug_info) != 0:

	
	print('\033[7m' + '################################################################################################################################'  + '\033[0m')
	print()

	for item in file_processing_debug_info:
		
		print('Filename:', item)
		print('------------------------------------------------------------------------------------------------------')
		print()
		
		debug_list_for_one_file = file_processing_debug_info[item]
		
		for counter in range(0, len(debug_list_for_one_file), 2):
			item_1 = str(debug_list_for_one_file[counter])
			item_2 = str(debug_list_for_one_file[counter + 1])
			if item_1 == 'Start Time':
				item_2 = item_2 + '\n'
			if item_1 == 'Stop Time':
				item_1 = '\n' + item_1
				item_2 = item_2 + '\n'
			if item_1 == 'Stream Filename':
				item_1 = '\n\t' + item_1
				item_2 = item_2 + '\n'
			if (item_1 != 'Start Time') and (item_1 != 'Stop Time'):
				item_1 = '\t' + item_1
			if ('Subprocess Name'not in item_1) and (item_1 != 'Start Time') and (item_1 != 'Stop Time'):
				item_1 = '\t' + item_1
			if ('error message' in item_1.lower().replace('_',' ')) and (item_2 != ''):
				item_2 = '\033[7m' + item_2  + '\033[0m'
			print(item_1, '=', item_2)
		print()
	print()

