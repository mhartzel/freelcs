#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#

# LoudnessCorrection configfile reader.
# This program reads the configfile '/etc/Loudness_Correction_Settings.pickle' and displays all values in it.

import pickle
import sys

# Read the config variables from a file. The file contains a dictionary with the needed values.
configfile_path = '/etc/Loudness_Correction_Settings.pickle'

if len(sys.argv) > 1:
	configfile_path = sys.argv[1]


all_settings_dict = {}

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


print()

print('Settings read from:', configfile_path)
print((len('Settings read from: ' + configfile_path) + 1) * '-')

for item in sorted(all_settings_dict.items()):

	if item[0] == 'unit_separator':

		print('unit_separator (in ascii) = ', end = '')
		variable_string = item[1]
		characters_in_ascii = '' 

		for item in variable_string:
			characters_in_ascii = characters_in_ascii + str(ord(item)) + ', ' 
		characters_in_ascii = characters_in_ascii[0:len(characters_in_ascii)-2]
		print(characters_in_ascii)

		continue

	if item[0] == 'record_separator':

		print('record_separator (in ascii) = ', end = '')
		variable_string = item[1]
		characters_in_ascii = '' 

		for item in variable_string:
			characters_in_ascii = characters_in_ascii + str(ord(item)) + ', ' 
		characters_in_ascii = characters_in_ascii[0:len(characters_in_ascii)-2]
		print(characters_in_ascii)

		continue

	print(item[0], '=', item[1])

print()
