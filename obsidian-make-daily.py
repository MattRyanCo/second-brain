#!/usr/bin/env python3
import os
from typing import Text
import arrow
import re
import subprocess
import requests

import get_calendar_events

def get_config_value(key):
	try:
		with open(os.path.join(home_root, config_file), 'r') as fh:
			for line in fh:
				if key + ":" in line:
					(_, value) = line.strip().split(":", 1)
					return value.strip()
	except:
		print('An error occurred reading your .notes config file. Does it exist?')
		quit()
	return ""

def get_link_for_file(file, link_text=""):
	if link_text != "":
		return "[[" + file.replace(".md", "") + "|" + link_text + "]]"
	else:
		return "[[" + file.replace(".md", "") + "]]"

def get_weather(location):
	payload = {'format': '3'}
	r = requests.get("http://wttr.in/" + location, params=payload)
	return r.text.strip()

def read_file(file_name):
	file_content = ""
	with open(file_name, 'r') as file_obj:
		for line in file_obj:
			file_content += line
	return(file_content)

def get_humanize_date_from_daily_note(file_name):
	daily_note = re.search("\d{4}\.\d{2}\.\d{2}\.[A-Za-z]{3}", os.path.basename(file_name).replace(".md", ""))
	if daily_note:
		(year, mon, day, _) = os.path.basename(file_name).replace(".md", "").split(".")
		todo_date = arrow.get(year + '-' + mon + '-' + day)
		return(" (from " + todo_date.humanize() + ")")
	else:
		return ""

def get_daily_notes_filename(offset=0):
	file_date = arrow.now()
	if offset != 0:
		file_date = file_date.shift(days=offset)
	return(file_date.format('YYYY.MM.DD.ddd') + ".md")

def find_todos_in_file(file_name, pattern):
	# Search a file for incomplete todos: [ ]
	# Strip the item down to its bare essentials
	# Hash it to eliminate duplicates
	matches = {}
	with open(file_name, 'r') as file_obj:
		for line in file_obj:
			todo = ""
			result = re.search(pattern, line.strip())
			if result:
				if result.group(1):
					todo = result.group(1).strip()
					if " (from " in todo:
						pos = todo.find("(from ")
						todo = todo[:pos].strip()
					else:
						todo = todo.strip()
					matches[todo] = file_name
	return matches

def search_in_file(file_name, search_for):
	# Searches file_name for search_for and returns boolean result
	with open(file_name, 'r') as file_obj:
		for line in file_obj:
			if search_for in line:
				return True
	return False

def get_done_todos():
	done_task_pattern = "\[x\](.*)"
	done = {}

	for root, dirs, files in os.walk(daily_notes):
		for fi in files:
			fi_done = {}
			if fi.endswith(".md"):
				fi_done = find_todos_in_file(os.path.join(root, fi), done_task_pattern)
				for m in fi_done:
					if m in done.keys():
						continue
					else:
						done[m] = fi_done[m]
	return done

def get_open_todos():
	open_task_pattern = "\[\s\](.*)"
	open = {}

	for root, dirs, files in os.walk(daily_notes):
		for fi in files:
			fi_open = {}
			if fi.endswith(".md"):
				fi_open = find_todos_in_file(os.path.join(root, fi), open_task_pattern)
				for m in fi_open:
					if m in open.keys():
						continue
					else:
						open[m] = fi_open[m]
	return open

# Put it all together
# home_root = os.path.expanduser('~')
home_root = "/mnt/e/OB-SecondBrain"
config_file = "_config/.notes.md"
open_tasks_template_file = "/mnt/e/OB-SecondBrain/_templates/open-tasks.md"

daily_notes = get_config_value("daily_notes_root")
weather_location = get_config_value("weather_zip")
daily_notes_file = os.path.join(daily_notes, get_daily_notes_filename())

if os.path.exists(daily_notes_file):
	print("File already exists. Not overwriting...")
else:
	print("Generating daily notes file " + os.path.basename(daily_notes_file) + "...")
	with open(daily_notes_file, 'w') as fh:
		tasks = {}
		# agenda = get_agenda().split("\n")
# Set UP YAML frontmatter at very top of file
		fh.write("---\ntags: DailyNote\n---\n")
# Build out Yesterday|Tomorrow navigation with weather
		agenda = get_calendar_events.main().split("\n")
# Make note navigation
		nav_bar = get_link_for_file(get_daily_notes_filename(offset=-1))
		nav_bar += " | " + get_link_for_file(get_daily_notes_filename(offset=1))
		nav_bar += " | " + get_weather(weather_location)
		fh.write(nav_bar + "\n")
# Grab the scheduled items from Google Calendar
		fh.write("\n## Agenda\n")
		if len(agenda) == 1:
			fh.write("Nothing in today's calendar\n")
		else:
			for item in agenda:
				fh.write(item + "\n")

# Output basic headings for today's notes.
#
		fh.write("\n## Readings & Keeps\n")
		fh.write(". \n")
#
		fh.write("\n## Today's notes & musings\n")
		fh.write("- \n")
#
		fh.write("\n---\n")
		fh.write("\n## To-Do\n")
#
#   Use daily notes & dataview format for listing open tasks. 
		fh.write("\n\n---\n")
		fh.write("### Past Due\n ```tasks\nnot done\ndue before today\n```\n")
		fh.write("\n\n---\n")
		fh.write("### Due Today\n ```tasks\nnot done\ndue today\n```\n")
		fh.write("\n\n---\n")
		fh.write("### Due Within 2 Weeks\n ```tasks\nnot done\ndue after today\ndue before in 2 weeks\n```\n")
		fh.write("\n\n---\n")
		fh.write("### Due Later\n ```tasks\nnot done\ndue after in 2 weeks\n```\n")
		fh.write("\n\n---\n")
		fh.write("### No Due Dates\n ```tasks\nnot done\nno due date\nheading does not include routine\n```")
		fh.write("\n\n---\n")
		fh.write("### Recently Created Notes\n ```dataview\nList\nFROM \"\" AND -#DailyNote\nWHERE file.ctime >= date(today) - dur(3 day)\nLIMIT 10\nSORT file.ctime\n```\n")
		fh.write("\n\n---\n")
#
# Future @todo: Read in the commands from the open-tasks template file and echo here
#   rather than recreating the commands here. This to remove the need to edit 
#   source code. Make changes in the template file and have it auto pulled in
#   on the next execution of the code. 

