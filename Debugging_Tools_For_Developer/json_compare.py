#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Mikael Hartzell 2026

import sys
import os
import json
import copy

def print_instructions_on_program_usage():

	print()
	print('This program can compare variables im two json - files.')
	print()
	print('Usage: ', sys.argv[0], 'file_1.json    file_2.json')
	print()
	sys.exit()

# Check if command line parameters are sane.
if len(sys.argv) < 3:
	print_instructions_on_program_usage()

if os.path.isfile(sys.argv[1]) != True:
	print('File', sys.argv[1], 'does not exist')
	sys.exit()

if os.path.isfile(sys.argv[2]) != True:
	print('File', sys.argv[2], 'does not exist')
	sys.exit()

file_1 = sys.argv[1]
file_2 = sys.argv[2]

file_1_dict = []
file_2_dict = []

# Read the first input file
try:

	if (os.path.exists(file_1)):

		with open(file_1, 'r') as file_handler:
			file_1_dict = json.load(file_handler)

except KeyboardInterrupt:
	print('\n\nUser cancelled operation.\n')
	sys.exit(0)
except IOError as reason_for_error:
	print('Error reading file: ', file_1, str(reason_for_error))
	sys.exit(1)
except OSError as reason_for_error:
	print('Error reading file: ', file_1, str(reason_for_error))
	sys.exit(1)
except EOFError as reason_for_error:
	print('Error reading file: ', file_1, str(reason_for_error))
	sys.exit(1)

# Read the second input file
try:

	if (os.path.exists(file_2)):

		with open(file_2, 'r') as file_handler:
			file_2_dict = json.load(file_handler)

except KeyboardInterrupt:
	print('\n\nUser cancelled operation.\n')
	sys.exit(0)
except IOError as reason_for_error:
	print('Error reading file: ', file_2, str(reason_for_error))
	sys.exit(1)
except OSError as reason_for_error:
	print('Error reading file: ', file_2, str(reason_for_error))
	sys.exit(1)
except EOFError as reason_for_error:
	print('Error reading file: ', file_2, str(reason_for_error))
	sys.exit(1)

file_1_dict_copy = copy.deepcopy(file_1_dict)
file_2_dict_copy = copy.deepcopy(file_2_dict)

print()
print("Different values in", file_1, file_2)
print("-----------------------------------------------------------------------------")

for key in sorted(file_1_dict_copy.keys()):

	# Check if value types are different
	if key in file_2_dict_copy:

		# If variable types differ then don't compare values
		if type(file_1_dict_copy[key]) != type(file_2_dict_copy[key]):

			print(key +": Types differ:", type(file_1_dict_copy[key]), type(file_2_dict_copy[key]))

			del file_1_dict[key]

			if key in file_2_dict:
				del file_2_dict[key]

			continue

		# Print value if they are different
		if file_1_dict_copy[key] != file_2_dict_copy[key]:
			print(key + ":", file_1_dict_copy[key], file_2_dict_copy[key])

	del file_1_dict[key]

	if key in file_2_dict:
		del file_2_dict[key]

# Print keys that were only in one dictionary
if len(file_1_dict) != 0:

	print()
	print("Keys in:", file_1, "but not in:", file_2)
	print("-----------------------------------------------------------------------------")

	for key in sorted(file_1_dict.keys()):
		print(key + ":", file_1_dict[key])

if len(file_2_dict) != 0:

	print()
	print("Keys in:", file_2, "but not in:", file_1)
	print("-----------------------------------------------------------------------------")

	for key in sorted(file_2_dict.keys()):
		print(key + ":", file_2_dict[key])

print()


