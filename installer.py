#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Mikael Hartzell 2012
#
# This program is distributed under the GNU General Public License, version 3 (GPLv3)
#
# Check the license here: http://www.gnu.org/licenses/gpl.txt
# Basically this license gives you full freedom to do what ever you wan't with this program. You are free to use, modify, distribute it any way you like.
# The only restriction is that if you make derivate works of this program AND distribute those, the derivate works must also be licensed under GPL 3.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#

import sys
import os
import subprocess
import pickle
import tkinter
import tkinter.ttk
import tkinter.filedialog
import time
import smtplib
import email
import email.mime
import email.mime.text
import email.mime.multipart
import tempfile

version = '068'

###################################
# Function definitions start here #
###################################

def call_first_frame_on_top():
	# This function can be called only from the second window.
	# Hide the second window and show the first window.
	license_frame.grid_forget()
	second_frame.grid_forget()
	first_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

	## Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(first_frame.winfo_reqwidth()+40) +'x'+ str(first_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
	
def call_second_frame_on_top():
	# This function can be called from the first and third windows.
	# Hide the first and third windows and show the second window.
	first_frame.grid_forget()
	third_frame.grid_forget()
	second_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(second_frame.winfo_reqwidth()+40) +'x'+ str(second_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
	
def call_third_frame_on_top():
	
	# If the user comes back to this window and there is an error message displayed on the window from the last time user was here, then remove that error message.
	email_sending_message_1.set('')
	email_sending_message_2.set('')
	third_window_label_15['foreground'] = 'black'
	third_window_label_17['foreground'] = 'black'
			
	# This function can be called from two possible windows depending on did the user come here by clicking Next or Back buttons.
	# Hide the the frames for other windows and raise the one we want.
	second_frame.grid_forget()
	fourth_frame.grid_forget()
	third_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(third_frame.winfo_reqwidth()+40) +'x'+ str(third_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

def call_fourth_frame_on_top():
	
	# If user clicked 'Send error messages by email' to True, then test if he has filled all needed email details and only allow him to advance to the next window is all settings are ok.
	if send_error_messages_by_email.get() == True:
		put_email_details_in_a_dictionary()
		email_settings_are_complete, error_message = test_if_email_settings_are_complete()
		if email_settings_are_complete == False:
			email_sending_message_1.set('Email settings are incomplete:')
			email_sending_message_2.set(error_message)
			third_window_label_15['foreground'] = 'red'
			third_window_label_17['foreground'] = 'red'
			return
	
	# This function can be called from two possible windows depending on did the user come here by clicking Next or Back buttons.
	# Hide the the frames for other windows and raise the one we want.
	third_frame.grid_forget()
	fifth_frame.grid_forget()
	fourth_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(fourth_frame.winfo_reqwidth()+40) +'x'+ str(fourth_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

def call_fifth_frame_on_top():
	# This function can be called from two possible windows depending on did the user come here by clicking Next or Back buttons.
	# Hide the the frames for other windows and raise the one we want.
	fourth_frame.grid_forget()
	sixth_frame.grid_forget()
	fifth_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(fifth_frame.winfo_reqwidth()+40) +'x'+ str(fifth_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

def call_sixth_frame_on_top():
	
	# The user may have navigated back and forth between windows and the sixth window may be incorrectly sized by an previous error message.
	# Remove the error message and update window dimensions.
	root_password_was_not_accepted_message.set('') # Remove a possible error message from the screen that remained when the user previously visited this window.
	sixth_frame.update() # Update the frame dimesions.	
	
	# If the user comes back here from window 7, empty window 7 error messages, the user will propably go back to window seven from here.
	seventh_window_label_16['foreground'] = 'dark green'
	seventh_window_label_17['foreground'] = 'dark green'
	seventh_window_message_1.set('')
	seventh_window_message_2.set('')
	
	# This function can be called from two possible windows depending on did the user come here by clicking Next or Back buttons.
	# Hide the the frames for other windows and raise the one we want.
	
	# Read samba configuration from the fifth window text label and assign configuration to a list.
	set_samba_configuration()
	fifth_frame.grid_forget()
	seventh_frame.grid_forget()
	root_password_entrybox.focus() # Set keyboard focus to the entrybox.
	sixth_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(sixth_frame.winfo_reqwidth()+40) +'x'+ str(sixth_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

def call_seventh_frame_on_top():
	
	# This function can be called from two possible windows depending on did the user come here by clicking Next or Back buttons.
	# Hide the the frames for other windows and raise the one we want.
	sixth_frame.grid_forget()
	eigth_frame.grid_forget()
	ffmpeg_frame.grid_forget()
	set_seventh_window_label_texts_and_colors()
	seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
	seventh_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

def call_eigth_frame_on_top():
	# This function can only be called from the seventh window.
	# Hide the seventh window and show the eigth window.
	seventh_frame.grid_forget()
	eigth_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(eigth_frame.winfo_reqwidth()+40) +'x'+ str(eigth_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
	
def call_ninth_frame_on_top():
	# This function can only be called from the FFmpeg infowindow.
	# Hide the FFmpeg info window and show the ninth window.
	ffmpeg_frame.grid_forget()
	startup_commands_text_widget.focus()
	ninth_frame.update()
	ninth_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(ninth_frame.winfo_reqwidth()+40) +'x'+ str(ninth_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
	
def call_ffmpeg_info_frame_on_top():
	# This function can only be called from the seventh window.
	# Hide the seventh window and show the ffmpeg info window.
	seventh_frame.grid_forget()
	ninth_frame.grid_forget()
	ffmpeg_info_window_text_widget.focus()
	ffmpeg_frame.update()
	ffmpeg_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(ffmpeg_frame.winfo_reqwidth()+40) +'x'+ str(ffmpeg_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

def call_showstopper_frame_on_top():
	# This funtions displays the showstopper window, telling user that the error we encountered stops us from continuing the program.
	first_frame.grid_forget()
	second_frame.grid_forget()
	third_frame.grid_forget()
	fourth_frame.grid_forget()
	fifth_frame.grid_forget()
	sixth_frame.grid_forget()
	seventh_frame.grid_forget()
	eigth_frame.grid_forget()
	ninth_frame.grid_forget()
	showstopper_frame.update()
	showstopper_frame.grid(column=0, row=0, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(showstopper_frame.winfo_reqwidth()+40) +'x'+ str(showstopper_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

def quit_program():
	root_window.destroy()

def add_email_addresses_to_list(*args):
	global message_recipients
	message_recipients = []
	counter = 0
	email_addresses_list = email_addresses_string.get().split(',') # Spit user given input to a list using comma as the separator.
	for item in email_addresses_list: # Strip each item of possible extra whitespace and store each item in a new list.
		counter = counter + 1
		if counter > 5:
			break
		if not len(item) == 0: # If item lenght is 0, then the item is not valid, skip it.
			message_recipients.append(item.strip())
	# Assign each item (email address) to a separate variable thet is only used to display the item on the GUI.
	if len(message_recipients) > 0:
		email_address_1.set(message_recipients[0])
	else:
		email_address_1.set('')
	if len(message_recipients) > 1:
		email_address_2.set(message_recipients[1])
	else:
		email_address_2.set('')
	if len(message_recipients) > 2:
		email_address_3.set(message_recipients[2])
	else:
		email_address_3.set('')
	if len(message_recipients) > 3:
		email_address_4.set(message_recipients[3])
	else:
		email_address_4.set('')
	if len(message_recipients) > 4:
		email_address_5.set(message_recipients[4])
	else:
		email_address_5.set('')
		
	if debug == True:
		print()
		print('message_recipients =', message_recipients)

def enable_email_settings():
	if send_error_messages_by_email.get() == True:
		use_tls_true_button.state(['!disabled'])
		use_tls_false_button.state(['!disabled'])
		smtp_server_requires_authentication_true_button.state(['!disabled'])
		smtp_server_requires_authentications_false_button.state(['!disabled'])
		smtp_server_name_combobox.state(['!disabled'])
		smtp_server_port_combobox.state(['!disabled'])
		smtp_username_entrybox.state(['!disabled'])
		smtp_password_entrybox.state(['!disabled'])
		email_sending_interval_combobox.state(['!disabled'])
		email_address_entrybox.state(['!disabled'])
		heartbeat_true_button.state(['!disabled'])
		heartbeat_false_button.state(['!disabled'])
		heartbeat.set(True)
		third_window_send_button['state'] = 'normal'
	else:
		use_tls_true_button.state(['disabled'])
		use_tls_false_button.state(['disabled'])
		smtp_server_requires_authentication_true_button.state(['disabled'])
		smtp_server_requires_authentications_false_button.state(['disabled'])
		smtp_server_name_combobox.state(['disabled'])
		smtp_server_port_combobox.state(['disabled'])
		smtp_username_entrybox.state(['disabled'])
		smtp_password_entrybox.state(['disabled'])
		email_sending_interval_combobox.state(['disabled'])
		email_address_entrybox.state(['disabled'])
		heartbeat_true_button.state(['disabled'])
		heartbeat_false_button.state(['disabled'])
		heartbeat.set(False)
		third_window_send_button['state'] = 'disabled'
		
	if debug == True:
		true_false_string = [False, True]
		print()
		print('send_error_messages_by_email =', true_false_string[send_error_messages_by_email.get()])
		print('heartbeat =', true_false_string[heartbeat.get()])

def convert_file_expiry_time_to_seconds(*args):
	global file_expiry_time
	file_expiry_time = int(file_expiry_time_in_minutes.get()) * 60
	if debug == True:
		print()
		print('file_expiry_time (seconds) =', file_expiry_time)

def get_target_directory():
	global target_path
	target_path_from_user = tkinter.filedialog.askdirectory(mustexist=True, initialdir=target_path.get())
	target_path.set(target_path_from_user)
	
	# User given target path has changed, we need to redefine all pathnames under target dir.
	set_directory_names_according_to_language()
	
	# If the path that the user selected is long, it has changed the dimensions of our frames and root window geometry is wrong.
	# We need to find out the new dinemsions of our frames and resize the root window if needed.
	second_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(second_frame.winfo_reqwidth()+40) +'x'+ str(second_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
	
def set_directory_names_according_to_language():
	
	global english
	global finnish
	
	path = target_path.get()
	
	if path == os.sep:
		path = ''
		
	directory_for_temporary_files.set(os.path.normpath(path + os.sep + '00-Loudness_Calculation_Temporary_Files'))
	
	if language.get() == 'english':
		hotfolder_name_to_use = 'LoudnessCorrection'
		english = 1
		finnish = 0
		hotfolder_path.set(os.path.normpath(path + os.sep + hotfolder_name_to_use))
		directory_for_results.set(hotfolder_path.get() + os.sep + '00-Corrected_Files')
		web_page_path.set(hotfolder_path.get() + os.sep + '00-Calculation_Queue_Information')
		web_page_name.set('00-Calculation_Queue_Information.html')
		# For display the directory names were saved in a truncated form, update names.
		hotfolder_path_truncated_for_display.set('Target Directory '  + os.sep + ' ' + hotfolder_name_to_use)
		directory_for_results_truncated_for_display.set('Target Directory ' + os.sep + ' ' + hotfolder_name_to_use + ' ' + os.sep + ' 00-Corrected_Files')
		web_page_path_truncated_for_display.set('Target Directory ' + os.sep + ' ' + hotfolder_name_to_use + ' ' + os.sep + ' 00-Calculation_Queue_Information')
	else:
		hotfolder_name_to_use = 'AanekkyysKorjaus'
		english = 0
		finnish = 1
		hotfolder_path.set(os.path.normpath(path + os.sep + hotfolder_name_to_use))
		directory_for_results.set(hotfolder_path.get() + os.sep + '00-Korjatut_Tiedostot')
		web_page_path.set(hotfolder_path.get() + os.sep + '00-Laskentajonon_Tiedot')
		web_page_name.set('00-Laskentajonon_Tiedot.html')
		# For display the directory names were saved in a truncated form, update names.
		hotfolder_path_truncated_for_display.set('Target Directory '  + os.sep + ' ' + hotfolder_name_to_use)
		directory_for_results_truncated_for_display.set('Target Directory ' + os.sep + ' ' + hotfolder_name_to_use + ' ' + os.sep + ' 00-Korjatut_Tiedostot')
		web_page_path_truncated_for_display.set('Target Directory ' + os.sep + ' ' + hotfolder_name_to_use + ' ' + os.sep + ' 00-Laskentajonon_Tiedot')
	
	directory_for_temporary_files_truncated_for_display.set('Target Directory ' + os.sep + ' 00-Loudness_Calculation_Temporary_Files')
	directory_for_error_logs.set(path + os.sep + '00-Error_Logs')
	directory_for_error_logs_truncated_for_display.set('Target Directory ' + os.sep + ' 00-Error_Logs')
	
	# Samba configuration needs to be updated also, since the path to HotFolder has changed.
	samba_configuration_file_content = ['# Samba Configuration File', \
	'', \
	'[global]', \
	'workgroup = WORKGROUP', \
	'server string = %h server (Samba, ' + hotfolder_name_to_use + ')', \
	'force create mode = 0777', \
	'unix extensions = no', \
	'log file = /var/log/samba/log.%m', \
	'max log size = 1000', \
	'syslog = 0', \
	'panic action = /usr/share/samba/panic-action %d', \
	'security = share', \
	'socket options = TCP_NODELAY', \
	'', \
	'[' + hotfolder_name_to_use + ']', \
	'comment = ' + hotfolder_name_to_use, \
	'read only = no', \
	'locking = no', \
	'path = ' + hotfolder_path.get(), \
	'guest ok = yes', \
	'browseable = yes']
	
	samba_configuration_file_content_as_a_string = '\n'.join(samba_configuration_file_content)
	
	samba_config_text_widget.delete('1.0', 'end')
	samba_config_text_widget.insert('1.0', samba_configuration_file_content_as_a_string)
	samba_config_text_widget.edit_modified(False)
	
	if debug == True:
		print()
		print('hotfolder_path =', hotfolder_path.get())
		print('directory_for_results =', directory_for_results.get())
		print('web_page_path =', web_page_path.get())
		print('directory_for_temporary_files =', directory_for_temporary_files.get())
		print('english =', english)
		print('finnish =', finnish)
		
def print_number_of_processors_cores_to_use(*args):
	if debug == True:
		print()
		print('number_of_processor_cores =', number_of_processor_cores.get())

def print_use_tls(*args):
	if debug == True:
		true_false_string = [False, True]
		print()
		print('use_tls =', true_false_string[use_tls.get()])
		
def print_smtp_server_requires_authentication(*args):
	if debug == True:
		true_false_string = [False, True]
		print()
		print('smtp_server_requires_authentication =', true_false_string[smtp_server_requires_authentication.get()])

def define_smtp_server_name(*args):
	smtp_server_name = smtp_server_name_combobox.get()
	if debug == True:
		print()
		print('smtp_server_name =', smtp_server_name)
		
def define_smtp_server_port(*args):
	smtp_server_port = smtp_server_port_combobox.get()
	if debug == True:
		print()
		print('smtp_server_port =', smtp_server_port)
		
def print_smtp_username(*args):
	if debug == True:
		print()
		print('smtp_username =', smtp_username.get())
		
def print_smtp_password(*args):
	if debug == True:
		print()
		print('smtp_password =', smtp_password.get())

def convert_email_sending_interval_to_seconds(*args):
	global email_sending_interval
	email_sending_interval = int(email_sending_interval_in_minutes.get()) * 60
	if debug == True:
		print()
		print('email_sending_interval =', email_sending_interval)

def print_heartbeat(*args):
	if debug == True:
		true_false_string = [False, True]
		print()
		print('heartbeat =', true_false_string[heartbeat.get()])

def send_test_email(*args):
	
	global message_text_string
	global email_sending_details
	global all_ip_addresses_of_the_machine
	
	message_text_string = ''
	put_email_details_in_a_dictionary()
	email_settings_are_complete, error_message = test_if_email_settings_are_complete()
	if email_settings_are_complete == False:
		email_sending_message_1.set('Email settings are incomplete:')
		email_sending_message_2.set(error_message)
		third_window_label_15['foreground'] = 'red'
		third_window_label_17['foreground'] = 'red'
		return
	if email_settings_are_complete == True:
		current_time = parse_time(time.time())
		message_text_string = '\nThis is a LoudnessCorrection test message sent ' + current_time + '.\n\nIP-Addresses of this machine are: ' + ', '.join(all_ip_addresses_of_the_machine) + '\n\n'
		email_sending_message_1.set('')
		email_sending_message_2.set('')
		third_window_label_15['foreground'] = 'black'
		third_window_label_17['foreground'] = 'black'
	
	connect_to_smtp_server()
	if email_sending_message_1.get() == 'Error sending email !!!!!!!':
		third_window_label_15['foreground'] = 'red'
		third_window_label_17['foreground'] = 'red'
	else:
		email_sending_message_1.set('Email sent successfully with the following content:')
		email_sending_message_2.set(message_text_string.strip('\n'))
		third_window_label_15['foreground'] = 'dark green'
		third_window_label_17['foreground'] = 'dark green'
	
	# The user may have misspelled some items and the error messages may have changed the dimensions of our frames and root window geometry is wrong.
	# We need to find out the new dinemsions of our frame and resize the root window if needed.
	# This also needs to be done when email sending is successful after an previous failed attempt.
	
	third_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(third_frame.winfo_reqwidth()+40) +'x'+ str(third_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
		
	if debug == True:
		print()
		print('email_sending_details =', email_sending_details)
		print('message_text_string =', message_text_string.strip('\n'))

def parse_time(time_int):
	
	# Parse time and expand one digit values to two (7 becomes 07).
	year = str(time.localtime(time_int).tm_year)
	month = str(time.localtime(time_int).tm_mon)
	day = str(time.localtime(time_int).tm_mday)
	hours = str(time.localtime(time_int).tm_hour)
	minutes = str(time.localtime(time_int).tm_min)
	seconds = str(time.localtime(time_int).tm_sec)
	# The length of each time string is either 1 or 2. Subtract the string length from number 2 and use the result to count how many zeroes needs to be before the time string.
	month = str('0' *( 2 - len(str(month))) + str(month))
	day = str('0' * (2 - len(str(day))) + str(day))
	hours = str('0' * (2 - len(str(hours))) + str(hours))
	minutes = str('0' *( 2 - len(str(minutes))) + str(minutes))
	seconds = str('0' * (2 - len(str(seconds))) + str(seconds))
	
	time_string= year + '.' + month + '.' + day + ' at ' + hours + ':' + minutes + ':' + seconds
	
	return(time_string)
	
def put_email_details_in_a_dictionary():
	
	true_false_string = [False, True]
	global email_sending_details
	global where_to_send_error_messages
	
	email_sending_details['send_error_messages_by_email'] = true_false_string[send_error_messages_by_email.get()]
	email_sending_details['use_tls'] = true_false_string[use_tls.get()]
	email_sending_details['smtp_server_requires_authentication'] = true_false_string[smtp_server_requires_authentication.get()]
	email_sending_details['smtp_server_name'] = smtp_server_name.get()
	email_sending_details['smtp_server_port'] = smtp_server_port.get()
	email_sending_details['smtp_username'] = smtp_username.get()
	email_sending_details['smtp_password'] = smtp_password.get()
	email_sending_details['message_recipients'] = message_recipients
	email_sending_details['email_sending_interval'] = email_sending_interval
	email_sending_details['message_title'] = 'LoudnessCorrection Error Message' # The title of the email message.
	
	if (true_false_string[send_error_messages_by_email.get()] == True) and ('email' not in where_to_send_error_messages):
		where_to_send_error_messages.append('email')
	
def test_if_email_settings_are_complete():
	error_message = ''
	email_settings_are_complete = True
	
	if email_sending_details['smtp_server_name'] == '':
		email_settings_are_complete = False
		error_message = 'ERROR !!!!!!! Smtp server name has not been defined.'
	if email_sending_details['smtp_server_port'] == '':
		email_settings_are_complete = False
		error_message = 'ERROR !!!!!!! Smtp server port has not been defined.'
	if email_sending_details['smtp_username'] == '':
		email_settings_are_complete = False
		error_message = 'ERROR !!!!!!! Smtp user name (email sender) has not been defined.'
	if (email_sending_details['smtp_server_requires_authentication'] == True) and (email_sending_details['smtp_password'] == ''):
		email_settings_are_complete = False
		error_message = 'ERROR !!!!!!! Password has not been defined.'
	if email_sending_details['message_recipients'] == []:
		email_settings_are_complete = False
		error_message = 'ERROR !!!!!!! No email recipients. (Remember to press ENTER to insert name)'
	return(email_settings_are_complete, error_message)

def connect_to_smtp_server():
   
	global message_text_string
	global email_sending_details
	
	message_recipients = email_sending_details['message_recipients']
	message_title = 'LoudnessCorrection Test Message'
	message_attachment_path =''
	smtp_server_name = email_sending_details['smtp_server_name']
	smtp_server_port = email_sending_details['smtp_server_port']
	use_tls = email_sending_details['use_tls']
	smtp_server_requires_authentication = email_sending_details['smtp_server_requires_authentication']
	smtp_username = email_sending_details['smtp_username']
	smtp_password = email_sending_details['smtp_password']
	
	# Compile the start of the email message.
	email_message_content = email.mime.multipart.MIMEMultipart()
	email_message_content['From'] = smtp_username
	email_message_content['To'] = ', '.join(message_recipients)
	email_message_content['Subject'] = message_title
   
	# Append the user given lines of text to the email message.
	email_message_content.attach(email.mime.text.MIMEText(message_text_string.encode('utf-8'), _charset='utf-8'))
   
	# Read attachment file, encode it and append it to the email message.
	if message_attachment_path != '': # If no attachment path is defined, do nothing.
		email_attachment_content = email.mime.base.MIMEBase('application', 'octet-stream')
		email_attachment_content.set_payload(open(message_attachment_path, 'rb').read())
		email.encoders.encode_base64(email_attachment_content)
		email_attachment_content.add_header('Content-Disposition','attachment; filename="%s"' % os.path.basename(message_attachment_path))
		email_message_content.attach(email_attachment_content)
   
	# Email message is ready, before sending it, it must be compiled  into a long string of characters.
	email_message_content_string = email_message_content.as_string()

	# Start communication with the smtp-server.
	try:
		mailServer = smtplib.SMTP(smtp_server_name, smtp_server_port, 'localhost', 15) # Timeout is set to 15 seconds.
		mailServer.ehlo()
		  
		# Check if message size is below the max limit the smpt server announced.
		message_size_is_within_limits = True # Set the default that is used if smtp-server does not annouce max message size.
		if 'size' in mailServer.esmtp_features:
			server_max_message_size = int(mailServer.esmtp_features['size']) # Get smtp server announced max message size
			message_size = len(email_message_content_string) # Get our message size
			if message_size > server_max_message_size: # Message is too large for the smtp server to accept, abort sending.
				message_size_is_within_limits = False
				email_sending_message_1.set('Error sending email !!!!!!!')
				email_sending_message_2.set('Message_size (', str(message_size), ') is larger than the max supported size (', str(server_max_message_size), ') of server:', smtp_server_name, 'Sending aborted.')
				return()
		if message_size_is_within_limits == True:
			# Uncomment the following line if you want to see printed out the final message that is sent to the smtp server
			# print('email_message_content_string =', email_message_content_string)
			if use_tls == True:
				mailServer.starttls()
				mailServer.ehlo() # After starting tls, ehlo must be done again.
			if smtp_server_requires_authentication == True:
				mailServer.login(smtp_username, smtp_password)
			mailServer.sendmail(smtp_username, message_recipients, email_message_content_string)
		mailServer.close()
		
	except smtplib.socket.timeout as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, Timeout error: ' + str(reason_for_error))
		return
	except smtplib.socket.error as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, Socket error: ' + str(reason_for_error))
		return
	except smtplib.SMTPRecipientsRefused as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, All recipients were refused: ' + str(reason_for_error))
		return
	except smtplib.SMTPHeloError as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, The server didn’t reply properly to the HELO greeting: ' + str(reason_for_error))
		return
	except smtplib.SMTPSenderRefused as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, The server didn’t accept the sender address: ' + str(reason_for_error))
		return
	except smtplib.SMTPDataError as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, The server replied with an unexpected error code or The SMTP server refused to accept the message data: ' + str(reason_for_error))
		return
	except smtplib.SMTPException as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, The server does not support the STARTTLS extension or No suitable authentication method was found: ' + str(reason_for_error))
		return
	except smtplib.SMTPAuthenticationError as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, The server didn’t accept the username/password combination: ' + str(reason_for_error))
		return
	except smtplib.SMTPConnectError as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, Error occurred during establishment of a connection with the server: ' + str(reason_for_error))
		return
	except RuntimeError as reason_for_error:
		email_sending_message_1.set('Error sending email !!!!!!!')
		email_sending_message_2.set('Error, SSL/TLS support is not available to your Python interpreter: ' + str(reason_for_error))
		return

	email_sending_message_1.set('')
	email_sending_message_2.set('')
	
def print_write_html_progress_report(*args):
	if debug == True:
		true_false_string = [False, True]
		print()
		print('write_html_progress_report =', true_false_string[write_html_progress_report.get()])

def print_create_a_ram_disk_for_html_report_and_toggle_next_button_state(*args):
	global list_of_ram_devices
	global list_of_normal_users_accounts
	
	if (len(list_of_ram_devices) == 0) and (create_a_ram_disk_for_html_report.get() == True):
		fourth_window_next_button['state'] = 'disabled'
	else:
		if len(list_of_normal_users_accounts) > 0:
			fourth_window_next_button['state'] = 'normal'
		
	if debug == True:
		true_false_string = [False, True]
		print()
		print('create_a_ram_disk_for_html_report =', true_false_string[create_a_ram_disk_for_html_report.get()])
		
def get_list_of_normal_user_accounts_from_os():
	
	# This subroutine gets the list of normal user accounts from the os.
	os_passwordfile_path = '/etc/passwd'
	one_line_of_textfile_as_list = []
	global list_of_normal_users_accounts
	error_happened = False
	error_message = ''

	try:
		with open(os_passwordfile_path, 'r') as passwordfile_handler:
			
			while True:
				one_line_of_textfile = passwordfile_handler.readline()
				if len(one_line_of_textfile) == 0: # Zero length indicates EOF
					break
				one_line_of_textfile_as_list = one_line_of_textfile.split(':')
				if (int(one_line_of_textfile_as_list[2]) >= 1000) and (one_line_of_textfile_as_list[0] != 'nobody'):
					list_of_normal_users_accounts.append(one_line_of_textfile_as_list[0])
					
	except IOError as reason_for_error:
		error_happened = True
		error_message = 'Error reading file /etc/passwd: ' + str(reason_for_error)
	except OSError as reason_for_error:
		error_happened = True
		error_message = 'Error reading /etc/passwd: ' + str(reason_for_error)
	except EOFError as reason_for_error:
		error_happened = True
		error_message = 'Error reading /etc/passwd: ' + str(reason_for_error)

	if len(list_of_normal_users_accounts) == 0:
		error_happened = True
		error_message = 'Unknown error, could not get the list of normal user accounts from the os'
		
	return(error_happened, error_message, list_of_normal_users_accounts)
	
def get_list_of_ram_devices_from_os():
	
	# This program gets the list of ram disks from the os and prints it.
	global list_of_ram_devices
	error_happened = False
	error_message = ''

	try:
		# Get directory listing for HotFolder. The 'break' statement stops the for - statement from recursing into subdirectories.
		for path, list_of_directories, list_of_files in os.walk('/dev/'):
			break
			
	except IOError as reason_for_error:
		error_happened = True
		list_of_ram_devices = ['Error !!!!!!!']
		error_message = 'Error getting list of os ram devices: ' + str(reason_for_error)
	except OSError as reason_for_error:
		error_happened = True
		list_of_ram_devices = ['Error !!!!!!!']
		error_message = 'Error getting list of os ram devices: ' + str(reason_for_error)

	if error_happened == False:
		for item in list_of_files:
			if ('ram' in item) and (int(item.strip('ram')) < 10) and (item != 'ram0'):
				list_of_ram_devices.append('/dev/' + item)

		list_of_ram_devices.sort()
	
	if len(list_of_ram_devices) == 0:
		error_happened = True
		error_message = 'Unknown error getting the list of ram devices from the os'
		
	return(error_happened, error_message, list_of_ram_devices)
	
def print_ram_device_name(*args):
	if debug == True:
		print()
		print('ram_device_name =', ram_device_name.get())
		
	return 'break'

def print_user_account(*args):
	if debug == True:
		print()
		print('user_account =', user_account.get())

def undo_text_in_text_widget(*args):
	# Test if there are any undo history left in the undo buffer.
	# If there is do an undo, otherwise prevent it,
	# Undoing beyond the last event would empty our text widget completely.
	if samba_config_text_widget.edit_modified() == 1:
		samba_config_text_widget.edit_undo()
		
	# The Ctrl+z is also bound to <Undo> event in the tkinter at system level.
	# User bound Ctrl+z events are run first and after that the system level bind is run.
	# As I have defined Ctrl+z binding in my text widget, this routine is run first.
	# The following return 'break' prevents Tkinter from running any other Ctrl+z bindings.
	# Without this return 'break' line an Ctrl+z would undo text in the text widget until the widget would be completely empty.
	return 'break'

def set_samba_configuration(*args):
	global samba_configuration_file_content
	samba_configuration_file_content = samba_config_text_widget.get('1.0', 'end').split('\n')
		
	if debug == True:
		print()
		for item in samba_configuration_file_content:
			 print (item)

def print_root_password(*args):
	if debug == True:
		print()
		print('root_password =', root_password.get())

def print_use_samba_variable_and_toggle_text_widget(*args):
	
	true_false_string = [False, True]
	
	if use_samba.get() == True:
		samba_config_text_widget['state'] = 'normal'
		samba_config_text_widget['background'] = 'white'
		samba_config_text_widget['foreground'] = 'black'
		first_window_undo_button['state'] = 'normal'

		# If there is no apt-get install command for samba, then add it to the package installation list.
		if 'samba' not in needed_packages_install_commands:
			needed_packages_install_commands.append('samba') 
	else:
		samba_config_text_widget['state'] = 'disabled'
		samba_config_text_widget['background'] = 'light gray'
		samba_config_text_widget['foreground'] = 'gray'
		first_window_undo_button['state'] = 'disabled'

		# If there is a apt-get install command for samba, then remove it from the package installation list.
		if 'samba' in needed_packages_install_commands:
			needed_packages_install_commands.remove('samba') 

	samba_config_text_widget.update()
	if debug == True:
		print()
		print('use_samba =', true_false_string[use_samba.get()])
		
def install_init_scripts_and_config_files(*args):
	
	# Create init scripts and gather all varible values that the LoudnessCorrection scripts need and save config data to file '/etc/Loudness_Correction_Settings.pickle'.
	# Copy LoudessCorrection.py and HeartBeat_Checker.py to /usr/bin
	# Write possible samba configuration file to /etc/samba/smb.conf
	# Write an init script that:
	#----------------------------
	# Creates an ram disk if user requested it.
	# Creates the needed directory structure in the HotFolder
	# Changes directory permissions so that users that use the server through network can not delete important files and directories
	# Starts up LoudnessCorrection.py and possibly HeartBeat_Checker.py
	
	global loudness_correction_init_script_content
	global ram_disk_mount_commands
	global python3_path
	global samba_configuration_file_content
	global configfile_path
	
	#############################################################################################
	# Create the init script that is going to start LoudnessCorrection when the computer starts #
	#############################################################################################
	
	# Gather init script commands in a list.
	loudness_correction_init_script_content_part_1 = ['#!/bin/sh', \
	'', \
	'### BEGIN INIT INFO', \
	'# Provides:          LoudnessCorrection', \
	'# Required-Start:    $all', \
	'# Required-Stop:', \
	'# Default-Start:     2', \
	'# Default-Stop:      0 1 6', \
	'# Short-Description: FreeLCS init script', \
	'# Description:       FreeLCS init script', \
	'### END INIT INFO', \
	'', \
	'USERNAME="' + user_account.get() + '"', \
	'TARGET_PATH="' + target_path.get() + '"', \
	'HOTFOLDER_NAME="' + os.path.basename(hotfolder_path.get()) + '"', \
	'WEB_PAGE_PATH="' + os.path.basename(web_page_path.get()) + '"', \
	'DIRECTORY_FOR_RESULTS="' + directory_for_results.get() + '"', \
	'PYTHON3_PATH="' + python3_path + '"', \
	'LOUDNESSCORRECTION_SCRIPT_PATH="/usr/bin/LoudnessCorrection.py"', \
	'HEARTBEAT_PATH="/usr/bin/HeartBeat_Checker.py"', \
	'RAM_DEVICE_NAME="'+ ram_device_name.get() + '"', \
	'CONFIGFILE_PATH="' + configfile_path + '"', \
	'', \
	'#############################################################################################', \
	'# Send output to logfile.', \
	'#############################################################################################', \
	'', \
	'exec >> /var/log/LoudnessCorrection.log 2>&1', \
	"# set -x   # Uncomment this if you want every command in this script written to the logfile.", \
	'', \
	'if [ "$1" = "stop" ] || [ "$1" = "restart"  ] ; then', \
	'', \
	'		#############################################################################################', \
	'		#                   Stop LoudnessCorrection.py and HeartBeat_Checker.py                     #', \
	'		#############################################################################################', \
	'', \
	'		echo `date`": Shutting down LoudnessCorrection and HeartBeat_Checker"', \
	'', \
	'		# Get LoudnessCorrection and HeartBEat_Checker PIDs', \
	'		LOUDNESSCORRECTION_PID=`pgrep -f "$PYTHON3_PATH $LOUDNESSCORRECTION_SCRIPT_PATH -configfile $CONFIGFILE_PATH"`', \
	'		HEARTBEATCHECKER_PID=`pgrep -f "$PYTHON3_PATH $HEARTBEAT_PATH -configfile $CONFIGFILE_PATH"`', \
	'', \
	'		if [ "$LOUDNESSCORRECTION_PID" != ""  ] ; then', \
	'			kill -HUP $LOUDNESSCORRECTION_PID', \
	'		fi', \
	'', \
	'		if [ "$HEARTBEATCHECKER_PID" != ""  ] ; then', \
	'			kill -HUP $HEARTBEATCHECKER_PID', \
	'		fi', \
	'', \
	'fi', \
	'', \
	'if [ "$1" = "start" ] || [ "$1" = "restart"  ] ; then', \
	'', \
	'		#############################################################################################', \
	'		# Wait for the os startup process to finish, so that all services are available', \
	'		#############################################################################################', \
	'', \
	'		sleep 90', \
	'', \
	'		#############################################################################################', \
	'		# Create directories needed by the LoudnessCorrection.py - script.', \
	'		#############################################################################################', \
	'', \
	'		mkdir -p "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH/"', \
	'		mkdir -p "$DIRECTORY_FOR_RESULTS"', \
	'		mkdir -p "$TARGET_PATH/00-Error_Logs"', \
	'		mkdir -p "$TARGET_PATH/00-Loudness_Calculation_Temporary_Files"', \
	'']


	ram_disk_mount_commands = ['		#############################################################################################', \
	'		# Create a Ram-Disk and mount it. LoudnessCorrecion.py writes the html-page on the ram disk,', \
	'		# because it speeds up html updating when the machine is under heavy load.', \
	'		#############################################################################################', \
	'', \
	'		chown -R $USERNAME:$USERNAME "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH"', \
	'		chmod -R 1755 "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH"', \
	'', \
	'		mke2fs -q -m 0 $RAM_DEVICE_NAME 1024', \
	'		mount $RAM_DEVICE_NAME "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH"', \
	'']


	loudness_correction_init_script_content_part_2_with_heartbeat = [
	'		#############################################################################################', \
	'		# Change directory ownerships and permissions so that network users can not delete important', \
	'		# files and directories.', \
	'		# Remove files that were possibly left in the temp - directory.', \
	'		#############################################################################################', \
	'', \
	'		mkdir -p "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH/.temporary_files"', \
	'		chown -R $USERNAME:$USERNAME "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH"', \
	'		chmod -R 1755 "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH"', \
	'', \
	'		chown $USERNAME:$USERNAME "$TARGET_PATH"', \
	'		chmod 1777 "$TARGET_PATH"', \
	'', \
	'		chown -R $USERNAME:$USERNAME "$TARGET_PATH/00-Error_Logs"', \
	'		chmod 1744 "$TARGET_PATH/00-Error_Logs"', \
	'', \
	'		chown -R $USERNAME:$USERNAME "$TARGET_PATH/00-Loudness_Calculation_Temporary_Files"', \
	'		chmod 1744 "$TARGET_PATH/00-Loudness_Calculation_Temporary_Files"', \
	'		find "$TARGET_PATH/00-Loudness_Calculation_Temporary_Files/"  -type f -exec rm -f {} \\;', \
	'', \
	'		chown $USERNAME:$USERNAME "$TARGET_PATH/$HOTFOLDER_NAME"', \
	'		chmod 1777 "$TARGET_PATH/$HOTFOLDER_NAME"', \
	'', \
	'		chown $USERNAME:$USERNAME "$DIRECTORY_FOR_RESULTS"', \
	'		chmod 1777 "$DIRECTORY_FOR_RESULTS"', \
	'', \
	'		#############################################################################################', \
	'		# Run LoudnessCorrection and HeartBeat - scripts as a normal user without root privileges.', \
	'		# Wait for the LoudnessCorrection process to get going before starting HeartBeat monitoring.', \
	'		#############################################################################################', \
	'', \
	'		su $USERNAME -c "$PYTHON3_PATH $LOUDNESSCORRECTION_SCRIPT_PATH -configfile $CONFIGFILE_PATH &"', \
	'', \
	'		echo `date`": LoudnessCorrection Started, Pid: "`pgrep -f "$PYTHON3_PATH $LOUDNESSCORRECTION_SCRIPT_PATH -configfile $CONFIGFILE_PATH"`', \
	'', \
	'		sleep 60', \
	'', \
	'		su $USERNAME -c "$PYTHON3_PATH $HEARTBEAT_PATH -configfile $CONFIGFILE_PATH &"', \
	'', \
	'		echo `date`": HeartBeat_Checker Started, Pid: "`pgrep -f "$PYTHON3_PATH $HEARTBEAT_PATH -configfile $CONFIGFILE_PATH"`', \
	'', \
	'fi', \
	'']


	loudness_correction_init_script_content_part_2_without_heartbeat = ['		#############################################################################################', \
	'		# Change directory ownerships and permissions so that network users can not delete important', \
	'		# files and directories.', \
	'		# Remove files that were possibly left in the temp - directory.', \
	'		#############################################################################################', \
	'', \
	'		mkdir -p "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH/.temporary_files"', \
	'		chown -R $USERNAME:$USERNAME "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH"', \
	'		chmod -R 1755 "$TARGET_PATH/$HOTFOLDER_NAME/$WEB_PAGE_PATH"', \
	'', \
	'		chown $USERNAME:$USERNAME "$TARGET_PATH"', \
	'		chmod 1777 "$TARGET_PATH"', \
	'', \
	'		chown -R $USERNAME:$USERNAME "$TARGET_PATH/00-Error_Logs"', \
	'		chmod 1744 "$TARGET_PATH/00-Error_Logs"', \
	'', \
	'		chown -R $USERNAME:$USERNAME "$TARGET_PATH/00-Loudness_Calculation_Temporary_Files"', \
	'		chmod 1744 "$TARGET_PATH/00-Loudness_Calculation_Temporary_Files"', \
	'		find "$TARGET_PATH/00-Loudness_Calculation_Temporary_Files/"  -type f -exec rm -f {} \\;', \
	'', \
	'		chown $USERNAME:$USERNAME "$TARGET_PATH/$HOTFOLDER_NAME"', \
	'		chmod 1777 "$TARGET_PATH/$HOTFOLDER_NAME"', \
	'', \
	'		chown $USERNAME:$USERNAME "$DIRECTORY_FOR_RESULTS"', \
	'		chmod 1777 "$DIRECTORY_FOR_RESULTS"', \
	'', \
	'		#############################################################################################', \
	'		# Run LoudnessCorrection and HeartBeat - scripts as a normal user without root privileges.', \
	'		# Wait for the LoudnessCorrection process to get going before starting HeartBeat monitoring.', \
	'		#############################################################################################', \
	'', \
	'		su $USERNAME -c "$PYTHON3_PATH $LOUDNESSCORRECTION_SCRIPT_PATH -configfile $CONFIGFILE_PATH &"', \
	'', \
	'		echo `date`": LoudnessCorrection Started, Pid: "`pgrep -f "$PYTHON3_PATH $LOUDNESSCORRECTION_SCRIPT_PATH -configfile $CONFIGFILE_PATH"`', \
	'', \
	'fi', \
	'']

	# Compile init script to one list from separate lists.
	# Add first part of the init script commands.
	loudness_correction_init_script_content = loudness_correction_init_script_content_part_1
	# If the user wants us to create a ram - disk, then add code in the init script to do it.
	if create_a_ram_disk_for_html_report.get() == True:
		loudness_correction_init_script_content.extend(ram_disk_mount_commands)
	# Add last part of the init script commands with or without HeartBeat_Checker commands depending whether user requested HeartBeat Checker or not.
	if heartbeat.get() == True:
		loudness_correction_init_script_content.extend(loudness_correction_init_script_content_part_2_with_heartbeat)
	else:
		loudness_correction_init_script_content.extend(loudness_correction_init_script_content_part_2_without_heartbeat)

	if debug == True:
		for line in loudness_correction_init_script_content:
			print(line)
	
	########################################################################################################################################
	# Put all variables that LoudnessCorrecion - sripts need to run into a dictionary, that is going to be saved on disk as the configfile #
	########################################################################################################################################

	true_false_string = [False, True]
	global english
	global finnish
	global delay_between_directory_reads
	global file_expiry_time
	global natively_supported_file_formats
	global loudness_path
	global ffmpeg_output_format
	global silent
	global html_progress_report_write_interval
	global send_error_messages_to_logfile
	global heartbeat_file_name
	global heartbeat_write_interval
	global email_sending_details
	global version
	global sox_path
	global gnuplot_path
	global all_ip_addresses_of_the_machine
	global peak_measurement_method
	
	put_email_details_in_a_dictionary()

	all_settings_dict = { 'language' : language.get(), 'english' : english, 'finnish' : finnish, 'target_path' : target_path.get(), 'hotfolder_path' : hotfolder_path.get(), \
	'directory_for_temporary_files' : directory_for_temporary_files.get(), 'directory_for_results' : directory_for_results.get(), 'delay_between_directory_reads' : int(delay_between_directory_reads), \
	'number_of_processor_cores' : int(number_of_processor_cores.get()), 'file_expiry_time' : int(file_expiry_time), 'natively_supported_file_formats' : natively_supported_file_formats, \
	'libebur128_path' : loudness_path, 'ffmpeg_output_format' : ffmpeg_output_format, 'silent' : silent, 'write_html_progress_report' : true_false_string[write_html_progress_report.get()], \
	'html_progress_report_write_interval' : int(html_progress_report_write_interval), 'web_page_name' : web_page_name.get(), 'web_page_path' : web_page_path.get(), \
	'directory_for_error_logs' : directory_for_error_logs.get(), 'send_error_messages_to_logfile' : send_error_messages_to_logfile, 'heartbeat' : true_false_string[heartbeat.get()], \
	'heartbeat_file_name' : heartbeat_file_name, 'heartbeat_write_interval' : int(heartbeat_write_interval), 'email_sending_details' : email_sending_details, \
	'send_error_messages_by_email' : true_false_string[send_error_messages_by_email.get()], 'where_to_send_error_messages' : where_to_send_error_messages, \
	'config_file_created_by_installer_version' : version, 'peak_measurement_method' : peak_measurement_method }

	# Get the total number of items in settings dictionary and save the number in the dictionary. The number can be used for degugging settings.
	number_of_all_items_in_dictionary = len(all_settings_dict)
	all_settings_dict['number_of_all_items_in_dictionary'] = number_of_all_items_in_dictionary

	if debug == True:
		# Print variables.
		title_text = '\nConfiguration variables written to ' + configfile_path + ' are:'
		
		print()
		print(title_text)
		print((len(title_text) + 1) * '-' + '\n') # Print a line exactly the length of the title text line + 1.
		print('language =', all_settings_dict['language'])
		print('english =', all_settings_dict['english'])
		print('finnish =', all_settings_dict['finnish'])
		print()	
		print('target_path =', all_settings_dict['target_path'])
		print('hotfolder_path =', all_settings_dict['hotfolder_path'])
		print('directory_for_temporary_files =', all_settings_dict['directory_for_temporary_files'])
		print('directory_for_results =', all_settings_dict['directory_for_results'])
		print('libebur128_path =', all_settings_dict['libebur128_path'])
		print()
		print('delay_between_directory_reads =', all_settings_dict['delay_between_directory_reads'])	
		print('number_of_processor_cores =', all_settings_dict['number_of_processor_cores'])
		print('file_expiry_time =', all_settings_dict['file_expiry_time'])
		print()
		print('natively_supported_file_formats =', all_settings_dict['natively_supported_file_formats'])
		print('ffmpeg_output_format =', all_settings_dict['ffmpeg_output_format'])
		print('peak_measurement_method =', all_settings_dict['peak_measurement_method'])
		print()	
		print('silent =', all_settings_dict['silent'])
		print()	
		print('write_html_progress_report =', all_settings_dict['write_html_progress_report'])
		print('html_progress_report_write_interval =', all_settings_dict['html_progress_report_write_interval'])
		print('web_page_name =', all_settings_dict['web_page_name'])
		print('web_page_path =', all_settings_dict['web_page_path'])
		print()
		print('heartbeat =', all_settings_dict['heartbeat'])
		print('heartbeat_file_name =', all_settings_dict['heartbeat_file_name'])
		print('heartbeat_write_interval =', all_settings_dict['heartbeat_write_interval'])
		print()
		print('where_to_send_error_messages =', all_settings_dict['where_to_send_error_messages'])
		print('send_error_messages_to_logfile =', all_settings_dict['send_error_messages_to_logfile'])
		print('directory_for_error_logs =', all_settings_dict['directory_for_error_logs'])
		print()
		print('send_error_messages_by_email =', all_settings_dict['send_error_messages_by_email'])
		print('email_sending_details =', all_settings_dict['email_sending_details'])
		print()
		print('number_of_all_items_in_dictionary =', all_settings_dict['number_of_all_items_in_dictionary'])
		print()
		print('config_file_created_by_installer_version =', all_settings_dict['config_file_created_by_installer_version'])
		print()

	##############################################################################
	# Copy scripts and write init scripts and config files to system directories #
	##############################################################################

	global path_to_loudnesscorrection
	global path_to_heartbeat_checker

	password = root_password.get()  + '\n' # Add a carriage return after the root password
	password = password.encode('utf-8') # Convert password from string to binary format.
	# Sudo switches are:
	# -k = Forget authentication immediately after command.
	# -p = Use a custom string to prompt the user for the password (we use an empty string here).
	# -S = Read password from stdin.
	
	###########################################
	# Copy LoudnessCorrection.py to /usr/bin/ #
	###########################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'cp', '-f', path_to_loudnesscorrection, '/usr/bin/' + os.path.basename(path_to_loudnesscorrection)] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.

	############################################
	# Change LoudnessCorrection.py permissions #
	############################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', '/usr/bin/' + os.path.basename(path_to_loudnesscorrection)] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
	
	######################################
	# Change LoudnessCorrection.py owner #
	######################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', '/usr/bin/' + os.path.basename(path_to_loudnesscorrection)] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.	

	##########################################
	# Copy HeartBeat_Checker.py to /usr/bin/ #
	##########################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'cp', path_to_heartbeat_checker, '/usr/bin/' + os.path.basename(path_to_heartbeat_checker)] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.

	###########################################
	# Change HeartBeat_Checker.py permissions #
	###########################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', '/usr/bin/' + os.path.basename(path_to_heartbeat_checker)] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.

	#####################################
	# Change HeartBeat_Checker.py owner #
	#####################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', '/usr/bin/' + os.path.basename(path_to_heartbeat_checker)] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.	

	###############################################################################################################################
	# Write all configuration variables in the config dictionary to the config file in '/tmp/Loudness_Correction_Settings.pickle' #
	###############################################################################################################################

	global directory_for_os_temporary_files
	path_for_configfile_in_temp_directory = directory_for_os_temporary_files + os.sep + os.path.basename(configfile_path)

	try:
		with open(path_for_configfile_in_temp_directory, 'wb') as configfile_handler:
			pickle.dump(all_settings_dict, configfile_handler)
			configfile_handler.flush() # Flushes written data to os cache
			os.fsync(configfile_handler.fileno()) # Flushes os cache to disk
	except IOError as reason_for_error:
		error_in_string_format = 'Error opening configfile for writing ' + str(reason_for_error)
		show_error_message_on_seventh_window(error_in_string_format)
		return(True) # There was an error, exit this subprogram.
	except OSError as reason_for_error:
		error_in_string_format = 'Error opening configfile for writing ' + str(reason_for_error)
		show_error_message_on_seventh_window(error_in_string_format)
		return(True) # There was an error, exit this subprogram.

	#########################################################################################################################
	# Move configfile from '/tmp/Loudness_Correction_Settings.pickle' to '/etc/Loudness_Correction_Settings.pickle' as root #
	#########################################################################################################################

	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'mv', '-f', path_for_configfile_in_temp_directory, configfile_path] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
	
	#################################
	# Change configfile permissions #
	#################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '644', configfile_path] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
	
	###########################
	# Change configfile owner #
	###########################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', configfile_path] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.

	########################################################################
	# Check if user wants to share the HotFolder to the network with samba #
	########################################################################

	if use_samba.get() == True:

		#################################################################
		# Check if directory '/etc/samba' exists, if not then create it #
		#################################################################
		
		if not os.path.exists('/etc/samba'):
			commands_to_run = ['sudo', '-k', '-p', '', '-S', 'mkdir', '-p', '/etc/samba'] # Create the commandline we need to run as root.

			# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
			sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
			sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
			
			# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
			if len(sudo_stderr_string) != 0:
				show_error_message_on_seventh_window(sudo_stderr_string)
				return(True) # There was an error, exit this subprogram.
			
			# Password was accepted and our command was successfully run as root.
			root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.

			###################################
			# Change '/etc/samba' permissions #
			###################################
			
			commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', '/etc/samba'] # Create the commandline we need to run as root.

			# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
			sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
			sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
			
			# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
			if len(sudo_stderr_string) != 0:
				show_error_message_on_seventh_window(sudo_stderr_string)
				return(True) # There was an error, exit this subprogram.
			
			# Password was accepted and our command was successfully run as root.
			root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
			
			#######################################
			# Change configfile'/etc/samba' owner #
			#######################################
			
			commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', '/etc/samba'] # Create the commandline we need to run as root.

			# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
			sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
			sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
			
			# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
			if len(sudo_stderr_string) != 0:
				show_error_message_on_seventh_window(sudo_stderr_string)
				return(True) # There was an error, exit this subprogram.
			
			# Password was accepted and our command was successfully run as root.
			root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
			
		##################################################################################################################################################################
		# Check if there already is an old version of smb.conf, if found read then last modification time of file and rename it adding the modification time to the name #
		##################################################################################################################################################################
		
		if os.path.exists('/etc/samba/smb.conf'):
			old_samba_configfile_timestamp = int(os.lstat('/etc/samba/smb.conf').st_mtime)
			old_samba_configfile_timestamp_string = parse_time(old_samba_configfile_timestamp)
			old_samba_configfile_timestamp_string = old_samba_configfile_timestamp_string.replace(' at ', '__')
		
			commands_to_run = ['sudo', '-k', '-p', '', '-S', 'mv', '-f', '/etc/samba/smb.conf', '/etc/samba/smb.conf' + '_' + old_samba_configfile_timestamp_string] # Create the commandline we need to run as root.

			# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
			sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
			sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
			
			# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
			if len(sudo_stderr_string) != 0:
				show_error_message_on_seventh_window(sudo_stderr_string)
				return(True) # There was an error, exit this subprogram.
			
			# Password was accepted and our command was successfully run as root.
			root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
		
		##############################################
		# Write samba configuration to /tmp/smb.conf #
		##############################################
		
		try:
			with open(directory_for_os_temporary_files + os.sep + 'smb.conf', 'wt') as samba_configfile_handler:
				samba_configfile_handler.write('\n'.join(samba_configuration_file_content))
				samba_configfile_handler.flush() # Flushes written data to os cache
				os.fsync(samba_configfile_handler.fileno()) # Flushes os cache to disk
		except IOError as reason_for_error:
			error_in_string_format = 'Error opening Samba configfile for writing ' + str(reason_for_error)
			show_error_message_on_seventh_window(error_in_string_format)
			return(True) # There was an error, exit this subprogram.
		except OSError as reason_for_error:
			error_in_string_format = 'Error opening Samba configfile for writing ' + str(reason_for_error)
			show_error_message_on_seventh_window(error_in_string_format)
			return(True) # There was an error, exit this subprogram.
		
		###############################################################################
		# Move Samba configfile from '/tmp/smb.conf' to '/etc/samba/smb.conf' as root #
		###############################################################################
		
		commands_to_run = ['sudo', '-k', '-p', '', '-S', 'mv', '-f', directory_for_os_temporary_files + os.sep + 'smb.conf', '/etc/samba/smb.conf'] # Create the commandline we need to run as root.

		# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
		sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
		sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		
		# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
		if len(sudo_stderr_string) != 0:
			show_error_message_on_seventh_window(sudo_stderr_string)
			return(True) # There was an error, exit this subprogram.
		
		# Password was accepted and our command was successfully run as root.
		root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
		
		#######################################
		# Change Samba configfile permissions #
		#######################################
		
		commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '644', '/etc/samba/smb.conf'] # Create the commandline we need to run as root.

		# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
		sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
		sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		
		# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
		if len(sudo_stderr_string) != 0:
			show_error_message_on_seventh_window(sudo_stderr_string)
			return(True) # There was an error, exit this subprogram.
		
		# Password was accepted and our command was successfully run as root.
		root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
		
		#################################
		# Change Samba configfile owner #
		#################################
		
		commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', '/etc/samba/smb.conf'] # Create the commandline we need to run as root.

		# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
		sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
		sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		
		# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
		if len(sudo_stderr_string) != 0:
			show_error_message_on_seventh_window(sudo_stderr_string)
			return(True) # There was an error, exit this subprogram.
		
		# Password was accepted and our command was successfully run as root.
		root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
		
	##############################################################
	# Write init script to '/tmp/LoudnessCorrection-init_script' #
	##############################################################
	
	global loudnesscorrection_init_script_name
	global loudnesscorrection_init_script_path
	global loudnesscorrection_init_script_link_path
	global os_name
	
	try:
		with open(directory_for_os_temporary_files + os.sep + loudnesscorrection_init_script_name, 'wt') as init_script_file_handler:
			init_script_file_handler.write('\n'.join(loudness_correction_init_script_content))
			init_script_file_handler.flush() # Flushes written data to os cache
			os.fsync(init_script_file_handler.fileno()) # Flushes os cache to disk
	except IOError as reason_for_error:
		error_in_string_format = 'Error opening init script file for writing ' + str(reason_for_error)
		show_error_message_on_seventh_window(error_in_string_format)
		return(True) # There was an error, exit this subprogram.
	except OSError as reason_for_error:
		error_in_string_format = 'Error opening init script file for writing ' + str(reason_for_error)
		show_error_message_on_seventh_window(error_in_string_format)
		return(True) # There was an error, exit this subprogram.
	
	#######################################################################################################################
	# Move init script from '/tmp/loudnesscorrection_init_script' to '/etc/init.d/loudnesscorrection_init_script' as root #
	#######################################################################################################################

	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'mv', '-f', directory_for_os_temporary_files + os.sep + loudnesscorrection_init_script_name, loudnesscorrection_init_script_path] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
	
	##################################
	# Change init script permissions #
	##################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', loudnesscorrection_init_script_path] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
	
	############################
	# Change init script owner #
	############################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', loudnesscorrection_init_script_path] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
	
	######################################################################################################################
	# Create a link for init script in /etc/rc2.d that starts up all LoudnessCorrection scripts when the computer starts #
	######################################################################################################################

	# The link to the init script must be done differently on Ubuntu and Debian.
	# On Ubuntu we manually link the init script to /etc/rc2.d/S99loudnesscorrection_init_script
	# On Debian  we must run: insserv -d /etc/init.d/loudnesscorrection_init_script
	# insserv links the init script to   /etc/rc2.d/  and it automatically adds a number to the link name (example:  S21loudnesscorrection_init_script)

	if os_name == 'ubuntu':
		commands_to_run = ['sudo', '-k', '-p', '', '-S', 'ln', '-s', '-f', loudnesscorrection_init_script_path, loudnesscorrection_init_script_link_path] # Create the commandline we need to run as root.
	if os_name == 'debian':
		commands_to_run = ['sudo', '-k', '-p', '', '-S', 'insserv', '-d', loudnesscorrection_init_script_path] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		show_error_message_on_seventh_window(sudo_stderr_string)
		return(True) # There was an error, exit this subprogram.
	
	# Password was accepted and our command was successfully run as root.
	root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.
	
	# Our scripts were installed successfully, update the label to tell it to the user.
	loudnesscorrection_scripts_are_installed.set('Installed')
	seventh_window_loudnesscorrection_label['foreground'] = 'dark green'
	
	return(False) # False means 'No errors happened everything was installed successfully :)'.
	
def test_if_root_password_is_valid(*args):
	
	#######################################################################################################################################
	# Test if root password is valid by copying LoudnessCorrection.py to /usr/bin and changing its permissions and owner.                 #
	# This copy is deleted from /usr/bin after the test because the file will be later be copied again with all other scripts and files.  #
	#######################################################################################################################################

	global path_to_loudnesscorrection
	target_testfile_name = '00-this_file_was_copied_here_when_FreeLCS_installer_tested_root_password_validity'
	root_password_was_accepted = True

	password = root_password.get()  + '\n' # Add a carriage return after the root password
	password = password.encode('utf-8') # Convert password from string to binary format.
	# Sudo switches are:
	# -k = Forget authentication immediately after command.
	# -p = Use a custom string to prompt the user for the password (we use an empty string here).
	# -S = Read password from stdin.
	
	###########################################
	# Copy LoudnessCorrection.py to /usr/bin/ #
	###########################################
	
	commands_to_run = ['sudo', '-k', '-p', '', '-S', 'cp', '-f', path_to_loudnesscorrection, '/usr/bin/' + target_testfile_name] # Create the commandline we need to run as root.

	# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
	sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
	sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
	
	# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
	if len(sudo_stderr_string) != 0:
		root_password_was_accepted = False
		show_error_message_on_root_password_window(sudo_stderr_string)

	############################################
	# Change LoudnessCorrection.py permissions #
	############################################
	
	if root_password_was_accepted == True:
	
		commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', '/usr/bin/' + target_testfile_name] # Create the commandline we need to run as root.

		# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
		sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
		sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		
		# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
		if len(sudo_stderr_string) != 0:
			root_password_was_accepted = False
			show_error_message_on_root_password_window(sudo_stderr_string)
		
	######################################
	# Change LoudnessCorrection.py owner #
	######################################
	
	if root_password_was_accepted == True:
	
		commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', '/usr/bin/' + target_testfile_name] # Create the commandline we need to run as root.

		# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
		sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
		sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		
		# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
		if len(sudo_stderr_string) != 0:
			root_password_was_accepted = False
			show_error_message_on_root_password_window(sudo_stderr_string)

	##############################################
	# Delete LoudnessCorrection.py from /usr/bin #
	##############################################
	
	if root_password_was_accepted == True:
	
		commands_to_run = ['sudo', '-k', '-p', '', '-S', 'rm', '-f', '/usr/bin/' + target_testfile_name] # Create the commandline we need to run as root.

		# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
		sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
		sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		
		# If sudo stderr ouput is nonempty, then an error happened, check for the cause for the error.
		if len(sudo_stderr_string) != 0:
			root_password_was_accepted = False
			show_error_message_on_root_password_window(sudo_stderr_string)

	# If root password was valid then call the next window.
	if root_password_was_accepted == True:
		# Password was accepted and our command was successfully run as root.
		root_password_was_not_accepted_message.set('') # Remove possible error message from the screen.	
		call_seventh_frame_on_top() # Call the next window.

def show_error_message_on_root_password_window(error_in_string_format):
	
	# If sudo stderror output includes string 'try again', then password was not valid.
	# Display an error message to the user. If user inputs wrong passwords many times in a row, change error messages between two messages.
	if 'try again' in error_in_string_format:
		if root_password_was_not_accepted_message.get() == 'Wrong password !!!!!!!':
			root_password_was_not_accepted_message.set('Wrong password again !!!!!!!')
		else:
			root_password_was_not_accepted_message.set('Wrong password !!!!!!!')
	else:
		# We don't know what the reason for error was, print the sudo error message on the window for the user.
		root_password_was_not_accepted_message.set('Error !!!!!!!\n\n' + error_in_string_format)
		
	# The error message may bee too long to display on the current window, resize the window again.
	sixth_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(sixth_frame.winfo_reqwidth()+40) +'x'+ str(sixth_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
	
	# Make the window 'shake head' like Apples OS X input windows do, when the input is not accepted :)
	counter = 1
	while counter < 5:
		root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position + 20)) + '+' + str(int(y_position)))
		time.sleep(0.1)
		root_window.update()
		root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
		time.sleep(0.1)
		root_window.update()
		
		counter = counter + 1

def find_program_in_os_path(program_name_to_find):

	global os_name

	# Find a program in the operating system path. Returns the full path to the program (search for python3 returns: '/usr/bin/python3').
	program_path = ''
	os_environment_list = os.environ["PATH"].split(os.pathsep)

	# In Debian we must manually add path '/usr/sbin' to the path list, since smbd is installed there.
	if os_name == 'debian':
		os_environment_list.append('/usr/sbin')

	for os_path in os_environment_list:
		true_or_false = os.path.exists(os_path + os.sep + program_name_to_find) and os.access(os_path + os.sep + program_name_to_find, os.X_OK) # True if program can be found in the path and it has executable permissions on.
		if true_or_false == True:
			program_path = os_path + os.sep + program_name_to_find
	return(program_path)

def find_program_in_current_dir(program_name_to_find):
	# Find a program in the current path. Returns the full path to the program (search for LoudnessCorrection.py returns: '/directory/LoudnessCorrection.py').
	program_path = ''
	current_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
	true_or_false = os.path.exists(current_directory + os.sep + program_name_to_find) # True if program can be found in the path.
	if true_or_false == True:
			program_path = current_directory + os.sep + program_name_to_find
	if debug == True:
			print()
			print('program_path =', program_path)
			print()
	return(program_path)

def set_seventh_window_label_texts_and_colors():

	# Set seventh window text labels and colors Seventh window tells the user if all needed programs are installed or not.
	
	global samba_path
	
	# Find paths to all critical programs we need to run LoudnessCorrection
	find_paths_to_all_external_programs_we_need()
	
	seventh_window_label_5['foreground'] = 'dark green'
	seventh_window_label_7['foreground'] = 'dark green'
	seventh_window_label_8['foreground'] = 'black'
	seventh_window_label_9['foreground'] = 'dark green'
	seventh_window_label_11['foreground'] = 'dark green'
	seventh_window_label_20['foreground'] = 'dark green'

	if sox_is_installed.get() == 'Not Installed':
		seventh_window_label_5['foreground'] = 'red'
	if gnuplot_is_installed.get() == 'Not Installed':
		seventh_window_label_7['foreground'] = 'red'		
	if use_samba.get() == False:
		samba_is_installed.set('Not Needed')
		seventh_window_label_8['foreground'] = 'dark gray'
		seventh_window_label_9['foreground'] = 'dark gray'
	if mediainfo_is_installed.get() == 'Not Installed':
		seventh_window_label_20['foreground'] = 'red'	
	if samba_is_installed.get() == 'Not Installed':
		seventh_window_label_9['foreground'] = 'red'
	if libebur128_is_installed.get() == 'Not Installed':
		seventh_window_label_11['foreground'] = 'red'

def find_paths_to_all_external_programs_we_need():

	# Find paths for all needed programs and define some tkinter variables, that are used on labels to indicate if some needed programs are installed or not.

	global python3_path
	global sox_path
	global gnuplot_path
	global samba_path
	global mediainfo_path
	global loudness_path
	global loudness_required_install_date_list
	global all_needed_external_programs_are_installed
	global force_reinstallation_of_all_programs

	all_needed_external_programs_are_installed = True
	python3_path = find_program_in_os_path('python3')
	
	sox_path = find_program_in_os_path('sox')
	check_sox_version_and_add_git_commands_to_checkout_specific_commit()
	if sox_path == '':
		sox_is_installed.set('Not Installed')
		all_needed_external_programs_are_installed = False
	else:
		sox_is_installed.set('Installed')

	gnuplot_path = find_program_in_os_path('gnuplot')
	if gnuplot_path == '':
		gnuplot_is_installed.set('Not Installed')
		all_needed_external_programs_are_installed = False
	else:
		gnuplot_is_installed.set('Installed')

	samba_path = find_program_in_os_path('smbd')
	if samba_path == '':
		samba_is_installed.set('Not Installed')
		# Check if user wants us to use samba, if not we don't care if it's installed or not.
		if use_samba.get() == True:
			all_needed_external_programs_are_installed = False
	else:
		samba_is_installed.set('Installed')
	
	mediainfo_path = find_program_in_os_path('mediainfo')
	if mediainfo_path == '':
		mediainfo_is_installed.set('Not Installed')
		all_needed_external_programs_are_installed = False
	else:
		mediainfo_is_installed.set('Installed')
	
	loudness_path = find_program_in_os_path('loudness')
	check_libebur128_version_and_add_git_commands_to_checkout_specific_commit()
	if loudness_path == '':
		libebur128_is_installed.set('Not Installed')
		all_needed_external_programs_are_installed = False
	else:
		libebur128_is_installed.set('Installed')
	
	# If user want's to reinstall all programs, then reset all path variables and force reinstallation.
	if force_reinstallation_of_all_programs == True:
		sox_path = ''
		gnuplot_path = ''
		samba_path = ''
		mediainfo_path = ''
		loudness_path = ''
		sox_is_installed.set('Not Installed')
		gnuplot_is_installed.set('Not Installed')
		
		# Check if user wants us to use samba, if not we don't care if it's installed or not.
		if use_samba.get() == True:
			samba_is_installed.set('Not Installed')
			
		mediainfo_is_installed.set('Not Installed')
		libebur128_is_installed.set('Not Installed')
		
		all_needed_external_programs_are_installed = False

def set_button_and_label_states_on_window_seven():
	
	# Set the label and button enable / disable state on window seven.
	
	global all_needed_external_programs_are_installed
	global external_program_installation_has_been_already_run
	global installation_is_running
	
	if all_needed_external_programs_are_installed == False:
		# Some needed external programs are not installed.
		# Button and text label for: install all missings programs
		seventh_window_label_14['foreground'] = 'black'
		seventh_window_install_button['state'] = 'normal'
		# Button and text label for: Show me the installation shell commands
		seventh_window_label_15['foreground'] = 'black'
		seventh_window_show_button_1['state'] = 'normal'
		# The 'Next' button for the window
		seventh_window_next_button['state'] = 'disabled'
	else:
		# All needed external programs are installed.
		# Button and text label for: install all missings programs
		seventh_window_label_14['foreground'] = 'dark gray'
		seventh_window_install_button['state'] = 'disabled'
		# Button and text label for: Show me the installation shell commands
		seventh_window_label_15['foreground'] = 'dark gray'
		seventh_window_show_button_1['state'] = 'disabled'
		# The 'Next' button for the window
		seventh_window_next_button['state'] = 'normal'

	if loudnesscorrection_scripts_are_installed.get() == 'Not Installed':
		seventh_window_label_14['foreground'] = 'black'
		seventh_window_install_button['state'] = 'normal'
		seventh_window_next_button['state'] = 'disabled'

	if external_program_installation_has_been_already_run == False:
		# Our program installation rutine has not been run yet.
		# Button and text label for: Show me the messages output during the installation
		seventh_window_label_18['foreground'] = 'dark gray'
		seventh_window_show_button_2['state'] = 'disabled'
	else:
		# Our program installation rutine has been run.
		# Button and text label for: Show me the messages output during the installation
		seventh_window_label_18['foreground'] = 'black'
		seventh_window_show_button_2['state'] = 'normal'
	
	if installation_is_running == True:
		# When installation has started disable active buttons so that the user can not accidentally start more processes.
		seventh_window_toggle_label['foreground'] = 'dark gray'
		seventh_window_toggle_button['state'] = 'disabled'
		
		seventh_window_label_14['foreground'] = 'dark gray'
		seventh_window_install_button['state'] = 'disabled'
		
		seventh_window_label_15['foreground'] = 'dark gray'
		seventh_window_show_button_1['state'] = 'disabled'
		
		seventh_window_back_button['state'] = 'disabled'

def show_installation_shell_commands(*args):
	
	# Gather all package install and configure and buils commands to a string that is displayed to the user.
	
	global eight_window_textwidget_text_content
	eight_window_textwidget_text_content = ''
	
	global all_needed_external_programs_are_installed
	global apt_get_commands
	global needed_packages_install_commands
	global sox_simplified_build_and_install_commands_displayed_to_user

	global apt_get_commands
	global libebur128_dependencies_install_commands

	global loudness_path
	global libebur128_git_commands
	global libebur128_cmake_commands
	global libebur128_make_build_and_install_commands
	
	if needed_packages_install_commands != []:
		eight_window_textwidget_text_content = '# Install missing programs.\n' + ' '.join(apt_get_commands) + ' ' + ' '.join(needed_packages_install_commands) + '\n\n'
		
	if sox_simplified_build_and_install_commands_displayed_to_user != []:
		eight_window_textwidget_text_content = eight_window_textwidget_text_content + '# Install sox from source.\n' + '\n'.join(sox_simplified_build_and_install_commands_displayed_to_user) + '\n\n'
		
	if libebur128_dependencies_install_commands != []:
		eight_window_textwidget_text_content = eight_window_textwidget_text_content + '# Install compilation tools and developer packages needed to build libebur128.\n' + ' '.join(apt_get_commands) + ' ' + ' '.join(libebur128_dependencies_install_commands) + '\n\n'
		
	if loudness_path == '':
		eight_window_textwidget_text_content = eight_window_textwidget_text_content + '# Download libebur128 source code, build it and install.\n' + '\n'.join(libebur128_git_commands) + '\n'
		eight_window_textwidget_text_content = eight_window_textwidget_text_content+ '\n'.join(libebur128_simplified_build_and_install_commands_displayed_to_user) + '\n'
		
	install_commands_text_widget.delete('1.0', 'end')
	install_commands_text_widget.insert('1.0', eight_window_textwidget_text_content)
		
	call_eigth_frame_on_top()
	
def show_installation_output_messages(*args):
	
	global eight_window_textwidget_text_content
	global all_installation_messages
	
	eight_window_textwidget_text_content = all_installation_messages
	
	install_commands_text_widget.delete('1.0', 'end')
	install_commands_text_widget.insert('1.0', eight_window_textwidget_text_content)
	
	call_eigth_frame_on_top()
	
def install_missing_programs(*args):
	
	global apt_get_commands
	global needed_packages_install_commands
	global libebur128_dependencies_install_commands
	global libebur128_git_commands
	global libebur128_cmake_commands
	global libebur128_make_build_and_install_commands
	global debug
	global external_program_installation_has_been_already_run
	global all_installation_messages
	global directory_for_os_temporary_files
	global force_reinstallation_of_all_programs
	global installation_is_running
	
	force_reinstallation_of_all_programs = False
	an_error_has_happened = False
	all_installation_messages = ''
	possible_apt_get_error_messages = ['could not get lock', 'error', 'fail', 'try again']
		
	# Disable active buttons on window seven so that user can't accidentally click them.
	installation_is_running = True
	set_button_and_label_states_on_window_seven()
	
	password = root_password.get()  + '\n' # Add a carriage return after the root password	
	password = password.encode('utf-8') # Convert password from string to binary format.
	
	if needed_packages_install_commands != []:
	
		###################################################
		# Run apt-get as root to install missing programs #
		###################################################
		
		# Create the commandline we need to run as root.
		commands_to_run = ['sudo', '-k', '-p', '', '-S']
		commands_to_run.extend(apt_get_commands)
		commands_to_run.extend(needed_packages_install_commands)

		seventh_window_label_16['foreground'] = 'dark green'
		seventh_window_label_17['foreground'] = 'dark green'
		seventh_window_message_1.set('Note: The GUI freezes while I run some external commands.\nPlease wait patiently :)')
		seventh_window_message_2.set('Installing program packages...')
		
		# Update window.
		seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
		
		# Get Frame dimensions and resize root_window to fit the whole frame.
		root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
		
		# Get root window geometry and center it on screen.
		root_window.update()
		x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
		y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
		root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
		
		# The user might come to this window again after an error message, resize the window again.
		seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
		
		# Get Frame dimensions and resize root_window to fit the whole frame.
		root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
		
		# Get root window geometry and center it on screen.
		root_window.update()
		x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
		y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
		root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
		
		if debug == True:
			print()
			print('Running commands:', commands_to_run)

		# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
		sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
		sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
		all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
		
		if debug == True:
			print()
			print('sudo_stdout:', sudo_stdout)
			print('sudo_stderr:', sudo_stderr)
		
		# Check if some error keywords can be found in apt-get output.
		for apt_error_string in possible_apt_get_error_messages:
			if apt_error_string in sudo_stderr_string.lower():
				show_error_message_on_seventh_window(sudo_stderr_string)
				an_error_has_happened = True
	
	if an_error_has_happened == False:
		
		find_paths_to_all_external_programs_we_need()
		set_button_and_label_states_on_window_seven()
		call_seventh_frame_on_top()
		
		if libebur128_dependencies_install_commands != []:
	
			#################################################################
			# Run apt-get as root to install missing libebur128 dependecies #
			#################################################################
			
			# Create the commandline we need to run as root.
			commands_to_run = ['sudo', '-k', '-p', '', '-S']
			commands_to_run.extend(apt_get_commands)
			commands_to_run.extend(libebur128_dependencies_install_commands)

			seventh_window_label_16['foreground'] = 'dark green'
			seventh_window_label_17['foreground'] = 'dark green'
			seventh_window_message_1.set('Note: The GUI freezes while I run some external commands.\nPlease wait patiently :)')
			seventh_window_message_2.set('Installing libebur128 dependencies...')
			
			# The user might come to this window again after an error message, resize the window again.
			seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
			
			# Get Frame dimensions and resize root_window to fit the whole frame.
			root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
			
			# Get root window geometry and center it on screen.
			root_window.update()
			x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
			y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
			root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
			
			if debug == True:
				print()
				print('Running commands:', commands_to_run)

			# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
			sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
			sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
			sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
			all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
			
			if debug == True:
				print()
				print('sudo_stdout:', sudo_stdout)
				print('sudo_stderr:', sudo_stderr)
			
			# Check if some error keywords can be found in apt-get output.
			for apt_error_string in possible_apt_get_error_messages:
				if apt_error_string in sudo_stderr_string.lower():
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
	if an_error_has_happened == False:
		
		find_paths_to_all_external_programs_we_need()
		set_button_and_label_states_on_window_seven()
		call_seventh_frame_on_top()
		
		if libebur128_git_commands != []:

			############################################################################################
			# Write libebur128 source code download commands to '/tmp/libebur128_download_commands.sh' #
			############################################################################################
			
			libebur128_source_downloadfile = 'libebur128_download_commands.sh'
			
			# Remove files possibly left by a previous installation.
			# If user has not rebooted the previous installation temp - files will still be there.
			
			if os.path.exists(directory_for_os_temporary_files + os.sep + libebur128_source_downloadfile):
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'rm', '-f', directory_for_os_temporary_files + os.sep + libebur128_source_downloadfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
			
			if os.path.exists(directory_for_os_temporary_files + os.sep + 'libebur128'):
				
				# Remove libebur128 source code directory tree.
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'rm', '-rf', directory_for_os_temporary_files + os.sep + 'libebur128']

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
			
			# Write libebur128 source code download commands to '/tmp/libebur128_download_commands.sh'
			try:
				with open(directory_for_os_temporary_files + os.sep + libebur128_source_downloadfile, 'wt') as libebur128_source_downloadfile_handler:
					libebur128_source_downloadfile_handler.write('#!/bin/bash\n' + '\n'.join(libebur128_git_commands))
					libebur128_source_downloadfile_handler.flush() # Flushes written data to os cache
					os.fsync(libebur128_source_downloadfile_handler.fileno()) # Flushes os cache to disk
			except IOError as reason_for_error:
				error_in_string_format = 'Error opening file ' + directory_for_os_temporary_files + os.sep + libebur128_source_downloadfile + ' for writing ' + str(reason_for_error)
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + error_in_string_format
				show_error_message_on_seventh_window(error_in_string_format)
				an_error_has_happened = True
				if debug == True:
					print()
					print('Error:', error_in_string_format)
					print()
			except OSError as reason_for_error:
				error_in_string_format = 'Error opening file ' + directory_for_os_temporary_files + os.sep + libebur128_source_downloadfile + ' for writing ' + str(reason_for_error)
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + error_in_string_format
				show_error_message_on_seventh_window(error_in_string_format)
				an_error_has_happened = True
				if debug == True:
					print()
					print('Error:', error_in_string_format)
					print()
						
			if an_error_has_happened == False:
					
				#############################################################
				# Change '/tmp/libebur128_download_commands.sh' permissions #
				#############################################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', directory_for_os_temporary_files + os.sep + libebur128_source_downloadfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
			if an_error_has_happened == False:
					
				#######################################################
				# Change '/tmp/libebur128_download_commands.sh' owner #
				#######################################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', directory_for_os_temporary_files + os.sep + libebur128_source_downloadfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
			if an_error_has_happened == False:
					
				##############################################
				# Run '/tmp/libebur128_download_commands.sh' #
				##############################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', directory_for_os_temporary_files + os.sep + libebur128_source_downloadfile]
				
				seventh_window_label_16['foreground'] = 'dark green'
				seventh_window_label_17['foreground'] = 'dark green'
				seventh_window_message_1.set('Note: The GUI freezes while I run some external commands.\nPlease wait patiently :)')
				seventh_window_message_2.set('Downloading libebur128 source code...')
				
				# The user might come to this window again after an error message, resize the window again.
				seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
				
				# Get Frame dimensions and resize root_window to fit the whole frame.
				root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
				
				# Get root window geometry and center it on screen.
				root_window.update()
				x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
				y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
				root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower() or ('cannot' in sudo_stderr_string.lower()) or ('fatal') in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
	
			if an_error_has_happened == False:
				
				find_paths_to_all_external_programs_we_need()
				set_button_and_label_states_on_window_seven()
				call_seventh_frame_on_top()

				###############################################################
				# Write cmake commands to '/tmp/libebur128_cmake_commands.sh' #
				###############################################################
				
				cmake_commandfile = 'libebur128_cmake_commands.sh'
				
				# Remove files possibly left by a previous installation.
				# If user has not rebooted the previous installation temp - files will still be there.
				
				if os.path.exists(directory_for_os_temporary_files + os.sep + cmake_commandfile):
					
					# Create the commandline we need to run as root.
					commands_to_run = ['sudo', '-k', '-p', '', '-S', 'rm', '-f', directory_for_os_temporary_files + os.sep + cmake_commandfile]

					if debug == True:
						print()
						print('Running commands:', commands_to_run)

					# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
					sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
					sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
					sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
					all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
					
					if debug == True:
						print()
						print('sudo_stdout:', sudo_stdout)
						print('sudo_stderr:', sudo_stderr)
					
					# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
					if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
						show_error_message_on_seventh_window(sudo_stderr_string)
						an_error_has_happened = True
				
				# Write cmake commands to '/tmp/libebur128_cmake_commands.sh'
				try:
					with open(directory_for_os_temporary_files + os.sep + cmake_commandfile, 'wt') as cmake_commandfile_handler:
						cmake_commandfile_handler.write('#!/bin/bash\n' + '\n'.join(libebur128_cmake_commands))
						cmake_commandfile_handler.flush() # Flushes written data to os cache
						os.fsync(cmake_commandfile_handler.fileno()) # Flushes os cache to disk
				except IOError as reason_for_error:
					error_in_string_format = 'Error opening file ' + directory_for_os_temporary_files + os.sep + cmake_commandfile + ' for writing ' + str(reason_for_error)
					all_installation_messages = all_installation_messages + '-' * 80 + '\n' + error_in_string_format
					show_error_message_on_seventh_window(error_in_string_format)
					an_error_has_happened = True
					if debug == True:
						print()
						print('Error:', error_in_string_format)
						print()
				except OSError as reason_for_error:
					error_in_string_format = 'Error opening file ' + directory_for_os_temporary_files + os.sep + cmake_commandfile + ' for writing ' + str(reason_for_error)
					all_installation_messages = all_installation_messages + '-' * 80 + '\n' + error_in_string_format
					show_error_message_on_seventh_window(error_in_string_format)
					an_error_has_happened = True
					if debug == True:
						print()
						print('Error:', error_in_string_format)
						print()
						
			if an_error_has_happened == False:
					
				##########################################################
				# Change '/tmp/libebur128_cmake_commands.sh' permissions #
				##########################################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', directory_for_os_temporary_files + os.sep + cmake_commandfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
			if an_error_has_happened == False:
					
				####################################################
				# Change '/tmp/libebur128_cmake_commands.sh' owner #
				####################################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', directory_for_os_temporary_files + os.sep + cmake_commandfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
			if an_error_has_happened == False:
					
				###########################################
				# Run '/tmp/libebur128_cmake_commands.sh' #
				###########################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', directory_for_os_temporary_files + os.sep + cmake_commandfile]
				
				seventh_window_label_16['foreground'] = 'dark green'
				seventh_window_label_17['foreground'] = 'dark green'
				seventh_window_message_1.set('Note: The GUI freezes while I run some external commands.\nPlease wait patiently :)')
				seventh_window_message_2.set('Preparing to compile libebur128 source...')
				
				# The user might come to this window again after an error message, resize the window again.
				seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
				
				# Get Frame dimensions and resize root_window to fit the whole frame.
				root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
				
				# Get root window geometry and center it on screen.
				root_window.update()
				x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
				y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
				root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
	
			if an_error_has_happened == False:
				
				find_paths_to_all_external_programs_we_need()
				set_button_and_label_states_on_window_seven()
				call_seventh_frame_on_top()

				############################################################
				# Write make commands to '/tmp/make_and_build_commands.sh' #
				############################################################
				
				make_and_build_commandfile = 'make_and_build_commands.sh'
				
				# Remove files possibly left by a previous installation.
				# If user has not rebooted the previous installation temp - files will still be there.
				
				if os.path.exists(directory_for_os_temporary_files + os.sep + make_and_build_commandfile):
					
					# Create the commandline we need to run as root.
					commands_to_run = ['sudo', '-k', '-p', '', '-S', 'rm', '-f', directory_for_os_temporary_files + os.sep + make_and_build_commandfile]

					if debug == True:
						print()
						print('Running commands:', commands_to_run)

					# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
					sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
					sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
					sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
					all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
					
					if debug == True:
						print()
						print('sudo_stdout:', sudo_stdout)
						print('sudo_stderr:', sudo_stderr)
					
					# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
					if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
						show_error_message_on_seventh_window(sudo_stderr_string)
						an_error_has_happened = True
				
				# Write make commands to '/tmp/make_and_build_commands.sh'
				try:
					with open(directory_for_os_temporary_files + os.sep + make_and_build_commandfile, 'wt') as make_and_build_commandfile_handler:
						make_and_build_commandfile_handler.write('#!/bin/bash\n' + '\n'.join(libebur128_make_build_and_install_commands))
						make_and_build_commandfile_handler.flush() # Flushes written data to os cache
						os.fsync(make_and_build_commandfile_handler.fileno()) # Flushes os cache to disk
				except IOError as reason_for_error:
					error_in_string_format = 'Error opening file ' + directory_for_os_temporary_files + os.sep + make_and_build_commandfile + ' for writing ' + str(reason_for_error)
					all_installation_messages = all_installation_messages + '-' * 80 + '\n' + error_in_string_format
					show_error_message_on_seventh_window(error_in_string_format)
					an_error_has_happened = True
					if debug == True:
						print()
						print('Error:', error_in_string_format)
						print()
				except OSError as reason_for_error:
					error_in_string_format = 'Error opening file ' + directory_for_os_temporary_files + os.sep + make_and_build_commandfile + ' for writing ' + str(reason_for_error)
					all_installation_messages = all_installation_messages + '-' * 80 + '\n' + error_in_string_format
					show_error_message_on_seventh_window(error_in_string_format)
					an_error_has_happened = True
					if debug == True:
						print()
						print('Error:', error_in_string_format)
						print()
						
			if an_error_has_happened == False:
					
				########################################################
				# Change '/tmp/make_and_build_commands.sh' permissions #
				########################################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', directory_for_os_temporary_files + os.sep + make_and_build_commandfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
			if an_error_has_happened == False:
					
				##################################################
				# Change '/tmp/make_and_build_commands.sh' owner #
				##################################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', directory_for_os_temporary_files + os.sep + make_and_build_commandfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
			if an_error_has_happened == False:
					
				#########################################
				# Run '/tmp/make_and_build_commands.sh' #
				#########################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', directory_for_os_temporary_files + os.sep + make_and_build_commandfile]
				
				seventh_window_label_16['foreground'] = 'dark green'
				seventh_window_label_17['foreground'] = 'dark green'
				seventh_window_message_1.set('Note: The GUI freezes while I run some external commands.\nPlease wait patiently :)')
				seventh_window_message_2.set('Compiling libebur128 source...')
				
				# The user might come to this window again after an error message, resize the window again.
				seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
				
				# Get Frame dimensions and resize root_window to fit the whole frame.
				root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
				
				# Get root window geometry and center it on screen.
				root_window.update()
				x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
				y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
				root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
		
	if an_error_has_happened == False:
	
		find_paths_to_all_external_programs_we_need()
		set_button_and_label_states_on_window_seven()
		call_seventh_frame_on_top()
		
		if sox_download_make_build_and_install_commands != []:

			##############################################################################
			# Write sox source code download commands to '/tmp/sox_download_commands.sh' #
			##############################################################################
			
			sox_source_downloadfile = 'sox_download_commands.sh'
			
			# Remove files possibly left by a previous installation.
			# If user has not rebooted the previous installation temp - files will still be there.
			
			if os.path.exists(directory_for_os_temporary_files + os.sep + sox_source_downloadfile):
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'rm', '-f', directory_for_os_temporary_files + os.sep + sox_source_downloadfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
			
			if os.path.exists(directory_for_os_temporary_files + os.sep + 'sox'):
				
				# Remove sox source code directory tree.
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'rm', '-rf', directory_for_os_temporary_files + os.sep + 'sox']

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
			
			# Write sox source code download commands to '/tmp/sox_download_commands.sh'
			try:
				with open(directory_for_os_temporary_files + os.sep + sox_source_downloadfile, 'wt') as sox_source_downloadfile_handler:
					sox_source_downloadfile_handler.write('#!/bin/bash\n' + '\n'.join(sox_download_make_build_and_install_commands))
					sox_source_downloadfile_handler.flush() # Flushes written data to os cache
					os.fsync(sox_source_downloadfile_handler.fileno()) # Flushes os cache to disk
			except IOError as reason_for_error:
				error_in_string_format = 'Error opening file ' + directory_for_os_temporary_files + os.sep + sox_source_downloadfile + ' for writing ' + str(reason_for_error)
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + error_in_string_format
				show_error_message_on_seventh_window(error_in_string_format)
				an_error_has_happened = True
				if debug == True:
					print()
					print('Error:', error_in_string_format)
					print()
			except OSError as reason_for_error:
				error_in_string_format = 'Error opening file ' + directory_for_os_temporary_files + os.sep + sox_source_downloadfile + ' for writing ' + str(reason_for_error)
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + error_in_string_format
				show_error_message_on_seventh_window(error_in_string_format)
				an_error_has_happened = True
				if debug == True:
					print()
					print('Error:', error_in_string_format)
					print()
						
			if an_error_has_happened == False:
					
				######################################################
				# Change '/tmp/sox_download_commands.sh' permissions #
				######################################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chmod', '755', directory_for_os_temporary_files + os.sep + sox_source_downloadfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
			if an_error_has_happened == False:
					
				#######################################################
				# Change '/tmp/sox_download_commands.sh' owner #
				#######################################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', 'chown', 'root:root', directory_for_os_temporary_files + os.sep + sox_source_downloadfile]

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower()):
					show_error_message_on_seventh_window(sudo_stderr_string)
					an_error_has_happened = True
		
			if an_error_has_happened == False:
					
				##############################################
				# Run '/tmp/sox_download_commands.sh' #
				##############################################
				
				# Create the commandline we need to run as root.
				commands_to_run = ['sudo', '-k', '-p', '', '-S', directory_for_os_temporary_files + os.sep + sox_source_downloadfile]
				
				seventh_window_label_16['foreground'] = 'dark green'
				seventh_window_label_17['foreground'] = 'dark green'
				seventh_window_message_1.set('Note: The GUI freezes while I run some external commands.\nPlease wait patiently :)')
				seventh_window_message_2.set('Downloading and installing sox from source...')
				
				# The user might come to this window again after an error message, resize the window again.
				seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
				
				# Get Frame dimensions and resize root_window to fit the whole frame.
				root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
				
				# Get root window geometry and center it on screen.
				root_window.update()
				x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
				y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
				root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

				if debug == True:
					print()
					print('Running commands:', commands_to_run)

				# Run our commands as root. The root password is piped to sudo stdin by the '.communicate(input=password)' method.
				sudo_stdout, sudo_stderr = subprocess.Popen(commands_to_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=password)
				sudo_stdout_string = str(sudo_stdout.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				sudo_stderr_string = str(sudo_stderr.decode('UTF-8')) # Convert sudo possible error output from binary to UTF-8 text.
				all_installation_messages = all_installation_messages + '-' * 80 + '\n' + sudo_stdout_string + sudo_stderr_string
				
				if debug == True:
					print()
					print('sudo_stdout:', sudo_stdout)
					print('sudo_stderr:', sudo_stderr)
				
				# Sox outputs various warnings when compiled and supressing these warnings with commandline options does not seem to work.
				# Unfortunately even though these warnings are not fatal, there are certain keywords in the warnings (like 'error') that makes it
				# impossible for us to detect if an error  has happened or not. That's why the following lines are commented.
				
				## If 'error' or 'fail' exist in std_err output then an error happened, check for the cause for the error.
				#if ('error' in sudo_stderr_string.lower()) or ('fail' in sudo_stderr_string.lower()) or ('try again' in sudo_stderr_string.lower() or ('cannot' in sudo_stderr_string.lower()) or ('fatal') in sudo_stderr_string.lower()):
					#show_error_message_on_seventh_window(sudo_stderr_string)
					#an_error_has_happened = True
		
	external_program_installation_has_been_already_run = True
	set_button_and_label_states_on_window_seven()
		
	if an_error_has_happened == False:
		
		########################################
		# Install init scripts and config file #
		########################################
		
		# Install LoudnessCorrection.py, HeartBeat_Checker.py and init scripts.
		seventh_window_label_16['foreground'] = 'dark green'
		seventh_window_label_17['foreground'] = 'dark green'
		seventh_window_message_1.set('Note: The GUI freezes while I run some external commands.\nPlease wait patiently :)')
		seventh_window_message_2.set('Installing LoudnessCorrection and init scripts...')
		
		# The user might come to this window again after an error message, resize the window again.
		seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
		
		# Get Frame dimensions and resize root_window to fit the whole frame.
		root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
		
		# Get root window geometry and center it on screen.
		root_window.update()
		x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
		y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
		root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
		
		find_paths_to_all_external_programs_we_need()
		set_button_and_label_states_on_window_seven()
		
		installing_init_scripts_and_config_files_succeeded = install_init_scripts_and_config_files()
		
		if installing_init_scripts_and_config_files_succeeded == True:
			an_error_has_happened = True
		
		find_paths_to_all_external_programs_we_need()
		set_button_and_label_states_on_window_seven()
		
	if (an_error_has_happened == False) and (all_needed_external_programs_are_installed == True) and (loudnesscorrection_scripts_are_installed.get() == 'Installed'):
		seventh_window_label_16['foreground'] = 'dark green'
		seventh_window_label_17['foreground'] = 'dark green'
		seventh_window_loudnesscorrection_label['foreground'] = 'dark green'
		seventh_window_message_1.set('Success :)')
		seventh_window_message_2.set('You can go ahead and click the NEXT button.')
		
		# The user might come to this window again after an error message, resize the window again.
		seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
		
		# Get Frame dimensions and resize root_window to fit the whole frame.
		root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
		
		# Get root window geometry and center it on screen.
		root_window.update()
		x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
		y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
		root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
	
	call_seventh_frame_on_top()

def show_error_message_on_seventh_window(error_in_string_format):
	
	# If sudo stderror output includes string 'try again', then password was not valid.
	# Display an error message to the user. If user inputs wrong passwords many times in a row, change error messages between two messages.
	
	if 'try again' in error_in_string_format:
		if seventh_window_error_message_1.get() == 'Wrong password !!!!!!!':
			seventh_window_error_message_1.set('Wrong password again !!!!!!!')
		else:
			seventh_window_error_message_1.set('Wrong password !!!!!!!')
	else:
		# We don't know what the reason for error was, print the sudo error message on the window for the user.
		seventh_window_error_message_1.set('Error !!!!!!!\n\n')
		seventh_window_error_message_2.set(error_in_string_format)
	
	# Assign message to the variable that actually displays the error message on label.
	seventh_window_message_1.set(seventh_window_error_message_1.get())
	seventh_window_message_2.set(seventh_window_error_message_2.get())
	
	# Set message color to red.
	seventh_window_label_16['foreground'] = 'red'
	seventh_window_label_17['foreground'] = 'red'
		
	# The error message may bee too long to display on the current window, resize the window again.
	seventh_frame.update() # Update the frame that has possibly changed, this triggers updating all child objects.
	
	# Get Frame dimensions and resize root_window to fit the whole frame.
	root_window.geometry(str(seventh_frame.winfo_reqwidth()+40) +'x'+ str(seventh_frame.winfo_reqheight()))
	
	# Get root window geometry and center it on screen.
	root_window.update()
	x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
	y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
	root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))
	
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

def set_sample_peak_measurement_method(*args):
	
	global peak_measurement_method
	
	if sample_peak.get() == True:
		peak_measurement_method = '--peak=sample'
	else:
		peak_measurement_method = '--peak=true'
	
	if debug == True:
		true_false_string = [False, True]
		print()
		print('sample_peak =', true_false_string[sample_peak.get()])
		print('peak_measurement_method =', peak_measurement_method)
		
def toggle_installation_status():
	
	global force_reinstallation_of_all_programs
	
	if force_reinstallation_of_all_programs == False:
		force_reinstallation_of_all_programs = True
	else:
		force_reinstallation_of_all_programs = False
		
	find_paths_to_all_external_programs_we_need()
	define_program_installation_commands()
	set_button_and_label_states_on_window_seven()
	set_seventh_window_label_texts_and_colors()
	
def define_program_installation_commands():
	
	global apt_get_commands
	global needed_packages_install_commands
	global libebur128_dependencies_install_commands
	global libebur128_git_commands
	global libebur128_dependencies_install_commands
	global directory_for_os_temporary_files
	global libebur128_cmake_commands
	global libebur128_make_build_and_install_commands
	global libebur128_simplified_build_and_install_commands_displayed_to_user
	global libebur128_repository_url

	libebur128_repository_directory_name = os.path.splitext(os.path.split(libebur128_repository_url)[1])[0]
	
	# Check if we need to install some programs that LoudnessCorrection needs and add install commands to lists.
	apt_get_commands = ['apt-get', '-q=2', '-y', '--reinstall', 'install']
	needed_packages_install_commands = []
	libebur128_dependencies_install_commands = []
	libebur128_git_commands = []

	if sox_path == '':
		needed_packages_install_commands.append('sox')
		check_sox_version_and_add_git_commands_to_checkout_specific_commit()
	if gnuplot_path == '':
		needed_packages_install_commands.append('gnuplot')
	if samba_path == '':
		needed_packages_install_commands.append('samba')
	if mediainfo_path == '':
		needed_packages_install_commands.append('mediainfo')
	if loudness_path == '':
		libebur128_dependencies_install_commands = ['build-essential', 'git', 'cmake', 'libsndfile-dev', 'libmpg123-dev', 'libmpcdec-dev', \
		'libglib2.0-dev', 'libfreetype6-dev', 'librsvg2-dev', 'libspeexdsp-dev', 'libavcodec-dev', 'libavformat-dev', 'libtag1-dev', \
		'libxml2-dev', 'libgstreamer0.10-dev', 'libgstreamer-plugins-base0.10-dev', 'libqt4-dev']
	if loudness_path == '':
		# Store commands of downloading and building libebur128 sourcecode to lists.
		libebur128_git_commands = ['cd ' + directory_for_os_temporary_files, \
		'if [ -e "' +  directory_for_os_temporary_files + os.sep + libebur128_repository_directory_name  + '" ] ; then rm -rf "' + directory_for_os_temporary_files + os.sep + libebur128_repository_directory_name  +  '" ; fi', \
		'if [ -e "' +  directory_for_os_temporary_files + os.sep + 'libebur128" ] ; then rm -rf "' + directory_for_os_temporary_files + os.sep + 'libebur128" ; fi', \
		'git clone ' + libebur128_repository_url, 
		'mv ' + libebur128_repository_directory_name + ' libebur128', \
		'cd libebur128']
		
		# Check if libebur128 is at version we need and add commands to get the version we want.
		libebur128_simplified_build_and_install_commands_displayed_to_user = ['mkdir build', 'cd build', 'cmake -DUSE_AVFORMAT=False -Wno-dev -DCMAKE_INSTALL_PREFIX:PATH=/usr ..', 'make -w', 'make install']
		check_libebur128_version_and_add_git_commands_to_checkout_specific_commit()

		libebur128_cmake_commands = ['cd ' + directory_for_os_temporary_files + '/libebur128', 'mkdir build', 'cd build', 'cmake -DUSE_AVFORMAT=False -Wno-dev -DCMAKE_INSTALL_PREFIX:PATH=/usr ..']
		libebur128_make_build_and_install_commands = ['cd ' + directory_for_os_temporary_files + '/libebur128/build', 'make -s -j 4', 'make install']


def check_libebur128_version_and_add_git_commands_to_checkout_specific_commit():
	
	global loudness_path
	global libebur128_git_commands
	global all_needed_external_programs_are_installed
	global directory_for_os_temporary_files
	global libebur128_simplified_build_and_install_commands_displayed_to_user
	global force_reinstallation_of_all_programs
	
	## Check if libebur128 'loudness' is recent enough version to be free of known bugs.
	## Since loudness is installed by compiling it from source, the timestamp of the executable tells us if we have the version we want.
	#loudness_required_installation_timestamp = int(time.mktime(time.strptime(' '.join(loudness_required_install_date_list), "%d %m %Y"))) # Convert date to seconds from epoch.
	
	## Get last modification time from program 'loudness'.
	#loudness_installation_timestamp = int(os.lstat(loudness_path).st_mtime)
	
	#if loudness_installation_timestamp < loudness_required_installation_timestamp: # 'loudness' compilation date must be at least the required date otherwise we have a known buggy version of the program.
		#loudness_path = '' # Empty value in the path-variable forces reinstallation of the 'loudness' program.
		#libebur128_is_installed.set('Not Installed')
		#all_needed_external_programs_are_installed = False
	#else:
		#libebur128_is_installed.set('Installed')
	
	# Get the path of the 'loudness' program.
	local_variable_pointing_to_loudness_executable = find_program_in_os_path('loudness')
	loudness_command_output_string = ''
	
	if local_variable_pointing_to_loudness_executable != '':
		# Run libebur128 and check if it needs 4.0 (L, R, LS, RS) and 5.0 (L, R, C, LS, RS) compatibility patch
		loudness_command_output, unused_stderr = subprocess.Popen(local_variable_pointing_to_loudness_executable, stdout=subprocess.PIPE, stdin=None, close_fds=True).communicate()
		
		# Convert libebur128 output from binary to UTF-8 text.
		loudness_command_output_string = loudness_command_output.decode('UTF-8')

	if ('Patched to disable progress bar.' in loudness_command_output_string) and (force_reinstallation_of_all_programs == False):
		libebur128_version_is_the_one_we_require = True
		libebur128_is_installed.set('Installed')
	else:
		# We get here if loudness is not installed or if it is installed but it's help text does not have the text that our 4.0 + 5.0 patch applies at the end of it.
		libebur128_version_is_the_one_we_require = False
		libebur128_is_installed.set('Not Installed')
		loudness_path = '' # Empty value in the path-variable forces reinstallation of the 'loudness' program.
		all_needed_external_programs_are_installed = False
		libebur128_simplified_build_and_install_commands_displayed_to_user = ['git checkout --force 18d1b743b27b810ebf04e012c34105a71c1620b1', 'mkdir build', 'cd build', 'cmake -DUSE_AVFORMAT=False -Wno-dev -DCMAKE_INSTALL_PREFIX:PATH=/usr ..', 'make -w', 'make install']
	
	if (libebur128_version_is_the_one_we_require == False) and (libebur128_git_commands != []):
		
		# Add 4.0 (L, R, LS, RS) and 5.0 (L, R, C, LS, RS) compatibility patching commands to git commands, but don't do it if it has already been done.
		if 'LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION="18d1b743b27b810ebf04e012c34105a71c1620b1"' not in libebur128_git_commands:
			libebur128_git_commands.extend(['', \
			'# Get the git commit number of current version of libebur128', \
			'echo', \
			'LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION="18d1b743b27b810ebf04e012c34105a71c1620b1"', \
			'LIBEBUR128_CURRENT_COMMIT=`git rev-parse HEAD`', \
			'', \
			'# If libebur128 commit number does not match, check out the correct version from git', \
			'if [ "$LIBEBUR128_CURRENT_COMMIT" == "$LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION" ] ; then', \
			'	echo "libebur128 already at the required version $LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION"', \
			'else', \
			'	echo "Checking out required version of libebur128 from git project"', \
			'	echo', \
			'	git checkout --force $LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION', \
			'	', \
			'	# Check that we have the correct version after checkout', \
			'	LIBEBUR128_CURRENT_COMMIT=`git rev-parse HEAD`', \
			'	if [ "$LIBEBUR128_CURRENT_COMMIT" == "$LIBEBUR128_REQUIRED_GIT_COMMIT_VERSION" ] ; then', \
			'		echo "Checkout was successful"', \
			'		echo', \
			'	else', \
			'		echo "There was an error when trying to check out the correct libebur128 version from the local git repository !!!!!!!"', \
			'		echo', \
			'		exit', \
			'	fi', \
			'fi', \
			'', \
			'# Write the patch data at the end of this script to libebur128 root directory', \
			'FULL_PATH_TO_SELF="' + directory_for_os_temporary_files + os.sep + 'libebur128_download_commands.sh"', \
			'FULL_PATH_TO_PATCH="' + directory_for_os_temporary_files + os.sep + 'libebur128' + os.sep + 'libebur128_scanner_4.0_and_5.0_channel_mapping_hack.diff"', \
			'tail --lines 104 "$FULL_PATH_TO_SELF" > "$FULL_PATH_TO_PATCH"', \
			'echo', \
			'', \
			'# Apply the 4.0 and 5.0 channel order patch to libebur128', \
			'OUTPUT_FROM_PATCHING=`git apply --whitespace=nowarn "$FULL_PATH_TO_PATCH" 2>&1`', \
			'', \
			'# Check if applying patch produced an error', \
			'', \
			'case "$OUTPUT_FROM_PATCHING" in', \
			'	*error*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;', \
			'	*cannot*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;', \
			'	*fatal*) echo "There was an error when applying patch to libebur128 !!!!!!!"  ; exit ;;', \
			'	*) echo "libebur128 patched successfully :)" ;;', \
			'esac', \
			'echo', \
			'', \
			'# Stop script here, the rest of this is data for the libebur128 patch file', \
			'exit', \
			'', \
			'# The libebur128 4.0 (L, R, LS, RS) and 5.0 (L, R, C, LS, RS) patch starts here', \
			'# This patch is written to its own file and applied to libebur128', \
			'', \
			'diff --git a/ebur128/ebur128.c b/ebur128/ebur128.c', \
			'index 320a6b5..f194d83 100644', \
			'--- a/ebur128/ebur128.c', \
			'+++ b/ebur128/ebur128.c', \
			'@@ -166,6 +166,17 @@ static int ebur128_init_channel_map(ebur128_state* st) {', \
			'       default: st->d->channel_map[i] = EBUR128_UNUSED;         break;', \
			'     }', \
			'   }', \
			'+  ', \
			'+  if (st->channels == 4) {', \
			'+	st->d->channel_map[2] = EBUR128_LEFT_SURROUND;', \
			'+	st->d->channel_map[3] = EBUR128_RIGHT_SURROUND;', \
			'+	}', \
			'+', \
			'+  if (st->channels == 5) {', \
			'+	st->d->channel_map[3] = EBUR128_LEFT_SURROUND;', \
			'+	st->d->channel_map[4] = EBUR128_RIGHT_SURROUND;', \
			'+	}', \
			'+', \
			'   return EBUR128_SUCCESS;', \
			' }', \
			' ', \
			'diff --git a/scanner/inputaudio/ffmpeg/input_ffmpeg.c b/scanner/inputaudio/ffmpeg/input_ffmpeg.c', \
			'index f41d0c9..f3600f8 100644', \
			'--- a/scanner/inputaudio/ffmpeg/input_ffmpeg.c', \
			'+++ b/scanner/inputaudio/ffmpeg/input_ffmpeg.c', \
			'@@ -177,6 +177,7 @@ close_file:', \
			' }', \
			' ', \
			' static int ffmpeg_set_channel_map(struct input_handle* ih, int* st) {', \
			'+  return 1;', \
			'   if (ih->codec_context->channel_layout) {', \
			'     unsigned int channel_map_index = 0;', \
			'     int bit_counter = 0;', \
			'diff --git a/scanner/inputaudio/gstreamer/input_gstreamer.c b/scanner/inputaudio/gstreamer/input_gstreamer.c', \
			'index 6f28822..9f3663e 100644', \
			'--- a/scanner/inputaudio/gstreamer/input_gstreamer.c', \
			'+++ b/scanner/inputaudio/gstreamer/input_gstreamer.c', \
			'@@ -256,6 +256,7 @@ static int gstreamer_open_file(struct input_handle* ih, const char* filename) {', \
			' }', \
			' ', \
			' static int gstreamer_set_channel_map(struct input_handle* ih, int* st) {', \
			'+  return 0;', \
			'   gint j;', \
			'   for (j = 0; j < ih->n_channels; ++j) {', \
			'     switch (ih->channel_positions[j]) {', \
			'diff --git a/scanner/inputaudio/sndfile/input_sndfile.c b/scanner/inputaudio/sndfile/input_sndfile.c', \
			'index aee098b..79e0f04 100644', \
			'--- a/scanner/inputaudio/sndfile/input_sndfile.c', \
			'+++ b/scanner/inputaudio/sndfile/input_sndfile.c', \
			'@@ -60,6 +60,7 @@ static int sndfile_open_file(struct input_handle* ih, const char* filename) {', \
			' }', \
			' ', \
			' static int sndfile_set_channel_map(struct input_handle* ih, int* st) {', \
			'+  return 1;', \
			'   int result;', \
			'   int* channel_map = (int*) calloc((size_t) ih->file_info.channels, sizeof(int));', \
			'   if (!channel_map) return 1;', \
			'diff --git a/scanner/scanner-common/scanner-common.c b/scanner/scanner-common/scanner-common.c', \
			'index 3a65db0..417dfad 100644', \
			'--- a/scanner/scanner-common/scanner-common.c', \
			'+++ b/scanner/scanner-common/scanner-common.c', \
			'@@ -331,16 +331,19 @@ void process_files(GSList *files, struct scan_opts *opts) {', \
			' ', \
			'     // Start the progress bar thread. It misuses progress_mutex and', \
			'     // progress_cond to signal when it is ready.', \
			'-    g_mutex_lock(progress_mutex);', \
			'-    progress_bar_thread = g_thread_create(print_progress_bar,', \
			'-                                          &started, TRUE, NULL);', \
			'-    while (!started)', \
			'-        g_cond_wait(progress_cond, progress_mutex);', \
			'-    g_mutex_unlock(progress_mutex);', \
			'+    //', \
			'+    // Note progress bar causes hangs sometimes and this is why progress bar is disabled when using libebur128 with FreeLCS', \
			'+    //', \
			'+    // g_mutex_lock(progress_mutex);', \
			'+    // progress_bar_thread = g_thread_create(print_progress_bar,', \
			'+    //                                       &started, TRUE, NULL);', \
			'+    // while (!started)', \
			'+    //     g_cond_wait(progress_cond, progress_mutex);', \
			'+    // g_mutex_unlock(progress_mutex);', \
			' ', \
			'     pool = g_thread_pool_new((GFunc) init_state_and_scan_work_item,', \
			'                              opts, nproc(), FALSE, NULL);', \
			'     g_slist_foreach(files, (GFunc) init_state_and_scan, pool);', \
			'     g_thread_pool_free(pool, FALSE, TRUE);', \
			'-    g_thread_join(progress_bar_thread);', \
			'+    // g_thread_join(progress_bar_thread);', \
			' }', \
			'diff --git a/scanner/scanner.c b/scanner/scanner.c', \
			'index d952f80..05fcd7e 100644', \
			'--- a/scanner/scanner.c', \
			'+++ b/scanner/scanner.c', \
			'@@ -90,6 +90,10 @@ static void print_help(void) {', \
			'     printf("  -m, --momentary=INTERVAL   print momentary loudness every INTERVAL seconds\\n");', \
			'     printf("  -s, --shortterm=INTERVAL   print shortterm loudness every INTERVAL seconds\\n");', \
			'     printf("  -i, --integrated=INTERVAL  print integrated loudness every INTERVAL seconds\\n");', \
			'+    printf("\\n");', \
			'+    printf("  Patched to support 4.0 (L, R, LS, RS) and 5.0 (L, R, C, LS, RS) files.\\n");', \
			'+    printf("  Patched to disable progress bar.\\n");', \
			'+    printf("\\n");', \
			' }', \
			' ', \
			' static gboolean recursive = FALSE;', \
			''])
	
	if debug == True:
		print()
		print('libebur128_version_is_the_one_we_require =', libebur128_version_is_the_one_we_require)
	
	return()

def check_sox_version_and_add_git_commands_to_checkout_specific_commit():
	
	global sox_download_make_build_and_install_commands
	global all_needed_external_programs_are_installed
	global directory_for_os_temporary_files
	global needed_packages_install_commands
	global sox_simplified_build_and_install_commands_displayed_to_user
	global force_reinstallation_of_all_programs
	global sox_path
	sox_version = []
	sox_command_output_string = ''
	sox_required_version = ['14', '4', '0']
	
	# Get the path of the 'sox' program.
	local_variable_pointing_to_sox_executable = find_program_in_os_path('sox')
	
	# Get version_number_of_sox.
	sox_version_is_the_one_we_require = True
	
	if local_variable_pointing_to_sox_executable != '':
		sox_command_to_run = [local_variable_pointing_to_sox_executable, '--version']
		sox_command_output, unused_stderr = subprocess.Popen(sox_command_to_run, stdout=subprocess.PIPE, stdin=None, close_fds=True).communicate()
	
		# Convert output from binary to UTF-8 text and split version number elements to a list.
		sox_command_output_string = sox_command_output.decode('UTF-8').strip()
		sox_version = sox_command_output_string.split('v')[1].split('.')
		
		# Check that we have the required version number or higher.
		for counter in range(0, len(sox_required_version)):
			if int(sox_version[counter]) < int(sox_required_version[counter]):
				sox_version_is_the_one_we_require = False
	else:
		sox_version_is_the_one_we_require = False
	
	if (sox_version_is_the_one_we_require == False) or (force_reinstallation_of_all_programs == True):
		sox_path = '' # Empty value in the path-variable forces reinstallation of the 'sox' program.
		sox_is_installed.set('Not Installed')
		all_needed_external_programs_are_installed = False
		sox_simplified_build_and_install_commands_displayed_to_user = ['git clone http://github.com/mhartzel/sox_personal_fork.git', 'cd sox_personal_fork', 'git checkout --force 6dff9411961cc8686aa75337a78b7df334606820', 'autoreconf -i', './configure --prefix=/usr', 'make -s && make install']
		
		# Remove sox from apt-get install commands since the version in repository is too old, we build a newer one from source.
		if 'sox' in needed_packages_install_commands:
			needed_packages_install_commands.remove('sox')
		
		# Check if sox build dependencies are already in apt-get install list, if not add them.
		for item in ['automake', 'autoconf', 'libtool']:
			if item not in needed_packages_install_commands:
				needed_packages_install_commands.append(item)
	else:
		# Sox is at the version we require.
		sox_is_installed.set('Installed')
	
	# Add sox source download and install commands.
	if (sox_version_is_the_one_we_require == False) and (sox_download_make_build_and_install_commands == []):
		
		sox_download_make_build_and_install_commands.extend(['', \
		'# Remove sox if it was installed from repositories since that version is too old', \
		'apt-get remove -y sox', \
		'', \
		'# Download sox source', \
		'if [ -e "' +  directory_for_os_temporary_files + os.sep + 'sox_personal_fork" ] ; then rm -rf "' + directory_for_os_temporary_files + os.sep + 'sox_personal_fork" ; fi', \
		'cd ' + directory_for_os_temporary_files, \
		'git clone http://github.com/mhartzel/sox_personal_fork.git', \
		'cd sox_personal_fork', \
		'echo', \
		'echo "Checking out required version of sox from git project"', \
		'echo', \
		'SOX_REQUIRED_GIT_COMMIT_VERSION="6dff9411961cc8686aa75337a78b7df334606820"', \
		'git checkout --force $SOX_REQUIRED_GIT_COMMIT_VERSION', \
		'', \
		'# Check that we have the correct version after checkout', \
		'SOX_CURRENT_COMMIT=`git rev-parse HEAD`', \
		'', \
		'if [ "$SOX_CURRENT_COMMIT" == "$SOX_REQUIRED_GIT_COMMIT_VERSION" ] ; then', \
		'	echo "Checkout was successful"', \
		'	echo', \
		'else', \
		'	echo "There was an error when trying to check out the correct sox version from the local git repository !!!!!!!"', \
		'	echo', \
		'	exit', \
		'fi', \
		'', \
		'# Build and install sox from source', \
		'autoreconf -i', \
		'./configure --prefix=/usr', \
		'make -s -j 4', \
		'make install', \
		''])
	
	if debug == True:
		print()
		print('sox_version_is_the_one_we_require =', sox_version_is_the_one_we_require)
	
	return()


def store_gnu_gpl3_to_a_global_variable():

	global gnu_gpl_3
	gnu_gpl_3 = "\n\
	 Free Loudness Correction Server (FreeLCS).\n\
	 Copyright (C) 2013  Mikael Hartzell, Finland.\n\
	\n\
	 This program is free software: you can redistribute it and/or modify\n\
	 it under the terms of the GNU General Public License as published by\n\
	 the Free Software Foundation version 3 of the License.\n\
	\n\
	 This program is distributed in the hope that it will be useful,\n\
	 but WITHOUT ANY WARRANTY; without even the implied warranty of\n\
	 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n\
	 GNU General Public License for more details.\n\
	\n\
	\n\
	\n\
	                     GNU GENERAL PUBLIC LICENSE\n\
			       Version 3, 29 June 2007\n\
	\n\
	 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>\n\
	 Everyone is permitted to copy and distribute verbatim copies\n\
	 of this license document, but changing it is not allowed.\n\
	\n\
				    Preamble\n\
	\n\
	  The GNU General Public License is a free, copyleft license for\n\
	software and other kinds of works.\n\
	\n\
	  The licenses for most software and other practical works are designed\n\
	to take away your freedom to share and change the works.  By contrast,\n\
	the GNU General Public License is intended to guarantee your freedom to\n\
	share and change all versions of a program--to make sure it remains free\n\
	software for all its users.  We, the Free Software Foundation, use the\n\
	GNU General Public License for most of our software; it applies also to\n\
	any other work released this way by its authors.  You can apply it to\n\
	your programs, too.\n\
	\n\
	  When we speak of free software, we are referring to freedom, not\n\
	price.  Our General Public Licenses are designed to make sure that you\n\
	have the freedom to distribute copies of free software (and charge for\n\
	them if you wish), that you receive source code or can get it if you\n\
	want it, that you can change the software or use pieces of it in new\n\
	free programs, and that you know you can do these things.\n\
	\n\
	  To protect your rights, we need to prevent others from denying you\n\
	these rights or asking you to surrender the rights.  Therefore, you have\n\
	certain responsibilities if you distribute copies of the software, or if\n\
	you modify it: responsibilities to respect the freedom of others.\n\
	\n\
	  For example, if you distribute copies of such a program, whether\n\
	gratis or for a fee, you must pass on to the recipients the same\n\
	freedoms that you received.  You must make sure that they, too, receive\n\
	or can get the source code.  And you must show them these terms so they\n\
	know their rights.\n\
	\n\
	  Developers that use the GNU GPL protect your rights with two steps:\n\
	(1) assert copyright on the software, and (2) offer you this License\n\
	giving you legal permission to copy, distribute and/or modify it.\n\
	\n\
	  For the developers' and authors' protection, the GPL clearly explains',\n\
	that there is no warranty for this free software.  For both users' and', \n\
	authors' sake, the GPL requires that modified versions be marked as', \n\
	changed, so that their problems will not be attributed erroneously to\n\
	authors of previous versions.\n\
	\n\
	  Some devices are designed to deny users access to install or run\n\
	modified versions of the software inside them, although the manufacturer\n\
	can do so.  This is fundamentally incompatible with the aim of\n\
	protecting users' freedom to change the software.  The systematic', \n\
	pattern of such abuse occurs in the area of products for individuals to\n\
	use, which is precisely where it is most unacceptable.  Therefore, we\n\
	have designed this version of the GPL to prohibit the practice for those\n\
	products.  If such problems arise substantially in other domains, we\n\
	stand ready to extend this provision to those domains in future versions\n\
	of the GPL, as needed to protect the freedom of users.\n\
	\n\
	  Finally, every program is threatened constantly by software patents.\n\
	States should not allow patents to restrict development and use of\n\
	software on general-purpose computers, but in those that do, we wish to\n\
	avoid the special danger that patents applied to a free program could\n\
	make it effectively proprietary.  To prevent this, the GPL assures that\n\
	patents cannot be used to render the program non-free.\n\
	\n\
	  The precise terms and conditions for copying, distribution and\n\
	modification follow.\n\
	\n\
			       TERMS AND CONDITIONS\n\
	\n\
	  0. Definitions.\n\
	\n\
	  'This License' refers to version 3 of the GNU General Public License.\n\
	\n\
	  'Copyright' also means copyright-like laws that apply to other kinds of\n\
	works, such as semiconductor masks.\n\
	\n\
	  'The Program' refers to any copyrightable work licensed under this\n\
	License.  Each licensee is addressed as 'you'.  'Licensees' and\n\
	'recipients' may be individuals or organizations.\n\
	\n\
	  To 'modify' a work means to copy from or adapt all or part of the work\n\
	in a fashion requiring copyright permission, other than the making of an\n\
	exact copy.  The resulting work is called a 'modified version' of the\n\
	earlier work or a work 'based on' the earlier work.\n\
	\n\
	  A 'covered work' means either the unmodified Program or a work based\n\
	on the Program.\n\
	\n\
	  To 'propagate' a work means to do anything with it that, without\n\
	permission, would make you directly or secondarily liable for\n\
	infringement under applicable copyright law, except executing it on a\n\
	computer or modifying a private copy.  Propagation includes copying,\n\
	distribution (with or without modification), making available to the\n\
	public, and in some countries other activities as well.\n\
	\n\
	  To 'convey' a work means any kind of propagation that enables other\n\
	parties to make or receive copies.  Mere interaction with a user through\n\
	a computer network, with no transfer of a copy, is not conveying.\n\
	\n\
	  An interactive user interface displays 'Appropriate Legal Notices'\n\
	to the extent that it includes a convenient and prominently visible\n\
	feature that (1) displays an appropriate copyright notice, and (2)\n\
	tells the user that there is no warranty for the work (except to the\n\
	extent that warranties are provided), that licensees may convey the\n\
	work under this License, and how to view a copy of this License.  If\n\
	the interface presents a list of user commands or options, such as a\n\
	menu, a prominent item in the list meets this criterion.\n\
	\n\
	  1. Source Code.\n\
	\n\
	  The 'source code' for a work means the preferred form of the work\n\
	for making modifications to it.  'Object code' means any non-source\n\
	form of a work.\n\
	\n\
	  A 'Standard Interface' means an interface that either is an official\n\
	standard defined by a recognized standards body, or, in the case of\n\
	interfaces specified for a particular programming language, one that\n\
	is widely used among developers working in that language.\n\
	\n\
	  The 'System Libraries' of an executable work include anything, other\n\
	than the work as a whole, that (a) is included in the normal form of\n\
	packaging a Major Component, but which is not part of that Major\n\
	Component, and (b) serves only to enable use of the work with that\n\
	Major Component, or to implement a Standard Interface for which an\n\
	implementation is available to the public in source code form.  A\n\
	'Major Component', in this context, means a major essential component\n\
	(kernel, window system, and so on) of the specific operating system\n\
	(if any) on which the executable work runs, or a compiler used to\n\
	produce the work, or an object code interpreter used to run it.\n\
	\n\
	  The 'Corresponding Source' for a work in object code form means all\n\
	the source code needed to generate, install, and (for an executable\n\
	work) run the object code and to modify the work, including scripts to\n\
	control those activities.  However, it does not include the work's', \n\
	System Libraries, or general-purpose tools or generally available free\n\
	programs which are used unmodified in performing those activities but\n\
	which are not part of the work.  For example, Corresponding Source\n\
	includes interface definition files associated with source files for\n\
	the work, and the source code for shared libraries and dynamically\n\
	linked subprograms that the work is specifically designed to require,\n\
	such as by intimate data communication or control flow between those\n\
	subprograms and other parts of the work.\n\
	\n\
	  The Corresponding Source need not include anything that users\n\
	can regenerate automatically from other parts of the Corresponding\n\
	Source.\n\
	\n\
	  The Corresponding Source for a work in source code form is that\n\
	same work.\n\
	\n\
	  2. Basic Permissions.\n\
	\n\
	  All rights granted under this License are granted for the term of\n\
	copyright on the Program, and are irrevocable provided the stated\n\
	conditions are met.  This License explicitly affirms your unlimited\n\
	permission to run the unmodified Program.  The output from running a\n\
	covered work is covered by this License only if the output, given its\n\
	content, constitutes a covered work.  This License acknowledges your\n\
	rights of fair use or other equivalent, as provided by copyright law.\n\
	\n\
	  You may make, run and propagate covered works that you do not\n\
	convey, without conditions so long as your license otherwise remains\n\
	in force.  You may convey covered works to others for the sole purpose\n\
	of having them make modifications exclusively for you, or provide you\n\
	with facilities for running those works, provided that you comply with\n\
	the terms of this License in conveying all material for which you do\n\
	not control copyright.  Those thus making or running the covered works\n\
	for you must do so exclusively on your behalf, under your direction\n\
	and control, on terms that prohibit them from making any copies of\n\
	your copyrighted material outside their relationship with you.\n\
	\n\
	  Conveying under any other circumstances is permitted solely under\n\
	the conditions stated below.  Sublicensing is not allowed; section 10\n\
	makes it unnecessary.\n\
	\n\
	  3. Protecting Users' Legal Rights From Anti-Circumvention Law.', \n\
	\n\
	  No covered work shall be deemed part of an effective technological\n\
	measure under any applicable law fulfilling obligations under article\n\
	11 of the WIPO copyright treaty adopted on 20 December 1996, or\n\
	similar laws prohibiting or restricting circumvention of such\n\
	measures.\n\
	\n\
	  When you convey a covered work, you waive any legal power to forbid\n\
	circumvention of technological measures to the extent such circumvention\n\
	is effected by exercising rights under this License with respect to\n\
	the covered work, and you disclaim any intention to limit operation or\n\
	modification of the work as a means of enforcing, against the work's', \n\
	users, your or third parties' legal rights to forbid circumvention of', \n\
	technological measures.\n\
	\n\
	  4. Conveying Verbatim Copies.\n\
	\n\
	  You may convey verbatim copies of the Program's source code as you', \n\
	receive it, in any medium, provided that you conspicuously and\n\
	appropriately publish on each copy an appropriate copyright notice;\n\
	keep intact all notices stating that this License and any\n\
	non-permissive terms added in accord with section 7 apply to the code;\n\
	keep intact all notices of the absence of any warranty; and give all\n\
	recipients a copy of this License along with the Program.\n\
	\n\
	  You may charge any price or no price for each copy that you convey,\n\
	and you may offer support or warranty protection for a fee.\n\
	\n\
	  5. Conveying Modified Source Versions.\n\
	\n\
	  You may convey a work based on the Program, or the modifications to\n\
	produce it from the Program, in the form of source code under the\n\
	terms of section 4, provided that you also meet all of these conditions:\n\
	\n\
	    a) The work must carry prominent notices stating that you modified\n\
	    it, and giving a relevant date.\n\
	\n\
	    b) The work must carry prominent notices stating that it is\n\
	    released under this License and any conditions added under section\n\
	    7.  This requirement modifies the requirement in section 4 to\n\
	    'keep intact all notices'.\n\
	\n\
	    c) You must license the entire work, as a whole, under this\n\
	    License to anyone who comes into possession of a copy.  This\n\
	    License will therefore apply, along with any applicable section 7\n\
	    additional terms, to the whole of the work, and all its parts,\n\
	    regardless of how they are packaged.  This License gives no\n\
	    permission to license the work in any other way, but it does not\n\
	    invalidate such permission if you have separately received it.\n\
	\n\
	    d) If the work has interactive user interfaces, each must display\n\
	    Appropriate Legal Notices; however, if the Program has interactive\n\
	    interfaces that do not display Appropriate Legal Notices, your\n\
	    work need not make them do so.\n\
	\n\
	  A compilation of a covered work with other separate and independent\n\
	works, which are not by their nature extensions of the covered work,\n\
	and which are not combined with it such as to form a larger program,\n\
	in or on a volume of a storage or distribution medium, is called an\n\
	'aggregate' if the compilation and its resulting copyright are not\n\
	used to limit the access or legal rights of the compilation's users', \n\
	beyond what the individual works permit.  Inclusion of a covered work\n\
	in an aggregate does not cause this License to apply to the other\n\
	parts of the aggregate.\n\
	\n\
	  6. Conveying Non-Source Forms.\n\
	\n\
	  You may convey a covered work in object code form under the terms\n\
	of sections 4 and 5, provided that you also convey the\n\
	machine-readable Corresponding Source under the terms of this License,\n\
	in one of these ways:\n\
	\n\
	    a) Convey the object code in, or embodied in, a physical product\n\
	    (including a physical distribution medium), accompanied by the\n\
	    Corresponding Source fixed on a durable physical medium\n\
	    customarily used for software interchange.\n\
	\n\
	    b) Convey the object code in, or embodied in, a physical product\n\
	    (including a physical distribution medium), accompanied by a\n\
	    written offer, valid for at least three years and valid for as\n\
	    long as you offer spare parts or customer support for that product\n\
	    model, to give anyone who possesses the object code either (1) a\n\
	    copy of the Corresponding Source for all the software in the\n\
	    product that is covered by this License, on a durable physical\n\
	    medium customarily used for software interchange, for a price no\n\
	    more than your reasonable cost of physically performing this\n\
	    conveying of source, or (2) access to copy the\n\
	    Corresponding Source from a network server at no charge.\n\
	\n\
	    c) Convey individual copies of the object code with a copy of the\n\
	    written offer to provide the Corresponding Source.  This\n\
	    alternative is allowed only occasionally and noncommercially, and\n\
	    only if you received the object code with such an offer, in accord\n\
	    with subsection 6b.\n\
	\n\
	    d) Convey the object code by offering access from a designated\n\
	    place (gratis or for a charge), and offer equivalent access to the\n\
	    Corresponding Source in the same way through the same place at no\n\
	    further charge.  You need not require recipients to copy the\n\
	    Corresponding Source along with the object code.  If the place to\n\
	    copy the object code is a network server, the Corresponding Source\n\
	    may be on a different server (operated by you or a third party)\n\
	    that supports equivalent copying facilities, provided you maintain\n\
	    clear directions next to the object code saying where to find the\n\
	    Corresponding Source.  Regardless of what server hosts the\n\
	    Corresponding Source, you remain obligated to ensure that it is\n\
	    available for as long as needed to satisfy these requirements.\n\
	\n\
	    e) Convey the object code using peer-to-peer transmission, provided\n\
	    you inform other peers where the object code and Corresponding\n\
	    Source of the work are being offered to the general public at no\n\
	    charge under subsection 6d.\n\
	\n\
	  A separable portion of the object code, whose source code is excluded\n\
	from the Corresponding Source as a System Library, need not be\n\
	included in conveying the object code work.\n\
	\n\
	  A 'User Product' is either (1) a 'consumer product', which means any\n\
	tangible personal property which is normally used for personal, family,\n\
	or household purposes, or (2) anything designed or sold for incorporation\n\
	into a dwelling.  In determining whether a product is a consumer product,\n\
	doubtful cases shall be resolved in favor of coverage.  For a particular\n\
	product received by a particular user, 'normally used' refers to a\n\
	typical or common use of that class of product, regardless of the status\n\
	of the particular user or of the way in which the particular user\n\
	actually uses, or expects or is expected to use, the product.  A product\n\
	is a consumer product regardless of whether the product has substantial\n\
	commercial, industrial or non-consumer uses, unless such uses represent\n\
	the only significant mode of use of the product.\n\
	\n\
	  'Installation Information' for a User Product means any methods,\n\
	procedures, authorization keys, or other information required to install\n\
	and execute modified versions of a covered work in that User Product from\n\
	a modified version of its Corresponding Source.  The information must\n\
	suffice to ensure that the continued functioning of the modified object\n\
	code is in no case prevented or interfered with solely because\n\
	modification has been made.\n\
	\n\
	  If you convey an object code work under this section in, or with, or\n\
	specifically for use in, a User Product, and the conveying occurs as\n\
	part of a transaction in which the right of possession and use of the\n\
	User Product is transferred to the recipient in perpetuity or for a\n\
	fixed term (regardless of how the transaction is characterized), the\n\
	Corresponding Source conveyed under this section must be accompanied\n\
	by the Installation Information.  But this requirement does not apply\n\
	if neither you nor any third party retains the ability to install\n\
	modified object code on the User Product (for example, the work has\n\
	been installed in ROM).\n\
	\n\
	  The requirement to provide Installation Information does not include a\n\
	requirement to continue to provide support service, warranty, or updates\n\
	for a work that has been modified or installed by the recipient, or for\n\
	the User Product in which it has been modified or installed.  Access to a\n\
	network may be denied when the modification itself materially and\n\
	adversely affects the operation of the network or violates the rules and\n\
	protocols for communication across the network.\n\
	\n\
	  Corresponding Source conveyed, and Installation Information provided,\n\
	in accord with this section must be in a format that is publicly\n\
	documented (and with an implementation available to the public in\n\
	source code form), and must require no special password or key for\n\
	unpacking, reading or copying.\n\
	\n\
	  7. Additional Terms.\n\
	\n\
	  'Additional permissions' are terms that supplement the terms of this\n\
	License by making exceptions from one or more of its conditions.\n\
	Additional permissions that are applicable to the entire Program shall\n\
	be treated as though they were included in this License, to the extent\n\
	that they are valid under applicable law.  If additional permissions\n\
	apply only to part of the Program, that part may be used separately\n\
	under those permissions, but the entire Program remains governed by\n\
	this License without regard to the additional permissions.\n\
	\n\
	  When you convey a copy of a covered work, you may at your option\n\
	remove any additional permissions from that copy, or from any part of\n\
	it.  (Additional permissions may be written to require their own\n\
	removal in certain cases when you modify the work.)  You may place\n\
	additional permissions on material, added by you to a covered work,\n\
	for which you have or can give appropriate copyright permission.\n\
	\n\
	  Notwithstanding any other provision of this License, for material you\n\
	add to a covered work, you may (if authorized by the copyright holders of\n\
	that material) supplement the terms of this License with terms:\n\
	\n\
	    a) Disclaiming warranty or limiting liability differently from the\n\
	    terms of sections 15 and 16 of this License; or\n\
	\n\
	    b) Requiring preservation of specified reasonable legal notices or\n\
	    author attributions in that material or in the Appropriate Legal\n\
	    Notices displayed by works containing it; or\n\
	\n\
	    c) Prohibiting misrepresentation of the origin of that material, or\n\
	    requiring that modified versions of such material be marked in\n\
	    reasonable ways as different from the original version; or\n\
	\n\
	    d) Limiting the use for publicity purposes of names of licensors or\n\
	    authors of the material; or\n\
	\n\
	    e) Declining to grant rights under trademark law for use of some\n\
	    trade names, trademarks, or service marks; or\n\
	\n\
	    f) Requiring indemnification of licensors and authors of that\n\
	    material by anyone who conveys the material (or modified versions of\n\
	    it) with contractual assumptions of liability to the recipient, for\n\
	    any liability that these contractual assumptions directly impose on\n\
	    those licensors and authors.\n\
	\n\
	  All other non-permissive additional terms are considered 'further\n\
	restrictions' within the meaning of section 10.  If the Program as you\n\
	received it, or any part of it, contains a notice stating that it is\n\
	governed by this License along with a term that is a further\n\
	restriction, you may remove that term.  If a license document contains\n\
	a further restriction but permits relicensing or conveying under this\n\
	License, you may add to a covered work material governed by the terms\n\
	of that license document, provided that the further restriction does\n\
	not survive such relicensing or conveying.\n\
	\n\
	  If you add terms to a covered work in accord with this section, you\n\
	must place, in the relevant source files, a statement of the\n\
	additional terms that apply to those files, or a notice indicating\n\
	where to find the applicable terms.\n\
	\n\
	  Additional terms, permissive or non-permissive, may be stated in the\n\
	form of a separately written license, or stated as exceptions;\n\
	the above requirements apply either way.\n\
	\n\
	  8. Termination.\n\
	\n\
	  You may not propagate or modify a covered work except as expressly\n\
	provided under this License.  Any attempt otherwise to propagate or\n\
	modify it is void, and will automatically terminate your rights under\n\
	this License (including any patent licenses granted under the third\n\
	paragraph of section 11).\n\
	\n\
	  However, if you cease all violation of this License, then your\n\
	license from a particular copyright holder is reinstated (a)\n\
	provisionally, unless and until the copyright holder explicitly and\n\
	finally terminates your license, and (b) permanently, if the copyright\n\
	holder fails to notify you of the violation by some reasonable means\n\
	prior to 60 days after the cessation.\n\
	\n\
	  Moreover, your license from a particular copyright holder is\n\
	reinstated permanently if the copyright holder notifies you of the\n\
	violation by some reasonable means, this is the first time you have\n\
	received notice of violation of this License (for any work) from that\n\
	copyright holder, and you cure the violation prior to 30 days after\n\
	your receipt of the notice.\n\
	\n\
	  Termination of your rights under this section does not terminate the\n\
	licenses of parties who have received copies or rights from you under\n\
	this License.  If your rights have been terminated and not permanently\n\
	reinstated, you do not qualify to receive new licenses for the same\n\
	material under section 10.\n\
	\n\
	  9. Acceptance Not Required for Having Copies.\n\
	\n\
	  You are not required to accept this License in order to receive or\n\
	run a copy of the Program.  Ancillary propagation of a covered work\n\
	occurring solely as a consequence of using peer-to-peer transmission\n\
	to receive a copy likewise does not require acceptance.  However,\n\
	nothing other than this License grants you permission to propagate or\n\
	modify any covered work.  These actions infringe copyright if you do\n\
	not accept this License.  Therefore, by modifying or propagating a\n\
	covered work, you indicate your acceptance of this License to do so.\n\
	\n\
	  10. Automatic Licensing of Downstream Recipients.\n\
	\n\
	  Each time you convey a covered work, the recipient automatically\n\
	receives a license from the original licensors, to run, modify and\n\
	propagate that work, subject to this License.  You are not responsible\n\
	for enforcing compliance by third parties with this License.\n\
	\n\
	  An 'entity transaction' is a transaction transferring control of an\n\
	organization, or substantially all assets of one, or subdividing an\n\
	organization, or merging organizations.  If propagation of a covered\n\
	work results from an entity transaction, each party to that\n\
	transaction who receives a copy of the work also receives whatever\n\
	licenses to the work the party's predecessor in interest had or could', \n\
	give under the previous paragraph, plus a right to possession of the\n\
	Corresponding Source of the work from the predecessor in interest, if\n\
	the predecessor has it or can get it with reasonable efforts.\n\
	\n\
	  You may not impose any further restrictions on the exercise of the\n\
	rights granted or affirmed under this License.  For example, you may\n\
	not impose a license fee, royalty, or other charge for exercise of\n\
	rights granted under this License, and you may not initiate litigation\n\
	(including a cross-claim or counterclaim in a lawsuit) alleging that\n\
	any patent claim is infringed by making, using, selling, offering for\n\
	sale, or importing the Program or any portion of it.\n\
	\n\
	  11. Patents.\n\
	\n\
	  A 'contributor' is a copyright holder who authorizes use under this\n\
	License of the Program or a work on which the Program is based.  The\n\
	work thus licensed is called the contributor's \'contributor version\'.', \n\
	\n\
	  A contributor's \'essential patent claims\' are all patent claims', \n\
	owned or controlled by the contributor, whether already acquired or\n\
	hereafter acquired, that would be infringed by some manner, permitted\n\
	by this License, of making, using, or selling its contributor version,\n\
	but do not include claims that would be infringed only as a\n\
	consequence of further modification of the contributor version.  For\n\
	purposes of this definition, 'control' includes the right to grant\n\
	patent sublicenses in a manner consistent with the requirements of\n\
	this License.\n\
	\n\
	  Each contributor grants you a non-exclusive, worldwide, royalty-free\n\
	patent license under the contributor's essential patent claims, to', \n\
	make, use, sell, offer for sale, import and otherwise run, modify and\n\
	propagate the contents of its contributor version.\n\
	\n\
	  In the following three paragraphs, a 'patent license' is any express\n\
	agreement or commitment, however denominated, not to enforce a patent\n\
	(such as an express permission to practice a patent or covenant not to\n\
	sue for patent infringement).  To 'grant' such a patent license to a\n\
	party means to make such an agreement or commitment not to enforce a\n\
	patent against the party.\n\
	\n\
	  If you convey a covered work, knowingly relying on a patent license,\n\
	and the Corresponding Source of the work is not available for anyone\n\
	to copy, free of charge and under the terms of this License, through a\n\
	publicly available network server or other readily accessible means,\n\
	then you must either (1) cause the Corresponding Source to be so\n\
	available, or (2) arrange to deprive yourself of the benefit of the\n\
	patent license for this particular work, or (3) arrange, in a manner\n\
	consistent with the requirements of this License, to extend the patent\n\
	license to downstream recipients.  'Knowingly relying' means you have\n\
	actual knowledge that, but for the patent license, your conveying the\n\
	covered work in a country, or your recipient's use of the covered work', \n\
	in a country, would infringe one or more identifiable patents in that\n\
	country that you have reason to believe are valid.\n\
	\n\
	  If, pursuant to or in connection with a single transaction or\n\
	arrangement, you convey, or propagate by procuring conveyance of, a\n\
	covered work, and grant a patent license to some of the parties\n\
	receiving the covered work authorizing them to use, propagate, modify\n\
	or convey a specific copy of the covered work, then the patent license\n\
	you grant is automatically extended to all recipients of the covered\n\
	work and works based on it.\n\
	\n\
	  A patent license is 'discriminatory' if it does not include within\n\
	the scope of its coverage, prohibits the exercise of, or is\n\
	conditioned on the non-exercise of one or more of the rights that are\n\
	specifically granted under this License.  You may not convey a covered\n\
	work if you are a party to an arrangement with a third party that is\n\
	in the business of distributing software, under which you make payment\n\
	to the third party based on the extent of your activity of conveying\n\
	the work, and under which the third party grants, to any of the\n\
	parties who would receive the covered work from you, a discriminatory\n\
	patent license (a) in connection with copies of the covered work\n\
	conveyed by you (or copies made from those copies), or (b) primarily\n\
	for and in connection with specific products or compilations that\n\
	contain the covered work, unless you entered into that arrangement,\n\
	or that patent license was granted, prior to 28 March 2007.\n\
	\n\
	  Nothing in this License shall be construed as excluding or limiting\n\
	any implied license or other defenses to infringement that may\n\
	otherwise be available to you under applicable patent law.\n\
	\n\
	  12. No Surrender of Others' Freedom.', \n\
	\n\
	  If conditions are imposed on you (whether by court order, agreement or\n\
	otherwise) that contradict the conditions of this License, they do not\n\
	excuse you from the conditions of this License.  If you cannot convey a\n\
	covered work so as to satisfy simultaneously your obligations under this\n\
	License and any other pertinent obligations, then as a consequence you may\n\
	not convey it at all.  For example, if you agree to terms that obligate you\n\
	to collect a royalty for further conveying from those to whom you convey\n\
	the Program, the only way you could satisfy both those terms and this\n\
	License would be to refrain entirely from conveying the Program.\n\
	\n\
	  13. Use with the GNU Affero General Public License.\n\
	\n\
	  Notwithstanding any other provision of this License, you have\n\
	permission to link or combine any covered work with a work licensed\n\
	under version 3 of the GNU Affero General Public License into a single\n\
	combined work, and to convey the resulting work.  The terms of this\n\
	License will continue to apply to the part which is the covered work,\n\
	but the special requirements of the GNU Affero General Public License,\n\
	section 13, concerning interaction through a network will apply to the\n\
	combination as such.\n\
	\n\
	  14. Revised Versions of this License.\n\
	\n\
	  The Free Software Foundation may publish revised and/or new versions of\n\
	the GNU General Public License from time to time.  Such new versions will\n\
	be similar in spirit to the present version, but may differ in detail to\n\
	address new problems or concerns.\n\
	\n\
	  Each version is given a distinguishing version number.  If the\n\
	Program specifies that a certain numbered version of the GNU General\n\
	Public License 'or any later version' applies to it, you have the\n\
	option of following the terms and conditions either of that numbered\n\
	version or of any later version published by the Free Software\n\
	Foundation.  If the Program does not specify a version number of the\n\
	GNU General Public License, you may choose any version ever published\n\
	by the Free Software Foundation.\n\
	\n\
	  If the Program specifies that a proxy can decide which future\n\
	versions of the GNU General Public License can be used, that proxy's', \n\
	public statement of acceptance of a version permanently authorizes you\n\
	to choose that version for the Program.\n\
	\n\
	  Later license versions may give you additional or different\n\
	permissions.  However, no additional obligations are imposed on any\n\
	author or copyright holder as a result of your choosing to follow a\n\
	later version.\n\
	\n\
	  15. Disclaimer of Warranty.\n\
	\n\
	  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY\n\
	APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT\n\
	HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM 'AS IS' WITHOUT WARRANTY\n\
	OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,\n\
	THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR\n\
	PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM\n\
	IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF\n\
	ALL NECESSARY SERVICING, REPAIR OR CORRECTION.\n\
	\n\
	  16. Limitation of Liability.\n\
	\n\
	  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING\n\
	WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS\n\
	THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY\n\
	GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE\n\
	USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF\n\
	DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD\n\
	PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),\n\
	EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF\n\
	SUCH DAMAGES.\n\
	\n\
	  17. Interpretation of Sections 15 and 16.\n\
	\n\
	  If the disclaimer of warranty and limitation of liability provided\n\
	above cannot be given local legal effect according to their terms,\n\
	reviewing courts shall apply local law that most closely approximates\n\
	an absolute waiver of all civil liability in connection with the\n\
	Program, unless a warranty or assumption of liability accompanies a\n\
	copy of the Program in return for a fee.\n\
	\n\
			     END OF TERMS AND CONDITIONS\n\
	\n\ "

	if debug == True:
		print()
		print(gnu_gpl_3)
		print()

def change_state_of_license_agreement_button():

	if accept_license.get() == 1:
		license_info_window_next_button['state'] = 'normal'
	else:
		license_info_window_next_button['state'] = 'disabled'

def find_os_name_and_version():

	path_to_os_release_file = '/etc/os-release'
	os_name_announced_in_os_release = ''
	os_version_announced_in_os_release = ''
	error_message = ''
	global supported_platforms
	list_of_supported_versions_numbers = []

	# Get names and versions of supported operating systems and construct a string that we later print on the window if we aren't running on a supported operating system.
	names_of_supported_operating_systems = '\n\nSupported operating systems are:\n\n'

	for name in supported_platforms:
		for version in supported_platforms[name]:
			names_of_supported_operating_systems = names_of_supported_operating_systems + str(name) + ' ' + str(version) + '\n'

	# If the file /etc/os-release exists, then parse operating system name and version from it.
	if os.path.exists(path_to_os_release_file):

		text_lines_list = [] 

		try:
			with open(path_to_os_release_file, 'rt') as file_handler: # Open file, the 'with' method closes files when execution exits the with - block
				file_handler.seek(0) # Make sure that the 'read' - pointer is at the beginning of the source file
				text_lines_list.extend(file_handler.readlines())														   

		except IOError:
			error_message = 'Error reading file: ' + path_to_os_release_file
		except OSError:
			error_message = 'Error reading file: ' + path_to_os_release_file

		if error_message == '':

			# Find operating system name and version number from the text file.
			for line in text_lines_list:
				
				# Strip line ending, tab - characters and white space.
				line = line.strip('\n')
				line = line.strip('\t')
				line = line.strip()
				
				# If the first charecter on the text line is '#' (a comment line), or the line is empty, then skip the line.
				if line == '':
					continue
				if line[0] == '#':
					continue

				# Get operating system name from the text line.
				if 'ID=' == line[0:3]:
					os_name_announced_in_os_release = line.split('=')[1].strip('"').strip().lower()
				# Get operating system version number from the text line.
				if 'VERSION_ID=' in line:
					os_version_announced_in_os_release = line.split('=')[1].strip('"').strip()

			# Test sanity of the text we parsed from /etc/os-release
			if os_name_announced_in_os_release not in supported_platforms:
				error_message = 'your "' + str(path_to_os_release_file)+ '" says your operating system is: "' + os_name_announced_in_os_release + ' ' + os_version_announced_in_os_release + '"\n\nThis version is not in the list of supported operating systems.' + names_of_supported_operating_systems + '\nYou can force installation by giving a supported os name and version on the commandline. Note that installation on a unsupported platform may not work correctly.\n\nExample below forces os and version to Ubuntu 14.04\n\n' + './installer.py  -force-distro  ubuntu  14.04'
			else:
				list_of_supported_versions_numbers = supported_platforms[os_name_announced_in_os_release]

				if os_version_announced_in_os_release not in list_of_supported_versions_numbers:
					error_message = 'your "' + str(path_to_os_release_file)+ '" says your operating system is: "' + os_name_announced_in_os_release + ' ' + os_version_announced_in_os_release + '"\n\nThis version is not in the list of supported operating systems.' + names_of_supported_operating_systems + '\nYou can force installation by giving a supported os name and version on the commandline. Note that installation on a unsupported platform may not work correctly.\n\nExample below forces os and version to Ubuntu 14.04\n\n' + './installer.py  -force-distro  ubuntu  14.04'
	else:
		error_message = 'Could not find file: "' + path_to_os_release_file + '"\n\nThis file is needed for determining what operating system and version we are running on.' + names_of_supported_operating_systems + '\nYou can force installation by giving a supported os name and version on the commandline. Note that installation on a unsupported platform may not work correctly.\n\nExample below forces os and version to Ubuntu 14.04\n\n' + './installer.py  -force-distro  ubuntu  14.04'

	if debug == True:
		print()
		print('os_name_announced_in_os_release =', os_name_announced_in_os_release)
		print('os_version_announced_in_os_release =', os_version_announced_in_os_release)
		print('error_message =', error_message)
		print()

	return(os_name_announced_in_os_release, os_version_announced_in_os_release, error_message)  


###############################
# Main program starts here :) #
###############################

# Check if user gave the -debug option on the commandline
debug = False
force_distro_found = False
os_name_found_on_commandline = False
os_name = ''
os_version = ''

# Define supported operating systems and versions
supported_platforms = {'debian': ['7'], 'ubuntu': ['12.04', '14.04']}

# Parse commandline arguments.
for item in sys.argv[1:]:

	print('item', item)

	if 'force-distro' in item.lower():
		force_distro_found=True
		continue
	if ('debug' in item.lower()):
		debug = True
		continue
	if force_distro_found==True:
		os_name=item.lower()
		os_name_found_on_commandline=True
		force_distro_found=False
		continue
	if os_name_found_on_commandline==True:
		os_version=item
		os_name_found_on_commandline=False
		continue

# Check if user forced operating system name and version number on commandline. This is used to force installation on an unsupported platform.
if (os_name != '') and (os_version != ''):
	if not os_name in supported_platforms:
		os_name = ''
	else:
		if not os_version in supported_platforms[os_name]:
			os_version = ''

if debug == True:
	print()
	print('FreeLCS installer version', version)
	print('-' * 75)
	print()
	print('Debug mode is ON')
	print('Commandline: ', sys.argv)
	print()

# If user has not forced operating system name and version on the commandline, then find out the true os name and version by reading the /etc/os-release
temporary_list = []
error_message_from_find_os_name_and_version = ''

if (os_name == '') or (os_version == ''):

	os_name = ''
	os_version = ''

	# Find out what is the name and version of the operating system we are running on.
	temporary_list = find_os_name_and_version()

	# If the error message is empty then we have found the name and version of the operating system. Assign this info to variables.
	error_message_from_find_os_name_and_version = temporary_list[2]

	if error_message_from_find_os_name_and_version == '':
		os_name = temporary_list[0]
		os_version = temporary_list[1]
	temporary_list = []

if debug == True:
	print()
	print('os_name =', os_name)
	print('os_version =', os_version)
	print()

# Create the root GUI window.
root_window = tkinter.Tk()
if error_message_from_find_os_name_and_version == '':
	root_window.title("FreeLCS Installer version " + version + ', running on ' + os_name[0].upper() + os_name[1:] + ' ' + os_version)
else:
	root_window.title("FreeLCS Installer version " + version)
#root_window.geometry('800x600')
root_window.grid_columnconfigure(0, weight=1)
root_window.grid_rowconfigure(0, weight=1)

# Define text wrap length
text_wrap_length_in_pixels = 500

# Define some tkinter variables
first_window_label_text = tkinter.StringVar()
language = tkinter.StringVar()
language.set('english')
target_path = tkinter.StringVar()
target_path.set('/')
hotfolder_path = tkinter.StringVar()
directory_for_temporary_files = tkinter.StringVar()
directory_for_results = tkinter.StringVar()
hotfolder_path_truncated_for_display = tkinter.StringVar()
directory_for_temporary_files_truncated_for_display = tkinter.StringVar()
directory_for_results_truncated_for_display = tkinter.StringVar()
directory_for_error_logs = tkinter.StringVar()
directory_for_error_logs_truncated_for_display = tkinter.StringVar()
file_expiry_time_in_minutes = tkinter.StringVar()
number_of_processor_cores = tkinter.StringVar()
write_html_progress_report = tkinter.BooleanVar()
write_html_progress_report.set(True)
web_page_path = tkinter.StringVar()
web_page_path_truncated_for_display = tkinter.StringVar()
create_a_ram_disk_for_html_report = tkinter.BooleanVar()
create_a_ram_disk_for_html_report.set(True)
ram_device_name = tkinter.StringVar()
user_account = tkinter.StringVar()
root_password = tkinter.StringVar()
root_password_was_not_accepted_message = tkinter.StringVar()
use_samba  = tkinter.BooleanVar()
use_samba.set(True)
web_page_name = tkinter.StringVar()
sample_peak = tkinter.BooleanVar()
sample_peak.set(True)
accept_license = tkinter.IntVar()
accept_license.set(0)

# Define variables that will be used as the text content on seventh window. The variables can hold one of two values: 'Installed' / 'Not Installed'.
sox_is_installed = tkinter.StringVar()
gnuplot_is_installed = tkinter.StringVar()	
samba_is_installed = tkinter.StringVar()
mediainfo_is_installed = tkinter.StringVar()
libebur128_is_installed = tkinter.StringVar()
loudnesscorrection_scripts_are_installed = tkinter.StringVar()
# More seventh window variables.
seventh_window_message_1 = tkinter.StringVar()
seventh_window_message_2 = tkinter.StringVar()
seventh_window_error_message_1 = tkinter.StringVar()
seventh_window_error_message_2 = tkinter.StringVar()


# Define Email variables
send_error_messages_by_email = tkinter.BooleanVar()
send_error_messages_by_email.set(False)
use_tls = tkinter.BooleanVar()
use_tls.set(False)
smtp_server_requires_authentication = tkinter.BooleanVar()
smtp_server_requires_authentication.set(False)
smtp_server_name = tkinter.StringVar()
smtp_server_port = tkinter.StringVar()
smtp_username = tkinter.StringVar()
smtp_password = tkinter.StringVar()
email_sending_interval_in_minutes = tkinter.StringVar()
email_addresses_string = tkinter.StringVar()
email_address_1 = tkinter.StringVar()
email_address_2 = tkinter.StringVar()
email_address_3 = tkinter.StringVar()
email_address_4 = tkinter.StringVar()
email_address_5 = tkinter.StringVar()
email_sending_details = {}
message_recipients = []
heartbeat = tkinter.BooleanVar()
heartbeat.set(False)
email_sending_message_1 = tkinter.StringVar()
email_sending_message_2 = tkinter.StringVar()
showstopper_error_message = tkinter.StringVar()

# We need to know when user inputs a new value in smtp server combobox and call a subroutine that writes that value to our variable.
# To achieve this we must trace when the combobox value changes.
smtp_server_name.trace('w', define_smtp_server_name)
smtp_server_port.trace('w', define_smtp_server_port)


# Define some normal python variables
gnu_gpl_3 = ''
english = 1
finnish = 0
file_expiry_time = 28800
email_sending_interval = 1800
message_text_string = ''
list_of_ram_devices = []
list_of_normal_users_accounts = []
loudness_correction_init_script_content = []
ram_disk_mount_commands = []
delay_between_directory_reads = 5
natively_supported_file_formats = ['.wav', '.flac', '.ogg']
ffmpeg_output_format = ''
silent = True
html_progress_report_write_interval = 5
send_error_messages_to_logfile = True
heartbeat_file_name = '00-HeartBeat.pickle'
heartbeat_write_interval = 30
where_to_send_error_messages = ['logfile'] # Tells where to print / send the error messages. The list can have any or all of these values: screen, logfile, email.
configfile_path = '/etc/Loudness_Correction_Settings.pickle'
loudnesscorrection_init_script_name = 'loudnesscorrection_init_script'
loudnesscorrection_init_script_path = '/etc/init.d/' + loudnesscorrection_init_script_name
loudnesscorrection_init_script_link_name = 'S99' + loudnesscorrection_init_script_name
loudnesscorrection_init_script_link_path = '/etc/rc2.d/' + loudnesscorrection_init_script_link_name
all_needed_external_programs_are_installed = True
external_program_installation_has_been_already_run = False
eight_window_textwidget_text_content  = ''
all_installation_messages = ''
all_ip_addresses_of_the_machine = []
all_ip_addresses_of_the_machine = get_ip_addresses_of_the_host_machine()
peak_measurement_method = '--peak=sample'
installation_is_running = False
libebur128_repository_url = "http://github.com/mhartzel/libebur128_fork_for_freelcs_2.4.git"

# Get the directory the os uses for storing temporary files.
directory_for_os_temporary_files = tempfile.gettempdir()

# Define global variables that later hold paths to external programs that LoudnessCorrection needs to operate.
python3_path = ''
sox_path = ''
gnuplot_path = ''
samba_path = ''
loudness_path = ''
mediainfo_path = ''
force_reinstallation_of_all_programs = False

# Libebur128 program 'loudness' must be a version known to be free of bad bugs.
# Since 'loudness' does not have a version number the only method to check for it's version is the compilation date of the 'loudness' executable.
# NOTE: This is variable is not used in installer version 48, 49, but it might be used in the future.
loudness_required_install_date_list = ['14', '8', '2012'] # Day, Month, Year. Timestamp of 'loudness' must be at least this or it is old version with known bugs.

# Define global installation variables.
apt_get_commands = []
needed_packages_install_commands = []
libebur128_dependencies_install_commands = []
libebur128_git_commands = []
libebur128_cmake_commands = []
libebur128_make_build_and_install_commands = []
libebur128_simplified_build_and_install_commands_displayed_to_user = []
sox_download_make_build_and_install_commands = []
sox_simplified_build_and_install_commands_displayed_to_user = []

# Find paths to all critical programs we need to run LoudnessCorrection
find_paths_to_all_external_programs_we_need()

# Get installation commands to global installation variables.
define_program_installation_commands()

# Find the path to LoudnessCorrection.py and HeartBeat_Checker.py in the current directory.
path_to_loudnesscorrection = find_program_in_current_dir('LoudnessCorrection.py')
path_to_heartbeat_checker = find_program_in_current_dir('HeartBeat_Checker.py')

# Define initial samba configuration
samba_configuration_file_content = ['# Samba Configuration File', \
'', \
'[global]', \
'workgroup = WORKGROUP', \
'server string = %h server (Samba, LoudnessCorrection)', \
'force create mode = 0777', \
'unix extensions = no', \
'log file = /var/log/samba/log.%m', \
'max log size = 1000', \
'syslog = 0', \
'panic action = /usr/share/samba/panic-action %d', \
'security = share', \
'socket options = TCP_NODELAY', \
'', \
'[LoudnessCorrection]', \
'comment = LoudnessCorrection', \
'read only = no', \
'locking = no', \
'path = /LoudnessCorrection', \
'guest ok = yes', \
'browseable = yes']
samba_configuration_file_content_as_a_string = '\n'.join(samba_configuration_file_content)

# If there is a previously saved settings-file then read in settings from that and assign values to variables.
previously_saved_settings_dict = {}
previously_saved_email_sending_details = {}

if (os.path.exists(configfile_path) == True) or (os.access(configfile_path, os.R_OK) == True):
	try:
		with open(configfile_path, 'rb') as configfile_handler:
			previously_saved_settings_dict = pickle.load(configfile_handler)
	except KeyboardInterrupt:
		print('\n\nUser cancelled operation.\n')
		sys.exit(0)
	except IOError as reason_for_error:
		error_message = 'Error reading configfile: ' * english + 'Asetustiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error)
		print(error_message)
		sys.exit(1)
	except OSError as reason_for_error:
		error_message = 'Error reading configfile: ' * english + 'Asetustiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error)
		print(error_message)
		sys.exit(1)
	except EOFError as reason_for_error:
		error_message = 'Error reading configfile: ' * english + 'Asetustiedoston lukemisessa tapahtui virhe: ' * finnish + str(reason_for_error)
		print(error_message)
		sys.exit(1)

config_file_created_by_installer_version = 0

if 'config_file_created_by_installer_version' in previously_saved_settings_dict:
	config_file_created_by_installer_version = previously_saved_settings_dict['config_file_created_by_installer_version']

# Configfile needs to be created at least wth version 039 of installer to be compatible with current version of installer.
if int(config_file_created_by_installer_version) >= 39:
	if debug == True:
		print('Values read from old configfile')
		print('-' * 75)
	if 'target_path' in previously_saved_settings_dict:
			target_path.set(previously_saved_settings_dict['target_path'])
			if debug == True:
				print('target_path =', previously_saved_settings_dict['target_path'])
	if 'language' in previously_saved_settings_dict:
			language.set(previously_saved_settings_dict['language'])
			if debug == True:
				print('language =', previously_saved_settings_dict['language'])
	if 'number_of_processor_cores' in previously_saved_settings_dict:
			number_of_processor_cores.set(previously_saved_settings_dict['number_of_processor_cores'])
			if debug == True:
				print('number_of_processor_cores =', previously_saved_settings_dict['number_of_processor_cores'])
	if 'file_expiry_time' in previously_saved_settings_dict:
			file_expiry_time = previously_saved_settings_dict['file_expiry_time']
			if debug == True:
				print('file_expiry_time =', previously_saved_settings_dict['file_expiry_time'])
	if 'send_error_messages_by_email' in previously_saved_settings_dict:
			send_error_messages_by_email.set(previously_saved_settings_dict['send_error_messages_by_email'])
			if debug == True:
				print('send_error_messages_by_email =', previously_saved_settings_dict['send_error_messages_by_email'])
	if 'email_sending_details' in previously_saved_settings_dict:
			previously_saved_email_sending_details = previously_saved_settings_dict['email_sending_details']
			use_tls.set(previously_saved_email_sending_details['use_tls'])
			smtp_server_requires_authentication.set(previously_saved_email_sending_details['smtp_server_requires_authentication'])
			smtp_username.set(previously_saved_email_sending_details['smtp_username'])
			smtp_password.set(previously_saved_email_sending_details['smtp_password'])
			email_sending_interval = previously_saved_email_sending_details['email_sending_interval']
			if debug == True:
				print('use_tls =', previously_saved_email_sending_details['use_tls'])
				print('smtp_server_requires_authentication =', previously_saved_email_sending_details['smtp_server_requires_authentication'])
				print('smtp_username =', previously_saved_email_sending_details['smtp_username'])
				print('smtp_password =', previously_saved_email_sending_details['smtp_password'])
				print('email_sending_interval =', previously_saved_email_sending_details['email_sending_interval'])
			if previously_saved_email_sending_details['message_recipients'] != []:
				email_addresses_string.set(previously_saved_email_sending_details['message_recipients'][0])
				if debug == True:
					print('message_recipients =', previously_saved_email_sending_details['message_recipients'][0])
	if 'write_html_progress_report' in previously_saved_settings_dict:
		write_html_progress_report.set(previously_saved_settings_dict['write_html_progress_report'])
		if debug == True:
				print('write_html_progress_report =', previously_saved_settings_dict['write_html_progress_report'])
	if 'peak_measurement_method' in previously_saved_settings_dict:
		if previously_saved_settings_dict['peak_measurement_method'] == '--peak=sample':
			sample_peak.set(True)
		if previously_saved_settings_dict['peak_measurement_method'] == '--peak=true':
			sample_peak.set(False)
		if debug == True:
				print('peak_measurement_method =', previously_saved_settings_dict['peak_measurement_method'])
		set_sample_peak_measurement_method()
	if debug == True:
		print('-' * 75)

# Create frames inside the root window to hold other GUI elements. All frames and widgets must be created in the main program, otherwise they are not accessible in subroutines. 
##########################################################################################################################

first_frame=tkinter.ttk.Frame(root_window)
first_frame.grid(column=0, row=0, padx=20, pady=5, columnspan=4, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))

first_frame_child_frame_1=tkinter.ttk.Frame(first_frame)
first_frame_child_frame_1['borderwidth'] = 2
first_frame_child_frame_1['relief'] = 'sunken'
first_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

second_frame=tkinter.ttk.Frame(root_window)
second_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

second_frame_child_frame_1=tkinter.ttk.Frame(second_frame)
second_frame_child_frame_1['borderwidth'] = 2
second_frame_child_frame_1['relief'] = 'sunken'
second_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

second_frame_child_frame_2=tkinter.ttk.Frame(second_frame)
second_frame_child_frame_2['borderwidth'] = 2
second_frame_child_frame_2['relief'] = 'sunken'
second_frame_child_frame_2.grid(column=0, row=1, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

second_frame_child_frame_3=tkinter.ttk.Frame(second_frame)
second_frame_child_frame_3['borderwidth'] = 2
second_frame_child_frame_3['relief'] = 'sunken'
second_frame_child_frame_3.grid(column=0, row=2, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

second_frame_child_frame_4=tkinter.ttk.Frame(second_frame)
second_frame_child_frame_4['borderwidth'] = 2
second_frame_child_frame_4['relief'] = 'sunken'
second_frame_child_frame_4.grid(column=0, row=3, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

third_frame=tkinter.ttk.Frame(root_window)
third_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

third_frame_child_frame_1=tkinter.ttk.Frame(third_frame)
third_frame_child_frame_1['borderwidth'] = 2
third_frame_child_frame_1['relief'] = 'sunken'
third_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

fourth_frame=tkinter.ttk.Frame(root_window)
fourth_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

fourth_frame_child_frame_1=tkinter.ttk.Frame(fourth_frame)
fourth_frame_child_frame_1['borderwidth'] = 2
fourth_frame_child_frame_1['relief'] = 'sunken'
fourth_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

fifth_frame=tkinter.ttk.Frame(root_window)
fifth_frame.columnconfigure(0, weight=1)
fifth_frame.columnconfigure(1, weight=1)
fifth_frame.columnconfigure(2, weight=1)
fifth_frame.columnconfigure(3, weight=1)
fifth_frame.rowconfigure(0, weight=1)
fifth_frame.rowconfigure(1, weight=0)
fifth_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))

fifth_frame_child_frame_1=tkinter.ttk.Frame(fifth_frame)
fifth_frame_child_frame_1['borderwidth'] = 2
fifth_frame_child_frame_1['relief'] = 'sunken'
fifth_frame_child_frame_1.columnconfigure(0, weight=1)
fifth_frame_child_frame_1.rowconfigure(0, weight=0)
fifth_frame_child_frame_1.rowconfigure(1, weight=1)
fifth_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))

##########################################################################################################################

sixth_frame=tkinter.ttk.Frame(root_window)
sixth_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

sixth_frame_child_frame_1=tkinter.ttk.Frame(sixth_frame)
sixth_frame_child_frame_1['borderwidth'] = 2
sixth_frame_child_frame_1['relief'] = 'sunken'
sixth_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

seventh_frame=tkinter.ttk.Frame(root_window)
seventh_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

seventh_frame_child_frame_1=tkinter.ttk.Frame(seventh_frame)
seventh_frame_child_frame_1['borderwidth'] = 2
seventh_frame_child_frame_1['relief'] = 'sunken'
seventh_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

eigth_frame=tkinter.ttk.Frame(root_window)
eigth_frame.columnconfigure(0, weight=1)
eigth_frame.columnconfigure(1, weight=1)
eigth_frame.columnconfigure(2, weight=1)
eigth_frame.columnconfigure(3, weight=1)
eigth_frame.rowconfigure(0, weight=1)
eigth_frame.rowconfigure(1, weight=0)
eigth_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))

eigth_frame_child_frame_1=tkinter.ttk.Frame(eigth_frame)
eigth_frame_child_frame_1['borderwidth'] = 2
eigth_frame_child_frame_1['relief'] = 'sunken'
eigth_frame_child_frame_1.columnconfigure(0, weight=1)
eigth_frame_child_frame_1.rowconfigure(0, weight=0)
eigth_frame_child_frame_1.rowconfigure(1, weight=1)
eigth_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))

##########################################################################################################################

ninth_frame=tkinter.ttk.Frame(root_window)
ninth_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

ninth_frame_child_frame_1=tkinter.ttk.Frame(ninth_frame)
ninth_frame_child_frame_1['borderwidth'] = 2
ninth_frame_child_frame_1['relief'] = 'sunken'
ninth_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

ffmpeg_frame=tkinter.ttk.Frame(root_window)
ffmpeg_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

ffmpeg_frame_child_frame_1=tkinter.ttk.Frame(ffmpeg_frame)
ffmpeg_frame_child_frame_1['borderwidth'] = 2
ffmpeg_frame_child_frame_1['relief'] = 'sunken'
ffmpeg_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

license_frame=tkinter.ttk.Frame(root_window)
license_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

license_frame_child_frame_1=tkinter.ttk.Frame(license_frame)
license_frame_child_frame_1['borderwidth'] = 2
license_frame_child_frame_1['relief'] = 'sunken'
license_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

##########################################################################################################################

showstopper_frame=tkinter.ttk.Frame(root_window)
showstopper_frame.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E))

showstopper_frame_child_frame_1=tkinter.ttk.Frame(showstopper_frame)
showstopper_frame_child_frame_1['borderwidth'] = 2
showstopper_frame_child_frame_1['relief'] = 'sunken'
showstopper_frame_child_frame_1.grid(column=0, row=0, columnspan=4, padx=20, pady=5, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))


###########################################################################################################
# Window number 1                                                                                         #
###########################################################################################################

# Define the text message to display on the first window.
# This is the introcution window, with nothing but text on it.
first_window_label_text.set('This program lets you configure LoudnessCorrection settings and install all needed Linux init scripts.\n\nAfter configuration LoudnessCorrection starts automatically every time the computer starts up. There will be a 1 - 2 minute delay after boot before LoudnessCorrection is started. This makes sure all needed Linux services are up when we start up.')
first_window_label = tkinter.ttk.Label(first_frame_child_frame_1, textvariable=first_window_label_text, wraplength=text_wrap_length_in_pixels)
first_window_label.grid(column=0, row=0, columnspan=4, pady=10, padx=20, sticky=(tkinter.E, tkinter.N))

# Create the buttons for the frame
first_window_quit_button = tkinter.Button(first_frame, text = "Quit", command = quit_program)
first_window_quit_button.grid(column=1, row=2, padx=30, pady=10, sticky=(tkinter.E, tkinter.N))
first_window_next_button = tkinter.Button(first_frame, text = "Next", command = call_second_frame_on_top)
first_window_next_button.grid(column=2, row=2, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))


###########################################################################################################
# Window number 2                                                                                         #
###########################################################################################################

# This window lets put in information for paths, language, how many processor cores to use for processing and file expiry time.

#################
# Child Frame 1 #
#################

# HotFolder path
second_window_label_1 = tkinter.ttk.Label(second_frame_child_frame_1, text='Target Directory:')
second_window_label_1.grid(column=0, row=0, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))
second_window_target_path_label = tkinter.ttk.Label(second_frame_child_frame_1, textvariable=target_path, wraplength=text_wrap_length_in_pixels)
second_window_target_path_label.grid(column=1, row=0, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))
second_window_browse_button = tkinter.Button(second_frame_child_frame_1, text = "Browse", command = get_target_directory, width = 10)
second_window_browse_button.grid(column=0, row=1, pady=10, sticky=(tkinter.N))
second_window_label_2 = tkinter.ttk.Label(second_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='The directory structure needed by the scripts is automatically created in the target directory. One of the directories that is created is called the HotFolder. HotFolder is the folder that users drop audio files into for loudness correction.\nThe name of the HotFolder is:')
second_window_label_2.grid(column=0, row=2, columnspan=4, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))

# Define label that shows the hotfolder path
hotfolder_path_label_1 = tkinter.ttk.Label(second_frame_child_frame_1,  textvariable=hotfolder_path_truncated_for_display)
hotfolder_path_label_1.grid(column=0, row=3, columnspan=4, padx=10, sticky=(tkinter.W, tkinter.N))

# Define a dummy label to show an empty row beneath the others
second_window_dummy_label_1 = tkinter.ttk.Label(second_frame_child_frame_1,  text='')
second_window_dummy_label_1.grid(column=0, row=5, columnspan=2, sticky=(tkinter.W, tkinter.N))

#################
# Child Frame 2 #
#################

# Define items to display in the GUI frames.
second_window_label_3 = tkinter.ttk.Label(second_frame_child_frame_2,  text='Language for HotFolder pathnames and result-graphics:')
second_window_label_3.grid(column=0, row=0, columnspan=2, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))

# Language for pathnames and result-graphics
english_radiobutton = tkinter.ttk.Radiobutton(second_frame_child_frame_2, text='English', variable=language, value='english', command=set_directory_names_according_to_language)
finnish_radiobutton = tkinter.ttk.Radiobutton(second_frame_child_frame_2, text='Finnish', variable=language, value='finnish', command=set_directory_names_according_to_language)
english_radiobutton.grid(column=2, row=0, padx=15)
finnish_radiobutton.grid(column=3, row=0, padx=15)

# Define label that shows the hotfolder path
second_window_label_4 = tkinter.ttk.Label(second_frame_child_frame_2, wraplength=text_wrap_length_in_pixels, text='Language setting affects directory names and text language in loudness result graphics. The following directories will be created in the Target Directory:')
second_window_label_4.grid(column=0, row=1, columnspan=4, padx=10, pady=10, sticky=(tkinter.W, tkinter.N))

# Define label that shows the hotfolder path
hotfolder_path_label_2 = tkinter.ttk.Label(second_frame_child_frame_2,  textvariable=hotfolder_path_truncated_for_display)
hotfolder_path_label_2.grid(column=0, row=2, columnspan=4, padx=10, sticky=(tkinter.W, tkinter.N))

# Define label that shows the path for 'directory_for_results'
directory_for_results_label = tkinter.ttk.Label(second_frame_child_frame_2,  textvariable=directory_for_results_truncated_for_display)
directory_for_results_label.grid(column=0, row=3, columnspan=4, padx=10, sticky=(tkinter.W, tkinter.N))

# Define label that shows the path for 'web_page_path'
web_page_path_label = tkinter.ttk.Label(second_frame_child_frame_2,  textvariable=web_page_path_truncated_for_display)
web_page_path_label.grid(column=0, row=4, columnspan=4, padx=10, sticky=(tkinter.W, tkinter.N))

# Define label that shows the path for 'directory_for_error_logs'
directory_for_error_logs_label = tkinter.ttk.Label(second_frame_child_frame_2,  textvariable=directory_for_error_logs_truncated_for_display)
directory_for_error_logs_label.grid(column=0, row=5, columnspan=4, padx=10, sticky=(tkinter.W, tkinter.N))

# Define label that shows the path for 'directory_for_temporary_files'
directory_for_temporary_files_label = tkinter.ttk.Label(second_frame_child_frame_2,  textvariable=directory_for_temporary_files_truncated_for_display)
directory_for_temporary_files_label.grid(column=0, row=6, columnspan=4, padx=10, sticky=(tkinter.W, tkinter.N))

# Define a dummy label to show an empty row beneath the others
second_window_dummy_label_2 = tkinter.ttk.Label(second_frame_child_frame_2,  text='')
second_window_dummy_label_2.grid(column=0, row=7, columnspan=2, sticky=(tkinter.W, tkinter.N))

#################
# Child Frame 3 #
#################

# Number of processor to use for processing
second_window_label_4 = tkinter.ttk.Label(second_frame_child_frame_3, text='Number Of Processor Cores to Use:')
second_window_label_4.grid(column=0, row=0, columnspan=2, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))
number_of_processor_cores_combobox = tkinter.ttk.Combobox(second_frame_child_frame_3, justify=tkinter.CENTER, width=4, textvariable=number_of_processor_cores)
number_of_processor_cores_combobox['values'] = (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64)

# If a previously saved setting can be found then use it.
if number_of_processor_cores.get() != '':
	number_of_processor_cores_combobox.set(number_of_processor_cores.get())
else:
	number_of_processor_cores_combobox.set(4)
	
number_of_processor_cores_combobox.bind('<<ComboboxSelected>>', print_number_of_processors_cores_to_use)
number_of_processor_cores_combobox.grid(column=3, row=0, pady=10, padx=10, sticky=(tkinter.E))
second_window_label_5 = tkinter.ttk.Label(second_frame_child_frame_3, wraplength=text_wrap_length_in_pixels, text='If your HotFolder is on a fast RAID, then selecting more processor cores here than you actually have speeds up processing (For Example select 6 cores, when you only have 2 real ones). Each file that is processed ties up two processor cores. Selecting more cores here results in more files being processed in parallel. It is adviced that you test different settings to find the sweet spot of your machine.')
second_window_label_5.grid(column=0, row=1, columnspan=4, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))

#################
# Child Frame 4 #
#################

# File expiry time
second_window_label_6 = tkinter.ttk.Label(second_frame_child_frame_4, text='File expiry time in minutes: \n\nFiles that have been in Hotfolder for longer than this time, will be automatically deleted.')
second_window_label_6.grid(column=0, row=0, columnspan=4, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))
file_expiry_time_in_minutes_combobox = tkinter.ttk.Combobox(second_frame_child_frame_4, justify=tkinter.CENTER, width=5, textvariable=file_expiry_time_in_minutes)
file_expiry_time_in_minutes_combobox['values'] = (60, 90, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900, 960)

# If a previously saved setting can be found then use it.
if file_expiry_time != 0:
	file_expiry_time_in_minutes.set(int(file_expiry_time / 60))
	file_expiry_time_in_minutes_combobox.set(file_expiry_time_in_minutes.get())
else:
	file_expiry_time_in_minutes_combobox.set(480)
	
file_expiry_time_in_minutes_combobox.bind('<<ComboboxSelected>>', convert_file_expiry_time_to_seconds)
file_expiry_time_in_minutes_combobox.grid(column=3, row=0, pady=10, padx=10, sticky=(tkinter.N))

# Create the buttons under childframes
second_window_back_button = tkinter.Button(second_frame, text = "Back", command = call_first_frame_on_top)
second_window_back_button.grid(column=1, row=5, padx=30, pady=10, sticky=(tkinter.E, tkinter.N))
second_window_next_button = tkinter.Button(second_frame, text = "Next", command = call_third_frame_on_top)
second_window_next_button.grid(column=2, row=5, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))


###########################################################################################################
# Window number 3                                                                                         #
###########################################################################################################

# Email settings and send test email.

# Define label and two buttons (enable / disable email settings)
third_window_label_1 = tkinter.ttk.Label(third_frame_child_frame_1, text='Send LoudnessCorrection error messages through email:')
third_window_label_1.grid(column=0, row=0, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))
send_error_messages_by_email_true_button = tkinter.ttk.Radiobutton(third_frame_child_frame_1, text='Yes', variable=send_error_messages_by_email, value=True, command=enable_email_settings)
send_error_messages_by_email_false_button = tkinter.ttk.Radiobutton(third_frame_child_frame_1, text='No', variable=send_error_messages_by_email, value=False, command=enable_email_settings)
send_error_messages_by_email_true_button.grid(column=1, row=0, padx=15)
send_error_messages_by_email_false_button.grid(column=2, row=0, padx=15)

third_window_label_10 = tkinter.ttk.Label(third_frame_child_frame_1, text='(Settings to use for Gmail:   TLS = yes   Authentication = yes   Server name = smtp.gmail.com   Port = 587.)', foreground='dark gray')
third_window_label_10.grid(column=0, row=1, pady=10, padx=10, columnspan=3, sticky=(tkinter.W, tkinter.N))

third_window_label_2 = tkinter.ttk.Label(third_frame_child_frame_1, text='Smtp Server requires TLS encryption:')
third_window_label_2.grid(column=0, row=2, padx=10, sticky=(tkinter.W, tkinter.N))

use_tls_true_button = tkinter.ttk.Radiobutton(third_frame_child_frame_1, text='Yes', variable=use_tls, value=True, command=print_use_tls)
use_tls_false_button = tkinter.ttk.Radiobutton(third_frame_child_frame_1, text='No', variable=use_tls, value=False, command=print_use_tls)
use_tls_true_button.state(['disabled'])
use_tls_false_button.state(['disabled'])
use_tls_true_button.grid(column=1, row=2, padx=15)
use_tls_false_button.grid(column=2, row=2, padx=15)

third_window_label_3 = tkinter.ttk.Label(third_frame_child_frame_1, text='Smtp Server requires authentication:')
third_window_label_3.grid(column=0, row=3, padx=10, sticky=(tkinter.W, tkinter.N))

smtp_server_requires_authentication_true_button = tkinter.ttk.Radiobutton(third_frame_child_frame_1, text='Yes', variable=smtp_server_requires_authentication, value=True, command=print_smtp_server_requires_authentication)
smtp_server_requires_authentications_false_button = tkinter.ttk.Radiobutton(third_frame_child_frame_1, text='No', variable=smtp_server_requires_authentication, value=False, command=print_smtp_server_requires_authentication)
smtp_server_requires_authentication_true_button.state(['disabled'])
smtp_server_requires_authentications_false_button.state(['disabled'])
smtp_server_requires_authentication_true_button.grid(column=1, row=3, padx=15)
smtp_server_requires_authentications_false_button.grid(column=2, row=3, padx=15)

# Define a dummy label to space out groups of rows.
third_window_dummy_label_0 = tkinter.ttk.Label(third_frame_child_frame_1,  text='')
third_window_dummy_label_0.grid(column=0, row=4, sticky=(tkinter.W, tkinter.E))

# Smtp server name
third_window_label_4 = tkinter.ttk.Label(third_frame_child_frame_1, text='Smtp server name:')
third_window_label_4.grid(column=0, row=5, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

smtp_server_name_combobox = tkinter.ttk.Combobox(third_frame_child_frame_1, textvariable=smtp_server_name)
smtp_server_name_combobox['values'] = ('smtp.gmail.com')

# If a previously saved setting can be found then use it.
if 'smtp_server_name' in previously_saved_email_sending_details:
	smtp_server_name.set(previously_saved_email_sending_details['smtp_server_name'])
	if smtp_server_name.get() not in smtp_server_name_combobox['values']:
		smtp_server_name_combobox['values'] = (smtp_server_name.get(), 'smtp.gmail.com')
	smtp_server_name_combobox.set(smtp_server_name.get())
smtp_server_name_combobox.state(['disabled'])
smtp_server_name_combobox.grid(column=2, row=5, padx=10, sticky=(tkinter.N, tkinter.E))

# Smtp server port
third_window_label_5 = tkinter.ttk.Label(third_frame_child_frame_1, text='Smtp server port:')
third_window_label_5.grid(column=0, row=6, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

smtp_server_port_combobox = tkinter.ttk.Combobox(third_frame_child_frame_1, textvariable=smtp_server_port)
smtp_server_port_combobox['values'] = (25, 465, 587)

# If a previously saved setting can be found then use it.
temporary_list = []
if ('smtp_server_port' in previously_saved_email_sending_details) and (previously_saved_email_sending_details['smtp_server_port'] != ''):
	smtp_server_port.set(previously_saved_email_sending_details['smtp_server_port'])
	if smtp_server_port.get() not in smtp_server_port_combobox['values']:
		temporary_list.append(smtp_server_port.get())

		for item in smtp_server_port_combobox['values']:
			temporary_list.append(item)

		smtp_server_port_combobox['values'] = temporary_list

	smtp_server_port_combobox.set(smtp_server_port.get())

smtp_server_port_combobox.state(['disabled'])
smtp_server_port_combobox.grid(column=2, row=6, padx=10, sticky=(tkinter.N, tkinter.E))

# Define a dummy label to space out groups of rows.
third_window_dummy_label_1 = tkinter.ttk.Label(third_frame_child_frame_1,  text='')
third_window_dummy_label_1.grid(column=0, row=7, sticky=(tkinter.W, tkinter.E))

# Smtp username
third_window_label_6 = tkinter.ttk.Label(third_frame_child_frame_1, text='Smtp user name')
third_window_label_6.grid(column=0, row=8, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

smtp_username_entrybox = tkinter.ttk.Entry(third_frame_child_frame_1, width=35, textvariable=smtp_username)
smtp_username_entrybox.state(['disabled'])
smtp_username_entrybox.grid(column=2, row=8, padx=10, sticky=(tkinter.N, tkinter.E))
smtp_username_entrybox.bind('<Key>', print_smtp_username)

# Smtp password
third_window_label_7 = tkinter.ttk.Label(third_frame_child_frame_1, text='Smtp password')
third_window_label_7.grid(column=0, row=9, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

smtp_password_entrybox = tkinter.ttk.Entry(third_frame_child_frame_1, width=35, textvariable=smtp_password, show='*')
smtp_password_entrybox.state(['disabled'])
smtp_password_entrybox.grid(column=2, row=9, padx=10, sticky=(tkinter.N, tkinter.E))
smtp_password_entrybox.bind('<Key>', print_smtp_password)

# Define a dummy label to space out groups of rows.
third_window_dummy_label_2 = tkinter.ttk.Label(third_frame_child_frame_1,  text='')
third_window_dummy_label_2.grid(column=0, row=10, sticky=(tkinter.W, tkinter.E))

# Email sending interval
third_window_label_8 = tkinter.ttk.Label(third_frame_child_frame_1, text='Email sending interval in minutes:')
third_window_label_8.grid(column=0, row=11, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

email_sending_interval_combobox = tkinter.ttk.Combobox(third_frame_child_frame_1, justify=tkinter.CENTER, width=5, textvariable=email_sending_interval_in_minutes)
email_sending_interval_combobox['values'] = (1, 2, 3, 4, 5, 10, 12, 15, 18, 20, 25, 30, 40, 50, 60, 90, 120, 180, 240, 300)

# If a previously saved setting can be found then use it.
if email_sending_interval != 0:
	email_sending_interval_in_minutes.set(int(email_sending_interval / 60))
	email_sending_interval_combobox.set(email_sending_interval_in_minutes.get())
else:
	email_sending_interval_combobox.set(30)
	
email_sending_interval_combobox.state(['disabled'])
email_sending_interval_combobox.bind('<<ComboboxSelected>>', convert_email_sending_interval_to_seconds)
email_sending_interval_combobox.grid(column=2, row=11, padx=10, sticky=(tkinter.N, tkinter.E))

# Email sending recipients
third_window_label_9 = tkinter.ttk.Label(third_frame_child_frame_1, text='Add email addresses separated\nby commas and press Enter:')
third_window_label_9.grid(column=0, row=12, pady=10, padx=10, rowspan=2, sticky=(tkinter.W, tkinter.N))

email_address_entrybox = tkinter.ttk.Entry(third_frame_child_frame_1, width=45, textvariable=email_addresses_string)
email_address_entrybox.state(['disabled'])
email_address_entrybox.grid(column=1, row=12, pady=10, padx=10, columnspan=3, sticky=(tkinter.N, tkinter.E))
email_address_entrybox.bind('<Return>', add_email_addresses_to_list)

# Define a dummy label to space out groups of rows.
third_window_dummy_label_3 = tkinter.ttk.Label(third_frame_child_frame_1,  text='')
third_window_dummy_label_3.grid(column=0, row=13, sticky=(tkinter.W, tkinter.E))

email_address_text_1 = tkinter.ttk.Label(third_frame_child_frame_1, text='Email address 1:')
email_address_text_1.grid(column=0, row=14, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))
email_address_label_1 = tkinter.ttk.Label(third_frame_child_frame_1, textvariable=email_address_1)
email_address_label_1.grid(column=1, row=14, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

email_address_text_2 = tkinter.ttk.Label(third_frame_child_frame_1, text='Email address 2:')
email_address_text_2.grid(column=0, row=15, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))
email_address_label_2 = tkinter.ttk.Label(third_frame_child_frame_1, textvariable=email_address_2)
email_address_label_2.grid(column=1, row=15, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

email_address_text_3 = tkinter.ttk.Label(third_frame_child_frame_1, text='Email address 3:')
email_address_text_3.grid(column=0, row=16, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))
email_address_label_3 = tkinter.ttk.Label(third_frame_child_frame_1, textvariable=email_address_3)
email_address_label_3.grid(column=1, row=16, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

email_address_text_4 = tkinter.ttk.Label(third_frame_child_frame_1, text='Email address 4:')
email_address_text_4.grid(column=0, row=17, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))
email_address_label_4 = tkinter.ttk.Label(third_frame_child_frame_1, textvariable=email_address_4)
email_address_label_4.grid(column=1, row=17, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

email_address_text_5 = tkinter.ttk.Label(third_frame_child_frame_1, text='Email address 5:')
email_address_text_5.grid(column=0, row=18, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))
email_address_label_5 = tkinter.ttk.Label(third_frame_child_frame_1, textvariable=email_address_5)
email_address_label_5.grid(column=1, row=18, padx=10, columnspan=2, sticky=(tkinter.W, tkinter.N))

# Define a dummy label to space out groups of rows.
third_window_dummy_label_4 = tkinter.ttk.Label(third_frame_child_frame_1,  text='')
third_window_dummy_label_4.grid(column=0, row=19, sticky=(tkinter.W, tkinter.E))

# Heartbeat settings
third_window_label_11 = tkinter.ttk.Label(third_frame_child_frame_1, text='Start HeartBeat Checker:')
third_window_label_11.grid(column=0, row=20, padx=10, sticky=(tkinter.W, tkinter.N))

heartbeat_true_button = tkinter.ttk.Radiobutton(third_frame_child_frame_1, text='Yes', variable=heartbeat, value=True, command=print_heartbeat)
heartbeat_false_button = tkinter.ttk.Radiobutton(third_frame_child_frame_1, text='No', variable=heartbeat, value=False, command=print_heartbeat)
heartbeat_true_button.state(['disabled'])
heartbeat_false_button.state(['disabled'])
heartbeat_true_button.grid(column=1, row=20, padx=15)
heartbeat_false_button.grid(column=2, row=20, padx=15)

third_window_label_12 = tkinter.ttk.Label(third_frame_child_frame_1, text="HeartBeat Checker monitors the health of LoudnessCorrection's threads and sends email if one stops.")
third_window_label_12.grid(column=0, row=21, pady=10, padx=10, columnspan=3, sticky=(tkinter.W, tkinter.N))

# Define a horizontal line to space out groups of rows.
third_window_separator_1 = tkinter.ttk.Separator(third_frame_child_frame_1, orient=tkinter.HORIZONTAL)
third_window_separator_1.grid(column=0, row=22, padx=10, columnspan=3, sticky=(tkinter.W, tkinter.E))

# Define another label.
third_window_label_14 = tkinter.ttk.Label(third_frame_child_frame_1, text="Send a test email using the above settings")
third_window_label_14.grid(column=0, row=23, padx=10, pady=10, columnspan=3, sticky=(tkinter.W, tkinter.N))

third_window_send_button = tkinter.Button(third_frame_child_frame_1, text = "Send", command = send_test_email)
third_window_send_button.grid(column=2, row=23, pady=10, sticky=(tkinter.N))	
third_window_send_button['state'] = 'disabled'

# Define a horizontal line to space out groups of rows.
third_window_separator_2 = tkinter.ttk.Separator(third_frame_child_frame_1, orient=tkinter.HORIZONTAL)
third_window_separator_2.grid(column=0, row=24, padx=10, columnspan=3, sticky=(tkinter.W, tkinter.E))

# Define labels that are used to display error or success messages.
third_window_label_15 = tkinter.ttk.Label(third_frame_child_frame_1, textvariable=email_sending_message_1, wraplength=text_wrap_length_in_pixels)
third_window_label_15.grid(column=0, row=25, padx=10, pady=5, columnspan=3, sticky=(tkinter.W, tkinter.N))

third_window_label_17 = tkinter.ttk.Label(third_frame_child_frame_1, textvariable=email_sending_message_2, wraplength=text_wrap_length_in_pixels)
third_window_label_17.grid(column=0, row=26, padx=10, pady=5, columnspan=3, sticky=(tkinter.W, tkinter.N))

# Create the buttons for the frame
third_window_back_button = tkinter.Button(third_frame, text = "Back", command = call_second_frame_on_top)
third_window_back_button.grid(column=1, row=1, padx=30, pady=10, sticky=(tkinter.E, tkinter.N))
third_window_next_button = tkinter.Button(third_frame, text = "Next", command = call_fourth_frame_on_top)
third_window_next_button.grid(column=2, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))

enable_email_settings()


###########################################################################################################
# Window number 4                                                                                         #
###########################################################################################################

# This window lets the user define if he want's html-report written on disk or and a ram disk created for writing it in.

# Html - report settings
fourth_window_label_1 = tkinter.ttk.Label(fourth_frame_child_frame_1, text='Write html progress report:')
fourth_window_label_1.grid(column=0, row=0, columnspan=2, padx=10, sticky=(tkinter.W, tkinter.N))
write_html_progress_report_true_radiobutton = tkinter.ttk.Radiobutton(fourth_frame_child_frame_1, text='Yes', variable=write_html_progress_report, value=True, command=print_write_html_progress_report)
write_html_progress_report_false_radiobutton = tkinter.ttk.Radiobutton(fourth_frame_child_frame_1, text='No', variable=write_html_progress_report, value=False, command=print_write_html_progress_report)
write_html_progress_report_true_radiobutton.grid(column=3, row=0, padx=15)
write_html_progress_report_false_radiobutton.grid(column=4, row=0, padx=15)

# Ram - disk.
fourth_window_label_2 = tkinter.ttk.Label(fourth_frame_child_frame_1, text='Create a ram - disk for html report:')
fourth_window_label_2.grid(column=0, row=2, columnspan=2, padx=10, sticky=(tkinter.W, tkinter.N))
create_a_ram_disk_for_html_report_true_radiobutton = tkinter.ttk.Radiobutton(fourth_frame_child_frame_1, text='Yes', variable=create_a_ram_disk_for_html_report, value=True, command=print_create_a_ram_disk_for_html_report_and_toggle_next_button_state)
create_a_ram_disk_for_html_report_false_radiobutton = tkinter.ttk.Radiobutton(fourth_frame_child_frame_1, text='No', variable=create_a_ram_disk_for_html_report, value=False, command=print_create_a_ram_disk_for_html_report_and_toggle_next_button_state)
create_a_ram_disk_for_html_report_true_radiobutton.grid(column=3, row=2, padx=15)
create_a_ram_disk_for_html_report_false_radiobutton.grid(column=4, row=2, padx=15)

# Some explanatory texts.
twentyfirst_label = tkinter.ttk.Label(fourth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Html progress report is a live view into LoudnessCorrection process queue showing a list of files being processed, waiting in the queue and 100 last completed files.\n\nProgress report is a html-file in the HotFolder that can be viewed with a web-browser. The page updates every 5 seconds and because of this needs speedy access to the disk. During heavy disk traffic html-page cannot be updated frequently enough unless a ram disk is created and mounted as the directory where the html-page is written into.')
twentyfirst_label.grid(column=0, row=3, pady=10, padx=10, columnspan=4, sticky=(tkinter.W, tkinter.N))

# Define a horizontal line to space out groups of rows.
fourth_window_separator_1 = tkinter.ttk.Separator(fourth_frame_child_frame_1, orient=tkinter.HORIZONTAL)
fourth_window_separator_1.grid(column=0, row=4, padx=10, pady=10, columnspan=5, sticky=(tkinter.W, tkinter.E))

# Ram device name.
fourth_window_label_3 = tkinter.ttk.Label(fourth_frame_child_frame_1, text='Use this ram device for creating the ram disk:')
fourth_window_label_3.grid(column=0, row=5, columnspan=4, padx=10, sticky=(tkinter.W, tkinter.N))
ram_device_name_combobox = tkinter.ttk.Combobox(fourth_frame_child_frame_1, justify=tkinter.CENTER, textvariable=ram_device_name)
# Get the ram device names from the os.
error_happened, error_message, list_of_ram_devices = get_list_of_ram_devices_from_os()
if error_happened == True:
	fourth_window_error_label_1 = tkinter.ttk.Label(fourth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, foreground='red', text=error_message)
	fourth_window_error_label_1.grid(column=0, row=10, columnspan=4, padx=10, pady=10, sticky=(tkinter.W, tkinter.N))
ram_device_name_combobox['values'] = list_of_ram_devices
if len(list_of_ram_devices) > 0:
	ram_device_name_combobox.set(list_of_ram_devices[0])
ram_device_name_combobox.bind('<<ComboboxSelected>>', print_ram_device_name)
ram_device_name_combobox.grid(column=3, row=5, columnspan=2, padx=10, sticky=(tkinter.N))

# Create another label with explanatory text on it.
fourth_window_label_4 = tkinter.ttk.Label(fourth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text="If you know you haven't used ram - devices for anything on this computer, then you can just select the first ram device /dev/ram1.")
fourth_window_label_4.grid(column=0, row=6, columnspan=4, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))

# Define a horizontal line to space out groups of rows.
fourth_window_separator_1 = tkinter.ttk.Separator(fourth_frame_child_frame_1, orient=tkinter.HORIZONTAL)
fourth_window_separator_1.grid(column=0, row=7, padx=10, pady=10, columnspan=5, sticky=(tkinter.W, tkinter.E))

# Choose which username LoudnessCorrection will run under.
fourth_window_label_5 = tkinter.ttk.Label(fourth_frame_child_frame_1, text='Which user account LoudnessCorrection will use to run:')
fourth_window_label_5.grid(column=0, row=8, columnspan=4, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))
username_combobox = tkinter.ttk.Combobox(fourth_frame_child_frame_1, justify=tkinter.CENTER, textvariable=user_account)
# Get user account names from the os.
error_happened, error_message, list_of_normal_useraccounts = get_list_of_normal_user_accounts_from_os()

if error_happened == True:
	fourth_window_error_label_2 = tkinter.ttk.Label(fourth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, foreground='red', text=error_message)
	fourth_window_error_label_2.grid(column=0, row=11, columnspan=4, padx=10, pady=10, sticky=(tkinter.W, tkinter.N))
	
username_combobox['values'] = list_of_normal_useraccounts

if len(list_of_normal_useraccounts) > 0:
	username_combobox.set(list_of_normal_useraccounts[0])
	
username_combobox.bind('<<ComboboxSelected>>', print_user_account)
username_combobox.grid(column=3, row=8, columnspan=2, pady=10, padx=10, sticky=(tkinter.N))

fourth_window_label_7 = tkinter.ttk.Label(fourth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='LoudnessCorrection will be run with non root privileges, you can choose here which user account to use.\n\nIf you choose the HotFolder to be shared to the network with Samba in the next screen, the HotFolder directory structure read and write permissions will be set so that only this user has write access to files in Hotfolder directories and all other users can only read.')
fourth_window_label_7.grid(column=0, row=9, columnspan=4, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))

# Define a horizontal line to space out groups of rows.
fourth_window_separator_1 = tkinter.ttk.Separator(fourth_frame_child_frame_1, orient=tkinter.HORIZONTAL)
fourth_window_separator_1.grid(column=0, row=10, padx=10, pady=10, columnspan=5, sticky=(tkinter.W, tkinter.E))

# Peak metering settings
fourth_window_label_1 = tkinter.ttk.Label(fourth_frame_child_frame_1, text='Peak measurement method:')
fourth_window_label_1.grid(column=0, row=11, columnspan=2, padx=10, sticky=(tkinter.W, tkinter.N))
sample_peak_radiobutton = tkinter.ttk.Radiobutton(fourth_frame_child_frame_1, text='Sample Peak', variable=sample_peak, value=True, command=set_sample_peak_measurement_method)
true_peak_radiobutton = tkinter.ttk.Radiobutton(fourth_frame_child_frame_1, text='TruePeak', variable=sample_peak, value=False, command=set_sample_peak_measurement_method)
sample_peak_radiobutton.grid(column=3, row=11, padx=15)
true_peak_radiobutton.grid(column=4, row=11, padx=15)

# Some explanatory texts.
peak_measurement_label = tkinter.ttk.Label(fourth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='This options lets you choose if you want to use sample peak or TruePeak measurement. The peak value is important only in cases where file loudness is below target -23 LUFS and needs to be increased. If increasing volume would cause peaks to go over a set limit (-2 dBFS for TruePeak and -4 dB for sample peak) then a protective limiter is used. The resulting max peaks will be about 1 dB above the limit (-1 dBFS / -3 dBFS).\n\nNote that using TruePeak slows down file processing by a factor of 4. When using sample peak you still have about 3 dBs headroom for the true peaks to exist.')
peak_measurement_label.grid(column=0, row=12, pady=10, padx=10, columnspan=4, sticky=(tkinter.W, tkinter.N))

# Create the buttons for the frame
fourth_window_back_button = tkinter.Button(fourth_frame, text = "Back", command = call_third_frame_on_top)
fourth_window_back_button.grid(column=1, row=1, padx=30, pady=10, sticky=(tkinter.E, tkinter.N))
fourth_window_next_button = tkinter.Button(fourth_frame, text = "Next", command = call_fifth_frame_on_top)

# If we were no successful in getting the list of ram device names from the os and create_ram_disk = True, disable the next button.
if (len(list_of_ram_devices) == 0) and (create_a_ram_disk_for_html_report.get() == True):
	fourth_window_next_button['state'] = 'disabled'
# If we were not successful in getting the list of user accounts from the os, disable the next button.
if len(list_of_normal_useraccounts) == 0:
	fourth_window_next_button['state'] = 'disabled'
fourth_window_next_button.grid(column=2, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))


###########################################################################################################
# Window number 5                                                                                         #
###########################################################################################################

# Define a label and two buttons for Samba configuration enable / disable.
fifth_window_label_1 = tkinter.ttk.Label(fifth_frame_child_frame_1,  text='Share HotFolder to the network with Samba:')
fifth_window_label_1.grid(column=0, row=0, columnspan=2, pady=20, padx=10, sticky=(tkinter.W, tkinter.N))

# Language for pathnames and result-graphics
enable_samba_radiobutton = tkinter.ttk.Radiobutton(fifth_frame_child_frame_1, text='Yes', variable=use_samba, value=True, command=print_use_samba_variable_and_toggle_text_widget)
disable_samba_radiobutton = tkinter.ttk.Radiobutton(fifth_frame_child_frame_1, text='No', variable=use_samba, value=False, command=print_use_samba_variable_and_toggle_text_widget)
enable_samba_radiobutton.grid(column=2, row=0, padx=15, pady=20)
disable_samba_radiobutton.grid(column=3, row=0, padx=15, pady=20)

# Create a text widget to display the samba configuration.
samba_config_text_widget = tkinter.Text(fifth_frame_child_frame_1, width=80, height=40, wrap='none', undo=True)
samba_config_text_widget.insert('1.0', samba_configuration_file_content_as_a_string)
samba_config_text_widget.columnconfigure(0, weight=1)
samba_config_text_widget.rowconfigure(0, weight=1)
samba_config_text_widget['background'] = 'white'
samba_config_text_widget.bind('<Control z>', undo_text_in_text_widget) # Bind Ctrl+z to our subroutine. The last command of the subroutine stops tkinter from processing system level bound Ctrl+z which would undo too far and empty our text widget totally.
samba_config_text_widget.grid(column=0, row=1, columnspan=4, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))

# .edit_modified() returns = 1 if the text in the widget has modified.
# The first insertion of text by this program in the widget is also considered as a modification of text.
# This results in user being able to undo past the first text insertion, resulting in an empty text display.
# To prevent user undoing too far, we set the flag to 'False' after the inital text is inserted.
# After this the user cannot undo so far that the text widget becomes empty.
samba_config_text_widget.edit_modified(False)

# Add scrollbars to the text widget.
samba_config_text_widget_vertical_scrollbar = tkinter.ttk.Scrollbar(fifth_frame_child_frame_1, orient=tkinter.VERTICAL, command=samba_config_text_widget.yview)
samba_config_text_widget.configure(yscrollcommand=samba_config_text_widget_vertical_scrollbar.set)
samba_config_text_widget_vertical_scrollbar.grid(column=5, row=1, sticky=(tkinter.N, tkinter.S))

samba_config_text_widget_horizontal_scrollbar = tkinter.ttk.Scrollbar(fifth_frame_child_frame_1, orient=tkinter.HORIZONTAL, command=samba_config_text_widget.xview)
samba_config_text_widget.configure(xscrollcommand=samba_config_text_widget_horizontal_scrollbar.set)
samba_config_text_widget_horizontal_scrollbar.grid(column=0, row=2, columnspan=4, sticky=(tkinter.W, tkinter.E))

# Create the buttons for the frame
first_window_back_button = tkinter.Button(fifth_frame, text = "Back", command = call_fourth_frame_on_top)
first_window_back_button.grid(column=1, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))
first_window_undo_button = tkinter.Button(fifth_frame, text = "Undo", command = undo_text_in_text_widget)
first_window_undo_button.grid(column=2, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))
first_window_next_button = tkinter.Button(fifth_frame, text = "Next", command = call_sixth_frame_on_top)
first_window_next_button.grid(column=3, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))


###########################################################################################################
# Window number 6                                                                                         #
###########################################################################################################

# Ask for root password

# Create the label for the frame
sixth_window_label_1 = tkinter.ttk.Label(sixth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Password is needed to write FreeLCS init scripts to system directories:')
sixth_window_label_1.grid(column=0, row=0, columnspan=4, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))

root_password_entrybox = tkinter.ttk.Entry(sixth_frame_child_frame_1, width=35, textvariable=root_password, show='*')
root_password_entrybox.grid(column=0, row=1, padx=10, pady=10, sticky=(tkinter.N, tkinter.E))
root_password_entrybox.bind('<Key>', print_root_password)
root_password_entrybox.bind('<Return>', test_if_root_password_is_valid)

# Define label that is used to display error messages.
sixth_window_label_2 = tkinter.ttk.Label(sixth_frame_child_frame_1, foreground='red', textvariable=root_password_was_not_accepted_message, wraplength=text_wrap_length_in_pixels)
sixth_window_label_2.grid(column=0, row=2, padx=10, pady=5, columnspan=4, sticky=(tkinter.W, tkinter.N))

# Create the buttons for the frame
sixth_window_back_button = tkinter.Button(sixth_frame, text = "Back", command = call_fifth_frame_on_top)
sixth_window_back_button.grid(column=1, row=1, padx=30, pady=10, sticky=(tkinter.E, tkinter.N))
sixth_window_next_button = tkinter.Button(sixth_frame, text = "Next", command = test_if_root_password_is_valid)
sixth_window_next_button.grid(column=2, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))


###########################################################################################################
# Window number 7                                                                                         #
###########################################################################################################

# Create the labels for the frame
seventh_window_label_1 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='This window displays all external programs LoudnessCorrection needs to do its job.\nAll programs displayed as "Not Installed" must be installed in order to use LoudnessCorrection.')
seventh_window_label_1.grid(column=0, row=0, columnspan=4, padx=10, pady=5, sticky=(tkinter.W, tkinter.N))

# Define a horizontal line to space out groups of rows.
seventh_window_separator_1 = tkinter.ttk.Separator(seventh_frame_child_frame_1, orient=tkinter.HORIZONTAL)
seventh_window_separator_1.grid(column=0, row=1, padx=10, pady=10, columnspan=5, sticky=(tkinter.W, tkinter.E))

# sox
seventh_window_label_4 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Sox          (version 14.4.0 required)')
seventh_window_label_4.grid(column=0, row=2, columnspan=1, padx=10, sticky=(tkinter.W, tkinter.N))
seventh_window_label_5 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, textvariable=sox_is_installed)
seventh_window_label_5.grid(column=3, row=2, columnspan=1, padx=10, sticky=(tkinter.N))

# gnuplot
seventh_window_label_6 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Gnuplot')
seventh_window_label_6.grid(column=0, row=3, columnspan=1, padx=10, sticky=(tkinter.W, tkinter.N))
seventh_window_label_7 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, textvariable=gnuplot_is_installed)
seventh_window_label_7.grid(column=3, row=3, columnspan=1, padx=10, sticky=(tkinter.N))

# samba
seventh_window_label_8 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Samba')
seventh_window_label_8.grid(column=0, row=4, columnspan=1, padx=10, sticky=(tkinter.W, tkinter.N))
seventh_window_label_9 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, textvariable=samba_is_installed)
seventh_window_label_9.grid(column=3, row=4, columnspan=1, padx=10, sticky=(tkinter.N))

# mediainfo
seventh_window_label_19 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Mediainfo')
seventh_window_label_19.grid(column=0, row=5, columnspan=1, padx=10, sticky=(tkinter.W, tkinter.N))
seventh_window_label_20 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, textvariable=mediainfo_is_installed)
seventh_window_label_20.grid(column=3, row=5, columnspan=1, padx=10, sticky=(tkinter.N))

# libebur128
#seventh_window_label_10 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Libebur128 (required version: ' + str(loudness_required_install_date_list[2]) + '.' + str(loudness_required_install_date_list[1]) + '.' + str(loudness_required_install_date_list[0]) + ')')
seventh_window_label_10 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Libebur128   (4.0 and 5.0 compatibility patch required)')
seventh_window_label_10.grid(column=0, row=6, columnspan=1, padx=10, sticky=(tkinter.W, tkinter.N))
seventh_window_label_11 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, textvariable=libebur128_is_installed)
seventh_window_label_11.grid(column=3, row=6, columnspan=1, padx=10, sticky=(tkinter.N))

# LoudnessCorrection
seventh_window_label_12 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='LoudnessCorrection Scripts')
seventh_window_label_12.grid(column=0, row=7, columnspan=1, padx=10, sticky=(tkinter.W, tkinter.N))
loudnesscorrection_scripts_are_installed.set('Not Installed')
seventh_window_loudnesscorrection_label = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, textvariable=loudnesscorrection_scripts_are_installed)
seventh_window_loudnesscorrection_label['foreground'] = 'red'
seventh_window_loudnesscorrection_label.grid(column=3, row=7, columnspan=1, padx=10, sticky=(tkinter.N))

# Define a horizontal line to space out groups of rows.
seventh_window_separator_2 = tkinter.ttk.Separator(seventh_frame_child_frame_1, orient=tkinter.HORIZONTAL)
seventh_window_separator_2.grid(column=0, row=8, padx=10, pady=10, columnspan=5, sticky=(tkinter.W, tkinter.E))

# Toggle installation status
seventh_window_toggle_label = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Toggle reinstallation of all programs:')
seventh_window_toggle_label.grid(column=0, row=9, columnspan=2, padx=10, pady=2, sticky=(tkinter.W))
seventh_window_toggle_button = tkinter.Button(seventh_frame_child_frame_1, text = "Toggle", command = toggle_installation_status)
seventh_window_toggle_button.grid(column=3, row=9, padx=30, pady=2, sticky=(tkinter.N))

seventh_window_label_14 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Install all missing programs:')
seventh_window_label_14.grid(column=0, row=10, columnspan=2, padx=10, pady=2, sticky=(tkinter.W))
seventh_window_install_button = tkinter.Button(seventh_frame_child_frame_1, text = "Install", command = install_missing_programs)
seventh_window_install_button.grid(column=3, row=10, padx=30, pady=2, sticky=(tkinter.N))

seventh_window_label_15 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Show me the shell commands to install external programs:')
seventh_window_label_15.grid(column=0, row=11, columnspan=2, padx=10, pady=2, sticky=(tkinter.W))
seventh_window_show_button_1 = tkinter.Button(seventh_frame_child_frame_1, text = "Show", command = show_installation_shell_commands)
seventh_window_show_button_1.grid(column=3, row=11, padx=30, pady=2, sticky=(tkinter.N))

# Define a horizontal line to space out groups of rows.
seventh_window_separator_3 = tkinter.ttk.Separator(seventh_frame_child_frame_1, orient=tkinter.HORIZONTAL)
seventh_window_separator_3.grid(column=0, row=12, padx=10, pady=10, columnspan=5, sticky=(tkinter.W, tkinter.E))

# Define labels that are used to display error or success messages.
seventh_window_label_16 = tkinter.ttk.Label(seventh_frame_child_frame_1, textvariable=seventh_window_message_1, wraplength=text_wrap_length_in_pixels)
seventh_window_label_16.grid(column=0, row=13, padx=10, pady=5, columnspan=3, sticky=(tkinter.W, tkinter.N))

seventh_window_label_17 = tkinter.ttk.Label(seventh_frame_child_frame_1, textvariable=seventh_window_message_2, wraplength=text_wrap_length_in_pixels)
seventh_window_label_17.grid(column=0, row=14, padx=10, pady=5, columnspan=3, sticky=(tkinter.W, tkinter.N))

seventh_window_label_18 = tkinter.ttk.Label(seventh_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text='Show me the messages that the installation produced:')
seventh_window_label_18.grid(column=0, row=15, columnspan=2, padx=10, pady=2, sticky=(tkinter.W))
seventh_window_show_button_2 = tkinter.Button(seventh_frame_child_frame_1, text = "Show", command = show_installation_output_messages)
seventh_window_show_button_2.grid(column=3, row=15, padx=30, pady=2, sticky=(tkinter.N))

# Create the buttons for the frame
seventh_window_back_button = tkinter.Button(seventh_frame, text = "Back", command = call_sixth_frame_on_top)
seventh_window_back_button.grid(column=1, row=1, padx=30, pady=10, sticky=(tkinter.E, tkinter.N))
seventh_window_next_button = tkinter.Button(seventh_frame, text = "Next", command = call_ffmpeg_info_frame_on_top)
seventh_window_next_button.grid(column=2, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))	

set_seventh_window_label_texts_and_colors()
set_button_and_label_states_on_window_seven()


###########################################################################################################
# Window number 8                                                                                         #
###########################################################################################################

# Create the label for the frame
eigth_window_label = tkinter.ttk.Label(eigth_frame_child_frame_1, text='You can copy selected text with control + c to clipboard.')
eigth_window_label.grid(column=0, row=0, pady=10, padx=10, sticky=(tkinter.W, tkinter.N))

# Create a text widget to display the installation commands.
install_commands_text_widget = tkinter.Text(eigth_frame_child_frame_1, width=80, height=40, wrap='none', undo=False)
install_commands_text_widget.insert('1.0', eight_window_textwidget_text_content)
install_commands_text_widget.columnconfigure(0, weight=1)
install_commands_text_widget.rowconfigure(0, weight=1)
install_commands_text_widget['background'] = 'white'
install_commands_text_widget.grid(column=0, row=1, columnspan=4, sticky=(tkinter.W, tkinter.N, tkinter.E, tkinter.S))

# Add scrollbars to the text widget.
install_commands_text_widget_vertical_scrollbar = tkinter.ttk.Scrollbar(eigth_frame_child_frame_1, orient=tkinter.VERTICAL, command=install_commands_text_widget.yview)
install_commands_text_widget.configure(yscrollcommand=install_commands_text_widget_vertical_scrollbar.set)
install_commands_text_widget_vertical_scrollbar.grid(column=5, row=1, sticky=(tkinter.N, tkinter.S))

install_commands_text_widget_horizontal_scrollbar = tkinter.ttk.Scrollbar(eigth_frame_child_frame_1, orient=tkinter.HORIZONTAL, command=install_commands_text_widget.xview)
install_commands_text_widget.configure(xscrollcommand=install_commands_text_widget_horizontal_scrollbar.set)
install_commands_text_widget_horizontal_scrollbar.grid(column=0, row=2, columnspan=4, sticky=(tkinter.W, tkinter.E))

# Disable all other key presses on the text widget but control+c.
# The user will not be able to modify text in the window, but he will be able to take a copy of it to the clipboard with Control+c.
install_commands_text_widget.bind('<Control c>', lambda ctrl_c: '')
install_commands_text_widget.bind('<Key>', lambda any_key: 'break')

# Create the Back - button for the frame
eigth_window_back_button = tkinter.Button(eigth_frame, text = "Back", command = call_seventh_frame_on_top)
eigth_window_back_button.grid(column=2, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))


###########################################################################################################
# Window number 9                                                                                         #
###########################################################################################################

# Create the label for the frame
ninth_window_label_1 = tkinter.ttk.Label(ninth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text="Everything was installed successfully :)\n\nLoudnessCorrection will be started when you boot up your computer, or you can start it now manually running the following command:\n")
ninth_window_label_1.grid(column=0, row=0, columnspan=4, pady=10, padx=10, sticky=(tkinter.N))

loudness_correction_manual_startup_commands = "sudo   -b   /etc/init.d/loudnesscorrection_init_script   restart"

# Create a text widget to display text that can be copy pasted.
startup_commands_text_widget = tkinter.Text(ninth_frame_child_frame_1, width=70, height=1, wrap='none', undo=False)
startup_commands_text_widget.insert('1.0', loudness_correction_manual_startup_commands)
startup_commands_text_widget.columnconfigure(0, weight=1)
startup_commands_text_widget.rowconfigure(0, weight=1)
startup_commands_text_widget['background'] = 'white'

# Setting text widget state to disabled disables copying text also. But if you set the disabled text widget at focus, then copying works :)
startup_commands_text_widget.config(state='disabled')
startup_commands_text_widget.focus()

startup_commands_text_widget.grid(column=0, row=1, columnspan=4, sticky=(tkinter.N, tkinter.S))

ninth_window_label_2 = tkinter.ttk.Label(ninth_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text="\nCopy the command in a terminal window and press enter to run.\n\nNote that there will be 90 seconds delay before LoudnessCorrection starts, HearBeat_Checker will start 60 seconds after LoudnessCorrection.")
ninth_window_label_2.grid(column=0, row=2, columnspan=4, pady=10, padx=10, sticky=(tkinter.N))

# Create the buttons for the frame
ninth_window_back_button = tkinter.Button(ninth_frame, text = "Back", command = call_ffmpeg_info_frame_on_top)
ninth_window_back_button.grid(column=1, row=3, padx=30, pady=10, sticky=(tkinter.E, tkinter.N))
ninth_window_finish_button = tkinter.Button(ninth_frame, text = "Finish", command = quit_program)
ninth_window_finish_button.grid(column=2, row=3, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))


###########################################################################################################
# FFmpeg installation info window                                                                         #
###########################################################################################################

# Create the label for the frame
ffmpeg_info_window_label_1 = tkinter.ttk.Label(ffmpeg_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text="Installer no longer automatically installs FFmpeg for you, but you can do it easily yourself by copy / pasting the following command in a terminal window:\n")
ffmpeg_info_window_label_1.grid(column=0, row=0, columnspan=4, pady=10, padx=10, sticky=(tkinter.N))

ffmpeg_manual_installation_command = "sudo apt-get -y install ffmpeg"

# Create a text widget to display text that can be copy pasted.
ffmpeg_info_window_text_widget = tkinter.Text(ffmpeg_frame_child_frame_1, width=31, height=1, wrap='none', undo=False)
ffmpeg_info_window_text_widget.insert('1.0', ffmpeg_manual_installation_command)
ffmpeg_info_window_text_widget.columnconfigure(0, weight=1)
ffmpeg_info_window_text_widget.rowconfigure(0, weight=1)
ffmpeg_info_window_text_widget['background'] = 'white'

# Setting text widget state to disabled disables copying text also. But if you set the disabled text widget at focus, then copying works :)
ffmpeg_info_window_text_widget.config(state='disabled')
ffmpeg_info_window_text_widget.focus()

ffmpeg_info_window_text_widget.grid(column=0, row=1, columnspan=4, sticky=(tkinter.N, tkinter.S))

ffmpeg_info_window_label_2 = tkinter.ttk.Label(ffmpeg_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text="\nDecompressing patented formats with FFmpeg may require a license from the rights holders. However FFmpeg may also be used to process free formats (MXF, MKV, WebM and others) or formats with possibly expired patents (Mpeg1 Layer1, Mpeg 1 Layer2) without aquiring licenses. (Disclaimer: This is not legal advice, if in doubt ask a lawyer).\n\nFFmpeg is used to process files if it's installed before starting LoudnessCorrection. So you can always install it later and reboot your server to take advantage of FFmpeg.\n\nSupported formats without FFmpeg are: Wav, Flac, Ogg.\n\nThe command to uninstall FFmpeg is: sudo apt-get remove ffmpeg libav-tools")
ffmpeg_info_window_label_2.grid(column=0, row=2, columnspan=4, pady=10, padx=10, sticky=(tkinter.N))

# Create the buttons for the frame
ffmpeg_info_window_back_button = tkinter.Button(ffmpeg_frame, text = "Back", command = call_seventh_frame_on_top)
ffmpeg_info_window_back_button.grid(column=1, row=3, padx=30, pady=10, sticky=(tkinter.E, tkinter.N))
ffmpeg_info_window_finish_button = tkinter.Button(ffmpeg_frame, text = "Next", command = call_ninth_frame_on_top)
ffmpeg_info_window_finish_button.grid(column=2, row=3, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))


###########################################################################################################
# Licence window                                                                                          #
###########################################################################################################

# Create the label for the frame
license_info_window_label_1 = tkinter.ttk.Label(license_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text="License agreement", font = ("Times", 30, "bold"))
license_info_window_label_1.grid(column=0, row=0, columnspan=4, pady=10, padx=10, sticky=(tkinter.N))

# Call a subroutine that assigns the text of Gnu GPL 3 to a variable.
store_gnu_gpl3_to_a_global_variable()

# Create a text widget to display text that can be copy pasted.
license_info_window_text_widget = tkinter.Text(license_frame_child_frame_1, width=90, height=40, wrap='none', undo=False)
license_info_window_text_widget.insert('1.0', gnu_gpl_3)
license_info_window_text_widget.columnconfigure(0, weight=1)
license_info_window_text_widget.rowconfigure(0, weight=1)
license_info_window_text_widget['background'] = 'white'

# Setting text widget state to disabled disables copying text also. But if you set the disabled text widget at focus, then copying works :)
license_info_window_text_widget.config(state='disabled')
license_info_window_text_widget.focus()

license_info_window_text_widget.grid(column=0, row=1, columnspan=4, sticky=(tkinter.N, tkinter.S))

# Add scrollbars to the text widget.
license_config_text_widget_vertical_scrollbar = tkinter.ttk.Scrollbar(license_frame_child_frame_1, orient=tkinter.VERTICAL, command=license_info_window_text_widget.yview)
license_info_window_text_widget.configure(yscrollcommand=license_config_text_widget_vertical_scrollbar.set)
license_config_text_widget_vertical_scrollbar.grid(column=5, row=1, sticky=(tkinter.N, tkinter.S))

license_config_text_widget_horizontal_scrollbar = tkinter.ttk.Scrollbar(license_frame_child_frame_1, orient=tkinter.HORIZONTAL, command=license_info_window_text_widget.xview)
license_info_window_text_widget.configure(xscrollcommand=license_config_text_widget_horizontal_scrollbar.set)
license_config_text_widget_horizontal_scrollbar.grid(column=0, row=2, columnspan=4, sticky=(tkinter.W, tkinter.E))

# Agreement button text.
license_info_window_label_2 = tkinter.ttk.Label(license_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, text="I accept the license agreement", font = ("Times", 12, "bold"))
license_info_window_label_2.grid(column=1, row=3, pady=10, padx=10, sticky=(tkinter.N))

license_checkbutton = tkinter.ttk.Checkbutton(license_frame_child_frame_1, variable=accept_license, command=change_state_of_license_agreement_button)
license_checkbutton.grid(column=2, row=3, padx=10, pady=10)

# Create the buttons for the frame
license_info_window_next_button = tkinter.Button(license_frame, text = "Next", command = call_first_frame_on_top)
license_info_window_next_button.grid(column=2, row=4, padx=30, pady=10, sticky=(tkinter.W, tkinter.N))
license_info_window_next_button['state'] = 'disabled'


###########################################################################################################
# 'Showstopper error encountered' window                                                                  #
###########################################################################################################

# Create the label for the frame
showstopper_error_window_label = tkinter.ttk.Label(showstopper_frame_child_frame_1, wraplength=text_wrap_length_in_pixels, textvariable=showstopper_error_message)
showstopper_error_window_label['foreground'] = 'red'
showstopper_error_window_label.grid(column=0, row=0, columnspan=4, pady=10, padx=20, sticky=(tkinter.E, tkinter.N, tkinter.S, tkinter.W))

# Create the buttons for the frame
showstopper_error_window_finish_button = tkinter.Button(showstopper_frame, text = "Quit", command = quit_program)
showstopper_error_window_finish_button.grid(column=2, row=1, padx=30, pady=10, sticky=(tkinter.W, tkinter.S))


##################################
# Window definitions end here :) #
##################################

# Set directory names according to language
set_directory_names_according_to_language()

# Hide all frames in reverse order, but leave first frame visible (unhidden).
showstopper_frame.grid_forget()
ninth_frame.grid_forget()
ffmpeg_frame.grid_forget()
eigth_frame.grid_forget()
seventh_frame.grid_forget()
sixth_frame.grid_forget()
fifth_frame.grid_forget()
fourth_frame.grid_forget()
third_frame.grid_forget()
second_frame.grid_forget()
first_frame.grid_forget()

## Set ttk window theme.
## Themes found in Ubuntu 12.04 are:
## ('clam', 'alt', 'default', 'classic')
#ttk_theme_name = 'clam'
#window_theme = tkinter.ttk.Style()
#available_styles = window_theme.theme_names()
## If a style named 'clam' is available, use it.
#if ttk_theme_name in available_styles:
#window_theme.theme_use(ttk_theme_name)

# Get root window geometry and center it on screen.
root_window.update()
x_position = (root_window.winfo_screenwidth() / 2) - (root_window.winfo_width() / 2) - 8
y_position = (root_window.winfo_screenheight() / 2) - (root_window.winfo_height() / 2) - 20
root_window.geometry(str(root_window.winfo_width()) + 'x' +str(root_window.winfo_height()) + '+' + str(int(x_position)) + '+' + str(int(y_position)))

# If LoudessCorrection.py or HeartBeat_Checker.py can not be found, stop and inform the user.
if path_to_loudnesscorrection == '':
	showstopper_error_message.set('Error, can not find LoudnessCorrection.py.\n\nLoudnessCorrection.py and HeartBeat_Checker.py must be in the same directory as the installer. Can not continue.')
	call_showstopper_frame_on_top()
if path_to_heartbeat_checker == '':
	showstopper_error_message.set('Error, can not find HeartBeat_Checker.py.\n\nLoudnessCorrection.py and HeartBeat_Checker.py must be in the same directory as the installer. Can not continue.')
	call_showstopper_frame_on_top()

# If we are running on a not supported operating system, then stop and inform user.
if error_message_from_find_os_name_and_version != '':
	error_message_text = 'Error, ' + error_message_from_find_os_name_and_version

	showstopper_error_message.set(error_message_text)
	call_showstopper_frame_on_top()

# Start tkinter event - loop
root_window.mainloop()
