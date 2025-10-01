#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Mikael Hartzell 2025.
#
# This program is distributed under the GNU General Public License, version 3 (GPLv3)
#

import os
import sys
import json
import pickle

configfile_path = ''
configfile_path = sys.argv[1]

if configfile_path == '':
	print ("Give configfile path on the commandline")
	sys.exit(0)

all_settings_dict = {}
configfile_path_json = os.path.splitext(os.path.splitext(configfile_path)) + ".json"
configfile_path_pickle = os.path.splitext(os.path.splitext(configfile_path)) + ".pickle"

# Read the config variables from a file. The file contains a dictionary with the needed values.
try:
	with open(configfile_path_pickle, 'rb') as configfile_handler:
		all_settings_dict = pickle.load(configfile_handler)
except KeyboardInterrupt:
	print('\n\nUser cancelled operation.\n')
	sys.exit(0)
except IOError as reason_for_error:
	print ('Error reading configfile: ' + str(reason_for_error))
	sys.exit(1)
except OSError as reason_for_error:
	print ('Error reading configfile: ' + str(reason_for_error))
	sys.exit(1)
except EOFError as reason_for_error:
	print ('Error reading configfile: ' + str(reason_for_error))
	sys.exit(1)

# Write config - values as a json file
try:
	with open(configfile_path_json, 'w') as json_configfile_handler:
		json.dump(all_settings_dict, json_configfile_handler)
		json_configfile_handler.flush() # Flushes written data to os cache
		os.fsync(json_configfile_handler.fileno()) # Flushes os cache to disk

except KeyboardInterrupt:
	print('\n\nUser cancelled operation.\n')
	sys.exit(0)
except IOError as reason_for_error:
	print ('Error opening HeartBeat commandfile for writing ' + str(reason_for_error))
	sys.exit(1)
except OSError as reason_for_error:
	print ('Error opening HeartBeat commandfile for writing ' + str(reason_for_error))
	sys.exit(1)


