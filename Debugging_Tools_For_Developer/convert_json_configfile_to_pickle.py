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
configfile_path_json = str(os.path.splitext(configfile_path)[0]) + ".json"
configfile_path_pickle = str(os.path.splitext(configfile_path)[0]) + ".pickle"

# Read the config variables from a file. The file contains a dictionary with the needed values.
try:
	with open(configfile_path_json, 'r') as configfile_handler:
		all_settings_dict = json.load(configfile_handler)

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

# Write config - values as a pickle file
try:
	with open(configfile_path_pickle, 'wb') as pickle_configfile_handler:
		pickle.dump(all_settings_dict, pickle_configfile_handler)
		pickle_configfile_handler.flush() # Flushes written data to os cache
		os.fsync(pickle_configfile_handler.fileno()) # Flushes os cache to disk

except KeyboardInterrupt:
	print('\n\nUser cancelled operation.\n')
	sys.exit(0)
except IOError as reason_for_error:
	print ('Error opening HeartBeat commandfile for writing ' + str(reason_for_error))
	sys.exit(1)
except OSError as reason_for_error:
	print ('Error opening HeartBeat commandfile for writing ' + str(reason_for_error))
	sys.exit(1)


